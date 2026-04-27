from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_CHECKPOINT_PATH,
    ACTIVE_CONSISTENCY_REPORT_PATH,
    ACTIVE_FORMAL_SCOPE_COMMENTS_KEY,
    ACTIVE_FORMAL_SCOPE_POSTS_KEY,
    ACTIVE_FORMAL_STAGE,
)
from ai4s_legitimacy.config.research_scope import (
    PAPER_SCOPE_EXCLUDED_ACTOR_TYPES,
    PAPER_SCOPE_REQUIRED_CRAWL_STATUS,
    RESEARCH_WINDOW_END,
    RESEARCH_WINDOW_START,
    sql_string_list,
)
from ai4s_legitimacy.config.settings import RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly
from ai4s_legitimacy.utils.paths import project_relative_path


EXCLUDED_ACTOR_VALUES_SQL = sql_string_list(PAPER_SCOPE_EXCLUDED_ACTOR_TYPES)


def _scope_counts(connection) -> dict[str, int]:
    return {
        str(row["scope_name"]): int(row["row_count"] or 0)
        for row in connection.execute(
            "SELECT scope_name, row_count FROM vw_scope_counts ORDER BY scope_name"
        ).fetchall()
    }


def _post_reason_breakdown(connection) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT
            CASE
                WHEN COALESCE(NULLIF(actor_type, ''), 'uncertain') IN ({EXCLUDED_ACTOR_VALUES_SQL})
                    THEN 'excluded_actor'
                WHEN legacy_crawl_status != ?
                    THEN 'not_crawled'
                WHEN post_date IS NULL OR post_date < ? OR post_date > ?
                    THEN 'outside_research_window'
                ELSE 'paper_scope'
            END AS bucket,
            COUNT(*) AS row_count
        FROM vw_posts_research_scope
        GROUP BY bucket
        ORDER BY bucket
        """,
        (
            PAPER_SCOPE_REQUIRED_CRAWL_STATUS,
            RESEARCH_WINDOW_START,
            RESEARCH_WINDOW_END,
        ),
    ).fetchall()
    return {str(row["bucket"]): int(row["row_count"] or 0) for row in rows}


def _comment_reason_breakdown(connection) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT
            CASE
                WHEN COALESCE(NULLIF(p.actor_type, ''), 'uncertain') IN ({EXCLUDED_ACTOR_VALUES_SQL})
                    THEN 'excluded_actor'
                WHEN p.legacy_crawl_status != ?
                    THEN 'post_not_crawled'
                WHEN c.comment_date IS NULL OR c.comment_date = ''
                    THEN 'missing_comment_date'
                WHEN c.comment_date < ? OR c.comment_date > ?
                    THEN 'outside_research_window'
                ELSE 'paper_scope'
            END AS bucket,
            COUNT(*) AS row_count
        FROM vw_comments_research_scope c
        JOIN vw_posts_research_scope p ON p.post_id = c.post_id
        GROUP BY bucket
        ORDER BY bucket
        """,
        (
            PAPER_SCOPE_REQUIRED_CRAWL_STATUS,
            RESEARCH_WINDOW_START,
            RESEARCH_WINDOW_END,
        ),
    ).fetchall()
    return {str(row["bucket"]): int(row["row_count"] or 0) for row in rows}


def evaluate_quality_v5_consistency(
    checkpoint_path: Path = ACTIVE_CHECKPOINT_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    *,
    generated_at_utc: str | None = None,
    immutable: bool = False,
) -> dict[str, object]:
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        scope_counts = _scope_counts(connection)
        post_reason_breakdown = _post_reason_breakdown(connection)
        comment_reason_breakdown = _comment_reason_breakdown(connection)

    reference_formal_posts = int(checkpoint.get("formal_posts", 0) or 0)
    reference_formal_comments = int(checkpoint.get("formal_comments", 0) or 0)
    observed_formal_posts = int(scope_counts.get(ACTIVE_FORMAL_SCOPE_POSTS_KEY, 0))
    observed_formal_comments = int(scope_counts.get(ACTIVE_FORMAL_SCOPE_COMMENTS_KEY, 0))

    report: dict[str, object] = {
        "reference_source": project_relative_path(checkpoint_path),
        "research_db_path": project_relative_path(db_path),
        "matching_rule": (
            f"compare {ACTIVE_FORMAL_STAGE} checkpoint counts with paper-scope views in the research DB"
        ),
        "reference": {
            "checkpoint_stage": checkpoint.get("checkpoint_stage"),
            "formal_posts": reference_formal_posts,
            "formal_comments": reference_formal_comments,
            "queued": checkpoint.get("queued"),
        },
        "scope_counts": scope_counts,
        "observed_paper_scope": {
            "formal_posts": observed_formal_posts,
            "formal_comments": observed_formal_comments,
        },
        "delta": {
            "paper_posts_minus_checkpoint": observed_formal_posts - reference_formal_posts,
            "paper_comments_minus_checkpoint": observed_formal_comments - reference_formal_comments,
        },
        "research_to_paper_exclusion": {
            "posts": post_reason_breakdown,
            "comments": comment_reason_breakdown,
        },
        "status": "aligned"
        if observed_formal_posts == reference_formal_posts and observed_formal_comments == reference_formal_comments
        else "mismatch",
    }
    if generated_at_utc is not None:
        report["generated_at_utc"] = generated_at_utc
    return report


def write_quality_v5_consistency_report(
    report: dict[str, object],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def export_quality_v5_consistency(
    output_path: Path | None = None,
    checkpoint_path: Path = ACTIVE_CHECKPOINT_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    *,
    generated_at_utc: str | None = None,
    immutable: bool = False,
) -> Path:
    report = evaluate_quality_v5_consistency(
        checkpoint_path=checkpoint_path,
        db_path=db_path,
        generated_at_utc=generated_at_utc,
        immutable=immutable,
    )
    output = output_path or ACTIVE_CONSISTENCY_REPORT_PATH
    return write_quality_v5_consistency_report(report, output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Compare {ACTIVE_FORMAL_STAGE} freeze metrics with the paper-scope views in the research DB."
    )
    parser.add_argument("--checkpoint", type=Path, default=ACTIVE_CHECKPOINT_PATH)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output", type=Path, default=ACTIVE_CONSISTENCY_REPORT_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = export_quality_v5_consistency(
        output_path=args.output,
        checkpoint_path=args.checkpoint,
        db_path=args.db,
    )
    print(output_path)


if __name__ == "__main__":
    main()
