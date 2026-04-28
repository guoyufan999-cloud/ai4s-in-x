from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection.canonical_schema import (
    AMBIGUITY_VALUES,
    CONFIDENCE_VALUES,
    DECISION_REASON_CODES,
    DECISION_VALUES,
    INTERACTION_BASIS_CODE_SET,
    INTERACTION_EVENT_CODE_SET,
    INTERACTION_EVENT_VALUES,
    INTERACTION_OUTCOME_VALUES,
    INTERACTION_ROLE_VALUES,
    MECHANISM_ELIGIBILITY_VALUES,
    ensure_list_of_strings,
    format_decision_reason,
    normalize_claim_units,
    validate_canonical_row,
)
from ai4s_legitimacy.collection.llm_prefill_normalization import (
    DISCURSIVE_MODE_VALUES,
    PRACTICE_STATUS_VALUES,
    QS_SUBJECT_VALUES,
    SPEAKER_POSITION_VALUES,
    _coerce_confidence,
    _confidence_label,
    _normalize_choice,
)


def _empty_workflow_dimension() -> dict[str, list[str]]:
    return {"primary_dimension": [], "secondary_stage": [], "evidence": []}


def _empty_legitimacy_evaluation() -> dict[str, list[str]]:
    return {"direction": [], "basis": [], "evidence": []}


def _empty_boundary_expression() -> dict[str, Any]:
    return {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }


def _empty_interaction_level(context_used: str) -> dict[str, Any]:
    return {
        "event_present": "不适用" if context_used == "none" else "无法判断",
        "interaction_role": "unclear",
        "target_claim_summary": "",
        "event_codes": [],
        "event_basis_codes": [],
        "event_outcome": "",
        "evidence": [],
    }


def _normalize_interaction_codes(values: Any, *, allowed: set[str]) -> list[str]:
    codes: list[str] = []
    for value in ensure_list_of_strings(values):
        if value in allowed and value not in codes:
            codes.append(value)
    return codes


V2_CLAIM_UNIT_FIELDS = (
    "ai_intervention_mode_codes",
    "ai_intervention_intensity_codes",
    "evaluation_tension_codes",
    "formal_norm_reference_codes",
    "boundary_mechanism_codes",
    "boundary_result_codes",
)


def _has_meaningful_claim_units(claim_units: Sequence[dict[str, Any]]) -> bool:
    for unit in claim_units:
        if not isinstance(unit, dict):
            continue
        has_workflow = bool(unit.get("workflow_stage_codes"))
        has_evidence = bool(ensure_list_of_strings(unit.get("evidence")))
        if has_workflow and has_evidence:
            return True
    return False


