from __future__ import annotations

import copy
import re
from typing import Any, Iterable


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


def format_decision_reason(code: str, note: str = "") -> list[str]:
    note = str(note or "").strip()
    if note:
        return [f"{code}: {note}"]
    return [code]


def decision_to_sample_status(decision: str) -> str:
    mapping = {
        "纳入": "true",
        "剔除": "false",
        "待复核": "review_needed",
    }
    return mapping.get(str(decision or "").strip(), "review_needed")


def sample_status_to_decision(sample_status: str) -> str:
    mapping = {
        "true": "纳入",
        "false": "剔除",
        "review_needed": "待复核",
    }
    return mapping.get(str(sample_status or "").strip(), "待复核")


def code_label(code: str) -> str:
    return ALL_CODE_LABELS.get(str(code or "").strip(), str(code or "").strip())


def primary_dimensions_from_workflow(stage_codes: Iterable[str]) -> list[str]:
    dimensions: list[str] = []
    for code in stage_codes:
        dimension = str(code or "").strip().split(".", 1)[0]
        if dimension in WORKFLOW_DIMENSION_LABELS and dimension not in dimensions:
            dimensions.append(dimension)
    return dimensions


def ensure_list_of_strings(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for item in value:
            normalized = str(item or "").strip()
            if normalized:
                items.append(normalized)
        return items
    return [str(value).strip()] if str(value).strip() else []


def normalize_decision_reason(entries: Any) -> list[str]:
    values = ensure_list_of_strings(entries)
    if len(values) == 2 and values[0] in DECISION_REASON_CODES and ":" not in values[0]:
        return format_decision_reason(values[0], values[1])
    normalized: list[str] = []
    for value in values:
        if not value:
            continue
        if value in DECISION_REASON_CODES:
            normalized.append(value)
            continue
        if re.match(r"^R\d+(?::\s.+)?$", value):
            normalized.append(value)
            continue
        normalized.append(f"R12: {value}")
    return normalized


def decision_reason_codes(entries: Any) -> list[str]:
    codes: list[str] = []
    for value in normalize_decision_reason(entries):
        code = value.split(":", 1)[0].strip()
        if code and code not in codes:
            codes.append(code)
    return codes


def _empty_workflow_dimension() -> dict[str, Any]:
    return {
        "primary_dimension": [],
        "secondary_stage": [],
        "evidence": [],
    }


def _empty_legitimacy_evaluation() -> dict[str, Any]:
    return {
        "direction": [],
        "basis": [],
        "evidence": [],
    }


def _empty_boundary_expression() -> dict[str, Any]:
    return {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }


def _empty_interaction_level() -> dict[str, Any]:
    return {
        "event_present": "不适用",
        "interaction_role": "unclear",
        "target_claim_summary": "",
        "event_codes": [],
        "event_basis_codes": [],
        "event_outcome": "",
        "evidence": [],
    }


def _empty_mechanism_memo() -> dict[str, Any]:
    return {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": [],
    }


def _empty_api_assistance() -> dict[str, Any]:
    return {
        "used": "否",
        "purpose": [],
        "api_confidence": "无",
        "adoption_note": "",
    }


def _empty_notes(record_id: str) -> dict[str, Any]:
    return {
        "multi_label": "否",
        "ambiguity": "否",
        "confidence": "中",
        "review_points": [],
        "dedup_group": record_id,
    }


def build_empty_canonical_row(
    record_type: str,
    record_id: str,
    *,
    platform: str = "xiaohongshu",
) -> dict[str, Any]:
    if record_type not in RECORD_TYPE_VALUES:
        raise ValueError(f"Unsupported record_type: {record_type}")
    id_field = RECORD_ID_FIELD[record_type]
    row = {
        "post_id": "",
        "task_batch_id": "",
        "coder_version": "",
        "platform": platform,
        "post_url": "",
        "author_id": "",
        "created_at": "",
        "language": "",
        "thread_id": "",
        "parent_post_id": "",
        "reply_to_post_id": "",
        "quoted_post_id": "",
        "context_available": "否",
        "context_used": "none",
        "source_text": "",
        "context_text": "",
        "decision": "待复核",
        "decision_reason": [],
        "theme_summary": "",
        "target_practice_summary": "",
        "evidence_master": [],
        "discursive_mode": "",
        "practice_status": "",
        "speaker_position_claimed": "",
        "workflow_dimension": _empty_workflow_dimension(),
        "legitimacy_evaluation": _empty_legitimacy_evaluation(),
        "boundary_expression": _empty_boundary_expression(),
        "interaction_level": _empty_interaction_level(),
        "claim_units": [],
        "mechanism_memo": _empty_mechanism_memo(),
        "api_assistance": _empty_api_assistance(),
        "notes": _empty_notes(record_id),
        "review_status": "unreviewed",
        "record_type": record_type,
        "record_id": record_id,
    }
    row[id_field] = record_id
    return row


def canonical_record_identity(row: dict[str, Any]) -> tuple[str, str]:
    record_type = str(row.get("record_type") or "").strip()
    if record_type not in RECORD_TYPE_VALUES:
        if str(row.get("comment_id") or "").strip():
            record_type = "comment"
        else:
            record_type = "post"
    record_id = str(row.get("record_id") or "").strip()
    if not record_id:
        record_id = str(row.get(RECORD_ID_FIELD[record_type]) or "").strip()
    if not record_id:
        raise ValueError("Canonical row missing record_id")
    return record_type, record_id


def _normalize_code_entries(values: Any, *, allowed_codes: set[str]) -> list[str]:
    normalized: list[str] = []
    if values in (None, ""):
        return normalized
    iterable = values if isinstance(values, (list, tuple, set)) else [values]
    for value in iterable:
        if isinstance(value, dict):
            raw_code = str(value.get("code") or "").strip()
        else:
            raw_code = str(value or "").strip()
        code = _normalize_code_token(raw_code, allowed_codes=allowed_codes)
        if code in allowed_codes and code not in normalized:
            normalized.append(code)
    return normalized


def _normalize_code_token(raw_code: str, *, allowed_codes: set[str]) -> str:
    text = OLD_BOUNDARY_TO_CONTENT_CODE.get(str(raw_code or "").strip(), str(raw_code or "").strip())
    if text in allowed_codes:
        return text
    if not text:
        return ""
    for code in sorted(allowed_codes, key=len, reverse=True):
        if text == code or text.startswith(f"{code} "):
            return code
        if text.startswith(f"{code}：") or text.startswith(f"{code}:"):
            return code
        if text.startswith(f"{code}-") or text.startswith(f"{code}_"):
            return code
    match = re.match(r"^([A-Z]\d(?:\.\d+)?)\b", text)
    if match:
        candidate = OLD_BOUNDARY_TO_CONTENT_CODE.get(match.group(1), match.group(1))
        if candidate in allowed_codes:
            return candidate
    return ""


def _normalize_code_with_evidence_entries(
    values: Any,
    *,
    allowed_codes: set[str],
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if values in (None, ""):
        return normalized
    iterable = values if isinstance(values, list) else [values]
    for item in iterable:
        if isinstance(item, dict):
            code = _normalize_code_token(
                str(item.get("code") or "").strip(),
                allowed_codes=allowed_codes,
            )
            evidence = str(item.get("evidence") or "").strip()
        else:
            code = _normalize_code_token(str(item or "").strip(), allowed_codes=allowed_codes)
            evidence = ""
        if code not in allowed_codes:
            continue
        key = (code, evidence)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"code": code, "evidence": evidence})
    return normalized


