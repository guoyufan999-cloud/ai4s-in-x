from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis._reporting_core import (
    _build_summary_payload_from_connection,
    _resolve_summary_context,
    _summarize_paper_quality_v4,
    _summarize_paper_quality_v4_cross_tabs,
    _summarize_research_db,
    _summarize_scope_counts,
    write_summary_payload,
)
from ai4s_legitimacy.analysis.figures.config import resolve_paper_scope_coverage_end_date
from ai4s_legitimacy.config.formal_baseline import ACTIVE_FORMAL_SUMMARY_KEY
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH, RESEARCH_DB_SUMMARY_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

__all__ = [
    "build_parser",
    "build_summary_payload",
    "export_summary_json",
    "main",
    "summarize_active_paper_quality",
    "summarize_active_paper_quality_cross_tabs",
    "summarize_paper_quality_v5",
    "summarize_paper_quality_v5_cross_tabs",
    "summarize_paper_quality_v4",
    "summarize_paper_quality_v4_cross_tabs",
    "summarize_research_db",
    "summarize_scope_counts",
    "write_summary_payload",
]


def summarize_scope_counts(db_path: Path = RESEARCH_DB_PATH, *, immutable: bool = False) -> dict[str, int]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        return _summarize_scope_counts(connection)


def summarize_paper_quality_v4_cross_tabs(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        return _summarize_paper_quality_v4_cross_tabs(connection)


def summarize_paper_quality_v4(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        scope_counts, coverage_end_date = _resolve_summary_context(
            connection,
            resolve_coverage_end_date=resolve_paper_scope_coverage_end_date,
        )
        return _summarize_paper_quality_v4(
            connection,
            scope_counts=scope_counts,
            coverage_end_date=coverage_end_date,
        )


def summarize_paper_quality_v5_cross_tabs(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    return summarize_paper_quality_v4_cross_tabs(db_path=db_path, immutable=immutable)


def summarize_paper_quality_v5(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    return summarize_paper_quality_v4(db_path=db_path, immutable=immutable)


def summarize_active_paper_quality_cross_tabs(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    return summarize_paper_quality_v5_cross_tabs(db_path=db_path, immutable=immutable)


def summarize_active_paper_quality(
    db_path: Path = RESEARCH_DB_PATH,
    *,
    immutable: bool = False,
) -> dict[str, Any]:
    return summarize_paper_quality_v5(db_path=db_path, immutable=immutable)


def summarize_research_db(db_path: Path = RESEARCH_DB_PATH, *, immutable: bool = False) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        scope_counts = _summarize_scope_counts(connection)
        return _summarize_research_db(connection, scope_counts=scope_counts)


def build_summary_payload(db_path: Path = RESEARCH_DB_PATH, *, immutable: bool = False) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        return _build_summary_payload_from_connection(
            connection,
            resolve_coverage_end_date=resolve_paper_scope_coverage_end_date,
        )


def export_summary_json(
    db_path: Path = RESEARCH_DB_PATH,
    output_path: Path | None = None,
    *,
    immutable: bool = False,
) -> Path:
    output = output_path or RESEARCH_DB_SUMMARY_PATH
    return write_summary_payload(build_summary_payload(db_path=db_path, immutable=immutable), output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export research DB summary JSON.")
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output", type=Path, default=RESEARCH_DB_SUMMARY_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = export_summary_json(db_path=args.db, output_path=args.output)
    print(output_path)


ACTIVE_SUMMARY_KEY = ACTIVE_FORMAL_SUMMARY_KEY


if __name__ == "__main__":
    main()
