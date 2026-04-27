from __future__ import annotations

import sqlite3
from collections import defaultdict

from ai4s_legitimacy.cleaning.normalization import join_unique, parse_engagement_text

from ._legacy_import_contracts import LegacyLookups


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


def _load_row_map(
    legacy: sqlite3.Connection,
    *,
    sql: str,
    key_field: str,
) -> dict[str, sqlite3.Row]:
    return {str(row[key_field]): row for row in legacy.execute(sql)}


def load_legacy_lookups(legacy: sqlite3.Connection) -> LegacyLookups:
    return LegacyLookups(
        query_map=_load_query_map(legacy),
        like_map=_load_like_map(legacy),
        comment_count_map=_load_comment_count_map(legacy),
        author_name_map=_load_author_names(legacy),
        post_label_map=_load_row_map(
            legacy,
            sql="SELECT * FROM coding_labels_posts",
            key_field="note_id",
        ),
        comment_label_map=_load_row_map(
            legacy,
            sql="SELECT * FROM coding_labels_comments",
            key_field="comment_id",
        ),
    )
