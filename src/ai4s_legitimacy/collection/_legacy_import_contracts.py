from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LegacyLookups:
    query_map: dict[str, str | None]
    like_map: dict[str, int | None]
    comment_count_map: dict[str, int]
    author_name_map: dict[str, str]
    post_label_map: dict[str, sqlite3.Row]
    comment_label_map: dict[str, sqlite3.Row]


@dataclass(frozen=True)
class PreparedPostInsert:
    post_values: tuple[Any, ...]
    code_values: tuple[Any, ...] | None


@dataclass(frozen=True)
class PreparedCommentInsert:
    comment_values: tuple[Any, ...]
    code_values: tuple[Any, ...] | None


@dataclass(frozen=True)
class MigrationCounts:
    post_count: int
    comment_count: int


@dataclass(frozen=True)
class LegacyImportMode:
    name: str
    batch_name: str
    source_freeze_version: str
    preserve_legacy_labels: bool
    summary_filename: str
    summary_subdir: str
    notes: str


POST_INSERT_SQL = """
    INSERT INTO posts (
        post_id, platform, legacy_note_id, legacy_crawl_status, post_url, author_id_hashed, author_name_masked,
        post_date, capture_date, title, content_text, engagement_like, engagement_comment,
        engagement_collect, keyword_query, is_public, sample_status, decision_reason, actor_type, qs_broad_subject,
        workflow_domain, workflow_stage, primary_legitimacy_stance, has_legitimacy_evaluation, primary_legitimacy_code,
        boundary_discussion, primary_boundary_type, uncertainty_note,
        risk_themes_json, ai_tools_json, benefit_themes_json, import_batch_id, notes
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
"""

COMMENT_INSERT_SQL = """
    INSERT INTO comments (
        comment_id, post_id, parent_comment_id, comment_date, comment_text,
        commenter_id_hashed, stance, legitimacy_basis, workflow_domain, workflow_stage, has_legitimacy_evaluation,
        primary_legitimacy_code, boundary_discussion, primary_boundary_type,
        uncertainty_note, benefit_themes_json, is_reply, import_batch_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

CODE_INSERT_SQL = """
    INSERT INTO codes (
        record_id, record_type, parent_id, workflow_domain_code, workflow_stage_code,
        legitimacy_code, boundary_discussion, boundary_negotiation_code, coder, coding_date, confidence, memo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

DEFAULT_QUERY_LAYER = "unspecified"
DEFAULT_SOURCE_LABEL = "legacy_query_dictionary"

LEGACY_QUALITY_V4_MODE = LegacyImportMode(
    name="legacy_quality_v4_migration",
    batch_name="legacy_quality_v4_migration",
    source_freeze_version="quality_v4",
    preserve_legacy_labels=True,
    summary_filename="legacy_to_research_migration_summary.json",
    summary_subdir="",
    notes=(
        "迁移保留 legacy sample_status 与 workflow 线索，并按 P/G/T + 合法性 + boundary_discussion 主框架写入研究型主库。"
    ),
)

REBASELINE_QUALITY_V5_MODE = LegacyImportMode(
    name="rebaseline_quality_v5_staging",
    batch_name="rebaseline_quality_v5_staging",
    source_freeze_version="quality_v5",
    preserve_legacy_labels=False,
    summary_filename="rebaseline_quality_v5_staging_summary.json",
    summary_subdir="rebaseline_quality_v5",
    notes="重建 staging 库仅保留结构性原始内容；旧标签、旧主题字段与 codes 不导入。",
)

LEGACY_IMPORT_MODES = {
    LEGACY_QUALITY_V4_MODE.name: LEGACY_QUALITY_V4_MODE,
    REBASELINE_QUALITY_V5_MODE.name: REBASELINE_QUALITY_V5_MODE,
}
