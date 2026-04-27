from __future__ import annotations

from ai4s_legitimacy.config.research_baseline import (
    ACTIVE_CODE_GROUPS,
    PRIMARY_ANALYSIS_AXES,
    SCREENING_SELF_CHECKS,
    STRUCTURED_OUTPUT_FIELD_DEFAULTS,
    has_multiple_codings,
    supports_research_question,
)


def test_research_baseline_exports_active_axes_and_output_fields() -> None:
    assert PRIMARY_ANALYSIS_AXES == (
        "A. 科研工作流环节识别",
        "B. 合法性评价识别",
        "C. 边界协商机制识别",
    )
    assert ACTIVE_CODE_GROUPS == (
        "A. 科研工作流环节",
        "B. 合法性评价",
        "C. 评价标准",
        "D. 边界协商",
    )
    assert len(SCREENING_SELF_CHECKS) == 3
    field_names = {field for field, _ in STRUCTURED_OUTPUT_FIELD_DEFAULTS}
    assert {
        "是否纳入",
        "纳入或剔除理由",
        "帖子主题摘要",
        "工作流维度",
        "合法性评价",
        "边界协商",
        "备注",
    } <= field_names


def test_research_baseline_helpers_follow_long_term_rules() -> None:
    assert supports_research_question(["A1.2"], [], []) is True
    assert supports_research_question([], ["B2"], []) is True
    assert supports_research_question([], [], ["D4"]) is True
    assert supports_research_question([], [], []) is False

    assert has_multiple_codings(["A1.2"], ["B2"]) is True
    assert has_multiple_codings(["A1.2"], [], []) is False
    assert has_multiple_codings(["A1.2", "A1.9"], [], []) is True
