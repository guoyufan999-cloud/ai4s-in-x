from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import REBASELINE_STAGING_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_writable

from ._canonical_db import apply_canonical_row_to_db, ensure_canonical_schema
from ._canonical_review import canonicalize_review_row
from ._review_db import (
    coalesce_mapping_value,
    normalize_record_identity,
    table_columns,
)
from .canonical_schema import DECISION_VALUES, canonical_record_identity, validate_canonical_row

APPROVED_REVIEW_STATUSES = {"approved", "reviewed", "revised"}
REVIEW_DECISION_SAMPLE_STATUSES = {"true", "false", "review_needed"}
REVIEW_DECISION_INCLUSION_VALUES = {"纳入", "剔除", "待复核"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _require_review_text_value(
    row: dict[str, Any],
    *,
    review_phase: str,
    field_name: str,
    aliases: tuple[str, ...],
    allowed_values: set[str] | None = None,
) -> str:
    value = str(coalesce_mapping_value(row, *aliases, default="")).strip()
    if not value:
        raise ValueError(
            f"Approved {review_phase} row missing required review decision field: {field_name}"
        )
    if allowed_values is not None and value not in allowed_values:
        expected = ", ".join(sorted(allowed_values))
        raise ValueError(
            f"Approved {review_phase} row has invalid {field_name}: {value!r}. "
            f"Expected one of: {expected}"
        )
    return value


def _validate_phase_decision_fields(row: dict[str, Any]) -> tuple[str, str]:
    review_phase = str(row.get("review_phase") or "").strip()

    decision = str(row.get("decision") or "").strip()
    if decision in DECISION_VALUES:
        return canonical_record_identity(row)

    if review_phase == "rescreen_posts":
        _require_review_text_value(
            row,
            review_phase=review_phase,
            field_name="sample_status",
            aliases=("sample_status",),
            allowed_values=REVIEW_DECISION_SAMPLE_STATUSES,
        )
    elif review_phase in {"post_review_v2", "comment_review_v2"}:
        _require_review_text_value(
            row,
            review_phase=review_phase,
            field_name="inclusion_decision",
            aliases=("inclusion_decision", "是否纳入"),
            allowed_values=REVIEW_DECISION_INCLUSION_VALUES,
        )
        _require_review_text_value(
            row,
            review_phase=review_phase,
            field_name="纳入或剔除理由",
            aliases=("reason", "纳入或剔除理由"),
        )

    return normalize_record_identity(row)


def _upsert_review_run(
    connection,
    *,
    row: dict[str, Any],
    source_file: Path,
) -> None:
    connection.execute(
        """
        INSERT INTO review_runs (
            run_id, review_phase, model, reviewer, review_date, source_file, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            review_phase = excluded.review_phase,
            model = excluded.model,
            reviewer = excluded.reviewer,
            review_date = excluded.review_date,
            source_file = excluded.source_file,
            notes = excluded.notes
        """,
        (
            str(row["run_id"]),
            str(row["review_phase"]),
            coalesce_mapping_value(row, "model"),
            str(row["reviewer"]),
            str(row["review_date"]),
            str(source_file),
            _stringify_run_notes(coalesce_mapping_value(row, "notes")),
        ),
    )


def _stringify_run_notes(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _store_reviewed_record(
    connection,
    *,
    row: dict[str, Any],
    record_type: str,
    record_id: str,
) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO reviewed_records (
            run_id, record_id, record_type, review_phase, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(row["run_id"]),
            record_id,
            record_type,
            str(row["review_phase"]),
            json.dumps(row, ensure_ascii=False),
        ),
    )


def _load_base_row(
    connection,
    *,
    record_type: str,
    record_id: str,
) -> dict[str, Any]:
    if record_type == "post":
        row = connection.execute(
            "SELECT * FROM posts WHERE post_id = ?",
            (record_id,),
        ).fetchone()
    else:
        row = connection.execute(
            "SELECT * FROM comments WHERE comment_id = ?",
            (record_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Reviewed row targets missing {record_type}: {record_id}")
    return dict(row)


def _insert_code_row(
    connection,
    *,
    row: dict[str, Any],
    record_id: str,
    record_type: str,
) -> None:
    columns = table_columns(connection, "codes")
    payload = {
        "record_id": record_id,
        "record_type": record_type,
        "parent_id": coalesce_mapping_value(row, "post_id", "parent_id"),
        "workflow_domain_code": coalesce_mapping_value(row, "workflow_domain_code"),
        "workflow_stage_code": coalesce_mapping_value(row, "workflow_stage_code"),
        "ai_practice_code": coalesce_mapping_value(row, "ai_practice_code"),
        "legitimacy_code": coalesce_mapping_value(row, "legitimacy_code"),
        "boundary_discussion": row.get("boundary_discussion", 0),
        "boundary_negotiation_code": coalesce_mapping_value(row, "boundary_negotiation_code"),
        "boundary_type_code": coalesce_mapping_value(
            row,
            "boundary_type_code",
            "boundary_negotiation_code",
        ),
        "coder": str(row["reviewer"]),
        "coding_date": str(row["review_date"]),
        "confidence": coalesce_mapping_value(row, "confidence"),
        "memo": coalesce_mapping_value(row, "memo"),
    }
    available_items = [(field, value) for field, value in payload.items() if field in columns]
    if not available_items:
        return
    field_sql = ", ".join(field for field, _ in available_items)
    placeholder_sql = ", ".join("?" for _ in available_items)
    connection.execute(
        f"INSERT INTO codes ({field_sql}) VALUES ({placeholder_sql})",
        [value for _, value in available_items],
    )


def import_reviewed_file(
    *,
    reviewed_path: Path,
    db_path: Path = REBASELINE_STAGING_DB_PATH,
) -> dict[str, Any]:
    rows = _load_jsonl(reviewed_path)
    if not rows:
        raise ValueError(f"No reviewed rows found in {reviewed_path}")

    with connect_sqlite_writable(db_path) as connection:
        ensure_canonical_schema(connection)
        imported = 0
        for row in rows:
            review_status = str(row.get("review_status") or "").strip()
            if review_status not in APPROVED_REVIEW_STATUSES:
                raise ValueError(
                    f"Reviewed import requires review_status in {sorted(APPROVED_REVIEW_STATUSES)}, "
                    f"got {review_status!r}"
                )
            for required in ("run_id", "review_phase", "reviewer", "review_date"):
                if str(row.get(required) or "").strip() == "":
                    raise ValueError(f"Reviewed row missing required field: {required}")

            record_type, record_id = _validate_phase_decision_fields(row)
            base_row = _load_base_row(connection, record_type=record_type, record_id=record_id)
            canonical = canonicalize_review_row(
                row,
                base_row=base_row,
                review_phase=str(row.get("review_phase") or "").strip(),
            )
            canonical["review_status"] = "revised" if review_status == "revised" else "reviewed"
            canonical = validate_canonical_row(canonical)

            _upsert_review_run(connection, row=canonical, source_file=reviewed_path)
            _store_reviewed_record(
                connection,
                row=canonical,
                record_type=canonical["record_type"],
                record_id=canonical["record_id"],
            )
            apply_canonical_row_to_db(connection, row=canonical)

            if str(row.get("review_phase") or "").strip() == "comment_codes":
                _insert_code_row(
                    connection,
                    row=row,
                    record_id=record_id,
                    record_type=record_type,
                )

            imported += 1

        connection.commit()

    return {
        "reviewed_path": str(reviewed_path),
        "db_path": str(db_path),
        "rows_imported": imported,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import reviewed JSONL decisions into the staging DB using canonical rows."
    )
    parser.add_argument("--db", type=Path, default=REBASELINE_STAGING_DB_PATH)
    parser.add_argument("--reviewed", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = import_reviewed_file(
        reviewed_path=args.reviewed,
        db_path=args.db,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


__all__ = ["import_reviewed_file", "main"]
