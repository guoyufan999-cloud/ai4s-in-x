from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.cli.build_artifacts import run_build
from src.config.research_scope import render_views_sql
from src.config.settings import SCHEMA_PATH
from src.utils.db import init_sqlite_db


def _seed_minimal_paper_scope_db(db_path: Path) -> None:
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
                actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2024-01-15', 'true',
                'graduate_student', 'Engineering & Technology', '选题与问题定义', '积极采用',
                '标题', '和AI讨论课题思路', '["ChatGPT"]', '["detection"]', '["efficiency"]',
                1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, stance,
                legitimacy_basis, benefit_themes_json, is_reply, import_batch_id
            ) VALUES (
                'c1', 'p1', '2024-01-16', '我也是这样用AI的', '积极采用',
                '效率正当性', '["efficiency"]', 0, 1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO codes (
                record_id, record_type, parent_id, boundary_negotiation_code,
                coder, coding_date, confidence, memo
            ) VALUES (
                'c1', 'comment', 'p1', 'boundary.assistance_vs_substitution',
                'tester', '2024-01-16', 1.0, 'test'
            )
            """
        )
        connection.commit()


def test_run_build_routes_all_outputs_to_the_same_custom_db(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "checkpoint.json"
    summary_output = tmp_path / "out" / "summary.json"
    consistency_output = tmp_path / "out" / "consistency.json"
    figure_dir = tmp_path / "figures"

    _seed_minimal_paper_scope_db(db_path)
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v4",
                "formal_posts": 1,
                "formal_comments": 1,
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
        summary_output=summary_output,
        consistency_output=consistency_output,
        figure_dir=figure_dir,
    )

    expected_slugs = {
        "posts_trend",
        "posts_by_period",
        "posts_by_quarter",
        "posts_heatmap",
        "comments_attitude",
        "tools_by_period",
        "tools_by_quarter",
        "risk_themes_by_period",
        "risk_themes_by_quarter",
    }
    assert result["summary"]["research_db"]["posts"] == 1
    assert result["summary"]["research_db"]["comments"] == 1
    assert result["summary"]["paper_quality_v4"]["coverage_end_date"] == "2024-01-16"
    assert result["coverage_end_date"] == "2024-01-16"
    assert result["consistency"]["research_db_path"] == str(db_path)
    assert "generated_at_utc" not in result["consistency"]
    assert set(result["figures"]["generated_slugs"]) == expected_slugs
    assert result["figures"]["coverage_end_date"] == "2024-01-16"
    assert Path(result["figure_manifest_path"]).exists()

    summary_payload = json.loads(summary_output.read_text(encoding="utf-8"))
    consistency_payload = json.loads(consistency_output.read_text(encoding="utf-8"))
    assert summary_payload["research_db"]["posts"] == 1
    assert summary_payload["paper_quality_v4"]["formal_posts"] == 1
    assert summary_payload["paper_quality_v4"]["coverage_end_date"] == "2024-01-16"
    assert consistency_payload["research_db_path"] == str(db_path)
    assert consistency_payload["status"] == "aligned"
    assert "generated_at_utc" not in consistency_payload
    manifest_text = Path(result["figure_manifest_path"]).read_text(encoding="utf-8")
    assert "- 正式覆盖截止日：`2024-01-16`" in manifest_text
