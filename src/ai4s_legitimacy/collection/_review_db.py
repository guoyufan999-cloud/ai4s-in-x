from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from typing import Any


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        str(row["name"])
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def ensure_json_list(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return parsed
        return [stripped]
    return [value]


def coalesce_mapping_value(
    mapping: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def normalize_record_identity(row: dict[str, Any]) -> tuple[str, str]:
    record_type = str(row.get("record_type") or "").strip()
    if record_type == "post":
        record_id = str(
            coalesce_mapping_value(row, "record_id", "post_id", default="")
        ).strip()
    elif record_type == "comment":
        record_id = str(
            coalesce_mapping_value(row, "record_id", "comment_id", default="")
        ).strip()
    else:
        post_id = str(row.get("post_id") or "").strip()
        comment_id = str(row.get("comment_id") or "").strip()
        # Reviewed comment rows often carry both `comment_id` and parent `post_id`.
        # Prefer the comment identity so comment-side effects and codes land correctly.
        if comment_id:
            record_type, record_id = "comment", comment_id
        elif post_id:
            record_type, record_id = "post", post_id
        else:
            raise ValueError("Unable to resolve record_type/record_id from reviewed row")
    if not record_id:
        raise ValueError("Reviewed row is missing record_id")
    return record_type, record_id


def load_reviewed_payloads(
    connection: sqlite3.Connection,
    *,
    review_phase: str,
    record_type: str | None = None,
) -> dict[str, dict[str, Any]]:
    params: list[Any] = [review_phase]
    sql = """
        SELECT record_id, payload_json
        FROM reviewed_records
        WHERE review_phase = ?
    """
    if record_type is not None:
        sql += " AND record_type = ?"
        params.append(record_type)
    sql += " ORDER BY id"
    payloads: dict[str, dict[str, Any]] = {}
    for row in connection.execute(sql, tuple(params)).fetchall():
        payloads[str(row["record_id"])] = json.loads(str(row["payload_json"]))
    return payloads


def first_nonempty(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return default


def iter_nonempty_strings(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
