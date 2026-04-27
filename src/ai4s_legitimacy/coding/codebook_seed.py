from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ai4s_legitimacy.collection.canonical_schema import (
    BOUNDARY_CONTENT_LABELS,
    BOUNDARY_MODE_LABELS,
    EVALUATION_LABELS,
    INTERACTION_BASIS_CODES,
    INTERACTION_EVENT_CODES,
    LEGITIMACY_LABELS,
)


@dataclass(frozen=True)
class CodebookRow:
    code_id: str
    code_group: str
    code_name: str
    definition: str
    include_rule: str
    exclude_rule: str
    example: str


WORKFLOW_DOMAINS = (
    (
        "A1",
        "P",
        "科研生产工作流",
        1,
        "AI 嵌入研究构思、研究实施、结果验证与成果表达等知识生产链条。",
    ),
    (
        "A2",
        "G",
        "科研治理工作流",
        2,
        "AI 嵌入科研组织、协作、资源配置、伦理合规、评价与出版治理链条。",
    ),
    (
        "A3",
        "T",
        "科研训练与能力建构",
        3,
        "AI 嵌入科研入门、方法学习、工具训练、阅读写作训练与效率习惯养成链条。",
    ),
)

WORKFLOW_STAGES = (
    ("A1.1", "P", "研究构思与问题定义", 1, "围绕研究问题、选题方向、创新切入点和课题构思的讨论。"),
    ("A1.2", "P", "文献调研与知识整合", 2, "围绕文献检索、筛选、阅读、综述与知识梳理的讨论。"),
    ("A1.3", "P", "研究设计与方案制定", 3, "围绕研究方案、实验设计、方法选择和任务拆解的讨论。"),
    ("A1.4", "P", "数据获取", 4, "围绕数据抓取、采集、标注、资料汇集与原始材料获取的讨论。"),
    ("A1.5", "P", "实验实施与仿真执行", 5, "围绕实验推进、仿真运行、自动化执行和实验流程控制的讨论。"),
    ("A1.6", "P", "数据处理与分析建模", 6, "围绕数据清洗、统计分析、建模、编码与算法计算的讨论。"),
    ("A1.7", "P", "结果验证与论文复现", 7, "围绕结果核验、论文复现、代码检查与可重复性验证的讨论。"),
    ("A1.8", "P", "结果解释与理论提炼", 8, "围绕结果含义、机制解释、理论抽象与研究发现提炼的讨论。"),
    ("A1.9", "P", "学术写作与成果表达", 9, "围绕论文写作、润色、摘要改写、图表表达与成果叙述的讨论。"),
    ("A1.10", "P", "发表与知识扩散", 10, "围绕投稿、返修、审稿回复、答辩与研究成果扩散的讨论。"),
    ("A2.1", "G", "科研项目管理", 11, "围绕课题推进、任务分配、项目计划与过程管理的讨论。"),
    ("A2.2", "G", "科研协作与沟通协调", 12, "围绕组会纪要、团队协作、跨成员沟通与协同安排的讨论。"),
    ("A2.3", "G", "科研资源配置与条件保障", 13, "围绕算力、实验条件、资料支持、订阅资源与资源调度的讨论。"),
    ("A2.4", "G", "数据治理与知识资产管理", 14, "围绕知识库整理、数据管理、文档归档与知识资产沉淀的讨论。"),
    ("A2.5", "G", "科研伦理、诚信与合规治理", 15, "围绕学术诚信、伦理风险、披露要求与合规规则的讨论。"),
    ("A2.6", "G", "科研评价", 16, "围绕科研评价标准、成果评价与能力判断的讨论。"),
    ("A2.7", "G", "出版与评审治理", 17, "围绕同行评审、出版治理、审稿规则与期刊要求的讨论。"),
    ("A2.8", "G", "科研传播、转化与社会扩散治理", 18, "围绕成果传播、知识转化、平台扩散与社会影响治理的讨论。"),
    ("A3.1", "T", "科研入门与学术适应", 19, "围绕科研起步、学术环境适应与研究路径入门的讨论。"),
    ("A3.2", "T", "研究方法学习", 20, "围绕研究方法理解、方法训练与方法选择学习的讨论。"),
    ("A3.3", "T", "科研工具与技术技能训练", 21, "围绕科研软件、编程、统计工具与技术技能训练的讨论。"),
    ("A3.4", "T", "学术阅读与写作能力训练", 22, "围绕学术阅读训练、写作训练与表达能力提升的讨论。"),
    ("A3.5", "T", "科研效率提升与习惯养成", 23, "围绕科研效率工具、节奏管理与研究习惯养成的讨论。"),
)

