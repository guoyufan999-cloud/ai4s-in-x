from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection.canonical_schema import (
    AMBIGUITY_VALUES,
    BOUNDARY_CONTENT_LABELS,
    BOUNDARY_MODE_LABELS,
    CONFIDENCE_VALUES,
    DECISION_REASON_CODES,
    DECISION_VALUES,
    EVALUATION_LABELS,
    INTERACTION_BASIS_CODE_SET,
    INTERACTION_BASIS_CODES,
    INTERACTION_EVENT_CODE_SET,
    INTERACTION_EVENT_CODES,
    INTERACTION_EVENT_VALUES,
    INTERACTION_OUTCOME_VALUES,
    INTERACTION_ROLE_VALUES,
    LEGITIMACY_LABELS,
    MECHANISM_ELIGIBILITY_VALUES,
    WORKFLOW_STAGE_LABELS,
    ensure_list_of_strings,
    format_decision_reason,
    normalize_claim_units,
    validate_canonical_row,
)
from ai4s_legitimacy.collection.llm_rescreen_posts import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DeepSeekClient,
)
from ai4s_legitimacy.config.formal_baseline import REBASELINE_REVIEWED_DIR


REVIEW_PHASE = "post_review_v2"
DEFAULT_BATCH_SIZE = 6
DEFAULT_MAX_WORKERS = 4
DEFAULT_REVIEWER = "guoyufan"

DISCURSIVE_MODE_VALUES = (
    "experience_share",
    "practice_demo",
    "question_help_seeking",
    "advice_guidance",
    "criticism",
    "policy_statement",
    "reflection",
    "unclear",
)
PRACTICE_STATUS_VALUES = (
    "actual_use",
    "intended_use",
    "hypothetical_use",
    "policy_or_rule",
    "secondhand_report",
    "unclear",
)
SPEAKER_POSITION_VALUES = (
    "researcher",
    "graduate_student",
    "undergraduate",
    "PI",
    "reviewer",
    "editor",
    "institution_or_lab",
    "teacher_or_trainer",
    "unclear",
)
QS_SUBJECT_VALUES = (
    "Engineering & Technology",
    "Arts & Humanities",
    "Life Sciences & Medicine",
    "Natural Sciences",
    "Social Sciences & Management",
    "uncertain",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _trim_text(value: Any, *, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "").strip())
    return normalized.strip("_") or "post_review_v2"


def _default_run_id(queue_path: Path) -> str:
    return f"qv5_{_slugify(queue_path.stem)}_deepseek_prefill_v1"


def _default_output_path(queue_path: Path, output_path: Path | None = None) -> Path:
    if output_path is not None:
        return output_path
    return REBASELINE_REVIEWED_DIR / f"{queue_path.stem}.ai_draft.jsonl"


def _summary_path_for_output(output_path: Path) -> Path:
    return output_path.with_suffix(".summary.json")


def _validate_queue_rows(rows: Sequence[dict[str, Any]]) -> None:
    for row in rows:
        review_phase = str(row.get("review_phase") or "").strip()
        if review_phase != REVIEW_PHASE:
            raise ValueError(
                f"LLM post-review prefill only supports {REVIEW_PHASE}, "
                f"got review_phase={review_phase!r}"
            )
        record_type = str(row.get("record_type") or "post").strip() or "post"
        if record_type != "post":
            raise ValueError(f"LLM post-review prefill only supports posts, got {record_type!r}")
        if not str(row.get("post_id") or row.get("record_id") or "").strip():
            raise ValueError("Each queue row must contain post_id or record_id")


def _empty_workflow_dimension() -> dict[str, list[str]]:
    return {"primary_dimension": [], "secondary_stage": [], "evidence": []}


def _empty_legitimacy_evaluation() -> dict[str, list[str]]:
    return {"direction": [], "basis": [], "evidence": []}


def _empty_boundary_expression() -> dict[str, Any]:
    return {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }


def _empty_interaction_level(context_used: str) -> dict[str, Any]:
    return {
        "event_present": "不适用" if context_used == "none" else "无法判断",
        "interaction_role": "unclear",
        "target_claim_summary": "",
        "event_codes": [],
        "event_basis_codes": [],
        "event_outcome": "",
        "evidence": [],
    }


def _confidence_label(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "低"
    if numeric >= 0.85:
        return "高"
    if numeric >= 0.6:
        return "中"
    return "低"


def _normalize_choice(value: Any, *, allowed: Sequence[str], default: str) -> str:
    normalized = str(value or "").strip()
    return normalized if normalized in allowed else default


def _coerce_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def _codebook_text(code_map: dict[str, str]) -> str:
    return "；".join(f"{code} {label}" for code, label in code_map.items())


def _serialize_queue_row_for_model(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "post_id": str(row.get("post_id") or row.get("record_id") or "").strip(),
        "source_text": _trim_text(row.get("source_text"), max_chars=2200),
        "context_used": str(row.get("context_used") or "none").strip() or "none",
        "context_text": _trim_text(row.get("context_text"), max_chars=900),
        "theme_summary_hint": _trim_text(row.get("theme_summary"), max_chars=160),
        "discursive_mode_hint": str(row.get("discursive_mode") or "unclear").strip() or "unclear",
        "practice_status_hint": str(row.get("practice_status") or "unclear").strip() or "unclear",
        "speaker_position_hint": str(row.get("speaker_position_claimed") or "unclear").strip()
        or "unclear",
        "actor_type_hint": str(row.get("actor_type") or "uncertain").strip() or "uncertain",
        "existing_decision_hint": str(row.get("decision") or "待复核").strip() or "待复核",
        "existing_decision_reason_hint": ensure_list_of_strings(row.get("decision_reason")),
    }


def _system_prompt() -> str:
    return """
你在做 AI4S 研究的 `post_review_v2` 正式复核预填。你必须只输出 JSON，不要输出解释。

你的任务是：基于单条帖子 `source_text` 以及可能提供的 `context_text`，按保守原则生成可复核的 canonical JSONL 预填草稿。

最高优先级规则：
- 只纳入“AI 介入科研具体环节”的帖子。
- 只要证据不足，就优先给 `待复核`，不要补推断。
- 没有原文证据，不要编码 workflow / legitimacy / basis / boundary / interaction。
- `claim_units` 是最高优先级分析单元。
- 如果 `decision=纳入`，必须至少给出 1 个带 evidence 的 `claim_unit`，并且该 claim_unit 必须包含 `workflow_stage_codes`。
- 如果你无法给出带 evidence 且能明确指向科研工作流环节的 `claim_units`，不要硬判 `纳入`，改成 `待复核`。
- 如果帖子被纳入，但原文没有明确表达支持/反对/限制，只是在陈述实践或经验，请把 `legitimacy_codes` 记为 `B0`，不要留空。
- 如果你无法识别 workflow_stage_codes，就不要输出 `纳入`。
- `interaction` 只有在 `context_used != none` 且上下文足以判断时才填写；否则保持空或“不适用”。

受控值：
- decision: 纳入 | 剔除 | 待复核
- decision_reason_code: {decision_reason_codes}
- discursive_mode: {discursive_modes}
- practice_status: {practice_statuses}
- speaker_position_claimed: {speaker_positions}
- qs_broad_subject: {subjects}
- workflow_stage_codes: {workflow_codes}
- legitimacy_codes: {legitimacy_codes}
- basis_codes: {basis_codes}
- boundary_codes: {boundary_codes}
- boundary_mode_codes: {boundary_mode_codes}
- interaction_event_present: {interaction_event_values}
- interaction_role: {interaction_roles}
- interaction_event_codes: {interaction_event_codes}
- interaction_event_basis_codes: {interaction_basis_codes}
- interaction_event_outcome: {interaction_outcomes}
- notes_ambiguity: {ambiguity_values}
- notes_confidence: {confidence_values}
- mechanism_eligible: {mechanism_values}

claim_unit 规则：
- 每个 claim_unit 对应一个可以独立识别的具体实践/评价单元。
- basis_codes / boundary_codes / boundary_mode_codes 必须使用 {{code, evidence}} 结构。
- 只在 evidence 能直接支持时才填 code。
- 一个 claim_unit 如果有任何 code，必须同时给出 `evidence`。

请返回一个 JSON object，顶层键为 `items`。
每个 item 必须包含：
- batch_item_id
- decision
- decision_reason_code
- decision_reason_note
- theme_summary
- target_practice_summary
- discursive_mode
- practice_status
- speaker_position_claimed
- qs_broad_subject
- evidence_master
- claim_units
- interaction_event_present
- interaction_role
- interaction_target_claim_summary
- interaction_event_codes
- interaction_event_basis_codes
- interaction_event_outcome
- interaction_evidence
- notes_ambiguity
- notes_confidence
- review_points
- mechanism_eligible
- mechanism_notes
- comparison_keys
- api_confidence
""".format(
        decision_reason_codes=" | ".join(DECISION_REASON_CODES),
        discursive_modes=" | ".join(DISCURSIVE_MODE_VALUES),
        practice_statuses=" | ".join(PRACTICE_STATUS_VALUES),
        speaker_positions=" | ".join(SPEAKER_POSITION_VALUES),
        subjects=" | ".join(QS_SUBJECT_VALUES),
        workflow_codes=_codebook_text(WORKFLOW_STAGE_LABELS),
        legitimacy_codes=_codebook_text(LEGITIMACY_LABELS),
        basis_codes=_codebook_text(EVALUATION_LABELS),
        boundary_codes=_codebook_text(BOUNDARY_CONTENT_LABELS),
        boundary_mode_codes=_codebook_text(BOUNDARY_MODE_LABELS),
        interaction_event_values=" | ".join(INTERACTION_EVENT_VALUES),
        interaction_roles=" | ".join(INTERACTION_ROLE_VALUES),
        interaction_event_codes=_codebook_text(INTERACTION_EVENT_CODES),
        interaction_basis_codes=_codebook_text(INTERACTION_BASIS_CODES),
        interaction_outcomes=" | ".join(INTERACTION_OUTCOME_VALUES),
        ambiguity_values=" | ".join(AMBIGUITY_VALUES),
        confidence_values=" | ".join(CONFIDENCE_VALUES),
        mechanism_values=" | ".join(MECHANISM_ELIGIBILITY_VALUES),
    ).strip()


def _normalize_interaction_codes(values: Any, *, allowed: set[str]) -> list[str]:
    codes: list[str] = []
    for value in ensure_list_of_strings(values):
        if value in allowed and value not in codes:
            codes.append(value)
    return codes


def _has_meaningful_claim_units(claim_units: Sequence[dict[str, Any]]) -> bool:
    for unit in claim_units:
        if not isinstance(unit, dict):
            continue
        has_workflow = bool(unit.get("workflow_stage_codes"))
        has_evidence = bool(ensure_list_of_strings(unit.get("evidence")))
        if has_workflow and has_evidence:
            return True
    return False


def _retain_formal_claim_units(claim_units: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    for unit in claim_units:
        if not isinstance(unit, dict):
            continue
        workflow_stage_codes = ensure_list_of_strings(unit.get("workflow_stage_codes"))
        evidence = ensure_list_of_strings(unit.get("evidence"))
        if not workflow_stage_codes or not evidence:
            continue
        retained_unit = {
            "practice_unit": str(unit.get("practice_unit") or "").strip(),
            "workflow_stage_codes": workflow_stage_codes,
            "legitimacy_codes": ensure_list_of_strings(unit.get("legitimacy_codes")) or ["B0"],
            "basis_codes": unit.get("basis_codes") or [],
            "boundary_codes": unit.get("boundary_codes") or [],
            "boundary_mode_codes": unit.get("boundary_mode_codes") or [],
            "evidence": evidence,
        }
        retained.append(retained_unit)
    return retained


def _fallback_item(reason: str) -> dict[str, Any]:
    message = str(reason or "prefill_failed").strip()
    return {
        "decision": "待复核",
        "decision_reason_code": "R11",
        "decision_reason_note": message,
        "theme_summary": "",
        "target_practice_summary": "",
        "discursive_mode": "unclear",
        "practice_status": "unclear",
        "speaker_position_claimed": "unclear",
        "qs_broad_subject": "",
        "evidence_master": [],
        "claim_units": [],
        "interaction_event_present": "",
        "interaction_role": "unclear",
        "interaction_target_claim_summary": "",
        "interaction_event_codes": [],
        "interaction_event_basis_codes": [],
        "interaction_event_outcome": "",
        "interaction_evidence": [],
        "notes_ambiguity": "是",
        "notes_confidence": "低",
        "review_points": [message],
        "mechanism_eligible": "否",
        "mechanism_notes": [],
        "comparison_keys": [],
        "api_confidence": 0.0,
    }


def _normalize_model_item(item: dict[str, Any], *, context_used: str) -> dict[str, Any]:
    decision = str(item.get("decision") or "").strip()
    if decision not in DECISION_VALUES:
        raise ValueError(f"invalid decision: {decision!r}")

    reason_code = str(item.get("decision_reason_code") or "").strip()
    if reason_code not in DECISION_REASON_CODES:
        reason_code = "R11" if decision == "待复核" else "R12"

    api_confidence = _coerce_confidence(item.get("api_confidence"))
    notes_confidence = _normalize_choice(
        item.get("notes_confidence"),
        allowed=CONFIDENCE_VALUES,
        default=_confidence_label(api_confidence),
    )

    claim_units = normalize_claim_units(item.get("claim_units"))
    interaction_event_present = _normalize_choice(
        item.get("interaction_event_present"),
        allowed=INTERACTION_EVENT_VALUES,
        default="不适用" if context_used == "none" else "无法判断",
    )
    if context_used == "none":
        interaction_event_present = "不适用"

    normalized = {
        "decision": decision,
        "decision_reason_code": reason_code,
        "decision_reason_note": str(item.get("decision_reason_note") or "").strip(),
        "theme_summary": str(item.get("theme_summary") or "").strip(),
        "target_practice_summary": str(item.get("target_practice_summary") or "").strip(),
        "discursive_mode": _normalize_choice(
            item.get("discursive_mode"),
            allowed=DISCURSIVE_MODE_VALUES,
            default="unclear",
        ),
        "practice_status": _normalize_choice(
            item.get("practice_status"),
            allowed=PRACTICE_STATUS_VALUES,
            default="unclear",
        ),
        "speaker_position_claimed": _normalize_choice(
            item.get("speaker_position_claimed"),
            allowed=SPEAKER_POSITION_VALUES,
            default="unclear",
        ),
        "qs_broad_subject": _normalize_choice(
            item.get("qs_broad_subject"),
            allowed=QS_SUBJECT_VALUES,
            default="",
        ),
        "evidence_master": ensure_list_of_strings(item.get("evidence_master")),
        "claim_units": claim_units,
        "interaction_event_present": interaction_event_present,
        "interaction_role": _normalize_choice(
            item.get("interaction_role"),
            allowed=INTERACTION_ROLE_VALUES,
            default="unclear",
        ),
        "interaction_target_claim_summary": str(
            item.get("interaction_target_claim_summary") or ""
        ).strip(),
        "interaction_event_codes": _normalize_interaction_codes(
            item.get("interaction_event_codes"),
            allowed=INTERACTION_EVENT_CODE_SET,
        ),
        "interaction_event_basis_codes": _normalize_interaction_codes(
            item.get("interaction_event_basis_codes"),
            allowed=INTERACTION_BASIS_CODE_SET,
        ),
        "interaction_event_outcome": _normalize_choice(
            item.get("interaction_event_outcome"),
            allowed=INTERACTION_OUTCOME_VALUES,
            default="",
        ),
        "interaction_evidence": ensure_list_of_strings(item.get("interaction_evidence")),
        "notes_ambiguity": _normalize_choice(
            item.get("notes_ambiguity"),
            allowed=AMBIGUITY_VALUES,
            default="否",
        ),
        "notes_confidence": notes_confidence,
        "review_points": ensure_list_of_strings(item.get("review_points")),
        "mechanism_eligible": _normalize_choice(
            item.get("mechanism_eligible"),
            allowed=MECHANISM_ELIGIBILITY_VALUES,
            default="否",
        ),
        "mechanism_notes": ensure_list_of_strings(item.get("mechanism_notes")),
        "comparison_keys": ensure_list_of_strings(item.get("comparison_keys")),
        "api_confidence": api_confidence,
    }
    if interaction_event_present != "是":
        normalized["interaction_role"] = "unclear"
        normalized["interaction_target_claim_summary"] = ""
        normalized["interaction_event_codes"] = []
        normalized["interaction_event_basis_codes"] = []
        normalized["interaction_event_outcome"] = ""
        normalized["interaction_evidence"] = []
    return normalized


@dataclass(slots=True)
class PostReviewBatchPrefiller:
    client: DeepSeekClient
    model: str

    def prefill_batch(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        messages = self._build_messages(rows)
        response = self.client.complete_json(model=self.model, messages=messages)
        payload = response["parsed"]
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("DeepSeek response must contain items[]")
        items_by_batch_id = {
            str(item.get("batch_item_id") or "").strip(): item
            for item in items
            if isinstance(item, dict)
        }

        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            batch_item_id = f"item_{index:03d}"
            raw_item = items_by_batch_id.get(batch_item_id)
            if raw_item is None:
                normalized_item = _fallback_item("missing_batch_item")
            else:
                try:
                    normalized_item = _normalize_model_item(
                        raw_item,
                        context_used=str(row.get("context_used") or "none").strip() or "none",
                    )
                except Exception as exc:
                    normalized_item = _fallback_item(
                        f"invalid_model_item: {type(exc).__name__}"
                    )
            normalized_item["model"] = str(response.get("model") or self.model)
            normalized.append(normalized_item)
        return normalized

    def _build_messages(self, rows: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
        items = []
        for index, row in enumerate(rows):
            items.append(
                {"batch_item_id": f"item_{index:03d}"} | _serialize_queue_row_for_model(row)
            )
        user_payload = {
            "task": "post_review_v2_prefill",
            "records": items,
        }
        return [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": (
                    "请仅输出 JSON。下面是需要预填的 post_review_v2 records。\n"
                    + json.dumps(user_payload, ensure_ascii=False)
                ),
            },
        ]


def _evidence_fallback(row: dict[str, Any]) -> list[str]:
    evidence = ensure_list_of_strings(row.get("evidence_master"))
    if evidence:
        return evidence
    source_text = str(row.get("source_text") or "").strip()
    if source_text:
        return [source_text[:160]]
    theme_summary = str(row.get("theme_summary") or "").strip()
    return [theme_summary] if theme_summary else []


def _interaction_payload(normalized: dict[str, Any], *, context_used: str) -> dict[str, Any]:
    if context_used == "none":
        return _empty_interaction_level("none")
    return {
        "event_present": normalized["interaction_event_present"],
        "interaction_role": normalized["interaction_role"],
        "target_claim_summary": normalized["interaction_target_claim_summary"],
        "event_codes": normalized["interaction_event_codes"],
        "event_basis_codes": normalized["interaction_event_basis_codes"],
        "event_outcome": normalized["interaction_event_outcome"],
        "evidence": normalized["interaction_evidence"],
    }


def _api_assistance_payload(
    *,
    used: bool,
    confidence: Any,
    adoption_note: str,
) -> dict[str, Any]:
    return {
        "used": "是" if used else "否",
        "purpose": ["formal_review_prefill"] if used else [],
        "api_confidence": _confidence_label(confidence) if used else "不可用",
        "adoption_note": str(adoption_note or "").strip(),
    }


def _notes_payload(
    *,
    row: dict[str, Any],
    ambiguity: str,
    confidence: str,
    review_points: Sequence[str],
) -> dict[str, Any]:
    return {
        "multi_label": "否",
        "ambiguity": ambiguity,
        "confidence": confidence,
        "review_points": ensure_list_of_strings(review_points),
        "dedup_group": str(row.get("record_id") or row.get("post_id") or "").strip(),
    }


def _fallback_canonical_row(
    row: dict[str, Any],
    *,
    run_id: str,
    reviewer: str,
    review_date: str,
    model: str,
    reason: str,
) -> dict[str, Any]:
    canonical = canonicalize_review_row(
        dict(row),
        base_row=row,
        review_phase=REVIEW_PHASE,
    )
    message = str(reason or "prefill_failed").strip()
    canonical["run_id"] = run_id
    canonical["review_phase"] = REVIEW_PHASE
    canonical["review_status"] = "unreviewed"
    canonical["reviewer"] = reviewer
    canonical["review_date"] = review_date
    canonical["model"] = model
    canonical["decision"] = "待复核"
    canonical["decision_reason"] = format_decision_reason("R11", message)
    canonical["workflow_dimension"] = _empty_workflow_dimension()
    canonical["legitimacy_evaluation"] = _empty_legitimacy_evaluation()
    canonical["boundary_expression"] = _empty_boundary_expression()
    canonical["interaction_level"] = _empty_interaction_level(
        str(canonical.get("context_used") or "none").strip() or "none"
    )
    canonical["claim_units"] = []
    canonical["evidence_master"] = _evidence_fallback(row)
    canonical["api_assistance"] = _api_assistance_payload(
        used=False,
        confidence=0.0,
        adoption_note=message,
    )
    canonical["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": "否",
        "candidate_pattern_notes": [],
        "comparison_keys": [],
    }
    canonical["notes"] = _notes_payload(
        row=row,
        ambiguity="是",
        confidence="低",
        review_points=[message],
    )
    return validate_canonical_row(canonical)


def _model_item_to_canonical(
    row: dict[str, Any],
    *,
    normalized_item: dict[str, Any],
    run_id: str,
    reviewer: str,
    review_date: str,
) -> dict[str, Any]:
    canonical = canonicalize_review_row(
        dict(row),
        base_row=row,
        review_phase=REVIEW_PHASE,
    )
    decision = normalized_item["decision"]
    reason_code = normalized_item["decision_reason_code"]
    reason_note = normalized_item["decision_reason_note"]
    claim_units = normalized_item["claim_units"] if decision == "纳入" else []
    review_points = list(normalized_item["review_points"])

    if decision == "纳入":
        claim_units = _retain_formal_claim_units(claim_units)

    if decision == "纳入" and not _has_meaningful_claim_units(claim_units):
        decision = "待复核"
        reason_code = "R11"
        reason_note = "模型未能给出有效的 claim_units（缺少 workflow_stage_codes 或证据），需人工复核。"
        review_points = review_points + ["模型未能给出有效的 claim_units（缺少 workflow_stage_codes 或证据），需人工复核。"]
        claim_units = []

    if decision == "纳入":
        reason_code = "R12"

    qs_broad_subject = normalized_item["qs_broad_subject"]
    if decision == "纳入" and not qs_broad_subject:
        qs_broad_subject = "uncertain"

    canonical["run_id"] = run_id
    canonical["review_phase"] = REVIEW_PHASE
    canonical["review_status"] = "unreviewed"
    canonical["reviewer"] = reviewer
    canonical["review_date"] = review_date
    canonical["model"] = normalized_item["model"]
    canonical["decision"] = decision
    canonical["decision_reason"] = format_decision_reason(reason_code, reason_note)
    canonical["theme_summary"] = (
        normalized_item["theme_summary"]
        or str(row.get("theme_summary") or "").strip()
        or str(row.get("source_text") or "").strip()[:120]
    )
    canonical["target_practice_summary"] = normalized_item["target_practice_summary"]
    canonical["discursive_mode"] = normalized_item["discursive_mode"]
    canonical["practice_status"] = normalized_item["practice_status"]
    canonical["speaker_position_claimed"] = normalized_item["speaker_position_claimed"]
    canonical["qs_broad_subject"] = qs_broad_subject
    canonical["workflow_dimension"] = _empty_workflow_dimension()
    canonical["legitimacy_evaluation"] = _empty_legitimacy_evaluation()
    canonical["boundary_expression"] = _empty_boundary_expression()
    canonical["interaction_level"] = _interaction_payload(
        normalized_item,
        context_used=str(canonical.get("context_used") or "none").strip() or "none",
    )
    canonical["claim_units"] = claim_units
    canonical["evidence_master"] = normalized_item["evidence_master"] or _evidence_fallback(row)
    canonical["mechanism_memo"] = {
        "eligible_for_mechanism_analysis": normalized_item["mechanism_eligible"],
        "candidate_pattern_notes": normalized_item["mechanism_notes"],
        "comparison_keys": normalized_item["comparison_keys"],
    }
    canonical["api_assistance"] = _api_assistance_payload(
        used=True,
        confidence=normalized_item["api_confidence"],
        adoption_note=reason_note,
    )
    canonical["notes"] = _notes_payload(
        row=row,
        ambiguity=normalized_item["notes_ambiguity"],
        confidence=normalized_item["notes_confidence"],
        review_points=review_points,
    )
    return validate_canonical_row(canonical)


def _prefill_batch_rows(
    batch_rows: Sequence[dict[str, Any]],
    *,
    prefiller: PostReviewBatchPrefiller,
    run_id: str,
    reviewer: str,
    review_date: str,
) -> tuple[list[dict[str, Any]], str | None]:
    try:
        normalized_items = prefiller.prefill_batch(batch_rows)
        return (
            [
                _model_item_to_canonical(
                    row,
                    normalized_item=item,
                    run_id=run_id,
                    reviewer=reviewer,
                    review_date=review_date,
                )
                for row, item in zip(batch_rows, normalized_items)
            ],
            None,
        )
    except Exception as exc:  # pragma: no cover - covered through fallback behavior tests
        message = str(exc).strip()
        reason = f"prefill_batch_error: {type(exc).__name__}"
        if message and isinstance(exc, RuntimeError):
            reason = f"{reason}: {message}"
        return (
            [
                _fallback_canonical_row(
                    row,
                    run_id=run_id,
                    reviewer=reviewer,
                    review_date=review_date,
                    model=prefiller.model,
                    reason=reason,
                )
                for row in batch_rows
            ],
            reason,
        )


def _run_prefill_batches(
    rows: Sequence[dict[str, Any]],
    *,
    prefiller: PostReviewBatchPrefiller,
    run_id: str,
    reviewer: str,
    review_date: str,
    batch_size: int,
    max_workers: int,
    log: Callable[[str], None],
) -> tuple[list[dict[str, Any]], list[str]]:
    batches: list[tuple[int, list[dict[str, Any]]]] = []
    for start in range(0, len(rows), batch_size):
        batches.append((start, list(rows[start : start + batch_size])))

    results: list[dict[str, Any] | None] = [None] * len(rows)
    batch_errors: list[str] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _prefill_batch_rows,
                batch_rows,
                prefiller=prefiller,
                run_id=run_id,
                reviewer=reviewer,
                review_date=review_date,
            ): (start, batch_rows)
            for start, batch_rows in batches
        }
        completed = 0
        for future in as_completed(future_map):
            start, batch_rows = future_map[future]
            batch_rows_result, batch_error = future.result()
            for offset, row in enumerate(batch_rows_result):
                results[start + offset] = row
            if batch_error:
                batch_errors.append(batch_error)
            completed += len(batch_rows)
            log(f"[post_review_prefill] completed {completed}/{len(rows)} rows")

    return [row for row in results if row is not None], batch_errors


