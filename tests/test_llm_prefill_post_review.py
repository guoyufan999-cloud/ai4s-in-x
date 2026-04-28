from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import validate_canonical_row
from ai4s_legitimacy.collection.deepseek_client import DeepSeekClient
from ai4s_legitimacy.collection.llm_prefill_post_review import (
    PostReviewBatchPrefiller,
    generate_post_review_prefill_draft,
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_generate_post_review_prefill_draft_writes_valid_canonical_rows(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "post_review_v2.batch_00.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p1",
                "post_id": "p1",
                "source_text": "我用 ChatGPT 帮我梳理综述框架，但最后自己核查并重写。",
                "context_used": "none",
                "context_text": "",
                "theme_summary": "用 ChatGPT 梳理综述框架",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "discursive_mode": "experience_share",
                "practice_status": "actual_use",
                "speaker_position_claimed": "graduate_student",
                "evidence_master": ["用 ChatGPT 梳理综述框架"],
                "actor_type": "graduate_student",
                "qs_broad_subject": "",
                "review_status": "reviewed",
            },
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p2",
                "post_id": "p2",
                "source_text": "AI科研神器推荐，欢迎咨询。",
                "context_used": "none",
                "context_text": "",
                "theme_summary": "AI科研神器推荐",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "discursive_mode": "unclear",
                "practice_status": "unclear",
                "speaker_position_claimed": "unclear",
                "evidence_master": ["AI科研神器推荐"],
                "actor_type": "tool_vendor_or_promotional",
                "qs_broad_subject": "",
                "review_status": "reviewed",
            },
        ],
    )

    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "items": [
                                            {
                                                "batch_item_id": "item_000",
                                                "decision": "纳入",
                                                "decision_reason_code": "R12",
                                                "decision_reason_note": "帖子明确展示 AI 辅助文献综述，并要求人工核查。",
                                                "theme_summary": "AI辅助文献综述框架整理",
                                                "target_practice_summary": "AI辅助文献综述",
                                                "discursive_mode": "experience_share",
                                                "practice_status": "actual_use",
                                                "speaker_position_claimed": "graduate_student",
                                                "qs_broad_subject": "Engineering & Technology",
                                                "evidence_master": [
                                                    "我用 ChatGPT 帮我梳理综述框架，但最后自己核查并重写。"
                                                ],
                                                "claim_units": [
                                                    {
                                                        "practice_unit": "AI辅助文献综述",
                                                        "workflow_stage_codes": ["A1.2"],
                                                        "legitimacy_codes": ["B2"],
                                                        "basis_codes": [
                                                            {
                                                                "code": "C1",
                                                                "evidence": "帮我梳理综述框架",
                                                            },
                                                            {
                                                                "code": "C7",
                                                                "evidence": "最后自己核查并重写",
                                                            },
                                                        ],
                                                        "boundary_codes": [
                                                            {
                                                                "code": "D1.2",
                                                                "evidence": "最后自己核查并重写",
                                                            }
                                                        ],
                                                        "boundary_mode_codes": [
                                                            {
                                                                "code": "D2.5",
                                                                "evidence": "最后自己核查并重写",
                                                            }
                                                        ],
                                                        "evidence": [
                                                            "我用 ChatGPT 帮我梳理综述框架，但最后自己核查并重写。"
                                                        ],
                                                    }
                                                ],
                                                "interaction_event_present": "不适用",
                                                "interaction_role": "unclear",
                                                "interaction_target_claim_summary": "",
                                                "interaction_event_codes": [],
                                                "interaction_event_basis_codes": [],
                                                "interaction_event_outcome": "",
                                                "interaction_evidence": [],
                                                "notes_ambiguity": "否",
                                                "notes_confidence": "高",
                                                "review_points": [],
                                                "mechanism_eligible": "否",
                                                "mechanism_notes": [],
                                                "comparison_keys": [],
                                                "api_confidence": 0.92,
                                            },
                                            {
                                                "batch_item_id": "item_001",
                                                "decision": "剔除",
                                                "decision_reason_code": "R8",
                                                "decision_reason_note": "更像工具宣传，缺少具体科研工作流实践。",
                                                "theme_summary": "AI科研工具宣传",
                                                "target_practice_summary": "",
                                                "discursive_mode": "criticism",
                                                "practice_status": "unclear",
                                                "speaker_position_claimed": "unclear",
                                                "qs_broad_subject": "",
                                                "evidence_master": ["AI科研神器推荐，欢迎咨询。"],
                                                "claim_units": [],
                                                "interaction_event_present": "不适用",
                                                "interaction_role": "unclear",
                                                "interaction_target_claim_summary": "",
                                                "interaction_event_codes": [],
                                                "interaction_event_basis_codes": [],
                                                "interaction_event_outcome": "",
                                                "interaction_evidence": [],
                                                "notes_ambiguity": "否",
                                                "notes_confidence": "中",
                                                "review_points": [],
                                                "mechanism_eligible": "否",
                                                "mechanism_notes": [],
                                                "comparison_keys": [],
                                                "api_confidence": 0.74,
                                            },
                                        ]
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                }
            )
        ]
    )
    client = DeepSeekClient(api_key="test-key", transport=transport)

    summary = generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=tmp_path / "reviewed" / "post_review_v2.batch_00.ai_draft.jsonl",
        run_id="qv5_post_review_v2_batch_00_deepseek_prefill_v1",
        reviewer="guoyufan",
        review_date="2026-04-23",
        prefiller=PostReviewBatchPrefiller(client=client, model="deepseek-chat"),
        batch_size=2,
        max_workers=1,
    )

    draft_rows = _load_jsonl(Path(summary["output_path"]))

    assert summary["status"] == "ok"
    assert summary["draft_count"] == 2
    assert summary["included_count"] == 1
    assert summary["excluded_count"] == 1
    assert transport.requests
    assert draft_rows[0]["review_status"] == "unreviewed"
    assert draft_rows[0]["api_assistance"]["used"] == "是"
    assert draft_rows[0]["decision"] == "纳入"
    assert draft_rows[0]["qs_broad_subject"] == "Engineering & Technology"
    assert draft_rows[0]["workflow_dimension"]["secondary_stage"] == ["A1.2"]
    assert draft_rows[0]["legitimacy_evaluation"]["direction"] == ["B2"]
    assert draft_rows[0]["boundary_expression"]["present"] == "是"
    assert draft_rows[1]["decision"] == "剔除"
    for row in draft_rows:
        assert validate_canonical_row(row)["review_status"] == "unreviewed"


