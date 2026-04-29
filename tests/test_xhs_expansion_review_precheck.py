from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai4s_legitimacy.collection.xhs_expansion_review_precheck import (
    complete_review_from_queue,
    run_reviewed_import_precheck,
)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_xhs_expansion_review_precheck_creates_reviewed_and_staged_jsonl(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "review_queue.jsonl"
    reviewed_path = tmp_path / "reviewed.jsonl"
    precheck_json = tmp_path / "precheck.json"
    precheck_md = tmp_path / "precheck.md"
    staged_path = tmp_path / "staged" / "accepted.jsonl"
    queue_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "candidate_id": "xhs_expansion_candidate_v1:p1",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p1",
                        "note_id": "p1",
                        "title": "AI文献综述",
                        "content_text": (
                            "我用AI辅助科研做文献综述，先让工具整理主题脉络、归纳关键词和生成阅读顺序，"
                            "但每一条引用仍需要回到原文核查，不能直接把AI总结当作论文证据。"
                            "我通常会把AI输出和数据库检索结果对照，再决定是否纳入自己的研究笔记。"
                        ),
                        "author_name_masked": None,
                        "author_id_hashed": "hash1",
                        "post_date": "2025-03-15",
                        "capture_date": "2026-04-28",
                        "query": "AI文献综述",
                        "query_group": "B. 文献处理与知识整合类",
                        "source_method": "opencli_xiaohongshu",
                        "preliminary_decision": "include",
                        "preliminary_reason": ["R12"],
                        "duplicate_status": "unique_after_sampling_dedup",
                        "public_access_status": "public_direct_fetch_ok",
                        "formal_result_scope": False,
                        "quality_v5_formal_scope": False,
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "candidate_id": "xhs_expansion_candidate_v1:p2",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p2",
                        "note_id": "p2",
                        "title": "AI办公训练营",
                        "content_text": "AI办公训练营立即咨询领取课程资料，适合职场提效。",
                        "author_name_masked": None,
                        "author_id_hashed": "hash2",
                        "post_date": "2025-03-16",
                        "capture_date": "2026-04-28",
                        "query": "AI工具",
                        "query_group": "A. AI科研总体类",
                        "source_method": "opencli_xiaohongshu",
                        "preliminary_decision": "include",
                        "preliminary_reason": ["R12"],
                        "duplicate_status": "unique_after_sampling_dedup",
                        "public_access_status": "public_direct_fetch_ok",
                        "formal_result_scope": False,
                        "quality_v5_formal_scope": False,
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    precheck_paths = run_reviewed_import_precheck(
        reviewed_path=reviewed_path,
        queue_path=queue_path,
        db_path=tmp_path / "missing.sqlite3",
        precheck_json_path=precheck_json,
        precheck_md_path=precheck_md,
        staged_accepted_path=staged_path,
    )

    assert precheck_paths == (precheck_json, precheck_md, staged_path)
    reviewed_rows = _read_jsonl(reviewed_path)
    staged_rows = _read_jsonl(staged_path)
    report = json.loads(precheck_json.read_text(encoding="utf-8"))
    assert reviewed_rows[0]["final_decision"] == "include"
    assert reviewed_rows[1]["final_decision"] == "exclude"
    assert len(staged_rows) == 1
    assert staged_rows[0]["staging_metadata"] == {
        **staged_rows[0]["staging_metadata"],
        "source_scope": "xhs_expansion_candidate_v1",
        "formal_scope": False,
        "quality_v5_formal": False,
        "supplemental_candidate": True,
    }
    assert report["status"] == "pass"
    assert report["accepted_count"] == 1
    assert "未写入研究主库" in precheck_md.read_text(encoding="utf-8")


def test_xhs_expansion_review_precheck_blocks_invalid_reviewed_rows(tmp_path: Path) -> None:
    reviewed_path = tmp_path / "reviewed.jsonl"
    reviewed_path.write_text(
        json.dumps(
            {
                "candidate_id": "xhs_expansion_candidate_v1:p1",
                "platform": "xiaohongshu",
                "post_url": "",
                "note_id": "p1",
                "title": "短文本",
                "content_text": "太短",
                "author_name_masked": None,
                "post_date": "",
                "capture_date": "2026-04-28",
                "query_group": None,
                "final_decision": "include",
                "public_access_status": "public_direct_fetch_ok",
                "formal_result_scope": False,
                "quality_v5_formal_scope": False,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    _, _, staged_path = run_reviewed_import_precheck(
        reviewed_path=reviewed_path,
        queue_path=tmp_path / "missing_queue.jsonl",
        db_path=tmp_path / "missing.sqlite3",
        precheck_json_path=tmp_path / "precheck.json",
        precheck_md_path=tmp_path / "precheck.md",
        staged_accepted_path=tmp_path / "staged.jsonl",
        create_reviewed_if_missing=False,
    )

    report = json.loads((tmp_path / "precheck.json").read_text(encoding="utf-8"))
    assert staged_path is None
    assert report["status"] == "fail"
    assert report["critical_issue_count"] >= 2
    assert report["warning_counts"] == {"missing_post_date": 1, "missing_query_group": 1}


def test_xhs_expansion_review_precheck_warns_for_excluded_public_boundary_rows(
    tmp_path: Path,
) -> None:
    reviewed_path = tmp_path / "reviewed.jsonl"
    reviewed_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "candidate_id": "xhs_expansion_candidate_v1:p1",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p1",
                        "note_id": "p1",
                        "title": "AI文献阅读",
                        "content_text": (
                            "我用AI辅助阅读英文文献，先生成摘要和关键词，再人工回到原文核查。"
                            "这个流程主要用于提高阅读效率，不直接替代自己的判断。"
                            "如果摘要中出现没有出处的判断，我会重新检索数据库并记录核查过程。"
                        ),
                        "author_name_masked": None,
                        "post_date": "2026-04-28",
                        "query_group": "B. 文献处理与知识整合类",
                        "final_decision": "include",
                        "public_access_status": "public_direct_fetch_ok",
                        "formal_result_scope": False,
                        "quality_v5_formal_scope": False,
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "candidate_id": "xhs_expansion_candidate_v1:p2",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p2",
                        "note_id": "p2",
                        "title": "微信聊天记录提取",
                        "content_text": "微信聊天记录提取 + AI 分析，涉及非公开聊天记录。",
                        "author_name_masked": None,
                        "post_date": "2026-04-28",
                        "query_group": "D. 数据分析与代码类",
                        "final_decision": "exclude",
                        "public_access_status": "public_direct_fetch_ok",
                        "formal_result_scope": False,
                        "quality_v5_formal_scope": False,
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _, _, staged_path = run_reviewed_import_precheck(
        reviewed_path=reviewed_path,
        queue_path=tmp_path / "missing_queue.jsonl",
        db_path=tmp_path / "missing.sqlite3",
        precheck_json_path=tmp_path / "precheck.json",
        precheck_md_path=tmp_path / "precheck.md",
        staged_accepted_path=tmp_path / "staged.jsonl",
        create_reviewed_if_missing=False,
    )

    report = json.loads((tmp_path / "precheck.json").read_text(encoding="utf-8"))
    assert staged_path == tmp_path / "staged.jsonl"
    assert report["status"] == "pass_with_warnings"
    assert report["accepted_count"] == 1
    assert report["critical_issue_count"] == 0
    assert report["warning_counts"] == {"public_boundary_issue": 1}


def test_xhs_expansion_review_precheck_warns_for_excluded_existing_duplicates(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE posts (post_id TEXT, legacy_note_id TEXT, post_url TEXT)"
        )
        connection.execute(
            "INSERT INTO posts VALUES (?, ?, ?)",
            ("p1", None, "https://www.xiaohongshu.com/explore/p1"),
        )

    reviewed_path = tmp_path / "reviewed.jsonl"
    reviewed_path.write_text(
        json.dumps(
            {
                "candidate_id": "xhs_expansion_candidate_v1:p1",
                "platform": "xiaohongshu",
                "post_url": "https://www.xiaohongshu.com/explore/p1",
                "note_id": "p1",
                "title": "AI文献阅读",
                "content_text": (
                    "我用AI辅助阅读英文文献，先生成摘要和关键词，再人工回到原文核查。"
                    "该候选已存在于研究主库，因此不应再次进入 supplemental staging。"
                ),
                "author_name_masked": None,
                "post_date": "2026-04-28",
                "query_group": "B. 文献处理与知识整合类",
                "final_decision": "exclude",
                "exclusion_reason": "duplicate_existing_post",
                "duplicate_status": "duplicate_existing_post",
                "public_access_status": "public_direct_fetch_ok",
                "formal_result_scope": False,
                "quality_v5_formal_scope": False,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    _, _, staged_path = run_reviewed_import_precheck(
        reviewed_path=reviewed_path,
        queue_path=tmp_path / "missing_queue.jsonl",
        db_path=db_path,
        precheck_json_path=tmp_path / "precheck.json",
        precheck_md_path=tmp_path / "precheck.md",
        staged_accepted_path=tmp_path / "staged.jsonl",
        create_reviewed_if_missing=False,
    )

    report = json.loads((tmp_path / "precheck.json").read_text(encoding="utf-8"))
    assert staged_path == tmp_path / "staged.jsonl"
    assert report["status"] == "pass_with_warnings"
    assert report["accepted_count"] == 0
    assert report["critical_issue_count"] == 0
    assert report["warning_counts"] == {"duplicate_existing_post": 1}


def test_complete_review_from_queue_preserves_review_fields(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.jsonl"
    reviewed_path = tmp_path / "reviewed.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "candidate_id": "xhs_expansion_candidate_v1:p1",
                "post_url": "https://www.xiaohongshu.com/explore/p1",
                "title": "AI统计分析",
                "content_text": (
                    "我用AI做科研数据分析和统计分析，主要让它辅助解释代码报错、整理变量处理步骤，"
                    "最终仍然人工检查统计模型、结果含义和论文中的表述。"
                    "如果模型假设或变量口径不清楚，我不会直接采用AI给出的解释。"
                ),
                "preliminary_decision": "include",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    complete_review_from_queue(queue_path=queue_path, reviewed_path=reviewed_path)
    row = _read_jsonl(reviewed_path)[0]
    assert row["final_decision"] == "include"
    assert row["workflow_stage"] == "data_analysis_or_code"
    assert row["review_status"] == "reviewed"