LEGITIMACY_DIRECTIONS = (
    ("B0", LEGITIMACY_LABELS["B0"], 0, "帖子主要是实践展示、经验分享或提问求助，未稳定表达支持、反对或条件限制。"),
    ("B1", LEGITIMACY_LABELS["B1"], 1, "明确将某种 AI 科研实践正当化、合理化，或认为其值得接受。"),
    ("B2", LEGITIMACY_LABELS["B2"], 2, "明确表示可以使用，但需要限定范围、人工审核或最终责任保留在人。"),
    ("B3", LEGITIMACY_LABELS["B3"], 3, "明确反对、否定或认为该实践不可接受。"),
    ("B4", LEGITIMACY_LABELS["B4"], 4, "同一文本同时出现支持与反对，或呈现冲突性、摇摆性判断。"),
    ("B5", LEGITIMACY_LABELS["B5"], 5, "看似在评价，但评价方向证据不足，无法稳定判断。"),
)

EVALUATION_CODES = tuple(
    (
        code_id,
        code_name,
        index,
        f"以“{code_name}”作为支持、限制或否定 AI 科研实践的明确评价标准。",
    )
    for index, (code_id, code_name) in enumerate(EVALUATION_LABELS.items(), start=1)
)

BOUNDARY_CONTENT_CODES = tuple(
    (
        code_id,
        code_name,
        index,
        f"围绕“{code_name}”明确划定 AI 使用边界。",
    )
    for index, (code_id, code_name) in enumerate(BOUNDARY_CONTENT_LABELS.items(), start=1)
)

BOUNDARY_MODE_CODES = tuple(
    (
        code_id,
        code_name,
        index,
        f"以“{code_name}”的方式表达边界规则或限制条件。",
    )
    for index, (code_id, code_name) in enumerate(BOUNDARY_MODE_LABELS.items(), start=1)
)

INTERACTION_ACTION_CODES = tuple(
    (
        code_id,
        code_name,
        index,
        f"在互动上下文中，以“{code_name}”的方式推进边界协商。",
    )
    for index, (code_id, code_name) in enumerate(INTERACTION_EVENT_CODES.items(), start=1)
)

INTERACTION_BASIS_LOOKUP = tuple(
    (
        code_id,
        code_name,
        index,
        f"在互动协商中，以“{code_name}”作为论证依据。",
    )
    for index, (code_id, code_name) in enumerate(INTERACTION_BASIS_CODES.items(), start=1)
)

INTERACTION_OUTCOME_CODES = (
    ("E4.1", "未形成共识", 1, "互动结束后未形成稳定共识。"),
    ("E4.2", "形成条件接受", 2, "互动结果是附条件地接受 AI 使用。"),
    ("E4.3", "形成明确限制", 3, "互动结果形成较明确的使用限制。"),
    ("E4.4", "形成明确禁止", 4, "互动结果形成明确禁止性结论。"),
    ("E4.5", "结果无法判断", 5, "互动存在，但结果不足以稳定判断。"),
)