def test_generate_post_review_prefill_draft_falls_back_on_invalid_batch_response(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "post_review_v2.batch_01.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p3",
                "post_id": "p3",
                "source_text": "Cursor 帮我调科研分析代码。",
                "context_used": "none",
                "context_text": "",
                "theme_summary": "Cursor 帮我调科研分析代码",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "review_status": "reviewed",
            }
        ],
    )

    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"unexpected": []}, ensure_ascii=False)
                            }
                        }
                    ],
                }
            )
        ]
    )
    client = DeepSeekClient(api_key="test-key", transport=transport)

    summary = generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=tmp_path / "reviewed" / "post_review_v2.batch_01.ai_draft.jsonl",
        reviewer="guoyufan",
        review_date="2026-04-23",
        prefiller=PostReviewBatchPrefiller(client=client, model="deepseek-chat"),
        batch_size=1,
        max_workers=1,
    )

    draft_rows = _load_jsonl(Path(summary["output_path"]))

    assert summary["status"] == "partial_fallback"
    assert summary["review_needed_count"] == 1
    assert summary["fallback_batch_errors"] == ["prefill_batch_error: ValueError"]
    assert draft_rows[0]["decision"] == "待复核"
    assert draft_rows[0]["api_assistance"]["used"] == "否"
    assert draft_rows[0]["api_assistance"]["api_confidence"] == "不可用"
    assert draft_rows[0]["notes"]["ambiguity"] == "是"
    assert "prefill_batch_error" in draft_rows[0]["decision_reason"][0]


