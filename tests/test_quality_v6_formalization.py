from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import ai4s_legitimacy.analysis.quality_v6_formalization as qv6
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _seed_base_quality_v5_db(db_path: Path) -> None:
    init_sqlite_db(db_path, SCHEMA_PATH, views_sql=render_views_sql())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO import_batches (batch_name, source_description) VALUES ('base', 'base')"
        )
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_note_id, legacy_crawl_status, post_url,
                post_date, capture_date, title, content_text, sample_status,
                actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                decision, review_status, risk_themes_json, ai_tools_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p_v5', 'xiaohongshu', 'p_v5', 'crawled', 'https://example.test/p_v5',
                '2025-01-10', '2026-04-10', 'v5', 'v5 formal post', 'true',
                'graduate_student', 'uncertain', '文献调研与知识整合', '积极采用',
                '纳入', 'reviewed', '[]', '[]', '[]', 1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES (
                'post', 'p_v5', 0, 'v5 claim', '["A1.2"]', '["B1"]', '["v5 formal post"]'
            )
            """
        )
        connection.commit()


def _supplemental_row(candidate_id: str, note_id: str, decision: str = "include") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "note_id": note_id,
        "platform": "xiaohongshu",
        "post_url": f"https://www.xiaohongshu.com/explore/{note_id}",
        "post_date": "2026-04-20",
        "reviewed_at": "2026-04-29T00:00:00+00:00",
        "query": "AI科研",
        "query_group": "A. AI科研总体类",
        "quality_v5_formal": False,
        "quality_v5_formal_scope": False,
        "supplemental_formalization_decision": decision,
        "content_text": "这是一条关于AI辅助科研文献处理和论文写作的公开帖子，包含足够正文用于测试。",
        "discourse_context": {"text_type": "经验分享", "interaction_form": "主帖"},
        "practice_position": {
            "source_field": "literature_processing",
            "domain_code": "A1",
            "workflow_stage": "文献处理与知识整合",
        },
        "claim_units": [
            {
                "evidence": "AI辅助科研文献处理和论文写作",
                "ai_intervention_mode_codes": ["F1"],
                "ai_intervention_intensity_codes": ["G1"],
                "evaluation_tension_codes": [],
                "formal_norm_reference_codes": ["I0"],
                "boundary_mechanism_codes": [],
                "boundary_result_codes": [],
                "boundary_type_codes": [],
                "boundary_mode_codes": [],
                "normative_evaluation_standard_codes": ["C1"],
                "normative_evaluation_tendency_codes": ["B1"],
            }
        ],
    }


def test_quality_v6_staging_preserves_quality_v5_and_adds_post_only_v6(tmp_path: Path) -> None:
    base_db = tmp_path / "base.sqlite3"
    staging_db = tmp_path / "quality_v6.sqlite3"
    supplemental = tmp_path / "supplemental.jsonl"
    _seed_base_quality_v5_db(base_db)
    _write_jsonl(
        supplemental,
        [
            _supplemental_row("cand_1", "note_1"),
            _supplemental_row("cand_2", "note_2"),
            _supplemental_row("cand_excluded", "note_excluded", decision="exclude"),
        ],
    )

    result = qv6.prepare_quality_v6_staging_db(
        base_db_path=base_db,
        supplemental_path=supplemental,
        output_db_path=staging_db,
        expected_include_count=2,
        expected_exclude_count=1,
    )

    assert result["imported_posts"] == 2
    with sqlite3.connect(staging_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM vw_posts_paper_scope_quality_v5").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM vw_posts_paper_scope_quality_v6").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM vw_comments_paper_scope_quality_v6").fetchone()[0] == 0
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM vw_posts_paper_scope_quality_v6 WHERE post_id = 'cand_excluded'"
            ).fetchone()[0]
            == 0
        )
    with sqlite3.connect(base_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 1


def test_quality_v6_consistency_uses_v6_checkpoint_and_v5_guard(tmp_path: Path) -> None:
    base_db = tmp_path / "base.sqlite3"
    staging_db = tmp_path / "quality_v6.sqlite3"
    supplemental = tmp_path / "supplemental.jsonl"
    checkpoint = tmp_path / "quality_v6_checkpoint.json"
    _seed_base_quality_v5_db(base_db)
    _write_jsonl(
        supplemental,
        [
            _supplemental_row("cand_1", "note_1"),
            _supplemental_row("cand_2", "note_2"),
            _supplemental_row("cand_excluded", "note_excluded", decision="exclude"),
        ],
    )
    qv6.prepare_quality_v6_staging_db(
        base_db_path=base_db,
        supplemental_path=supplemental,
        output_db_path=staging_db,
        expected_include_count=2,
        expected_exclude_count=1,
    )
    checkpoint.write_text(
        json.dumps(
            {"checkpoint_stage": "quality_v6", "formal_posts": 3, "formal_comments": 0},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = qv6.evaluate_quality_v6_consistency(
        db_path=staging_db,
        checkpoint_path=checkpoint,
        expected_quality_v5_posts=1,
        expected_quality_v5_comments=0,
    )

    assert report["status"] == "aligned"
    assert report["observed_paper_scope"] == {"formal_posts": 3, "formal_comments": 0}
    assert report["quality_v5_guard"] == {"formal_posts": 1, "formal_comments": 0}


def test_quality_v6_builder_writes_isolated_artifacts(tmp_path: Path, monkeypatch) -> None:
    base_db = tmp_path / "base.sqlite3"
    staging_db = tmp_path / "quality_v6.sqlite3"
    supplemental = tmp_path / "supplemental.jsonl"
    _seed_base_quality_v5_db(base_db)
    _write_jsonl(
        supplemental,
        [
            _supplemental_row("cand_1", "note_1"),
            _supplemental_row("cand_2", "note_2"),
            _supplemental_row("cand_excluded", "note_excluded", decision="exclude"),
        ],
    )
    monkeypatch.setattr(qv6, "SUPPLEMENTAL_REVIEWED_PATH", supplemental)
    monkeypatch.setattr(qv6, "QUALITY_V6_SUMMARY_PATH", tmp_path / "reports" / "summary.json")
    monkeypatch.setattr(
        qv6,
        "QUALITY_V6_FREEZE_CHECKPOINT_PATH",
        tmp_path / "reports" / "quality_v6_freeze_checkpoint.json",
    )
    monkeypatch.setattr(
        qv6,
        "QUALITY_V6_FREEZE_CHECKPOINT_MARKDOWN_PATH",
        tmp_path / "reports" / "quality_v6_freeze_checkpoint.md",
    )
    monkeypatch.setattr(
        qv6,
        "QUALITY_V6_CONSISTENCY_REPORT_PATH",
        tmp_path / "reports" / "quality_v6_consistency.json",
    )
    monkeypatch.setattr(
        qv6,
        "QUALITY_V6_ARTIFACT_PROVENANCE_PATH",
        tmp_path / "reports" / "quality_v6_provenance.json",
    )
    monkeypatch.setattr(qv6, "QUALITY_V6_PAPER_MATERIALS_DIR", tmp_path / "paper_materials")
    monkeypatch.setattr(qv6, "QUALITY_V6_TABLE_DIR", tmp_path / "tables")
    monkeypatch.setattr(qv6, "QUALITY_V6_FIGURE_DIR", tmp_path / "figures")

    result = qv6.build_quality_v6_artifacts(
        base_db_path=base_db,
        supplemental_path=supplemental,
        staging_db_path=staging_db,
        skip_figures=True,
        expected_include_count=2,
        expected_exclude_count=1,
        expected_quality_v5_posts=1,
        expected_quality_v5_comments=0,
    )

    assert result["status"] == "aligned"
    assert json.loads((tmp_path / "reports" / "summary.json").read_text(encoding="utf-8"))[
        "paper_quality_v6"
    ]["formal_posts"] == 3
    assert (tmp_path / "paper_materials" / "paper_results_chapter_quality_v6.md").exists()
    assert (tmp_path / "paper_materials" / "framework_v2" / "framework_v2_summary_tables.json").exists()
