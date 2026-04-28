from __future__ import annotations

import re
from typing import Any

from .canonical_constants import (
    BOUNDARY_CONTENT_CODE_SET,
    BOUNDARY_MODE_CODE_SET,
    EVALUATION_CODE_SET,
    LEGITIMACY_CODE_SET,
    OLD_BOUNDARY_TO_CONTENT_CODE,
    WORKFLOW_CODE_SET,
)
from .canonical_utils import ensure_list_of_strings


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
        if text.startswith((f"{code}：", f"{code}:", f"{code}-", f"{code}_")):
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
