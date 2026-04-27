from __future__ import annotations

DECISION_VALUES = ("纳入", "剔除", "待复核")
CONTEXT_AVAILABLE_VALUES = ("是", "否")
CONTEXT_USED_VALUES = ("none", "thread", "quoted_post", "reply_chain", "user_provided_context")
BOUNDARY_PRESENT_VALUES = ("是", "否")
INTERACTION_EVENT_VALUES = ("是", "否", "无法判断", "不适用")
INTERACTION_ROLE_VALUES = (
    "original_poster",
    "replier",
    "quoter",
    "third_party_commentator",
    "unclear",
)
MULTI_LABEL_VALUES = ("是", "否")
AMBIGUITY_VALUES = ("是", "否")
CONFIDENCE_VALUES = ("高", "中", "低")
API_ASSISTANCE_VALUES = ("是", "否")
API_CONFIDENCE_VALUES = ("高", "中", "低", "无", "不可用")
MECHANISM_ELIGIBILITY_VALUES = ("是", "否", "待定")
REVIEW_STATUS_VALUES = ("unreviewed", "reviewed", "revised")
RECORD_TYPE_VALUES = ("post", "comment", "reply")

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

WORKFLOW_DIMENSION_LABELS = {
    "A1": "科研生产工作流",
    "A2": "科研治理工作流",
    "A3": "科研训练与能力建构",
}

LEGITIMACY_LABELS = {
    "B0": "未表达评价",
    "B1": "正面接受/正当化",
    "B2": "有条件接受",
    "B3": "质疑/否定",
    "B4": "混合/冲突性评价",
    "B5": "无法判断",
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
    "C10": "训练价值/能力养成",
    "C11": "披露/透明性",
    "C12": "署名/贡献归属",
    "C13": "数据隐私/知识产权/合规风险",
    "C14": "专业判断/领域知识门槛",
}

BOUNDARY_CONTENT_LABELS = {
    "D1.1": "合理辅助 vs 不可接受替代",
    "D1.2": "人机分工边界",
    "D1.3": "科研主体责任边界",
    "D1.4": "科研规范边界",
    "D1.5": "学术诚信边界",
    "D1.6": "训练与学习边界",
    "D1.7": "披露/说明使用边界",
    "D1.8": "不同科研环节的差异化边界",
    "D1.9": "署名与贡献边界",
    "D1.10": "验证/复核边界",
    "D1.11": "数据/隐私/知识资产使用边界",
}

BOUNDARY_MODE_LABELS = {
    "D2.1": "明确允许",
    "D2.2": "有条件允许",
    "D2.3": "明确限制",
    "D2.4": "明确禁止",
    "D2.5": "要求人类最终审核",
    "D2.6": "要求人类承担最终责任",
    "D2.7": "要求披露/说明使用情况",
    "D2.8": "按任务风险区分",
    "D2.9": "按科研环节区分",
    "D2.10": "按是否影响原创性/结论生成区分",
}

INTERACTION_EVENT_CODES = {
    "E2.1": "支持原边界主张",
    "E2.2": "反对原边界主张",
    "E2.3": "修正原边界主张",
    "E2.4": "细化条件",
    "E2.5": "转移争点",
    "E2.6": "折中/调和",
    "E2.7": "强化限制",
    "E2.8": "放宽限制",
}

INTERACTION_BASIS_CODES = {
    "E3.1": "效率",
    "E3.2": "能力补充",
    "E3.3": "责任归属",
    "E3.4": "原创性",
    "E3.5": "科研规范",
    "E3.6": "学术诚信",
    "E3.7": "可靠性/可验证性",
    "E3.8": "公平性",
    "E3.9": "训练价值",
    "E3.10": "发表/评审要求",
    "E3.11": "披露/透明性",
    "E3.12": "数据/合规风险",
}

INTERACTION_OUTCOME_VALUES = ("E4.1", "E4.2", "E4.3", "E4.4", "E4.5")

DECISION_REASON_CODES = {
    "R1": "未明确提及 AI/AI工具",
    "R2": "无具体科研工作流环节",
    "R3": "仅泛论 AI 与科研",
    "R4": "非科研场景（学习/办公/求职/商业/一般开发）",
    "R5": "上下文不足",
    "R6": "科研环节不明确",
    "R7": "评价对象不明确",
    "R8": "广告/产品发布/新闻/趋势信息",
    "R9": "纯链接/纯转发/纯口号/纯情绪表达",
    "R10": "重复帖/同源转发",
    "R11": "可能相关但证据不足，建议复核",
    "R12": "其他",
}

ALL_CODE_LABELS = (
    WORKFLOW_STAGE_LABELS
    | LEGITIMACY_LABELS
    | EVALUATION_LABELS
    | BOUNDARY_CONTENT_LABELS
    | BOUNDARY_MODE_LABELS
    | INTERACTION_EVENT_CODES
    | INTERACTION_BASIS_CODES
)

WORKFLOW_CODE_SET = set(WORKFLOW_STAGE_LABELS)
LEGITIMACY_CODE_SET = set(LEGITIMACY_LABELS)
EVALUATION_CODE_SET = set(EVALUATION_LABELS)
BOUNDARY_CONTENT_CODE_SET = set(BOUNDARY_CONTENT_LABELS)
BOUNDARY_MODE_CODE_SET = set(BOUNDARY_MODE_LABELS)
INTERACTION_EVENT_CODE_SET = set(INTERACTION_EVENT_CODES)
INTERACTION_BASIS_CODE_SET = set(INTERACTION_BASIS_CODES)

INTERNAL_METADATA_FIELDS = {
    "record_type",
    "record_id",
    "review_phase",
    "run_id",
    "reviewer",
    "review_date",
    "model",
    "source_phase",
    "system_metadata",
}

RECORD_ID_FIELD = {
    "post": "post_id",
    "comment": "comment_id",
    "reply": "comment_id",
}

OLD_BOUNDARY_TO_CONTENT_CODE = {
    "D1": "D1.1",
    "D2": "D1.2",
    "D3": "D1.3",
    "D4": "D1.4",
    "D5": "D1.5",
    "D6": "D1.6",
    "D7": "D1.7",
    "D8": "D1.8",
}
