from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.settings import INTERIM_DIR, OUTPUTS_DIR

PHASE = "xhs_expansion_candidate_v1"
DEFAULT_CANDIDATE_PATH = OUTPUTS_DIR / "tables" / PHASE / "candidate300.jsonl"
DEFAULT_SUMMARY_PATH = OUTPUTS_DIR / "reports" / PHASE / "candidate300.summary.json"
DEFAULT_QUEUE_PATH = INTERIM_DIR / PHASE / "review_queues" / f"{PHASE}.review_queue.jsonl"
DEFAULT_TEMPLATE_PATH = INTERIM_DIR / PHASE / "reviewed" / f"{PHASE}.review_template.jsonl"
DEFAULT_REPORT_PATH = INTERIM_DIR / PHASE / "review_queue.report.md"

HUMAN_REVIEW_FIELDS = [
    "final_decision",
    "exclusion_reason",
    "research_relevance",
    "workflow_stage",
    "discourse_context",
    "ai_intervention_mode",
    "ai_intervention_intensity",
    "normative_evaluation_signal",
    "boundary_signal",
    "reviewer_note",
]

REVIEW_REQUIRED_FIELDS = list(HUMAN_REVIEW_FIELDS)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = []
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


def _load_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _capture_date(summary: dict[str, Any]) -> str:
    generated_at = str(summary.get("generated_at") or "").strip()
    if generated_at:
        return generated_at[:10]
    return datetime.now(tz=UTC).date().isoformat()


def _preliminary_decision(raw_decision: str) -> str:
    return {
        "纳入": "include",
        "待复核": "review_needed",
        "剔除": "exclude",
    }.get(str(raw_decision or "").strip(), "review_needed")


def _title(row: dict[str, Any]) -> str:
    return str(row.get("theme_summary") or row.get("title") or row.get("record_id") or "").strip()


def _content(row: dict[str, Any]) -> str:
    return str(row.get("source_text") or "").strip()


def _author_hash(row: dict[str, Any]) -> str:
    return str(row.get("author_id") or "").strip()


def _query(row: dict[str, Any]) -> str | None:
    value = str(row.get("query") or row.get("source_query") or "").strip()
    return value or None


def _query_group(row: dict[str, Any]) -> str | None:
    value = str(row.get("query_group") or row.get("source_query_group") or "").strip()
    return value or None


def _query_assignments_from_summary(summary: dict[str, Any]) -> list[dict[str, str]]:
    assignments: list[dict[str, str]] = []
    for item in summary.get("query_stats", []):
        if not isinstance(item, dict):
            continue
        verified_kept = int(item.get("verified_kept") or 0)
        assignments.extend(
            {
                "query": str(item.get("query") or "").strip(),
                "query_group": str(item.get("category") or "").strip(),
                "query_name": str(item.get("query_name") or "").strip(),
            }
            for _ in range(verified_kept)
        )
    return assignments


def backfill_candidate_query_metadata(
    candidate_rows: list[dict[str, Any]],
    *,
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    assignments = _query_assignments_from_summary(summary)
    if not assignments:
        return [dict(row) for row in candidate_rows]
    backfilled_rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_rows):
        updated = dict(row)
        assignment = assignments[index] if index < len(assignments) else {}
        if not _query(updated) and assignment.get("query"):
            updated["query"] = assignment["query"]
            updated["source_query"] = assignment["query"]
        if not _query_group(updated) and assignment.get("query_group"):
            updated["query_group"] = assignment["query_group"]
            updated["source_query_group"] = assignment["query_group"]
        if not updated.get("query_name") and assignment.get("query_name"):
            updated["query_name"] = assignment["query_name"]
        if assignment:
            updated["query_metadata_source"] = (
                "candidate300_summary_sequence_backfill"
                if not row.get("query_group")
                else "candidate_row"
            )
        backfilled_rows.append(updated)
    return backfilled_rows


