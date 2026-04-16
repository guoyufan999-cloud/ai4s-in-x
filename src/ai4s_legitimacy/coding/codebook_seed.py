from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CodebookRow:
    code_id: str
    code_group: str
    code_name: str
    definition: str
    include_rule: str
    exclude_rule: str
    example: str


WORKFLOW_STAGES = (
    ("workflow.topic_definition", "选题与问题定义", 1, "围绕研究主题、问题意识和创新切入点展开的讨论。"),
    ("workflow.literature_review", "文献检索与阅读", 2, "围绕文献搜索、阅读、综述整理的讨论。"),
    ("workflow.hypothesis_formation", "假设形成", 3, "围绕研究假设和理论构思的讨论。"),
    ("workflow.research_design", "研究设计", 4, "围绕研究方案、实验设计和方法路径的讨论。"),
    ("workflow.data_processing", "数据处理", 5, "围绕数据获取、清洗、标注和预处理的讨论。"),
    ("workflow.modeling_computation", "建模与计算", 6, "围绕编程、建模、统计和算法计算的讨论。"),
    ("workflow.result_interpretation", "结果解释", 7, "围绕研究结果说明、解释和因果推断的讨论。"),
    ("workflow.visualization_presentation", "可视化呈现", 8, "围绕图表、汇报展示和结果呈现的讨论。"),
    ("workflow.paper_writing", "论文写作", 9, "围绕写作、润色、结构整理和表达的讨论。"),
    ("workflow.submission_defense", "投稿与答辩", 10, "围绕投稿、审稿、答辩和返修的讨论。"),
    ("workflow.collaboration_management", "协作与项目管理", 11, "围绕科研协作、组会和项目推进的讨论。"),
)

AI_PRACTICES = (
    CodebookRow("practice.substitution", "ai_practice", "替代执行", "AI 直接替代研究者完成任务。", "明确让 AI 代做核心任务。", "仅提供建议或整理。", "[构造示例] 直接让 AI 写完一整篇课程论文并提交。"),
    CodebookRow("practice.advisory", "ai_practice", "辅助建议", "AI 提供建议、灵感或备选路径。", "明确作为参考或启发。", "直接代写代做。", "[构造示例] 向 AI 请教几种可行的实证方法路径。"),
    CodebookRow("practice.generation", "ai_practice", "自动生成", "AI 直接生成文本、代码、结构或材料。", "明确产出成品。", "仅做摘要整理。", "[构造示例] 用 AI 一键生成完整的文献综述段落。"),
    CodebookRow("practice.structuring", "ai_practice", "结构化整理", "AI 对已有信息做提取、摘要、分类和重组。", "强调归纳、提炼、整理。", "首次生成全新内容。", "[构造示例] 把几十篇文献摘要丢给 AI 做分类归纳。"),
    CodebookRow("practice.quality_check", "ai_practice", "质量检查", "AI 用于校验、查错、比较和审核。", "明确是核查环节。", "首次生成内容。", "[构造示例] 用 AI 检查代码中的逻辑错误和数据异常。"),
    CodebookRow("practice.explanation_support", "ai_practice", "解释支持", "AI 用于说明概念、解释结果或辅助理解。", "强调帮助理解。", "直接替代判断。", "[构造示例] 让 AI 用通俗语言解释复杂的统计指标。"),
    CodebookRow("practice.coordination", "ai_practice", "协作协调", "AI 用于任务安排、沟通组织和项目协同。", "强调协同推进。", "单纯写作润色。", "[构造示例] 用 AI 安排课题组每周的任务分工和进度。"),
)

LEGITIMACY_CODES = (
    ("legitimacy.efficiency_justification", "效率正当性", 1, "以提效、节约时间和减轻负担作为正当化依据。"),
    ("legitimacy.professional_boundary", "专业能力边界", 2, "强调研究者应保留的核心能力边界。"),
    ("legitimacy.originality", "原创性", 3, "围绕原创贡献和独立完成展开的判断。"),
    ("legitimacy.academic_integrity", "学术诚信", 4, "围绕不端、欺骗、违规和伦理风险展开的判断。"),
    ("legitimacy.explainability", "可解释性", 5, "围绕过程和结果是否能够说明展开的判断。"),
    ("legitimacy.reproducibility", "可复现性", 6, "围绕过程透明与结果复做展开的判断。"),
    ("legitimacy.accountability", "责任归属", 7, "围绕错误、署名和后果由谁承担展开的判断。"),
    ("legitimacy.tool_fit", "工具适配性", 8, "围绕工具与任务/学科匹配度展开的判断。"),
    ("legitimacy.disciplinary_consistency", "学科规范一致性", 9, "围绕学科内部规范是否允许展开的判断。"),
    ("legitimacy.training_value", "教育/训练价值", 10, "围绕能力培养和训练价值是否受损展开的判断。"),
)

