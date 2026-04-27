from __future__ import annotations

import copy
import re
from typing import Any, Iterable

from .canonical_claim_units import _normalize_code_entries, normalize_claim_units
from .canonical_constants import (
    AMBIGUITY_VALUES,
    API_ASSISTANCE_VALUES,
    API_CONFIDENCE_VALUES,
    BOUNDARY_CONTENT_CODE_SET,
    BOUNDARY_MODE_CODE_SET,
    BOUNDARY_PRESENT_VALUES,
    CONFIDENCE_VALUES,
    CONTEXT_AVAILABLE_VALUES,
    CONTEXT_USED_VALUES,
    DECISION_REASON_CODES,
    DECISION_VALUES,
    EVALUATION_CODE_SET,
    INTERACTION_BASIS_CODE_SET,
    INTERACTION_EVENT_CODE_SET,
    INTERACTION_EVENT_VALUES,
    INTERACTION_OUTCOME_VALUES,
    INTERACTION_ROLE_VALUES,
    LEGITIMACY_CODE_SET,
    MECHANISM_ELIGIBILITY_VALUES,
    MULTI_LABEL_VALUES,
    RECORD_ID_FIELD,
    RECORD_TYPE_VALUES,
    REVIEW_STATUS_VALUES,
    WORKFLOW_CODE_SET,
    WORKFLOW_DIMENSION_LABELS,
)
from .canonical_utils import (
    ensure_list_of_strings,
    normalize_decision_reason,
    primary_dimensions_from_workflow,
)


def _empty_workflow_dimension() -> dict[str, Any]:
    return {
        "primary_dimension": [],
        "secondary_stage": [],
        "evidence": [],
    }


def _empty_legitimacy_evaluation() -> dict[str, Any]:
    return {
        "direction": [],
        "basis": [],
        "evidence": [],
    }


def _empty_boundary_expression() -> dict[str, Any]:
    return {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }


def _empty_interaction_level() -> dict[str, Any]:
    return {
        "event_present": "不适用",
        "interaction_role": "unclear",
        "target_claim_summary": "",
        "event_codes": [],
        "event_basis_codes": [],
        "event_outcome": "",
        "evidence": [],
    }


def _empty_mechanism_memo() -> dict[str, Any]:
    return {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": [],
    }


def _empty_api_assistance() -> dict[str, Any]:
    return {
        "used": "否",
        "purpose": [],
        "api_confidence": "无",
        "adoption_note": "",
    }


def _empty_notes(record_id: str) -> dict[str, Any]:
    return {
        "multi_label": "否",
        "ambiguity": "否",
        "confidence": "中",
        "review_points": [],
        "dedup_group": record_id,
    }


def build_empty_canonical_row(
    record_type: str,
    record_id: str,
    *,
    platform: str = "xiaohongshu",
) -> dict[str, Any]:
    if record_type not in RECORD_TYPE_VALUES:
        raise ValueError(f"Unsupported record_type: {record_type}")
    id_field = RECORD_ID_FIELD[record_type]
    row = {
        "post_id": "",
        "task_batch_id": "",
        "coder_version": "",
        "platform": platform,
        "post_url": "",
        "author_id": "",
        "created_at": "",
        "language": "",
        "thread_id": "",
        "parent_post_id": "",
        "reply_to_post_id": "",
        "quoted_post_id": "",
        "context_available": "否",
        "context_used": "none",
        "source_text": "",
        "context_text": "",
        "decision": "待复核",
        "decision_reason": [],
        "theme_summary": "",
        "target_practice_summary": "",
        "evidence_master": [],
        "discursive_mode": "",
        "practice_status": "",
        "speaker_position_claimed": "",
        "workflow_dimension": _empty_workflow_dimension(),
        "legitimacy_evaluation": _empty_legitimacy_evaluation(),
        "boundary_expression": _empty_boundary_expression(),
        "interaction_level": _empty_interaction_level(),
        "claim_units": [],
        "mechanism_memo": _empty_mechanism_memo(),
        "api_assistance": _empty_api_assistance(),
        "notes": _empty_notes(record_id),
        "review_status": "unreviewed",
        "record_type": record_type,
        "record_id": record_id,
    }
    row[id_field] = record_id
    return row


def canonical_record_identity(row: dict[str, Any]) -> tuple[str, str]:
    record_type = str(row.get("record_type") or "").strip()
    if record_type not in RECORD_TYPE_VALUES:
        if str(row.get("comment_id") or "").strip():
            record_type = "comment"
        else:
            record_type = "post"
    record_id = str(row.get("record_id") or "").strip()
    if not record_id:
        record_id = str(row.get(RECORD_ID_FIELD[record_type]) or "").strip()
    if not record_id:
        raise ValueError("Canonical row missing record_id")
    return record_type, record_id


