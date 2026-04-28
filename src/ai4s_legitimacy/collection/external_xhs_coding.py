from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import format_decision_reason
from ai4s_legitimacy.collection.external_xhs_runtime import (
    PagePayload,
    SearchCandidate,
    _contains_any,
    _normalize_space,
    _sentence_for_keywords,
    _sha1,
    _split_sentences,
)
from ai4s_legitimacy.collection.external_xhs_terms import (
    AI_CORE_TERMS,
    BASIS_PATTERNS,
    BOUNDARY_CONTENT_PATTERNS,
    BOUNDARY_MODE_PATTERNS,
    CONDITIONAL_TERMS,
    EVALUATIVE_QUESTION_TERMS,
    NEGATIVE_TERMS,
    NON_RESEARCH_TERMS,
    POSITIVE_TERMS,
    RESEARCH_STAGE_TERMS,
    STAGE_TO_DIMENSION,
    STRONG_RESEARCH_PRACTICE_TERMS,
    WORKFLOW_PATTERNS,
)

TASK_BATCH_ID = "external_xhs_opencli_2025plus_pilot100_v1"
CODER_VERSION = "codex_ai4s_schema_v1"


def _looks_like_generic_tool_roundup(text: str) -> bool:
    lowered = text.lower()
    marker_hits = sum(lowered.count(marker) for marker in (".com", "www.", "http", "⇢"))
    generic_hits = sum(text.count(marker) for marker in ("工具", "神器", "合集", "网站"))
    has_strong_research = _contains_any(text, STRONG_RESEARCH_PRACTICE_TERMS)
    return marker_hits + generic_hits >= 4 and not has_strong_research


def _format_decision_reason(code: str, note: str) -> list[str]:
    return format_decision_reason(code, note)


def _choose_workflow_codes(text: str) -> list[str]:
    lowered = text.lower()
    codes = [
        code
        for code, keywords in WORKFLOW_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    ]
    if not codes:
        return []
    # Apply a few project-specific disambiguation rules conservatively.
    if "文献" in text and any(token in text for token in ("怎么读论文", "写作训练", "英文写作", "训练")):
        codes = [code for code in codes if code != "A1.2"]
        if "A3.4" not in codes:
            codes.append("A3.4")
    if "研究设计" in text and any(token in text for token in ("方法学习", "方法训练")):
        codes = [code for code in codes if code != "A1.3"]
        if "A3.2" not in codes:
            codes.append("A3.2")
    if any(token in text for token in ("审稿人", "期刊要求", "同行评议")) and "A2.7" not in codes:
        codes.append("A2.7")
    return sorted(dict.fromkeys(codes))


def _choose_legitimacy(text: str) -> list[str]:
    has_positive = _contains_any(text, POSITIVE_TERMS)
    has_negative = _contains_any(text, NEGATIVE_TERMS)
    has_conditional = _contains_any(text, CONDITIONAL_TERMS)
    has_eval_question = _contains_any(text, EVALUATIVE_QUESTION_TERMS)
    if has_positive and has_negative:
        return ["B4"]
    if has_negative:
        return ["B3"]
    if has_conditional:
        return ["B2"]
    if has_positive:
        return ["B1"]
    if has_eval_question:
        return ["B5"]
    return ["B0"]


def _choose_basis_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code
        for code, keywords in BASIS_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    )


def _choose_boundary_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code
        for code, keywords in BOUNDARY_CONTENT_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    )


def _choose_boundary_mode_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code
        for code, keywords in BOUNDARY_MODE_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    )


def _discursive_mode(text: str) -> str:
    if "?" in text or "？" in text or any(token in text for token in ("请问", "求助")):
        return "question_help_seeking"
    if any(token in text for token in ("建议", "别再", "应该", "必须")):
        return "advice_guidance"
    if any(token in text for token in ("踩坑", "太香了", "亲测", "我用")):
        return "experience_share"
    if any(token in text for token in ("不合适", "学术不端", "风险")):
        return "criticism"
    if any(token in text for token in ("规定", "要求", "声明")):
        return "policy_statement"
    return "unclear"


def _practice_status(text: str) -> str:
    if any(token in text for token in ("我用", "用了", "我现在", "亲测", "实测")):
        return "actual_use"
    if any(token in text for token in ("打算", "准备", "想用")):
        return "intended_use"
    if any(token in text for token in ("如果", "假如", "能不能")):
        return "hypothetical_use"
    if any(token in text for token in ("规定", "要求", "声明", "期刊要求")):
        return "policy_or_rule"
    if any(token in text for token in ("看到", "听说", "吴恩达团队", "别人")):
        return "secondhand_report"
    return "unclear"


