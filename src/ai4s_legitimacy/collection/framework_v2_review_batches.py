from __future__ import annotations

import argparse
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import normalize_claim_units
from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_FORMAL_STAGE,
    REBASELINE_MEMOS_DIR,
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_REVIEWED_DIR,
    REBASELINE_STAGING_DB_PATH,
    paper_scope_view,
)
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

DEFAULT_BATCH_SIZE = 100
DEFAULT_REVIEWER = "guoyufan"
PHASE = "post_review_v2"
TASK_SLUG = "framework_v2_post_review"

FRAMEWORK_V2_CLAIM_FIELDS = (
    "ai_intervention_mode_codes",
    "ai_intervention_intensity_codes",
    "evaluation_tension_codes",
    "formal_norm_reference_codes",
    "boundary_mechanism_codes",
    "boundary_result_codes",
)

V2_MEMO_TEMPLATE = """# framework_v2.batch_{batch_index:02d} 人工补码备忘

- 正式阶段：`{formal_stage} post-only`
- 运行批次：`{run_id}`
- review_phase：`post_review_v2`
- 审核人：`{reviewer}`
- 审核日期：

## 允许编辑

- `review_status`
- `review_date`
- `claim_units[*].ai_intervention_mode_codes`
- `claim_units[*].ai_intervention_intensity_codes`
- `claim_units[*].evaluation_tension_codes`
- `claim_units[*].formal_norm_reference_codes`
- `claim_units[*].boundary_mechanism_codes`
- `claim_units[*].boundary_result_codes`
- `framework_v2_reviewer_notes`

## 不允许编辑

- `decision`
- `workflow_dimension`
- `legitimacy_evaluation`
- `boundary_expression`
- `claim_units[*]` 中除 F/G/H/I/J/K 外的旧字段

## v2 编码规则

- F 组至少 1 个，允许多选。
- G 组正好 1 个。
- H 组仅在文本明确呈现张力时填写，允许为空或多选。
- I 组至少 1 个；无正式规范参照时填 `I0`，且 `I0` 不得与 `I1-I8` 同时出现。
- 有 D 组边界时，J 组至少 1 个，K 组正好 1 个。
- 无 D 组边界时，J/K 组保持为空。
- 任一 v2 代码必须能回到该 claim unit 的 `evidence`。
"""


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _run_id(batch_index: int) -> str:
    return f"qv5_framework_v2_post_review_batch_{batch_index:02d}"


def _batch_path(directory: Path, batch_index: int, suffix: str) -> Path:
    return directory / f"{TASK_SLUG}.batch_{batch_index:02d}.{suffix}"


def _load_formal_post_ids(connection) -> list[str]:
    scope_view = paper_scope_view("posts")
    return [
        str(row["post_id"])
        for row in connection.execute(
            f"""
            SELECT post_id
            FROM {scope_view}
            ORDER BY post_date, post_id
            """
        ).fetchall()
    ]


def _load_latest_post_review_payloads(connection) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for row in connection.execute(
        """
        SELECT record_id, payload_json
        FROM reviewed_records
        WHERE review_phase = 'post_review_v2' AND record_type = 'post'
        ORDER BY id
        """
    ).fetchall():
        payloads[str(row["record_id"])] = json.loads(str(row["payload_json"]))
    return payloads


def _template_claim_units(payload: dict[str, Any]) -> list[dict[str, Any]]:
    units = normalize_claim_units(payload.get("claim_units"))
    templated: list[dict[str, Any]] = []
    for unit in units:
        next_unit = deepcopy(unit)
        for field_name in FRAMEWORK_V2_CLAIM_FIELDS:
            next_unit[field_name] = []
        templated.append(next_unit)
    return templated


def _template_row(
    *,
    payload: dict[str, Any],
    batch_index: int,
    reviewer: str,
) -> dict[str, Any]:
    row = deepcopy(payload)
    row["run_id"] = _run_id(batch_index)
    row["review_phase"] = PHASE
    row["review_status"] = "unreviewed"
    row["reviewer"] = reviewer
    row["review_date"] = ""
    row["framework_v2_update"] = True
    row["framework_v2_source_run_id"] = str(payload.get("run_id") or "")
    row["framework_v2_reviewer_notes"] = []
    row["claim_units"] = _template_claim_units(payload)
    row.pop("claim_unit_template", None)
    return row


