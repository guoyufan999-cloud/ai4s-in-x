from __future__ import annotations

import sqlite3
from pathlib import Path

from ai4s_legitimacy.cleaning.normalization import normalize_text
from ai4s_legitimacy.coding.codebook_seed import (
    iter_codebook_rows,
    iter_legitimacy_lookup_rows,
    iter_workflow_domain_lookup_rows,
    iter_workflow_lookup_rows,
)
from ai4s_legitimacy.config.settings import PLATFORM_CODE, PLATFORM_NAME

from ._legacy_import_contracts import (
    DEFAULT_QUERY_LAYER,
    DEFAULT_SOURCE_LABEL,
    LegacyImportMode,
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
        INSERT OR REPLACE INTO workflow_domain_lookup (
            domain_code, domain_name, display_order, definition
        ) VALUES (?, ?, ?, ?)
        """,
        list(iter_workflow_domain_lookup_rows()),
    )
    research.executemany(
        """
        INSERT OR REPLACE INTO workflow_stage_lookup (
            stage_code, stage_name, domain_code, display_order, definition
        ) VALUES (?, ?, ?, ?, ?)
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
        query_layer = normalize_text(row["layer"]) or DEFAULT_QUERY_LAYER
        source_label = normalize_text(row["source"]) or DEFAULT_SOURCE_LABEL
        research.execute(
            """
            INSERT OR IGNORE INTO source_queries (platform_code, query_text, query_layer, source_label)
            VALUES (?, ?, ?, ?)
            """,
            (
                PLATFORM_CODE,
                normalize_text(row["term"]),
                query_layer,
                source_label,
            ),
        )


def seed_research_reference_data(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
) -> None:
    _seed_support_tables(research)
    _seed_source_queries(legacy, research)


def insert_import_batch(
    research: sqlite3.Connection,
    source_db_path: Path,
    *,
    mode: LegacyImportMode,
) -> int:
    cursor = research.execute(
        """
        INSERT INTO import_batches (
            batch_name, source_description, source_db_path, source_freeze_version, notes
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            mode.batch_name,
            "从 legacy 运行库迁移到研究型主库的结构化导入",
            str(source_db_path),
            mode.source_freeze_version,
            mode.notes,
        ),
    )
    return int(cursor.lastrowid)
