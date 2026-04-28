from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection._jsonl import (
    load_jsonl as _load_jsonl,
)
from ai4s_legitimacy.collection._jsonl import (
    write_jsonl as _write_jsonl,
)
from ai4s_legitimacy.collection.deepseek_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DeepSeekClient,
)
from ai4s_legitimacy.collection.llm_prefill_canonical import (
    _fallback_canonical_row,
    _fallback_item,
    _model_item_to_canonical,
    _normalize_model_item,
)
from ai4s_legitimacy.collection.llm_prefill_prompts import (
    _serialize_queue_row_for_model,
    _system_prompt,
)
from ai4s_legitimacy.config.formal_baseline import REBASELINE_REVIEWED_DIR

REVIEW_PHASE = "post_review_v2"
DEFAULT_BATCH_SIZE = 6
DEFAULT_MAX_WORKERS = 4
DEFAULT_REVIEWER = "guoyufan"


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return normalized.strip("_") or "post_review_v2"


def _default_run_id(queue_path: Path) -> str:
    return f"qv5_{_slugify(queue_path.stem)}_deepseek_prefill_v1"


def _default_output_path(queue_path: Path, output_path: Path | None = None) -> Path:
    if output_path is not None:
        return output_path
    return REBASELINE_REVIEWED_DIR / f"{queue_path.stem}.ai_draft.jsonl"


def _summary_path_for_output(output_path: Path) -> Path:
    return output_path.with_suffix(".summary.json")


def _validate_queue_rows(rows: Sequence[dict[str, Any]]) -> None:
    for row in rows:
        review_phase = str(row.get("review_phase") or "").strip()
        if review_phase != REVIEW_PHASE:
            raise ValueError(
                f"LLM post-review prefill only supports {REVIEW_PHASE}, "
                f"got review_phase={review_phase!r}"
            )
        record_type = str(row.get("record_type") or "post").strip() or "post"
        if record_type != "post":
            raise ValueError(f"LLM post-review prefill only supports posts, got {record_type!r}")
        if not str(row.get("post_id") or row.get("record_id") or "").strip():
            raise ValueError("Each queue row must contain post_id or record_id")


@dataclass(slots=True)
class PostReviewBatchPrefiller:
    client: DeepSeekClient
    model: str

    def prefill_batch(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        messages = self._build_messages(rows)
        response = self.client.complete_json(model=self.model, messages=messages)
        payload = response["parsed"]
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("DeepSeek response must contain items[]")
        items_by_batch_id = {
            str(item.get("batch_item_id") or "").strip(): item
            for item in items
            if isinstance(item, dict)
        }

        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            batch_item_id = f"item_{index:03d}"
            raw_item = items_by_batch_id.get(batch_item_id)
            if raw_item is None:
                normalized_item = _fallback_item("missing_batch_item")
            else:
                try:
                    normalized_item = _normalize_model_item(
                        raw_item,
                        context_used=str(row.get("context_used") or "none").strip() or "none",
                    )
                except Exception as exc:
                    normalized_item = _fallback_item(
                        f"invalid_model_item: {type(exc).__name__}"
                    )
            normalized_item["model"] = str(response.get("model") or self.model)
            normalized.append(normalized_item)
        return normalized

    def _build_messages(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
        items = []
        for index, row in enumerate(rows):
            items.append(
                {"batch_item_id": f"item_{index:03d}"} | _serialize_queue_row_for_model(row)
            )
        user_payload = {
            "task": "post_review_v2_prefill",
            "records": items,
        }
        return [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": (
                    "请仅输出 JSON。下面是需要预填的 post_review_v2 records。\n"
                    + json.dumps(user_payload, ensure_ascii=False)
                ),
            },
        ]


def _prefill_batch_rows(
    batch_rows: Sequence[dict[str, Any]],
    *,
    prefiller: PostReviewBatchPrefiller,
    run_id: str,
    reviewer: str,
    review_date: str,
) -> tuple[list[dict[str, Any]], str | None]:
    try:
        normalized_items = prefiller.prefill_batch(batch_rows)
        return (
            [
                _model_item_to_canonical(
                    row,
                    review_phase=REVIEW_PHASE,
                    normalized_item=item,
                    run_id=run_id,
                    reviewer=reviewer,
                    review_date=review_date,
                )
                for row, item in zip(batch_rows, normalized_items, strict=True)
            ],
            None,
        )
    except Exception as exc:  # pragma: no cover - covered through fallback behavior tests
        message = str(exc).strip()
        reason = f"prefill_batch_error: {type(exc).__name__}"
        if message and isinstance(exc, RuntimeError):
            reason = f"{reason}: {message}"
        return (
            [
                _fallback_canonical_row(
                    row,
                    review_phase=REVIEW_PHASE,
                    run_id=run_id,
                    reviewer=reviewer,
                    review_date=review_date,
                    model=prefiller.model,
                    reason=reason,
                )
                for row in batch_rows
            ],
            reason,
        )


