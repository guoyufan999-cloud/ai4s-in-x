from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from ai4s_legitimacy.collection._jsonl import write_jsonl as _write_jsonl
from ai4s_legitimacy.collection.llm_rescreen_rules import (
    _coerce_confidence,
    _is_low_information,
    _is_positive,
    _normalize_current_actor,
    _normalize_current_status,
)

REVIEW_PHASE = "rescreen_posts"


def _status_change_key(row: dict[str, Any]) -> str:
    return (
        f"{_normalize_current_status(row.get('current_sample_status'))}"
        f"->{row['sample_status']}"
    )


def _actor_change_key(row: dict[str, Any]) -> str:
    return f"{_normalize_current_actor(row.get('current_actor_type'))}->{row['actor_type']}"


def _priority_true_or_review_needed(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized = [row for row in rows if _is_positive(row["sample_status"])]
    prioritized.sort(
        key=lambda row: (
            0
            if row["sample_status"] != row.get("current_sample_status", "")
            or row["actor_type"] != row.get("current_actor_type", "")
            else 1,
            0 if row["sample_status"] == "true" else 1,
            row.get("ai_confidence", 0.0),
            row.get("queue_position", 0),
        )
    )
    return prioritized


def _priority_reverted_positive_to_false(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized = [
        row
        for row in rows
        if _is_positive(_normalize_current_status(row.get("current_sample_status")))
        and row["sample_status"] == "false"
    ]
    prioritized.sort(
        key=lambda row: (
            row.get("ai_confidence", 0.0),
            row.get("queue_position", 0),
        )
    )
    return prioritized


def _priority_promoted_to_true_or_review_needed(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized = [
        row
        for row in rows
        if row.get("current_sample_status") == "false" and _is_positive(row["sample_status"])
    ]
    prioritized.sort(
        key=lambda row: (
            0 if row["sample_status"] == "true" else 1,
            row.get("ai_confidence", 0.0),
            row.get("queue_position", 0),
        )
    )
    return prioritized


def _build_false_sample(rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    false_rows = [row for row in rows if row["sample_status"] == "false"]
    false_rows.sort(
        key=lambda row: (
            0 if row["current_sample_status"] != row["sample_status"] else 1,
            0 if _is_low_information(row) else 1,
            row.get("ai_confidence", 0.0),
            str(row.get("post_date") or ""),
            str(row.get("post_id") or row.get("record_id") or ""),
        )
    )
    return false_rows[:limit]


def _build_spot_checks(
    rows: list[dict[str, Any]],
    *,
    false_sample_size: int,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "true": [row for row in rows if row["sample_status"] == "true"],
        "review_needed": [row for row in rows if row["sample_status"] == "review_needed"],
        "vendor": [
            row for row in rows if row["actor_type"] == "tool_vendor_or_promotional"
        ],
        "false_sample": _build_false_sample(rows, limit=false_sample_size),
    }


def _write_markdown(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _top_query_patterns(rows: Sequence[dict[str, Any]], *, limit: int = 10) -> list[tuple[str, int]]:
    counter = Counter()
    for row in rows:
        query = str(row.get("keyword_query") or "").strip() or "<empty>"
        counter[query] += 1
    return counter.most_common(limit)


def _example_titles(rows: Sequence[dict[str, Any]], *, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for row in rows:
        title = str(row.get("title") or "").strip()
        if title and title not in seen:
            seen.append(title)
        if len(seen) >= limit:
            break
    return seen


def _build_summary(
    *,
    queue_rows: Sequence[dict[str, Any]],
    full_rows: Sequence[dict[str, Any]],
    delta_rows: Sequence[dict[str, Any]],
    reasoner_reviewed_count: int,
    output_paths: dict[str, str],
    shard_index: int | None = None,
    shard_count: int | None = None,
    queue_start: int | None = None,
    queue_end: int | None = None,
) -> dict[str, Any]:
    low_information_count = sum(1 for row in queue_rows if _is_low_information(row))
    sample_status_distribution = Counter(row["sample_status"] for row in full_rows)
    actor_distribution = Counter(row["actor_type"] for row in full_rows)
    status_changes = Counter(_status_change_key(row) for row in delta_rows)
    actor_changes = Counter(_actor_change_key(row) for row in delta_rows)
    summary = {
        "status": "ok",
        "review_phase": REVIEW_PHASE,
        "queue_count": len(queue_rows),
        "full_draft_count": len(full_rows),
        "delta_count": len(delta_rows),
        "reasoner_reviewed_count": reasoner_reviewed_count,
        "reasoner_coverage_ratio": round(reasoner_reviewed_count / len(queue_rows), 4)
        if queue_rows
        else 0.0,
        "low_information_count": low_information_count,
        "sample_status_distribution": dict(sample_status_distribution),
        "actor_distribution": dict(actor_distribution),
        "status_changes": dict(status_changes),
        "actor_changes": dict(actor_changes),
        "outputs": output_paths,
    }
    if shard_index is not None:
        summary["shard_index"] = shard_index
    if shard_count is not None:
        summary["shard_count"] = shard_count
    if queue_start is not None:
        summary["queue_start"] = queue_start
    if queue_end is not None:
        summary["queue_end"] = queue_end
    return summary


def _canonical_confidence_label(value: Any) -> str:
    numeric = _coerce_confidence(value)
    if numeric >= 0.85:
        return "高"
    if numeric >= 0.6:
        return "中"
    return "低"


def _write_run_outputs(
    *,
    run_dir: Path,
    file_prefix: str,
    full_rows: Sequence[dict[str, Any]],
    delta_rows: Sequence[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, str]:
    output_paths = {
        "full_draft": str(_write_jsonl(run_dir / f"{file_prefix}.full_draft.jsonl", full_rows)),
        "delta_only": str(_write_jsonl(run_dir / f"{file_prefix}.delta_only.jsonl", delta_rows)),
        "priority_true_or_review_needed": str(
            _write_jsonl(
                run_dir / f"{file_prefix}.priority.true_or_review_needed.jsonl",
                _priority_true_or_review_needed(full_rows),
            )
        ),
        "priority_reverted_positive_to_false": str(
            _write_jsonl(
                run_dir / f"{file_prefix}.priority.reverted_positive_to_false.jsonl",
                _priority_reverted_positive_to_false(delta_rows),
            )
        ),
    }
    summary["outputs"] = output_paths
    summary_path = run_dir / f"{file_prefix}.summary.json"
    summary["outputs"]["summary"] = str(summary_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary["outputs"]


def _build_analysis_markdown(
    *,
    run_id: str,
    full_rows: Sequence[dict[str, Any]],
    delta_rows: Sequence[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    reverted_positive = _priority_reverted_positive_to_false(delta_rows)
    promoted_positive = _priority_promoted_to_true_or_review_needed(delta_rows)
    final_positive = _priority_true_or_review_needed(full_rows)
    lines = [
        f"# {run_id} DeepSeek 复筛解读",
        "",
        "## 全量分布",
        f"- sample_status: `{json.dumps(summary['sample_status_distribution'], ensure_ascii=False)}`",
        f"- actor_type: `{json.dumps(summary['actor_distribution'], ensure_ascii=False)}`",
        f"- delta_count: `{summary['delta_count']}`",
        f"- reasoner_coverage_ratio: `{summary['reasoner_coverage_ratio']}`",
        "",
        "## 变更方向",
        f"- sample_status changes: `{json.dumps(summary['status_changes'], ensure_ascii=False)}`",
        f"- actor_type changes: `{json.dumps(summary['actor_changes'], ensure_ascii=False)}`",
        "",
        "## 最终 true / review_needed 模式",
    ]
    for query, count in _top_query_patterns(final_positive):
        lines.append(f"- `{query}`: {count}")
    lines.extend(["", "Representative titles:"])
    for title in _example_titles(final_positive):
        lines.append(f"- {title}")
    lines.extend(["", "## 当前 true/review_needed -> false 的收紧类型"])
    for query, count in _top_query_patterns(reverted_positive):
        lines.append(f"- `{query}`: {count}")
    lines.extend(["", "Representative titles:"])
    for title in _example_titles(reverted_positive):
        lines.append(f"- {title}")
    lines.extend(["", "## 当前 false -> true/review_needed 的补回类型"])
    for query, count in _top_query_patterns(promoted_positive):
        lines.append(f"- `{query}`: {count}")
    lines.extend(["", "Representative titles:"])
    for title in _example_titles(promoted_positive):
        lines.append(f"- {title}")
    return "\n".join(lines) + "\n"
