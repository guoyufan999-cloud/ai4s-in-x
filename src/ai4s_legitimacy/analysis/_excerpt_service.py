from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis._excerpt_rendering import deidentify_text, export_excerpts
from ai4s_legitimacy.analysis._excerpt_specs import (
    BATCH_EXPORT_SPECS,
    BOUNDARY_CODE_QUERY_SPEC,
    COMMENT_STANCE_QUERY_SPEC,
    EXCERPTS_DIR,
    ExcerptBatchSpec,
    ExcerptQuerySpec,
    ExcerptRecordType,
    MAX_CHARS_DEFAULT,
    POST_STANCE_QUERY_SPEC,
    WORKFLOW_STAGE_QUERY_SPEC,
)
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly


def _select_rows(
    db_path: Path,
    sql: str,
    params: tuple[object, ...] = (),
) -> list[Any]:
    with connect_sqlite_readonly(db_path, immutable=True) as conn:
        return conn.execute(sql, params).fetchall()


def _distinct_values_from_connection(connection, sql: str) -> list[str]:
    return [str(row[0]) for row in connection.execute(sql).fetchall() if row[0] is not None]


def _query_excerpt_rows(
    coding_label: str,
    limit: int,
    *,
    db_path: Path,
    query_spec: ExcerptQuerySpec,
) -> list[Any]:
    return _select_rows(db_path, query_spec.sql, (coding_label, limit))


def _build_excerpt_record(
    record_id: str,
    record_type: str,
    coding_label: str,
    deidentified_text: str,
    record_date: str | None,
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "record_type": record_type,
        "coding_label": coding_label,
        "excerpt": deidentified_text,
        "record_date": record_date or "",
    }


def _build_excerpt_from_row(
    row: Any,
    *,
    query_spec: ExcerptQuerySpec,
    coding_label: str,
    max_chars: int,
) -> dict[str, str]:
    return _build_excerpt_record(
        str(row[query_spec.record_id_key]),
        query_spec.record_type,
        coding_label,
        deidentify_text(row[query_spec.text_key], max_chars),
        str(row[query_spec.date_key]) if row[query_spec.date_key] else None,
    )


def _build_excerpts(
    rows: Sequence[Any],
    *,
    query_spec: ExcerptQuerySpec,
    coding_label: str,
    max_chars: int,
) -> list[dict[str, str]]:
    return [
        _build_excerpt_from_row(
            row,
            query_spec=query_spec,
            coding_label=coding_label,
            max_chars=max_chars,
        )
        for row in rows
    ]


def _extract_excerpts_for_label(
    coding_label: str,
    *,
    query_spec: ExcerptQuerySpec,
    max_chars: int,
    limit: int,
    db_path: Path,
) -> list[dict[str, str]]:
    return _build_excerpts(
        _query_excerpt_rows(
            coding_label,
            limit,
            db_path=db_path,
            query_spec=query_spec,
        ),
        query_spec=query_spec,
        coding_label=coding_label,
        max_chars=max_chars,
    )


def extract_excerpts_by_workflow_stage(
    stage: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    return _extract_excerpts_for_label(
        stage,
        query_spec=WORKFLOW_STAGE_QUERY_SPEC,
        max_chars=max_chars,
        limit=limit,
        db_path=db_path,
    )


def _query_spec_for_stance(record_type: ExcerptRecordType) -> ExcerptQuerySpec:
    if record_type == "post":
        return POST_STANCE_QUERY_SPEC
    if record_type == "comment":
        return COMMENT_STANCE_QUERY_SPEC
    raise ValueError("record_type must be 'post' or 'comment'")


def extract_excerpts_by_stance(
    stance: str,
    record_type: ExcerptRecordType = "post",
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    return _extract_excerpts_for_label(
        stance,
        query_spec=_query_spec_for_stance(record_type),
        max_chars=max_chars,
        limit=limit,
        db_path=db_path,
    )


def extract_excerpts_by_boundary_code(
    code: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    return _extract_excerpts_for_label(
        code,
        query_spec=BOUNDARY_CODE_QUERY_SPEC,
        max_chars=max_chars,
        limit=limit,
        db_path=db_path,
    )


def _append_export_if_present(
    generated: list[Path],
    *,
    category_slug: str,
    excerpts: list[dict[str, str]],
    output_dir: Path,
    generated_at: str | None,
) -> None:
    if excerpts:
        generated.append(
            export_excerpts(
                category_slug,
                excerpts,
                output_dir,
                generated_at=generated_at,
            )
        )


def _load_batch_category_groups(
    db_path: Path,
    batch_specs: Sequence[ExcerptBatchSpec],
) -> list[list[str]]:
    with connect_sqlite_readonly(db_path, immutable=True) as conn:
        return [
            _distinct_values_from_connection(conn, batch_spec.distinct_values_sql)
            for batch_spec in batch_specs
        ]


def _generate_excerpt_paths_for_batch_spec(
    category_values: Sequence[str],
    *,
    batch_spec: ExcerptBatchSpec,
    db_path: Path,
    output_dir: Path,
    max_chars: int,
    limit: int,
    generated_at: str | None,
) -> list[Path]:
    generated: list[Path] = []
    for coding_label in category_values:
        _append_export_if_present(
            generated,
            category_slug=batch_spec.slug_builder(coding_label),
            excerpts=_extract_excerpts_for_label(
                coding_label,
                query_spec=batch_spec.query_spec,
                max_chars=max_chars,
                limit=limit,
                db_path=db_path,
            ),
            output_dir=output_dir,
            generated_at=generated_at,
        )
    return generated


def generate_all_excerpts(
    db_path: Path = RESEARCH_DB_PATH,
    output_dir: Path = EXCERPTS_DIR,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    *,
    generated_at: str | None = None,
) -> list[Path]:
    generated: list[Path] = []
    category_groups = _load_batch_category_groups(db_path, BATCH_EXPORT_SPECS)
    for batch_spec, category_values in zip(BATCH_EXPORT_SPECS, category_groups, strict=True):
        generated.extend(
            _generate_excerpt_paths_for_batch_spec(
                category_values,
                batch_spec=batch_spec,
                db_path=db_path,
                output_dir=output_dir,
                max_chars=max_chars,
                limit=limit,
                generated_at=generated_at,
            )
        )
    return generated