def _run_prefill_batches(
    rows: Sequence[dict[str, Any]],
    *,
    prefiller: PostReviewBatchPrefiller,
    run_id: str,
    reviewer: str,
    review_date: str,
    batch_size: int,
    max_workers: int,
    log: Callable[[str], None],
) -> tuple[list[dict[str, Any]], list[str]]:
    batches = [
        (start, list(rows[start : start + batch_size]))
        for start in range(0, len(rows), batch_size)
    ]

    results: list[dict[str, Any] | None] = [None] * len(rows)
    batch_errors: list[str] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _prefill_batch_rows,
                batch_rows,
                prefiller=prefiller,
                run_id=run_id,
                reviewer=reviewer,
                review_date=review_date,
            ): (start, batch_rows)
            for start, batch_rows in batches
        }
        completed = 0
        for future in as_completed(future_map):
            start, batch_rows = future_map[future]
            batch_rows_result, batch_error = future.result()
            for offset, row in enumerate(batch_rows_result):
                results[start + offset] = row
            if batch_error:
                batch_errors.append(batch_error)
            completed += len(batch_rows)
            log(f"[post_review_prefill] completed {completed}/{len(rows)} rows")

    return [row for row in results if row is not None], batch_errors


def generate_post_review_prefill_draft(
    *,
    queue_path: Path,
    output_path: Path | None = None,
    run_id: str | None = None,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    prefiller: PostReviewBatchPrefiller,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if max_workers <= 0:
        raise ValueError("max_workers must be a positive integer")
    if not queue_path.exists():
        raise FileNotFoundError(f"Queue file not found: {queue_path}")

    queue_rows = _load_jsonl(queue_path)
    _validate_queue_rows(queue_rows)

    resolved_run_id = run_id or _default_run_id(queue_path)
    resolved_review_date = review_date or date.today().isoformat()
    resolved_output_path = _default_output_path(queue_path, output_path=output_path)
    logger = log or (lambda _message: None)

    draft_rows, batch_errors = _run_prefill_batches(
        queue_rows,
        prefiller=prefiller,
        run_id=resolved_run_id,
        reviewer=reviewer,
        review_date=resolved_review_date,
        batch_size=batch_size,
        max_workers=max_workers,
        log=logger,
    )
    draft_path = _write_jsonl(resolved_output_path, draft_rows)

    decision_distribution = Counter(str(row["decision"]) for row in draft_rows)
    summary = {
        "status": "ok" if not batch_errors else "partial_fallback",
        "review_phase": REVIEW_PHASE,
        "queue_path": str(queue_path),
        "output_path": str(draft_path),
        "summary_path": str(_summary_path_for_output(draft_path)),
        "run_id": resolved_run_id,
        "reviewer": reviewer,
        "review_date": resolved_review_date,
        "model": prefiller.model,
        "queue_count": len(queue_rows),
        "draft_count": len(draft_rows),
        "batch_size": batch_size,
        "max_workers": max_workers,
        "decision_distribution": dict(decision_distribution),
        "included_count": decision_distribution.get("纳入", 0),
        "review_needed_count": decision_distribution.get("待复核", 0),
        "excluded_count": decision_distribution.get("剔除", 0),
        "fallback_batch_errors": batch_errors,
    }
    summary_path = _summary_path_for_output(draft_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def run_llm_post_review_prefill(
    *,
    queue_path: Path,
    output_path: Path | None = None,
    run_id: str | None = None,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL,
    model: str = DEFAULT_CHAT_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> dict[str, Any]:
    client = DeepSeekClient.from_env()
    client.base_url = base_url
    client.timeout_seconds = timeout_seconds
    client.max_retries = max_retries
    return generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=output_path,
        run_id=run_id,
        reviewer=reviewer,
        review_date=review_date,
        prefiller=PostReviewBatchPrefiller(client=client, model=model),
        batch_size=batch_size,
        max_workers=max_workers,
        log=print,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate DeepSeek-assisted post_review_v2 prefill JSONL for a single batch file."
    )
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    parser.add_argument("--review-date", default=None)
    parser.add_argument("--base-url", default=DEFAULT_DEEPSEEK_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_llm_post_review_prefill(
        queue_path=args.queue,
        output_path=args.output,
        run_id=args.run_id,
        reviewer=args.reviewer,
        review_date=args.review_date,
        base_url=args.base_url,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_WORKERS",
    "DEFAULT_REVIEWER",
    "PostReviewBatchPrefiller",
    "generate_post_review_prefill_draft",
    "run_llm_post_review_prefill",
]