def _speaker_position(text: str) -> str:
    mapping = {
        "researcher": ("研究者", "科研人员"),
        "graduate_student": ("研究生", "博士生", "硕士"),
        "undergraduate": ("本科生", "本科科研"),
        "PI": ("导师",),
        "reviewer": ("审稿人",),
        "editor": ("编辑", "期刊编辑"),
        "institution_or_lab": ("实验室", "课题组", "学校"),
        "teacher_or_trainer": ("老师", "课程", "训练营"),
    }
    for code, keywords in mapping.items():
        if _contains_any(text, keywords):
            return code
    if re.search(r"(?<![A-Za-z])PI(?![A-Za-z])", text):
        return "PI"
    return "unclear"


def _theme_summary(title: str, workflow_codes: list[str], legitimacy_codes: list[str]) -> str:
    summary = _normalize_space(title)
    if summary:
        return summary[:120]
    if workflow_codes:
        return f"AI4S {workflow_codes[0]} 讨论"
    if legitimacy_codes and legitimacy_codes != ["B0"]:
        return f"AI科研实践 {legitimacy_codes[0]} 评价"
    return "AI科研相关帖子"


def _target_practice_summary(workflow_codes: list[str], boundary_codes: list[str]) -> str:
    if workflow_codes:
        return "; ".join(workflow_codes)
    if boundary_codes:
        return "; ".join(boundary_codes)
    return ""


def _make_claim_units(
    *,
    source_text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_codes: list[str],
    boundary_mode_codes: list[str],
) -> list[dict[str, Any]]:
    claim_units: list[dict[str, Any]] = []
    evidence_map: dict[str, str] = {}
    for code in workflow_codes:
        sentence = _sentence_for_keywords(source_text, WORKFLOW_PATTERNS[code])
        if sentence:
            evidence_map[code] = sentence
    if not evidence_map and workflow_codes:
        evidence_map[workflow_codes[0]] = (
            _split_sentences(source_text)[0] if _split_sentences(source_text) else source_text[:160]
        )
    fallback_evidence = ""
    if not workflow_codes:
        fallback_patterns = (
            *[BASIS_PATTERNS[code] for code in basis_codes],
            *[BOUNDARY_CONTENT_PATTERNS[code] for code in boundary_codes],
            *[BOUNDARY_MODE_PATTERNS[code] for code in boundary_mode_codes],
            POSITIVE_TERMS,
            NEGATIVE_TERMS,
            CONDITIONAL_TERMS,
            EVALUATIVE_QUESTION_TERMS,
        )
        for patterns in fallback_patterns:
            fallback_evidence = _sentence_for_keywords(source_text, patterns)
            if fallback_evidence:
                break
    for index, code in enumerate(workflow_codes or [""]):
        evidence = evidence_map.get(code, "") or fallback_evidence
        if not evidence:
            continue
        unit_basis = [
            {
                "code": basis,
                "evidence": _sentence_for_keywords(source_text, BASIS_PATTERNS[basis]) or evidence,
            }
            for basis in basis_codes
        ]
        unit_boundary = [
            {
                "code": boundary,
                "evidence": _sentence_for_keywords(source_text, BOUNDARY_CONTENT_PATTERNS[boundary])
                or evidence,
            }
            for boundary in boundary_codes
        ]
        unit_boundary_modes = [
            {
                "code": mode,
                "evidence": _sentence_for_keywords(source_text, BOUNDARY_MODE_PATTERNS[mode])
                or evidence,
            }
            for mode in boundary_mode_codes
        ]
        claim_units.append(
            {
                "practice_unit": f"AI相关实践单元{index + 1}: {code}" if code else "AI相关实践单元",
                "workflow_stage_codes": [code] if code else [],
                "legitimacy_codes": legitimacy_codes,
                "basis_codes": unit_basis,
                "boundary_codes": unit_boundary,
                "boundary_mode_codes": unit_boundary_modes,
                "evidence": [evidence],
            }
        )
    return claim_units


