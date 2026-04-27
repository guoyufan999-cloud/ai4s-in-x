from __future__ import annotations

from typing import Any

from .canonical_claim_units import normalize_claim_units
from .canonical_defaults import (
    empty_boundary_expression,
    empty_legitimacy_evaluation,
    empty_notes,
    empty_workflow_dimension,
)
from .canonical_utils import primary_dimensions_from_workflow


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

    workflow_dimension = row.get("workflow_dimension") or empty_workflow_dimension()
    workflow_dimension["secondary_stage"] = workflow_codes
    workflow_dimension["primary_dimension"] = primary_dimensions_from_workflow(workflow_codes)
    workflow_dimension["evidence"] = workflow_evidence
    row["workflow_dimension"] = workflow_dimension

    legitimacy_evaluation = row.get("legitimacy_evaluation") or empty_legitimacy_evaluation()
    legitimacy_evaluation["direction"] = legitimacy_codes
    legitimacy_evaluation["basis"] = basis_codes
    legitimacy_evaluation["evidence"] = legitimacy_evidence
    row["legitimacy_evaluation"] = legitimacy_evaluation

    boundary_expression = row.get("boundary_expression") or empty_boundary_expression()
    boundary_expression["present"] = "是" if (boundary_content_codes or boundary_mode_codes) else "否"
    boundary_expression["boundary_content_codes"] = boundary_content_codes
    boundary_expression["boundary_expression_mode_codes"] = boundary_mode_codes
    boundary_expression["evidence"] = boundary_evidence
    row["boundary_expression"] = boundary_expression

    notes = row.get("notes") or empty_notes(str(row.get("record_id") or ""))
    notes["multi_label"] = "是" if len(workflow_codes) > 1 or len(claim_units) > 1 else "否"
    row["notes"] = notes
    return row
