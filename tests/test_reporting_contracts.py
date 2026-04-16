from __future__ import annotations

import sqlite3
from pathlib import Path

from ai4s_legitimacy.analysis.reporting import build_summary_payload
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db


def _seed_minimal_reporting_db(db_path: Path) -> None:
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


def test_build_summary_payload_keeps_contract_shape_and_core_series(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_minimal_reporting_db(db_path)

    payload = build_summary_payload(db_path=db_path)

    assert list(payload.keys()) == ["research_db", "paper_quality_v4"]
    assert list(payload["research_db"].keys()) == [
        "posts",
        "comments",
        "codes",
        "codebook_rows",
        "sample_status",
        "scope_counts",
    ]
    assert list(payload["paper_quality_v4"].keys()) == [
        "scope_counts",
        "formal_posts",
        "formal_comments",
        "coverage_end_date",
        "monthly_posts_by_workflow",
        "subject_distribution",
        "workflow_distribution",
        "comment_stance_distribution",
        "comment_stance_by_month",
        "cross_tabs",
    ]
    assert list(payload["paper_quality_v4"]["cross_tabs"].keys()) == [
        "workflow_legitimacy",
        "subject_workflow",
        "subject_legitimacy",
        "boundary_negotiation",
        "comment_legitimacy_basis",
        "halfyear_workflow",
        "halfyear_subject",
    ]

    assert payload["research_db"]["posts"] == 1
    assert payload["research_db"]["comments"] == 1
    assert payload["research_db"]["codes"] == 1
    assert payload["research_db"]["sample_status"] == {"true": 1}
    assert payload["paper_quality_v4"]["formal_posts"] == 1
    assert payload["paper_quality_v4"]["formal_comments"] == 1
    assert payload["paper_quality_v4"]["coverage_end_date"] == "2024-01-16"
    assert payload["paper_quality_v4"]["monthly_posts_by_workflow"] == [
        {"period_month": "2024-01", "workflow_stage": "选题与问题定义", "post_count": 1}
    ]
    assert payload["paper_quality_v4"]["comment_stance_distribution"] == [
        {"label": "积极采用", "comment_count": 1}
    ]
    assert payload["paper_quality_v4"]["cross_tabs"]["workflow_legitimacy"] == [
        {
            "workflow_stage": "选题与问题定义",
            "legitimacy_stance": "积极采用",
            "post_count": 1,
        }
    ]
    assert payload["paper_quality_v4"]["cross_tabs"]["boundary_negotiation"] == [
        {
            "boundary_negotiation_code": "boundary.assistance_vs_substitution",
            "coded_count": 1,
        }
    ]