def _retain_formal_claim_units(claim_units: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    for unit in claim_units:
        if not isinstance(unit, dict):
            continue
        workflow_stage_codes = ensure_list_of_strings(unit.get("workflow_stage_codes"))
        evidence = ensure_list_of_strings(unit.get("evidence"))
        if not workflow_stage_codes or not evidence:
            continue
        retained_unit = {
            "practice_unit": str(unit.get("practice_unit") or "").strip(),
            "workflow_stage_codes": workflow_stage_codes,
            "legitimacy_codes": ensure_list_of_strings(unit.get("legitimacy_codes")) or ["B0"],
            "basis_codes": unit.get("basis_codes") or [],
            "boundary_codes": unit.get("boundary_codes") or [],
            "boundary_mode_codes": unit.get("boundary_mode_codes") or [],
            "evidence": evidence,
        }
        for field_name in V2_CLAIM_UNIT_FIELDS:
            retained_unit[field_name] = ensure_list_of_strings(unit.get(field_name))
        retained.append(retained_unit)
    return retained


def _fallback_item(reason: str) -> dict[str, Any]:
    message = str(reason or "prefill_failed").strip()
    return {
        "decision": "待复核",
        "decision_reason_code": "R11",
        "decision_reason_note": message,
        "theme_summary": "",
        "target_practice_summary": "",
        "discursive_mode": "unclear",
        "practice_status": "unclear",
        "speaker_position_claimed": "unclear",
        "qs_broad_subject": "",
        "evidence_master": [],
        "claim_units": [],
        "interaction_event_present": "",
        "interaction_role": "unclear",
        "interaction_target_claim_summary": "",
        "interaction_event_codes": [],
        "interaction_event_basis_codes": [],
        "interaction_event_outcome": "",
        "interaction_evidence": [],
        "notes_ambiguity": "是",
        "notes_confidence": "低",
        "review_points": [message],
        "mechanism_eligible": "否",
        "mechanism_notes": [],
        "comparison_keys": [],
        "api_confidence": 0.0,
    }


def _normalize_model_item(item: dict[str, Any], *, context_used: str) -> dict[str, Any]:
    decision = str(item.get("decision") or "").strip()
    if decision not in DECISION_VALUES:
        raise ValueError(f"invalid decision: {decision!r}")

    reason_code = str(item.get("decision_reason_code") or "").strip()
    if reason_code not in DECISION_REASON_CODES:
        reason_code = "R11" if decision == "待复核" else "R12"

    api_confidence = _coerce_confidence(item.get("api_confidence"))
    notes_confidence = _normalize_choice(
        item.get("notes_confidence"),
        allowed=CONFIDENCE_VALUES,
        default=_confidence_label(api_confidence),
    )

    claim_units = normalize_claim_units(item.get("claim_units"))
    interaction_event_present = _normalize_choice(
        item.get("interaction_event_present"),
        allowed=INTERACTION_EVENT_VALUES,
        default="不适用" if context_used == "none" else "无法判断",
    )
    if context_used == "none":
        interaction_event_present = "不适用"

    normalized = {
        "decision": decision,
        "decision_reason_code": reason_code,
        "decision_reason_note": str(item.get("decision_reason_note") or "").strip(),
        "theme_summary": str(item.get("theme_summary") or "").strip(),
        "target_practice_summary": str(item.get("target_practice_summary") or "").strip(),
        "discursive_mode": _normalize_choice(
            item.get("discursive_mode"),
            allowed=DISCURSIVE_MODE_VALUES,
            default="unclear",
        ),
        "practice_status": _normalize_choice(
            item.get("practice_status"),
            allowed=PRACTICE_STATUS_VALUES,
            default="unclear",
        ),
        "speaker_position_claimed": _normalize_choice(
            item.get("speaker_position_claimed"),
            allowed=SPEAKER_POSITION_VALUES,
            default="unclear",
        ),
        "qs_broad_subject": _normalize_choice(
            item.get("qs_broad_subject"),
            allowed=QS_SUBJECT_VALUES,
            default="",
        ),
        "evidence_master": ensure_list_of_strings(item.get("evidence_master")),
        "claim_units": claim_units,
        "interaction_event_present": interaction_event_present,
        "interaction_role": _normalize_choice(
            item.get("interaction_role"),
            allowed=INTERACTION_ROLE_VALUES,
            default="unclear",
        ),
        "interaction_target_claim_summary": str(
            item.get("interaction_target_claim_summary") or ""
        ).strip(),
        "interaction_event_codes": _normalize_interaction_codes(
            item.get("interaction_event_codes"),
            allowed=INTERACTION_EVENT_CODE_SET,
        ),
        "interaction_event_basis_codes": _normalize_interaction_codes(
            item.get("interaction_event_basis_codes"),
            allowed=INTERACTION_BASIS_CODE_SET,
        ),
        "interaction_event_outcome": _normalize_choice(
            item.get("interaction_event_outcome"),
            allowed=INTERACTION_OUTCOME_VALUES,
            default="",
        ),
        "interaction_evidence": ensure_list_of_strings(item.get("interaction_evidence")),
        "notes_ambiguity": _normalize_choice(
            item.get("notes_ambiguity"),
            allowed=AMBIGUITY_VALUES,
            default="否",
        ),
        "notes_confidence": notes_confidence,
        "review_points": ensure_list_of_strings(item.get("review_points")),
        "mechanism_eligible": _normalize_choice(
            item.get("mechanism_eligible"),
            allowed=MECHANISM_ELIGIBILITY_VALUES,
            default="否",
        ),
        "mechanism_notes": ensure_list_of_strings(item.get("mechanism_notes")),
        "comparison_keys": ensure_list_of_strings(item.get("comparison_keys")),
        "api_confidence": api_confidence,
    }
    if interaction_event_present != "是":
        normalized["interaction_role"] = "unclear"
        normalized["interaction_target_claim_summary"] = ""
        normalized["interaction_event_codes"] = []
        normalized["interaction_event_basis_codes"] = []
        normalized["interaction_event_outcome"] = ""
        normalized["interaction_evidence"] = []
    return normalized


def _evidence_fallback(row: dict[str, Any]) -> list[str]:
    evidence = ensure_list_of_strings(row.get("evidence_master"))
    if evidence:
        return evidence
    source_text = str(row.get("source_text") or "").strip()
    if source_text:
        return [source_text[:160]]
    theme_summary = str(row.get("theme_summary") or "").strip()
    return [theme_summary] if theme_summary else []


def _interaction_payload(normalized: dict[str, Any], *, context_used: str) -> dict[str, Any]:
    if context_used == "none":
        return _empty_interaction_level("none")
    return {
        "event_present": normalized["interaction_event_present"],
        "interaction_role": normalized["interaction_role"],
        "target_claim_summary": normalized["interaction_target_claim_summary"],
        "event_codes": normalized["interaction_event_codes"],
        "event_basis_codes": normalized["interaction_event_basis_codes"],
        "event_outcome": normalized["interaction_event_outcome"],
        "evidence": normalized["interaction_evidence"],
    }


def _api_assistance_payload(
    *,
    used: bool,
    confidence: Any,
    adoption_note: str,
) -> dict[str, Any]:
    return {
        "used": "是" if used else "否",
        "purpose": ["formal_review_prefill"] if used else [],
        "api_confidence": _confidence_label(confidence) if used else "不可用",
        "adoption_note": str(adoption_note or "").strip(),
    }


def _notes_payload(
    *,
    row: dict[str, Any],
    ambiguity: str,
    confidence: str,
    review_points: Sequence[str],
) -> dict[str, Any]:
    return {
        "multi_label": "否",
        "ambiguity": ambiguity,
        "confidence": confidence,
        "review_points": ensure_list_of_strings(review_points),
        "dedup_group": str(row.get("record_id") or row.get("post_id") or "").strip(),
    }


def _fallback_canonical_row(
    row: dict[str, Any],
    *,
    review_phase: str,
    run_id: str,
    reviewer: str,
    review_date: str,
    model: str,
    reason: str,
) -> dict[str, Any]:
    canonical = canonicalize_review_row(
        dict(row),
        base_row=row,
        review_phase=review_phase,
    )
    message = str(reason or "prefill_failed").strip()
    canonical["run_id"] = run_id
    canonical["review_phase"] = review_phase
    canonical["review_status"] = "unreviewed"
    canonical["reviewer"] = reviewer
    canonical["review_date"] = review_date
    canonical["model"] = model
    canonical["decision"] = "待复核"
    canonical["decision_reason"] = format_decision_reason("R11", message)
    canonical["workflow_dimension"] = _empty_workflow_dimension()
    canonical["legitimacy_evaluation"] = _empty_legitimacy_evaluation()
    canonical["boundary_expression"] = _empty_boundary_expression()
    canonical["interaction_level"] = _empty_interaction_level(
        str(canonical.get("context_used") or "none").strip() or "none"
    )
    canonical["claim_units"] = []
    canonical["evidence_master"] = _evidence_fallback(row)
    canonical["api_assistance"] = _api_assistance_payload(
        used=False,
        confidence=0.0,
        adoption_note=message,
    )
    canonical["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": [],
    }
    canonical["notes"] = _notes_payload(
        row=row,
        ambiguity="是",
        confidence="低",
        review_points=[message],
    )
    return validate_canonical_row(canonical)


def _model_item_to_canonical(
    row: dict[str, Any],
    *,
    review_phase: str,
    normalized_item: dict[str, Any],
    run_id: str,
    reviewer: str,
    review_date: str,
) -> dict[str, Any]:
    canonical = canonicalize_review_row(
        dict(row),
        base_row=row,
        review_phase=review_phase,
    )
    decision = normalized_item["decision"]
    reason_code = normalized_item["decision_reason_code"]
    reason_note = normalized_item["decision_reason_note"]
    claim_units = normalized_item["claim_units"] if decision == "纳入" else []
    review_points = list(normalized_item["review_points"])

    if decision == "纳入":
        claim_units = _retain_formal_claim_units(claim_units)

    if decision == "纳入" and not _has_meaningful_claim_units(claim_units):
        decision = "待复核"
        reason_code = "R11"
        reason_note = "模型未能给出有效的 claim_units（缺少 workflow_stage_codes 或证据），需人工复核。"
        review_points = [*review_points, "模型未能给出有效的 claim_units（缺少 workflow_stage_codes 或证据），需人工复核。"]
        claim_units = []

    if decision == "纳入":
        reason_code = "R12"

    qs_broad_subject = normalized_item["qs_broad_subject"]
    if decision == "纳入" and not qs_broad_subject:
        qs_broad_subject = "uncertain"

    canonical["run_id"] = run_id
    canonical["review_phase"] = review_phase
    canonical["review_status"] = "unreviewed"
    canonical["reviewer"] = reviewer
    canonical["review_date"] = review_date
    canonical["model"] = normalized_item["model"]
    canonical["decision"] = decision
    canonical["decision_reason"] = format_decision_reason(reason_code, reason_note)
    canonical["theme_summary"] = (
        normalized_item["theme_summary"]
        or str(row.get("theme_summary") or "").strip()
        or str(row.get("source_text") or "").strip()[:120]
    )
    canonical["target_practice_summary"] = normalized_item["target_practice_summary"]
    canonical["discursive_mode"] = normalized_item["discursive_mode"]
    canonical["practice_status"] = normalized_item["practice_status"]
    canonical["speaker_position_claimed"] = normalized_item["speaker_position_claimed"]
    canonical["qs_broad_subject"] = qs_broad_subject
    canonical["workflow_dimension"] = _empty_workflow_dimension()
    canonical["legitimacy_evaluation"] = _empty_legitimacy_evaluation()
    canonical["boundary_expression"] = _empty_boundary_expression()
    canonical["interaction_level"] = _interaction_payload(
        normalized_item,
        context_used=str(canonical.get("context_used") or "none").strip() or "none",
    )
    canonical["claim_units"] = claim_units
    canonical["evidence_master"] = normalized_item["evidence_master"] or _evidence_fallback(row)
    canonical["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": normalized_item["mechanism_eligible"],
        "candidate_pattern_notes": normalized_item["mechanism_notes"],
        "comparison_keys": normalized_item["comparison_keys"],
    }
    canonical["api_assistance"] = _api_assistance_payload(
        used=True,
        confidence=normalized_item["api_confidence"],
        adoption_note=reason_note,
    )
    canonical["notes"] = _notes_payload(
        row=row,
        ambiguity=normalized_item["notes_ambiguity"],
        confidence=normalized_item["notes_confidence"],
        review_points=review_points,
    )
    return validate_canonical_row(canonical)
