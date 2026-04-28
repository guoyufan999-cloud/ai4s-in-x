from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest

from ai4s_legitimacy.analysis.framework_v2_materials import (
    COMPLETE_V2_FIELD_NOTE,
    generate_framework_v2_materials,
)
from ai4s_legitimacy.collection.framework_v2_review_batches import (
    prepare_framework_v2_review_batches,
)
from ai4s_legitimacy.collection.reviewed_import import import_reviewed_file
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db


def _baseline_payload(post_id: str, *, run_id: str = "baseline-post-review") -> dict[str, object]:
    return {
        "run_id": run_id,
        "review_phase": "post_review_v2",
        "review_status": "reviewed",
        "reviewer": "human-a",
        "review_date": "2026-04-18",
        "record_type": "post",
        "record_id": post_id,
        "post_id": post_id,
        "decision": "纳入",
        "decision_reason": ["R12: 明确展示 AI 辅助文献综述。"],
        "source_text": "用AI梳理综述框架但人工复核。",
        "workflow_dimension": {
            "primary_dimension": ["A1"],
            "secondary_stage": ["A1.2"],
            "evidence": ["用AI梳理综述框架"],
        },
        "legitimacy_evaluation": {
            "direction": ["B2"],
            "basis": ["C1"],
            "evidence": ["节省综述整理时间"],
        },
        "boundary_expression": {
            "present": "是",
            "boundary_content_codes": ["D1.10"],
            "boundary_expression_mode_codes": [],
            "evidence": ["人工复核"],
        },
        "claim_units": [
            {
                "practice_unit": "AI辅助文献综述",
                "workflow_stage_codes": ["A1.2"],
                "legitimacy_codes": ["B2"],
                "basis_codes": [{"code": "C1", "evidence": "节省综述整理时间"}],
                "boundary_codes": [{"code": "D1.10", "evidence": "人工复核"}],
                "boundary_mode_codes": [],
                "evidence": ["用AI梳理综述框架但人工复核。"],
            }
        ],
    }


def _seed_formal_posts_with_post_review_payloads(db_path: Path, *, count: int) -> None:
    init_sqlite_db(db_path, SCHEMA_PATH, views_sql=render_views_sql())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO import_batches (batch_name, source_description) VALUES ('test_batch', 'test')"
        )
        connection.execute(
            "INSERT INTO platform_sources (platform_code, platform_name) VALUES ('xiaohongshu', '小红书')"
        )
        connection.execute(
            """
            INSERT INTO review_runs (
                run_id, review_phase, reviewer, review_date, source_file
            ) VALUES ('baseline-post-review', 'post_review_v2', 'human-a', '2026-04-18', 'seed.jsonl')
            """
        )
        for index in range(count):
            post_id = f"p{index + 1:03d}"
            connection.execute(
                """
                INSERT INTO posts (
                    post_id, platform, legacy_crawl_status, post_date, sample_status,
                    actor_type, qs_broad_subject, workflow_domain, workflow_stage,
                    primary_legitimacy_stance, decision, review_status,
                    title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                    import_batch_id
                ) VALUES (
                    ?, 'xiaohongshu', 'crawled', '2024-01-15', 'true',
                    'graduate_student', 'Engineering & Technology', 'P', '文献调研与知识整合',
                    '有条件接受', '纳入', 'reviewed',
                    '标题', '用AI梳理综述框架但人工复核', '["ChatGPT"]', '[]', '["efficiency"]',
                    1
                )
                """,
                (post_id,),
            )
            connection.execute(
                """
                INSERT INTO claim_units (
                    record_type, record_id, claim_index, practice_unit,
                    workflow_stage_codes_json, legitimacy_codes_json,
                    basis_codes_json, boundary_codes_json, boundary_mode_codes_json,
                    evidence_json
                ) VALUES (
                    'post', ?, 0, 'AI辅助文献综述',
                    '["A1.2"]', '["B2"]',
                    '[{"code":"C1","evidence":"节省综述整理时间"}]',
                    '[{"code":"D1.10","evidence":"人工复核"}]',
                    '[]',
                    '["用AI梳理综述框架但人工复核。"]'
                )
                """,
                (post_id,),
            )
            connection.execute(
                """
                INSERT INTO reviewed_records (
                    run_id, record_id, record_type, review_phase, payload_json
                ) VALUES ('baseline-post-review', ?, 'post', 'post_review_v2', ?)
                """,
                (post_id, json.dumps(_baseline_payload(post_id), ensure_ascii=False)),
            )
        connection.commit()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _completed_framework_v2_row(post_id: str) -> dict[str, object]:
    row = deepcopy(_baseline_payload(post_id, run_id="qv5_framework_v2_post_review_batch_00"))
    row["framework_v2_update"] = True
    row["review_status"] = "reviewed"
    row["review_date"] = "2026-04-28"
    claim_unit = row["claim_units"][0]  # type: ignore[index]
    claim_unit["ai_intervention_mode_codes"] = ["F1"]  # type: ignore[index]
    claim_unit["ai_intervention_intensity_codes"] = ["G1"]  # type: ignore[index]
    claim_unit["evaluation_tension_codes"] = ["H3"]  # type: ignore[index]
    claim_unit["formal_norm_reference_codes"] = ["I0"]  # type: ignore[index]
    claim_unit["boundary_mechanism_codes"] = ["J1"]  # type: ignore[index]
    claim_unit["boundary_result_codes"] = ["K2"]  # type: ignore[index]
    return row