def _collect_evidence(
    source_text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_codes: list[str],
    boundary_mode_codes: list[str],
) -> dict[str, list[str]]:
    workflow_evidence = [
        _sentence_for_keywords(source_text, WORKFLOW_PATTERNS[code]) for code in workflow_codes
    ]
    workflow_evidence = [item for item in workflow_evidence if item]

    legitimacy_evidence: list[str] = []
    if legitimacy_codes != ["B0"]:
        for code in legitimacy_codes:
            if code == "B1":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, POSITIVE_TERMS))
            elif code == "B2":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, CONDITIONAL_TERMS))
            elif code == "B3":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, NEGATIVE_TERMS))
            elif code == "B4":
                legitimacy_evidence.append(
                    _sentence_for_keywords(source_text, POSITIVE_TERMS + NEGATIVE_TERMS)
                )
            elif code == "B5":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, EVALUATIVE_QUESTION_TERMS))
    legitimacy_evidence = [item for item in legitimacy_evidence if item]

    basis_evidence = [
        _sentence_for_keywords(source_text, BASIS_PATTERNS[code]) for code in basis_codes
    ]
    basis_evidence = [item for item in basis_evidence if item]

    boundary_evidence = [
        _sentence_for_keywords(source_text, BOUNDARY_CONTENT_PATTERNS[code]) for code in boundary_codes
    ]
    boundary_evidence.extend(
        _sentence_for_keywords(source_text, BOUNDARY_MODE_PATTERNS[code]) for code in boundary_mode_codes
    )
    boundary_evidence = [item for item in boundary_evidence if item]

    return {
        "workflow": list(dict.fromkeys(workflow_evidence)),
        "legitimacy": list(dict.fromkeys(legitimacy_evidence + basis_evidence)),
        "boundary": list(dict.fromkeys(boundary_evidence)),
    }


def _decision_for_page(page: PagePayload, *, title: str | None = None) -> tuple[str, list[str]]:
    page_title = page.title if title is None else title
    text = f"{page_title}\n{page.source_text}".strip()
    has_ai = _contains_any(text, AI_CORE_TERMS)
    if not has_ai:
        return "剔除", _format_decision_reason("R1", "未明确提及 AI 或可识别 AI 工具。")
    if _looks_like_generic_tool_roundup(text):
        return "剔除", _format_decision_reason("R8", "更像 AI 工具合集/产品信息，缺少具体科研实践场景。")

    workflow_codes = _choose_workflow_codes(text)
    has_research_context = _contains_any(text, RESEARCH_STAGE_TERMS)
    has_strong_research_practice = _contains_any(text, STRONG_RESEARCH_PRACTICE_TERMS)
    has_non_research = _contains_any(text, NON_RESEARCH_TERMS) and not has_research_context
    has_boundary_or_basis = bool(_choose_basis_codes(text) or _choose_boundary_codes(text))

    if has_non_research:
        return "剔除", _format_decision_reason("R4", "文本更像学习/办公/求职/一般开发场景。")
    if workflow_codes:
        return "纳入", _format_decision_reason("R12", "纳入：明确 AI 进入具体科研工作流环节。")
    if has_research_context and has_boundary_or_basis and has_strong_research_practice:
        return "纳入", _format_decision_reason("R12", "纳入：明确评价/边界对象指向具体科研实践。")
    if has_research_context and has_boundary_or_basis:
        return "待复核", _format_decision_reason("R6", "存在评价/边界信号，但科研工作流环节识别不稳定。")
    if has_research_context:
        return "待复核", _format_decision_reason("R6", "科研环节可能相关，但环节识别不稳定。")
    if len(page.source_text) < 140:
        return "待复核", _format_decision_reason("R11", "可能相关但证据不足，建议复核。")
    return "剔除", _format_decision_reason("R2", "无可稳定识别的具体科研工作流环节。")


def _confidence(
    decision: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    boundary_codes: list[str],
) -> str:
    if decision == "待复核":
        return "低"
    evidence_count = (
        len(workflow_codes)
        + len([code for code in legitimacy_codes if code != "B0"])
        + len(boundary_codes)
    )
    if evidence_count >= 3:
        return "高"
    return "中"


def _review_points(decision: str, workflow_codes: list[str], legitimacy_codes: list[str]) -> list[str]:
    points: list[str] = []
    if decision == "待复核":
        if not workflow_codes:
            points.append("需复核科研工作流环节是否可稳定判定。")
        if legitimacy_codes == ["B5"]:
            points.append("疑似存在评价，但方向不清。")
    return points