LEGACY_WORKFLOW_TO_STAGE_CODE = {
    "选题与问题定义": "A1.1",
    "文献检索与综述": "A1.2",
    "研究设计与实验/方案制定": "A1.3",
    "数据获取与预处理": "A1.6",
    "编码/建模/统计分析": "A1.6",
    "论文写作/投稿/审稿回复": "A1.9",
    "学术交流与科研管理": "A2.2",
}

_STAGE_CODE_TO_DOMAIN_CODE = {
    stage_code: domain_code
    for stage_code, domain_code, _, _, _ in WORKFLOW_STAGES
}

_DOMAIN_CODE_TO_NAME = {
    domain_code: domain_name for _, domain_code, domain_name, _, _ in WORKFLOW_DOMAINS
}

_WORKFLOW_EXAMPLES = {
    "A1": "AI 已经嵌进从想课题、做分析到写论文的科研生产链条。",
    "A2": "AI 不只是做研究，还在重塑审稿、协作、管理和规范执行。",
    "A3": "很多研究生把 AI 当科研训练教练，用它学方法、学工具、练写作。",
    "A1.1": "博士生会先让 AI 帮自己拎一下课题方向和研究问题。",
    "A1.2": "我现在用 AI 先扫文献、做综述框架，再回头精读原文。",
    "A1.3": "让 AI 帮忙把研究问题拆成可执行的实验方案。",
    "A1.4": "用 AI 辅助抓取网页和整理研究数据源。",
    "A1.5": "让智能体自动跑仿真和重复实验流程。",
    "A1.6": "用 Claude Code 做统计分析和建模。",
    "A1.7": "拿 AI 去复现论文结果到底靠不靠谱。",
    "A1.8": "我会让 AI 先帮我解释回归结果再自己核查。",
    "A1.9": "用 AI 改摘要和论文结构已经成了日常写作流程。",
    "A1.10": "我用 AI 起草审稿回复，再自己逐条改。",
    "A2.1": "AI 帮我把课题时间线和任务看板排得很清楚。",
    "A2.2": "组会纪要、任务同步和协作提醒都交给 AI 做初稿。",
    "A2.3": "实验室开始讨论要不要给 AI 工具单独配经费和算力。",
    "A2.4": "用 AI 整理组里的文档库和数据资产，后面找资料快很多。",
    "A2.5": "学校开始要求说明论文里哪些部分用了生成式 AI。",
    "A2.6": "现在很多讨论其实是在评价，用 AI 做科研到底算不算合格能力。",
    "A2.7": "审稿和投稿环节能不能用 AI，期刊规则现在说法不一。",
    "A2.8": "研究成果经 AI 二次传播后，平台上又出现了新的治理争议。",
    "A3.1": "刚入学时我会先问 AI 怎么开始做科研和适应组里的节奏。",
    "A3.2": "把 AI 当方法助教，先解释概念再自己查教材。",
    "A3.3": "我用 AI 学 Python、R 和统计软件，训练效率高很多。",
    "A3.4": "拿 AI 练学术阅读和英文写作，比单纯背模板有效。",
    "A3.5": "AI 把我的科研日程、读文献节奏和写作习惯都带起来了。",
}

_LEGITIMACY_EXAMPLES = {
    "B0": "我用 AI 把文献初筛了一遍，后面再自己慢慢细读。",
    "B1": "这种重复劳动让 AI 处理，确实能把时间留给更重要的研究判断。",
    "B2": "可以用，但最后一定要自己核查，责任不能外包给 AI。",
    "B3": "如果连方法和分析都全交给 AI，这种做法就不合适了。",
    "B4": "它确实提效，但如果直接拿来写结论，我又觉得不太稳妥。",
    "B5": "这样做到底算不算合理，我现在也说不准。",
}

