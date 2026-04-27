from __future__ import annotations

import sqlite3
from pathlib import Path

from ._legacy_import_contracts import (
    CODE_INSERT_SQL,
    COMMENT_INSERT_SQL,
    LegacyImportMode,
    POST_INSERT_SQL,
    LegacyLookups,
    MigrationCounts,
)
from ._legacy_import_records import prepare_comment_insert, prepare_post_insert
from ._legacy_import_seed import insert_import_batch, seed_research_reference_data


def _insert_post_row(research: sqlite3.Connection, post_values: tuple[object, ...]) -> None:
    research.execute(POST_INSERT_SQL, post_values)


def _insert_comment_row(
    research: sqlite3.Connection,
    comment_values: tuple[object, ...],
) -> None:
    research.execute(COMMENT_INSERT_SQL, comment_values)


def _insert_code_row(research: sqlite3.Connection, code_values: tuple[object, ...]) -> None:
    research.execute(CODE_INSERT_SQL, code_values)


def _migrate_posts(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
    *,
    batch_id: int,
    lookups: LegacyLookups,
    mode: LegacyImportMode,
) -> int:
    post_count = 0
    for row in legacy.execute("SELECT * FROM note_details ORDER BY note_id"):
        note_id = str(row["note_id"])
        label = lookups.post_label_map.get(note_id)
        prepared = prepare_post_insert(
            row,
            label,
            batch_id=batch_id,
            lookups=lookups,
            preserve_legacy_labels=mode.preserve_legacy_labels,
        )
        _insert_post_row(research, prepared.post_values)
        if prepared.code_values is not None:
            _insert_code_row(research, prepared.code_values)
        post_count += 1
    return post_count


def _migrate_comments(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
    *,
    batch_id: int,
    lookups: LegacyLookups,
    mode: LegacyImportMode,
) -> int:
    comment_count = 0
    for row in legacy.execute("SELECT * FROM comments ORDER BY comment_id"):
        label = lookups.comment_label_map.get(str(row["comment_id"]))
        prepared = prepare_comment_insert(
            row,
            label,
            batch_id=batch_id,
            preserve_legacy_labels=mode.preserve_legacy_labels,
        )
        _insert_comment_row(research, prepared.comment_values)
        if prepared.code_values is not None:
            _insert_code_row(research, prepared.code_values)
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


def run_legacy_migration(
    legacy: sqlite3.Connection,
    research: sqlite3.Connection,
    *,
    legacy_db_path: Path,
    lookups: LegacyLookups,
    mode: LegacyImportMode,
) -> MigrationCounts:
    batch_id = insert_import_batch(research, legacy_db_path, mode=mode)
    seed_research_reference_data(legacy, research)
    post_count = _migrate_posts(
        legacy,
        research,
        batch_id=batch_id,
        lookups=lookups,
        mode=mode,
    )
    comment_count = _migrate_comments(
        legacy,
        research,
        batch_id=batch_id,
        lookups=lookups,
        mode=mode,
    )
    counts = MigrationCounts(post_count=post_count, comment_count=comment_count)
    _update_import_batch_counts(
        research,
        batch_id=batch_id,
        post_count=counts.post_count,
        comment_count=counts.comment_count,
    )
    research.commit()
    return counts
