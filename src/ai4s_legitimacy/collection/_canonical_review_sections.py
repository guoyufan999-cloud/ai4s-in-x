from __future__ import annotations

from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    apply_claim_units_to_row,
    normalize_canonical_row,
)

from ._canonical_review_inference import (
    api_assistance_for_row,
    basis_codes_for_row,
    bootstrap_claim_units,
    boundary_content_codes_for_row,
    boundary_mode_codes_for_row,
    evidence_for_codes,
    evidence_master_for_row,
    interaction_level_for_row,
    legitimacy_codes_for_row,
    mechanism_memo_for_row,
    notes_for_row,
    workflow_codes_for_row,
)


def populate_rescreen_sections(
    canonical: dict[str, Any],
    row: dict[str, Any],
    *,
    decision: str,
    record_id: str,
) -> dict[str, Any]:
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
    canonical["api_assistance"] = api_assistance_for_row(row)
    canonical["notes"] = notes_for_row(row, decision=decision, record_id=record_id)
    canonical["claim_units"] = []
    canonical["evidence_master"] = evidence_master_for_row(canonical)
    canonical["mechanism_memo"] = mechanism_memo_for_row(canonical)
    return normalize_canonical_row(canonical)


def populate_formal_review_sections(
    canonical: dict[str, Any],
    row: dict[str, Any],
    *,
    decision: str,
    base_row: dict[str, Any] | None,
) -> dict[str, Any]:
    workflow_codes = workflow_codes_for_row(row, base_row=base_row)
    legitimacy_codes = legitimacy_codes_for_row(row, decision=decision, base_row=base_row)
    basis_codes = basis_codes_for_row(row, base_row=base_row)
    boundary_content_codes = boundary_content_codes_for_row(row, base_row=base_row)
    boundary_mode_codes = boundary_mode_codes_for_row(row, base_row=base_row)

    canonical["workflow_dimension"] = {
        "primary_dimension": [],
        "secondary_stage": workflow_codes,
        "evidence": evidence_for_codes(row, base_row=base_row, codes=workflow_codes),
    }
    canonical["legitimacy_evaluation"] = {
        "direction": legitimacy_codes,
        "basis": basis_codes,
        "evidence": evidence_for_codes(
            row,
            base_row=base_row,
            codes=legitimacy_codes + basis_codes,
        ),
    }
    canonical["boundary_expression"] = {
        "present": "是" if (boundary_content_codes or boundary_mode_codes) else "否",
        "boundary_content_codes": boundary_content_codes,
        "boundary_expression_mode_codes": boundary_mode_codes,
        "evidence": evidence_for_codes(
            row,
            base_row=base_row,
            codes=boundary_content_codes + boundary_mode_codes,
        ),
    }
    canonical["interaction_level"] = interaction_level_for_row(row)
    canonical["api_assistance"] = api_assistance_for_row(row)
    canonical["notes"] = notes_for_row(
        row,
        decision=decision,
        record_id=str(canonical["record_id"]),
    )

    claim_units = row.get("claim_units")
    if claim_units:
        canonical["claim_units"] = claim_units
    elif decision == "纳入":
        canonical["claim_units"] = bootstrap_claim_units(
            canonical["source_text"],
            workflow_codes=workflow_codes,
            legitimacy_codes=legitimacy_codes,
            basis_codes=basis_codes,
            boundary_content_codes=boundary_content_codes,
            boundary_mode_codes=boundary_mode_codes,
        )
    else:
        canonical["claim_units"] = []

    canonical["evidence_master"] = evidence_master_for_row(canonical)
    canonical["mechanism_memo"] = mechanism_memo_for_row(canonical)
    return normalize_canonical_row(apply_claim_units_to_row(canonical))
