from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis.figure_generation import generate_submission_figures, write_figure_manifest
from ai4s_legitimacy.analysis.quality_v4_consistency import (
    evaluate_quality_v4_consistency,
    write_quality_v4_consistency_report,
)
from ai4s_legitimacy.analysis.reporting import build_summary_payload, write_summary_payload
from ai4s_legitimacy.analysis.figures.config import FIGURE_DIR
from ai4s_legitimacy.config.settings import (
    QUALITY_V4_CHECKPOINT,
    QUALITY_V4_CONSISTENCY_REPORT_PATH,
    RESEARCH_DB_PATH,
    RESEARCH_DB_SUMMARY_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild all paper artifacts from the research DB."
    )
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--checkpoint", type=Path, default=QUALITY_V4_CHECKPOINT)
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=RESEARCH_DB_SUMMARY_PATH,
    )
    parser.add_argument(
        "--consistency-output",
        type=Path,
        default=QUALITY_V4_CONSISTENCY_REPORT_PATH,
    )
    parser.add_argument("--figure-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip figure generation (matplotlib not required).",
    )
    return parser


def run_build(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    checkpoint_path: Path = QUALITY_V4_CHECKPOINT,
    summary_output: Path = RESEARCH_DB_SUMMARY_PATH,
    consistency_output: Path = QUALITY_V4_CONSISTENCY_REPORT_PATH,
    figure_dir: Path = FIGURE_DIR,
    skip_figures: bool = False,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(f"Research DB not found at {db_path}")

    summary_payload = build_summary_payload(db_path=db_path)
    summary_path = write_summary_payload(summary_payload, summary_output)

    consistency_report = evaluate_quality_v4_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
    )
    consistency_path = write_quality_v4_consistency_report(
        consistency_report,
        consistency_output,
    )

    result: dict[str, Any] = {
        "db_path": str(db_path),
        "summary": summary_payload,
        "summary_path": str(summary_path),
        "consistency": consistency_report,
        "consistency_path": str(consistency_path),
        "coverage_end_date": summary_payload["paper_quality_v4"]["coverage_end_date"],
        "figures_skipped": skip_figures,
    }
    if skip_figures:
        return result

    figure_result = generate_submission_figures(
        db_path=db_path,
        figure_dir=figure_dir,
        coverage_end_date=summary_payload["paper_quality_v4"]["coverage_end_date"],
    )
    figure_manifest_path = write_figure_manifest(
        figure_dir=Path(figure_result["figure_dir"]),
        generated_slugs=figure_result["generated_slugs"],
        formal_posts=int(summary_payload["paper_quality_v4"]["formal_posts"]),
        formal_comments=int(summary_payload["paper_quality_v4"]["formal_comments"]),
        coverage_end_date=summary_payload["paper_quality_v4"]["coverage_end_date"],
    )
    result["figures"] = figure_result
    result["figure_manifest_path"] = str(figure_manifest_path)
    return result


def main() -> None:
    args = build_parser().parse_args()
    result = run_build(
        db_path=args.db,
        checkpoint_path=args.checkpoint,
        summary_output=args.summary_output,
        consistency_output=args.consistency_output,
        figure_dir=args.figure_dir,
        skip_figures=args.skip_figures,
    )

    print(f"Building paper artifacts from {args.db}")
    summary = result["summary"]
    print("  [summary JSON]")
    print(
        f"    -> {result['summary_path']}  "
        f"(posts={summary['research_db']['posts']}, comments={summary['research_db']['comments']})"
    )
    consistency = result["consistency"]
    print("  [consistency report]")
    print(
        f"    -> {result['consistency_path']}  "
        f"(status={consistency['status']}, "
        f"delta_posts={consistency['delta']['paper_posts_minus_checkpoint']})"
    )

    if result["figures_skipped"]:
        print("  [submission figures (skipped)]")
        print("  [figure manifest (skipped)]")
        return

    figures = result["figures"]
    print("  [submission figures]")
    print(f"    -> {figures['figure_dir']}  ({figures['figure_count']} figures)")
    for slug in figures["generated_slugs"]:
        print(f"       - {slug}")
    print("  [figure manifest]")
    print(f"    -> {result['figure_manifest_path']}")


if __name__ == "__main__":
    main()
