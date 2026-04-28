from __future__ import annotations

from collections.abc import Sequence

RESEARCH_CORE = (
    "社交媒体中呈现出哪些 AI 介入科研活动的话语情境",
    "这些实践嵌入科研生产、科研治理、科研训练与能力建构的哪些实践位置",
    "AI 以何种方式和强度介入具体科研活动",
    "平台用户如何围绕这些具体实践形成差异化的规范评价与评价张力",
    "讨论中如何形成对合理辅助/不可接受替代、人机分工、责任、原创性、披露、诚信、训练与治理边界的协商",
)

PRIMARY_ANALYSIS_AXES = (
    "1. 话语情境",
    "2. 实践位置",
    "3. 介入方式",
    "4. 规范评价",
    "5. 边界生成",
)

ACTIVE_CODE_GROUPS = (
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

WORKFLOW_DIMENSIONS = (
    "科研生产工作流",
    "科研治理工作流",
    "科研训练与能力建构",
)

INCLUSION_RULES = (
    "帖子必须明确涉及 AI 或具体 AI 工具。",
    "帖子必须明确落到科研生产、科研治理或科研训练/能力建构中的具体实践位置。",
    "帖子至少包含实践展示、使用过程、评价判断、规范争议、边界协商之一。",
    "能支持识别话语情境、实践位置、介入方式、规范评价或边界生成中的至少一个研究问题。",
)

EXCLUSION_RULES = (
    "泛化趋势帖、科技新闻帖、纯产品介绍、纯广告、纯链接、空泛态度帖默认剔除。",
    "普通学习、办公、求职、编程、课堂作业等内容，若无法回到科研工作流则剔除。",
    "低信息帖子若无法从标题或正文识别具体科研环节、评价或边界，则剔除。",
)

SCREENING_SELF_CHECKS = (
    "是否能明确回到至少一个五层框架研究问题；若完全不能支持，则剔除。",
    "是否存在帖子原文证据支撑当前编码；无明确证据时不补码。",
    "是否需要多重编码；涉及多个环节、评价或边界时不得强行单选。",
    "F/G/H/I/J/K 只能作为人工 reviewed draft/正式字段保留，不得由程序自动推断。",
)

STRUCTURED_OUTPUT_FIELD_DEFAULTS = (
    ("inclusion_decision", ""),
    ("reason", ""),
    ("summary", ""),
    ("workflow_codes", []),
    ("legitimacy_codes", []),
    ("evaluation_codes", []),
    ("boundary_codes", []),
    ("ai_intervention_mode_codes", []),
    ("ai_intervention_intensity_codes", []),
    ("evaluation_tension_codes", []),
    ("formal_norm_reference_codes", []),
    ("boundary_mechanism_codes", []),
    ("boundary_result_codes", []),
    ("ambiguity_note", ""),
    ("followup_check", ""),
    ("是否纳入", ""),
    ("纳入或剔除理由", ""),
    ("帖子主题摘要", ""),
    ("工作流维度", {"一级维度": [], "二级环节": []}),
    ("规范评价", {"评价倾向": [], "评价标准": [], "评价张力": []}),
    ("AI介入", {"介入方式": [], "介入强度": []}),
    ("正式规范参照", []),
    ("边界协商", {"是否涉及": False, "涉及哪类边界": []}),
    ("边界生成", {"协商机制": [], "协商结果": []}),
    (
        "备注",
        {
            "是否多重编码": False,
            "是否存在歧义": False,
            "建议后续复核点": "",
        },
    ),
)


def supports_research_question(
    workflow_codes: Sequence[str] | None,
    legitimacy_codes: Sequence[str] | None,
    boundary_codes: Sequence[str] | None,
) -> bool:
    return bool(
        list(_normalized_codes(workflow_codes))
        or list(_normalized_codes(legitimacy_codes))
        or list(_normalized_codes(boundary_codes))
    )


def has_multiple_codings(*code_groups: Sequence[str] | None) -> bool:
    total_codes = sum(len(list(_normalized_codes(group))) for group in code_groups)
    return total_codes > 1


def screening_prompt_context() -> str:
    axes = "；".join(PRIMARY_ANALYSIS_AXES)
    inclusion = "\n".join(f"- {item}" for item in INCLUSION_RULES)
    exclusion = "\n".join(f"- {item}" for item in EXCLUSION_RULES)
    return (
        f"研究主线：{axes}\n"
        "纳入标准：\n"
        f"{inclusion}\n"
        "默认剔除：\n"
        f"{exclusion}"
    )


def _normalized_codes(code_group: Sequence[str] | None) -> list[str]:
    if not code_group:
        return []
    return [str(code).strip() for code in code_group if str(code).strip()]


__all__ = [
    "ACTIVE_CODE_GROUPS",
    "EXCLUSION_RULES",
    "INCLUSION_RULES",
    "PRIMARY_ANALYSIS_AXES",
    "RESEARCH_CORE",
    "SCREENING_SELF_CHECKS",
    "STRUCTURED_OUTPUT_FIELD_DEFAULTS",
    "WORKFLOW_DIMENSIONS",
    "has_multiple_codings",
    "screening_prompt_context",
    "supports_research_question",
]
