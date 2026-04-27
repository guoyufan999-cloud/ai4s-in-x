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

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai4s_legitimacy.collection.audit_snapshot import export_quality_v4_audit_snapshot
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import (
    INTERIM_DIR,
    LEGACY_DB_PATH,
    PLATFORM_CODE as SETTINGS_PLATFORM_CODE,
    RESEARCH_DB_PATH,
    SCHEMA_PATH,
)
from ai4s_legitimacy.utils.db import (
    checkpoint_sqlite_wal,
    connect_sqlite_readonly,
    connect_sqlite_writable,
    init_sqlite_db,
)

from ._legacy_import_contracts import (
    LEGACY_IMPORT_MODES,
    REBASELINE_QUALITY_V5_MODE,
    LegacyLookups,
    LegacyImportMode,
    MigrationCounts,
    PreparedCommentInsert,
    PreparedPostInsert,
)
from ._legacy_import_lookups import load_legacy_lookups
from ._legacy_import_records import prepare_comment_insert, prepare_post_insert
from ._legacy_import_run import run_legacy_migration


PLATFORM_CODE = SETTINGS_PLATFORM_CODE


def _load_legacy_lookups(legacy) -> LegacyLookups:
    return load_legacy_lookups(legacy)


def _prepare_post_insert(
    row,
    label,
    *,
    batch_id: int,
    lookups: LegacyLookups,
) -> PreparedPostInsert:
    return prepare_post_insert(
        row,
        label,
        batch_id=batch_id,
        lookups=lookups,
    )


def _prepare_comment_insert(
    row,
    label,
    *,
    batch_id: int,
) -> PreparedCommentInsert:
    return prepare_comment_insert(
        row,
        label,
        batch_id=batch_id,
    )


def _build_migration_summary(
    *,
    legacy_db_path: Path,
    research_db_path: Path,
    counts: MigrationCounts,
    mode: LegacyImportMode,
) -> dict[str, object]:
    return {
        "legacy_db_path": str(legacy_db_path),
        "research_db_path": str(research_db_path),
        "batch_name": mode.batch_name,
        "mode": mode.name,
        "source_freeze_version": mode.source_freeze_version,
        "preserve_legacy_labels": mode.preserve_legacy_labels,
        "posts_migrated": counts.post_count,
        "comments_migrated": counts.comment_count,
        "status": "ok",
    }


def _write_migration_summary(
    summary: dict[str, object],
    *,
    interim_dir: Path = INTERIM_DIR,
    mode: LegacyImportMode,
) -> Path:
    output_dir = interim_dir / mode.summary_subdir if mode.summary_subdir else interim_dir
    interim_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / mode.summary_filename
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def migrate_legacy_sqlite(
    legacy_db_path: Path = LEGACY_DB_PATH,
    research_db_path: Path = RESEARCH_DB_PATH,
    *,
    overwrite: bool = False,
    mode_name: str = REBASELINE_QUALITY_V5_MODE.name,
    audit_snapshot_path: Path | None = None,
) -> Path:
    if mode_name not in LEGACY_IMPORT_MODES:
        valid_modes = ", ".join(sorted(LEGACY_IMPORT_MODES))
        raise ValueError(f"Unknown legacy import mode: {mode_name}. Expected one of: {valid_modes}")
    mode = LEGACY_IMPORT_MODES[mode_name]
    if not legacy_db_path.exists():
        raise FileNotFoundError(f"Legacy DB not found: {legacy_db_path}")
    if research_db_path.exists():
        if not overwrite:
            raise FileExistsError(f"Research DB already exists: {research_db_path}")
        research_db_path.unlink()

    if audit_snapshot_path is not None:
        export_quality_v4_audit_snapshot(output_path=audit_snapshot_path)

    init_sqlite_db(
        research_db_path,
        SCHEMA_PATH,
        views_sql=render_views_sql(),
    )
    with connect_sqlite_readonly(legacy_db_path) as legacy, connect_sqlite_writable(
        research_db_path
    ) as research:
        counts = run_legacy_migration(
            legacy,
            research,
            legacy_db_path=legacy_db_path,
            lookups=_load_legacy_lookups(legacy),
            mode=mode,
        )
    checkpoint_sqlite_wal(research_db_path)

    summary = _build_migration_summary(
        legacy_db_path=legacy_db_path,
        research_db_path=research_db_path,
        counts=counts,
        mode=mode,
    )
    return _write_migration_summary(summary, interim_dir=INTERIM_DIR, mode=mode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate legacy AI4S runtime SQLite data into the research-oriented schema."
    )
    parser.add_argument("--legacy-db", type=Path, default=LEGACY_DB_PATH)
    parser.add_argument("--research-db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--mode",
        choices=sorted(LEGACY_IMPORT_MODES),
        default=REBASELINE_QUALITY_V5_MODE.name,
    )
    parser.add_argument(
        "--audit-snapshot",
        type=Path,
        default=None,
        help="Optional path for a one-time quality_v4 audit snapshot before rebuilding the staging DB.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary_path = migrate_legacy_sqlite(
        args.legacy_db,
        args.research_db,
        overwrite=args.overwrite,
        mode_name=args.mode,
        audit_snapshot_path=args.audit_snapshot,
    )
    print(summary_path)


if __name__ == "__main__":
    main()
