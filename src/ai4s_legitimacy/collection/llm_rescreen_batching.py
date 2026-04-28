from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.deepseek_client import DeepSeekClient
from ai4s_legitimacy.collection.llm_rescreen_outputs import REVIEW_PHASE
from ai4s_legitimacy.collection.llm_rescreen_prompts import (
    _stage1_system_prompt,
    _stage2_system_prompt,
)
from ai4s_legitimacy.collection.llm_rescreen_rules import (
    ACTOR_TYPE_VALUES,
    _apply_guardrails,
    _fallback_result,
    _normalize_current_actor,
    _normalize_current_status,
    _normalize_model_item,
    _serialize_queue_row_for_model,
)


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
    batches = [
        (start, list(rows[start : start + batch_size]))
        for start in range(0, len(rows), batch_size)
    ]

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
