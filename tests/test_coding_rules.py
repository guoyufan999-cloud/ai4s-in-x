from __future__ import annotations

import pytest

import ai4s_legitimacy.coding.codebook_seed as codebook_seed
from ai4s_legitimacy.coding.codebook_seed import (
    LEGACY_WORKFLOW_TO_STAGE_CODE,
    iter_codebook_rows,
    iter_legitimacy_lookup_rows,
    iter_workflow_lookup_rows,
)


def test_workflow_lookup_contains_core_stage() -> None:
    rows = list(iter_workflow_lookup_rows())
    stage_names = {row[1] for row in rows}
    assert "研究设计" in stage_names
    assert "论文写作" in stage_names


def test_legitimacy_lookup_contains_core_dimensions() -> None:
    rows = list(iter_legitimacy_lookup_rows())
    dimension_names = {row[1] for row in rows}
    assert "学术诚信" in dimension_names
    assert "责任归属" in dimension_names


def test_codebook_seed_covers_all_four_layers() -> None:
    groups = {row.code_group for row in iter_codebook_rows()}
    assert {"workflow_stage", "ai_practice", "legitimacy_dimension", "boundary"} <= groups


def test_codebook_seed_examples_do_not_emit_placeholder_text() -> None:
    examples = {row.example for row in iter_codebook_rows()}
    assert "示例待补" not in examples


def test_codebook_seed_fails_fast_when_workflow_example_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_code_id = "workflow.topic_definition"
    monkeypatch.delitem(codebook_seed._WORKFLOW_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError) as exc_info:
        list(iter_codebook_rows())
    message = str(exc_info.value)
    assert "missing example" in message
    assert "workflow_stage" in message
    assert missing_code_id in message


def test_codebook_seed_fails_fast_when_legitimacy_example_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_code_id = "legitimacy.training_value"
    monkeypatch.delitem(codebook_seed._LEGITIMACY_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError) as exc_info:
        list(iter_codebook_rows())
    message = str(exc_info.value)
    assert "missing example" in message
    assert "legitimacy_dimension" in message
    assert missing_code_id in message


def test_legacy_workflow_mapping_exists_for_current_runtime_labels() -> None:
    assert LEGACY_WORKFLOW_TO_STAGE_CODE["数据获取与预处理"] == "workflow.data_processing"
