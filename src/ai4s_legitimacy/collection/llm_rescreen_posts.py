from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection._jsonl import (
    load_jsonl as _load_jsonl,
    trim_text as _trim_text,
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
from ai4s_legitimacy.collection.review_queue import export_review_queue
from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_STAGING_DB_PATH,
    REBASELINE_SUGGESTIONS_DIR,
)
from ai4s_legitimacy.config.research_baseline import screening_prompt_context


DEFAULT_STAGE1_BATCH_SIZE = 8
DEFAULT_STAGE2_BATCH_SIZE = 4
DEFAULT_MAX_WORKERS = 6
DEFAULT_FALSE_SAMPLE_SIZE = 100
DEFAULT_REVIEWER = "guoyufan"
DEFAULT_RUN_ID = "qv5_rescreen_deepseek_full_v1"
CONFIDENCE_THRESHOLD = 0.85
MAX_STAGE2_COVERAGE_RATIO = 0.7

REVIEW_PHASE = "rescreen_posts"
SAMPLE_STATUS_VALUES = {"true", "false", "review_needed"}
ACTOR_TYPE_VALUES = {
    "graduate_student",
    "faculty",
    "tool_vendor_or_promotional",
    "institution",
    "lab_or_group",
    "undergraduate_research",
    "uncertain",
}
LOW_INFORMATION_STATUSES = {
    "failed",
    "paused",
    "skipped",
    "skipped_interruption",
    "skipped_timeout",
}
RESEARCH_TERMS = (
    "科研",
    "研究",
    "论文",
    "文献",
    "综述",
    "投稿",
    "开题",
    "组会",
    "实验",
    "学术",
    "课题",
    "导师",
    "research",
    "paper",
    "literature",
    "lab",
    "academic",
    "peer review",
    "审稿",
    "评审",
    "返修",
    "研究方法",
    "科研训练",
)
WORKFLOW_TERMS = (
    "文献",
    "综述",
    "阅读",
    "投稿",
    "返修",
    "审稿",
    "评审",
    "写作",
    "写论文",
    "论文初稿",
    "润色",
    "选题",
    "开题",
    "组会",
    "实验",
    "数据分析",
    "统计",
    "代码",
    "r代码",
    "python",
    "作图",
    "机制图",
    "科研绘图",
    "爬虫",
    "复现",
    "项目管理",
    "组会纪要",
    "协作",
    "知识库",
    "伦理",
    "合规",
    "方法学习",
    "写作训练",
    "科研入门",
    "学术适应",
    "效率提升",
)
LEGITIMACY_TERMS = (
    "瞎编",
    "幻觉",
    "学术不端",
    "越界",
    "合理",
    "正当",
    "能不能",
    "可以吗",
    "合规",
    "检测",
    "伦理",
    "原创性",
    "责任",
    "替代",
    "辅助",
    "披露",
)
VENDOR_NEWS_TERMS = (
    "发布",
    "上线",
    "接入",
    "平台",
    "免费",
    "推荐",
    "黑科技",
    "神器",
    "一秒",
    "开源",
    "支持",
    "集成",
    "新功能",
)
FIRST_PERSON_TERMS = (
    "我",
    "自己",
    "亲测",
    "实测",
    "用了",
    "用它",
    "经验",
    "踩坑",
    "分享",
)
AI_TERMS = (
    "ai",
    "人工智能",
    "大模型",
    "llm",
    "gpt",
    "chatgpt",
    "claude",
    "deepseek",
    "copilot",
    "gemini",
    "智能体",
)


def _normalize_current_status(value: Any) -> str:
    sample_status = str(value or "").strip()
    return sample_status if sample_status in SAMPLE_STATUS_VALUES else "review_needed"


def _normalize_current_actor(value: Any) -> str:
    actor_type = str(value or "").strip()
    return actor_type if actor_type in ACTOR_TYPE_VALUES else "uncertain"