def _write_memo(
    *,
    batch_index: int,
    reviewer: str,
    memos_dir: Path,
) -> Path:
    path = _batch_path(memos_dir, batch_index, "memo.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        V2_MEMO_TEMPLATE.format(
            batch_index=batch_index,
            formal_stage=ACTIVE_FORMAL_STAGE,
            run_id=_run_id(batch_index),
            reviewer=reviewer,
        ),
        encoding="utf-8",
    )
    return path


def prepare_framework_v2_review_batches(
    *,
    db_path: Path = REBASELINE_STAGING_DB_PATH,
    batch_size: int = DEFAULT_BATCH_SIZE,
    reviewer: str = DEFAULT_REVIEWER,
    queue_dir: Path = REBASELINE_REVIEW_QUEUE_DIR,
    reviewed_dir: Path = REBASELINE_REVIEWED_DIR,
    memos_dir: Path = REBASELINE_MEMOS_DIR,
) -> Path:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    with connect_sqlite_readonly(db_path) as connection:
        formal_post_ids = _load_formal_post_ids(connection)
        latest_payloads = _load_latest_post_review_payloads(connection)

    missing_payloads = [post_id for post_id in formal_post_ids if post_id not in latest_payloads]
    if missing_payloads:
        preview = ", ".join(missing_payloads[:10])
        raise ValueError(
            "Cannot prepare framework_v2 batches because formal posts are missing latest "
            f"post_review_v2 payloads: {preview}"
        )

    batch_count = math.ceil(len(formal_post_ids) / batch_size) if formal_post_ids else 0
    batches: list[dict[str, Any]] = []
    for batch_index in range(batch_count):
        post_ids = formal_post_ids[batch_index * batch_size : (batch_index + 1) * batch_size]
        rows = [
            _template_row(
                payload=latest_payloads[post_id],
                batch_index=batch_index,
                reviewer=reviewer,
            )
            for post_id in post_ids
        ]
        queue_path = _write_jsonl(_batch_path(queue_dir, batch_index, "jsonl"), rows)
        template_path = _write_jsonl(
            _batch_path(reviewed_dir, batch_index, "review_template.jsonl"),
            rows,
        )
        memo_path = _write_memo(batch_index=batch_index, reviewer=reviewer, memos_dir=memos_dir)
        batches.append(
            {
                "batch_index": batch_index,
                "run_id": _run_id(batch_index),
                "row_count": len(rows),
                "queue_path": str(queue_path),
                "review_template_path": str(template_path),
                "memo_path": str(memo_path),
            }
        )

    manifest = {
        "task": TASK_SLUG,
        "formal_stage": ACTIVE_FORMAL_STAGE,
        "review_phase": PHASE,
        "db_path": str(db_path),
        "batch_size": batch_size,
        "reviewer": reviewer,
        "row_count": len(formal_post_ids),
        "batch_count": batch_count,
        "batches": batches,
        "constraints": {
            "formal_posts_only": True,
            "formal_comments_remain_zero": True,
            "llm_prefill": "disabled",
            "db_schema_migration": "disabled",
        },
    }
    manifest_path = reviewed_dir / f"{TASK_SLUG}.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare manual framework_v2 F/G/H/I/J/K review templates."
    )
    parser.add_argument("--db", type=Path, default=REBASELINE_STAGING_DB_PATH)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    parser.add_argument("--queue-dir", type=Path, default=REBASELINE_REVIEW_QUEUE_DIR)
    parser.add_argument("--reviewed-dir", type=Path, default=REBASELINE_REVIEWED_DIR)
    parser.add_argument("--memos-dir", type=Path, default=REBASELINE_MEMOS_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest_path = prepare_framework_v2_review_batches(
        db_path=args.db,
        batch_size=args.batch_size,
        reviewer=args.reviewer,
        queue_dir=args.queue_dir,
        reviewed_dir=args.reviewed_dir,
        memos_dir=args.memos_dir,
    )
    print(manifest_path)


__all__ = ["prepare_framework_v2_review_batches", "main"]


if __name__ == "__main__":
    main()
