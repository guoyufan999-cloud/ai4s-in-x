from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from ai4s_legitimacy.coding.codebook_seed import LEGACY_WORKFLOW_TO_STAGE_CODE
from ai4s_legitimacy.collection._canonical_review import canonicalize_review_row
from ai4s_legitimacy.collection.canonical_schema import (
    format_decision_reason,
    sample_status_to_decision,
    validate_canonical_row,
)
from ai4s_legitimacy.config.formal_baseline import (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_REVIEWED_DIR,
    REBASELINE_SUGGESTIONS_DIR,
)
from ai4s_legitimacy.config.settings import OUTPUTS_DIR

DEFAULT_MANIFEST_PATH = (
    OUTPUTS_DIR / "reports" / "freeze_checkpoints" / "canonical_backfill_manifest.json"
)
DEFAULT_ROOTS = (
    REBASELINE_REVIEW_QUEUE_DIR,
    REBASELINE_REVIEWED_DIR,
    REBASELINE_SUGGESTIONS_DIR,
    OUTPUTS_DIR / "tables",
    Path("archive"),
)
SUPPORTED_SUFFIXES = {".jsonl", ".json", ".csv"}
NON_RECORD_NAME_MARKERS = (
    "summary",
    "manifest",
    "checkpoint",
    "consistency_report",
    "delta_report",
    "snapshot",
)
NON_RECORD_KEYS = {
    "generated_at_utc",
    "generated_at",
    "outputs",
    "entries",
    "batches",
    "counts",
    "delta",
    "status",
    "queue_path",
    "batch_count",
    "row_count",
    "view_source",
}

LEGACY_ATTITUDE_TO_CODE = {
    "积极采用": "B1",
    "积极但保留": "B2",
    "中性经验帖": "B0",
    "批判_担忧": "B3",
    "明确拒绝": "B3",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return rows, "jsonl"
    if suffix == ".json":
        stripped = path.read_text(encoding="utf-8").strip()
        if not stripped:
            return [], "json"
        payload = json.loads(stripped)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)], "json_array"
        if isinstance(payload, dict):
            return [payload], "json_object"
        raise ValueError("JSON payload must be an object or array of objects")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader], "csv"
    raise ValueError(f"Unsupported suffix: {suffix}")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _infer_review_phase(path: Path, row: dict[str, Any]) -> str:
    review_phase = str(row.get("review_phase") or "").strip()
    if review_phase:
        return review_phase
    name = path.name
    for candidate in (
        "rescreen_posts",
        "post_review_v2",
        "comment_review_v2",
        "post_review",
        "comment_review",
    ):
        if candidate in name:
            return candidate
    if "external_xhs" in name:
        return "external_opencli_pilot"
    return "historical_backfill"


def _legacy_note_to_canonical(row: dict[str, Any]) -> dict[str, Any]:
    note_id = str(row.get("note_id") or "").strip()
    if not note_id:
        raise ValueError("Legacy note JSON missing note_id")
    workflow_label = str(row.get("workflow_primary") or "").strip()
    workflow_code = LEGACY_WORKFLOW_TO_STAGE_CODE.get(workflow_label, "")
    legitimacy_code = LEGACY_ATTITUDE_TO_CODE.get(str(row.get("attitude_polarity") or "").strip(), "")
    title = str(row.get("title") or "").strip()
    source_text = "\n".join(
        part
        for part in (
            title,
            str(row.get("full_text") or "").strip(),
        )
        if part
    ).strip()
    decision = sample_status_to_decision(str(row.get("sample_status") or "").strip())
    seed = {
        "record_type": "post",
        "record_id": note_id,
        "post_id": note_id,
        "post_url": str(
            row.get("canonical_url") or row.get("source_url") or ""
        ).strip(),
        "created_at": str(row.get("publish_time") or row.get("created_at") or "").strip(),
        "source_text": source_text,
        "theme_summary": title,
        "decision": decision,
        "decision_reason": format_decision_reason(
            "R12" if decision == "纳入" else "R11" if decision == "待复核" else "R2",
            "Migrated from legacy note export.",
        ),
        "workflow_stage": workflow_code or workflow_label,
        "primary_legitimacy_code": legitimacy_code,
        "qs_broad_subject": str(row.get("qs_broad_subject") or "").strip(),
        "review_phase": "legacy_backfill",
        "review_status": "reviewed",
    }
    return validate_canonical_row(
        canonicalize_review_row(seed, base_row=seed, review_phase="legacy_backfill")
    )


