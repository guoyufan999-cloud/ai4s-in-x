from __future__ import annotations

from typing import Any

from ai4s_legitimacy.collection.canonical_schema import build_empty_canonical_row

from ._canonical_review_common import (
    is_rescreen_phase,
    populate_shared_review_fields,
    resolve_identity,
)
from ._canonical_review_sections import (
    populate_formal_review_sections,
    populate_rescreen_sections,
)


def canonicalize_review_row(
    row: dict[str, Any],
    *,
    base_row: dict[str, Any] | None = None,
    review_phase: str | None = None,
) -> dict[str, Any]:
    resolved_review_phase = review_phase or str(row.get("review_phase") or "").strip()
    record_type, record_id = resolve_identity(row, base_row=base_row)
    canonical = build_empty_canonical_row(record_type, record_id)
    decision = populate_shared_review_fields(
        canonical,
        row,
        base_row=base_row,
        review_phase=resolved_review_phase,
        record_type=record_type,
        record_id=record_id,
    )

    if is_rescreen_phase(resolved_review_phase):
        return populate_rescreen_sections(
            canonical,
            row,
            decision=decision,
            record_id=record_id,
        )
    return populate_formal_review_sections(
        canonical,
        row,
        decision=decision,
        base_row=base_row,
    )
