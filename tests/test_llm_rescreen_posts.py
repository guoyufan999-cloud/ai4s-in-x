from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import pytest

from ai4s_legitimacy.collection.deepseek_client import DeepSeekClient
from ai4s_legitimacy.collection.llm_rescreen_posts import (
    _apply_guardrails,
    _stage1_system_prompt,
    _stage2_system_prompt,
    generate_llm_rescreen_draft,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _TransportSequence:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.requests: list[Any] = []

    def __call__(self, request, timeout: float, context=None):
        _ = context
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("transport called too many times")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeClassifier:
    def __init__(self, *, mode: str, model: str, mapping: dict[str, dict[str, Any]]) -> None:
        self.mode = mode
        self.model = model
        self.mapping = mapping

    def classify_batch(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for row in rows:
            post_id = str(row["post_id"])
            payload = dict(self.mapping[post_id])
            payload["model"] = self.model
            results.append(payload)
        return results


class _ExplodingClassifier:
    def classify_batch(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _ = rows
        raise AssertionError("resume path should not invoke classifier")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_deepseek_client_posts_openai_compatible_json_request(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": '{"items":[]}',
                                "reasoning_content": "hidden chain",
                            }
                        }
                    ],
                }
            )
        ]
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    client = DeepSeekClient.from_env()
    client.transport = transport
    response = client.complete_json(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "json only"}],
    )

    assert response == {"parsed": {"items": []}, "model": "deepseek-chat"}
    request, timeout = transport.requests[0]
    assert timeout == client.timeout_seconds
    assert request.full_url == "https://api.deepseek.com/chat/completions"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "deepseek-chat"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["content"] == "json only"


def test_deepseek_client_retries_http_and_json_errors() -> None:
    transport = _TransportSequence(
        [
            HTTPError(
                url="https://api.deepseek.com/chat/completions",
                code=429,
                msg="rate limited",
                hdrs=None,
                fp=None,
            ),
            _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "{not valid json",
                            }
                        }
                    ]
                }
            ),
            _FakeResponse(
                {
                    "model": "deepseek-reasoner",
                    "choices": [
                        {
                            "message": {
                                "content": '{"items":[{"batch_item_id":"item_000","sample_status":"true","actor_type":"uncertain","ai_review_reason":"ok","ai_confidence":0.9,"risk_flags":[]}]}'
                            }
                        }
                    ],
                }
            ),
        ]
    )
    client = DeepSeekClient(
        api_key="test-key",
        max_retries=3,
        timeout_seconds=0.01,
        transport=transport,
    )

    response = client.complete_json(
        model="deepseek-reasoner",
        messages=[{"role": "user", "content": "json please"}],
    )

    assert response["model"] == "deepseek-reasoner"
    assert response["parsed"]["items"][0]["sample_status"] == "true"
    assert len(transport.requests) == 3


