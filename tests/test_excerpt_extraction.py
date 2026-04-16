from __future__ import annotations

from pathlib import Path

from ai4s_legitimacy.analysis.excerpt_extraction import (
    deidentify_text,
    export_excerpts,
    extract_excerpts_by_stance,
    extract_excerpts_by_workflow_stage,
    format_excerpts_markdown,
    generate_all_excerpts,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.utils.db import init_sqlite_db


def test_deidentify_text() -> None:
    assert "[URL]" in deidentify_text("Visit https://example.com for details.")
    assert "[email]" in deidentify_text("Contact me at test@example.com please.")
    assert "..." in deidentify_text("a " * 200, max_chars=50)
    assert deidentify_text("") == ""


def test_extract_and_format(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite3"
    schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    init_sqlite_db(db_path, schema_path, views_sql=render_views_sql())

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO import_batches (batch_name, source_description) VALUES ('test', 'test')"
    )
    conn.execute(
        "INSERT INTO platform_sources (platform_code, platform_name) VALUES ('xhs', '小红书')"
    )
    conn.execute(
        """
        INSERT INTO posts (
            post_id, platform, sample_status, workflow_stage, primary_legitimacy_stance,
            content_text, post_date, is_public, import_batch_id, legacy_crawl_status, actor_type
        ) VALUES ('p1', 'xhs', 'true', '选题与问题定义', '积极采用', '和AI讨论课题思路', '2024-01-01', 1, 1, 'crawled', 'graduate_student')
        """
    )
    conn.execute(
        """
        INSERT INTO comments (
            comment_id, post_id, comment_text, stance, comment_date, is_reply, import_batch_id
        ) VALUES ('c1', 'p1', '我也是这样用AI的', '积极采用', '2024-01-01', 0, 1)
        """
    )
    conn.commit()
    conn.close()

    excerpts = extract_excerpts_by_workflow_stage("选题与问题定义", limit=5, db_path=db_path)
    assert len(excerpts) == 1
    assert excerpts[0]["record_type"] == "post"
    assert "AI" in excerpts[0]["excerpt"]

    excerpts = extract_excerpts_by_stance("积极采用", record_type="comment", limit=5, db_path=db_path)
    assert len(excerpts) == 1
    assert excerpts[0]["record_type"] == "comment"

    md = format_excerpts_markdown(excerpts, "test_label")
    md_with_timestamp = format_excerpts_markdown(
        excerpts,
        "test_label",
        generated_at="2026-04-10T00:00:00",
    )
    assert "test_label" in md
    assert "摘录 1" in md
    assert "生成时间" not in md
    assert "生成时间：2026-04-10T00:00:00" in md_with_timestamp

    default_export_path = export_excerpts("test_label_default", excerpts, output_dir=tmp_path / "exports")
    audited_export_path = export_excerpts(
        "test_label_audit",
        excerpts,
        output_dir=tmp_path / "exports",
        generated_at="2026-04-10T00:00:00",
    )
    assert "生成时间" not in default_export_path.read_text(encoding="utf-8")
    assert "生成时间：2026-04-10T00:00:00" in audited_export_path.read_text(encoding="utf-8")

    batch_paths = generate_all_excerpts(db_path=db_path, output_dir=tmp_path / "batch", limit=5)
    assert batch_paths
    for path in batch_paths:
        assert "生成时间" not in path.read_text(encoding="utf-8")
