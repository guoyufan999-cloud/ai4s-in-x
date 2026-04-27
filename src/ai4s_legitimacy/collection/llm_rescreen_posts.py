from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection._jsonl import (
    load_jsonl as _load_jsonl,
    write_jsonl as _write_jsonl,
)
from ai4s_legitimacy.collection.canonical_schema import (
    format_decision_reason,
    sample_status_to_decision,
)
from ai4s_legitimacy.collection.deepseek_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REASONER_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    DeepSeekClient,
)
from ai4s_legitimacy.collection.llm_rescreen_prompts import (
    _stage1_system_prompt,
    _stage2_system_prompt,
)
from ai4s_legitimacy.collection.llm_rescreen_outputs import (
    REVIEW_PHASE as REVIEW_PHASE,
    _actor_change_key as _actor_change_key,
    _build_analysis_markdown as _build_analysis_markdown,
    _build_false_sample as _build_false_sample,
    _build_spot_checks as _build_spot_checks,
    _build_summary as _build_summary,
    _canonical_confidence_label as _canonical_confidence_label,
    _example_titles as _example_titles,
    _priority_promoted_to_true_or_review_needed as _priority_promoted_to_true_or_review_needed,
    _priority_reverted_positive_to_false as _priority_reverted_positive_to_false,
    _priority_true_or_review_needed as _priority_true_or_review_needed,
    _status_change_key as _status_change_key,
    _top_query_patterns as _top_query_patterns,
    _write_markdown as _write_markdown,
    _write_run_outputs as _write_run_outputs,
)
from ai4s_legitimacy.collection.llm_rescreen_rules import (
    ACTOR_TYPE_VALUES as ACTOR_TYPE_VALUES,
    AI_TERMS as AI_TERMS,
    CONFIDENCE_THRESHOLD as CONFIDENCE_THRESHOLD,
    FIRST_PERSON_TERMS as FIRST_PERSON_TERMS,
    LEGITIMACY_TERMS as LEGITIMACY_TERMS,
    LOW_INFORMATION_STATUSES as LOW_INFORMATION_STATUSES,
    RESEARCH_TERMS as RESEARCH_TERMS,
    SAMPLE_STATUS_VALUES as SAMPLE_STATUS_VALUES,
    VENDOR_NEWS_TERMS as VENDOR_NEWS_TERMS,
    WORKFLOW_TERMS as WORKFLOW_TERMS,
    _apply_guardrails as _apply_guardrails,
    _coerce_confidence as _coerce_confidence,
    _fallback_result as _fallback_result,
    _has_first_person_practice_signal as _has_first_person_practice_signal,
    _has_research_ai_signal as _has_research_ai_signal,
    _has_strong_low_info_relevance as _has_strong_low_info_relevance,
    _is_high_signal_low_confidence_false as _is_high_signal_low_confidence_false,
    _is_low_information as _is_low_information,
    _is_low_information_vendor_false as _is_low_information_vendor_false,
    _is_positive as _is_positive,
    _looks_like_vendor_news as _looks_like_vendor_news,
    _needs_reasoner_review as _needs_reasoner_review,
    _normalize_current_actor as _normalize_current_actor,
    _normalize_current_status as _normalize_current_status,
    _normalize_model_item as _normalize_model_item,
    _normalize_risk_flags as _normalize_risk_flags,
    _serialize_queue_row_for_model as _serialize_queue_row_for_model,
)
from ai4s_legitimacy.collection.review_queue import export_review_queue
from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)


DEFAULT_STAGE1_BATCH_SIZE = 8
DEFAULT_STAGE2_BATCH_SIZE = 4
DEFAULT_MAX_WORKERS = 6
DEFAULT_FALSE_SAMPLE_SIZE = 100
DEFAULT_REVIEWER = "guoyufan"
DEFAULT_RUN_ID = "qv5_rescreen_deepseek_full_v1"
MAX_STAGE2_COVERAGE_RATIO = 0.7


def _compute_shard_bounds(total_rows: int, *, shard_index: int, shard_count: int) -> tuple[int, int]:
    if shard_count <= 0:
        raise ValueError("shard_count must be a positive integer")
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must be between 0 and shard_count - 1")
    start = total_rows * shard_index // shard_count
    end = total_rows * (shard_index + 1) // shard_count
    return start, end


