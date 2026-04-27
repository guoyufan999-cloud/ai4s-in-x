from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

import ai4s_legitimacy.analysis.excerpt_extraction as excerpt_extraction
from ai4s_legitimacy.analysis.excerpt_extraction import (
    EXCERPTS_DIR,
    MAX_CHARS_DEFAULT,
    build_parser,
    deidentify_text,
    export_excerpts,
    extract_excerpts_by_boundary_code,
    extract_excerpts_by_stance,
    extract_excerpts_by_workflow_stage,
    format_excerpts_markdown,
    generate_all_excerpts,
    main,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import checkpoint_sqlite_wal, init_sqlite_db


GENERATED_AT = "2026-04-10T00:00:00"
EXPECTED_RECORD_KEYS = {
    "record_id",
    "record_type",
    "coding_label",
    "excerpt",
    "record_date",
}


def _create_excerpt_test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.sqlite3"
    schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    init_sqlite_db(db_path, schema_path, views_sql=render_views_sql())

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
            content_text, post_date, is_public, import_batch_id, legacy_crawl_status, actor_type,
            qs_broad_subject, decision, review_status
        ) VALUES (
            'p1', 'xhs', 'true', '选题与问题定义', '积极采用',
            '和AI讨论课题思路', '2024-01-01', 1, 1, 'crawled', 'graduate_student',
            'Engineering & Technology', '纳入', 'reviewed'
        )
        """
    )
    conn.execute(
        """
        INSERT INTO comments (
            comment_id, post_id, comment_text, stance, comment_date, is_reply, import_batch_id,
            decision, review_status
        ) VALUES (
            'c1', 'p1', '我也是这样用AI的', '积极采用', '2024-01-01', 0, 1,
            '纳入', 'reviewed'
        )
        """
    )
    conn.execute(
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
    conn.execute(
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
    conn.execute(
        """
        INSERT INTO codes (
            record_id, record_type, parent_id, boundary_negotiation_code,
            coder, coding_date, confidence, memo
        ) VALUES (
            'c1', 'comment', 'p1', 'boundary.assistance_vs_substitution',
            'tester', '2024-01-01', 1.0, 'test'
        )
        """
    )
    conn.commit()
    conn.close()
    checkpoint_sqlite_wal(db_path)
    return db_path


def test_deidentify_text_masks_patterns_and_truncates() -> None:
    text = (
        "Visit https://example.com and contact test@example.com "
        "微信号: codex_friend " + ("a " * 100)
    )

    cleaned = deidentify_text(text, max_chars=60)

    assert "[URL]" in cleaned
    assert "[email]" in cleaned
    assert "[ID]" in cleaned
    assert cleaned.endswith("...")
    assert "\n" not in cleaned
    assert deidentify_text("") == ""


def test_extractors_keep_record_contract_across_category_types(tmp_path: Path) -> None:
    db_path = _create_excerpt_test_db(tmp_path)

    excerpt_groups = [
        (
            extract_excerpts_by_workflow_stage("选题与问题定义", limit=5, db_path=db_path),
            "post",
            "p1",
            "选题与问题定义",
        ),
        (
            extract_excerpts_by_stance("积极采用", record_type="post", limit=5, db_path=db_path),
            "post",
            "p1",
            "积极采用",
        ),
        (
            extract_excerpts_by_stance("积极采用", record_type="comment", limit=5, db_path=db_path),
            "comment",
            "c1",
            "积极采用",
        ),
        (
            extract_excerpts_by_boundary_code(
                "boundary.assistance_vs_substitution",
                limit=5,
                db_path=db_path,
            ),
            "comment",
            "c1",
            "boundary.assistance_vs_substitution",
        ),
    ]

    for excerpts, expected_type, expected_id, expected_label in excerpt_groups:
        assert len(excerpts) == 1
        record = excerpts[0]
        assert set(record) == EXPECTED_RECORD_KEYS
        assert record["record_type"] == expected_type
        assert record["record_id"] == expected_id
        assert record["coding_label"] == expected_label
        assert record["record_date"] == "2024-01-01"
        assert record["excerpt"]


def test_extract_excerpts_by_stance_rejects_invalid_record_type(tmp_path: Path) -> None:
    db_path = _create_excerpt_test_db(tmp_path)

    with pytest.raises(ValueError, match="record_type must be 'post' or 'comment'"):
        extract_excerpts_by_stance(
            "积极采用",
            record_type="invalid",
            limit=5,
            db_path=db_path,
        )


def test_markdown_and_export_keep_generated_at_opt_in_only(tmp_path: Path) -> None:
    db_path = _create_excerpt_test_db(tmp_path)
    excerpts = extract_excerpts_by_stance("积极采用", record_type="comment", limit=5, db_path=db_path)

    markdown = format_excerpts_markdown(excerpts, "test_label")
    markdown_with_timestamp = format_excerpts_markdown(
        excerpts,
        "test_label",
        generated_at=GENERATED_AT,
    )

    assert "# test_label — 分析摘录" in markdown
    assert "摘录 1" in markdown
    assert "生成时间" not in markdown
    assert f"生成时间：{GENERATED_AT}" in markdown_with_timestamp

    export_dir = tmp_path / "exports"
    default_export_path = export_excerpts(
        "boundary_boundary_assistance_vs_substitution",
        excerpts,
        output_dir=export_dir,
    )
    audited_export_path = export_excerpts(
        "boundary_boundary_assistance_vs_substitution_audit",
        excerpts,
        output_dir=export_dir,
        generated_at=GENERATED_AT,
    )

    default_text = default_export_path.read_text(encoding="utf-8")
    audited_text = audited_export_path.read_text(encoding="utf-8")

    assert (
        "# boundary boundary assistance vs substitution — 分析摘录" in default_text
    )
    assert "生成时间" not in default_text
    assert f"生成时间：{GENERATED_AT}" in audited_text


def test_generate_all_excerpts_keeps_slug_contract_and_order(tmp_path: Path) -> None:
    db_path = _create_excerpt_test_db(tmp_path)

    paths = generate_all_excerpts(db_path=db_path, output_dir=tmp_path / "batch", limit=5)

    assert all(isinstance(path, Path) for path in paths)
    assert [path.name for path in paths] == [
        "workflow_选题与问题定义.md",
        "post_stance_积极采用.md",
        "comment_stance_积极采用.md",
        "boundary_boundary_assistance_vs_substitution.md",
    ]
    for path in paths:
        assert "生成时间" not in path.read_text(encoding="utf-8")

    audited_paths = generate_all_excerpts(
        db_path=db_path,
        output_dir=tmp_path / "batch_audit",
        limit=5,
        generated_at=GENERATED_AT,
    )

    assert [path.name for path in audited_paths] == [path.name for path in paths]
    for path in audited_paths:
        assert f"生成时间：{GENERATED_AT}" in path.read_text(encoding="utf-8")


def test_build_parser_keeps_defaults_and_main_prompt(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    parser = build_parser()
    args = parser.parse_args([])

    assert args.db == RESEARCH_DB_PATH
    assert args.output_dir == EXCERPTS_DIR
    assert args.max_chars == MAX_CHARS_DEFAULT
    assert args.limit == 10
    assert args.batch is False

    generated_path = tmp_path / "workflow_选题与问题定义.md"

    def fake_generate_all_excerpts(
        db_path: Path,
        output_dir: Path,
        max_chars: int,
        limit: int,
        *,
        generated_at: str | None = None,
    ) -> list[Path]:
        assert db_path == RESEARCH_DB_PATH
        assert output_dir == EXCERPTS_DIR
        assert max_chars == MAX_CHARS_DEFAULT
        assert limit == 10
        assert generated_at is None
        return [generated_path]

    monkeypatch.setattr(excerpt_extraction, "generate_all_excerpts", fake_generate_all_excerpts)

    monkeypatch.setattr(sys, "argv", ["excerpt_extraction"])
    main()
    prompt_output = capsys.readouterr()
    assert prompt_output.out.strip() == "Use --batch to generate all excerpt files."

    monkeypatch.setattr(sys, "argv", ["excerpt_extraction", "--batch"])
    main()
    batch_output = capsys.readouterr()
    assert batch_output.out.strip() == str(generated_path)
