from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.review_queue import export_review_queue
from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_FORMAL_STAGE,
    REBASELINE_MEMOS_DIR,
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_REVIEWED_DIR,
    REBASELINE_STAGING_DB_PATH,
    paper_scope_view,
)
from ai4s_legitimacy.config.research_baseline import (
    PRIMARY_ANALYSIS_AXES,
    SCREENING_SELF_CHECKS,
)
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

DEFAULT_BATCH_SIZE = 250
DEFAULT_REVIEWER = "guoyufan"
DEFAULT_TEMPLATE_BATCH_INDEX = 0

CLAIM_UNIT_TEMPLATE = {
    "practice_unit": "",
    "workflow_stage_codes": [],
    "legitimacy_codes": [],
    "basis_codes": [],
    "boundary_codes": [],
    "boundary_mode_codes": [],
    "ai_intervention_mode_codes": [],
    "ai_intervention_intensity_codes": [],
    "evaluation_tension_codes": [],
    "formal_norm_reference_codes": [],
    "boundary_mechanism_codes": [],
    "boundary_result_codes": [],
    "evidence": [],
}

REVIEW_TEMPLATE_PHASES = frozenset(
    {
        "rescreen_posts",
        "post_review",
        "post_review_v2",
        "comment_review",
        "comment_review_v2",
    }
)

