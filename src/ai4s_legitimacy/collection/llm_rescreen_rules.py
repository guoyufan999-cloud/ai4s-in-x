from __future__ import annotations

import json
from typing import Any

from ai4s_legitimacy.collection._jsonl import trim_text as _trim_text


CONFIDENCE_THRESHOLD = 0.85

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
