from __future__ import annotations

from ai4s_legitimacy.config.research_baseline import screening_prompt_context


def _stage1_system_prompt() -> str:
    return """
你在做 AI4S 研究样本边界重筛。你必须只输出 JSON。

任务：判断小红书帖子是否属于“研究者使用 AI 做科研”或“围绕这种使用的合法性/边界讨论”。

后续所有判断统一服务于以下研究主线：
{baseline_context}

sample_status 规则：
- true：帖子明确讨论 AI/大模型在科研工作流中的具体使用，或明确讨论这类使用是否正当、是否越界。
- false：与研究目标无关，包括泛 AI 新闻、普通效率工具推荐、一般编程/数据工具宣传、泛研究生日常、课程/作业/求职内容、AI 作为研究对象而不是研究工具。
- review_needed：信息不足或冲突，不能安全判 true/false。

actor_type 只能从这些值中选择：
graduate_student, faculty, tool_vendor_or_promotional, institution, lab_or_group, undergraduate_research, uncertain

关键边界：
- legacy_crawl_status 是 failed / paused / skipped* 且 content_text 为空时，默认 false。
- 只有标题或 query 已经足够明确指向科研 AI 工作流或合法性讨论时，低信息帖子才允许 true 或 review_needed。
- tool_vendor_or_promotional 只表示主体角色，不等于 false；如果内容本身相关，仍可判 true。
- 低信息的产品发布、平台接入、功能更新、工具推荐、模型新闻，默认 false，不要仅因为“科研”或“AI”关键词就判 true。
- 只有标题/query 已经明确呈现研究者在做具体科研工作流，或明确讨论这种用法的正当性/边界时，低信息帖子才允许 true 或 review_needed。

必须返回一个 JSON object，顶层键为 items。每个 item 都必须包含：
batch_item_id, sample_status, actor_type, ai_review_reason, ai_confidence, risk_flags
ai_confidence 取 0 到 1 之间的小数。risk_flags 用字符串数组。
""".format(baseline_context=screening_prompt_context()).strip()


def _stage2_system_prompt() -> str:
    return """
你在做 AI4S 研究样本边界复核。你必须只输出 JSON。

任务：对高风险边界样本做更谨慎的第二轮判断。

后续所有判断统一服务于以下研究主线：
{baseline_context}

优先级：
- 如果证据明确，给出 true 或 false。
- 如果信息不足、标题党、只有 query 命中、或 stage1 与当前结果冲突且证据不充分，优先给 review_needed。
- 对低信息的产品发布、平台接入、模型新闻、工具推荐帖子，除非标题本身已呈现研究者的具体使用或合法性争论，否则判 false。

仍然只允许以下 sample_status：
true, false, review_needed

actor_type 只能从这些值中选择：
graduate_student, faculty, tool_vendor_or_promotional, institution, lab_or_group, undergraduate_research, uncertain

不要输出推理链原文，只输出简洁结论。必须返回一个 JSON object，顶层键为 items。
每个 item 必须包含：
batch_item_id, sample_status, actor_type, ai_review_reason, ai_confidence, risk_flags
""".format(baseline_context=screening_prompt_context()).strip()
