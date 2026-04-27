from __future__ import annotations

import json
from typing import Any

from ai4s_legitimacy.config.research_baseline import (
    has_multiple_codings,
    supports_research_question,
)

from ._review_db import ensure_json_list, first_nonempty

AI_TERMS = (
    "ai",
    "chatgpt",
    "claude",
    "gemini",
    "deepseek",
    "copilot",
    "cursor",
    "kimi",
    "豆包",
    "通义",
    "元宝",
    "智能体",
    "大模型",
    "生成式",
)
PRACTICE_TERMS = (
    "我用",
    "用了",
    "用 ai",
    "workflow",
    "提示词",
    "让 ai",
    "帮我",
    "自动",
    "生成",
    "整理",
    "分析",
    "建模",
    "复现",
    "投稿",
    "审稿",
)
WORKFLOW_RULES = {
    "A1.1": ("选题", "研究问题", "idea", "课题", "创新点", "问题定义"),
    "A1.2": ("文献", "综述", "检索", "citation", "参考文献", "paper search"),
    "A1.3": ("研究设计", "实验设计", "方案", "方法设计", "protocol"),
    "A1.4": ("数据获取", "抓取", "爬虫", "收集数据", "采集数据", "问卷发放"),
    "A1.5": ("实验", "仿真", "simulation", "自动跑", "执行实验", "agent 跑"),
    "A1.6": ("数据清洗", "统计", "建模", "回归", "分析", "python", "r语言", "stata", "代码"),
    "A1.7": ("复现", "验证", "benchmark", "可重复", "reproduce"),
    "A1.8": ("解释结果", "机制", "理论", "结果解释", "讨论结果"),
    "A1.9": ("写论文", "写作", "润色", "摘要", "降ai味", "改论文", "综述写作"),
    "A1.10": ("投稿", "返修", "答辩", "审稿回复", "发表"),
    "A2.1": ("项目管理", "时间线", "任务看板", "进度管理"),
    "A2.2": ("组会", "协作", "沟通", "团队同步", "纪要"),
    "A2.3": ("算力", "经费", "资源", "订阅", "条件保障"),
    "A2.4": ("知识库", "文档库", "数据治理", "引用管理", "资产管理"),
    "A2.5": ("伦理", "合规", "学术不端", "披露", "声明 ai", "诚信"),
    "A2.6": ("科研评价", "评价标准", "是否合格", "能力判断"),
    "A2.7": ("审稿人", "peer review", "期刊要求", "出版规则", "评审"),
    "A2.8": ("传播", "转化", "平台扩散", "社会影响"),
    "A3.1": ("科研入门", "研一", "新生", "小白科研", "学术适应"),
    "A3.2": ("研究方法", "方法学习", "因果推断", "方法训练"),
    "A3.3": ("学 python", "学 r", "工具训练", "技术技能", "copilot 替代"),
    "A3.4": ("文献阅读", "学术阅读", "写作训练", "英文写作"),
    "A3.5": ("效率", "习惯", "节奏", "生产力", "workflow"),
}
LEGITIMACY_RULES = {
    "B1": ("合理", "必要", "高效", "提效", "有帮助", "值得用"),
    "B2": ("但是", "但", "只能", "辅助", "不能替代", "人工审核", "自己核查", "责任还在"),
    "B3": ("不合适", "不可接受", "别用", "风险", "越界", "学术不端", "胡说八道", "不敢"),
    "B4": ("规范", "合规", "期刊要求", "披露", "审稿要求", "伦理"),
}
EVALUATION_RULES = {
    "C1": ("效率", "省时间", "高效", "提效"),
    "C2": ("补充", "补位", "降低门槛", "辅助能力"),
    "C3": ("责任", "担责", "负责", "核查"),
    "C4": ("原创", "原创性", "自己的研究"),
    "C5": ("规范", "规则", "共同体", "期刊要求"),
    "C6": ("诚信", "不端", "造假", "虚构", "编文献"),
    "C7": ("人来做", "AI 只能", "不能替代", "人机分工"),
    "C8": ("可靠", "验证", "复现", "可追溯", "可核查"),
    "C9": ("公平", "不公平", "资源差异"),
    "C10": ("训练", "能力养成", "学习价值", "学不到"),
}
BOUNDARY_RULES = {
    "D1": ("辅助", "替代", "代写", "代做", "越界"),
    "D2": ("人机分工", "必须自己", "该由人做", "AI 做什么"),
    "D3": ("责任", "作者负责", "导师负责", "审稿人负责"),
    "D4": ("规范边界", "学科规范", "期刊要求", "合规"),
    "D5": ("诚信边界", "学术不端", "虚构", "造假"),
    "D6": ("训练边界", "训练价值", "学习边界", "不能外包"),
    "D7": ("披露", "说明", "公开声明"),
    "D8": ("不同环节", "查文献可以", "结论不行", "分环节"),
}
WORKFLOW_DOMAIN_LABELS = {
    "A1": "科研生产工作流",
    "A2": "科研治理工作流",
    "A3": "科研训练与能力建构",
}
WORKFLOW_STAGE_LABELS = {
    "A1.1": "研究构思与问题定义",
    "A1.2": "文献调研与知识整合",
    "A1.3": "研究设计与方案制定",
    "A1.4": "数据获取",
    "A1.5": "实验实施与仿真执行",
    "A1.6": "数据处理与分析建模",
    "A1.7": "结果验证与论文复现",
    "A1.8": "结果解释与理论提炼",
    "A1.9": "学术写作与成果表达",
    "A1.10": "发表与知识扩散",
    "A2.1": "科研项目管理",
    "A2.2": "科研协作与沟通协调",
    "A2.3": "科研资源配置与条件保障",
    "A2.4": "数据治理与知识资产管理",
    "A2.5": "科研伦理、诚信与合规治理",
    "A2.6": "科研评价",
    "A2.7": "出版与评审治理",
    "A2.8": "科研传播、转化与社会扩散治理",
    "A3.1": "科研入门与学术适应",
    "A3.2": "研究方法学习",
    "A3.3": "科研工具与技术技能训练",
    "A3.4": "学术阅读与写作能力训练",
    "A3.5": "科研效率提升与习惯养成",
}
LEGITIMACY_LABELS = {
    "B1": "正面正当化",
    "B2": "有条件接受",
    "B3": "质疑/否定",
    "B4": "规范适配性判断",
}
EVALUATION_LABELS = {
    "C1": "效率",
    "C2": "能力补充",
    "C3": "责任归属",
    "C4": "原创性",
    "C5": "科研规范",
    "C6": "学术诚信",
    "C7": "人机分工",
    "C8": "结果可靠性/可验证性",
    "C9": "公平性",
    "C10": "训练价值/能力养成价值",
}
BOUNDARY_LABELS = {
    "D1": "合理辅助 vs 不可接受替代",
    "D2": "人机分工边界",
    "D3": "科研主体责任边界",
    "D4": "科研规范边界",
    "D5": "学术诚信边界",
    "D6": "训练与学习边界",
    "D7": "可公开披露/需说明的使用边界",
    "D8": "不同科研环节的差异化边界",
}


