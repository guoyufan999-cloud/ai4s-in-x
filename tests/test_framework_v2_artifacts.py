from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai4s_legitimacy.analysis.framework_v2_materials import (
    MISSING_V2_FIELD_NOTE,
    generate_framework_v2_materials,
)
from ai4s_legitimacy.cli.build_artifacts import run_build
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db

ROOT = Path(__file__).resolve().parents[1]


def _seed_quality_v5_post_only_db(db_path: Path) -> None:
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
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                actor_type, qs_broad_subject, workflow_domain, workflow_stage,
                primary_legitimacy_stance, decision, review_status,
                title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2024-01-15', 'true',
                'graduate_student', 'Engineering & Technology', 'P', '文献调研与知识整合',
                '有条件接受', '纳入', 'reviewed',
                '标题', '用AI梳理综述框架但人工复核', '["ChatGPT"]', '[]', '["efficiency"]',
                1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json,
                basis_codes_json, boundary_codes_json, boundary_mode_codes_json,
                evidence_json
            ) VALUES (
                'post', 'p1', 0, 'AI辅助文献综述',
                '["A1.2"]', '["B2"]',
                '[{"code":"C1","evidence":"节省综述整理时间"}]',
                '[{"code":"D1.10","evidence":"人工复核"}]',
                '[]',
                '["用AI梳理综述框架但人工复核"]'
            )
            """
        )
        connection.commit()


def test_framework_v2_material_builder_handles_empty_new_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    output_dir = tmp_path / "framework_v2"
    _seed_quality_v5_post_only_db(db_path)

    result = generate_framework_v2_materials(db_path=db_path, output_dir=output_dir)

    assert result["formal_posts"] == 1
    assert result["formal_comments"] == 0
    for path in result["paths"].values():
        assert Path(path).exists()

    summary = json.loads((output_dir / "framework_v2_summary_tables.json").read_text())
    cross_tabs = json.loads((output_dir / "cross_tabs_v2.json").read_text())
    assert summary["metadata"]["formal_stage"] == "quality_v5"
    assert summary["metadata"]["formal_posts"] == 1
    assert summary["metadata"]["formal_comments"] == 0
    assert summary["metadata"]["note"] == MISSING_V2_FIELD_NOTE
    assert summary["tables"]["ai_intervention_mode_distribution"] == []
    assert summary["tables"]["ai_intervention_intensity_distribution"] == []
    assert summary["tables"]["evaluation_tension_distribution"] == []
    assert summary["tables"]["formal_norm_reference_distribution"] == []
    assert summary["tables"]["boundary_mechanism_distribution"] == []
    assert summary["tables"]["boundary_result_distribution"] == []
    assert cross_tabs["cross_tabs"]["normative_standard_x_boundary_type"]
    assert cross_tabs["cross_tabs"]["workflow_stage_x_ai_intervention_mode"] == []
    assert MISSING_V2_FIELD_NOTE in (output_dir / "writing_memo_v2.md").read_text(
        encoding="utf-8"
    )


def test_build_artifacts_can_route_framework_v2_outputs_to_custom_directory(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "checkpoint.json"
    framework_v2_dir = tmp_path / "paper_materials" / "framework_v2"
    _seed_quality_v5_post_only_db(db_path)
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
                "formal_posts": 1,
                "formal_comments": 0,
                "queued": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = run_build(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        summary_output=tmp_path / "out" / "summary.json",
        consistency_output=tmp_path / "out" / "consistency.json",
        provenance_output=tmp_path / "out" / "provenance.json",
        figure_dir=tmp_path / "figures",
        review_v2_post_output_path=tmp_path / "review_v2" / "post_review_v2_master.jsonl",
        review_v2_comment_output_path=tmp_path / "review_v2" / "comment_review_v2_master.jsonl",
        review_v2_delta_output_path=tmp_path / "review_v2" / "post_review_v2_delta_report.json",
        framework_v2_output_dir=framework_v2_dir,
        skip_figures=True,
    )

    assert result["framework_v2"]["output_dir"] == str(framework_v2_dir)
    assert result["framework_v2"]["formal_posts"] == 1
    assert result["framework_v2"]["formal_comments"] == 0
    assert (framework_v2_dir / "framework_v2_summary_tables.json").exists()


def test_versioned_framework_v2_outputs_preserve_quality_v5_post_only_boundary() -> None:
    output_dir = ROOT / "outputs" / "reports" / "paper_materials" / "framework_v2"
    readme_text = (output_dir / "README.md").read_text(encoding="utf-8")
    summary = json.loads((output_dir / "framework_v2_summary_tables.json").read_text())

    assert "`quality_v5 post-only`" in readme_text
    assert "`514 / 0`" in readme_text
    assert "comment_review_v2" not in readme_text or "不启动评论层正式结果" in readme_text
    assert summary["metadata"]["formal_posts"] == 514
    assert summary["metadata"]["formal_comments"] == 0
    assert summary["metadata"]["note"] == MISSING_V2_FIELD_NOTE
