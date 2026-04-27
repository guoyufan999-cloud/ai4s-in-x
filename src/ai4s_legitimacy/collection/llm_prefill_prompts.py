from __future__ import annotations

from typing import Any

from ai4s_legitimacy.collection._jsonl import trim_text as _trim_text
from ai4s_legitimacy.collection.canonical_schema import (
    AMBIGUITY_VALUES,
    BOUNDARY_CONTENT_LABELS,
    BOUNDARY_MODE_LABELS,
    CONFIDENCE_VALUES,
    DECISION_REASON_CODES,
    EVALUATION_LABELS,
    INTERACTION_BASIS_CODES,
    INTERACTION_EVENT_CODES,
    INTERACTION_EVENT_VALUES,
    INTERACTION_OUTCOME_VALUES,
    INTERACTION_ROLE_VALUES,
    LEGITIMACY_LABELS,
    MECHANISM_ELIGIBILITY_VALUES,
    WORKFLOW_STAGE_LABELS,
    ensure_list_of_strings,
)
from ai4s_legitimacy.collection.llm_prefill_normalization import (
    DISCURSIVE_MODE_VALUES,
    PRACTICE_STATUS_VALUES,
    QS_SUBJECT_VALUES,
    SPEAKER_POSITION_VALUES,
)


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
