from __future__ import annotations

import re
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    OLD_BOUNDARY_TO_CONTENT_CODE,
    WORKFLOW_STAGE_LABELS,
    code_label,
)

from ._canonical_review_common import coalesce, context_used, source_text_for_row

WORKFLOW_STAGE_BY_LABEL = {label: code for code, label in WORKFLOW_STAGE_LABELS.items()}


def workflow_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    codes = ensure_codes(
        row.get("workflow_dimension", {}).get("secondary_stage")
        or row.get("workflow_codes")
        or row.get("workflow_stage_codes")
    )
    if codes:
        return codes
    workflow_stage = coalesce(row.get("workflow_stage"), (base_row or {}).get("workflow_stage"))
    if workflow_stage in WORKFLOW_STAGE_BY_LABEL:
        return [WORKFLOW_STAGE_BY_LABEL[workflow_stage]]
    if workflow_stage in WORKFLOW_STAGE_LABELS:
        return [workflow_stage]
    return []


def legitimacy_codes_for_row(
    row: dict[str, Any],
    *,
    decision: str,
    base_row: dict[str, Any] | None,
) -> list[str]:
    codes = ensure_codes(
        row.get("legitimacy_evaluation", {}).get("direction") or row.get("legitimacy_codes")
    )
    if codes:
        return codes
    primary = coalesce(
        row.get("primary_legitimacy_code"),
        (base_row or {}).get("primary_legitimacy_code"),
    )
    if primary:
        return [primary]
    return ["B0"] if decision != "剔除" else []


def basis_codes_for_row(row: dict[str, Any], *, base_row: dict[str, Any] | None) -> list[str]:
    codes = ensure_codes(
        row.get("legitimacy_evaluation", {}).get("basis") or row.get("evaluation_codes")
    )
    if codes:
        return codes
    basis = coalesce(row.get("legitimacy_basis"), (base_row or {}).get("legitimacy_basis"))
    if re.match(r"^C\d+$", basis):
        return [basis]
    return []


def boundary_content_codes_for_row(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None,
) -> list[str]:
    del base_row
    codes = ensure_codes(
        row.get("boundary_expression", {}).get("boundary_content_codes") or row.get("boundary_codes")
    )
    return [OLD_BOUNDARY_TO_CONTENT_CODE.get(code, code) for code in codes]


def boundary_mode_codes_for_row(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None,
) -> list[str]:
    del base_row
    return ensure_codes(row.get("boundary_expression", {}).get("boundary_expression_mode_codes"))


def interaction_level_for_row(row: dict[str, Any]) -> dict[str, Any]:
    existing = row.get("interaction_level") or {}
    event_present = str(existing.get("event_present") or "").strip()
    if not event_present:
        event_present = "不适用" if context_used(row) == "none" else "无法判断"
    return {
        "event_present": event_present,
        "interaction_role": coalesce(existing.get("interaction_role"), "unclear"),
        "target_claim_summary": coalesce(existing.get("target_claim_summary"), ""),
        "event_codes": ensure_codes(existing.get("event_codes")),
        "event_basis_codes": ensure_codes(existing.get("event_basis_codes")),
        "event_outcome": coalesce(existing.get("event_outcome"), ""),
        "evidence": ensure_strings(existing.get("evidence")),
    }


def api_assistance_for_row(row: dict[str, Any]) -> dict[str, Any]:
    existing = row.get("api_assistance") or {}
    if existing:
        return {
            "used": coalesce(existing.get("used"), "否"),
            "purpose": ensure_strings(existing.get("purpose")),
            "api_confidence": coalesce(existing.get("api_confidence"), "无"),
            "adoption_note": coalesce(existing.get("adoption_note"), ""),
        }
    model = coalesce(row.get("model"), row.get("stage1_model"), row.get("stage2_model"))
    ai_confidence = coalesce(row.get("ai_confidence"), row.get("stage1_ai_confidence"))
    ai_reason = coalesce(row.get("ai_review_reason"))
    if model or ai_confidence or ai_reason:
        return {
            "used": "是",
            "purpose": ["candidate_screening"],
            "api_confidence": confidence_label(ai_confidence),
            "adoption_note": coalesce(ai_reason, f"Assisted by {model}" if model else ""),
        }
    return {
        "used": "否",
        "purpose": [],
        "api_confidence": "无",
        "adoption_note": "",
    }


