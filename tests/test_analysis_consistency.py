from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai4s_legitimacy.analysis.quality_v4_consistency import evaluate_quality_v4_consistency
from ai4s_legitimacy.config.research_scope import render_views_sql


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def test_quality_v4_consistency_report_shape(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "quality_v4_checkpoint.json"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(render_views_sql())
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status
            ) VALUES ('p1', 'xiaohongshu', 'crawled', '2025-01-15', 'true')
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text
            ) VALUES ('c1', 'p1', '2025-01-16', 'ok')
            """
        )
        connection.commit()
    finally:
        connection.close()

    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v4",
                "formal_posts": 1,
                "formal_comments": 1,
                "queued": 0,
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_quality_v4_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )
    repeated_report = evaluate_quality_v4_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )
    audited_report = evaluate_quality_v4_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
        generated_at_utc="2026-04-10T00:00:00+00:00",
    )

    assert repeated_report == report
    assert report["status"] == "aligned"
    assert report["reference"]["formal_posts"] == 1
    assert report["scope_counts"]["paper_quality_v4_posts"] == 1
    assert report["scope_counts"]["paper_quality_v4_comments"] == 1
    assert "generated_at_utc" not in report
    assert audited_report["generated_at_utc"] == "2026-04-10T00:00:00+00:00"