def _source_method(row: dict[str, Any], summary: dict[str, Any]) -> str:
    return str(
        row.get("source_method")
        or summary.get("provider_used")
        or row.get("source_phase")
        or "unknown"
    )


def _public_access_status(row: dict[str, Any]) -> str:
    if row.get("quality_v5_formal_scope") is True or row.get("formal_result_scope") is True:
        return "invalid_formal_scope_flag"
    return "public_direct_fetch_ok"


def _queue_row(
    row: dict[str, Any],
    *,
    line_number: int,
    capture_date: str,
    summary: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    record_id = str(row.get("record_id") or row.get("post_id") or "").strip()
    candidate_suffix = record_id or f"row_{line_number:04d}"
    preliminary_reason = row.get("decision_reason") or []
    if not isinstance(preliminary_reason, list):
        preliminary_reason = [str(preliminary_reason)]
    queue_row: dict[str, Any] = {
        "candidate_id": f"{PHASE}:{candidate_suffix}",
        "platform": str(row.get("platform") or "xiaohongshu"),
        "post_url": str(row.get("post_url") or ""),
        "note_id": str(row.get("post_id") or row.get("record_id") or ""),
        "record_id": record_id,
        "title": _title(row),
        "content_text": _content(row),
        "author_name_masked": None,
        "author_id_hashed": _author_hash(row) or None,
        "post_date": str(row.get("created_at") or ""),
        "capture_date": capture_date,
        "query": _query(row),
        "query_group": _query_group(row),
        "source_method": _source_method(row, summary),
        "preliminary_decision": _preliminary_decision(str(row.get("decision") or "")),
        "preliminary_reason": preliminary_reason,
        "duplicate_status": "unique_after_sampling_dedup",
        "public_access_status": _public_access_status(row),
        "review_required_fields": REVIEW_REQUIRED_FIELDS,
        "source_candidate_path": str(source_path),
        "source_candidate_line": line_number,
        "source_phase": str(row.get("source_phase") or PHASE),
        "formal_result_scope": False,
        "quality_v5_formal_scope": False,
        "preliminary_decision_note": (
            "Preliminary decision is a rule-based pre-screen suggestion only; "
            "it is not a formal human review result."
        ),
    }
    for field in HUMAN_REVIEW_FIELDS:
        queue_row[field] = None
    return queue_row


def build_review_rows(
    candidate_rows: list[dict[str, Any]],
    *,
    capture_date: str,
    summary: dict[str, Any],
    source_path: Path,
) -> list[dict[str, Any]]:
    return [
        _queue_row(
            row,
            line_number=index,
            capture_date=capture_date,
            summary=summary,
            source_path=source_path,
        )
        for index, row in enumerate(candidate_rows, start=1)
    ]


def _template_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "candidate_id",
        "platform",
        "post_url",
        "note_id",
        "title",
        "content_text",
        "post_date",
        "query",
        "query_group",
        "source_method",
        "preliminary_decision",
        "preliminary_reason",
        "duplicate_status",
        "public_access_status",
        "review_required_fields",
    ]
    template = {key: row.get(key) for key in keys}
    for field in HUMAN_REVIEW_FIELDS:
        template[field] = None
    return template