def normalize_claim_units(claim_units: Any) -> list[dict[str, Any]]:
    normalized_units: list[dict[str, Any]] = []
    if claim_units in (None, ""):
        return normalized_units
    iterable = claim_units if isinstance(claim_units, list) else [claim_units]
    for item in iterable:
        if not isinstance(item, dict):
            continue
        practice_unit = str(item.get("practice_unit") or "").strip()
        workflow_stage_codes = _normalize_code_entries(
            item.get("workflow_stage_codes"),
            allowed_codes=WORKFLOW_CODE_SET,
        )
        legitimacy_codes = _normalize_code_entries(
            item.get("legitimacy_codes"),
            allowed_codes=LEGITIMACY_CODE_SET,
        )
        basis_codes = _normalize_code_with_evidence_entries(
            item.get("basis_codes"),
            allowed_codes=EVALUATION_CODE_SET,
        )
        boundary_codes = _normalize_code_with_evidence_entries(
            item.get("boundary_codes"),
            allowed_codes=BOUNDARY_CONTENT_CODE_SET,
        )
        boundary_mode_codes = _normalize_code_with_evidence_entries(
            item.get("boundary_mode_codes"),
            allowed_codes=BOUNDARY_MODE_CODE_SET,
        )
        evidence = ensure_list_of_strings(item.get("evidence"))
        normalized_units.append(
            {
                "practice_unit": practice_unit,
                "workflow_stage_codes": workflow_stage_codes,
                "legitimacy_codes": legitimacy_codes,
                "basis_codes": basis_codes,
                "boundary_codes": boundary_codes,
                "boundary_mode_codes": boundary_mode_codes,
                "evidence": evidence,
            }
        )
    return normalized_units