_EVALUATION_EXAMPLES = {
    "C1": "这种用法最大的优点就是快，能省下很多机械劳动时间。",
    "C2": "不会编程的人先靠 AI 补位，不代表就不做科研了。",
    "C3": "AI 给错了结论，最后答辩和署名承担责任的还是人。",
    "C4": "核心观点如果都是 AI 想出来的，那原创性就有问题。",
    "C5": "我们学科对 AI 写作有明确要求，不是想怎么用就怎么用。",
    "C6": "拿 AI 编文献和造数据，就是学术不端。",
    "C7": "研究问题和结论判断必须自己来，AI 只能做辅助。",
    "C8": "它给的分析过程说不清、复验不了，我就不敢直接用。",
    "C9": "资源多的人能买更强模型，这会不会让科研竞争更不公平。",
    "C10": "本科生一上来就让 AI 代做，方法能力根本练不出来。",
    "C11": "如果你用了 AI，就应该把使用范围和方式写清楚。",
    "C12": "这部分贡献到底该算作者自己的，还是工具辅助带来的？",
    "C13": "把敏感数据直接喂给模型，本身就有合规风险。",
    "C14": "这个环节必须要有领域判断，不能只看模型给的表面答案。",
}

_BOUNDARY_EXAMPLES = {
    "D1.1": "让 AI 润色和让 AI 代写，性质完全不一样。",
    "D1.2": "选题和结论必须自己做，AI 只能帮忙整理材料。",
    "D1.3": "用了 AI 也不能把责任甩给工具，最后还是作者自己负责。",
    "D1.4": "有的学科允许辅助写作，有的期刊明确要求披露，边界并不一样。",
    "D1.5": "一旦开始虚构引用和数据，这条线就踩到学术诚信边界了。",
    "D1.6": "科研训练最怕的是把本来该自己练的能力直接外包给 AI。",
    "D1.7": "哪些地方用了 AI 应不应该在论文里说明，大家争议很大。",
    "D1.8": "查文献可以用 AI，但研究结论和核心判断不能直接交给它。",
    "D1.9": "署名和贡献说明不能把工具使用写得含糊不清。",
    "D1.10": "模型可以先做草稿，但最终必须人工复核。",
    "D1.11": "组里的敏感资料和知识资产不能随便上传到外部模型。",
    "D2.1": "文献检索这种环节，用 AI 完全没问题。",
    "D2.2": "可以用，但前提是你自己做最终核查。",
    "D2.3": "这个环节我允许辅助，但会限制它只做初稿。",
    "D2.4": "结论生成绝对不能直接交给 AI。",
    "D2.5": "任何生成结果都必须有人工最终审核。",
    "D2.6": "作者必须承担最终责任，不能拿工具当挡箭牌。",
    "D2.7": "投稿时需要说明哪里用了 AI。",
    "D2.8": "高风险任务和低风险任务的用法要分开。",
    "D2.9": "不同科研环节的规则应该不一样。",
    "D2.10": "一旦影响原创性或结论生成，就要收紧边界。",
}

