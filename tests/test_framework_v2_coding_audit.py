from __future__ import annotations

import json
from pathlib import Path

from ai4s_legitimacy.analysis.framework_v2_coding_audit import (
    PROVENANCE_MARKER,
    build_framework_v2_coding_audit,
    write_framework_v2_coding_audit,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _summary_payload() -> dict[str, object]:
    return {
        "metadata": {
            "formal_stage": "quality_v5",
            "formal_posts": 1,
            "formal_comments": 0,
            "framework_v2_reviewed_posts": 1,
            "framework_v2_missing_posts": 0,
            "framework_v2_coding_complete": True,
        },
        "tables": {},
    }


def _cross_tabs_payload() -> dict[str, object]:
    return {
        "metadata": {"note": "test"},
        "cross_tabs": {
            "workflow_stage_x_ai_intervention_mode": [
                {
                    "left_code": "A1.2",
                    "left_label": "文献调研与知识整合",
                    "right_code": "F1",
                    "right_label": "信息辅助",
                    "count": 1,
                }
            ]
        },
    }


def _reviewed_row() -> dict[str, object]:
    return {
        "run_id": "qv5_framework_v2_post_review_batch_00",
        "record_id": "p1",
        "post_id": "p1",
        "record_type": "post",
        "review_phase": "post_review_v2",
        "review_status": "reviewed",
        "framework_v2_update": True,
        "framework_v2_reviewer_notes": [PROVENANCE_MARKER],
        "theme_summary": "AI辅助文献综述",
        "claim_units": [
            {
                "practice_unit": "AI辅助文献综述",
                "workflow_stage_codes": ["A1.2"],
                "legitimacy_codes": ["B2"],
                "basis_codes": [{"code": "C1", "evidence": "节省整理时间"}],
                "boundary_codes": [{"code": "D1.10", "evidence": "人工复核"}],
                "ai_intervention_mode_codes": ["F1"],
                "ai_intervention_intensity_codes": ["G1"],
                "evaluation_tension_codes": ["H3"],
                "formal_norm_reference_codes": ["I0"],
                "boundary_mechanism_codes": ["J1"],
                "boundary_result_codes": ["K2"],
                "evidence": ["用AI梳理综述框架但人工复核。"],
            }
        ],
    }


def test_framework_v2_coding_audit_writes_report_for_valid_rows(tmp_path: Path) -> None:
    post_master = tmp_path / "post_review_v2_master.jsonl"
    summary_tables = tmp_path / "framework_v2_summary_tables.json"
    cross_tabs = tmp_path / "cross_tabs_v2.json"
    output_json = tmp_path / "framework_v2_coding_audit_report.json"
    output_md = tmp_path / "framework_v2_coding_audit_report.md"
    _write_jsonl(post_master, [_reviewed_row()])
    _write_json(summary_tables, _summary_payload())
    _write_json(cross_tabs, _cross_tabs_payload())

    result = write_framework_v2_coding_audit(
        output_json_path=output_json,
        output_md_path=output_md,
        post_master_path=post_master,
        summary_tables_path=summary_tables,
        cross_tabs_path=cross_tabs,
    )

    audit = json.loads(output_json.read_text(encoding="utf-8"))
    report = output_md.read_text(encoding="utf-8")
    assert result["mechanical_checks"]["status"] == "ok"
    assert audit["metadata"]["formal_posts"] == 1
    assert audit["metadata"]["formal_comments"] == 0
    assert audit["metadata"]["claim_units_with_framework_v2_fields"] == 1
    assert audit["code_distributions"]["F"][0]["code"] == "F1"
    assert "不能替代逐条语义复核" in report
    assert "用户授权接受 AI 辅助编码草稿并保留 provenance" in report


def test_framework_v2_coding_audit_flags_invalid_i0_mixed_reference(
    tmp_path: Path,
) -> None:
    post_master = tmp_path / "post_review_v2_master.jsonl"
    summary_tables = tmp_path / "framework_v2_summary_tables.json"
    cross_tabs = tmp_path / "cross_tabs_v2.json"
    row = _reviewed_row()
    row["claim_units"][0]["formal_norm_reference_codes"] = ["I0", "I1"]  # type: ignore[index]
    _write_jsonl(post_master, [row])
    _write_json(summary_tables, _summary_payload())
    _write_json(cross_tabs, _cross_tabs_payload())

    audit = build_framework_v2_coding_audit(
        post_master_path=post_master,
        summary_tables_path=summary_tables,
        cross_tabs_path=cross_tabs,
    )

    assert audit["mechanical_checks"]["status"] == "review_needed"
    assert audit["mechanical_checks"]["violation_count"] == 1
    assert "I0 mixed with formal references" in audit["mechanical_checks"]["violations"][0]
