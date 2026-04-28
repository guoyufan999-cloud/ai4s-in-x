from __future__ import annotations

import pytest

from ai4s_legitimacy.coding import codebook_seed
from ai4s_legitimacy.coding.codebook_seed import FRAMEWORK_V2_GROUPS, iter_codebook_rows

EXPECTED_GROUPS = {
    "practice_position_domain",
    "practice_position_stage",
    "normative_evaluation_tendency",
    "normative_evaluation_standard",
    "boundary_type",
    "boundary_mode",
    "interaction_action",
    "interaction_basis",
    "interaction_outcome",
    "ai_intervention_mode",
    "ai_intervention_intensity",
    "evaluation_tension",
    "formal_norm_reference",
    "boundary_mechanism",
    "boundary_result",
}

GROUP_PREFIXES: dict[str, tuple[str, ...]] = {
    "practice_position_domain": ("A",),
    "practice_position_stage": ("A",),
    "normative_evaluation_tendency": ("B",),
    "normative_evaluation_standard": ("C",),
    "boundary_type": ("D1",),
    "boundary_mode": ("D2",),
    "interaction_action": ("E2",),
    "interaction_basis": ("E3",),
    "interaction_outcome": ("E4",),
    "ai_intervention_mode": ("F",),
    "ai_intervention_intensity": ("G",),
    "evaluation_tension": ("H",),
    "formal_norm_reference": ("I",),
    "boundary_mechanism": ("J",),
    "boundary_result": ("K",),
}

OBSOLETE_DRAFT_GROUPS = {
    "discursive_context",
    "practice_position",
    "intervention_mode",
    "normative_evaluation",
    "boundary_generation",
}


def test_iter_codebook_rows_outputs_exact_framework_v2_groups() -> None:
    rows = list(iter_codebook_rows())
    assert {row.code_group for row in rows} == EXPECTED_GROUPS
    assert set(FRAMEWORK_V2_GROUPS) == EXPECTED_GROUPS


def test_framework_v2_code_ids_are_unique_and_match_group_prefixes() -> None:
    rows = list(iter_codebook_rows())
    code_ids = [row.code_id for row in rows]

    assert len(code_ids) == len(set(code_ids))
    for row in rows:
        assert row.code_id.startswith(GROUP_PREFIXES[row.code_group])


def test_framework_v2_extension_code_groups_are_present() -> None:
    rows = list(iter_codebook_rows())
    by_code = {row.code_id: row for row in rows}

    assert by_code["F1"].code_group == "ai_intervention_mode"
    assert by_code["G1"].code_group == "ai_intervention_intensity"
    assert by_code["H1"].code_group == "evaluation_tension"
    assert by_code["I0"].code_group == "formal_norm_reference"
    assert by_code["J1"].code_group == "boundary_mechanism"
    assert by_code["K1"].code_group == "boundary_result"
    assert by_code["C14"].code_group == "normative_evaluation_standard"
    assert by_code["D1.12"].code_group == "boundary_type"


def test_framework_v2_examples_are_complete_and_not_placeholder_text() -> None:
    rows = list(iter_codebook_rows())

    assert rows
    assert all(row.definition.strip() for row in rows)
    assert all(row.include_rule.strip() for row in rows)
    assert all(row.exclude_rule.strip() for row in rows)
    assert all(row.example.strip() for row in rows)
    assert "示例待补" not in {row.example for row in rows}


def test_obsolete_s_p_i_n_g_draft_groups_are_not_primary_codebook_output() -> None:
    groups = {row.code_group for row in iter_codebook_rows()}
    assert groups.isdisjoint(OBSOLETE_DRAFT_GROUPS)


def test_framework_v2_seed_fails_fast_when_example_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_code_id = "F1"
    monkeypatch.delitem(codebook_seed._V2_EXTENSION_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError, match="missing example") as exc_info:
        list(iter_codebook_rows())

    message = str(exc_info.value)
    assert "ai_intervention_mode" in message
    assert missing_code_id in message
