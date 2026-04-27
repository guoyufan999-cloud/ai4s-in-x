from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import REBASELINE_SUGGESTIONS_DIR
from ai4s_legitimacy.config.research_baseline import (
    has_multiple_codings,
    supports_research_question,
)
from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

from ._canonical_review import canonicalize_review_row
from ._review_db import ensure_json_list, first_nonempty, load_reviewed_payloads
from .canonical_schema import decision_to_sample_status, validate_canonical_row
from .review_queue import _load_suggestion_index


TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports" / "review_v2"
POST_MASTER_PATH = TABLES_DIR / "post_review_v2_master.jsonl"
COMMENT_MASTER_PATH = TABLES_DIR / "comment_review_v2_master.jsonl"
DELTA_REPORT_PATH = REPORTS_DIR / "post_review_v2_delta_report.json"

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


def _normalize_text(*parts: Any) -> str:
    return " ".join(str(part or "").strip() for part in parts).strip().lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _is_low_information(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.count("#") >= 4 and len(stripped.replace("#", "").replace("[话题]", "").strip()) < 24:
        return True
    return len(stripped) < 18


def _infer_codes(text: str, rules: dict[str, tuple[str, ...]]) -> list[str]:
    normalized_text = _normalize_text(text)
    return [code for code, keywords in rules.items() if _contains_any(normalized_text, keywords)]


def _first_sentence(text: str) -> str:
    stripped = str(text or "").strip()
    if not stripped:
        return ""
    for token in ("。", "\n", "!", "！", "?", "？"):
        if token in stripped:
            head = stripped.split(token, 1)[0].strip()
            if head:
                return head
    return stripped[:120].strip()


def _domain_codes_from_workflow(workflow_codes: list[str]) -> list[str]:
    domains = []
    for code in workflow_codes:
        domain = code.split(".", 1)[0]
        if domain in WORKFLOW_DOMAIN_LABELS and domain not in domains:
            domains.append(domain)
    return domains


def _practice_signal(text: str) -> bool:
    return _contains_any(_normalize_text(text), PRACTICE_TERMS)


def _ai_signal(text: str) -> bool:
    return _contains_any(_normalize_text(text), AI_TERMS)


def _manual_or_bootstrap_codes(
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
        _infer_codes(text, WORKFLOW_RULES),
        _infer_codes(text, LEGITIMACY_RULES),
        _infer_codes(text, EVALUATION_RULES),
        _infer_codes(text, BOUNDARY_RULES),
    )


def _bootstrap_inclusion_decision(
    *,
    text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    evaluation_codes: list[str],
    boundary_codes: list[str],
    historical_status: str,
    suggestion_status: str,
) -> str:
    if _is_low_information(text):
        if suggestion_status == "true" and workflow_codes:
            return "纳入"
        return "剔除"
    if not _ai_signal(text):
        return "剔除"
    if not workflow_codes:
        return "剔除"
    if not supports_research_question(workflow_codes, legitimacy_codes, boundary_codes):
        return "剔除"
    if _practice_signal(text) or legitimacy_codes or evaluation_codes or boundary_codes:
        return "纳入"
    if historical_status == "true":
        return "纳入"
    if suggestion_status == "true":
        return "纳入"
    return "剔除"


def _bootstrap_reason(
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
    if _is_low_information(text):
        return "正文信息过薄，无法支持识别具体科研环节、合法性评价或边界协商。"
    return "帖子缺少可回到原文证据的具体科研实践、评价判断或边界信息，按规则剔除。"


def _structured_record(
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
        for domain in _domain_codes_from_workflow(workflow_codes)
        if domain in WORKFLOW_DOMAIN_LABELS
    ]
    workflow_stage_labels = [
        WORKFLOW_STAGE_LABELS[code]
        for code in workflow_codes
        if code in WORKFLOW_STAGE_LABELS
    ]
    legitimacy_labels = [
        LEGITIMACY_LABELS[code]
        for code in legitimacy_codes
        if code in LEGITIMACY_LABELS
    ]
    evaluation_labels = [
        EVALUATION_LABELS[code]
        for code in evaluation_codes
        if code in EVALUATION_LABELS
    ]
    boundary_labels = [
        BOUNDARY_LABELS[code]
        for code in boundary_codes
        if code in BOUNDARY_LABELS
    ]
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


def _json_list(value: Any) -> list[Any]:
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


def _canonical_record_from_source(
    *,
    record_type: str,
    base_row: dict[str, Any],
    review_phase: str,
    reviewed_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if reviewed_payload:
        try:
            canonical = validate_canonical_row(reviewed_payload)
        except ValueError:
            canonical = canonicalize_review_row(
                reviewed_payload,
                base_row=base_row,
                review_phase=review_phase,
            )
        if canonical.get("review_status") == "unreviewed":
            canonical["review_status"] = "reviewed"
        return validate_canonical_row(canonical)

    seed = dict(base_row)
    seed.update(
        {
            "record_type": record_type,
            "record_id": str(
                base_row["post_id"] if record_type == "post" else base_row["comment_id"]
            ),
            "review_phase": f"{review_phase}_bootstrap",
            "review_status": str(base_row.get("review_status") or "unreviewed"),
        }
    )
    if str(base_row.get("decision") or "").strip():
        seed["decision"] = str(base_row.get("decision") or "").strip()
    if base_row.get("decision_reason_json") not in (None, ""):
        seed["decision_reason"] = _json_list(base_row.get("decision_reason_json"))
    canonical = canonicalize_review_row(
        seed,
        base_row=base_row,
        review_phase=f"{review_phase}_bootstrap",
    )
    return validate_canonical_row(canonical)


def _build_post_records(connection, suggestions_dir: Path) -> list[dict[str, Any]]:
    reviewed_payloads = load_reviewed_payloads(
        connection,
        review_phase="post_review_v2",
        record_type="post",
    )
    rescreen_payloads = load_reviewed_payloads(
        connection,
        review_phase="rescreen_posts",
        record_type="post",
    )
    suggestion_index = _load_suggestion_index(suggestions_dir)
    records: list[dict[str, Any]] = []
    for row in connection.execute("SELECT * FROM posts ORDER BY post_date, post_id").fetchall():
        post = dict(row)
        post_id = str(post["post_id"])
        canonical = _canonical_record_from_source(
            record_type="post",
            base_row=post,
            review_phase="post_review_v2",
            reviewed_payload=reviewed_payloads.get(post_id),
        )
        canonical["historical_sample_status"] = str(post.get("sample_status") or "")
        if post.get("post_date") not in (None, ""):
            canonical["post_date"] = post.get("post_date")
        if post.get("title") not in (None, ""):
            canonical["title"] = post.get("title")
        if post_id in rescreen_payloads:
            canonical["historical_rescreen"] = rescreen_payloads[post_id]
        if post_id in suggestion_index:
            canonical["deepseek_suggestion"] = suggestion_index[post_id]
        records.append(canonical)
    return records


def _build_comment_records(
    connection,
    *,
    included_post_ids: set[str],
) -> list[dict[str, Any]]:
    reviewed_payloads = load_reviewed_payloads(
        connection,
        review_phase="comment_review_v2",
        record_type="comment",
    )
    records: list[dict[str, Any]] = []
    for row in connection.execute("SELECT * FROM comments ORDER BY comment_date, comment_id").fetchall():
        comment = dict(row)
        post_id = str(comment["post_id"])
        if post_id not in included_post_ids:
            continue
        comment_id = str(comment["comment_id"])
        canonical = _canonical_record_from_source(
            record_type="reply" if str(comment.get("is_reply") or "") in {"1", "true"} else "comment",
            base_row=comment,
            review_phase="comment_review_v2",
            reviewed_payload=reviewed_payloads.get(comment_id),
        )
        canonical["comment_id"] = comment_id
        canonical["post_id"] = post_id
        if comment.get("comment_date") not in (None, ""):
            canonical["comment_date"] = comment.get("comment_date")
        records.append(canonical)
    return records


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _build_delta_report(post_records: list[dict[str, Any]]) -> dict[str, Any]:
    changes: dict[str, list[dict[str, Any]]] = {
        "old_true_to_new_false": [],
        "old_false_to_new_true": [],
        "old_review_needed_to_new_true": [],
    }
    decision_counts = {"纳入": 0, "剔除": 0, "待复核": 0}
    claim_unit_distribution: dict[str, int] = {}
    for row in post_records:
        decision = str(row["decision"])
        old_status = str(row.get("historical_sample_status") or "")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        claim_units = row.get("claim_units") or []
        claim_unit_distribution[str(len(claim_units))] = claim_unit_distribution.get(
            str(len(claim_units)),
            0,
        ) + 1
        entry = {
            "post_id": row["post_id"],
            "title": row.get("theme_summary") or row.get("title"),
            "old_status": old_status,
            "new_status": decision_to_sample_status(decision),
            "reason": " | ".join(row.get("decision_reason") or []),
        }
        if old_status == "true" and decision == "剔除":
            changes["old_true_to_new_false"].append(entry)
        elif old_status == "false" and decision == "纳入":
            changes["old_false_to_new_true"].append(entry)
        elif old_status == "review_needed" and decision == "纳入":
            changes["old_review_needed_to_new_true"].append(entry)
    return {
        "generated_at": date.today().isoformat(),
        "decision_counts": decision_counts,
        "claim_unit_distribution": claim_unit_distribution,
        "key_changes": changes,
    }


def build_review_v2_artifacts(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
    post_output_path: Path = POST_MASTER_PATH,
    comment_output_path: Path = COMMENT_MASTER_PATH,
    delta_output_path: Path = DELTA_REPORT_PATH,
) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        post_records = _build_post_records(connection, suggestions_dir)
        included_post_ids = {
            str(row["post_id"])
            for row in post_records
            if row["decision"] == "纳入"
        }
        comment_records = _build_comment_records(
            connection,
            included_post_ids=included_post_ids,
        )
    post_path = _write_jsonl(post_output_path, post_records)
    comment_path = _write_jsonl(comment_output_path, comment_records)
    delta_report = _build_delta_report(post_records)
    delta_output_path.parent.mkdir(parents=True, exist_ok=True)
    delta_output_path.write_text(
        json.dumps(delta_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "post_master_path": str(post_path),
        "comment_master_path": str(comment_path),
        "delta_report_path": str(delta_output_path),
        "post_rows": len(post_records),
        "comment_rows": len(comment_records),
        "included_posts": len(included_post_ids),
    }


__all__ = [
    "build_review_v2_artifacts",
    "COMMENT_MASTER_PATH",
    "DELTA_REPORT_PATH",
    "POST_MASTER_PATH",
]
