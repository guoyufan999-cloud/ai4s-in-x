from __future__ import annotations

import argparse
from pathlib import Path

from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)

from .review_queue_io import (
    REVIEW_PHASES,
    _default_output_path,
    _latest_suggestion_file,
    _load_jsonl,
    _load_suggestion_index,
)
from .review_queue_output import _empty_queue_row_for_phase, export_review_queue
from .review_queue_rows import (
    _build_comment_rows,
    _build_post_rows,
    _priority_bucket,
    _rows_for_phase,
    _stable_comment_row,
    _stable_post_row,
)

__all__ = [
    "REVIEW_PHASES",
    "_build_comment_rows",
    "_build_post_rows",
    "_default_output_path",
    "_empty_queue_row_for_phase",
    "_latest_suggestion_file",
    "_load_jsonl",
    "_load_suggestion_index",
    "_priority_bucket",
    "_rows_for_phase",
    "_stable_comment_row",
    "_stable_post_row",
    "build_parser",
    "export_review_queue",
    "main",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export JSONL review queues from the quality_v5 rebaseline staging DB."
    )
    parser.add_argument("--db", type=Path, default=REBASELINE_STAGING_DB_PATH)
    parser.add_argument("--phase", choices=sorted(REVIEW_PHASES), required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--suggestions-dir", type=Path, default=REBASELINE_SUGGESTIONS_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(
        export_review_queue(
            db_path=args.db,
            phase=args.phase,
            output_path=args.output,
            limit=args.limit,
            suggestions_dir=args.suggestions_dir,
        )
    )


if __name__ == "__main__":
    main()
