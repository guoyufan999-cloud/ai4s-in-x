from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import ai4s_legitimacy.collection.import_legacy_sqlite as legacy_import
from ai4s_legitimacy.cleaning.normalization import hash_identifier
from ai4s_legitimacy.utils.db import connect_sqlite_readonly


def _create_minimal_legacy_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE note_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id TEXT,
                query_text TEXT,
                likes_text TEXT
            );
            CREATE TABLE comments (
                comment_id TEXT PRIMARY KEY,
                note_id TEXT,
                parent_comment_id TEXT,
                comment_time TEXT,
                comment_text TEXT,
                commenter_id TEXT,
                commenter_name TEXT,
                updated_at TEXT,
                created_at TEXT
            );
            CREATE TABLE authors (
                author_id TEXT PRIMARY KEY,
                author_name TEXT
            );
            CREATE TABLE coding_labels_posts (
                note_id TEXT PRIMARY KEY,
                workflow_primary TEXT,
                attitude_polarity TEXT,
                sample_status TEXT,
                actor_type TEXT,
                decided_by TEXT,
                review_override INTEGER,
                qs_broad_subject TEXT,
                risk_themes_json TEXT,
                ai_tools_json TEXT,
                benefit_themes_json TEXT
            );
            CREATE TABLE coding_labels_comments (
                comment_id TEXT PRIMARY KEY,
                workflow_primary TEXT,
                attitude_polarity TEXT,
                controversy_type TEXT,
                benefit_themes_json TEXT
            );
            CREATE TABLE note_details (
                note_id TEXT PRIMARY KEY,
                crawl_status TEXT,
                canonical_url TEXT,
                source_url TEXT,
                author_id TEXT,
                publish_time TEXT,
                updated_at TEXT,
                created_at TEXT,
                title TEXT,
                full_text TEXT,
                note_type TEXT,
                media_count INTEGER
            );
            CREATE TABLE query_dictionary (
                layer TEXT,
                term TEXT,
                source TEXT
            );
            """
        )
        connection.executemany(
            "INSERT INTO note_candidates (note_id, query_text, likes_text) VALUES (?, ?, ?)",
            [
                ("note-1", "AI科研", ""),
                ("note-1", "ChatGPT", "1.2万"),
                ("note-1", "AI科研", "999"),
            ],
        )
        connection.execute(
            "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "comment-1",
                "note-1",
                "",
                "2026-04-10 12:00:00",
                "这个思路有帮助",
                "commenter-1",
                "李四",
                "2026-04-10 13:00:00",
                "2026-04-10 12:00:00",
            ),
        )
        connection.execute(
            "INSERT INTO authors VALUES (?, ?)",
            ("author-1", "张三丰"),
        )
        connection.execute(
            """
            INSERT INTO coding_labels_posts VALUES (
                'note-1',
                '研究设计与实验/方案制定',
                '积极采用',
                'true',
                'graduate_student',
                'legacy_rule',
                1,
                'Engineering & Technology',
                '["detection"]',
                '["ChatGPT"]',
                '["efficiency"]'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO coding_labels_comments VALUES (
                'comment-1',
                '研究设计与实验/方案制定',
                '积极但保留',
                'risk',
                '["efficiency"]'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO note_details VALUES (
                'note-1',
                'crawled',
                'https://example.com/note-1',
                'https://source.example.com/note-1',
                'author-1',
                '2026-04-09 08:00:00',
                '2026-04-09 10:00:00',
                '2026-04-09 08:00:00',
                '研究设计标题',
                '和AI一起设计实验方案',
                'normal',
                2
            )
            """
        )
        connection.execute(
            "INSERT INTO query_dictionary VALUES ('topic', 'AI科研', 'manual_seed')"
        )
        connection.commit()


def test_migrate_legacy_sqlite_imports_core_records_and_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_db_path = tmp_path / "legacy.sqlite3"
    research_db_path = tmp_path / "research.sqlite3"
    summary_dir = tmp_path / "interim"
    _create_minimal_legacy_db(legacy_db_path)
    monkeypatch.setattr(legacy_import, "INTERIM_DIR", summary_dir)

    summary_path = legacy_import.migrate_legacy_sqlite(
        legacy_db_path=legacy_db_path,
        research_db_path=research_db_path,
    )

    assert summary_path == summary_dir / "legacy_to_research_migration_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["batch_name"] == "legacy_quality_v4_migration"
    assert summary["posts_migrated"] == 1
    assert summary["comments_migrated"] == 1
    assert summary["status"] == "ok"

    with connect_sqlite_readonly(research_db_path) as connection:
        post = connection.execute("SELECT * FROM posts").fetchone()
        assert post["post_id"] == "note-1"
        assert post["keyword_query"] == "AI科研 | ChatGPT"
        assert post["engagement_like"] == 12000
        assert post["engagement_comment"] == 1
        assert post["author_id_hashed"] == hash_identifier("author-1")
        assert post["author_name_masked"] == "张*丰"
        assert post["workflow_stage"] == "研究设计与实验/方案制定"
        assert post["primary_legitimacy_stance"] == "积极采用"
        assert post["sample_status"] == "true"
        assert post["notes"] == (
            "legacy_decided_by=legacy_rule; "
            "legacy_review_override=1; "
            "legacy_note_type=normal; "
            "legacy_media_count=2"
        )

        comment = connection.execute("SELECT * FROM comments").fetchone()
        assert comment["comment_id"] == "comment-1"
        assert comment["stance"] == "积极但保留"
        assert comment["legitimacy_basis"] == "risk"
        assert comment["benefit_themes_json"] == '["efficiency"]'

        batch = connection.execute(
            "SELECT batch_name, record_post_count, record_comment_count FROM import_batches"
        ).fetchone()
        assert batch["batch_name"] == "legacy_quality_v4_migration"
        assert batch["record_post_count"] == 1
        assert batch["record_comment_count"] == 1

        post_code = connection.execute(
            "SELECT * FROM codes WHERE record_type = 'post'"
        ).fetchone()
        comment_code = connection.execute(
            "SELECT * FROM codes WHERE record_type = 'comment'"
        ).fetchone()
        assert post_code["workflow_stage_code"] == "workflow.research_design"
        assert comment_code["workflow_stage_code"] == "workflow.research_design"
        assert (
            comment_code["boundary_negotiation_code"]
            == "boundary.assistance_vs_substitution"
        )


def test_migrate_legacy_sqlite_requires_existing_legacy_db(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        legacy_import.migrate_legacy_sqlite(
            legacy_db_path=tmp_path / "missing.sqlite3",
            research_db_path=tmp_path / "research.sqlite3",
        )


def test_migrate_legacy_sqlite_refuses_existing_research_db_without_overwrite(
    tmp_path: Path,
) -> None:
    legacy_db_path = tmp_path / "legacy.sqlite3"
    research_db_path = tmp_path / "research.sqlite3"
    _create_minimal_legacy_db(legacy_db_path)
    research_db_path.write_text("already exists", encoding="utf-8")

    with pytest.raises(FileExistsError):
        legacy_import.migrate_legacy_sqlite(
            legacy_db_path=legacy_db_path,
            research_db_path=research_db_path,
        )