def test_generate_post_review_prefill_draft_downgrades_included_rows_without_meaningful_claim_units(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "post_review_v2.batch_02.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p4",
                "post_id": "p4",
                "source_text": "分享我如何用 GPT 帮忙找选题。",
                "context_used": "none",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "review_status": "reviewed",
            }
        ],
    )

    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "items": [
                                            {
                                                "batch_item_id": "item_000",
                                                "decision": "纳入",
                                                "decision_reason_code": "R1",
                                                "decision_reason_note": "帖子讲了 GPT 找选题。",
                                                "theme_summary": "GPT找选题",
                                                "target_practice_summary": "GPT辅助选题",
                                                "discursive_mode": "experience_share",
                                                "practice_status": "actual_use",
                                                "speaker_position_claimed": "unclear",
                                                "qs_broad_subject": "",
                                                "evidence_master": ["分享我如何用 GPT 帮忙找选题。"],
                                                "claim_units": [
                                                    {
                                                        "practice_unit": "",
                                                        "workflow_stage_codes": [],
                                                        "legitimacy_codes": [],
                                                        "basis_codes": [],
                                                        "boundary_codes": [],
                                                        "boundary_mode_codes": [],
                                                        "evidence": [],
                                                    }
                                                ],
                                                "interaction_event_present": "不适用",
                                                "interaction_role": "unclear",
                                                "interaction_target_claim_summary": "",
                                                "interaction_event_codes": [],
                                                "interaction_event_basis_codes": [],
                                                "interaction_event_outcome": "",
                                                "interaction_evidence": [],
                                                "notes_ambiguity": "否",
                                                "notes_confidence": "高",
                                                "review_points": [],
                                                "mechanism_eligible": "否",
                                                "mechanism_notes": [],
                                                "comparison_keys": [],
                                                "api_confidence": 0.91,
                                            }
                                        ]
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                }
            )
        ]
    )
    client = DeepSeekClient(api_key="test-key", transport=transport)

    summary = generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=tmp_path / "reviewed" / "post_review_v2.batch_02.ai_draft.jsonl",
        reviewer="guoyufan",
        review_date="2026-04-23",
        prefiller=PostReviewBatchPrefiller(client=client, model="deepseek-chat"),
        batch_size=1,
        max_workers=1,
    )

    draft_rows = _load_jsonl(Path(summary["output_path"]))
    assert summary["included_count"] == 0
    assert summary["review_needed_count"] == 1
    assert draft_rows[0]["decision"] == "待复核"
    assert draft_rows[0]["claim_units"] == []
    assert "有效的 claim_units" in draft_rows[0]["decision_reason"][0]


def test_generate_post_review_prefill_draft_downgrades_included_rows_without_workflow_codes(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "post_review_v2.batch_03.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p5",
                "post_id": "p5",
                "source_text": "我用 GPT 快速查某领域文献，并自己复核。",
                "context_used": "none",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "review_status": "reviewed",
            }
        ],
    )

    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "items": [
                                            {
                                                "batch_item_id": "item_000",
                                                "decision": "纳入",
                                                "decision_reason_code": "R12",
                                                "decision_reason_note": "帖子展示了AI辅助文献处理。",
                                                "theme_summary": "GPT辅助找文献",
                                                "target_practice_summary": "GPT辅助文献检索",
                                                "discursive_mode": "experience_share",
                                                "practice_status": "actual_use",
                                                "speaker_position_claimed": "unclear",
                                                "qs_broad_subject": "uncertain",
                                                "evidence_master": ["我用 GPT 快速查某领域文献，并自己复核。"],
                                                "claim_units": [
                                                    {
                                                        "practice_unit": "GPT辅助文献检索",
                                                        "workflow_stage_codes": [],
                                                        "legitimacy_codes": ["B2"],
                                                        "basis_codes": [
                                                            {"code": "C1", "evidence": "快速查某领域文献"}
                                                        ],
                                                        "boundary_codes": [],
                                                        "boundary_mode_codes": [],
                                                        "evidence": ["我用 GPT 快速查某领域文献，并自己复核。"],
                                                    }
                                                ],
                                                "interaction_event_present": "不适用",
                                                "interaction_role": "unclear",
                                                "interaction_target_claim_summary": "",
                                                "interaction_event_codes": [],
                                                "interaction_event_basis_codes": [],
                                                "interaction_event_outcome": "",
                                                "interaction_evidence": [],
                                                "notes_ambiguity": "否",
                                                "notes_confidence": "中",
                                                "review_points": [],
                                                "mechanism_eligible": "否",
                                                "mechanism_notes": [],
                                                "comparison_keys": [],
                                                "api_confidence": 0.8,
                                            }
                                        ]
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                }
            )
        ]
    )
    client = DeepSeekClient(api_key="test-key", transport=transport)

    summary = generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=tmp_path / "reviewed" / "post_review_v2.batch_03.ai_draft.jsonl",
        reviewer="guoyufan",
        review_date="2026-04-23",
        prefiller=PostReviewBatchPrefiller(client=client, model="deepseek-chat"),
        batch_size=1,
        max_workers=1,
    )

    draft_rows = _load_jsonl(Path(summary["output_path"]))
    assert summary["included_count"] == 0
    assert draft_rows[0]["decision"] == "待复核"
    assert draft_rows[0]["claim_units"] == []
    assert "workflow_stage_codes" in draft_rows[0]["decision_reason"][0]