def test_generate_llm_rescreen_draft_writes_pending_outputs_without_mutating_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE posts (post_id TEXT PRIMARY KEY, sample_status TEXT, actor_type TEXT)")
        connection.execute(
            "INSERT INTO posts (post_id, sample_status, actor_type) VALUES ('p1', 'false', 'uncertain')"
        )
        connection.execute(
            "INSERT INTO posts (post_id, sample_status, actor_type) VALUES ('p2', 'false', 'uncertain')"
        )
        connection.execute(
            "INSERT INTO posts (post_id, sample_status, actor_type) VALUES ('p3', 'true', 'tool_vendor_or_promotional')"
        )
        connection.commit()

    queue_path = tmp_path / "rescreen_posts.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "rescreen_posts",
                "record_type": "post",
                "record_id": "p1",
                "post_id": "p1",
                "post_date": "2025-01-01",
                "legacy_crawl_status": "crawled",
                "keyword_query": "科研 ChatGPT",
                "title": "科研用 AI 写文献综述",
                "content_text": "分享我如何用大模型整理文献。",
                "sample_status": "false",
                "actor_type": "uncertain",
            },
            {
                "review_phase": "rescreen_posts",
                "record_type": "post",
                "record_id": "p2",
                "post_id": "p2",
                "post_date": "2025-01-02",
                "legacy_crawl_status": "failed",
                "keyword_query": "科研 AI 投稿",
                "title": "AI 投稿经验",
                "content_text": "",
                "sample_status": "false",
                "actor_type": "uncertain",
            },
            {
                "review_phase": "rescreen_posts",
                "record_type": "post",
                "record_id": "p3",
                "post_id": "p3",
                "post_date": "2025-01-03",
                "legacy_crawl_status": "crawled",
                "keyword_query": "科研 AI 助手",
                "title": "科研 AI 助手推广",
                "content_text": "我们产品可以帮你做论文初稿。",
                "sample_status": "true",
                "actor_type": "tool_vendor_or_promotional",
            },
        ],
    )

    summary = generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=tmp_path / "suggestions",
        run_id="qv5_rescreen_deepseek_test",
        reviewer="guoyufan",
        review_date="2026-04-19",
        chat_classifier=_FakeClassifier(
            mode="stage1",
            model="deepseek-chat",
            mapping={
                "p1": {
                    "sample_status": "true",
                    "actor_type": "graduate_student",
                    "ai_review_reason": "明确讨论科研工作流使用",
                    "ai_confidence": 0.93,
                    "risk_flags": [],
                },
                "p2": {
                    "sample_status": "review_needed",
                    "actor_type": "uncertain",
                    "ai_review_reason": "低信息命中科研 AI 关键词",
                    "ai_confidence": 0.72,
                    "risk_flags": ["low_information"],
                },
                "p3": {
                    "sample_status": "true",
                    "actor_type": "tool_vendor_or_promotional",
                    "ai_review_reason": "推广帖但内容仍在科研 AI 使用场景",
                    "ai_confidence": 0.88,
                    "risk_flags": ["vendor_like"],
                },
            },
        ),
        reasoner_classifier=_FakeClassifier(
            mode="stage2",
            model="deepseek-reasoner",
            mapping={
                "p1": {
                    "sample_status": "true",
                    "actor_type": "graduate_student",
                    "ai_review_reason": "维持 true",
                    "ai_confidence": 0.95,
                    "risk_flags": [],
                },
                "p2": {
                    "sample_status": "review_needed",
                    "actor_type": "uncertain",
                    "ai_review_reason": "信息不足，保留 review_needed",
                    "ai_confidence": 0.81,
                    "risk_flags": ["low_information"],
                },
                "p3": {
                    "sample_status": "false",
                    "actor_type": "tool_vendor_or_promotional",
                    "ai_review_reason": "更像产品宣传，不足以保留进样本",
                    "ai_confidence": 0.9,
                    "risk_flags": ["vendor_like"],
                },
            },
        ),
        stage1_batch_size=2,
        stage2_batch_size=1,
        max_workers=2,
        false_sample_size=5,
        shard_count=1,
        shard_index=0,
        max_stage2_coverage_ratio=1.0,
    )

    full_draft_path = Path(summary["outputs"]["full_draft"])
    full_rows = [json.loads(line) for line in full_draft_path.read_text(encoding="utf-8").splitlines()]
    delta_rows = [
        json.loads(line)
        for line in Path(summary["outputs"]["delta_only"]).read_text(encoding="utf-8").splitlines()
    ]

    assert summary["full_draft_count"] == 3
    assert summary["delta_count"] == 3
    assert summary["reasoner_reviewed_count"] == 3
    assert summary["shard_index"] == 0
    assert summary["shard_count"] == 1
    assert all(row["review_status"] == "unreviewed" for row in full_rows)
    assert {row["post_id"] for row in delta_rows} == {"p1", "p2", "p3"}
    assert full_rows[0]["decision"] in {"纳入", "待复核", "剔除"}
    assert full_rows[0]["api_assistance"]["used"] == "是"
    assert full_rows[0]["stage1_model"] == "deepseek-chat"
    assert full_rows[0]["stage2_model"] == "deepseek-reasoner"
    assert Path(summary["outputs"]["priority_true_or_review_needed"]).exists()
    assert Path(summary["outputs"]["priority_reverted_positive_to_false"]).exists()
    assert "summary" in summary["outputs"]

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT post_id, sample_status, actor_type FROM posts ORDER BY post_id"
        ).fetchall()

    assert rows == [
        ("p1", "false", "uncertain"),
        ("p2", "false", "uncertain"),
        ("p3", "true", "tool_vendor_or_promotional"),
    ]


def test_low_information_vendor_news_guardrail_forces_false() -> None:
    guarded = _apply_guardrails(
        {
            "title": "风暴统计平台深度接入DeepSeek啦",
            "keyword_query": "AI辅助科研",
            "content_text": "",
            "legacy_crawl_status": "failed",
            "actor_type": "uncertain",
        },
        {
            "sample_status": "true",
            "actor_type": "tool_vendor_or_promotional",
            "ai_review_reason": "模型原本判 true",
            "ai_confidence": 0.92,
            "risk_flags": [],
        },
    )

    assert guarded["sample_status"] == "false"
    assert guarded["actor_type"] == "tool_vendor_or_promotional"
    assert "vendor_like" in guarded["risk_flags"]


