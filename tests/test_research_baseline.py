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
        "1. 话语情境",
        "2. 实践位置",
        "3. 介入方式",
        "4. 规范评价",
        "5. 边界生成",
    )
    assert ACTIVE_CODE_GROUPS == (
        "A. 实践位置（原科研工作流环节）",
        "B. 规范评价倾向（原合法性评价）",
        "C. 规范评价标准",
        "D. 边界类型与边界表达",
        "E. 互动协商兼容字段",
        "F. AI介入方式",
        "G. AI介入强度",
        "H. 评价张力",
        "I. 正式规范参照",
        "J. 边界协商机制",
        "K. 边界协商结果",
    )
    assert len(SCREENING_SELF_CHECKS) == 4
    field_names = {field for field, _ in STRUCTURED_OUTPUT_FIELD_DEFAULTS}
    assert {
        "是否纳入",
        "纳入或剔除理由",
        "帖子主题摘要",
        "工作流维度",
        "规范评价",
        "AI介入",
        "正式规范参照",
        "边界协商",
        "边界生成",
        "备注",
    } <= field_names
    assert "ai_intervention_mode_codes" in field_names
    assert "boundary_result_codes" in field_names


def test_research_baseline_helpers_follow_long_term_rules() -> None:
    assert supports_research_question(["A1.2"], [], []) is True
    assert supports_research_question([], ["B2"], []) is True
    assert supports_research_question([], [], ["D4"]) is True
    assert supports_research_question([], [], []) is False

    assert has_multiple_codings(["A1.2"], ["B2"]) is True
    assert has_multiple_codings(["A1.2"], [], []) is False
    assert has_multiple_codings(["A1.2", "A1.9"], [], []) is True
