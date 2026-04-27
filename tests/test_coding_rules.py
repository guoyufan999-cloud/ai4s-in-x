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
    assert "研究设计与方案制定" in stage_names
    assert "学术写作与成果表达" in stage_names


def test_legitimacy_lookup_contains_core_dimensions() -> None:
    rows = list(iter_legitimacy_lookup_rows())
    dimension_names = {row[1] for row in rows}
    assert "质疑/否定" in dimension_names
    assert "混合/冲突性评价" in dimension_names


def test_codebook_seed_covers_all_four_layers() -> None:
    groups = {row.code_group for row in iter_codebook_rows()}
    assert {
        "workflow_domain",
        "workflow_stage",
        "legitimacy_direction",
        "evaluation_standard",
        "boundary_content",
        "boundary_mode",
    } <= groups


def test_codebook_seed_examples_do_not_emit_placeholder_text() -> None:
    examples = {row.example for row in iter_codebook_rows()}
    assert "示例待补" not in examples


def test_codebook_seed_fails_fast_when_workflow_example_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_code_id = "A1.1"
    monkeypatch.delitem(codebook_seed._WORKFLOW_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError) as exc_info:
        list(iter_codebook_rows())
    message = str(exc_info.value)
    assert "missing example" in message
    assert "workflow_stage" in message
    assert missing_code_id in message


def test_codebook_seed_fails_fast_when_legitimacy_example_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_code_id = "B4"
    monkeypatch.delitem(codebook_seed._LEGITIMACY_EXAMPLES, missing_code_id)

    with pytest.raises(ValueError) as exc_info:
        list(iter_codebook_rows())
    message = str(exc_info.value)
    assert "missing example" in message
    assert "legitimacy_direction" in message
    assert missing_code_id in message


def test_legacy_workflow_mapping_exists_for_current_runtime_labels() -> None:
    assert LEGACY_WORKFLOW_TO_STAGE_CODE["数据获取与预处理"] == "A1.6"
