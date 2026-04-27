from __future__ import annotations

import re
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    OLD_BOUNDARY_TO_CONTENT_CODE,
    WORKFLOW_STAGE_LABELS,
    apply_claim_units_to_row,
    build_empty_canonical_row,
    code_label,
    format_decision_reason,
    normalize_canonical_row,
    normalize_decision_reason,
    sample_status_to_decision,
)

WORKFLOW_STAGE_BY_LABEL = {label: code for code, label in WORKFLOW_STAGE_LABELS.items()}


def canonicalize_review_row(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None = None,
    review_phase: str | None = None,
) -> dict[str, Any]:
    resolved_review_phase = review_phase or str(row.get("review_phase") or "").strip()
    record_type, record_id = _identity(row, base_row=base_row)
    canonical = build_empty_canonical_row(record_type, record_id)
    canonical.update(
        {
            "platform": _coalesce(row.get("platform"), (base_row or {}).get("platform"), "xiaohongshu"),
            "post_url": _coalesce(row.get("post_url"), (base_row or {}).get("post_url"), ""),
            "author_id": _coalesce(
                row.get("author_id"),
                (base_row or {}).get("author_id_hashed"),
                (base_row or {}).get("commenter_id_hashed"),
                "",
            ),
            "created_at": _coalesce(
                row.get("created_at"),
                (base_row or {}).get("post_date"),
                (base_row or {}).get("comment_date"),
                "",
            ),
            "language": _coalesce(row.get("language"), "zh"),
            "task_batch_id": _coalesce(row.get("task_batch_id"), (base_row or {}).get("task_batch_id"), ""),
            "coder_version": _coalesce(row.get("coder_version"), ""),
            "thread_id": _coalesce(row.get("thread_id"), (base_row or {}).get("thread_id"), ""),
            "parent_post_id": _coalesce(
                row.get("parent_post_id"),
                (base_row or {}).get("post_id") if record_type != "post" else "",
                "",
            ),
            "reply_to_post_id": _coalesce(
                row.get("reply_to_post_id"),
                row.get("parent_comment_id"),
                (base_row or {}).get("parent_comment_id"),
                "",
            ),
            "quoted_post_id": _coalesce(row.get("quoted_post_id"), ""),
            "context_text": _coalesce(row.get("context_text"), ""),
            "source_text": _source_text_for_row(row, base_row=base_row),
            "theme_summary": _coalesce(
                row.get("theme_summary"),
                row.get("summary"),
                row.get("帖子主题摘要"),
                (base_row or {}).get("title"),
                "",
            ),
            "target_practice_summary": _coalesce(row.get("target_practice_summary"), ""),
            "discursive_mode": _coalesce(row.get("discursive_mode"), _discursive_mode(row, base_row=base_row)),
            "practice_status": _coalesce(row.get("practice_status"), _practice_status(row, base_row=base_row)),
            "speaker_position_claimed": _coalesce(
                row.get("speaker_position_claimed"),
                _speaker_position_claimed(row, base_row=base_row),
            ),
            "record_type": record_type,
            "record_id": record_id,
            "review_phase": resolved_review_phase,
            "run_id": str(row.get("run_id") or "").strip(),
            "reviewer": str(row.get("reviewer") or "").strip(),
            "review_date": str(row.get("review_date") or "").strip(),
            "model": str(row.get("model") or "").strip(),
            "review_status": _canonical_review_status(row.get("review_status")),
            "actor_type": _coalesce(row.get("actor_type"), (base_row or {}).get("actor_type"), ""),
            "qs_broad_subject": _coalesce(
                row.get("qs_broad_subject"),
                (base_row or {}).get("qs_broad_subject"),
                "",
            ),
        }
    )

    if record_type == "post":
        canonical["post_id"] = record_id
    else:
        canonical["post_id"] = _coalesce(row.get("post_id"), (base_row or {}).get("post_id"), "")

    canonical["context_used"] = _context_used(row)
    canonical["context_available"] = "否" if canonical["context_used"] == "none" else "是"

    decision = _decision_for_row(row, base_row=base_row)
    canonical["decision"] = decision
    canonical["decision_reason"] = _decision_reason_for_row(row, decision=decision, base_row=base_row)

    if _is_rescreen_phase(resolved_review_phase):
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
            "event_present": "不适用" if canonical["context_used"] == "none" else "无法判断",
            "interaction_role": "unclear",
            "target_claim_summary": "",
            "event_codes": [],
            "event_basis_codes": [],
            "event_outcome": "",
            "evidence": [],
        }
        canonical["api_assistance"] = _api_assistance_for_row(row)
        canonical["notes"] = _notes_for_row(
            row,
            decision=decision,
            record_id=record_id,
        )
        canonical["claim_units"] = []
        canonical["evidence_master"] = _evidence_master_for_row(canonical)
        canonical["mechanism_memo"] = _mechanism_memo_for_row(canonical)
        return normalize_canonical_row(canonical)

    workflow_codes = _workflow_codes_for_row(row, base_row=base_row)
    legitimacy_codes = _legitimacy_codes_for_row(row, decision=decision, base_row=base_row)
    basis_codes = _basis_codes_for_row(row, base_row=base_row)
    boundary_content_codes = _boundary_content_codes_for_row(row, base_row=base_row)
    boundary_mode_codes = _boundary_mode_codes_for_row(row, base_row=base_row)

    canonical["workflow_dimension"] = {
        "primary_dimension": [],
        "secondary_stage": workflow_codes,
        "evidence": _evidence_for_codes(row, base_row=base_row, codes=workflow_codes),
    }
    canonical["legitimacy_evaluation"] = {
        "direction": legitimacy_codes,
        "basis": basis_codes,
        "evidence": _evidence_for_codes(
            row,
            base_row=base_row,
            codes=legitimacy_codes + basis_codes,
        ),
    }
    canonical["boundary_expression"] = {
        "present": "是" if (boundary_content_codes or boundary_mode_codes) else "否",
        "boundary_content_codes": boundary_content_codes,
        "boundary_expression_mode_codes": boundary_mode_codes,
        "evidence": _evidence_for_codes(
            row,
            base_row=base_row,
            codes=boundary_content_codes + boundary_mode_codes,
        ),
    }
    canonical["interaction_level"] = _interaction_level_for_row(row)
    canonical["api_assistance"] = _api_assistance_for_row(row)
    canonical["notes"] = _notes_for_row(
        row,
        decision=decision,
        record_id=record_id,
    )

    claim_units = row.get("claim_units")
    if claim_units:
        canonical["claim_units"] = claim_units
    elif decision == "纳入":
        canonical["claim_units"] = _bootstrap_claim_units(
            canonical["source_text"],
            workflow_codes=workflow_codes,
            legitimacy_codes=legitimacy_codes,
            basis_codes=basis_codes,
            boundary_content_codes=boundary_content_codes,
            boundary_mode_codes=boundary_mode_codes,
        )
    else:
        canonical["claim_units"] = []

    canonical["evidence_master"] = _evidence_master_for_row(canonical)
    canonical["mechanism_memo"] = _mechanism_memo_for_row(canonical)
    return normalize_canonical_row(apply_claim_units_to_row(canonical))


