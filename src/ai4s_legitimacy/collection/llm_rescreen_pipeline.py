from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection._jsonl import (
    load_jsonl as _load_jsonl,
)
from ai4s_legitimacy.collection._jsonl import (
    write_jsonl as _write_jsonl,
)
from ai4s_legitimacy.collection.canonical_schema import (
    format_decision_reason,
    sample_status_to_decision,
)
from ai4s_legitimacy.collection.llm_rescreen_batching import (
    BatchClassifier,
    _load_summary_if_complete,
    _run_classifier_batches,
    _shard_dir,
    _shard_name,
    _validate_queue_rows,
)
from ai4s_legitimacy.collection.llm_rescreen_outputs import (
    REVIEW_PHASE,
    _build_analysis_markdown,
    _build_summary,
    _canonical_confidence_label,
    _priority_promoted_to_true_or_review_needed,
    _write_markdown,
    _write_run_outputs,
)
from ai4s_legitimacy.collection.llm_rescreen_rules import (
    _needs_reasoner_review,
    _normalize_current_actor,
    _normalize_current_status,
)


def _merge_final_rows(
    queue_rows: Sequence[dict[str, Any]],
    stage1_results: Sequence[dict[str, Any]],
    stage2_results_by_post_id: dict[str, dict[str, Any]],
    *,
    run_id: str,
    reviewer: str,
    review_date: str,
) -> list[dict[str, Any]]:
    final_rows: list[dict[str, Any]] = []
    for row, stage1 in zip(queue_rows, stage1_results, strict=True):
        post_id = str(row.get("post_id") or row.get("record_id") or "").strip()
        final_decision = stage2_results_by_post_id.get(post_id, stage1)
        merged = {
            "run_id": run_id,
            "review_phase": REVIEW_PHASE,
            "review_status": "pending_review",
            "reviewer": reviewer,
            "review_date": review_date,
            "sample_status": final_decision["sample_status"],
            "actor_type": final_decision["actor_type"],
            "ai_review_reason": final_decision["ai_review_reason"],
            "ai_confidence": final_decision["ai_confidence"],
            "risk_flags": final_decision["risk_flags"],
            "current_sample_status": _normalize_current_status(row.get("sample_status")),
            "current_actor_type": _normalize_current_actor(row.get("actor_type")),
            "stage1_sample_status": stage1["sample_status"],
            "stage1_actor_type": stage1["actor_type"],
            "stage1_ai_confidence": stage1["ai_confidence"],
            "stage1_model": stage1["model"],
            "stage2_model": final_decision["model"] if post_id in stage2_results_by_post_id else "",
        }
        for row_field, row_value in row.items():
            if row_field not in merged:
                merged[row_field] = row_value
        canonical = canonicalize_review_row(
            merged,
            base_row=row,
            review_phase=REVIEW_PHASE,
        )
        canonical["decision"] = sample_status_to_decision(final_decision["sample_status"])
        canonical["decision_reason"] = format_decision_reason(
            "R11" if canonical["decision"] == "待复核" else "R12",
            final_decision["ai_review_reason"],
        )
        canonical["review_status"] = "unreviewed"
        canonical["api_assistance"] = {
            "used": "是",
            "purpose": ["candidate_screening"],
            "api_confidence": _canonical_confidence_label(final_decision["ai_confidence"]),
            "adoption_note": final_decision["ai_review_reason"],
        }
        canonical["workflow_dimension"] = {
            "primary_dimension": [],
            "secondary_stage": [],
            "evidence": [],
        }
        canonical["legitimacy_evaluation"] = {
            "direction": [],
            "basis": [],
            "evidence": [],
        }
        canonical["boundary_expression"] = {
            "present": "否",
            "boundary_content_codes": [],
            "boundary_expression_mode_codes": [],
            "evidence": [],
        }
        canonical["interaction_level"] = {
            "event_present": "不适用",
            "interaction_role": "unclear",
            "target_claim_summary": "",
            "event_codes": [],
            "event_basis_codes": [],
            "event_outcome": "",
            "evidence": [],
        }
        canonical["claim_units"] = []
        canonical["evidence_master"] = []
        canonical["notes"]["multi_label"] = "否"
        for extra_field, value in merged.items():
            if extra_field not in canonical:
                canonical[extra_field] = value
        final_rows.append(canonical)
    return final_rows