REVIEW_MEMO_TEMPLATE = """# {phase}.batch_{batch_index:02d} 判例备忘

- 运行批次：`{run_id}`
- 阶段：`{phase}`
- 审核人：`{reviewer}`
- 审核日期：

## 当前主线

- {analysis_axes}

## 编码自检

{self_checks}

## 高频边界案例

### AI 与科研同时出现但不构成 AI4S 科研工作流实践

- 

### 科研训练 vs 普通学习 / 作业 / 备考

- 

### 工具推荐 / 产品宣传 vs 真实科研实践

- 

### 研究相关但宣传账号

- 

### 明确合法性评价但工作流环节不清

- 

## 需二次复核样本

- 
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _batch_suffix(batch_index: int) -> str:
    return f"batch_{batch_index:02d}"


def _batch_path_for_phase(phase: str, batch_index: int, queue_dir: Path) -> Path:
    return queue_dir / f"{phase}.{_batch_suffix(batch_index)}.jsonl"


def _template_path_for_phase(phase: str, batch_index: int, reviewed_dir: Path) -> Path:
    return reviewed_dir / f"{phase}.{_batch_suffix(batch_index)}.review_template.jsonl"


def _memo_path_for_phase(phase: str, batch_index: int, memos_dir: Path) -> Path:
    return memos_dir / f"{phase}.{_batch_suffix(batch_index)}.memo.md"


def _run_id_for_batch(phase: str, batch_index: int) -> str:
    phase_slug = "rescreen" if phase == "rescreen_posts" else phase
    return f"qv5_{phase_slug}_{_batch_suffix(batch_index)}"


def _build_review_template_row(
    *,
    phase: str,
    row: dict[str, Any],
    reviewer: str,
    batch_index: int,
) -> dict[str, Any]:
    template = dict(row)
    template.update(
        {
            "run_id": _run_id_for_batch(phase, batch_index),
            "review_phase": phase,
            "review_status": "unreviewed",
            "reviewer": reviewer,
            "review_date": "",
        }
    )
    if phase in {"post_review_v2", "comment_review_v2"}:
        template.update(
            {
                "decision": "待复核",
                "decision_reason": [],
                "target_practice_summary": "",
                "evidence_master": [],
                "workflow_dimension": {
                    "primary_dimension": [],
                    "secondary_stage": [],
                    "evidence": [],
                },
                "legitimacy_evaluation": {
                    "direction": [],
                    "basis": [],
                    "evidence": [],
                },
                "boundary_expression": {
                    "present": "否",
                    "boundary_content_codes": [],
                    "boundary_expression_mode_codes": [],
                    "evidence": [],
                },
                "interaction_level": {
                    "event_present": "不适用"
                    if str(template.get("context_used") or "none") == "none"
                    else "无法判断",
                    "interaction_role": "unclear",
                    "target_claim_summary": "",
                    "event_codes": [],
                    "event_basis_codes": [],
                    "event_outcome": "",
                    "evidence": [],
                },
                "claim_units": [],
                "claim_unit_template": CLAIM_UNIT_TEMPLATE,
                "mechanism_memo": {
                    "eligible_for_mechanism_analysis": "否",
                    "candidate_pattern_notes": [],
                    "comparison_keys": [],
                },
                "notes": {
                    "multi_label": "否",
                    "ambiguity": "否",
                    "confidence": "中",
                    "review_points": [],
                    "dedup_group": str(
                        row.get("record_id")
                        or row.get("post_id")
                        or row.get("comment_id")
                        or ""
                    ),
                },
            }
        )
    return template


def _write_batch_memo_template(
    *,
    phase: str,
    batch_index: int,
    reviewer: str,
    memos_dir: Path,
) -> Path | None:
    if phase not in {"rescreen_posts", "post_review", "post_review_v2", "comment_review_v2"}:
        return None
    memo_path = _memo_path_for_phase(phase, batch_index, memos_dir)
    memo_path.parent.mkdir(parents=True, exist_ok=True)
    memo_path.write_text(
        REVIEW_MEMO_TEMPLATE.format(
            batch_index=batch_index,
            phase=phase,
            reviewer=reviewer,
            run_id=_run_id_for_batch(phase, batch_index),
            analysis_axes=" / ".join(PRIMARY_ANALYSIS_AXES),
            self_checks="\n".join(f"- {item}" for item in SCREENING_SELF_CHECKS),
        ),
        encoding="utf-8",
    )
    return memo_path


def _load_preflight_counts(db_path: Path) -> dict[str, Any]:
    post_scope_view = paper_scope_view("posts")
    comment_scope_view = paper_scope_view("comments")
    with connect_sqlite_readonly(db_path) as connection:
        posts = int(connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0])
        comments = int(connection.execute("SELECT COUNT(*) FROM comments").fetchone()[0])
        codes = int(connection.execute("SELECT COUNT(*) FROM codes").fetchone()[0])
        scope_posts = int(
            connection.execute(f"SELECT COUNT(*) FROM {post_scope_view}").fetchone()[0]
        )
        scope_comments = int(
            connection.execute(f"SELECT COUNT(*) FROM {comment_scope_view}").fetchone()[0]
        )
        sample_status_rows = [
            dict(row)
            for row in connection.execute(
                """
                SELECT COALESCE(sample_status, '') AS sample_status, COUNT(*) AS count
                FROM posts
                GROUP BY COALESCE(sample_status, '')
                ORDER BY sample_status
                """
            ).fetchall()
        ]

    return {
        "active_stage": ACTIVE_FORMAL_STAGE,
        "counts": {
            "posts": posts,
            "comments": comments,
            "codes": codes,
            "paper_scope_posts": scope_posts,
            "paper_scope_comments": scope_comments,
        },
        "sample_status_distribution": sample_status_rows,
    }


def prepare_review_batches(
    *,
    db_path: Path = REBASELINE_STAGING_DB_PATH,
    phase: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    reviewer: str = DEFAULT_REVIEWER,
    template_batch_index: int = DEFAULT_TEMPLATE_BATCH_INDEX,
    queue_dir: Path = REBASELINE_REVIEW_QUEUE_DIR,
    reviewed_dir: Path = REBASELINE_REVIEWED_DIR,
    memos_dir: Path = REBASELINE_MEMOS_DIR,
) -> Path:
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if phase not in REVIEW_TEMPLATE_PHASES:
        valid_phases = ", ".join(sorted(REVIEW_TEMPLATE_PHASES))
        raise ValueError(
            f"Unsupported review phase for batch prep: {phase}. Expected one of: {valid_phases}"
        )

    queue_path = export_review_queue(
        db_path=db_path,
        phase=phase,
        output_path=queue_dir / f"{phase}.jsonl",
    )
    queue_rows = _load_jsonl(queue_path)
    if phase == "post_review_v2":
        priority_order = {
            "current_review_needed": 0,
            "deepseek_conflict": 1,
            "historical_true_vendor": 2,
            "remaining_posts": 3,
        }
        queue_rows.sort(
            key=lambda row: (
                priority_order.get(str(row.get("priority_bucket") or ""), 9),
                str(row.get("post_date") or ""),
                str(row.get("post_id") or ""),
            )
        )
        _write_jsonl(queue_path, queue_rows)
    total_rows = len(queue_rows)
    batch_count = math.ceil(total_rows / batch_size) if total_rows else 0

    batch_records: list[dict[str, Any]] = []
    template_path: Path | None = None
    memo_path: Path | None = None

    for batch_index in range(batch_count):
        start = batch_index * batch_size
        end = start + batch_size
        batch_rows = queue_rows[start:end]
        batch_path = _write_jsonl(_batch_path_for_phase(phase, batch_index, queue_dir), batch_rows)
        batch_records.append(
            {
                "batch_index": batch_index,
                "run_id": _run_id_for_batch(phase, batch_index),
                "path": str(batch_path),
                "row_count": len(batch_rows),
            }
        )

        if batch_index == template_batch_index:
            template_rows = [
                _build_review_template_row(
                    phase=phase,
                    row=row,
                    reviewer=reviewer,
                    batch_index=batch_index,
                )
                for row in batch_rows
            ]
            template_path = _write_jsonl(
                _template_path_for_phase(phase, batch_index, reviewed_dir),
                template_rows,
            )
            memo_path = _write_batch_memo_template(
                phase=phase,
                batch_index=batch_index,
                reviewer=reviewer,
                memos_dir=memos_dir,
            )

    manifest_path = queue_dir / f"{phase}.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": phase,
        "db_path": str(db_path),
        "queue_path": str(queue_path),
        "batch_size": batch_size,
        "row_count": total_rows,
        "batch_count": batch_count,
        "template_batch_index": template_batch_index,
        "reviewer": reviewer,
        "batches": batch_records,
        "review_template_path": str(template_path) if template_path else None,
        "memo_template_path": str(memo_path) if memo_path else None,
        "preflight": _load_preflight_counts(db_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare batched review queues and batch_00 templates for quality_v5 rebaseline review."
    )
    parser.add_argument("--db", type=Path, default=REBASELINE_STAGING_DB_PATH)
    parser.add_argument("--phase", choices=sorted(REVIEW_TEMPLATE_PHASES), required=True)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    parser.add_argument("--template-batch-index", type=int, default=DEFAULT_TEMPLATE_BATCH_INDEX)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(
        prepare_review_batches(
            db_path=args.db,
            phase=args.phase,
            batch_size=args.batch_size,
            reviewer=args.reviewer,
            template_batch_index=args.template_batch_index,
        )
    )


if __name__ == "__main__":
    main()
