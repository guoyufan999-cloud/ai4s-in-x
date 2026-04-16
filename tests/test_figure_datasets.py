from __future__ import annotations

import sqlite3
from pathlib import Path

from ai4s_legitimacy.analysis.figures.queries import load_submission_figure_data
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly, init_sqlite_db


def _seed_diverse_submission_db(db_path: Path) -> None:
    init_sqlite_db(db_path, SCHEMA_PATH, views_sql=render_views_sql())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO import_batches (batch_name, source_description) VALUES ('test_batch', 'test')"
        )
        connection.execute(
            "INSERT INTO platform_sources (platform_code, platform_name) VALUES ('xiaohongshu', '小红书')"
        )
        posts = [
            (
                "p1",
                "2024-01-15",
                "Engineering & Technology",
                "选题与问题定义",
                '["ChatGPT"]',
                '["detection"]',
            ),
            (
                "p2",
                "2024-07-20",
                "Engineering & Technology",
                "研究设计与实验/方案制定",
                '["Claude"]',
                '["hallucination"]',
            ),
            (
                "p3",
                "2025-03-11",
                "Natural Sciences",
                "编码/建模/统计分析",
                '["Gemini"]',
                '["ethics"]',
            ),
            (
                "p4",
                "2025-10-01",
                "Social Sciences & Management",
                "论文写作/投稿/审稿回复",
                '["Cursor"]',
                '["privacy"]',
            ),
            (
                "p5",
                "2026-02-14",
                "Arts & Humanities",
                "数据获取与预处理",
                '["Copilot"]',
                '["bias"]',
            ),
            (
                "p6",
                "2026-04-10",
                "Engineering & Technology",
                "选题与问题定义",
                '["ToolX"]',
                '["cost"]',
            ),
        ]
        for post_id, post_date, subject, workflow, tools_json, risks_json in posts:
            connection.execute(
                """
                INSERT INTO posts (
                    post_id, platform, legacy_crawl_status, post_date, sample_status,
                    actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                    title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                    import_batch_id
                ) VALUES (?, 'xiaohongshu', 'crawled', ?, 'true',
                         'graduate_student', ?, ?, '积极采用',
                         '标题', '内容', ?, ?, '["efficiency"]', 1)
                """,
                (post_id, post_date, subject, workflow, tools_json, risks_json),
            )

        comments = [
            ("c1", "p1", "2024-01-16", "积极采用", "效率正当性"),
            ("c2", "p2", "2024-07-21", "积极但保留", "专业能力边界"),
            ("c3", "p3", "2025-03-12", "批判/担忧", "学术诚信"),
            ("c4", "p4", "2025-10-02", "中性经验帖", "工具适配性"),
            ("c5", "p5", "2026-02-15", "明确拒绝", "教育/训练价值"),
            ("c6", "p6", "2026-04-10", "积极采用", "效率正当性"),
        ]
        for comment_id, post_id, comment_date, stance, legitimacy_basis in comments:
            connection.execute(
                """
                INSERT INTO comments (
                    comment_id, post_id, comment_date, comment_text, stance,
                    legitimacy_basis, benefit_themes_json, is_reply, import_batch_id
                ) VALUES (?, ?, ?, 'comment', ?, ?, '["efficiency"]', 0, 1)
                """,
                (comment_id, post_id, comment_date, stance, legitimacy_basis),
            )
        connection.commit()


def test_load_submission_figure_data_exposes_dataset_contracts_and_other_buckets(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_diverse_submission_db(db_path)

    with connect_sqlite_readonly(db_path) as connection:
        datasets = load_submission_figure_data(
            connection,
            coverage_end_date="2026-04-10",
        )

    assert {
        "posts_trend",
        "posts_by_period",
        "posts_by_quarter",
        "posts_heatmap",
        "comments_attitude",
        "tools_by_period",
        "tools_by_quarter",
        "risk_themes_by_period",
        "risk_themes_by_quarter",
    } <= set(datasets)
    assert "2026H1(部分)" in datasets["posts_by_period"]["display_labels"]
    assert "2026Q2(部分)" in datasets["posts_by_quarter"]["display_labels"]
    assert "2026H1(部分)" in datasets["tools_by_period"]["display_labels"]
    assert datasets["tools_by_period"]["categories"][-1] == "其他"
    assert datasets["risk_themes_by_period"]["categories"][:5] == [
        "detection",
        "hallucination",
        "ethics",
        "privacy",
        "bias",
    ]
    assert datasets["risk_themes_by_period"]["categories"][-1] == "其他"
    assert "积极采用" in datasets["comments_attitude"]["categories"]
    assert datasets["posts_trend"]["month_order"][0] == "2024-01"
    assert datasets["posts_heatmap"]["row_labels"]

