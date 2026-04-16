from __future__ import annotations

import sqlite3
from pathlib import Path

from src.analysis.figures.manifest import write_figure_manifest
from src.analysis.figures.render import generate_submission_figures
from src.config.research_scope import render_views_sql
from src.config.settings import SCHEMA_PATH
from src.utils.db import init_sqlite_db


def _seed_minimal_submission_db(db_path: Path) -> None:
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
                'p1', 'xiaohongshu', 'crawled', '2026-04-10', 'true',
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
                'c1', 'p1', '2026-04-10', '我也是这样用AI的', '积极采用',
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
                'tester', '2026-04-10', 1.0, 'test'
            )
            """
        )
        connection.commit()


def test_figure_manifest_and_svg_stay_partial_for_mid_period_coverage(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    figure_dir = tmp_path / "figures_mid"
    _seed_minimal_submission_db(db_path)

    figure_result = generate_submission_figures(
        db_path=db_path,
        figure_dir=figure_dir,
        coverage_end_date="2026-04-10",
    )
    manifest_path = write_figure_manifest(
        figure_dir=figure_dir,
        generated_slugs=figure_result["generated_slugs"],
        formal_posts=1,
        formal_comments=1,
        coverage_end_date="2026-04-10",
    )

    manifest_text = manifest_path.read_text(encoding="utf-8")
    posts_by_period_svg = (figure_dir / "posts_by_period.svg").read_text(encoding="utf-8")
    posts_by_quarter_svg = (figure_dir / "posts_by_quarter.svg").read_text(encoding="utf-8")

    assert "2026H1(部分)" in manifest_text
    assert "2026Q2(部分)" in manifest_text
    assert "2026H1(部分)" in posts_by_period_svg
    assert "2026Q2(部分)" in posts_by_quarter_svg


def test_figure_manifest_and_svg_drop_partial_suffix_at_period_end(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    figure_dir = tmp_path / "figures_end"
    _seed_minimal_submission_db(db_path)

    figure_result = generate_submission_figures(
        db_path=db_path,
        figure_dir=figure_dir,
        coverage_end_date="2026-06-30",
    )
    manifest_path = write_figure_manifest(
        figure_dir=figure_dir,
        generated_slugs=figure_result["generated_slugs"],
        formal_posts=1,
        formal_comments=1,
        coverage_end_date="2026-06-30",
    )

    manifest_text = manifest_path.read_text(encoding="utf-8")
    posts_by_period_svg = (figure_dir / "posts_by_period.svg").read_text(encoding="utf-8")
    posts_by_quarter_svg = (figure_dir / "posts_by_quarter.svg").read_text(encoding="utf-8")

    assert "2026H1(部分)" not in manifest_text
    assert "2026Q2(部分)" not in manifest_text
    assert "2026H1(部分)" not in posts_by_period_svg
    assert "2026Q2(部分)" not in posts_by_quarter_svg
    assert "2026H1" in manifest_text
    assert "2026Q2" in manifest_text
    assert "2026H1" in posts_by_period_svg
    assert "2026Q2" in posts_by_quarter_svg
