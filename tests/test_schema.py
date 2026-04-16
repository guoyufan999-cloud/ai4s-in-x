from __future__ import annotations

import sqlite3
from pathlib import Path

from ai4s_legitimacy.config.research_scope import render_views_sql


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def test_schema_creates_core_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(render_views_sql())
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {"posts", "comments", "codes", "codebook", "import_batches",
                "ai_tools_lookup", "risk_themes_lookup", "benefit_themes_lookup"} <= tables
        views = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            ).fetchall()
        }
        assert {
            "vw_posts_candidate_scope",
            "vw_posts_research_scope",
            "vw_posts_paper_scope_quality_v4",
            "vw_comments_candidate_scope",
            "vw_comments_research_scope",
            "vw_comments_paper_scope_quality_v4",
            "vw_scope_counts",
            "vw_posts_by_month_workflow",
            "vw_comments_by_month_legitimacy",
            "vw_workflow_legitimacy_cross",
            "vw_boundary_negotiation_summary",
            "vw_paper_quality_v4_post_ai_tools",
            "vw_paper_quality_v4_post_risk_themes",
            "vw_paper_quality_v4_post_benefit_themes",
            "vw_paper_quality_v4_workflow_legitimacy_cross",
            "vw_paper_quality_v4_boundary_negotiation_summary",
            "vw_paper_quality_v4_subject_workflow_cross",
            "vw_paper_quality_v4_subject_legitimacy_cross",
            "vw_paper_quality_v4_comment_legitimacy_basis_distribution",
            "vw_paper_quality_v4_halfyear_workflow",
            "vw_paper_quality_v4_halfyear_subject",
        } <= views
    finally:
        connection.close()