def test_llm_rescreen_prompts_embed_active_research_baseline() -> None:
    stage1_prompt = _stage1_system_prompt()
    stage2_prompt = _stage2_system_prompt()

    for prompt in (stage1_prompt, stage2_prompt):
        assert "1. 话语情境" in prompt
        assert "2. 实践位置" in prompt
        assert "3. 介入方式" in prompt
        assert "4. 规范评价" in prompt
        assert "5. 边界生成" in prompt
        assert "帖子必须明确涉及 AI 或具体 AI 工具" in prompt
        assert "泛化趋势帖、科技新闻帖、纯产品介绍" in prompt


def test_generate_llm_rescreen_draft_rejects_overwide_stage2_coverage(tmp_path: Path) -> None:
    queue_path = tmp_path / "rescreen_posts.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "rescreen_posts",
                "record_type": "post",
                "record_id": f"p{i}",
                "post_id": f"p{i}",
                "post_date": "2025-01-01",
                "legacy_crawl_status": "crawled",
                "keyword_query": "科研 AI",
                "title": f"title-{i}",
                "content_text": "科研 AI 工作流",
                "sample_status": "false",
                "actor_type": "uncertain",
            }
            for i in range(4)
        ],
    )

    mapping = {
        f"p{i}": {
            "sample_status": "true",
            "actor_type": "graduate_student",
            "ai_review_reason": "positive",
            "ai_confidence": 0.95,
            "risk_flags": [],
        }
        for i in range(4)
    }

    with pytest.raises(ValueError, match="stage2_coverage_ratio exceeded guardrail"):
        generate_llm_rescreen_draft(
            queue_path=queue_path,
            output_dir=tmp_path / "suggestions",
            run_id="qv5_guardrail",
            reviewer="guoyufan",
            review_date="2026-04-20",
            chat_classifier=_FakeClassifier(mode="stage1", model="deepseek-chat", mapping=mapping),
            reasoner_classifier=_FakeClassifier(
                mode="stage2",
                model="deepseek-reasoner",
                mapping=mapping,
            ),
            shard_count=1,
            shard_index=0,
        )


