from __future__ import annotations

"""
输入：
- archive/legacy_collection_runtime/data/db/ai4s_xhs.sqlite3
- database/schema.sql
- database/views.sql.template（运行时通过 Python 配置渲染）

输出：
- data/processed/ai4s_legitimacy.sqlite3
- data/interim/legacy_to_research_migration_summary.json

依赖：
- Python 标准库 sqlite3
- ai4s_legitimacy.config.settings
- ai4s_legitimacy.cleaning.normalization
- ai4s_legitimacy.coding.codebook_seed

适用步骤：
- 研究型主库初始化
- legacy 运行库向研究型数据库的第一次迁移
"""

import argparse
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai4s_legitimacy.cleaning.normalization import (
    hash_identifier,
    join_unique,
    mask_name,
    normalize_date,
    normalize_text,
    parse_engagement_text,
)
from ai4s_legitimacy.coding.codebook_seed import (
    LEGACY_WORKFLOW_TO_STAGE_CODE,
    iter_codebook_rows,
    iter_legitimacy_lookup_rows,
    iter_workflow_lookup_rows,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import (
    INTERIM_DIR,
    LEGACY_DB_PATH,
    PLATFORM_CODE,
    PLATFORM_NAME,
    RESEARCH_DB_PATH,
    SCHEMA_PATH,
)
from ai4s_legitimacy.utils.db import (
    connect_sqlite_readonly,
    connect_sqlite_writable,
    init_sqlite_db,
)


@dataclass(frozen=True)
class LegacyLookups:
    query_map: dict[str, str | None]
    like_map: dict[str, int | None]
    comment_count_map: dict[str, int]
    author_name_map: dict[str, str]
    post_label_map: dict[str, sqlite3.Row]
    comment_label_map: dict[str, sqlite3.Row]


def _load_query_map(legacy: sqlite3.Connection) -> dict[str, str | None]:
    mapping: dict[str, list[str]] = defaultdict(list)
    for row in legacy.execute("SELECT note_id, query_text FROM note_candidates ORDER BY id"):
        mapping[str(row["note_id"])].append(str(row["query_text"] or ""))
    return {note_id: join_unique(values) for note_id, values in mapping.items()}


def _load_like_map(legacy: sqlite3.Connection) -> dict[str, int | None]:
    likes: dict[str, int | None] = {}
    for row in legacy.execute("SELECT note_id, likes_text FROM note_candidates ORDER BY id"):
        note_id = str(row["note_id"])
        if note_id in likes and likes[note_id] is not None:
            continue
        likes[note_id] = parse_engagement_text(row["likes_text"])
    return likes


def _load_comment_count_map(legacy: sqlite3.Connection) -> dict[str, int]:
    return {
        str(row["note_id"]): int(row["count"])
        for row in legacy.execute(
            "SELECT note_id, COUNT(*) AS count FROM comments GROUP BY note_id"
        )
    }


def _load_author_names(legacy: sqlite3.Connection) -> dict[str, str]:
    return {
        str(row["author_id"]): str(row["author_name"] or "")
        for row in legacy.execute("SELECT author_id, author_name FROM authors")
        if str(row["author_id"] or "").strip()
    }


def _load_legacy_lookups(legacy: sqlite3.Connection) -> LegacyLookups:
    return LegacyLookups(
        query_map=_load_query_map(legacy),
        like_map=_load_like_map(legacy),
        comment_count_map=_load_comment_count_map(legacy),
        author_name_map=_load_author_names(legacy),
        post_label_map={
            str(row["note_id"]): row
            for row in legacy.execute("SELECT * FROM coding_labels_posts")
        },
        comment_label_map={
            str(row["comment_id"]): row
            for row in legacy.execute("SELECT * FROM coding_labels_comments")
        },
    )


def _seed_theme_lookup_tables(research: sqlite3.Connection) -> None:
    research.executemany(
        "INSERT OR REPLACE INTO ai_tools_lookup (tool_key, display_name, category, display_order) VALUES (?, ?, ?, ?)",
        [
            ("ChatGPT", "ChatGPT", "chatbot", 1),
            ("Claude", "Claude", "chatbot", 2),
            ("Gemini", "Gemini", "chatbot", 3),
            ("DeepSeek", "DeepSeek", "chatbot", 4),
            ("Copilot", "Copilot", "coding_assistant", 5),
            ("Cursor", "Cursor", "coding_assistant", 6),
            ("Kimi", "Kimi", "chatbot", 7),
            ("豆包", "Doubao", "chatbot", 8),
            ("通义", "Tongyi Qianwen", "chatbot", 9),
            ("元宝", "Yuanbao", "chatbot", 10),
            ("讯飞星火", "iFlytek Spark", "chatbot", 11),
            ("GPT-4o", "GPT-4o", "chatbot", 12),
        ],
    )
    research.executemany(
        "INSERT OR REPLACE INTO risk_themes_lookup (risk_key, display_name, display_order) VALUES (?, ?, ?)",
        [
            ("detection", "检测/学术可识别性", 1),
            ("hallucination", "幻觉/生成不可靠", 2),
            ("ethics", "伦理/学术诚信", 3),
        ],
    )
    research.executemany(
        "INSERT OR REPLACE INTO benefit_themes_lookup (benefit_key, display_name, display_order) VALUES (?, ?, ?)",
        [
            ("efficiency", "效率提升", 1),
            ("coding_support", "编程辅助", 2),
            ("idea_generation", "思路生成", 3),
        ],
    )


def _seed_support_tables(research: sqlite3.Connection) -> None:
    research.execute(
        """
        INSERT OR REPLACE INTO platform_sources (
            platform_code, platform_name, public_scope_note, compliance_note
        ) VALUES (?, ?, ?, ?)
        """,
        (
            PLATFORM_CODE,
            PLATFORM_NAME,
            "仅处理公开可获取的小红书帖子、评论与公开媒体文本。",
            "历史自动采集链已归档，当前活跃主线只保留研究导入与分析接口。",
        ),
    )
    research.executemany(
        """
        INSERT OR REPLACE INTO workflow_stage_lookup (
            stage_code, stage_name, display_order, definition
        ) VALUES (?, ?, ?, ?)
        """,
        list(iter_workflow_lookup_rows()),
    )
    research.executemany(
        """
        INSERT OR REPLACE INTO legitimacy_dimension_lookup (
            dimension_code, dimension_name, display_order, definition
        ) VALUES (?, ?, ?, ?)
        """,
        list(iter_legitimacy_lookup_rows()),
    )
    research.executemany(
        """
        INSERT OR REPLACE INTO codebook (
            code_id, code_group, code_name, definition, include_rule, exclude_rule, example
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row.code_id,
                row.code_group,
                row.code_name,
                row.definition,
                row.include_rule,
                row.exclude_rule,
                row.example,
            )
            for row in iter_codebook_rows()
        ],
    )
    _seed_theme_lookup_tables(research)


def _seed_source_queries(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
) -> None:
    for row in legacy.execute(
        "SELECT layer, term, source FROM query_dictionary ORDER BY layer, term"
    ):
        research.execute(
            """
            INSERT OR IGNORE INTO source_queries (platform_code, query_text, query_layer, source_label)
            VALUES (?, ?, ?, ?)
            """,
            (
                PLATFORM_CODE,
                normalize_text(row["term"]),
                normalize_text(row["layer"]),
                normalize_text(row["source"]) or "legacy_query_dictionary",
            ),
        )


def _insert_import_batch(research: sqlite3.Connection, source_db_path: Path) -> int:
    cursor = research.execute(
        """
        INSERT INTO import_batches (
            batch_name, source_description, source_db_path, source_freeze_version, notes
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            "legacy_quality_v4_migration",
            "从 legacy 运行库迁移到研究型主库的首轮基线导入",
            str(source_db_path),
            "quality_v4",
            "迁移保留 legacy sample_status、workflow 和 stance，但 AI 实践与边界协商细码仍待后续人工完善。",
        ),
    )
    return int(cursor.lastrowid)


def _normalize_sample_status(value: str | None) -> str:
    sample_status = normalize_text(value)
    return sample_status if sample_status in {"true", "false", "review_needed"} else "review_needed"


def _build_post_notes(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
) -> str | None:
    return join_unique(
        [
            f"legacy_decided_by={normalize_text(label['decided_by'])}" if label else None,
            f"legacy_review_override={int(label['review_override'])}" if label else None,
            f"legacy_note_type={normalize_text(row['note_type'])}"
            if normalize_text(row["note_type"])
            else None,
            f"legacy_media_count={int(row['media_count'])}",
        ],
        separator="; ",
    )


def _build_post_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
    lookups: LegacyLookups,
) -> tuple[tuple[Any, ...], str | None]:
    note_id = str(row["note_id"])
    author_id = normalize_text(row["author_id"])
    author_name = lookups.author_name_map.get(author_id or "", "")
    workflow_stage = normalize_text(label["workflow_primary"]) if label else ""
    values = (
        note_id,
        PLATFORM_CODE,
        note_id,
        normalize_text(row["crawl_status"]) or "unknown",
        normalize_text(row["canonical_url"]) or normalize_text(row["source_url"]),
        hash_identifier(author_id or normalize_text(row["canonical_url"])),
        mask_name(author_name),
        normalize_date(row["publish_time"]),
        normalize_date(row["updated_at"]) or normalize_date(row["created_at"]),
        normalize_text(row["title"]),
        normalize_text(row["full_text"]),
        lookups.like_map.get(note_id),
        lookups.comment_count_map.get(note_id),
        None,
        lookups.query_map.get(note_id),
        1,
        _normalize_sample_status(label["sample_status"] if label else "review_needed"),
        normalize_text(label["actor_type"]) if label else None,
        normalize_text(label["qs_broad_subject"]) if label else None,
        workflow_stage or None,
        normalize_text(label["attitude_polarity"]) if label else None,
        label["risk_themes_json"] if label else "[]",
        label["ai_tools_json"] if label else "[]",
        label["benefit_themes_json"] if label else "[]",
        batch_id,
        _build_post_notes(row, label),
    )
    return values, (workflow_stage or None)


