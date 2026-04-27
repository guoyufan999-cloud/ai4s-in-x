from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

import ai4s_legitimacy.collection.import_legacy_sqlite as legacy_import
from ai4s_legitimacy.cli.build_artifacts import run_build
from ai4s_legitimacy.collection.review_v2_artifacts import (
    COMMENT_MASTER_PATH,
    DELTA_REPORT_PATH,
    POST_MASTER_PATH,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import checkpoint_sqlite_wal, init_sqlite_db


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
                decision, review_status,
                title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2024-01-15', 'true',
                'graduate_student', 'Engineering & Technology', '选题与问题定义', '积极采用',
                '纳入', 'reviewed',
                '标题', '和AI讨论课题思路', '["ChatGPT"]', '["detection"]', '["efficiency"]',
                1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, stance,
                legitimacy_basis, benefit_themes_json, is_reply, import_batch_id,
                decision, review_status
            ) VALUES (
                'c1', 'p1', '2024-01-16', '我也是这样用AI的', '积极采用',
                '效率正当性', '["efficiency"]', 0, 1,
                '纳入', 'reviewed'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES (
                'post', 'p1', 0, 'AI辅助研究构思',
                '["A1.1"]', '["B1"]', '["和AI讨论课题思路"]'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES (
                'comment', 'c1', 0, '评论回应AI使用',
                '["A1.1"]', '["B1"]', '["我也是这样用AI的"]'
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
    checkpoint_sqlite_wal(db_path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checksum_snapshot(*paths: Path) -> dict[str, str]:
    return {str(path): _sha256(path) for path in paths}


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


def test_run_build_routes_all_outputs_to_the_same_custom_db(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "checkpoint.json"
    summary_output = tmp_path / "out" / "summary.json"
    consistency_output = tmp_path / "out" / "consistency.json"
    provenance_output = tmp_path / "out" / "provenance.json"
    figure_dir = tmp_path / "figures"
    post_master_path = tmp_path / "review_v2" / "post_review_v2_master.jsonl"
    comment_master_path = tmp_path / "review_v2" / "comment_review_v2_master.jsonl"
    delta_report_path = tmp_path / "review_v2" / "post_review_v2_delta_report.json"

    _seed_minimal_paper_scope_db(db_path)
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
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
        provenance_output=provenance_output,
        figure_dir=figure_dir,
        review_v2_post_output_path=post_master_path,
        review_v2_comment_output_path=comment_master_path,
        review_v2_delta_output_path=delta_report_path,
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
    assert result["summary"]["paper_quality_v5"]["coverage_end_date"] == "2024-01-16"
    assert result["coverage_end_date"] == "2024-01-16"
    assert result["consistency"]["research_db_path"] == str(db_path)
    assert "generated_at_utc" not in result["consistency"]
    assert set(result["figures"]["generated_slugs"]) == expected_slugs
    assert result["figures"]["coverage_end_date"] == "2024-01-16"
    assert Path(result["figure_manifest_path"]).exists()
    assert result["review_v2"]["post_master_path"] == str(post_master_path)
    assert result["review_v2"]["comment_master_path"] == str(comment_master_path)
    assert result["review_v2"]["delta_report_path"] == str(delta_report_path)
    assert result["provenance_path"] == str(provenance_output)
    assert post_master_path.exists()
    assert comment_master_path.exists()
    assert delta_report_path.exists()
    assert provenance_output.exists()
    assert str(POST_MASTER_PATH) not in {
        result["review_v2"]["post_master_path"],
        result["review_v2"]["comment_master_path"],
        result["review_v2"]["delta_report_path"],
    }

    summary_payload = json.loads(summary_output.read_text(encoding="utf-8"))
    consistency_payload = json.loads(consistency_output.read_text(encoding="utf-8"))
    delta_payload = json.loads(delta_report_path.read_text(encoding="utf-8"))
    provenance_payload = json.loads(provenance_output.read_text(encoding="utf-8"))
    assert summary_payload["research_db"]["posts"] == 1
    assert summary_payload["paper_quality_v5"]["formal_posts"] == 1
    assert summary_payload["paper_quality_v5"]["coverage_end_date"] == "2024-01-16"
    assert consistency_payload["research_db_path"] == str(db_path)
    assert consistency_payload["status"] == "aligned"
    assert "generated_at_utc" not in consistency_payload
    assert "generated_at" not in delta_payload
    assert "generated_at" not in provenance_output.read_text(encoding="utf-8")
    assert provenance_payload["formal_stage"] == "quality_v5"
    assert provenance_payload["formal_posts"] == 1
    assert provenance_payload["formal_comments"] == 1
    assert provenance_payload["source_db"]["sha256"] == _sha256(db_path)
    assert provenance_payload["files"]["summary"]["sha256"] == _sha256(summary_output)
    assert provenance_payload["files"]["post_review_v2_master"]["line_count"] == 1
    manifest_text = Path(result["figure_manifest_path"]).read_text(encoding="utf-8")
    assert "- 正式覆盖截止日：`2024-01-16`" in manifest_text

    repeated_result = run_build(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        summary_output=summary_output,
        consistency_output=consistency_output,
        provenance_output=provenance_output,
        figure_dir=figure_dir,
        review_v2_post_output_path=post_master_path,
        review_v2_comment_output_path=comment_master_path,
        review_v2_delta_output_path=delta_report_path,
    )
    assert repeated_result["provenance"] == provenance_payload


def test_legacy_import_and_build_artifacts_stay_smoke_test_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_db_path = tmp_path / "legacy.sqlite3"
    research_db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "checkpoint.json"
    summary_output = tmp_path / "out" / "summary.json"
    consistency_output = tmp_path / "out" / "consistency.json"
    provenance_output = tmp_path / "out" / "provenance.json"
    figure_dir = tmp_path / "figures"
    post_master_path = tmp_path / "review_v2" / "post_review_v2_master.jsonl"
    comment_master_path = tmp_path / "review_v2" / "comment_review_v2_master.jsonl"
    delta_report_path = tmp_path / "review_v2" / "post_review_v2_delta_report.json"

    _create_minimal_legacy_db(legacy_db_path)
    monkeypatch.setattr(legacy_import, "INTERIM_DIR", tmp_path / "interim")
    legacy_import.migrate_legacy_sqlite(
        legacy_db_path=legacy_db_path,
        research_db_path=research_db_path,
        mode_name="legacy_quality_v4_migration",
    )
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
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
        db_path=research_db_path,
        checkpoint_path=checkpoint_path,
        summary_output=summary_output,
        consistency_output=consistency_output,
        provenance_output=provenance_output,
        figure_dir=figure_dir,
        review_v2_post_output_path=post_master_path,
        review_v2_comment_output_path=comment_master_path,
        review_v2_delta_output_path=delta_report_path,
    )

    assert summary_output.exists()
    assert consistency_output.exists()
    assert post_master_path.exists()
    assert comment_master_path.exists()
    assert delta_report_path.exists()
    assert provenance_output.exists()
    assert result["review_v2"]["post_master_path"] != str(POST_MASTER_PATH)
    assert result["review_v2"]["comment_master_path"] != str(COMMENT_MASTER_PATH)
    assert result["review_v2"]["delta_report_path"] != str(DELTA_REPORT_PATH)
    assert Path(result["figure_manifest_path"]).exists()
    assert result["summary"]["paper_quality_v5"]["formal_posts"] == 0
    assert result["summary"]["paper_quality_v5"]["formal_comments"] == 0
    assert result["summary"]["paper_quality_v5"]["coverage_end_date"] == "2026-04-10"
    assert result["figures"]["figure_count"] >= 0


def test_run_build_skip_figures_stays_checksum_stable_across_repeated_runs(tmp_path: Path) -> None:
    db_path = tmp_path / "research.sqlite3"
    checkpoint_path = tmp_path / "checkpoint.json"
    summary_output = tmp_path / "out" / "summary.json"
    consistency_output = tmp_path / "out" / "consistency.json"
    provenance_output = tmp_path / "out" / "provenance.json"
    post_master_path = tmp_path / "review_v2" / "post_review_v2_master.jsonl"
    comment_master_path = tmp_path / "review_v2" / "comment_review_v2_master.jsonl"
    delta_report_path = tmp_path / "review_v2" / "post_review_v2_delta_report.json"

    _seed_minimal_paper_scope_db(db_path)
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v5",
                "formal_posts": 1,
                "formal_comments": 1,
                "queued": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    first_result = run_build(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        summary_output=summary_output,
        consistency_output=consistency_output,
        provenance_output=provenance_output,
        review_v2_post_output_path=post_master_path,
        review_v2_comment_output_path=comment_master_path,
        review_v2_delta_output_path=delta_report_path,
        skip_figures=True,
    )
    first_checksums = _checksum_snapshot(
        summary_output,
        consistency_output,
        provenance_output,
        post_master_path,
        comment_master_path,
        delta_report_path,
    )

    second_result = run_build(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        summary_output=summary_output,
        consistency_output=consistency_output,
        provenance_output=provenance_output,
        review_v2_post_output_path=post_master_path,
        review_v2_comment_output_path=comment_master_path,
        review_v2_delta_output_path=delta_report_path,
        skip_figures=True,
    )
    second_checksums = _checksum_snapshot(
        summary_output,
        consistency_output,
        provenance_output,
        post_master_path,
        comment_master_path,
        delta_report_path,
    )

    assert first_result["figures_skipped"] is True
    assert second_result["figures_skipped"] is True
    assert first_result["summary"] == second_result["summary"]
    assert first_result["consistency"] == second_result["consistency"]
    assert first_result["review_v2"] == second_result["review_v2"]
    assert first_result["provenance"] == second_result["provenance"]
    assert first_checksums == second_checksums
