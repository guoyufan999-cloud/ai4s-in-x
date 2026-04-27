from __future__ import annotations

from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    format_decision_reason,
    normalize_decision_reason,
    sample_status_to_decision,
)


def is_rescreen_phase(review_phase: str | None) -> bool:
    normalized = str(review_phase or "").strip()
    return normalized in {"rescreen_posts", "rescreen_posts_bootstrap"}


def resolve_identity(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None,
) -> tuple[str, str]:
    record_type = str(row.get("record_type") or "").strip()
    if not record_type:
        if str(row.get("comment_id") or "").strip():
            record_type = "comment"
        elif base_row and str(base_row.get("comment_id") or "").strip():
            record_type = "comment"
        else:
            record_type = "post"

    record_id = str(row.get("record_id") or "").strip()
    if not record_id:
        if record_type == "post":
            record_id = coalesce(row.get("post_id"), (base_row or {}).get("post_id"), "")
        else:
            record_id = coalesce(row.get("comment_id"), (base_row or {}).get("comment_id"), "")

    if not record_id:
        raise ValueError("Unable to resolve record identity for canonical review row")

    is_reply = str(row.get("is_reply") or (base_row or {}).get("is_reply") or "").strip()
    if record_type == "comment" and is_reply in {"1", "true", "True"}:
        record_type = "reply"

    return record_type, record_id


def populate_shared_review_fields(
    canonical: dict[str, Any],
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None,
    review_phase: str,
    record_type: str,
    record_id: str,
) -> str:
    canonical.update(
        {
            "platform": coalesce(row.get("platform"), (base_row or {}).get("platform"), "xiaohongshu"),
            "post_url": coalesce(row.get("post_url"), (base_row or {}).get("post_url"), ""),
            "author_id": coalesce(
                row.get("author_id"),
                (base_row or {}).get("author_id_hashed"),
                (base_row or {}).get("commenter_id_hashed"),
                "",
            ),
            "created_at": coalesce(
                row.get("created_at"),
                (base_row or {}).get("post_date"),
                (base_row or {}).get("comment_date"),
                "",
            ),
            "language": coalesce(row.get("language"), "zh"),
            "task_batch_id": coalesce(row.get("task_batch_id"), (base_row or {}).get("task_batch_id"), ""),
            "coder_version": coalesce(row.get("coder_version"), ""),
            "thread_id": coalesce(row.get("thread_id"), (base_row or {}).get("thread_id"), ""),
            "parent_post_id": coalesce(
                row.get("parent_post_id"),
                (base_row or {}).get("post_id") if record_type != "post" else "",
                "",
            ),
            "reply_to_post_id": coalesce(
                row.get("reply_to_post_id"),
                row.get("parent_comment_id"),
                (base_row or {}).get("parent_comment_id"),
                "",
            ),
            "quoted_post_id": coalesce(row.get("quoted_post_id"), ""),
            "context_text": coalesce(row.get("context_text"), ""),
            "source_text": source_text_for_row(row, base_row=base_row),
            "theme_summary": coalesce(
                row.get("theme_summary"),
                row.get("summary"),
                row.get("帖子主题摘要"),
                (base_row or {}).get("title"),
                "",
            ),
            "target_practice_summary": coalesce(row.get("target_practice_summary"), ""),
            "discursive_mode": coalesce(row.get("discursive_mode"), discursive_mode(row, base_row=base_row)),
            "practice_status": coalesce(row.get("practice_status"), practice_status(row, base_row=base_row)),
            "speaker_position_claimed": coalesce(
                row.get("speaker_position_claimed"),
                speaker_position_claimed(row, base_row=base_row),
            ),
            "record_type": record_type,
            "record_id": record_id,
            "review_phase": review_phase,
            "run_id": str(row.get("run_id") or "").strip(),
            "reviewer": str(row.get("reviewer") or "").strip(),
            "review_date": str(row.get("review_date") or "").strip(),
            "model": str(row.get("model") or "").strip(),
            "review_status": canonical_review_status(row.get("review_status")),
            "actor_type": coalesce(row.get("actor_type"), (base_row or {}).get("actor_type"), ""),
            "qs_broad_subject": coalesce(
                row.get("qs_broad_subject"),
                (base_row or {}).get("qs_broad_subject"),
                "",
            ),
        }
    )

    if record_type == "post":
        canonical["post_id"] = record_id
    else:
        canonical["post_id"] = coalesce(row.get("post_id"), (base_row or {}).get("post_id"), "")

    canonical["context_used"] = context_used(row)
    canonical["context_available"] = "否" if canonical["context_used"] == "none" else "是"

    decision = decision_for_row(row, base_row=base_row)
    canonical["decision"] = decision
    canonical["decision_reason"] = decision_reason_for_row(row, decision=decision, base_row=base_row)
    return decision