def _generate_shard_draft(
    *,
    shard_rows: Sequence[dict[str, Any]],
    run_dir: Path,
    run_id: str,
    reviewer: str,
    review_date: str | None,
    chat_classifier: BatchClassifier,
    reasoner_classifier: BatchClassifier,
    stage1_batch_size: int,
    stage2_batch_size: int,
    max_workers: int,
    false_sample_size: int,
    shard_index: int,
    shard_count: int,
    queue_start: int,
    queue_end: int,
    log: Callable[[str], None] | None,
    max_stage2_coverage_ratio: float,
) -> dict[str, Any]:
    logger = log or (lambda _message: None)
    if stage1_batch_size <= 0 or stage2_batch_size <= 0:
        raise ValueError("stage batch sizes must be positive integers")
    if max_workers <= 0:
        raise ValueError("max_workers must be a positive integer")
    if false_sample_size <= 0:
        raise ValueError("false_sample_size must be a positive integer")
    queue_rows = list(shard_rows)
    _validate_queue_rows(queue_rows)

    resolved_review_date = review_date or date.today().isoformat()
    stage1_results = _run_classifier_batches(
        queue_rows,
        classifier=chat_classifier,
        batch_size=stage1_batch_size,
        max_workers=max_workers,
        log=logger,
    )

    stage2_input_rows: list[dict[str, Any]] = []
    for row, stage1 in zip(queue_rows, stage1_results, strict=True):
        if _needs_reasoner_review(row, stage1):
            stage2_input_rows.append(row | {"stage1_result": stage1})

    logger(f"[stage2] selected {len(stage2_input_rows)} high-risk rows")
    coverage_ratio = len(stage2_input_rows) / len(queue_rows) if queue_rows else 0.0
    if coverage_ratio > max_stage2_coverage_ratio:
        raise ValueError(
            "stage2_coverage_ratio exceeded guardrail: "
            f"{coverage_ratio:.4f} > {max_stage2_coverage_ratio:.4f}"
        )
    stage2_results = _run_classifier_batches(
        stage2_input_rows,
        classifier=reasoner_classifier,
        batch_size=stage2_batch_size,
        max_workers=max_workers,
        log=logger,
    )
    stage2_results_by_post_id = {
        str(row.get("post_id") or row.get("record_id") or "").strip(): result
        for row, result in zip(stage2_input_rows, stage2_results, strict=True)
    }

    full_rows = _merge_final_rows(
        queue_rows,
        stage1_results,
        stage2_results_by_post_id,
        run_id=run_id,
        reviewer=reviewer,
        review_date=resolved_review_date,
    )
    delta_rows = [
        row
        for row in full_rows
        if row["sample_status"] != row["current_sample_status"]
        or row["actor_type"] != row["current_actor_type"]
    ]
    summary = _build_summary(
        queue_rows=queue_rows,
        full_rows=full_rows,
        delta_rows=delta_rows,
        reasoner_reviewed_count=len(stage2_input_rows),
        output_paths={},
        shard_index=shard_index,
        shard_count=shard_count,
        queue_start=queue_start,
        queue_end=queue_end,
    )
    summary["false_sample_count"] = min(false_sample_size, summary["full_draft_count"])
    _write_run_outputs(
        run_dir=run_dir,
        file_prefix=_shard_name(shard_index, shard_count),
        full_rows=full_rows,
        delta_rows=delta_rows,
        summary=summary,
    )
    return summary


def _merge_shard_outputs(
    *,
    run_dir: Path,
    run_id: str,
    shard_count: int,
) -> dict[str, Any]:
    shard_summaries: list[dict[str, Any]] = []
    full_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    for shard_index in range(shard_count):
        shard_dir = _shard_dir(run_dir, shard_index=shard_index, shard_count=shard_count)
        summary = _load_summary_if_complete(shard_dir / f"{_shard_name(shard_index, shard_count)}.summary.json")
        if summary is None:
            raise FileNotFoundError(f"Missing complete shard summary for {_shard_name(shard_index, shard_count)}")
        shard_summaries.append(summary)
        full_rows.extend(_load_jsonl(Path(summary["outputs"]["full_draft"])))
        delta_rows.extend(_load_jsonl(Path(summary["outputs"]["delta_only"])))

    full_rows.sort(key=lambda row: row.get("queue_position", 0))
    delta_rows.sort(key=lambda row: row.get("queue_position", 0))
    summary = _build_summary(
        queue_rows=full_rows,
        full_rows=full_rows,
        delta_rows=delta_rows,
        reasoner_reviewed_count=sum(item["reasoner_reviewed_count"] for item in shard_summaries),
        output_paths={},
    )
    summary["shard_count"] = shard_count
    summary["merged_from_shards"] = [_shard_name(index, shard_count) for index in range(shard_count)]
    summary["priority_promoted_to_true_or_review_needed_count"] = len(
        _priority_promoted_to_true_or_review_needed(delta_rows)
    )
    output_paths = _write_run_outputs(
        run_dir=run_dir,
        file_prefix=run_id,
        full_rows=full_rows,
        delta_rows=delta_rows,
        summary=summary,
    )
    promoted_path = _write_jsonl(
        run_dir / f"{run_id}.priority.promoted_to_true_or_review_needed.jsonl",
        _priority_promoted_to_true_or_review_needed(delta_rows),
    )
    output_paths["priority_promoted_to_true_or_review_needed"] = str(promoted_path)
    summary_path = Path(output_paths["summary"])
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    analysis_path = _write_markdown(
        run_dir / f"{run_id}.analysis.md",
        _build_analysis_markdown(
            run_id=run_id,
            full_rows=full_rows,
            delta_rows=delta_rows,
            summary=summary,
        ),
    )
    output_paths["analysis"] = str(analysis_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