def _render_report(
    *,
    rows: list[dict[str, Any]],
    queue_path: Path,
    template_path: Path,
    source_path: Path,
    summary: dict[str, Any],
) -> str:
    decision_counts = {
        decision: sum(1 for row in rows if row.get("preliminary_decision") == decision)
        for decision in ("include", "review_needed", "exclude")
    }
    missing_query_count = sum(1 for row in rows if not row.get("query"))
    missing_query_group_count = sum(1 for row in rows if not row.get("query_group"))
    lines = [
        "# xhs_expansion_candidate_v1 review queue report",
        "",
        "本报告说明 `candidate300.jsonl` 到人工 review 队列的转换结果。该队列只用于人工判断候选帖是否纳入研究样本，不会自动写入 `quality_v5` formal baseline，也不会写入正式研究主库。",
        "",
        "## 输出文件",
        "",
        f"- review queue：`{queue_path}`",
        f"- review template：`{template_path}`",
        f"- source candidate：`{source_path}`",
        "",
        "## 队列规模",
        "",
        f"- 候选条目数：`{len(rows)}`",
        f"- preliminary include / review_needed / exclude：`{decision_counts['include']} / {decision_counts['review_needed']} / {decision_counts['exclude']}`",
        f"- candidate300 summary row_count：`{summary.get('row_count', 'unknown')}`",
        "",
        "## 人工审核字段",
        "",
        *[f"- `{field}`" for field in HUMAN_REVIEW_FIELDS],
        "",
        "所有人工字段均保持 `null`。`preliminary_decision` 只是规则预筛建议，不等于正式人工判断。",
        "",
        "## 审核建议",
        "",
        "- `final_decision` 只允许人工填写 `include`、`exclude` 或 `review_needed`。",
        "- 若 `final_decision=exclude`，应填写 `exclusion_reason`，例如非科研场景、广告营销、内容不足、重复样本、不可验证等。",
        "- `research_relevance` 用于人工判断该帖与“AI介入科研活动”主题的相关度。",
        "- `workflow_stage`、`discourse_context`、`ai_intervention_mode`、`ai_intervention_intensity`、`normative_evaluation_signal`、`boundary_signal` 均为人工判断辅助字段，不应由程序自动补齐为正式编码。",
        "- `reviewer_note` 用于记录边界案例、噪声原因或后续复核建议。",
        "",
        "## 已知限制",
        "",
        f"- 缺失逐行 query 的条目：`{missing_query_count}`",
        f"- 缺失逐行 query_group 的条目：`{missing_query_group_count}`",
        "- 当前 `candidate300.jsonl` 是在新增逐行 query 元数据前生成的，因此部分或全部条目的 `query` / `query_group` 可能为空。后续重新采集时，pilot 已支持写入逐行 query 元数据。",
        "- 队列中的 `duplicate_status=unique_after_sampling_dedup` 表示这些条目已通过采样阶段的去重过滤，但仍建议人工 review 时继续检查语义重复和广告噪声。",
    ]
    return "\n".join(lines) + "\n"


def prepare_xhs_expansion_review_queue(
    *,
    candidate_path: Path = DEFAULT_CANDIDATE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    queue_path: Path = DEFAULT_QUEUE_PATH,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    repair_candidate_metadata: bool = False,
) -> tuple[Path, Path, Path]:
    summary = _load_summary(summary_path)
    candidate_rows = backfill_candidate_query_metadata(
        _read_jsonl(candidate_path),
        summary=summary,
    )
    if repair_candidate_metadata:
        _write_jsonl(candidate_path, candidate_rows)
    capture_date = _capture_date(summary)
    rows = build_review_rows(
        candidate_rows,
        capture_date=capture_date,
        summary=summary,
        source_path=candidate_path,
    )
    _write_jsonl(queue_path, rows)
    _write_jsonl(template_path, [_template_row(row) for row in rows])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            rows=rows,
            queue_path=queue_path,
            template_path=template_path,
            source_path=candidate_path,
            summary=summary,
        ),
        encoding="utf-8",
    )
    return queue_path, template_path, report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a human review queue for xhs_expansion_candidate_v1 candidates."
    )
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--repair-candidate-metadata",
        action="store_true",
        help="Rewrite candidate JSONL with query/query_group metadata backfilled from summary.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    queue_path, template_path, report_path = prepare_xhs_expansion_review_queue(
        candidate_path=args.candidate,
        summary_path=args.summary,
        queue_path=args.queue,
        template_path=args.template,
        report_path=args.report,
        repair_candidate_metadata=args.repair_candidate_metadata,
    )
    print(queue_path)
    print(template_path)
    print(report_path)


if __name__ == "__main__":
    main()