_INTERACTION_EXAMPLES = {
    "E2.1": "我同意楼主这个边界判断，至少文献初筛可以这么做。",
    "E2.2": "我不同意，这已经不是辅助而是替代了。",
    "E2.3": "我觉得原说法太绝对，应该改成只限于初稿整理。",
    "E2.4": "如果限定在公开数据和低风险任务里，我可以接受。",
    "E2.5": "重点不是能不能用，而是用了之后谁来负责。",
    "E2.6": "折中一点：查资料可以，核心判断不行。",
    "E2.7": "即便是初稿，也必须再加人工核查这条限制。",
    "E2.8": "如果只是做辅助提纲，我觉得没必要卡得这么死。",
    "E3.1": "这样做主要是效率高，不代表就越界。",
    "E3.2": "对不会编程的人来说，它确实是能力补充。",
    "E3.3": "最后担责的是作者，所以边界要按责任来划。",
    "E3.4": "只要影响原创性，我就反对。",
    "E3.5": "期刊规则已经写明了，这里不能随意放宽。",
    "E3.6": "一旦涉及学术不端，这个口子就不能开。",
    "E3.7": "结果不能复核的话，这种协商没有意义。",
    "E3.8": "资源差异会让这种做法对不同人不公平。",
    "E3.9": "学生如果太依赖 AI，训练价值就没了。",
    "E3.10": "审稿和投稿要求本身就是这里的关键依据。",
    "E3.11": "至少应该透明披露，不然别人无法判断边界。",
    "E3.12": "数据合规风险太高，这个使用方式得收紧。",
    "E4.1": "评论区吵到最后也没形成统一看法。",
    "E4.2": "大家最后基本同意：可以用，但要人工复核。",
    "E4.3": "最后形成的共识是只能用于文献初筛和润色。",
    "E4.4": "最后大家都认为这种做法应该禁止。",
    "E4.5": "上下文不完整，看不出最后协商到了哪一步。",
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
        raise ValueError(f"missing example for {code_group}: {code_id}") from exc


def workflow_domain_name(domain_code: str) -> str:
    try:
        return _DOMAIN_CODE_TO_NAME[domain_code]
    except KeyError as exc:
        raise KeyError(domain_code) from exc


def workflow_stage_name(stage_code: str) -> str:
    for code_id, _, stage_name, _, _ in WORKFLOW_STAGES:
        if code_id == stage_code:
            return stage_name
    raise KeyError(stage_code)


def workflow_stage_domain(stage_code: str) -> str:
    try:
        return _STAGE_CODE_TO_DOMAIN_CODE[stage_code]
    except KeyError as exc:
        raise KeyError(stage_code) from exc


def legacy_workflow_to_domain_code(legacy_label: str | None) -> str | None:
    stage_code = LEGACY_WORKFLOW_TO_STAGE_CODE.get((legacy_label or "").strip())
    if not stage_code:
        return None
    return workflow_stage_domain(stage_code)


def legacy_workflow_to_stage_name(legacy_label: str | None) -> str | None:
    stage_code = LEGACY_WORKFLOW_TO_STAGE_CODE.get((legacy_label or "").strip())
    if not stage_code:
        return None
    return workflow_stage_name(stage_code)


def iter_codebook_rows() -> Iterable[CodebookRow]:
    for code_id, _, domain_name, _, definition in WORKFLOW_DOMAINS:
        yield CodebookRow(
            code_id=code_id,
            code_group="workflow_domain",
            code_name=domain_name,
            definition=definition,
            include_rule="文本明确落在科研生产、科研治理或科研训练与能力建构三个一级维度之一。",
            exclude_rule="只有 AI 或只有科研，但无法落到任何科研工作流一级维度。",
            example=_require_example(
                _WORKFLOW_EXAMPLES,
                code_id=code_id,
                code_group="workflow_domain",
            ),
        )
    for code_id, _, stage_name, _, definition in WORKFLOW_STAGES:
        yield CodebookRow(
            code_id=code_id,
            code_group="workflow_stage",
            code_name=stage_name,
            definition=definition,
            include_rule="文本明确指向该科研工作流二级环节；允许多重编码。",
            exclude_rule="只泛谈 AI 很强或科研会变化，无法定位到具体环节。",
            example=_require_example(
                _WORKFLOW_EXAMPLES,
                code_id=code_id,
                code_group="workflow_stage",
            ),
        )
    for code_id, code_name, _, definition in LEGITIMACY_DIRECTIONS:
        yield CodebookRow(
            code_id=code_id,
            code_group="legitimacy_direction",
            code_name=code_name,
            definition=definition,
            include_rule="文本明确对 AI 科研实践做出正当化、条件接受、否定或规范适配性判断。",
            exclude_rule="只展示实践，不存在评价取向或判断方向。",
            example=_require_example(
                _LEGITIMACY_EXAMPLES,
                code_id=code_id,
                code_group="legitimacy_direction",
            ),
        )
    for code_id, code_name, _, definition in EVALUATION_CODES:
        yield CodebookRow(
            code_id=code_id,
            code_group="evaluation_standard",
            code_name=code_name,
            definition=definition,
            include_rule="文本明确说明判断 AI 科研实践合理或不合理的依据。",
            exclude_rule="只有情绪态度，没有可回到原文的评价标准。",
            example=_require_example(
                _EVALUATION_EXAMPLES,
                code_id=code_id,
                code_group="evaluation_standard",
            ),
        )
    for code_id, code_name, _, definition in BOUNDARY_CONTENT_CODES:
        yield CodebookRow(
            code_id=code_id,
            code_group="boundary_content",
            code_name=code_name,
            definition=definition,
            include_rule="文本明确在划定 AI 使用范围、责任、披露或规范边界。",
            exclude_rule="只有风险感受或好恶表达，没有划界动作。",
            example=_require_example(
                _BOUNDARY_EXAMPLES,
                code_id=code_id,
                code_group="boundary_content",
            ),
        )
    for code_id, code_name, _, definition in BOUNDARY_MODE_CODES:
        yield CodebookRow(
            code_id=code_id,
            code_group="boundary_mode",
            code_name=code_name,
            definition=definition,
            include_rule="文本明确说明边界是允许、限制、禁止、人工审核、责任保留或按任务区分等表达方式。",
            exclude_rule="只表达一般态度，没有实际划界方式。",
            example=_require_example(
                _BOUNDARY_EXAMPLES,
                code_id=code_id,
                code_group="boundary_mode",
            ),
        )
    for code_id, code_name, _, definition in INTERACTION_ACTION_CODES:
        yield CodebookRow(
            code_id=code_id,
            code_group="interaction_action",
            code_name=code_name,
            definition=definition,
            include_rule="存在明确 thread / reply / quoted_post 等互动上下文，并能识别具体协商动作。",
            exclude_rule="无上下文，或只有单帖边界表达。",
            example=_require_example(
                _INTERACTION_EXAMPLES,
                code_id=code_id,
                code_group="interaction_action",
            ),
        )
    for code_id, code_name, _, definition in INTERACTION_BASIS_LOOKUP:
        yield CodebookRow(
            code_id=code_id,
            code_group="interaction_basis",
            code_name=code_name,
            definition=definition,
            include_rule="互动协商中明确调用该依据来支持、限制或否定边界主张。",
            exclude_rule="互动存在，但论证依据无法从原文证据稳定回溯。",
            example=_require_example(
                _INTERACTION_EXAMPLES,
                code_id=code_id,
                code_group="interaction_basis",
            ),
        )
    for code_id, code_name, _, definition in INTERACTION_OUTCOME_CODES:
        yield CodebookRow(
            code_id=code_id,
            code_group="interaction_outcome",
            code_name=code_name,
            definition=definition,
            include_rule="互动上下文足以判断边界协商的暂时结果。",
            exclude_rule="上下文不完整，无法判断是否形成结果。",
            example=_require_example(
                _INTERACTION_EXAMPLES,
                code_id=code_id,
                code_group="interaction_outcome",
            ),
        )


def iter_workflow_domain_lookup_rows() -> Iterable[tuple[str, str, int, str]]:
    for _, domain_code, domain_name, order_index, definition in WORKFLOW_DOMAINS:
        yield domain_code, domain_name, order_index, definition


def iter_workflow_lookup_rows() -> Iterable[tuple[str, str, str, int, str]]:
    for stage_code, domain_code, stage_name, order_index, definition in WORKFLOW_STAGES:
        yield stage_code, stage_name, domain_code, order_index, definition


def iter_legitimacy_lookup_rows() -> Iterable[tuple[str, str, int, str]]:
    for code_id, code_name, order_index, definition in LEGITIMACY_DIRECTIONS:
        yield code_id, code_name, order_index, definition
