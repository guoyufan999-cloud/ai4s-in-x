from __future__ import annotations

import re
from typing import Any, Iterable

from .canonical_constants import ALL_CODE_LABELS, DECISION_REASON_CODES, WORKFLOW_DIMENSION_LABELS


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