def generate_post_review_prefill_draft(
    *,
    queue_path: Path,
    output_path: Path | None = None,
    run_id: str | None = None,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    prefiller: PostReviewBatchPrefiller,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if max_workers <= 0:
        raise ValueError("max_workers must be a positive integer")
    if not queue_path.exists():
        raise FileNotFoundError(f"Queue file not found: {queue_path}")

    queue_rows = _load_jsonl(queue_path)
    _validate_queue_rows(queue_rows)

    resolved_run_id = run_id or _default_run_id(queue_path)
    resolved_review_date = review_date or date.today().isoformat()
    resolved_output_path = _default_output_path(queue_path, output_path=output_path)
    logger = log or (lambda _message: None)

    draft_rows, batch_errors = _run_prefill_batches(
        queue_rows,
        prefiller=prefiller,
        run_id=resolved_run_id,
        reviewer=reviewer,
        review_date=resolved_review_date,
        batch_size=batch_size,
        max_workers=max_workers,
        log=logger,
    )
    draft_path = _write_jsonl(resolved_output_path, draft_rows)

    decision_distribution = Counter(str(row["decision"]) for row in draft_rows)
    summary = {
        "status": "ok" if not batch_errors else "partial_fallback",
        "review_phase": REVIEW_PHASE,
        "queue_path": str(queue_path),
        "output_path": str(draft_path),
        "summary_path": str(_summary_path_for_output(draft_path)),
        "run_id": resolved_run_id,
        "reviewer": reviewer,
        "review_date": resolved_review_date,
        "model": prefiller.model,
        "queue_count": len(queue_rows),
        "draft_count": len(draft_rows),
        "batch_size": batch_size,
        "max_workers": max_workers,
        "decision_distribution": dict(decision_distribution),
        "included_count": decision_distribution.get("纳入", 0),
        "review_needed_count": decision_distribution.get("待复核", 0),
        "excluded_count": decision_distribution.get("剔除", 0),
        "fallback_batch_errors": batch_errors,
    }
    summary_path = _summary_path_for_output(draft_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def run_llm_post_review_prefill(
    *,
    queue_path: Path,
    output_path: Path | None = None,
    run_id: str | None = None,
    reviewer: str = DEFAULT_REVIEWER,
    review_date: str | None = None,
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL,
    model: str = DEFAULT_CHAT_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> dict[str, Any]:
    client = DeepSeekClient.from_env()
    client.base_url = base_url
    client.timeout_seconds = timeout_seconds
    client.max_retries = max_retries
    return generate_post_review_prefill_draft(
        queue_path=queue_path,
        output_path=output_path,
        run_id=run_id,
        reviewer=reviewer,
        review_date=review_date,
        prefiller=PostReviewBatchPrefiller(client=client, model=model),
        batch_size=batch_size,
        max_workers=max_workers,
        log=print,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate DeepSeek-assisted post_review_v2 prefill JSONL for a single batch file."
    )
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--reviewer", default=DEFAULT_REVIEWER)
    parser.add_argument("--review-date", default=None)
    parser.add_argument("--base-url", default=DEFAULT_DEEPSEEK_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_llm_post_review_prefill(
        queue_path=args.queue,
        output_path=args.output,
        run_id=args.run_id,
        reviewer=args.reviewer,
        review_date=args.review_date,
        base_url=args.base_url,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_WORKERS",
    "DEFAULT_REVIEWER",
    "PostReviewBatchPrefiller",
    "generate_post_review_prefill_draft",
    "run_llm_post_review_prefill",
]
