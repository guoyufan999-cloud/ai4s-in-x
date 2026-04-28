from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from ai4s_legitimacy.collection import llm_rescreen_batching as _batching
from ai4s_legitimacy.collection import llm_rescreen_outputs as _outputs
from ai4s_legitimacy.collection import llm_rescreen_pipeline as _pipeline
from ai4s_legitimacy.collection import llm_rescreen_prompts as _prompts
from ai4s_legitimacy.collection import llm_rescreen_rules as _rules
from ai4s_legitimacy.collection._jsonl import load_jsonl as _load_jsonl
from ai4s_legitimacy.collection.deepseek_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REASONER_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    DeepSeekClient,
)
from ai4s_legitimacy.collection.review_queue import export_review_queue
from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)

BatchClassifier = _batching.BatchClassifier
REVIEW_PHASE = _outputs.REVIEW_PHASE
_apply_guardrails = _rules._apply_guardrails
_stage1_system_prompt = _prompts._stage1_system_prompt
_stage2_system_prompt = _prompts._stage2_system_prompt

DEFAULT_STAGE1_BATCH_SIZE = 8
DEFAULT_STAGE2_BATCH_SIZE = 4
DEFAULT_MAX_WORKERS = 6
DEFAULT_FALSE_SAMPLE_SIZE = 100
DEFAULT_REVIEWER = "guoyufan"
DEFAULT_RUN_ID = "qv5_rescreen_deepseek_full_v1"
MAX_STAGE2_COVERAGE_RATIO = 0.7


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
) -> dict[str, object]:
    if false_sample_size <= 0:
        raise ValueError("false_sample_size must be a positive integer")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if merge_only:
        return _pipeline._merge_shard_outputs(
            run_dir=run_dir,
            run_id=run_id,
            shard_count=shard_count,
        )

    shard_dir = _batching._shard_dir(run_dir, shard_index=shard_index, shard_count=shard_count)
    shard_dir.mkdir(parents=True, exist_ok=True)
    summary_path = shard_dir / f"{_batching._shard_name(shard_index, shard_count)}.summary.json"
    if resume:
        existing = _batching._load_summary_if_complete(summary_path)
        if existing is not None:
            return existing

    queue_rows = _load_jsonl(queue_path)
    _batching._validate_queue_rows(queue_rows)
    shard_rows, queue_start, queue_end = _batching._select_shard_rows(
        queue_rows,
        shard_index=shard_index,
        shard_count=shard_count,
    )

    return _pipeline._generate_shard_draft(
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
) -> dict[str, object]:
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


__all__ = [
    "DEFAULT_FALSE_SAMPLE_SIZE",
    "DEFAULT_MAX_WORKERS",
    "DEFAULT_REVIEWER",
    "DEFAULT_RUN_ID",
    "DEFAULT_STAGE1_BATCH_SIZE",
    "DEFAULT_STAGE2_BATCH_SIZE",
    "MAX_STAGE2_COVERAGE_RATIO",
    "REVIEW_PHASE",
    "BatchClassifier",
    "_apply_guardrails",
    "_stage1_system_prompt",
    "_stage2_system_prompt",
    "generate_llm_rescreen_draft",
    "run_llm_rescreen",
]


if __name__ == "__main__":
    main()