def apply_claim_units_to_row(row: dict[str, Any]) -> dict[str, Any]:
    claim_units = normalize_claim_units(row.get("claim_units"))
    if not claim_units:
        row["claim_units"] = []
        return row

    workflow_codes: list[str] = []
    legitimacy_codes: list[str] = []
    basis_codes: list[str] = []
    boundary_content_codes: list[str] = []
    boundary_mode_codes: list[str] = []
    workflow_evidence: list[str] = []
    legitimacy_evidence: list[str] = []
    boundary_evidence: list[str] = []
    evidence_master: list[str] = []
    practice_units: list[str] = []

    for unit in claim_units:
        practice_unit = str(unit.get("practice_unit") or "").strip()
        if practice_unit:
            practice_units.append(practice_unit)

        for code in unit["workflow_stage_codes"]:
            if code not in workflow_codes:
                workflow_codes.append(code)
        for code in unit["legitimacy_codes"]:
            if code not in legitimacy_codes:
                legitimacy_codes.append(code)

        for entry in unit["basis_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in basis_codes:
                basis_codes.append(code)
            if evidence and evidence not in legitimacy_evidence:
                legitimacy_evidence.append(evidence)

        for entry in unit["boundary_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in boundary_content_codes:
                boundary_content_codes.append(code)
            if evidence and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

        for entry in unit["boundary_mode_codes"]:
            code = entry["code"]
            evidence = entry["evidence"]
            if code not in boundary_mode_codes:
                boundary_mode_codes.append(code)
            if evidence and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

        for evidence in unit["evidence"]:
            if evidence not in evidence_master:
                evidence_master.append(evidence)
            if unit["workflow_stage_codes"] and evidence not in workflow_evidence:
                workflow_evidence.append(evidence)
            if unit["legitimacy_codes"] and evidence not in legitimacy_evidence:
                legitimacy_evidence.append(evidence)
            if (unit["boundary_codes"] or unit["boundary_mode_codes"]) and evidence not in boundary_evidence:
                boundary_evidence.append(evidence)

    row["claim_units"] = claim_units
    row["evidence_master"] = evidence_master
    row["target_practice_summary"] = row.get("target_practice_summary") or "; ".join(practice_units[:3])
    workflow_dimension = row.get("workflow_dimension") or _empty_workflow_dimension()
    workflow_dimension["secondary_stage"] = workflow_codes
    workflow_dimension["primary_dimension"] = primary_dimensions_from_workflow(workflow_codes)
    workflow_dimension["evidence"] = workflow_evidence
    row["workflow_dimension"] = workflow_dimension

    legitimacy_evaluation = row.get("legitimacy_evaluation") or _empty_legitimacy_evaluation()
    legitimacy_evaluation["direction"] = legitimacy_codes
    legitimacy_evaluation["basis"] = basis_codes
    legitimacy_evaluation["evidence"] = legitimacy_evidence
    row["legitimacy_evaluation"] = legitimacy_evaluation

    boundary_expression = row.get("boundary_expression") or _empty_boundary_expression()
    boundary_expression["present"] = "是" if (boundary_content_codes or boundary_mode_codes) else "否"
    boundary_expression["boundary_content_codes"] = boundary_content_codes
    boundary_expression["boundary_expression_mode_codes"] = boundary_mode_codes
    boundary_expression["evidence"] = boundary_evidence
    row["boundary_expression"] = boundary_expression

    notes = row.get("notes") or _empty_notes(str(row.get("record_id") or ""))
    notes["multi_label"] = "是" if len(workflow_codes) > 1 or len(claim_units) > 1 else "否"
    row["notes"] = notes
    return row


def normalize_canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = build_empty_canonical_row(*canonical_record_identity(row))
    for key, value in row.items():
        if value is not None:
            normalized[key] = copy.deepcopy(value)

    record_type, record_id = canonical_record_identity(normalized)
    normalized["record_type"] = record_type
    normalized["record_id"] = record_id
    normalized[RECORD_ID_FIELD[record_type]] = record_id
    normalized["decision_reason"] = normalize_decision_reason(normalized.get("decision_reason"))
    normalized["evidence_master"] = ensure_list_of_strings(normalized.get("evidence_master"))
    normalized["workflow_dimension"] = {
        "primary_dimension": _normalize_code_entries(
            normalized.get("workflow_dimension", {}).get("primary_dimension"),
            allowed_codes=set(WORKFLOW_DIMENSION_LABELS),
        ),
        "secondary_stage": _normalize_code_entries(
            normalized.get("workflow_dimension", {}).get("secondary_stage"),
            allowed_codes=WORKFLOW_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("workflow_dimension", {}).get("evidence"),
        ),
    }
    if not normalized["workflow_dimension"]["primary_dimension"]:
        normalized["workflow_dimension"]["primary_dimension"] = primary_dimensions_from_workflow(
            normalized["workflow_dimension"]["secondary_stage"]
        )

    normalized["legitimacy_evaluation"] = {
        "direction": _normalize_code_entries(
            normalized.get("legitimacy_evaluation", {}).get("direction"),
            allowed_codes=LEGITIMACY_CODE_SET,
        ),
        "basis": _normalize_code_entries(
            normalized.get("legitimacy_evaluation", {}).get("basis"),
            allowed_codes=EVALUATION_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("legitimacy_evaluation", {}).get("evidence"),
        ),
    }

    normalized["boundary_expression"] = {
        "present": str(
            normalized.get("boundary_expression", {}).get("present") or "否"
        ).strip()
        or "否",
        "boundary_content_codes": _normalize_code_entries(
            normalized.get("boundary_expression", {}).get("boundary_content_codes"),
            allowed_codes=BOUNDARY_CONTENT_CODE_SET,
        ),
        "boundary_expression_mode_codes": _normalize_code_entries(
            normalized.get("boundary_expression", {}).get("boundary_expression_mode_codes"),
            allowed_codes=BOUNDARY_MODE_CODE_SET,
        ),
        "evidence": ensure_list_of_strings(
            normalized.get("boundary_expression", {}).get("evidence"),
        ),
    }

    normalized["interaction_level"] = {
        "event_present": str(
            normalized.get("interaction_level", {}).get("event_present") or "不适用"
        ).strip()
        or "不适用",
        "interaction_role": str(
            normalized.get("interaction_level", {}).get("interaction_role") or "unclear"
        ).strip()
        or "unclear",
        "target_claim_summary": str(
            normalized.get("interaction_level", {}).get("target_claim_summary") or ""
        ).strip(),
        "event_codes": _normalize_code_entries(
            normalized.get("interaction_level", {}).get("event_codes"),
            allowed_codes=INTERACTION_EVENT_CODE_SET,
        ),
        "event_basis_codes": _normalize_code_entries(
            normalized.get("interaction_level", {}).get("event_basis_codes"),
            allowed_codes=INTERACTION_BASIS_CODE_SET,
        ),
        "event_outcome": str(
            normalized.get("interaction_level", {}).get("event_outcome") or ""
        ).strip(),
        "evidence": ensure_list_of_strings(
            normalized.get("interaction_level", {}).get("evidence"),
        ),
    }

    normalized["claim_units"] = normalize_claim_units(normalized.get("claim_units"))

    normalized["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": str(
            normalized.get("mechanism_memo", {}).get("eligible_for_mechanism_analysis") or "否"
        ).strip()
        or "否",
        "candidate_pattern_notes": ensure_list_of_strings(
            normalized.get("mechanism_memo", {}).get("candidate_pattern_notes"),
        ),
        "comparison_keys": ensure_list_of_strings(
            normalized.get("mechanism_memo", {}).get("comparison_keys"),
        ),
    }

    normalized["api_assistance"] = {
        "used": str(normalized.get("api_assistance", {}).get("used") or "否").strip() or "否",
        "purpose": ensure_list_of_strings(normalized.get("api_assistance", {}).get("purpose")),
        "api_confidence": str(
            normalized.get("api_assistance", {}).get("api_confidence") or "无"
        ).strip()
        or "无",
        "adoption_note": str(
            normalized.get("api_assistance", {}).get("adoption_note") or ""
        ).strip(),
    }

    normalized["notes"] = {
        "multi_label": str(normalized.get("notes", {}).get("multi_label") or "否").strip() or "否",
        "ambiguity": str(normalized.get("notes", {}).get("ambiguity") or "否").strip() or "否",
        "confidence": str(normalized.get("notes", {}).get("confidence") or "中").strip() or "中",
        "review_points": ensure_list_of_strings(normalized.get("notes", {}).get("review_points")),
        "dedup_group": str(normalized.get("notes", {}).get("dedup_group") or record_id).strip()
        or record_id,
    }

    normalized["review_status"] = str(normalized.get("review_status") or "unreviewed").strip() or "unreviewed"
    normalized["context_used"] = str(normalized.get("context_used") or "none").strip() or "none"
    normalized["context_available"] = "否" if normalized["context_used"] == "none" else "是"
    if normalized["context_used"] == "none":
        normalized["interaction_level"]["event_present"] = "不适用"
    normalized = apply_claim_units_to_row(normalized)
    if normalized["boundary_expression"]["present"] == "否" and (
        normalized["boundary_expression"]["boundary_content_codes"]
        or normalized["boundary_expression"]["boundary_expression_mode_codes"]
    ):
        normalized["boundary_expression"]["present"] = "是"
    return normalized


def _require_allowed(value: str, *, allowed: Iterable[str], field_name: str) -> None:
    if value not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {expected}. Got {value!r}")


def _require_evidence_if_codes(codes: list[str], evidence: list[str], *, field_name: str) -> None:
    if codes and not evidence:
        raise ValueError(f"{field_name} has codes but no evidence")


def validate_canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_canonical_row(row)
    _require_allowed(normalized["record_type"], allowed=RECORD_TYPE_VALUES, field_name="record_type")
    _require_allowed(normalized["decision"], allowed=DECISION_VALUES, field_name="decision")
    _require_allowed(
        normalized["context_available"],
        allowed=CONTEXT_AVAILABLE_VALUES,
        field_name="context_available",
    )
    _require_allowed(normalized["context_used"], allowed=CONTEXT_USED_VALUES, field_name="context_used")
    _require_allowed(
        normalized["boundary_expression"]["present"],
        allowed=BOUNDARY_PRESENT_VALUES,
        field_name="boundary_expression.present",
    )
    _require_allowed(
        normalized["interaction_level"]["event_present"],
        allowed=INTERACTION_EVENT_VALUES,
        field_name="interaction_level.event_present",
    )
    _require_allowed(
        normalized["interaction_level"]["interaction_role"],
        allowed=INTERACTION_ROLE_VALUES,
        field_name="interaction_level.interaction_role",
    )
    _require_allowed(
        normalized["notes"]["multi_label"],
        allowed=MULTI_LABEL_VALUES,
        field_name="notes.multi_label",
    )
    _require_allowed(
        normalized["notes"]["ambiguity"],
        allowed=AMBIGUITY_VALUES,
        field_name="notes.ambiguity",
    )
    _require_allowed(
        normalized["notes"]["confidence"],
        allowed=CONFIDENCE_VALUES,
        field_name="notes.confidence",
    )
    _require_allowed(
        normalized["api_assistance"]["used"],
        allowed=API_ASSISTANCE_VALUES,
        field_name="api_assistance.used",
    )
    _require_allowed(
        normalized["api_assistance"]["api_confidence"],
        allowed=API_CONFIDENCE_VALUES,
        field_name="api_assistance.api_confidence",
    )
    _require_allowed(
        normalized["mechanism_memo"]["eligible_for_mechanism_analysis"],
        allowed=MECHANISM_ELIGIBILITY_VALUES,
        field_name="mechanism_memo.eligible_for_mechanism_analysis",
    )
    _require_allowed(
        normalized["review_status"],
        allowed=REVIEW_STATUS_VALUES,
        field_name="review_status",
    )

    if normalized["context_used"] == "none" and normalized["context_available"] != "否":
        raise ValueError("context_available must be 否 when context_used=none")
    if normalized["context_used"] != "none" and normalized["context_available"] != "是":
        raise ValueError("context_available must be 是 when context_used!=none")
    if normalized["context_used"] == "none" and normalized["interaction_level"]["event_present"] != "不适用":
        raise ValueError("interaction_level.event_present must be 不适用 when context_used=none")
    if (
        normalized["interaction_level"]["event_outcome"]
        and normalized["interaction_level"]["event_outcome"] not in INTERACTION_OUTCOME_VALUES
    ):
        raise ValueError("interaction_level.event_outcome has invalid code")

    for entry in normalized["decision_reason"]:
        if not re.match(r"^R\d+(?::\s.+)?$", entry):
            raise ValueError(f"decision_reason entry must be R# or R#: note. Got {entry!r}")
        code = entry.split(":", 1)[0].strip()
        if code not in DECISION_REASON_CODES:
            raise ValueError(f"decision_reason code not in controlled vocab: {code}")

    _require_evidence_if_codes(
        normalized["workflow_dimension"]["secondary_stage"],
        normalized["workflow_dimension"]["evidence"],
        field_name="workflow_dimension",
    )
    _require_evidence_if_codes(
        normalized["legitimacy_evaluation"]["direction"] + normalized["legitimacy_evaluation"]["basis"],
        normalized["legitimacy_evaluation"]["evidence"],
        field_name="legitimacy_evaluation",
    )
    _require_evidence_if_codes(
        normalized["boundary_expression"]["boundary_content_codes"]
        + normalized["boundary_expression"]["boundary_expression_mode_codes"],
        normalized["boundary_expression"]["evidence"],
        field_name="boundary_expression",
    )
    _require_evidence_if_codes(
        normalized["interaction_level"]["event_codes"] + normalized["interaction_level"]["event_basis_codes"],
        normalized["interaction_level"]["evidence"],
        field_name="interaction_level",
    )

    for unit in normalized["claim_units"]:
        has_codes = bool(
            unit["workflow_stage_codes"]
            or unit["legitimacy_codes"]
            or unit["basis_codes"]
            or unit["boundary_codes"]
            or unit["boundary_mode_codes"]
        )
        if has_codes and not unit["evidence"]:
            raise ValueError("claim_unit with codes must include evidence")
        for entry in unit["basis_codes"] + unit["boundary_codes"] + unit["boundary_mode_codes"]:
            if entry["code"] and not entry["evidence"]:
                raise ValueError("claim_unit code+evidence entries must include evidence")

    return normalized
