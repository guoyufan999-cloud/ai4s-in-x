from __future__ import annotations

from typing import Any, Sequence

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
