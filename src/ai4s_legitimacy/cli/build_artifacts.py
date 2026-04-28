from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis.artifact_provenance import (
    build_artifact_provenance,
    write_artifact_provenance,
)
from ai4s_legitimacy.analysis.figure_generation import (
    generate_submission_figures,
    write_figure_manifest,
)
from ai4s_legitimacy.analysis.figures.config import FIGURE_DIR
from ai4s_legitimacy.analysis.framework_v2_coding_audit import (
    write_framework_v2_coding_audit,
)
from ai4s_legitimacy.analysis.framework_v2_materials import (
    FRAMEWORK_V2_OUTPUT_DIR,
    generate_framework_v2_materials,
)
from ai4s_legitimacy.analysis.quality_v5_consistency import (
    evaluate_quality_v5_consistency,
    write_quality_v5_consistency_report,
)
from ai4s_legitimacy.analysis.reporting import build_summary_payload, write_summary_payload
from ai4s_legitimacy.collection.review_v2_artifacts import (
    COMMENT_MASTER_PATH,
    DELTA_REPORT_PATH,
    POST_MASTER_PATH,
    build_review_v2_artifacts,
)
from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_ARTIFACT_PROVENANCE_PATH,
    ACTIVE_CHECKPOINT_PATH,
    ACTIVE_CONSISTENCY_REPORT_PATH,
    ACTIVE_FORMAL_SUMMARY_KEY,
)
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH, RESEARCH_DB_SUMMARY_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild all paper artifacts from the research DB."
    )
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--checkpoint", type=Path, default=ACTIVE_CHECKPOINT_PATH)
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=RESEARCH_DB_SUMMARY_PATH,
    )
    parser.add_argument(
        "--consistency-output",
        type=Path,
        default=ACTIVE_CONSISTENCY_REPORT_PATH,
    )
    parser.add_argument(
        "--provenance-output",
        type=Path,
        default=ACTIVE_ARTIFACT_PROVENANCE_PATH,
    )
    parser.add_argument("--figure-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--framework-v2-dir", type=Path, default=None)
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip figure generation (matplotlib not required).",
    )
    return parser


def run_build(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    checkpoint_path: Path = ACTIVE_CHECKPOINT_PATH,
    summary_output: Path = RESEARCH_DB_SUMMARY_PATH,
    consistency_output: Path = ACTIVE_CONSISTENCY_REPORT_PATH,
    provenance_output: Path = ACTIVE_ARTIFACT_PROVENANCE_PATH,
    figure_dir: Path = FIGURE_DIR,
    review_v2_post_output_path: Path = POST_MASTER_PATH,
    review_v2_comment_output_path: Path = COMMENT_MASTER_PATH,
    review_v2_delta_output_path: Path = DELTA_REPORT_PATH,
    framework_v2_output_dir: Path | None = None,
    skip_figures: bool = False,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(f"Research DB not found at {db_path}")

    summary_payload = build_summary_payload(db_path=db_path, immutable=True)
    summary_path = write_summary_payload(summary_payload, summary_output)

    consistency_report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
        immutable=True,
    )
    consistency_path = write_quality_v5_consistency_report(
        consistency_report,
        consistency_output,
    )
    formal_summary = summary_payload[ACTIVE_FORMAL_SUMMARY_KEY]

    canonical_corpus = build_review_v2_artifacts(
        db_path=db_path,
        post_output_path=review_v2_post_output_path,
        comment_output_path=review_v2_comment_output_path,
        delta_output_path=review_v2_delta_output_path,
        immutable=True,
    )
    resolved_framework_v2_dir = framework_v2_output_dir
    if resolved_framework_v2_dir is None:
        resolved_framework_v2_dir = (
            FRAMEWORK_V2_OUTPUT_DIR
            if summary_output == RESEARCH_DB_SUMMARY_PATH
            else summary_output.parent / "framework_v2"
        )
    framework_v2 = generate_framework_v2_materials(
        db_path=db_path,
        output_dir=resolved_framework_v2_dir,
        immutable=True,
    )
    framework_v2_audit = write_framework_v2_coding_audit(
        output_json_path=Path(framework_v2["output_dir"]) / "framework_v2_coding_audit_report.json",
        output_md_path=Path(framework_v2["output_dir"]) / "framework_v2_coding_audit_report.md",
        output_appendix_path=Path(framework_v2["output_dir"])
        / "framework_v2_high_risk_recheck_appendix.md",
        post_master_path=review_v2_post_output_path,
        summary_tables_path=Path(framework_v2["paths"]["summary_tables"]),
        cross_tabs_path=Path(framework_v2["paths"]["cross_tabs"]),
    )
    result: dict[str, Any] = {
        "db_path": str(db_path),
        "summary": summary_payload,
        "summary_path": str(summary_path),
        "consistency": consistency_report,
        "consistency_path": str(consistency_path),
        "coverage_end_date": formal_summary["coverage_end_date"],
        "figures_skipped": skip_figures,
        "canonical_corpus": canonical_corpus,
        "review_v2": canonical_corpus,
        "framework_v2": framework_v2,
        "framework_v2_coding_audit": framework_v2_audit,
    }
    figure_manifest_path = figure_dir / "paper_figures_submission_manifest.md"

    if not skip_figures:
        figure_result = generate_submission_figures(
            db_path=db_path,
            figure_dir=figure_dir,
            coverage_end_date=formal_summary["coverage_end_date"],
            immutable=True,
        )
        figure_manifest_path = write_figure_manifest(
            figure_dir=Path(figure_result["figure_dir"]),
            generated_slugs=figure_result["generated_slugs"],
            formal_posts=int(formal_summary["formal_posts"]),
            formal_comments=int(formal_summary["formal_comments"]),
            coverage_end_date=formal_summary["coverage_end_date"],
        )
        result["figures"] = figure_result
        result["figure_manifest_path"] = str(figure_manifest_path)

    provenance = build_artifact_provenance(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        summary_payload=summary_payload,
        consistency_report=consistency_report,
        summary_path=summary_path,
        consistency_path=consistency_path,
        canonical_corpus=canonical_corpus,
        skip_figures=skip_figures,
        figure_manifest_path=figure_manifest_path,
    )
    provenance_path = write_artifact_provenance(provenance, provenance_output)
    result["provenance"] = provenance
    result["provenance_path"] = str(provenance_path)
    return result


def main() -> None:
    args = build_parser().parse_args()
    result = run_build(
        db_path=args.db,
        checkpoint_path=args.checkpoint,
        summary_output=args.summary_output,
        consistency_output=args.consistency_output,
        provenance_output=args.provenance_output,
        figure_dir=args.figure_dir,
        framework_v2_output_dir=args.framework_v2_dir,
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
    review_v2 = result["canonical_corpus"]
    print("  [canonical corpus]")
    print(
        "    -> "
        f"{review_v2['post_master_path']}  "
        f"(posts={review_v2['post_rows']}, included={review_v2['included_posts']})"
    )
    print(f"    -> {review_v2['comment_master_path']}  (comments={review_v2['comment_rows']})")
    print(f"    -> {review_v2['delta_report_path']}")
    framework_v2 = result["framework_v2"]
    print("  [framework v2 materials]")
    print(f"    -> {framework_v2['output_dir']}")
    framework_v2_audit = result["framework_v2_coding_audit"]
    print("  [framework v2 coding audit]")
    print(f"    -> {framework_v2_audit['audit_markdown_path']}")
    print("  [artifact provenance]")
    print(f"    -> {result['provenance_path']}")

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