def test_prepare_framework_v2_review_batches_exports_514_formal_posts_as_six_batches(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_formal_posts_with_post_review_payloads(db_path, count=514)

    manifest_path = prepare_framework_v2_review_batches(
        db_path=db_path,
        batch_size=100,
        reviewer="guoyufan",
        queue_dir=tmp_path / "review_queues",
        reviewed_dir=tmp_path / "reviewed",
        memos_dir=tmp_path / "memos",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["row_count"] == 514
    assert manifest["batch_count"] == 6
    assert [batch["row_count"] for batch in manifest["batches"]] == [100, 100, 100, 100, 100, 14]
    first_batch = Path(manifest["batches"][0]["review_template_path"])
    rows = [json.loads(line) for line in first_batch.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["framework_v2_update"] is True
    assert rows[0]["review_phase"] == "post_review_v2"
    assert rows[0]["review_status"] == "unreviewed"
    assert rows[0]["claim_units"][0]["workflow_stage_codes"] == ["A1.2"]
    assert rows[0]["claim_units"][0]["ai_intervention_mode_codes"] == []
    assert rows[0]["claim_units"][0]["boundary_result_codes"] == []


def test_framework_v2_update_import_accepts_only_v2_claim_unit_changes(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    reviewed_path = tmp_path / "reviewed" / "framework_v2.reviewed.jsonl"
    _seed_formal_posts_with_post_review_payloads(db_path, count=1)
    _write_jsonl(reviewed_path, [_completed_framework_v2_row("p001")])

    result = import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)

    assert result["rows_imported"] == 1
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        counts = {
            row["scope_name"]: row["row_count"]
            for row in connection.execute(
                "SELECT scope_name, row_count FROM vw_scope_counts WHERE scope_name LIKE 'paper_quality_v5%'"
            )
        }
        payload = json.loads(
            connection.execute(
                """
                SELECT payload_json
                FROM reviewed_records
                WHERE run_id = 'qv5_framework_v2_post_review_batch_00'
                """
            ).fetchone()["payload_json"]
        )
    assert counts["paper_quality_v5_posts"] == 1
    assert counts["paper_quality_v5_comments"] == 0
    assert payload["framework_v2_update"] is True
    assert payload["claim_units"][0]["ai_intervention_mode_codes"] == ["F1"]


def test_framework_v2_update_import_rejects_legacy_abcd_changes(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    reviewed_path = tmp_path / "reviewed" / "framework_v2.invalid.jsonl"
    _seed_formal_posts_with_post_review_payloads(db_path, count=1)
    row = _completed_framework_v2_row("p001")
    row["claim_units"][0]["workflow_stage_codes"] = ["A1.9"]  # type: ignore[index]
    _write_jsonl(reviewed_path, [row])

    with pytest.raises(ValueError, match="cannot modify existing A/B/C/D fields"):
        import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)


def test_framework_v2_materials_mark_complete_after_reviewed_v2_update(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    reviewed_path = tmp_path / "reviewed" / "framework_v2.reviewed.jsonl"
    output_dir = tmp_path / "framework_v2"
    _seed_formal_posts_with_post_review_payloads(db_path, count=1)
    _write_jsonl(reviewed_path, [_completed_framework_v2_row("p001")])
    import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)

    generate_framework_v2_materials(db_path=db_path, output_dir=output_dir)

    summary = json.loads((output_dir / "framework_v2_summary_tables.json").read_text())
    assert summary["metadata"]["framework_v2_reviewed_posts"] == 1
    assert summary["metadata"]["framework_v2_missing_posts"] == 0
    assert summary["metadata"]["framework_v2_coding_complete"] is True
    assert summary["metadata"]["note"] == COMPLETE_V2_FIELD_NOTE
    assert summary["tables"]["ai_intervention_mode_distribution"][0]["code"] == "F1"
    assert summary["tables"]["ai_intervention_intensity_distribution"][0]["code"] == "G1"
    assert summary["tables"]["formal_norm_reference_distribution"][0]["code"] == "I0"