def test_generate_post_review_prefill_draft_defaults_missing_legitimacy_to_b0_for_included_rows(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "post_review_v2.batch_04.jsonl"
    _write_jsonl(
        queue_path,
        [
            {
                "review_phase": "post_review_v2",
                "record_type": "post",
                "record_id": "p6",
                "post_id": "p6",
                "source_text": "我用 ChatGPT 帮忙梳理论文综述框架。",
                "context_used": "none",
                "decision": "待复核",
                "decision_reason": ["R11: 可能相关但证据不足，建议复核。"],
                "review_status": "reviewed",
            }
        ],
    )

    transport = _TransportSequence(
        [
            _FakeResponse(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "items": [
                                            {
                                                "batch_item_id": "item_000",
                                                "decision": "纳入",
                                                "decision_reason_code": "R12",
                                                "decision_reason_note": "帖子展示了AI辅助文献综述。",
                                                "theme_summary": "ChatGPT辅助综述框架整理",
                                                "target_practice_summary": "AI辅助文献综述",
                                                "discursive_mode": "experience_share",
                                                "practice_status": "actual_use",
                                                "speaker_position_claimed": "graduate_student",
                                                "qs_broad_subject": "Engineering & Technology",
                                                "evidence_master": ["我用 ChatGPT 帮忙梳理论文综述框架。"],
                                                "claim_units": [
                                                    {
                                                        "practice_unit": "AI辅助文献综述",
                                                        "workflow_stage_codes": ["A1.2"],
                                                        "legitimacy_codes": [],
                                                        "basis_codes": [],
                                                        "boundary_codes": [],
                                                        "boundary_mode_codes": [],
                                                        "evidence": ["我用 ChatGPT 帮忙梳理论文综述框架。"],
                                                    }
                                                ],
                                                "interaction_event_present": "不适用",
                                                "interaction_role": "unclear",
                                                "interaction_target_claim_summary": "",
                                                "interaction_event_codes": [],
                                                "interaction_event_basis_codes": [],
                                                "interaction_event_outcome": "",
                                                "interaction_evidence": [],
                                                "notes_ambiguity": "否",
                                                "notes_confidence": "中",
                                                "review_points": [],
                                                "mechanism_eligible": "否",
                                                "mechanism_notes": [],
                                                "comparison_keys": [],
                                                "api_confidence": 0.78,
                                            }
                                        ]
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ],
                }
            )
        ]
    )
    client = DeepSeekClient(api_key="test-key", transport=transport)

    summary = generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=tmp_path / "reviewed" / "post_review_v2.batch_04.ai_draft.jsonl",
        reviewer="guoyufan",
        review_date="2026-04-23",
        prefiller=PostReviewBatchPrefiller(client=client, model="deepseek-chat"),
        batch_size=1,
        max_workers=1,
    )

    draft_rows = _load_jsonl(Path(summary["output_path"]))
    assert summary["included_count"] == 1
    assert draft_rows[0]["decision"] == "纳入"
    assert draft_rows[0]["claim_units"][0]["legitimacy_codes"] == ["B0"]
    assert draft_rows[0]["legitimacy_evaluation"]["direction"] == ["B0"]