def test_generate_llm_rescreen_shard_resume_and_merge_only(tmp_path: Path) -> None:
    queue_path = tmp_path / "rescreen_posts.jsonl"
    queue_rows = [
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p1",
            "post_id": "p1",
            "post_date": "2025-01-01",
            "legacy_crawl_status": "crawled",
            "keyword_query": "科研 AI 文献",
            "title": "科研 AI 文献综述",
            "content_text": "使用 AI 整理文献",
            "sample_status": "false",
            "actor_type": "uncertain",
        },
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p2",
            "post_id": "p2",
            "post_date": "2025-01-02",
            "legacy_crawl_status": "crawled",
            "keyword_query": "科研 AI 投稿",
            "title": "科研 AI 投稿经验",
            "content_text": "当前 true 但模型会打回 false",
            "sample_status": "true",
            "actor_type": "graduate_student",
        },
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p3",
            "post_id": "p3",
            "post_date": "2025-01-03",
            "legacy_crawl_status": "failed",
            "keyword_query": "AI辅助科研",
            "title": "平台接入 DeepSeek 啦",
            "content_text": "",
            "sample_status": "false",
            "actor_type": "uncertain",
        },
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p4",
            "post_id": "p4",
            "post_date": "2025-01-04",
            "legacy_crawl_status": "failed",
            "keyword_query": "科研 AI 实验",
            "title": "AI 实验设计谁能救救",
            "content_text": "",
            "sample_status": "false",
            "actor_type": "uncertain",
        },
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p5",
            "post_id": "p5",
            "post_date": "2025-01-05",
            "legacy_crawl_status": "crawled",
            "keyword_query": "科研 AI 助手",
            "title": "科研 AI 助手体验",
            "content_text": "实际写论文初稿",
            "sample_status": "false",
            "actor_type": "uncertain",
        },
        {
            "review_phase": "rescreen_posts",
            "record_type": "post",
            "record_id": "p6",
            "post_id": "p6",
            "post_date": "2025-01-06",
            "legacy_crawl_status": "crawled",
            "keyword_query": "科研 AI 边界",
            "title": "科研 AI 能不能直接写结果",
            "content_text": "当前 review_needed，模型会打回 false",
            "sample_status": "review_needed",
            "actor_type": "uncertain",
        },
    ]
    _write_jsonl(queue_path, queue_rows)

    stage1_mapping = {
        "p1": {
            "sample_status": "false",
            "actor_type": "uncertain",
            "ai_review_reason": "维持 false",
            "ai_confidence": 0.95,
            "risk_flags": [],
        },
        "p2": {
            "sample_status": "false",
            "actor_type": "graduate_student",
            "ai_review_reason": "想打回 false",
            "ai_confidence": 0.9,
            "risk_flags": [],
        },
        "p3": {
            "sample_status": "true",
            "actor_type": "tool_vendor_or_promotional",
            "ai_review_reason": "模型先给 true，guardrail 应压回 false",
            "ai_confidence": 0.9,
            "risk_flags": [],
        },
        "p4": {
            "sample_status": "false",
            "actor_type": "uncertain",
            "ai_review_reason": "低置信度 false",
            "ai_confidence": 0.6,
            "risk_flags": ["low_information"],
        },
        "p5": {
            "sample_status": "true",
            "actor_type": "tool_vendor_or_promotional",
            "ai_review_reason": "保留 true",
            "ai_confidence": 0.93,
            "risk_flags": [],
        },
        "p6": {
            "sample_status": "false",
            "actor_type": "uncertain",
            "ai_review_reason": "想打回 false",
            "ai_confidence": 0.9,
            "risk_flags": [],
        },
    }
    stage2_mapping = {
        "p2": {
            "sample_status": "false",
            "actor_type": "graduate_student",
            "ai_review_reason": "确实应打回 false",
            "ai_confidence": 0.94,
            "risk_flags": [],
        },
        "p3": {
            "sample_status": "false",
            "actor_type": "tool_vendor_or_promotional",
            "ai_review_reason": "低信息接入型帖子，维持 false",
            "ai_confidence": 0.93,
            "risk_flags": ["low_information", "vendor_like"],
        },
        "p4": {
            "sample_status": "review_needed",
            "actor_type": "uncertain",
            "ai_review_reason": "信息不足保留 review_needed",
            "ai_confidence": 0.82,
            "risk_flags": ["low_information"],
        },
        "p5": {
            "sample_status": "true",
            "actor_type": "tool_vendor_or_promotional",
            "ai_review_reason": "确有科研使用场景",
            "ai_confidence": 0.96,
            "risk_flags": [],
        },
        "p6": {
            "sample_status": "false",
            "actor_type": "uncertain",
            "ai_review_reason": "边界讨论不足，打回 false",
            "ai_confidence": 0.91,
            "risk_flags": [],
        },
    }

    output_dir = tmp_path / "suggestions"
    summary0 = generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=output_dir,
        run_id="qv5_rescreen_deepseek_test",
        reviewer="guoyufan",
        review_date="2026-04-20",
        chat_classifier=_FakeClassifier(mode="stage1", model="deepseek-chat", mapping=stage1_mapping),
        reasoner_classifier=_FakeClassifier(
            mode="stage2",
            model="deepseek-reasoner",
            mapping=stage2_mapping,
        ),
        shard_count=2,
        shard_index=0,
        max_stage2_coverage_ratio=1.0,
    )
    summary1 = generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=output_dir,
        run_id="qv5_rescreen_deepseek_test",
        reviewer="guoyufan",
        review_date="2026-04-20",
        chat_classifier=_FakeClassifier(mode="stage1", model="deepseek-chat", mapping=stage1_mapping),
        reasoner_classifier=_FakeClassifier(
            mode="stage2",
            model="deepseek-reasoner",
            mapping=stage2_mapping,
        ),
        shard_count=2,
        shard_index=1,
        max_stage2_coverage_ratio=1.0,
    )
    queue_path.unlink()
    resumed = generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=output_dir,
        run_id="qv5_rescreen_deepseek_test",
        reviewer="guoyufan",
        review_date="2026-04-20",
        chat_classifier=_ExplodingClassifier(),
        reasoner_classifier=_ExplodingClassifier(),
        shard_count=2,
        shard_index=0,
        resume=True,
    )
    merged = generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=output_dir,
        run_id="qv5_rescreen_deepseek_test",
        reviewer="guoyufan",
        review_date="2026-04-20",
        chat_classifier=_ExplodingClassifier(),
        reasoner_classifier=_ExplodingClassifier(),
        shard_count=2,
        merge_only=True,
    )

    assert resumed["queue_start"] == summary0["queue_start"]
    assert summary0["reasoner_reviewed_count"] >= 1
    assert summary1["reasoner_reviewed_count"] >= 1
    assert merged["full_draft_count"] == 6
    assert merged["delta_count"] == 5
    assert merged["reasoner_reviewed_count"] >= 1
    assert Path(merged["outputs"]["full_draft"]).exists()
    assert Path(merged["outputs"]["priority_true_or_review_needed"]).exists()
    assert Path(merged["outputs"]["priority_reverted_positive_to_false"]).exists()
    assert Path(merged["outputs"]["priority_promoted_to_true_or_review_needed"]).exists()
    assert Path(merged["outputs"]["analysis"]).exists()

    merged_rows = _load_jsonl(Path(merged["outputs"]["full_draft"]))
    assert [row["post_id"] for row in merged_rows] == ["p1", "p2", "p3", "p4", "p5", "p6"]
    assert {row["post_id"] for row in _load_jsonl(Path(merged["outputs"]["priority_true_or_review_needed"]))} == {
        "p4",
        "p5",
    }