def _canonicalize_row(path: Path, row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    try:
        return validate_canonical_row(row), True
    except Exception:
        pass

    if "note_id" in row and not str(row.get("record_id") or row.get("post_id") or "").strip():
        return _legacy_note_to_canonical(row), False

    review_phase = _infer_review_phase(path, row)
    canonical = canonicalize_review_row(
        row,
        base_row=row,
        review_phase=review_phase,
    )
    if canonical["review_status"] == "unreviewed" and review_phase != "rescreen_posts":
        canonical["review_status"] = "reviewed"
    if not canonical.get("decision_reason"):
        decision = canonical["decision"]
        canonical["decision_reason"] = format_decision_reason(
            "R11" if decision == "待复核" else "R12" if decision == "纳入" else "R2",
            str(row.get("reason") or row.get("ai_review_reason") or "").strip(),
        )
    return validate_canonical_row(canonical), False


def _looks_like_non_record_payload(path: Path, rows: list[dict[str, Any]]) -> bool:
    lowered_name = path.name.lower()
    if any(marker in lowered_name for marker in NON_RECORD_NAME_MARKERS):
        return True
    if len(rows) != 1:
        return False
    row = rows[0]
    record_keys = {
        "record_id",
        "post_id",
        "comment_id",
        "note_id",
        "source_text",
        "decision",
        "review_phase",
    }
    if record_keys & set(row):
        return False
    return bool(NON_RECORD_KEYS & set(row))


def _iter_candidate_files(root_dirs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in root_dirs:
        root = Path(root)
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix.lower() in SUPPORTED_SUFFIXES:
                files.append(root)
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
                files.append(path)
    return files


def backfill_canonical_history(
    *,
    root_dirs: Iterable[Path] = DEFAULT_ROOTS,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    converted_files = 0
    skipped_files = 0
    preserved_non_record_files = 0
    preserved_empty_files = 0
    converted_rows = 0
    for path in _iter_candidate_files(root_dirs):
        original_sha = _sha256(path)
        try:
            rows, parse_mode = _load_rows(path)
            if not rows:
                preserved_empty_files += 1
                entries.append(
                    {
                        "path": str(path),
                        "parse_mode": parse_mode,
                        "original_sha256": original_sha,
                        "rewritten_sha256": original_sha,
                        "records": 0,
                        "status": "preserved_empty",
                        "migrated_at_utc": datetime.now(UTC).isoformat(),
                    }
                )
                continue
            if _looks_like_non_record_payload(path, rows):
                preserved_non_record_files += 1
                entries.append(
                    {
                        "path": str(path),
                        "parse_mode": parse_mode,
                        "original_sha256": original_sha,
                        "rewritten_sha256": original_sha,
                        "records": len(rows),
                        "status": "preserved_non_record",
                        "migrated_at_utc": datetime.now(UTC).isoformat(),
                    }
                )
                continue
            canonical_rows: list[dict[str, Any]] = []
            already_canonical = True
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("row is not a JSON object")
                canonical, is_canonical = _canonicalize_row(path, row)
                canonical_rows.append(canonical)
                already_canonical = already_canonical and is_canonical
            if not canonical_rows:
                raise ValueError("no canonicalizable record rows found")
            _write_jsonl(path, canonical_rows)
            converted_files += 1
            converted_rows += len(canonical_rows)
            entries.append(
                {
                    "path": str(path),
                    "parse_mode": parse_mode,
                    "original_sha256": original_sha,
                    "rewritten_sha256": _sha256(path),
                    "records": len(canonical_rows),
                    "lossless": already_canonical,
                    "status": "migrated",
                    "migrated_at_utc": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as exc:
            skipped_files += 1
            entries.append(
                {
                    "path": str(path),
                    "original_sha256": original_sha,
                    "status": "skipped",
                    "reason": str(exc),
                    "migrated_at_utc": datetime.now(UTC).isoformat(),
                }
            )

    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "roots": [str(Path(root)) for root in root_dirs],
        "converted_files": converted_files,
        "skipped_files": skipped_files,
        "preserved_non_record_files": preserved_non_record_files,
        "preserved_empty_files": preserved_empty_files,
        "converted_rows": converted_rows,
        "entries": entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill versioned historical exports into canonical JSONL rows."
    )
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        default=None,
        help="Root directory or file to backfill. Can be supplied multiple times.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    roots = [Path(item) for item in args.roots] if args.roots else list(DEFAULT_ROOTS)
    manifest = backfill_canonical_history(
        root_dirs=roots,
        manifest_path=args.manifest,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


__all__ = ["backfill_canonical_history", "main"]
