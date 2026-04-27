from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai4s_legitimacy.analysis.quality_v5_consistency import evaluate_quality_v5_consistency
from ai4s_legitimacy.config.research_scope import render_views_sql


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def test_quality_v5_consistency_report_shape(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "quality_v5_checkpoint.json"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(render_views_sql())
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                decision, review_status
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2025-01-15', 'true',
                'graduate_student', 'Engineering & Technology', '选题与问题定义', '积极采用',
                '纳入', 'reviewed'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, stance, decision, review_status
            ) VALUES ('c1', 'p1', '2025-01-16', 'ok', '积极采用', '纳入', 'reviewed')
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('post', 'p1', 0, 'AI辅助研究构思', '["A1.1"]', '["B1"]', '["ok"]')
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('comment', 'c1', 0, '评论回应AI使用', '["A1.1"]', '["B1"]', '["ok"]')
            """
        )
        connection.commit()
    finally:
        connection.close()

    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
                "formal_posts": 1,
                "formal_comments": 1,
                "queued": 0,
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )
    repeated_report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )
    audited_report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
        generated_at_utc="2026-04-10T00:00:00+00:00",
    )

    assert repeated_report == report
    assert report["status"] == "aligned"
    assert report["reference"]["formal_posts"] == 1
    assert report["scope_counts"]["paper_quality_v5_posts"] == 1
    assert report["scope_counts"]["paper_quality_v5_comments"] == 1
    assert "generated_at_utc" not in report
    assert audited_report["generated_at_utc"] == "2026-04-10T00:00:00+00:00"


def test_quality_v5_consistency_keeps_missing_comment_dates_out_of_paper_scope(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research_missing_comment_date.sqlite3"
    checkpoint_path = tmp_path / "quality_v5_checkpoint_missing_comment_date.json"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(render_views_sql())
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                decision, review_status
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2025-01-15', 'true',
                'graduate_student', 'Engineering & Technology', '选题与问题定义', '积极采用',
                '纳入', 'reviewed'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('post', 'p1', 0, 'AI辅助研究构思', '["A1.1"]', '["B1"]', '["paper scope"]')
            """
        )
        connection.executemany(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, stance, decision, review_status
            ) VALUES (?, 'p1', ?, ?, '积极采用', '纳入', 'reviewed')
            """,
            [
                ("c_missing", None, "missing comment date"),
                ("c_outside", "2026-07-01", "outside research window"),
                ("c_in_scope", "2025-01-16", "paper scope"),
            ],
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('comment', 'c_missing', 0, 'comment', '["A1.1"]', '["B1"]', '["missing comment date"]')
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('comment', 'c_outside', 0, 'comment', '["A1.1"]', '["B1"]', '["outside research window"]')
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES ('comment', 'c_in_scope', 0, 'comment', '["A1.1"]', '["B1"]', '["paper scope"]')
            """
        )
        connection.commit()
    finally:
        connection.close()

    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
                "formal_posts": 1,
                "formal_comments": 1,
                "queued": 0,
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )

    assert report["status"] == "aligned"
    assert report["scope_counts"]["paper_quality_v5_comments"] == 1
    assert report["research_to_paper_exclusion"]["comments"] == {
        "missing_comment_date": 1,
        "outside_research_window": 1,
        "paper_scope": 1,
    }