def notes_for_row(row: dict[str, Any], *, decision: str, record_id: str) -> dict[str, Any]:
    review_points = ensure_strings(
        row.get("notes", {}).get("review_points") if isinstance(row.get("notes"), dict) else None
    )
    review_points.extend(
        item
        for item in (
            coalesce(row.get("followup_check")),
            coalesce(row.get("ambiguity_note")),
            (
                coalesce(row.get("备注", {}).get("建议后续复核点"))
                if isinstance(row.get("备注"), dict)
                else ""
            ),
        )
        if item
    )
    ambiguity = coalesce(
        row.get("notes", {}).get("ambiguity") if isinstance(row.get("notes"), dict) else "",
        "是" if decision == "待复核" or review_points else "否",
    )
    multi_label = coalesce(
        row.get("notes", {}).get("multi_label") if isinstance(row.get("notes"), dict) else "",
        "否",
    )
    raw_confidence = coalesce(
        row.get("notes", {}).get("confidence") if isinstance(row.get("notes"), dict) else "",
        row.get("confidence"),
        "",
    )
    return {
        "multi_label": multi_label,
        "ambiguity": ambiguity,
        "confidence": confidence_label(raw_confidence),
        "review_points": list(dict.fromkeys(point for point in review_points if point)),
        "dedup_group": coalesce(
            row.get("notes", {}).get("dedup_group") if isinstance(row.get("notes"), dict) else "",
            row.get("post_id"),
            record_id,
        ),
    }


def ensure_codes(value: Any) -> list[str]:
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


def ensure_strings(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    iterable = value if isinstance(value, list) else [value]
    items: list[str] = []
    for item in iterable:
        text = str(item or "").strip()
        if text and text not in items:
            items.append(text)
    return items


def evidence_for_codes(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None,
    codes: list[str],
) -> list[str]:
    if not codes:
        return []
    text = source_text_for_row(row, base_row=base_row)
    if not text:
        return []
    sentences = split_sentences(text)
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


def bootstrap_claim_units(
    source_text: str,
    *,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_content_codes: list[str],
    boundary_mode_codes: list[str],
) -> list[dict[str, Any]]:
    if not (
        workflow_codes
        or legitimacy_codes
        or basis_codes
        or boundary_content_codes
        or boundary_mode_codes
    ):
        return []
    evidence = split_sentences(source_text)[:1] or [source_text[:220]]
    unit_codes = workflow_codes or [""]
    return [
        {
            "practice_unit": code_label(workflow_code) if workflow_code else "AI科研相关实践单元",
            "workflow_stage_codes": [workflow_code] if workflow_code else [],
            "legitimacy_codes": legitimacy_codes,
            "basis_codes": [{"code": code, "evidence": evidence[0]} for code in basis_codes],
            "boundary_codes": [{"code": code, "evidence": evidence[0]} for code in boundary_content_codes],
            "boundary_mode_codes": [
                {"code": code, "evidence": evidence[0]} for code in boundary_mode_codes
            ],
            "evidence": evidence,
        }
        for workflow_code in unit_codes
    ]


def evidence_master_for_row(row: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for claim_unit in row.get("claim_units") or []:
        for item in claim_unit.get("evidence") or []:
            text = str(item or "").strip()
            if text and text not in evidence:
                evidence.append(text)
    if evidence:
        return evidence
    return ensure_strings(
        row.get("workflow_dimension", {}).get("evidence")
        + row.get("legitimacy_evaluation", {}).get("evidence")
        + row.get("boundary_expression", {}).get("evidence")
    )


def mechanism_memo_for_row(row: dict[str, Any]) -> dict[str, Any]:
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


def confidence_label(value: Any) -> str:
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


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?；;])|\n+", text or "") if part.strip()]