def _coerce_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def _normalize_risk_flags(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            return _normalize_risk_flags(parsed)
        return [stripped]
    raise ValueError(f"Unsupported risk_flags payload: {value!r}")


def _normalize_model_item(
    item: dict[str, Any],
    *,
    fallback_actor_type: str,
) -> dict[str, Any]:
    sample_status = str(item.get("sample_status", "")).strip()
    actor_type = str(item.get("actor_type", "")).strip()
    if sample_status not in SAMPLE_STATUS_VALUES:
        raise ValueError(f"Unsupported sample_status from model: {sample_status!r}")
    if actor_type not in ACTOR_TYPE_VALUES:
        actor_type = fallback_actor_type
    return {
        "sample_status": sample_status,
        "actor_type": actor_type,
        "ai_review_reason": _trim_text(item.get("ai_review_reason"), max_chars=500),
        "ai_confidence": _coerce_confidence(item.get("ai_confidence")),
        "risk_flags": _normalize_risk_flags(item.get("risk_flags")),
    }


def _fallback_result(
    row: dict[str, Any],
    *,
    reason: str,
    model: str,
) -> dict[str, Any]:
    return {
        "sample_status": "review_needed",
        "actor_type": _normalize_current_actor(row.get("actor_type")),
        "ai_review_reason": _trim_text(reason, max_chars=500),
        "ai_confidence": 0.0,
        "risk_flags": ["api_error"],
        "model": model,
    }


def _serialize_queue_row_for_model(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_id": str(row.get("post_id") or row.get("record_id") or ""),
        "post_date": str(row.get("post_date") or ""),
        "legacy_crawl_status": str(row.get("legacy_crawl_status") or ""),
        "keyword_query": _trim_text(row.get("keyword_query"), max_chars=200),
        "title": _trim_text(row.get("title"), max_chars=300),
        "content_text": _trim_text(row.get("content_text"), max_chars=1800),
    }


def _has_research_ai_signal(row: dict[str, Any]) -> bool:
    haystack = " ".join(
        (
            str(row.get("title") or ""),
            str(row.get("keyword_query") or ""),
            str(row.get("content_text") or ""),
        )
    ).lower()
    has_research = any(term.lower() in haystack for term in RESEARCH_TERMS)
    has_ai = any(term.lower() in haystack for term in AI_TERMS)
    return has_research and has_ai


def _has_strong_low_info_relevance(row: dict[str, Any]) -> bool:
    haystack = " ".join((str(row.get("title") or ""), str(row.get("keyword_query") or ""))).lower()
    has_ai = any(term.lower() in haystack for term in AI_TERMS)
    has_workflow = any(term.lower() in haystack for term in WORKFLOW_TERMS)
    has_legitimacy = any(term.lower() in haystack for term in LEGITIMACY_TERMS)
    return has_ai and (has_workflow or has_legitimacy)


def _looks_like_vendor_news(row: dict[str, Any]) -> bool:
    haystack = " ".join((str(row.get("title") or ""), str(row.get("keyword_query") or ""))).lower()
    return any(term.lower() in haystack for term in VENDOR_NEWS_TERMS)


def _has_first_person_practice_signal(row: dict[str, Any]) -> bool:
    haystack = " ".join(
        (
            str(row.get("title") or ""),
            str(row.get("keyword_query") or ""),
            str(row.get("content_text") or ""),
        )
    ).lower()
    return any(term.lower() in haystack for term in FIRST_PERSON_TERMS)


def _is_low_information(row: dict[str, Any]) -> bool:
    status = str(row.get("legacy_crawl_status") or "").strip().lower()
    normalized_status = status if status in LOW_INFORMATION_STATUSES else (
        "skipped" if status.startswith("skipped") else status
    )
    return normalized_status in LOW_INFORMATION_STATUSES and not str(
        row.get("content_text") or ""
    ).strip()


def _is_positive(sample_status: str) -> bool:
    return sample_status in {"true", "review_needed"}


def _is_low_information_vendor_false(row: dict[str, Any], stage1_result: dict[str, Any]) -> bool:
    return (
        stage1_result["sample_status"] == "false"
        and _is_low_information(row)
        and _looks_like_vendor_news(row)
        and not _has_first_person_practice_signal(row)
    )


def _is_high_signal_low_confidence_false(row: dict[str, Any], stage1_result: dict[str, Any]) -> bool:
    if stage1_result["sample_status"] != "false":
        return False
    if stage1_result["ai_confidence"] >= CONFIDENCE_THRESHOLD:
        return False
    if not _has_strong_low_info_relevance(row) and not _has_research_ai_signal(row):
        return False
    if _is_low_information_vendor_false(row, stage1_result):
        return False
    return True


def _needs_reasoner_review(
    row: dict[str, Any],
    stage1_result: dict[str, Any],
) -> bool:
    current_status = _normalize_current_status(row.get("sample_status"))
    if _is_positive(stage1_result["sample_status"]):
        return True
    if stage1_result["sample_status"] == "false" and current_status == "true":
        return True
    if _is_high_signal_low_confidence_false(row, stage1_result):
        return True
    return False


def _apply_guardrails(row: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    risk_flags = set(normalized.get("risk_flags", []))

    if _is_low_information(row):
        risk_flags.add("low_information")
        if not _has_strong_low_info_relevance(row):
            normalized["sample_status"] = "false"
            normalized["actor_type"] = (
                "tool_vendor_or_promotional"
                if _looks_like_vendor_news(row)
                else _normalize_current_actor(row.get("actor_type"))
            )
            normalized["ai_review_reason"] = (
                "低信息帖子且标题/query 不足以明确指向科研 AI 工作流或合法性讨论"
            )
            normalized["ai_confidence"] = max(normalized.get("ai_confidence", 0.0), 0.9)
        elif _looks_like_vendor_news(row) and not _has_first_person_practice_signal(row):
            normalized["sample_status"] = "false"
            normalized["actor_type"] = "tool_vendor_or_promotional"
            normalized["ai_review_reason"] = "低信息产品/发布型帖子，缺少研究者实际使用证据"
            normalized["ai_confidence"] = max(normalized.get("ai_confidence", 0.0), 0.88)
            risk_flags.add("vendor_like")

    normalized["risk_flags"] = sorted(risk_flags)
    return normalized


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


def _stage1_system_prompt() -> str:
    return """
你在做 AI4S 研究样本边界重筛。你必须只输出 JSON。

任务：判断小红书帖子是否属于“研究者使用 AI 做科研”或“围绕这种使用的合法性/边界讨论”。

后续所有判断统一服务于以下研究主线：
{baseline_context}

sample_status 规则：
- true：帖子明确讨论 AI/大模型在科研工作流中的具体使用，或明确讨论这类使用是否正当、是否越界。
- false：与研究目标无关，包括泛 AI 新闻、普通效率工具推荐、一般编程/数据工具宣传、泛研究生日常、课程/作业/求职内容、AI 作为研究对象而不是研究工具。
- review_needed：信息不足或冲突，不能安全判 true/false。

actor_type 只能从这些值中选择：
graduate_student, faculty, tool_vendor_or_promotional, institution, lab_or_group, undergraduate_research, uncertain

关键边界：
- legacy_crawl_status 是 failed / paused / skipped* 且 content_text 为空时，默认 false。
- 只有标题或 query 已经足够明确指向科研 AI 工作流或合法性讨论时，低信息帖子才允许 true 或 review_needed。
- tool_vendor_or_promotional 只表示主体角色，不等于 false；如果内容本身相关，仍可判 true。
- 低信息的产品发布、平台接入、功能更新、工具推荐、模型新闻，默认 false，不要仅因为“科研”或“AI”关键词就判 true。
- 只有标题/query 已经明确呈现研究者在做具体科研工作流，或明确讨论这种用法的正当性/边界时，低信息帖子才允许 true 或 review_needed。

必须返回一个 JSON object，顶层键为 items。每个 item 都必须包含：
batch_item_id, sample_status, actor_type, ai_review_reason, ai_confidence, risk_flags
ai_confidence 取 0 到 1 之间的小数。risk_flags 用字符串数组。
""".format(baseline_context=screening_prompt_context()).strip()


def _stage2_system_prompt() -> str:
    return """
你在做 AI4S 研究样本边界复核。你必须只输出 JSON。

任务：对高风险边界样本做更谨慎的第二轮判断。

后续所有判断统一服务于以下研究主线：
{baseline_context}

优先级：
- 如果证据明确，给出 true 或 false。
- 如果信息不足、标题党、只有 query 命中、或 stage1 与当前结果冲突且证据不充分，优先给 review_needed。
- 对低信息的产品发布、平台接入、模型新闻、工具推荐帖子，除非标题本身已呈现研究者的具体使用或合法性争论，否则判 false。

仍然只允许以下 sample_status：
true, false, review_needed

actor_type 只能从这些值中选择：
graduate_student, faculty, tool_vendor_or_promotional, institution, lab_or_group, undergraduate_research, uncertain

不要输出推理链原文，只输出简洁结论。必须返回一个 JSON object，顶层键为 items。
每个 item 必须包含：
batch_item_id, sample_status, actor_type, ai_review_reason, ai_confidence, risk_flags
""".format(baseline_context=screening_prompt_context()).strip()


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
    for row, stage1 in zip(queue_rows, stage1_results):
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
    for row, stage1 in zip(queue_rows, stage1_results):
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
        for row, result in zip(stage2_input_rows, stage2_results)
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
