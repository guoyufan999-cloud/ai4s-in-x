from __future__ import annotations

import pytest

from ai4s_legitimacy.coding import codebook_seed
from ai4s_legitimacy.coding.codebook_seed import FRAMEWORK_V2_GROUPS, iter_codebook_rows

EXPECTED_GROUPS = {
    "discursive_context",
    "practice_position",
    "intervention_mode",
    "normative_evaluation",
    "boundary_generation",
}

GROUP_PREFIXES = {
    "discursive_context": "S",
    "practice_position": "P",
    "intervention_mode": "I",
    "normative_evaluation": "N",
    "boundary_generation": "G",
}

LEGACY_MAIN_GROUPS = {
    "workflow_domain",
    "workflow_stage",
    "legitimacy_direction",
    "evaluation_standard",
    "boundary_content",
    "boundary_mode",
    "interaction_action",
    "interaction_basis",
    "interaction_outcome",
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


def test_framework_v2_examples_are_complete_and_not_placeholder_text() -> None:
    rows = list(iter_codebook_rows())

    assert rows
    assert all(row.definition.strip() for row in rows)
    assert all(row.include_rule.strip() for row in rows)
    assert all(row.exclude_rule.strip() for row in rows)
    assert all(row.example.strip() for row in rows)
    assert "示例待补" not in {row.example for row in rows}


def test_legacy_groups_are_not_primary_codebook_output() -> None:
    groups = {row.code_group for row in iter_codebook_rows()}
    assert groups.isdisjoint(LEGACY_MAIN_GROUPS)


def test_framework_v2_seed_fails_fast_when_example_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_code_id = "S1"
    monkeypatch.delitem(codebook_seed._FRAMEWORK_V2_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError, match="missing example") as exc_info:
        list(iter_codebook_rows())

    message = str(exc_info.value)
    assert "discursive_context" in message
    assert missing_code_id in message