BOUNDARY_CODES = (
    CodebookRow("boundary.human_ai_division", "boundary", "人机分工边界", "讨论哪些任务应由人做、哪些可交给 AI。", "明确区分人做与 AI 做。", "只泛谈技术优缺点。", "[构造示例] 数据分析可以交给 AI，但研究问题和结论必须由人来做。"),
    CodebookRow("boundary.academic_ability_boundary", "boundary", "学术能力边界", "讨论研究者应保留哪些核心能力。", "强调科研训练不能外包。", "只谈效率。", "[构造示例] 读研究生至少要自己能写代码，不能全外包给 AI。"),
    CodebookRow("boundary.authorship_accountability_boundary", "boundary", "责任与署名边界", "讨论署名、责任和归因问题。", "明确讨论作者署名或责任。", "只谈输出质量。", "[构造示例] 如果用了 AI，论文作者名单里要不要加 ChatGPT。"),
    CodebookRow("boundary.assistance_vs_substitution", "boundary", "辅助与替代边界", "讨论可接受辅助与不可接受替代的界限。", "明确区分辅助与代做。", "只谈工具推荐。", "[构造示例] 让 AI 润色语言和让 AI 代写整段，性质不一样。"),
    CodebookRow("boundary.role_based_usage", "boundary", "不同身份使用边界", "讨论本科生、研究生、教师等不同角色的使用界限。", "明确涉及身份差异。", "只谈一般规范。", "[构造示例] 本科生写作业用 AI 和老师做科研用 AI，标准能一样吗。"),
    CodebookRow("boundary.disciplinary_norm_boundary", "boundary", "学科规范边界", "讨论不同学科之间规范差异形成的边界。", "明确谈学科差异。", "只谈个人偏好。", "[构造示例] 理工科和人文社科对 AI 辅助写作的接受度明显不同。"),
)

LEGACY_WORKFLOW_TO_STAGE_CODE = {
    "选题与问题定义": "workflow.topic_definition",
    "文献检索与综述": "workflow.literature_review",
    "研究设计与实验/方案制定": "workflow.research_design",
    "数据获取与预处理": "workflow.data_processing",
    "编码/建模/统计分析": "workflow.modeling_computation",
    "论文写作/投稿/审稿回复": "workflow.paper_writing",
    "学术交流与科研管理": "workflow.collaboration_management",
}

_WORKFLOW_EXAMPLES = {
    "workflow.topic_definition": "博士生是不是都会和 AI 讨论一下课题思路，笑死。",
    "workflow.literature_review": "1文献调研 2文献粗读 3文献精读 4课堂讲义总结。",
    "workflow.hypothesis_formation": "[构造示例] 用 AI 推导变量之间的中介效应假设。",
    "workflow.research_design": "[构造示例] 让 AI 帮忙设计对照实验的分组和样本量。",
    "workflow.data_processing": "不写一行代码，如何爬取网页数据。",
    "workflow.modeling_computation": "用 Claude Code 做统计分析和建模。",
    "workflow.result_interpretation": "[构造示例] 借助 AI 解释回归系数的经济学含义。",
    "workflow.visualization_presentation": "[构造示例] 用 AI 把数据结果一键转换成科研汇报 PPT 配图。",
    "workflow.paper_writing": "AI 论文写作质量超过我的毕业论文。",
    "workflow.submission_defense": "[构造示例] 用 AI 生成审稿回复信和答辩 PPT。",
    "workflow.collaboration_management": "如何用 GPT 进行项目管理 + PARA 原则打造个人知识库。",
}

_LEGITIMACY_EXAMPLES = {
    "legitimacy.efficiency_justification": "[构造示例] 用 AI 写代码比手动写快三倍，省下来的时间可以做实验。",
    "legitimacy.professional_boundary": "[构造示例] 如果连代码都不会自己写，研究生毕业还能做什么。",
    "legitimacy.originality": "[构造示例] 论文核心观点如果都是 AI 想的，还算不算自己的研究。",
    "legitimacy.academic_integrity": "[构造示例] 用 AI 生成虚假数据属于学术不端。",
    "legitimacy.explainability": "[构造示例] AI 给的分析结果我根本讲不清楚原理，答辩怎么过。",
    "legitimacy.reproducibility": "[构造示例] 如果审稿人要复现分析过程，我不知道 AI 中间做了什么。",
    "legitimacy.accountability": "[构造示例] AI 写的内容出了错，导师问责算谁的。",
    "legitimacy.tool_fit": "[构造示例] 这种复杂模型任务本来就不适合用通用聊天 AI。",
    "legitimacy.disciplinary_consistency": "[构造示例] 我们学科不允许在正式论文中使用 AI 生成的文本。",
    "legitimacy.training_value": "[构造示例] 本科生一上来就用 AI 写论文，根本学不到研究方法。",
}


def _require_example(
    examples: dict[str, str],
    *,
    code_id: str,
    code_group: str,
) -> str:
    try:
        return examples[code_id]
    except KeyError as exc:
        raise ValueError(
            f"missing example for {code_group}: {code_id}"
        ) from exc


def iter_codebook_rows() -> Iterable[CodebookRow]:
    for code_id, code_name, _, definition in WORKFLOW_STAGES:
        yield CodebookRow(
            code_id,
            "workflow_stage",
            code_name,
            definition,
            "围绕该科研环节的讨论。",
            "与该环节无关的泛化讨论。",
            _require_example(
                _WORKFLOW_EXAMPLES,
                code_id=code_id,
                code_group="workflow_stage",
            ),
        )
    for row in AI_PRACTICES:
        yield row
    for code_id, code_name, _, definition in LEGITIMACY_CODES:
        yield CodebookRow(
            code_id,
            "legitimacy_dimension",
            code_name,
            definition,
            "直接以该标准判断 AI 使用是否合理。",
            "只表达一般态度、不涉及判断标准。",
            _require_example(
                _LEGITIMACY_EXAMPLES,
                code_id=code_id,
                code_group="legitimacy_dimension",
            ),
        )
    for row in BOUNDARY_CODES:
        yield row


def iter_workflow_lookup_rows() -> Iterable[tuple[str, str, int, str]]:
    for code_id, code_name, order_index, definition in WORKFLOW_STAGES:
        yield code_id, code_name, order_index, definition


def iter_legitimacy_lookup_rows() -> Iterable[tuple[str, str, int, str]]:
    for code_id, code_name, order_index, definition in LEGITIMACY_CODES:
        yield code_id, code_name, order_index, definition