def _is_rescreen_phase(review_phase: str | None) -> bool:
    normalized = str(review_phase or "").strip()
    return normalized in {"rescreen_posts", "rescreen_posts_bootstrap"}


def _identity(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> tuple[str, str]:
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
            record_id = _coalesce(row.get("post_id"), (base_row or {}).get("post_id"), "")
        else:
            record_id = _coalesce(
                row.get("comment_id"),
                (base_row or {}).get("comment_id"),
                "",
            )
    if not record_id:
        raise ValueError("Unable to resolve record identity for canonical review row")
    if record_type == "comment" and str(row.get("is_reply") or (base_row or {}).get("is_reply") or "").strip() in {"1", "true", "True"}:
        record_type = "reply"
    return record_type, record_id


def _coalesce(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _source_text_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    source_text = _coalesce(row.get("source_text"))
    if source_text:
        return source_text
    if str(row.get("record_type") or "").strip() in {"comment", "reply"} or str(row.get("comment_id") or "").strip():
        return _coalesce(row.get("comment_text"), (base_row or {}).get("comment_text"))
    title = _coalesce(row.get("title"), (base_row or {}).get("title"))
    content = _coalesce(row.get("content_text"), (base_row or {}).get("content_text"))
    return "\n".join(part for part in (title, content) if part).strip()


def _canonical_review_status(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized in {"reviewed", "revised"}:
        return normalized
    if normalized == "unreviewed":
        return "unreviewed"
    return "reviewed"


def _context_used(row: dict[str, Any]) -> str:
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


def _decision_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    decision = str(row.get("decision") or "").strip()
    if decision:
        return decision
    inclusion = _coalesce(row.get("inclusion_decision"), row.get("是否纳入"))
    if inclusion in {"纳入", "剔除"}:
        return inclusion
    sample_status = _coalesce(
        row.get("sample_status"),
        row.get("current_sample_status"),
        row.get("historical_sample_status"),
        (base_row or {}).get("sample_status"),
    )
    return sample_status_to_decision(sample_status)


def _decision_reason_for_row(
    row: dict[str, Any],
    *,
    decision: str,
    base_row: dict[str, Any] | None,
) -> list[str]:
    existing = normalize_decision_reason(row.get("decision_reason"))
    if existing:
        return existing
    raw_reason = _coalesce(
        row.get("reason"),
        row.get("纳入或剔除理由"),
        row.get("ai_review_reason"),
        (base_row or {}).get("decision_reason"),
    )
    if decision == "纳入":
        return format_decision_reason("R12", raw_reason or "纳入：可稳定识别为 AI 介入具体科研环节或对应评价对象。")
    if decision == "待复核":
        return format_decision_reason("R11", raw_reason or "可能相关但证据不足，建议复核。")
    return format_decision_reason("R12" if raw_reason else "R2", raw_reason)


def _workflow_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    codes = _ensure_codes(
        row.get("workflow_dimension", {}).get("secondary_stage")
        or row.get("workflow_codes")
        or row.get("workflow_stage_codes"),
    )
    if codes:
        return codes
    workflow_stage = _coalesce(row.get("workflow_stage"), (base_row or {}).get("workflow_stage"))
    if workflow_stage in WORKFLOW_STAGE_BY_LABEL:
        return [WORKFLOW_STAGE_BY_LABEL[workflow_stage]]
    if workflow_stage in WORKFLOW_STAGE_LABELS:
        return [workflow_stage]
    return []


def _legitimacy_codes_for_row(
    row: dict[str, Any],
    *,
    decision: str,
    base_row: dict[str, Any] | None,
) -> list[str]:
    codes = _ensure_codes(
        row.get("legitimacy_evaluation", {}).get("direction")
        or row.get("legitimacy_codes"),
    )
    if codes:
        return codes
    primary = _coalesce(
        row.get("primary_legitimacy_code"),
        (base_row or {}).get("primary_legitimacy_code"),
    )
    if primary:
        return [primary]
    return ["B0"] if decision != "剔除" else []


def _basis_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    codes = _ensure_codes(
        row.get("legitimacy_evaluation", {}).get("basis")
        or row.get("evaluation_codes"),
    )
    if codes:
        return codes
    basis = _coalesce(row.get("legitimacy_basis"), (base_row or {}).get("legitimacy_basis"))
    if re.match(r"^C\d+$", basis):
        return [basis]
    return []


def _boundary_content_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    codes = _ensure_codes(
        row.get("boundary_expression", {}).get("boundary_content_codes")
        or row.get("boundary_codes"),
    )
    return [OLD_BOUNDARY_TO_CONTENT_CODE.get(code, code) for code in codes]


def _boundary_mode_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    return _ensure_codes(
        row.get("boundary_expression", {}).get("boundary_expression_mode_codes"),
    )


def _interaction_level_for_row(row: dict[str, Any]) -> dict[str, Any]:
    existing = row.get("interaction_level") or {}
    event_present = str(existing.get("event_present") or "").strip()
    if not event_present:
        event_present = "不适用" if _context_used(row) == "none" else "无法判断"
    return {
        "event_present": event_present,
        "interaction_role": _coalesce(existing.get("interaction_role"), "unclear"),
        "target_claim_summary": _coalesce(existing.get("target_claim_summary"), ""),
        "event_codes": _ensure_codes(existing.get("event_codes")),
        "event_basis_codes": _ensure_codes(existing.get("event_basis_codes")),
        "event_outcome": _coalesce(existing.get("event_outcome"), ""),
        "evidence": _ensure_strings(existing.get("evidence")),
    }


def _api_assistance_for_row(row: dict[str, Any]) -> dict[str, Any]:
    existing = row.get("api_assistance") or {}
    if existing:
        return {
            "used": _coalesce(existing.get("used"), "否"),
            "purpose": _ensure_strings(existing.get("purpose")),
            "api_confidence": _coalesce(existing.get("api_confidence"), "无"),
            "adoption_note": _coalesce(existing.get("adoption_note"), ""),
        }
    model = _coalesce(row.get("model"), row.get("stage1_model"), row.get("stage2_model"))
    ai_confidence = _coalesce(row.get("ai_confidence"), row.get("stage1_ai_confidence"))
    ai_reason = _coalesce(row.get("ai_review_reason"))
    if model or ai_confidence or ai_reason:
        return {
            "used": "是",
            "purpose": ["candidate_screening"],
            "api_confidence": _confidence_label(ai_confidence),
            "adoption_note": _coalesce(ai_reason, f"Assisted by {model}" if model else ""),
        }
    return {
        "used": "否",
        "purpose": [],
        "api_confidence": "无",
        "adoption_note": "",
    }


def _notes_for_row(row: dict[str, Any], *, decision: str, record_id: str) -> dict[str, Any]:
    review_points = _ensure_strings(
        row.get("notes", {}).get("review_points")
        if isinstance(row.get("notes"), dict)
        else None
    )
    review_points.extend(
        item
        for item in (
            _coalesce(row.get("followup_check")),
            _coalesce(row.get("ambiguity_note")),
            _coalesce(row.get("备注", {}).get("建议后续复核点")) if isinstance(row.get("备注"), dict) else "",
        )
        if item
    )
    ambiguity = _coalesce(
        row.get("notes", {}).get("ambiguity") if isinstance(row.get("notes"), dict) else "",
        "是" if decision == "待复核" or review_points else "否",
    )
    multi_label = _coalesce(
        row.get("notes", {}).get("multi_label") if isinstance(row.get("notes"), dict) else "",
        "否",
    )
    raw_confidence = _coalesce(
        row.get("notes", {}).get("confidence") if isinstance(row.get("notes"), dict) else "",
        row.get("confidence"),
        "",
    )
    return {
        "multi_label": multi_label,
        "ambiguity": ambiguity,
        "confidence": _confidence_label(raw_confidence),
        "review_points": list(dict.fromkeys(point for point in review_points if point)),
        "dedup_group": _coalesce(
            row.get("notes", {}).get("dedup_group") if isinstance(row.get("notes"), dict) else "",
            row.get("post_id"),
            record_id,
        ),
    }


def _discursive_mode(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = _source_text_for_row(row, base_row=base_row)
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


def _practice_status(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = _source_text_for_row(row, base_row=base_row)
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


def _speaker_position_claimed(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> str:
    text = _source_text_for_row(row, base_row=base_row)
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


def _ensure_codes(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    iterable = value if isinstance(value, list) else [value]
    codes: list[str] = []
    for item in iterable:
        if isinstance(item, dict):
            code = str(item.get("code") or "").strip()
        else:
            code = str(item or "").strip()
        if code and code not in codes:
            codes.append(code)
    return codes


def _ensure_strings(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    iterable = value if isinstance(value, list) else [value]
    items: list[str] = []
    for item in iterable:
        text = str(item or "").strip()
        if text and text not in items:
            items.append(text)
    return items


def _evidence_for_codes(row: dict[str, Any], *, base_row: dict[str, Any] | None, codes: list[str]) -> list[str]:
    if not codes:
        return []
    text = _source_text_for_row(row, base_row=base_row)
    if not text:
        return []
    sentences = _split_sentences(text)
    if not sentences:
        return [text[:220]]
    evidence: list[str] = []
    for code in codes:
        label = code_label(code)
        for sentence in sentences:
            if code.lower() in sentence.lower() or label in sentence:
                evidence.append(sentence)
                break
    if not evidence:
        evidence.append(sentences[0])
    return list(dict.fromkeys(evidence))


def _bootstrap_claim_units(
    source_text: str,
    *,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_content_codes: list[str],
    boundary_mode_codes: list[str],
) -> list[dict[str, Any]]:
    if not workflow_codes and not legitimacy_codes and not basis_codes and not boundary_content_codes and not boundary_mode_codes:
        return []
    evidence = _split_sentences(source_text)[:1] or [source_text[:220]]
    unit_codes = workflow_codes or [""]
    claim_units: list[dict[str, Any]] = []
    for workflow_code in unit_codes:
        claim_units.append(
            {
                "practice_unit": code_label(workflow_code) if workflow_code else "AI科研相关实践单元",
                "workflow_stage_codes": [workflow_code] if workflow_code else [],
                "legitimacy_codes": legitimacy_codes,
                "basis_codes": [{"code": code, "evidence": evidence[0]} for code in basis_codes],
                "boundary_codes": [{"code": code, "evidence": evidence[0]} for code in boundary_content_codes],
                "boundary_mode_codes": [{"code": code, "evidence": evidence[0]} for code in boundary_mode_codes],
                "evidence": evidence,
            }
        )
    return claim_units


def _evidence_master_for_row(row: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for claim_unit in row.get("claim_units") or []:
        for item in claim_unit.get("evidence") or []:
            text = str(item or "").strip()
            if text and text not in evidence:
                evidence.append(text)
    if evidence:
        return evidence
    return _ensure_strings(
        row.get("workflow_dimension", {}).get("evidence")
        + row.get("legitimacy_evaluation", {}).get("evidence")
        + row.get("boundary_expression", {}).get("evidence")
    )


def _mechanism_memo_for_row(row: dict[str, Any]) -> dict[str, Any]:
    boundary_present = row.get("boundary_expression", {}).get("present") == "是"
    if row["decision"] == "纳入" and boundary_present:
        return {
            "eligible_for_mechanism_analysis": "待定",
            "candidate_pattern_notes": ["单帖边界表达可用于后续比较，但不能直接视为稳定机制。"],
            "comparison_keys": list(
                dict.fromkeys(
                    row.get("workflow_dimension", {}).get("secondary_stage", [])
                    + row.get("legitimacy_evaluation", {}).get("direction", [])
                    + row.get("boundary_expression", {}).get("boundary_content_codes", [])
                )
            ),
        }
    return {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": row.get("workflow_dimension", {}).get("secondary_stage", []),
    }


def _confidence_label(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"高", "中", "低"}:
        return text
    try:
        score = float(text)
    except (TypeError, ValueError):
        return "低" if not text else "中"
    if score >= 0.85:
        return "高"
    if score >= 0.6:
        return "中"
    return "低"


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?；;])|\n+", text or "") if part.strip()]