def coalesce(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def source_text_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    source_text = coalesce(row.get("source_text"))
    if source_text:
        return source_text
    record_type = str(row.get("record_type") or "").strip()
    if record_type in {"comment", "reply"} or str(row.get("comment_id") or "").strip():
        return coalesce(row.get("comment_text"), (base_row or {}).get("comment_text"))
    title = coalesce(row.get("title"), (base_row or {}).get("title"))
    content = coalesce(row.get("content_text"), (base_row or {}).get("content_text"))
    return "\n".join(part for part in (title, content) if part).strip()


def canonical_review_status(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized in {"reviewed", "revised"}:
        return normalized
    if normalized == "unreviewed":
        return "unreviewed"
    return "reviewed"


def context_used(row: dict[str, Any]) -> str:
    existing = str(row.get("context_used") or "").strip()
    if existing:
        return existing
    if any(str(row.get(key) or "").strip() for key in ("thread_id", "parent_post_id")):
        return "thread"
    if str(row.get("quoted_post_id") or "").strip():
        return "quoted_post"
    if str(row.get("reply_to_post_id") or row.get("parent_comment_id") or "").strip():
        return "reply_chain"
    if str(row.get("context_text") or "").strip():
        return "user_provided_context"
    return "none"


def decision_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    decision = str(row.get("decision") or "").strip()
    if decision:
        return decision
    inclusion = coalesce(row.get("inclusion_decision"), row.get("是否纳入"))
    if inclusion in {"纳入", "剔除"}:
        return inclusion
    sample_status = coalesce(
        row.get("sample_status"),
        row.get("current_sample_status"),
        row.get("historical_sample_status"),
        (base_row or {}).get("sample_status"),
    )
    return sample_status_to_decision(sample_status)


def decision_reason_for_row(
    row: dict[str, Any],
    *,
    decision: str,
    base_row: dict[str, Any] | None,
) -> list[str]:
    existing = normalize_decision_reason(row.get("decision_reason"))
    if existing:
        return existing
    raw_reason = coalesce(
        row.get("reason"),
        row.get("纳入或剔除理由"),
        row.get("ai_review_reason"),
        (base_row or {}).get("decision_reason"),
    )
    if decision == "纳入":
        return format_decision_reason(
            "R12",
            raw_reason or "纳入：可稳定识别为 AI 介入具体科研环节或对应评价对象。",
        )
    if decision == "待复核":
        return format_decision_reason("R11", raw_reason or "可能相关但证据不足，建议复核。")
    return format_decision_reason("R12" if raw_reason else "R2", raw_reason)


def discursive_mode(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = source_text_for_row(row, base_row=base_row)
    if any(token in text for token in ("请问", "求助", "能不能", "可以吗", "？", "?")):
        return "question_help_seeking"
    if any(token in text for token in ("建议", "应该", "必须", "别")):
        return "advice_guidance"
    if any(token in text for token in ("我用", "亲测", "踩坑", "经验")):
        return "experience_share"
    if any(token in text for token in ("风险", "不合适", "学术不端")):
        return "criticism"
    if any(token in text for token in ("规定", "要求", "声明", "政策")):
        return "policy_statement"
    return "unclear"


def practice_status(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = source_text_for_row(row, base_row=base_row)
    if any(token in text for token in ("我用", "用了", "我现在", "亲测", "实测")):
        return "actual_use"
    if any(token in text for token in ("准备", "打算", "想用")):
        return "intended_use"
    if any(token in text for token in ("如果", "假如", "能不能", "可以吗")):
        return "hypothetical_use"
    if any(token in text for token in ("规定", "要求", "声明", "期刊要求")):
        return "policy_or_rule"
    if any(token in text for token in ("听说", "别人", "看到")):
        return "secondhand_report"
    return "unclear"


def speaker_position_claimed(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = source_text_for_row(row, base_row=base_row)
    mapping = {
        "researcher": ("研究者", "科研人员"),
        "graduate_student": ("研究生", "博士生", "硕士"),
        "undergraduate": ("本科生", "本科科研"),
        "PI": ("导师", "PI"),
        "reviewer": ("审稿人",),
        "editor": ("编辑", "期刊编辑"),
        "institution_or_lab": ("实验室", "课题组", "学校"),
        "teacher_or_trainer": ("老师", "训练营", "课程"),
    }
    for code, keywords in mapping.items():
        if any(keyword in text for keyword in keywords):
            return code
    return "unclear"
