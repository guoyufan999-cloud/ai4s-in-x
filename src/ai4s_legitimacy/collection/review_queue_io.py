from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_SUGGESTIONS_DIR,
)

REVIEW_PHASES = (
    "rescreen_posts",
    "post_review",
    "post_review_v2",
    "comment_review",
    "comment_review_v2",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _latest_suggestion_file(
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> Path | None:
    if not suggestions_dir.exists():
        return None
    candidates = [
        path
        for path in suggestions_dir.rglob("*.full_draft.jsonl")
        if "/shards/" not in str(path)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, str(path)))[-1]


def _load_suggestion_index(
    suggestions_dir: Path = REBASELINE_SUGGESTIONS_DIR,
) -> dict[str, dict[str, Any]]:
    suggestion_file = _latest_suggestion_file(suggestions_dir)
    if suggestion_file is None:
        return {}
    index: dict[str, dict[str, Any]] = {}
    for row in _load_jsonl(suggestion_file):
        post_id = str(row.get("post_id") or row.get("record_id") or "").strip()
        if post_id:
            index[post_id] = row
    return index


def _default_output_path(phase: str) -> Path:
    return REBASELINE_REVIEW_QUEUE_DIR / f"{phase}.jsonl"
