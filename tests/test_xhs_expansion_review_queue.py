from __future__ import annotations

import json
from pathlib import Path

from ai4s_legitimacy.collection.xhs_expansion_review_queue import (
    HUMAN_REVIEW_FIELDS,
    backfill_candidate_query_metadata,
    prepare_xhs_expansion_review_queue,
)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_prepare_xhs_expansion_review_queue_keeps_human_fields_empty(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate300.jsonl"
    summary_path = tmp_path / "candidate300.summary.json"
    queue_path = tmp_path / "review_queues" / "xhs_expansion_candidate_v1.review_queue.jsonl"
    template_path = tmp_path / "reviewed" / "xhs_expansion_candidate_v1.review_template.jsonl"
    report_path = tmp_path / "review_queue.report.md"
    candidate_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "post_id": "p1",
                        "record_id": "p1",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p1",
                        "theme_summary": "AI文献综述",
                        "source_text": "我用AI辅助科研做文献综述，但需要人工核查。",
                        "author_id": "hashed-author",
                        "created_at": "2025-03-15",
                        "query": "AI文献综述",
                        "query_group": "B. 文献处理与知识整合类",
                        "source_method": "opencli_xiaohongshu",
                        "decision": "纳入",
                        "decision_reason": ["R12: 纳入：明确 AI 进入具体科研工作流环节。"],
                        "formal_result_scope": False,
                        "quality_v5_formal_scope": False,
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "post_id": "p2",
                        "record_id": "p2",
                        "platform": "xiaohongshu",
                        "post_url": "https://www.xiaohongshu.com/explore/p2",
                        "theme_summary": "泛AI工具",
                        "source_text": "工具合集。",
                        "author_id": "",
                        "created_at": "2025-04-01",
                        "decision": "剔除",
                        "decision_reason": ["R8: 更像 AI 工具合集。"],
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
    summary_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-28T12:00:00+00:00",
                "row_count": 2,
                "provider_used": "opencli_xiaohongshu",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    prepare_xhs_expansion_review_queue(
        candidate_path=candidate_path,
        summary_path=summary_path,
        queue_path=queue_path,
        template_path=template_path,
        report_path=report_path,
    )

    queue_rows = _read_jsonl(queue_path)
    template_rows = _read_jsonl(template_path)
    assert len(queue_rows) == 2
    assert len(template_rows) == 2
    assert queue_rows[0]["candidate_id"] == "xhs_expansion_candidate_v1:p1"
    assert queue_rows[0]["preliminary_decision"] == "include"
    assert queue_rows[1]["preliminary_decision"] == "exclude"
    assert queue_rows[0]["query"] == "AI文献综述"
    assert queue_rows[1]["query"] is None
    assert queue_rows[0]["author_name_masked"] is None
    assert queue_rows[0]["author_id_hashed"] == "hashed-author"
    assert queue_rows[0]["capture_date"] == "2026-04-28"
    assert queue_rows[0]["public_access_status"] == "public_direct_fetch_ok"
    assert queue_rows[0]["formal_result_scope"] is False
    assert queue_rows[0]["quality_v5_formal_scope"] is False
    assert queue_rows[0]["review_required_fields"] == HUMAN_REVIEW_FIELDS
    for row in queue_rows + template_rows:
        for field in HUMAN_REVIEW_FIELDS:
            assert row[field] is None
    assert "preliminary_decision` 只是规则预筛建议" in report_path.read_text(encoding="utf-8")


def test_backfill_candidate_query_metadata_uses_summary_sequence() -> None:
    rows = [
        {"record_id": "p1", "source_text": "row 1"},
        {"record_id": "p2", "source_text": "row 2", "query": "保留原始query"},
        {"record_id": "p3", "source_text": "row 3"},
    ]
    summary = {
        "query_stats": [
            {
                "query": "AI文献综述",
                "query_name": "query_file_b_01",
                "category": "B. 文献处理与知识整合类",
                "verified_kept": 2,
            },
            {
                "query": "AI统计分析",
                "query_name": "query_file_d_01",
                "category": "D. 数据分析与代码类",
                "verified_kept": 1,
            },
        ]
    }

    backfilled = backfill_candidate_query_metadata(rows, summary=summary)

    assert backfilled[0]["query"] == "AI文献综述"
    assert backfilled[0]["query_group"] == "B. 文献处理与知识整合类"
    assert backfilled[0]["query_metadata_source"] == "candidate300_summary_sequence_backfill"
    assert backfilled[1]["query"] == "保留原始query"
    assert backfilled[1]["query_group"] == "B. 文献处理与知识整合类"
    assert backfilled[2]["query"] == "AI统计分析"
    assert backfilled[2]["query_group"] == "D. 数据分析与代码类"
