from __future__ import annotations

import json
from pathlib import Path

from ai4s_legitimacy.analysis.xhs_expansion_supplemental_analysis import (
    generate_xhs_expansion_supplemental_analysis,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_xhs_expansion_supplemental_analysis_writes_report_and_tables(tmp_path: Path) -> None:
    staged_path = tmp_path / "staged.jsonl"
    reviewed_path = tmp_path / "reviewed.jsonl"
    report_path = tmp_path / "reports" / "supplemental_analysis.md"
    table_dir = tmp_path / "tables"
    _write_jsonl(
        staged_path,
        [
            {
                "candidate_id": "xhs_expansion_candidate_v1:p1",
                "final_decision": "include",
                "post_date": "2026-04-10",
                "query_group": "B. 文献处理与知识整合类",
                "discourse_context": "tool_recommendation",
                "workflow_stage": "literature_processing",
                "ai_intervention_mode": "information_assistance",
                "ai_intervention_intensity": "low_assistance",
                "normative_evaluation_signal": "efficiency_positive",
                "boundary_signal": "none_or_unclear",
            }
        ],
    )
    _write_jsonl(
        reviewed_path,
        [
            {"candidate_id": "xhs_expansion_candidate_v1:p1", "final_decision": "include"},
            {"candidate_id": "xhs_expansion_candidate_v1:p2", "final_decision": "review_needed"},
            {"candidate_id": "xhs_expansion_candidate_v1:p3", "final_decision": "exclude"},
        ],
    )

    summary = generate_xhs_expansion_supplemental_analysis(
        staged_path=staged_path,
        reviewed_path=reviewed_path,
        db_path=tmp_path / "missing.sqlite3",
        report_path=report_path,
        table_dir=table_dir,
    )

    assert summary["source_scope"] == "xhs_expansion_candidate_v1"
    assert summary["quality_v5_formal"] is False
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "只描述 `xhs_expansion_candidate_v1` 补充候选样本结构" in report
    assert "不建议直接并入 `quality_v5` 主结果" in report
    decision_rows = json.loads(
        (table_dir / "supplemental_decision_counts.json").read_text(encoding="utf-8")
    )
    assert {row["final_decision"]: row["count"] for row in decision_rows} == {
        "include": 1,
        "review_needed": 1,
        "exclude": 1,
    }
    assert (table_dir / "supplemental_research_theme_distribution.csv").exists()
    assert (table_dir / "supplemental_analysis_summary.json").exists()
