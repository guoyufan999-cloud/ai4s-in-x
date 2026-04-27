from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import LEGACY_AUDIT_SNAPSHOT_PATH, paper_scope_view
from ai4s_legitimacy.config.settings import (
    OUTPUTS_DIR,
    QUALITY_V4_CHECKPOINT,
    QUALITY_V4_CONSISTENCY_REPORT_PATH,
    RESEARCH_DB_PATH,
    RESEARCH_DB_SUMMARY_PATH,
)
from ai4s_legitimacy.utils.db import connect_sqlite_readonly
from ai4s_legitimacy.utils.paths import project_relative_path

LEGACY_POST_VIEW = "vw_posts_paper_scope_quality_v4"
LEGACY_COMMENT_VIEW = "vw_comments_paper_scope_quality_v4"


def _resolve_audit_view_name(connection, *, legacy_view: str, active_view: str) -> str:
    legacy_row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name = ?",
        (legacy_view,),
    ).fetchone()
    if legacy_row is not None:
        return legacy_view
    active_row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name = ?",
        (active_view,),
    ).fetchone()
    if active_row is not None:
        return active_view
    raise sqlite3.OperationalError(
        f"Neither legacy audit view {legacy_view!r} nor active view {active_view!r} exists"
    )


def _query_distribution(
    connection,
    *,
    table: str,
    value_column: str,
    count_column: str = "row_count",
    where_sql: str = "",
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"""
        SELECT COALESCE(NULLIF({value_column}, ''), 'uncoded') AS label, COUNT(*) AS {count_column}
        FROM {table}
        {where_sql}
        GROUP BY COALESCE(NULLIF({value_column}, ''), 'uncoded')
        ORDER BY {count_column} DESC, label
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _formal_id_list(connection, *, view_name: str, id_column: str) -> list[str]:
    rows = connection.execute(
        f"SELECT {id_column} FROM {view_name} ORDER BY {id_column}"
    ).fetchall()
    return [str(row[id_column]) for row in rows]


def _snapshot_output_paths() -> dict[str, Any]:
    figure_dir = OUTPUTS_DIR / "figures" / "paper_figures_submission" / "quality_v4"
    freeze_dir = OUTPUTS_DIR / "reports" / "freeze_checkpoints"
    materials_dir = OUTPUTS_DIR / "reports" / "paper_materials"
    return {
        "figure_dir": project_relative_path(figure_dir),
        "freeze_checkpoint_json": project_relative_path(
            freeze_dir / "quality_v4_freeze_checkpoint.json"
        ),
        "freeze_checkpoint_markdown": project_relative_path(
            freeze_dir / "quality_v4_freeze_checkpoint.md"
        ),
        "consistency_report": project_relative_path(QUALITY_V4_CONSISTENCY_REPORT_PATH),
        "summary_json": project_relative_path(RESEARCH_DB_SUMMARY_PATH),
        "paper_materials_manifest": project_relative_path(
            materials_dir / "paper_materials_manifest.json"
        ),
        "evidence_matrix": project_relative_path(
            materials_dir / "quality_v4_evidence_matrix.md"
        ),
        "results_snapshot": project_relative_path(materials_dir / "paper_results_snapshot.md"),
    }


def export_quality_v4_audit_snapshot(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    checkpoint_path: Path = QUALITY_V4_CHECKPOINT,
    output_path: Path = LEGACY_AUDIT_SNAPSHOT_PATH,
) -> Path:
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    with connect_sqlite_readonly(db_path) as connection:
        post_view = _resolve_audit_view_name(
            connection,
            legacy_view=LEGACY_POST_VIEW,
            active_view=paper_scope_view("posts"),
        )
        comment_view = _resolve_audit_view_name(
            connection,
            legacy_view=LEGACY_COMMENT_VIEW,
            active_view=paper_scope_view("comments"),
        )
        snapshot: dict[str, Any] = {
            "audit_stage": "quality_v4",
            "research_db_path": project_relative_path(db_path),
            "checkpoint_path": project_relative_path(checkpoint_path),
            "view_source": {
                "posts": post_view,
                "comments": comment_view,
            },
            "formal_counts": {
                "posts": int(checkpoint.get("formal_posts", 0) or 0),
                "comments": int(checkpoint.get("formal_comments", 0) or 0),
                "queued": int(checkpoint.get("queued", 0) or 0),
            },
            "formal_ids": {
                "posts": _formal_id_list(
                    connection,
                    view_name=post_view,
                    id_column="post_id",
                ),
                "comments": _formal_id_list(
                    connection,
                    view_name=comment_view,
                    id_column="comment_id",
                ),
            },
            "label_distributions": {
                "posts": {
                    "sample_status": _query_distribution(
                        connection,
                        table="posts",
                        value_column="sample_status",
                    ),
                    "actor_type": _query_distribution(
                        connection,
                        table=post_view,
                        value_column="actor_type",
                    ),
                    "qs_broad_subject": _query_distribution(
                        connection,
                        table=post_view,
                        value_column="qs_broad_subject",
                    ),
                    "workflow_stage": _query_distribution(
                        connection,
                        table=post_view,
                        value_column="workflow_stage",
                    ),
                    "primary_legitimacy_stance": _query_distribution(
                        connection,
                        table=post_view,
                        value_column="primary_legitimacy_stance",
                    ),
                },
                "comments": {
                    "stance": _query_distribution(
                        connection,
                        table=comment_view,
                        value_column="stance",
                        count_column="comment_count",
                    ),
                    "legitimacy_basis": _query_distribution(
                        connection,
                        table=comment_view,
                        value_column="legitimacy_basis",
                        count_column="comment_count",
                    ),
                },
                "codes": {
                    "workflow_stage_code": _query_distribution(
                        connection,
                        table="codes",
                        value_column="workflow_stage_code",
                        count_column="coded_count",
                    ),
                    "ai_practice_code": _query_distribution(
                        connection,
                        table="codes",
                        value_column="ai_practice_code",
                        count_column="coded_count",
                    ),
                    "legitimacy_code": _query_distribution(
                        connection,
                        table="codes",
                        value_column="legitimacy_code",
                        count_column="coded_count",
                    ),
                    "boundary_negotiation_code": _query_distribution(
                        connection,
                        table="codes",
                        value_column="boundary_negotiation_code",
                        count_column="coded_count",
                    ),
                },
            },
            "versioned_outputs": _snapshot_output_paths(),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a one-time quality_v4 audit snapshot before rebaseline rebuild."
    )
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--checkpoint", type=Path, default=QUALITY_V4_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=LEGACY_AUDIT_SNAPSHOT_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(
        export_quality_v4_audit_snapshot(
            db_path=args.db,
            checkpoint_path=args.checkpoint,
            output_path=args.output,
        )
    )


if __name__ == "__main__":
    main()