def _select_shard_rows(
    queue_rows: Sequence[dict[str, Any]],
    *,
    shard_index: int,
    shard_count: int,
) -> tuple[list[dict[str, Any]], int, int]:
    start, end = _compute_shard_bounds(len(queue_rows), shard_index=shard_index, shard_count=shard_count)
    shard_rows: list[dict[str, Any]] = []
    for queue_position, row in enumerate(queue_rows[start:end], start=start):
        shard_rows.append(dict(row) | {"queue_position": queue_position})
    return shard_rows, start, end


def _shard_name(shard_index: int, shard_count: int) -> str:
    width = max(2, len(str(max(shard_count - 1, 0))))
    return f"shard_{shard_index:0{width}d}_of_{shard_count:0{width}d}"


def _shard_dir(run_dir: Path, *, shard_index: int, shard_count: int) -> Path:
    return run_dir / "shards" / _shard_name(shard_index, shard_count)


def _load_summary_if_complete(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    summary = json.loads(path.read_text(encoding="utf-8"))
    outputs = summary.get("outputs", {})
    if not isinstance(outputs, dict):
        return None
    for output_path in outputs.values():
        if not Path(output_path).exists():
            return None
    return summary


def _validate_queue_rows(rows: Sequence[dict[str, Any]]) -> None:
    for row in rows:
        review_phase = str(row.get("review_phase") or "").strip()
        if review_phase != REVIEW_PHASE:
            raise ValueError(
                f"LLM rescreen only supports {REVIEW_PHASE}, got review_phase={review_phase!r}"
            )
        if not str(row.get("post_id") or row.get("record_id") or "").strip():
            raise ValueError("Each queue row must contain post_id or record_id")


@dataclass(slots=True)
class BatchClassifier:
    client: DeepSeekClient
    model: str
    mode: str

    def classify_batch(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        messages = self._build_messages(rows)
        response = self.client.complete_json(model=self.model, messages=messages)
        payload = response["parsed"]
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("DeepSeek response must contain items[]")

        items_by_batch_id = {
            str(item.get("batch_item_id") or "").strip(): item for item in items if item
        }
        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            batch_id = f"item_{index:03d}"
            if batch_id not in items_by_batch_id:
                raise ValueError(f"DeepSeek response missing {batch_id}")
            normalized_item = _normalize_model_item(
                items_by_batch_id[batch_id],
                fallback_actor_type=_normalize_current_actor(row.get("actor_type")),
            )
            normalized_item = _apply_guardrails(row, normalized_item)
            normalized_item["model"] = str(response["model"] or self.model)
            normalized.append(normalized_item)
        return normalized

    def _build_messages(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
        if self.mode == "stage1":
            items = []
            for index, row in enumerate(rows):
                items.append(
                    {"batch_item_id": f"item_{index:03d}"} | _serialize_queue_row_for_model(row)
                )
            user_payload = {
                "task": "rescreen_posts",
                "output_schema": {
                    "items": [
                        {
                            "batch_item_id": "item_000",
                            "sample_status": "true|false|review_needed",
                            "actor_type": "|".join(sorted(ACTOR_TYPE_VALUES)),
                            "ai_review_reason": "short reason",
                            "ai_confidence": 0.0,
                            "risk_flags": ["low_information"],
                        }
                    ]
                },
                "records": items,
            }
            return [
                {"role": "system", "content": _stage1_system_prompt()},
                {
                    "role": "user",
                    "content": (
                        "请仅输出 JSON。下面是需要判断的 records。\n"
                        + json.dumps(user_payload, ensure_ascii=False)
                    ),
                },
            ]

        items = []
        for index, row in enumerate(rows):
            stage1 = row["stage1_result"]
            items.append(
                {
                    "batch_item_id": f"item_{index:03d}",
                    "current_screening": {
                        "sample_status": _normalize_current_status(row.get("sample_status")),
                        "actor_type": _normalize_current_actor(row.get("actor_type")),
                    },
                    "stage1_suggestion": {
                        "sample_status": stage1["sample_status"],
                        "actor_type": stage1["actor_type"],
                        "ai_review_reason": stage1["ai_review_reason"],
                        "ai_confidence": stage1["ai_confidence"],
                        "risk_flags": stage1["risk_flags"],
                    },
                }
                | _serialize_queue_row_for_model(row)
            )
        user_payload = {
            "task": "rescreen_posts_reasoner_review",
            "output_schema": {
                "items": [
                    {
                        "batch_item_id": "item_000",
                        "sample_status": "true|false|review_needed",
                        "actor_type": "|".join(sorted(ACTOR_TYPE_VALUES)),
                        "ai_review_reason": "short reason",
                        "ai_confidence": 0.0,
                        "risk_flags": ["needs_more_context"],
                    }
                ]
            },
            "records": items,
        }
        return [
            {"role": "system", "content": _stage2_system_prompt()},
            {
                "role": "user",
                "content": (
                    "请仅输出 JSON。下面是需要复核的 records。\n"
                    + json.dumps(user_payload, ensure_ascii=False)
                ),
            },
        ]


def _run_classifier_batches(
    rows: Sequence[dict[str, Any]],
    *,
    classifier: BatchClassifier,
    batch_size: int,
    max_workers: int,
    log: Callable[[str], None],
) -> list[dict[str, Any]]:
    batches: list[tuple[int, list[dict[str, Any]]]] = []
    for start in range(0, len(rows), batch_size):
        batches.append((start, list(rows[start : start + batch_size])))

    results: list[dict[str, Any] | None] = [None] * len(rows)

    def run_one_batch(batch_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            return classifier.classify_batch(batch_rows)
        except Exception as exc:  # pragma: no cover - exercised by integration fallbacks
            return [
                _fallback_result(
                    row,
                    reason=f"{classifier.mode}_error: {type(exc).__name__}",
                    model=classifier.model,
                )
                for row in batch_rows
            ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(run_one_batch, batch_rows): (start, batch_rows)
            for start, batch_rows in batches
        }
        completed = 0
        for future in as_completed(future_map):
            start, batch_rows = future_map[future]
            batch_results = future.result()
            for offset, result in enumerate(batch_results):
                results[start + offset] = result
            completed += len(batch_rows)
            log(f"[{classifier.mode}] completed {completed}/{len(rows)} rows")

    return [result for result in results if result is not None]


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
    run_id: str = DEFAULT_RUN_ID,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    chat_classifier: BatchClassifier,
    reasoner_classifier: BatchClassifier,
    stage1_batch_size: int = DEFAULT_STAGE1_BATCH_SIZE,
    stage2_batch_size: int = DEFAULT_STAGE2_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    false_sample_size: int = DEFAULT_FALSE_SAMPLE_SIZE,
    shard_index: int,
    shard_count: int,
    queue_start: int,
    queue_end: int,
    log: Callable[[str], None] | None = None,
    max_stage2_coverage_ratio: float = MAX_STAGE2_COVERAGE_RATIO,
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

    review_date = review_date or date.today().isoformat()
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
        review_date=review_date,
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
    run_id: str = DEFAULT_RUN_ID,
    shard_count: int,
    false_sample_size: int = DEFAULT_FALSE_SAMPLE_SIZE,
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


def generate_llm_rescreen_draft(
    *,
    queue_path: Path,
    output_dir: Path = REBASELINE_SUGGESTIONS_DIR,
    run_id: str = DEFAULT_RUN_ID,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    chat_classifier: BatchClassifier,
    reasoner_classifier: BatchClassifier,
    stage1_batch_size: int = DEFAULT_STAGE1_BATCH_SIZE,
    stage2_batch_size: int = DEFAULT_STAGE2_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    false_sample_size: int = DEFAULT_FALSE_SAMPLE_SIZE,
    shard_count: int = 1,
    shard_index: int = 0,
    resume: bool = False,
    merge_only: bool = False,
    log: Callable[[str], None] | None = None,
    max_stage2_coverage_ratio: float = MAX_STAGE2_COVERAGE_RATIO,
) -> dict[str, Any]:
    if false_sample_size <= 0:
        raise ValueError("false_sample_size must be a positive integer")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if merge_only:
        return _merge_shard_outputs(
            run_dir=run_dir,
            run_id=run_id,
            shard_count=shard_count,
            false_sample_size=false_sample_size,
        )

    shard_dir = _shard_dir(run_dir, shard_index=shard_index, shard_count=shard_count)
    shard_dir.mkdir(parents=True, exist_ok=True)
    summary_path = shard_dir / f"{_shard_name(shard_index, shard_count)}.summary.json"
    if resume:
        existing = _load_summary_if_complete(summary_path)
        if existing is not None:
            return existing

    queue_rows = _load_jsonl(queue_path)
    _validate_queue_rows(queue_rows)
    shard_rows, queue_start, queue_end = _select_shard_rows(
        queue_rows,
        shard_index=shard_index,
        shard_count=shard_count,
    )

    return _generate_shard_draft(
        shard_rows=shard_rows,
        run_dir=shard_dir,
        run_id=run_id,
        reviewer=reviewer,
        review_date=review_date,
        chat_classifier=chat_classifier,
        reasoner_classifier=reasoner_classifier,
        stage1_batch_size=stage1_batch_size,
        stage2_batch_size=stage2_batch_size,
        max_workers=max_workers,
        false_sample_size=false_sample_size,
        shard_index=shard_index,
        shard_count=shard_count,
        queue_start=queue_start,
        queue_end=queue_end,
        log=log,
        max_stage2_coverage_ratio=max_stage2_coverage_ratio,
    )


def run_llm_rescreen(
    *,
    queue_path: Path,
    output_dir: Path = REBASELINE_SUGGESTIONS_DIR,
    run_id: str = DEFAULT_RUN_ID,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL,
    chat_model: str = DEFAULT_CHAT_MODEL,
    reasoner_model: str = DEFAULT_REASONER_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    stage1_batch_size: int = DEFAULT_STAGE1_BATCH_SIZE,
    stage2_batch_size: int = DEFAULT_STAGE2_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    false_sample_size: int = DEFAULT_FALSE_SAMPLE_SIZE,
    shard_count: int = 1,
    shard_index: int = 0,
    resume: bool = False,
    merge_only: bool = False,
    db_path: Path = REBASELINE_STAGING_DB_PATH,
) -> dict[str, Any]:
    if not queue_path.exists():
        export_review_queue(
            db_path=db_path,
            phase=REVIEW_PHASE,
            output_path=queue_path,
        )
    client = DeepSeekClient.from_env()
    client.base_url = base_url
    client.timeout_seconds = timeout_seconds
    client.max_retries = max_retries
    return generate_llm_rescreen_draft(
        queue_path=queue_path,
        output_dir=output_dir,
        run_id=run_id,
        reviewer=reviewer,
        review_date=review_date,
        chat_classifier=BatchClassifier(client=client, model=chat_model, mode="stage1"),
        reasoner_classifier=BatchClassifier(client=client, model=reasoner_model, mode="stage2"),
        stage1_batch_size=stage1_batch_size,
        stage2_batch_size=stage2_batch_size,
        max_workers=max_workers,
        false_sample_size=false_sample_size,
        shard_count=shard_count,
        shard_index=shard_index,
        resume=resume,
        merge_only=merge_only,
        log=print,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate DeepSeek-assisted rescreen_posts draft JSONL without writing to the DB."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=REBASELINE_STAGING_DB_PATH,
        help="Staging DB path used only when the queue needs to be exported.",
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=REBASELINE_REVIEW_QUEUE_DIR / f"{REVIEW_PHASE}.jsonl",
        help="Existing rescreen_posts queue JSONL. If missing, it will be exported from --db.",
    )
    parser.add_argument("--output-dir", type=Path, default=REBASELINE_SUGGESTIONS_DIR)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    parser.add_argument("--review-date", default=None)
    parser.add_argument("--base-url", default=DEFAULT_DEEPSEEK_BASE_URL)
    parser.add_argument("--chat-model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--reasoner-model", default=DEFAULT_REASONER_MODEL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--stage1-batch-size", type=int, default=DEFAULT_STAGE1_BATCH_SIZE)
    parser.add_argument("--stage2-batch-size", type=int, default=DEFAULT_STAGE2_BATCH_SIZE)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument("--false-sample-size", type=int, default=DEFAULT_FALSE_SAMPLE_SIZE)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_llm_rescreen(
        queue_path=args.queue,
        output_dir=args.output_dir,
        run_id=args.run_id,
        reviewer=args.reviewer,
        review_date=args.review_date,
        base_url=args.base_url,
        chat_model=args.chat_model,
        reasoner_model=args.reasoner_model,
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        stage1_batch_size=args.stage1_batch_size,
        stage2_batch_size=args.stage2_batch_size,
        max_workers=args.max_workers,
        false_sample_size=args.false_sample_size,
        shard_count=args.shard_count,
        shard_index=args.shard_index,
        resume=args.resume,
        merge_only=args.merge_only,
        db_path=args.db,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
