from __future__ import annotations

import pytest

from ai4s_legitimacy.coding import codebook_seed
from ai4s_legitimacy.coding.codebook_seed import (
    LEGACY_WORKFLOW_TO_STAGE_CODE,
    iter_codebook_rows,
    iter_legitimacy_lookup_rows,
    iter_workflow_lookup_rows,
)


def test_legacy_workflow_lookup_still_contains_core_stage() -> None:
    rows = list(iter_workflow_lookup_rows())
    stage_names = {row[1] for row in rows}
    assert "研究设计与方案制定" in stage_names
    assert "学术写作与成果表达" in stage_names


def test_legacy_legitimacy_lookup_still_contains_core_dimensions() -> None:
    rows = list(iter_legitimacy_lookup_rows())
    dimension_names = {row[1] for row in rows}
    assert "质疑/否定" in dimension_names
    assert "混合/冲突性评价" in dimension_names


def test_codebook_seed_primary_output_is_framework_v2() -> None:
    groups = {row.code_group for row in iter_codebook_rows()}
    assert groups == {
        "discursive_context",
        "practice_position",
        "intervention_mode",
        "normative_evaluation",
        "boundary_generation",
    }


def test_codebook_seed_examples_do_not_emit_placeholder_text() -> None:
    examples = {row.example for row in iter_codebook_rows()}
    assert "示例待补" not in examples


def test_codebook_seed_fails_fast_when_framework_v2_example_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_code_id = "N3"
    monkeypatch.delitem(codebook_seed._FRAMEWORK_V2_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError, match="missing example") as exc_info:
        list(iter_codebook_rows())
    message = str(exc_info.value)
    assert "missing example" in message
    assert "normative_evaluation" in message
    assert missing_code_id in message


def test_legacy_workflow_mapping_exists_for_current_runtime_labels() -> None:
    assert LEGACY_WORKFLOW_TO_STAGE_CODE["数据获取与预处理"] == "A1.6"