def apply_claim_units_to_row(row: dict[str, Any]) -> dict[str, Any]:
    claim_units = normalize_claim_units(row.get("claim_units"))
    if not claim_units:
        row["claim_units"] = []
        return row

    workflow_codes: list[str] = []
    legitimacy_codes: list[str] = []
    basis_codes: list[str] = []
    boundary_content_codes: list[str] = []
    boundary_mode_codes: list[str] = []
    workflow_evidence: list[str] = []
    legitimacy_evidence: list[str] = []
    boundary_evidence: list[str] = []
    evidence_master: list[str] = []
    practice_units: list[str] = []

    for unit in claim_units:
        practice_unit = str(unit.get("practice_unit") or "").strip()
        if practice_unit:
            practice_units.append(practice_unit)

        for code in unit["workflow_stage_codes"]:
            if code not in workflow_codes:
                workflow_codes.append(code)
        for code in unit["legitimacy_codes"]:
            if code not in legitimacy_codes:
                legitimacy_codes.append(code)

        for entry in unit["basis_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in basis_codes:
                basis_codes.append(code)
            if evidence and evidence not in legitimacy_evidence:
                legitimacy_evidence.append(evidence)

        for entry in unit["boundary_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in boundary_content_codes:
                boundary_content_codes.append(code)
            if evidence and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

        for entry in unit["boundary_mode_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in boundary_mode_codes:
                boundary_mode_codes.append(code)
            if evidence and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

        for evidence in unit["evidence"]:
            if evidence not in evidence_master:
                evidence_master.append(evidence)
            if unit["workflow_stage_codes"] and evidence not in workflow_evidence:
                workflow_evidence.append(evidence)
            if unit["legitimacy_codes"] and evidence not in legitimacy_evidence:
                legitimacy_evidence.append(evidence)
            if (unit["boundary_codes"] or unit["boundary_mode_codes"]) and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

    row["claim_units"] = claim_units
    row["evidence_master"] = evidence_master
    row["target_practice_summary"] = row.get("target_practice_summary") or "; ".join(practice_units[:3])
    workflow_dimension = row.get("workflow_dimension") or _empty_workflow_dimension()
    workflow_dimension["secondary_stage"] = workflow_codes
    workflow_dimension["primary_dimension"] = primary_dimensions_from_workflow(workflow_codes)
    workflow_dimension["evidence"] = workflow_evidence
    row["workflow_dimension"] = workflow_dimension

    legitimacy_evaluation = row.get("legitimacy_evaluation") or _empty_legitimacy_evaluation()
    legitimacy_evaluation["direction"] = legitimacy_codes
    legitimacy_evaluation["basis"] = basis_codes
    legitimacy_evaluation["evidence"] = legitimacy_evidence
    row["legitimacy_evaluation"] = legitimacy_evaluation

    boundary_expression = row.get("boundary_expression") or _empty_boundary_expression()
    boundary_expression["present"] = "是" if (boundary_content_codes or boundary_mode_codes) else "否"
    boundary_expression["boundary_content_codes"] = boundary_content_codes
    boundary_expression["boundary_expression_mode_codes"] = boundary_mode_codes
    boundary_expression["evidence"] = boundary_evidence
    row["boundary_expression"] = boundary_expression

    notes = row.get("notes") or _empty_notes(str(row.get("record_id") or ""))
    notes["multi_label"] = "是" if len(workflow_codes) > 1 or len(claim_units) > 1 else "否"
    row["notes"] = notes
    return row


def normalize_canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = build_empty_canonical_row(*canonical_record_identity(row))
    for key, value in row.items():
        if value is not None:
            normalized[key] = copy.deepcopy(value)

    record_type, record_id = canonical_record_identity(normalized)
    normalized["record_type"] = record_type
    normalized["record_id"] = record_id
    normalized[RECORD_ID_FIELD[record_type]] = record_id
    normalized["decision_reason"] = normalize_decision_reason(normalized.get("decision_reason"))
    normalized["evidence_master"] = ensure_list_of_strings(normalized.get("evidence_master"))
    normalized["workflow_dimension"] = {
        "primary_dimension": _normalize_code_entries(
            normalized.get("workflow_dimension", {}).get("primary_dimension"),
            allowed_codes=set(WORKFLOW_DIMENSION_LABELS),
        ),
        "secondary_stage": _normalize_code_entries(
            normalized.get("workflow_dimension", {}).get("secondary_stage"),
            allowed_codes=WORKFLOW_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("workflow_dimension", {}).get("evidence"),
        ),
    }
    if not normalized["workflow_dimension"]["primary_dimension"]:
        normalized["workflow_dimension"]["primary_dimension"] = primary_dimensions_from_workflow(
            normalized["workflow_dimension"]["secondary_stage"]
        )

    normalized["legitimacy_evaluation"] = {
        "direction": _normalize_code_entries(
            normalized.get("legitimacy_evaluation", {}).get("direction"),
            allowed_codes=LEGITIMACY_CODE_SET,
        ),
        "basis": _normalize_code_entries(
            normalized.get("legitimacy_evaluation", {}).get("basis"),
            allowed_codes=EVALUATION_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("legitimacy_evaluation", {}).get("evidence"),
        ),
    }

    normalized["boundary_expression"] = {
        "present": str(
            normalized.get("boundary_expression", {}).get("present") or "否"
        ).strip()
        or "否",
        "boundary_content_codes": _normalize_code_entries(
            normalized.get("boundary_expression", {}).get("boundary_content_codes"),
            allowed_codes=BOUNDARY_CONTENT_CODE_SET,
        ),
        "boundary_expression_mode_codes": _normalize_code_entries(
            normalized.get("boundary_expression", {}).get("boundary_expression_mode_codes"),
            allowed_codes=BOUNDARY_MODE_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("boundary_expression", {}).get("evidence"),
        ),
    }

    normalized["interaction_level"] = {
        "event_present": str(
            normalized.get("interaction_level", {}).get("event_present") or "不适用"
        ).strip()
        or "不适用",
        "interaction_role": str(
            normalized.get("interaction_level", {}).get("interaction_role") or "unclear"
        ).strip()
        or "unclear",
        "target_claim_summary": str(
            normalized.get("interaction_level", {}).get("target_claim_summary") or ""
        ).strip(),
        "event_codes": _normalize_code_entries(
            normalized.get("interaction_level", {}).get("event_codes"),
            allowed_codes=INTERACTION_EVENT_CODE_SET,
        ),
        "event_basis_codes": _normalize_code_entries(
            normalized.get("interaction_level", {}).get("event_basis_codes"),
            allowed_codes=INTERACTION_BASIS_CODE_SET,
        ),
        "event_outcome": str(
            normalized.get("interaction_level", {}).get("event_outcome") or ""
        ).strip(),
        "evidence": ensure_list_of_strings(
            normalized.get("interaction_level", {}).get("evidence"),
        ),
    }

    normalized["claim_units"] = normalize_claim_units(normalized.get("claim_units"))

    normalized["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": str(
            normalized.get("mechanism_memo", {}).get("eligible_for_mechanism_analysis") or "否"
        ).strip()
        or "否",
        "candidate_pattern_notes": ensure_list_of_strings(
            normalized.get("mechanism_memo", {}).get("candidate_pattern_notes"),
        ),
        "comparison_keys": ensure_list_of_strings(
            normalized.get("mechanism_memo", {}).get("comparison_keys"),
        ),
    }

    normalized["api_assistance"] = {
        "used": str(normalized.get("api_assistance", {}).get("used") or "否").strip() or "否",
        "purpose": ensure_list_of_strings(normalized.get("api_assistance", {}).get("purpose")),
        "api_confidence": str(
            normalized.get("api_assistance", {}).get("api_confidence") or "无"
        ).strip()
        or "无",
        "adoption_note": str(
            normalized.get("api_assistance", {}).get("adoption_note") or ""
        ).strip(),
    }

    normalized["notes"] = {
        "multi_label": str(normalized.get("notes", {}).get("multi_label") or "否").strip() or "否",
        "ambiguity": str(normalized.get("notes", {}).get("ambiguity") or "否").strip() or "否",
        "confidence": str(normalized.get("notes", {}).get("confidence") or "中").strip() or "中",
        "review_points": ensure_list_of_strings(normalized.get("notes", {}).get("review_points")),
        "dedup_group": str(normalized.get("notes", {}).get("dedup_group") or record_id).strip()
        or record_id,
    }

    normalized["review_status"] = str(normalized.get("review_status") or "unreviewed").strip() or "unreviewed"
    normalized["context_used"] = str(normalized.get("context_used") or "none").strip() or "none"
    normalized["context_available"] = "否" if normalized["context_used"] == "none" else "是"
    if normalized["context_used"] == "none":
        normalized["interaction_level"]["event_present"] = "不适用"
    normalized = apply_claim_units_to_row(normalized)
    if normalized["boundary_expression"]["present"] == "否" and (
        normalized["boundary_expression"]["boundary_content_codes"]
        or normalized["boundary_expression"]["boundary_expression_mode_codes"]
    ):
        normalized["boundary_expression"]["present"] = "是"
    return normalized


def _require_allowed(value: str, *, allowed: Iterable[str], field_name: str) -> None:
    if value not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {expected}. Got {value!r}")


def _require_evidence_if_codes(codes: list[str], evidence: list[str], *, field_name: str) -> None:
    if codes and not evidence:
        raise ValueError(f"{field_name} has codes but no evidence")


def validate_canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_canonical_row(row)
    _require_allowed(normalized["record_type"], allowed=RECORD_TYPE_VALUES, field_name="record_type")
    _require_allowed(normalized["decision"], allowed=DECISION_VALUES, field_name="decision")
    _require_allowed(
        normalized["context_available"],
        allowed=CONTEXT_AVAILABLE_VALUES,
        field_name="context_available",
    )
    _require_allowed(normalized["context_used"], allowed=CONTEXT_USED_VALUES, field_name="context_used")
    _require_allowed(
        normalized["boundary_expression"]["present"],
        allowed=BOUNDARY_PRESENT_VALUES,
        field_name="boundary_expression.present",
    )
    _require_allowed(
        normalized["interaction_level"]["event_present"],
        allowed=INTERACTION_EVENT_VALUES,
        field_name="interaction_level.event_present",
    )
    _require_allowed(
        normalized["interaction_level"]["interaction_role"],
        allowed=INTERACTION_ROLE_VALUES,
        field_name="interaction_level.interaction_role",
    )
    _require_allowed(
        normalized["notes"]["multi_label"],
        allowed=MULTI_LABEL_VALUES,
        field_name="notes.multi_label",
    )
    _require_allowed(
        normalized["notes"]["ambiguity"],
        allowed=AMBIGUITY_VALUES,
        field_name="notes.ambiguity",
    )
    _require_allowed(
        normalized["notes"]["confidence"],
        allowed=CONFIDENCE_VALUES,
        field_name="notes.confidence",
    )
    _require_allowed(
        normalized["api_assistance"]["used"],
        allowed=API_ASSISTANCE_VALUES,
        field_name="api_assistance.used",
    )
    _require_allowed(
        normalized["api_assistance"]["api_confidence"],
        allowed=API_CONFIDENCE_VALUES,
        field_name="api_assistance.api_confidence",
    )
    _require_allowed(
        normalized["mechanism_memo"]["eligible_for_mechanism_analysis"],
        allowed=MECHANISM_ELIGIBILITY_VALUES,
        field_name="mechanism_memo.eligible_for_mechanism_analysis",
    )
    _require_allowed(
        normalized["review_status"],
        allowed=REVIEW_STATUS_VALUES,
        field_name="review_status",
    )

    if normalized["context_used"] == "none" and normalized["context_available"] != "否":
        raise ValueError("context_available must be 否 when context_used=none")
    if normalized["context_used"] != "none" and normalized["context_available"] != "是":
        raise ValueError("context_available must be 是 when context_used!=none")
    if normalized["context_used"] == "none" and normalized["interaction_level"]["event_present"] != "不适用":
        raise ValueError("interaction_level.event_present must be 不适用 when context_used=none")
    if (
        normalized["interaction_level"]["event_outcome"]
        and normalized["interaction_level"]["event_outcome"] not in INTERACTION_OUTCOME_VALUES
    ):
        raise ValueError("interaction_level.event_outcome has invalid code")

    for entry in normalized["decision_reason"]:
        if not re.match(r"^R\d+(?::\s.+)?$", entry):
            raise ValueError(f"decision_reason entry must be R# or R#: note. Got {entry!r}")
        code = entry.split(":", 1)[0].strip()
        if code not in DECISION_REASON_CODES:
            raise ValueError(f"decision_reason code not in controlled vocab: {code}")

    _require_evidence_if_codes(
        normalized["workflow_dimension"]["secondary_stage"],
        normalized["workflow_dimension"]["evidence"],
        field_name="workflow_dimension",
    )
    _require_evidence_if_codes(
        normalized["legitimacy_evaluation"]["direction"] + normalized["legitimacy_evaluation"]["basis"],
        normalized["legitimacy_evaluation"]["evidence"],
        field_name="legitimacy_evaluation",
    )
    _require_evidence_if_codes(
        normalized["boundary_expression"]["boundary_content_codes"]
        + normalized["boundary_expression"]["boundary_expression_mode_codes"],
        normalized["boundary_expression"]["evidence"],
        field_name="boundary_expression",
    )
    _require_evidence_if_codes(
        normalized["interaction_level"]["event_codes"] + normalized["interaction_level"]["event_basis_codes"],
        normalized["interaction_level"]["evidence"],
        field_name="interaction_level",
    )

    for unit in normalized["claim_units"]:
        has_codes = bool(
            unit["workflow_stage_codes"]
            or unit["legitimacy_codes"]
            or unit["basis_codes"]
            or unit["boundary_codes"]
            or unit["boundary_mode_codes"]
        )
        if has_codes and not unit["evidence"]:
            raise ValueError("claim_unit with codes must include evidence")
        for entry in unit["basis_codes"] + unit["boundary_codes"] + unit["boundary_mode_codes"]:
            if entry["code"] and not entry["evidence"]:
                raise ValueError("claim_unit code+evidence entries must include evidence")

    return normalized