def normalize_text(*parts: Any) -> str:
    return " ".join(str(part or "").strip() for part in parts).strip().lower()


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_low_information(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.count("#") >= 4 and len(stripped.replace("#", "").replace("[话题]", "").strip()) < 24:
        return True
    return len(stripped) < 18


def infer_codes(text: str, rules: dict[str, tuple[str, ...]]) -> list[str]:
    normalized_text = normalize_text(text)
    return [code for code, keywords in rules.items() if contains_any(normalized_text, keywords)]


def first_sentence(text: str) -> str:
    stripped = str(text or "").strip()
    if not stripped:
        return ""
    for token in ("。", "\n", "!", "！", "?", "？"):
        if token in stripped:
            head = stripped.split(token, 1)[0].strip()
            if head:
                return head
    return stripped[:120].strip()


def domain_codes_from_workflow(workflow_codes: list[str]) -> list[str]:
    domains: list[str] = []
    for code in workflow_codes:
        domain = code.split(".", 1)[0]
        if domain in WORKFLOW_DOMAIN_LABELS and domain not in domains:
            domains.append(domain)
    return domains


def practice_signal(text: str) -> bool:
    return contains_any(normalize_text(text), PRACTICE_TERMS)


def ai_signal(text: str) -> bool:
    return contains_any(normalize_text(text), AI_TERMS)


def manual_or_bootstrap_codes(
    payload: dict[str, Any] | None,
    *,
    text: str,
) -> tuple[list[str], list[str], list[str], list[str]]:
    if payload:
        workflow_codes = ensure_json_list(payload.get("workflow_codes"))
        legitimacy_codes = ensure_json_list(payload.get("legitimacy_codes"))
        evaluation_codes = ensure_json_list(payload.get("evaluation_codes"))
        boundary_codes = ensure_json_list(payload.get("boundary_codes"))
        if any((workflow_codes, legitimacy_codes, evaluation_codes, boundary_codes)):
            return (
                [str(item) for item in workflow_codes],
                [str(item) for item in legitimacy_codes],
                [str(item) for item in evaluation_codes],
                [str(item) for item in boundary_codes],
            )
    return (
        infer_codes(text, WORKFLOW_RULES),
        infer_codes(text, LEGITIMACY_RULES),
        infer_codes(text, EVALUATION_RULES),
        infer_codes(text, BOUNDARY_RULES),
    )


def bootstrap_inclusion_decision(
    *,
    text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    evaluation_codes: list[str],
    boundary_codes: list[str],
    historical_status: str,
    suggestion_status: str,
) -> str:
    if is_low_information(text):
        if suggestion_status == "true" and workflow_codes:
            return "纳入"
        return "剔除"
    if not ai_signal(text):
        return "剔除"
    if not workflow_codes:
        return "剔除"
    if not supports_research_question(workflow_codes, legitimacy_codes, boundary_codes):
        return "剔除"
    if practice_signal(text) or legitimacy_codes or evaluation_codes or boundary_codes:
        return "纳入"
    if historical_status == "true":
        return "纳入"
    if suggestion_status == "true":
        return "纳入"
    return "剔除"


def bootstrap_reason(
    *,
    inclusion_decision: str,
    text: str,
    historical_reason: str,
    suggestion_reason: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    boundary_codes: list[str],
) -> str:
    explicit_reason = first_nonempty(historical_reason, suggestion_reason, default="")
    if explicit_reason:
        return str(explicit_reason)
    if inclusion_decision == "纳入":
        if legitimacy_codes or boundary_codes:
            return "帖子明确涉及 AI 进入具体科研环节，并且包含规范判断或边界协商。"
        if workflow_codes:
            return "帖子明确展示了 AI 介入科研具体环节的做法，满足工作流纳入标准。"
    if is_low_information(text):
        return "正文信息过薄，无法支持识别具体科研环节、合法性评价或边界协商。"
    return "帖子缺少可回到原文证据的具体科研实践、评价判断或边界信息，按规则剔除。"


def structured_record(
    *,
    record_type: str,
    record_id: str,
    source_phase: str,
    title: str,
    summary: str,
    inclusion_decision: str,
    reason: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    evaluation_codes: list[str],
    boundary_codes: list[str],
    ambiguity_note: str,
    followup_check: str,
    historical_status: str,
    suggestion_status: str,
) -> dict[str, Any]:
    workflow_domain_labels = [
        WORKFLOW_DOMAIN_LABELS[domain]
        for domain in domain_codes_from_workflow(workflow_codes)
        if domain in WORKFLOW_DOMAIN_LABELS
    ]
    workflow_stage_labels = [
        WORKFLOW_STAGE_LABELS[code] for code in workflow_codes if code in WORKFLOW_STAGE_LABELS
    ]
    legitimacy_labels = [
        LEGITIMACY_LABELS[code] for code in legitimacy_codes if code in LEGITIMACY_LABELS
    ]
    evaluation_labels = [
        EVALUATION_LABELS[code] for code in evaluation_codes if code in EVALUATION_LABELS
    ]
    boundary_labels = [BOUNDARY_LABELS[code] for code in boundary_codes if code in BOUNDARY_LABELS]
    return {
        "record_type": record_type,
        "record_id": record_id,
        "source_phase": source_phase,
        "historical_sample_status": historical_status,
        "deepseek_suggested_sample_status": suggestion_status or None,
        "inclusion_decision": inclusion_decision,
        "reason": reason,
        "summary": summary,
        "workflow_codes": workflow_codes,
        "legitimacy_codes": legitimacy_codes,
        "evaluation_codes": evaluation_codes,
        "boundary_codes": boundary_codes,
        "ambiguity_note": ambiguity_note,
        "followup_check": followup_check,
        "是否纳入": inclusion_decision,
        "纳入或剔除理由": reason,
        "帖子主题摘要": summary or title,
        "工作流维度": {
            "一级维度": workflow_domain_labels,
            "二级环节": workflow_stage_labels,
        },
        "合法性评价": {
            "评价方向": legitimacy_labels,
            "评价依据": evaluation_labels,
        },
        "边界协商": {
            "是否涉及": bool(boundary_codes),
            "涉及哪类边界": boundary_labels,
        },
        "备注": {
            "是否多重编码": has_multiple_codings(
                workflow_codes,
                legitimacy_codes,
                evaluation_codes,
                boundary_codes,
            ),
            "是否存在歧义": bool(ambiguity_note),
            "建议后续复核点": followup_check,
        },
    }


def json_list(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return parsed
        return [stripped]
    return [value]
