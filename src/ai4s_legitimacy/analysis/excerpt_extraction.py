from __future__ import annotations

import argparse
from pathlib import Path

from ai4s_legitimacy.analysis._excerpt_rendering import (
    deidentify_text,
    export_excerpts,
    format_excerpts_markdown,
)
from ai4s_legitimacy.analysis._excerpt_service import (
    extract_excerpts_by_boundary_code,
    extract_excerpts_by_stance,
    extract_excerpts_by_workflow_stage,
    generate_all_excerpts,
)
from ai4s_legitimacy.analysis._excerpt_specs import (
    EXCERPTS_DIR,
    MAX_CHARS_DEFAULT,
    ExcerptBatchSpec,
    ExcerptQuerySpec,
    ExcerptRecordType,
)
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH


__all__ = [
    "EXCERPTS_DIR",
    "MAX_CHARS_DEFAULT",
    "ExcerptBatchSpec",
    "ExcerptQuerySpec",
    "ExcerptRecordType",
    "build_parser",
    "deidentify_text",
    "export_excerpts",
    "extract_excerpts_by_boundary_code",
    "extract_excerpts_by_stance",
    "extract_excerpts_by_workflow_stage",
    "format_excerpts_markdown",
    "generate_all_excerpts",
    "main",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract anonymized excerpts from the research DB for coding categories."
    )
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output-dir", type=Path, default=EXCERPTS_DIR)
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS_DEFAULT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Generate excerpts for all known categories",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.batch:
        paths = generate_all_excerpts(
            args.db,
            args.output_dir,
            args.max_chars,
            args.limit,
        )
        for p in paths:
            print(p)
    else:
        print("Use --batch to generate all excerpt files.")


if __name__ == "__main__":
    main()