def _build_post_code_insert_values(
    *,
    note_id: str,
    row: sqlite3.Row,
    label: sqlite3.Row,
    workflow_stage: str | None,
) -> tuple[Any, ...]:
    return (
        note_id,
        "post",
        None,
        LEGACY_WORKFLOW_TO_STAGE_CODE.get(workflow_stage or ""),
        None,
        None,
        None,
        normalize_text(label["decided_by"]) or "legacy_rule",
        normalize_text(row["updated_at"]) or normalize_text(row["created_at"]) or "legacy",
        0.85 if int(label["review_override"] or 0) else 0.65,
        "Legacy post coding migrated. Fine-grained AI practice / legitimacy / boundary codes pending.",
    )


def _insert_posts(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
    *,
    batch_id: int,
    lookups: LegacyLookups,
) -> int:
    post_count = 0
    for row in legacy.execute("SELECT * FROM note_details ORDER BY note_id"):
        note_id = str(row["note_id"])
        label = lookups.post_label_map.get(note_id)
        post_values, workflow_stage = _build_post_insert_values(
            row,
            label,
            batch_id=batch_id,
            lookups=lookups,
        )
        research.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_note_id, legacy_crawl_status, post_url, author_id_hashed, author_name_masked,
                post_date, capture_date, title, content_text, engagement_like, engagement_comment,
                engagement_collect, keyword_query, is_public, sample_status, actor_type, qs_broad_subject,
                workflow_stage, primary_legitimacy_stance, risk_themes_json, ai_tools_json, benefit_themes_json, import_batch_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            post_values,
        )
        if label:
            research.execute(
                """
                INSERT INTO codes (
                    record_id, record_type, parent_id, workflow_stage_code, ai_practice_code,
                    legitimacy_code, boundary_negotiation_code, coder, coding_date, confidence, memo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _build_post_code_insert_values(
                    note_id=note_id,
                    row=row,
                    label=label,
                    workflow_stage=workflow_stage,
                ),
            )
        post_count += 1
    return post_count


def _build_comment_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row | None,
    *,
    batch_id: int,
) -> tuple[Any, ...]:
    return (
        str(row["comment_id"]),
        str(row["note_id"]),
        normalize_text(row["parent_comment_id"]) or None,
        normalize_date(row["comment_time"]),
        normalize_text(row["comment_text"]),
        hash_identifier(
            normalize_text(row["commenter_id"]) or normalize_text(row["commenter_name"])
        ),
        normalize_text(label["attitude_polarity"]) if label else None,
        normalize_text(label["controversy_type"]) if label else None,
        label["benefit_themes_json"] if label else "[]",
        1 if normalize_text(row["parent_comment_id"]) else 0,
        batch_id,
    )


def _build_comment_code_insert_values(
    row: sqlite3.Row,
    label: sqlite3.Row,
) -> tuple[Any, ...]:
    workflow_stage = normalize_text(label["workflow_primary"])
    controversy = normalize_text(label["controversy_type"])
    return (
        str(row["comment_id"]),
        "comment",
        str(row["note_id"]),
        LEGACY_WORKFLOW_TO_STAGE_CODE.get(workflow_stage),
        None,
        None,
        "boundary.assistance_vs_substitution" if controversy == "risk" else None,
        "legacy_comment_inheritance",
        normalize_text(row["updated_at"]) or normalize_text(row["created_at"]) or "legacy",
        0.6,
        "Legacy comment coding migrated. Stance retained; fine-grained legitimacy code pending manual review.",
    )


def _insert_comments(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
    *,
    batch_id: int,
    lookups: LegacyLookups,
) -> int:
    comment_count = 0
    for row in legacy.execute("SELECT * FROM comments ORDER BY comment_id"):
        label = lookups.comment_label_map.get(str(row["comment_id"]))
        research.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, parent_comment_id, comment_date, comment_text,
                commenter_id_hashed, stance, legitimacy_basis, benefit_themes_json, is_reply, import_batch_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _build_comment_insert_values(row, label, batch_id=batch_id),
        )
        if label:
            research.execute(
                """
                INSERT INTO codes (
                    record_id, record_type, parent_id, workflow_stage_code, ai_practice_code,
                    legitimacy_code, boundary_negotiation_code, coder, coding_date, confidence, memo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _build_comment_code_insert_values(row, label),
            )
        comment_count += 1
    return comment_count


def _update_import_batch_counts(
    research: sqlite3.Connection,
    *,
    batch_id: int,
    post_count: int,
    comment_count: int,
) -> None:
    research.execute(
        """
        UPDATE import_batches
        SET record_post_count=?, record_comment_count=?
        WHERE batch_id=?
        """,
        (post_count, comment_count, batch_id),
    )


def _build_migration_summary(
    *,
    legacy_db_path: Path,
    research_db_path: Path,
    post_count: int,
    comment_count: int,
) -> dict[str, object]:
    return {
        "legacy_db_path": str(legacy_db_path),
        "research_db_path": str(research_db_path),
        "batch_name": "legacy_quality_v4_migration",
        "posts_migrated": post_count,
        "comments_migrated": comment_count,
        "status": "ok",
    }


def _write_migration_summary(summary: dict[str, object]) -> Path:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = INTERIM_DIR / "legacy_to_research_migration_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def migrate_legacy_sqlite(
    legacy_db_path: Path = LEGACY_DB_PATH,
    research_db_path: Path = RESEARCH_DB_PATH,
    *,
    overwrite: bool = False,
) -> Path:
    if not legacy_db_path.exists():
        raise FileNotFoundError(f"Legacy DB not found: {legacy_db_path}")
    if research_db_path.exists():
        if not overwrite:
            raise FileExistsError(f"Research DB already exists: {research_db_path}")
        research_db_path.unlink()

    init_sqlite_db(
        research_db_path,
        SCHEMA_PATH,
        views_sql=render_views_sql(),
    )
    with connect_sqlite_readonly(legacy_db_path) as legacy, connect_sqlite_writable(
        research_db_path
    ) as research:
        batch_id = _insert_import_batch(research, legacy_db_path)
        _seed_support_tables(research)
        _seed_source_queries(legacy, research)
        lookups = _load_legacy_lookups(legacy)
        post_count = _insert_posts(
            legacy,
            research,
            batch_id=batch_id,
            lookups=lookups,
        )
        comment_count = _insert_comments(
            legacy,
            research,
            batch_id=batch_id,
            lookups=lookups,
        )
        _update_import_batch_counts(
            research,
            batch_id=batch_id,
            post_count=post_count,
            comment_count=comment_count,
        )
        research.commit()

    summary = _build_migration_summary(
        legacy_db_path=legacy_db_path,
        research_db_path=research_db_path,
        post_count=post_count,
        comment_count=comment_count,
    )
    return _write_migration_summary(summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate legacy AI4S runtime SQLite data into the research-oriented schema."
    )
    parser.add_argument("--legacy-db", type=Path, default=LEGACY_DB_PATH)
    parser.add_argument("--research-db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary_path = migrate_legacy_sqlite(
        args.legacy_db,
        args.research_db,
        overwrite=args.overwrite,
    )
    print(summary_path)


if __name__ == "__main__":
    main()
