from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import REBASELINE_SUGGESTIONS_DIR
from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

from .review_v2_artifact_bootstrap import (
    bootstrap_inclusion_decision,
    bootstrap_reason,
    manual_or_bootstrap_codes,
    structured_record,
)
from .review_v2_artifact_output import build_delta_report, write_jsonl
from .review_v2_artifact_records import build_comment_records, build_post_records

TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports" / "review_v2"
POST_MASTER_PATH = TABLES_DIR / "post_review_v2_master.jsonl"
COMMENT_MASTER_PATH = TABLES_DIR / "comment_review_v2_master.jsonl"
DELTA_REPORT_PATH = REPORTS_DIR / "post_review_v2_delta_report.json"


def build_review_v2_artifacts(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
    post_output_path: Path = POST_MASTER_PATH,
    comment_output_path: Path = COMMENT_MASTER_PATH,
    delta_output_path: Path = DELTA_REPORT_PATH,
    immutable: bool = False,
) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        post_records = build_post_records(connection, suggestions_dir)
        included_post_ids = {
            str(row["post_id"])
            for row in post_records
            if row["decision"] == "纳入"
        }
        comment_records = build_comment_records(
            connection,
            included_post_ids=included_post_ids,
        )
    post_path = write_jsonl(post_output_path, post_records)
    comment_path = write_jsonl(comment_output_path, comment_records)
    delta_report = build_delta_report(post_records)
    delta_output_path.parent.mkdir(parents=True, exist_ok=True)
    delta_output_path.write_text(
        json.dumps(delta_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "post_master_path": str(post_path),
        "comment_master_path": str(comment_path),
        "delta_report_path": str(delta_output_path),
        "post_rows": len(post_records),
        "comment_rows": len(comment_records),
        "included_posts": len(included_post_ids),
    }


# Private compatibility aliases retained for current tests and likely local callers.
_manual_or_bootstrap_codes = manual_or_bootstrap_codes
_bootstrap_inclusion_decision = bootstrap_inclusion_decision
_bootstrap_reason = bootstrap_reason
_structured_record = structured_record


__all__ = [
    "build_review_v2_artifacts",
    "COMMENT_MASTER_PATH",
    "DELTA_REPORT_PATH",
    "POST_MASTER_PATH",
]
