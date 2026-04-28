from __future__ import annotations

from collections.abc import Sequence

RESEARCH_CORE = (
    "社交媒体中呈现出哪些 AI4S 科研工作流实践",
    "这些实践嵌入科研生产、科研治理、科研训练与能力建构的哪些具体环节",
    "平台用户如何围绕这些具体实践形成差异化的合法性判断",
    "这些判断依据了哪些评价标准",
    "讨论中如何形成对合理辅助/不可接受替代、人机分工边界、科研规范边界、科研诚信边界的协商",
)

PRIMARY_ANALYSIS_AXES = (
    "A. 科研工作流环节识别",
    "B. 合法性评价识别",
    "C. 边界协商机制识别",
)

ACTIVE_CODE_GROUPS = (
    "A. 科研工作流环节",
    "B. 合法性评价",
    "C. 评价标准",
    "D. 边界协商",
)

WORKFLOW_DIMENSIONS = (
    "科研生产工作流",
    "科研治理工作流",
    "科研训练与能力建构",
)

INCLUSION_RULES = (
    "帖子必须明确涉及 AI 或具体 AI 工具。",
    "帖子必须明确落到科研生产、科研治理或科研训练/能力建构中的具体环节。",
    "帖子至少包含实践展示、使用过程、评价判断、规范争议、边界协商之一。",
    "能支持识别工作流环节、合法性评价或边界协商中的至少一个研究问题。",
)

EXCLUSION_RULES = (
    "泛化趋势帖、科技新闻帖、纯产品介绍、纯广告、纯链接、空泛态度帖默认剔除。",
    "普通学习、办公、求职、编程、课堂作业等内容，若无法回到科研工作流则剔除。",
    "低信息帖子若无法从标题或正文识别具体科研环节、评价或边界，则剔除。",
)

SCREENING_SELF_CHECKS = (
    "是否能明确回到至少一个 A/B/D 研究问题；若三者都不能支持，则剔除。",
    "是否存在帖子原文证据支撑当前编码；无明确证据时不补码。",
    "是否需要多重编码；涉及多个环节、评价或边界时不得强行单选。",
)

STRUCTURED_OUTPUT_FIELD_DEFAULTS = (
    ("inclusion_decision", ""),
    ("reason", ""),
    ("summary", ""),
    ("workflow_codes", []),
    ("legitimacy_codes", []),
    ("evaluation_codes", []),
    ("boundary_codes", []),
    ("ambiguity_note", ""),
    ("followup_check", ""),
    ("是否纳入", ""),
    ("纳入或剔除理由", ""),
    ("帖子主题摘要", ""),
    ("工作流维度", {"一级维度": [], "二级环节": []}),
    ("合法性评价", {"评价方向": [], "评价依据": []}),
    ("边界协商", {"是否涉及": False, "涉及哪类边界": []}),
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