def encode_page(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    end_date: date,
) -> dict[str, Any]:
    page_title = page.title
    if not page_title or page_title.startswith("小红书_"):
        page_title = candidate.title or page_title
    author_handle = page.author_handle or candidate.author
    combined_text = _normalize_space(f"{page_title}\n{page.source_text}")
    workflow_codes = _choose_workflow_codes(combined_text)
    legitimacy_codes = _choose_legitimacy(combined_text)
    basis_codes = _choose_basis_codes(combined_text)
    boundary_codes = _choose_boundary_codes(combined_text)
    boundary_mode_codes = _choose_boundary_mode_codes(combined_text)
    decision, decision_reason = _decision_for_page(page, title=page_title)
    if decision != "纳入":
        workflow_codes = workflow_codes if decision == "待复核" else []
        legitimacy_codes = legitimacy_codes if decision == "待复核" else []
        basis_codes = basis_codes if decision == "待复核" else []
        boundary_codes = boundary_codes if decision == "待复核" else []
        boundary_mode_codes = boundary_mode_codes if decision == "待复核" else []
    evidence_groups = _collect_evidence(
        combined_text,
        workflow_codes,
        legitimacy_codes,
        basis_codes,
        boundary_codes,
        boundary_mode_codes,
    )
    claim_units = (
        _make_claim_units(
            source_text=combined_text,
            workflow_codes=workflow_codes,
            legitimacy_codes=legitimacy_codes,
            basis_codes=basis_codes,
            boundary_codes=boundary_codes,
            boundary_mode_codes=boundary_mode_codes,
        )
        if decision == "纳入"
        else []
    )
    primary_dimensions = sorted({STAGE_TO_DIMENSION[code] for code in workflow_codes})
    evidence_master = list(
        dict.fromkeys(
            claim_evidence
            for claim in claim_units
            for claim_evidence in claim.get("evidence", [])
            if claim_evidence
        )
    )
    boundary_present = "是" if boundary_codes or boundary_mode_codes else "否"
    ambiguity = "是" if decision == "待复核" or legitimacy_codes == ["B5"] else "否"
    confidence = _confidence(decision, workflow_codes, legitimacy_codes, boundary_codes)
    mechanism_eligible = "待定" if decision == "纳入" and boundary_present == "是" else "否"
    theme_summary = _theme_summary(page_title, workflow_codes, legitimacy_codes)
    target_practice_summary = _target_practice_summary(workflow_codes, boundary_codes)
    created_at = page.created_at or candidate.result_date
    if created_at:
        try:
            created_date = datetime.strptime(created_at, "%Y-%m-%d").date()
            if created_date > end_date:
                created_at = ""
        except ValueError:
            created_at = ""

    return {
        "post_id": page.note_id,
        "record_type": "post",
        "record_id": page.note_id,
        "task_batch_id": TASK_BATCH_ID,
        "coder_version": CODER_VERSION,
        "platform": "xiaohongshu",
        "post_url": page.url,
        "author_id": _sha1(author_handle) if author_handle else "",
        "created_at": created_at,
        "language": "zh",
        "thread_id": "",
        "parent_post_id": "",
        "reply_to_post_id": "",
        "quoted_post_id": "",
        "context_available": "否",
        "context_used": "none",
        "source_text": combined_text,
        "context_text": "",
        "decision": decision,
        "decision_reason": decision_reason,
        "theme_summary": theme_summary,
        "target_practice_summary": target_practice_summary,
        "evidence_master": evidence_master,
        "discursive_mode": _discursive_mode(combined_text),
        "practice_status": _practice_status(combined_text),
        "speaker_position_claimed": _speaker_position(combined_text),
        "workflow_dimension": {
            "primary_dimension": primary_dimensions,
            "secondary_stage": workflow_codes,
            "evidence": evidence_groups["workflow"],
        },
        "legitimacy_evaluation": {
            "direction": legitimacy_codes if decision != "剔除" else [],
            "basis": basis_codes if decision != "剔除" else [],
            "evidence": evidence_groups["legitimacy"],
        },
        "boundary_expression": {
            "present": boundary_present if decision != "剔除" else "否",
            "boundary_content_codes": boundary_codes if decision != "剔除" else [],
            "boundary_expression_mode_codes": boundary_mode_codes if decision != "剔除" else [],
            "evidence": evidence_groups["boundary"],
        },
        "interaction_level": {
            "event_present": "不适用",
            "interaction_role": "unclear",
            "target_claim_summary": "",
            "event_codes": [],
            "event_basis_codes": [],
            "event_outcome": "",
            "evidence": [],
        },
        "claim_units": claim_units,
        "mechanism_memo": {
            "eligible_for_mechanism_analysis": mechanism_eligible,
            "candidate_pattern_notes": (
                ["单帖存在边界表达，可与其他帖子做后续比较；不得直接视为机制。"]
                if mechanism_eligible == "待定"
                else []
            ),
            "comparison_keys": workflow_codes + legitimacy_codes + boundary_codes,
        },
        "api_assistance": {
            "used": "否",
            "purpose": [],
            "api_confidence": "无",
            "adoption_note": "No external model used; conservative rule-based coding only.",
        },
        "notes": {
            "multi_label": "是" if len(workflow_codes) > 1 or len(claim_units) > 1 else "否",
            "ambiguity": ambiguity,
            "confidence": confidence,
            "review_points": _review_points(decision, workflow_codes, legitimacy_codes),
            "dedup_group": page.note_id,
        },
        "review_status": "unreviewed",
    }
