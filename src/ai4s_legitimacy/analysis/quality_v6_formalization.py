from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis.figure_generation import (
    generate_submission_figures,
    write_figure_manifest,
)
from ai4s_legitimacy.analysis.figures.config import resolve_paper_scope_coverage_end_date
from ai4s_legitimacy.analysis.framework_v2_materials import generate_framework_v2_materials
from ai4s_legitimacy.collection.canonical_schema import (
    WORKFLOW_STAGE_LABELS,
    normalize_claim_units,
)
from ai4s_legitimacy.config.formal_baseline import (
    QUALITY_V6_ARTIFACT_PROVENANCE_PATH,
    QUALITY_V6_CONSISTENCY_REPORT_PATH,
    QUALITY_V6_FIGURE_DIR,
    QUALITY_V6_FREEZE_CHECKPOINT_MARKDOWN_PATH,
    QUALITY_V6_FREEZE_CHECKPOINT_PATH,
    QUALITY_V6_PAPER_MATERIALS_DIR,
    QUALITY_V6_STAGE,
    QUALITY_V6_STAGING_DB_PATH,
    paper_quality_view,
    paper_scope_contract_name,
    paper_scope_view,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import (
    OUTPUTS_DIR,
    RESEARCH_DB_PATH,
)
from ai4s_legitimacy.utils.db import checkpoint_sqlite_wal, connect_sqlite_readonly
from ai4s_legitimacy.utils.paths import project_relative_path, resolve_project_path

SUPPLEMENTAL_SCOPE = "xhs_expansion_candidate_v1"
SUPPLEMENTAL_FORMALIZATION_SCOPE = "supplemental_formalization_v1"
QUALITY_V6_IMPORT_BATCH = (
    "quality_v6_xhs_expansion_candidate_v1_supplemental_formalization_v1"
)
QUALITY_V6_REVIEW_RUN_ID = (
    "quality_v6_supplemental_formalization_v1_post_review_v2"
)
SUPPLEMENTAL_REVIEWED_PATH = (
    Path("data")
    / "interim"
    / SUPPLEMENTAL_SCOPE
    / SUPPLEMENTAL_FORMALIZATION_SCOPE
    / "supplemental_formalization_v1.codex_reviewed.jsonl"
)
QUALITY_V6_SUMMARY_PATH = (
    OUTPUTS_DIR / "reports" / "freeze_checkpoints" / "quality_v6_research_db_summary.json"
)
QUALITY_V6_TABLE_DIR = OUTPUTS_DIR / "tables" / QUALITY_V6_STAGE

WORKFLOW_SOURCE_TO_CODE = {
    "literature_processing": "A1.2",
    "research_design": "A1.3",
    "data_analysis_or_code": "A1.6",
    "paper_writing": "A1.9",
    "research_training": "A3.5",
    "research_governance": "A2.7",
}
WORKFLOW_CODE_TO_DOMAIN = {"A1": "P", "A2": "G", "A3": "T"}
LEGITIMACY_TO_STANCE = {
    "B0": "中性经验帖",
    "B1": "积极采用",
    "B2": "积极但保留",
    "B3": "质疑/否定",
    "B4": "混合/冲突性评价",
    "B5": "无法判断",
}
TEXT_TYPE_TO_DISCURSIVE_MODE = {
    "工具推荐": "advice_guidance",
    "经验分享": "experience_share",
    "教程展示": "practice_demo",
    "风险提醒": "criticism",
    "伦理批评": "criticism",
    "规范解读": "policy_statement",
    "评论争论": "reflection",
    "其他": "unclear",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row}) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def _remove_sqlite_sidecars(db_path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(db_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()


def _file_record(path: Path) -> dict[str, Any]:
    resolved = Path(path)
    record: dict[str, Any] = {
        "path": project_relative_path(resolved),
        "exists": resolved.exists(),
    }
    if resolved.exists():
        record.update(
            {
                "sha256": _sha256(resolved),
                "bytes": resolved.stat().st_size,
                "line_count": _line_count(resolved),
            }
        )
    return record


def _json_list(values: Any) -> str:
    return json.dumps(values if isinstance(values, list) else [], ensure_ascii=False)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _first_code(row: Mapping[str, Any], field: str) -> str:
    values = row.get(field)
    if isinstance(values, list) and values:
        return str(values[0] or "").strip()
    return ""


def _practice_position(row: Mapping[str, Any]) -> dict[str, Any]:
    value = row.get("practice_position")
    return value if isinstance(value, dict) else {}


def _workflow_code(row: Mapping[str, Any]) -> str:
    practice = _practice_position(row)
    source_field = _clean_text(practice.get("source_field"))
    return WORKFLOW_SOURCE_TO_CODE.get(source_field, "")


def _workflow_stage(row: Mapping[str, Any]) -> str:
    code = _workflow_code(row)
    if code:
        return WORKFLOW_STAGE_LABELS[code]
    return "uncertain"


def _workflow_domain(row: Mapping[str, Any]) -> str | None:
    code = _workflow_code(row)
    if not code:
        return None
    return WORKFLOW_CODE_TO_DOMAIN.get(code.split(".", 1)[0])


def _discursive_mode(row: Mapping[str, Any]) -> str:
    context = row.get("discourse_context")
    text_type = ""
    if isinstance(context, dict):
        text_type = _clean_text(context.get("text_type"))
    elif isinstance(context, str):
        text_type = context
    return TEXT_TYPE_TO_DISCURSIVE_MODE.get(text_type, "unclear")


def _stance(row: Mapping[str, Any]) -> str:
    return LEGITIMACY_TO_STANCE.get(_first_code(row, "normative_evaluation_tendency_codes"), "中性经验帖")


def _claim_evidence(item: Mapping[str, Any], fallback: str) -> list[str]:
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        return [_clean_text(value) for value in evidence if _clean_text(value)]
    if _clean_text(evidence):
        return [_clean_text(evidence)]
    return [fallback[:240]] if fallback else []


def _code_evidence_entries(codes: Iterable[str], evidence: str) -> list[dict[str, str]]:
    return [{"code": code, "evidence": evidence[:240]} for code in codes if code]


def _canonical_claim_units(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_units = row.get("claim_units")
    units = raw_units if isinstance(raw_units, list) else []
    workflow_code = _workflow_code(row)
    fallback_evidence = _clean_text(row.get("content_text"))
    canonical_units: list[dict[str, Any]] = []
    for index, item in enumerate(units, start=1):
        if not isinstance(item, dict):
            continue
        evidence_values = _claim_evidence(item, fallback_evidence)
        evidence = evidence_values[0] if evidence_values else fallback_evidence[:240]
        canonical_units.append(
            {
                "practice_unit": _clean_text(item.get("practice_unit"))
                or f"quality_v6 supplemental claim {index}",
                "workflow_stage_codes": [workflow_code] if workflow_code else [],
                "legitimacy_codes": item.get("normative_evaluation_tendency_codes") or [],
                "basis_codes": _code_evidence_entries(
                    item.get("normative_evaluation_standard_codes") or [],
                    evidence,
                ),
                "boundary_codes": _code_evidence_entries(
                    item.get("boundary_type_codes") or [],
                    evidence,
                ),
                "boundary_mode_codes": _code_evidence_entries(
                    item.get("boundary_mode_codes") or [],
                    evidence,
                ),
                "ai_intervention_mode_codes": item.get("ai_intervention_mode_codes") or [],
                "ai_intervention_intensity_codes": item.get("ai_intervention_intensity_codes") or [],
                "evaluation_tension_codes": item.get("evaluation_tension_codes") or [],
                "formal_norm_reference_codes": item.get("formal_norm_reference_codes") or [],
                "boundary_mechanism_codes": item.get("boundary_mechanism_codes") or [],
                "boundary_result_codes": item.get("boundary_result_codes") or [],
                "evidence": evidence_values,
            }
        )
    if not canonical_units:
        evidence = fallback_evidence[:240]
        canonical_units.append(
            {
                "practice_unit": "quality_v6 supplemental claim",
                "workflow_stage_codes": [workflow_code] if workflow_code else [],
                "legitimacy_codes": row.get("normative_evaluation_tendency_codes") or [],
                "basis_codes": _code_evidence_entries(
                    row.get("normative_evaluation_standard_codes") or [],
                    evidence,
                ),
                "boundary_codes": _code_evidence_entries(
                    row.get("boundary_type_codes") or [],
                    evidence,
                ),
                "boundary_mode_codes": _code_evidence_entries(
                    row.get("boundary_mode_codes") or [],
                    evidence,
                ),
                "ai_intervention_mode_codes": row.get("ai_intervention_mode_codes") or [],
                "ai_intervention_intensity_codes": row.get("ai_intervention_intensity_codes") or [],
                "evaluation_tension_codes": row.get("evaluation_tension_codes") or [],
                "formal_norm_reference_codes": row.get("formal_norm_reference_codes") or [],
                "boundary_mechanism_codes": row.get("boundary_mechanism_codes") or [],
                "boundary_result_codes": row.get("boundary_result_codes") or [],
                "evidence": [evidence] if evidence else [],
            }
        )
    return normalize_claim_units(canonical_units)


def _post_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    post_id = _clean_text(row.get("candidate_id"))
    claim_units = _canonical_claim_units(row)
    evidence = [
        evidence
        for unit in claim_units
        for evidence in unit.get("evidence", [])
        if _clean_text(evidence)
    ]
    return {
        "record_type": "post",
        "record_id": post_id,
        "post_id": post_id,
        "review_phase": "post_review_v2",
        "run_id": QUALITY_V6_REVIEW_RUN_ID,
        "reviewer": _clean_text(row.get("reviewer")) or "codex_assisted_supplemental_formalization",
        "review_date": _clean_text(row.get("reviewed_at"))[:10] or "2026-04-29",
        "decision": "纳入",
        "review_status": "reviewed",
        "framework_v2_update": True,
        "quality_v6_formal": True,
        "quality_v5_formal": False,
        "source_scope": SUPPLEMENTAL_SCOPE,
        "formalization_scope": SUPPLEMENTAL_FORMALIZATION_SCOPE,
        "comment_review_v2_scope": False,
        "title": _clean_text(row.get("title")),
        "content_text": _clean_text(row.get("content_text")),
        "post_url": _clean_text(row.get("post_url")),
        "post_date": _clean_text(row.get("post_date")),
        "claim_units": claim_units,
        "evidence_master": evidence,
        "supplemental_source": dict(row),
    }


def _post_db_row(row: Mapping[str, Any], *, import_batch_id: int) -> dict[str, Any]:
    post_id = _clean_text(row.get("candidate_id"))
    reviewed_date = _clean_text(row.get("reviewed_at"))[:10] or "2026-04-29"
    claim_units = _canonical_claim_units(row)
    boundary_present = any(unit.get("boundary_codes") for unit in claim_units)
    first_boundary = ""
    for unit in claim_units:
        for entry in unit.get("boundary_codes", []):
            if isinstance(entry, dict) and entry.get("code"):
                first_boundary = str(entry["code"])
                break
        if first_boundary:
            break
    return {
        "post_id": post_id,
        "platform": _clean_text(row.get("platform")) or "xiaohongshu",
        "legacy_note_id": _clean_text(row.get("note_id")) or None,
        "legacy_crawl_status": "supplemental_verified",
        "post_url": _clean_text(row.get("post_url")),
        "author_id_hashed": _clean_text(row.get("author_id_hashed")) or None,
        "author_name_masked": _clean_text(row.get("author_name_masked")) or "匿名化作者",
        "post_date": _clean_text(row.get("post_date")),
        "capture_date": reviewed_date,
        "title": _clean_text(row.get("title")),
        "content_text": _clean_text(row.get("content_text")),
        "keyword_query": _clean_text(row.get("query")),
        "is_public": 1,
        "sample_status": "true",
        "decision_reason": "quality_v6_supplemental_formalization_include",
        "actor_type": "uncertain",
        "qs_broad_subject": "uncertain",
        "workflow_domain": _workflow_domain(row),
        "workflow_stage": _workflow_stage(row),
        "primary_legitimacy_stance": _stance(row),
        "has_legitimacy_evaluation": 1
        if _first_code(row, "normative_evaluation_tendency_codes") not in {"", "B0", "B5"}
        else 0,
        "primary_legitimacy_code": _first_code(row, "normative_evaluation_standard_codes"),
        "boundary_discussion": 1 if boundary_present else 0,
        "primary_boundary_type": first_boundary or None,
        "risk_themes_json": "[]",
        "ai_tools_json": "[]",
        "benefit_themes_json": "[]",
        "import_batch_id": import_batch_id,
        "task_batch_id": QUALITY_V6_IMPORT_BATCH,
        "coder_version": "supplemental_formalization_v1",
        "language": "zh",
        "context_available": "否",
        "context_used": "none",
        "decision": "纳入",
        "decision_reason_json": _json_list(["quality_v6 supplemental include"]),
        "theme_summary": (_clean_text(row.get("title")) or _clean_text(row.get("content_text")))[:160],
        "target_practice_summary": _workflow_stage(row),
        "evidence_master_json": _json_list(
            [
                evidence
                for unit in claim_units
                for evidence in unit.get("evidence", [])
                if _clean_text(evidence)
            ]
        ),
        "discursive_mode": _discursive_mode(row),
        "practice_status": "actual_use_or_discussion",
        "speaker_position_claimed": "unclear",
        "boundary_present": "是" if boundary_present else "否",
        "interaction_event_present": "不适用",
        "mechanism_eligible": "否",
        "mechanism_notes_json": "[]",
        "comparison_keys_json": _json_list([_clean_text(row.get("note_id"))]),
        "api_assistance_used": "否",
        "api_assistance_purpose_json": "[]",
        "api_assistance_confidence": "无",
        "api_assistance_note": "No LLM prefill; quality_v6 uses supplemental_formalization_v1 reviewed payload.",
        "notes_multi_label": "是" if len(claim_units) > 1 else "否",
        "notes_ambiguity": "否",
        "notes_confidence": "中",
        "notes_review_points_json": "[]",
        "notes_dedup_group": _clean_text(row.get("note_id")) or post_id,
        "review_status": "reviewed",
        "notes": (
            "quality_v6_formal=true; quality_v5_formal=false; "
            f"source_scope={SUPPLEMENTAL_SCOPE}; "
            f"formalization_scope={SUPPLEMENTAL_FORMALIZATION_SCOPE}; "
            "formal_comments=false"
        ),
    }


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _insert_mapping(connection: sqlite3.Connection, table: str, values: Mapping[str, Any]) -> None:
    columns = [column for column in values if column in _table_columns(connection, table)]
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    connection.execute(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        [values[column] for column in columns],
    )


def _insert_import_batch(connection: sqlite3.Connection, supplemental_rows: list[dict[str, Any]]) -> int:
    connection.execute(
        """
        INSERT OR IGNORE INTO import_batches (
            batch_name, source_description, source_db_path, source_freeze_version,
            record_post_count, record_comment_count, notes
        ) VALUES (?, ?, ?, ?, ?, 0, ?)
        """,
        (
            QUALITY_V6_IMPORT_BATCH,
            "quality_v6 post-only supplemental import from xhs_expansion_candidate_v1",
            project_relative_path(SUPPLEMENTAL_REVIEWED_PATH),
            SUPPLEMENTAL_FORMALIZATION_SCOPE,
            len(supplemental_rows),
            "quality_v6_formal=true; quality_v5_formal=false; formal_comments=false",
        ),
    )
    row = connection.execute(
        "SELECT batch_id FROM import_batches WHERE batch_name = ?",
        (QUALITY_V6_IMPORT_BATCH,),
    ).fetchone()
    if row is None:
        raise RuntimeError("quality_v6 import batch was not created")
    return int(row["batch_id"] if hasattr(row, "keys") else row[0])


def _insert_review_run(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO review_runs (
            run_id, review_phase, model, reviewer, review_date, source_file, notes
        ) VALUES (?, 'post_review_v2', NULL, ?, '2026-04-29', ?, ?)
        """,
        (
            QUALITY_V6_REVIEW_RUN_ID,
            "codex_assisted_supplemental_formalization",
            project_relative_path(SUPPLEMENTAL_REVIEWED_PATH),
            "quality_v6 supplemental post-only formalization; no comment_review_v2 import",
        ),
    )


def validate_supplemental_rows(
    supplemental_path: Path = SUPPLEMENTAL_REVIEWED_PATH,
    *,
    base_db_path: Path = RESEARCH_DB_PATH,
    expected_include_count: int = 200,
    expected_exclude_count: int = 6,
) -> dict[str, Any]:
    rows = _read_jsonl(supplemental_path)
    include_rows = [row for row in rows if row.get("supplemental_formalization_decision") == "include"]
    exclude_rows = [row for row in rows if row.get("supplemental_formalization_decision") == "exclude"]
    failures: list[str] = []

    def _duplicates(values: Iterable[str]) -> list[str]:
        counter = Counter(value for value in values if value)
        return sorted(value for value, count in counter.items() if count > 1)

    if len(include_rows) != expected_include_count:
        failures.append(
            f"include_count={len(include_rows)}; expected {expected_include_count}"
        )
    if len(exclude_rows) != expected_exclude_count:
        failures.append(
            f"exclude_count={len(exclude_rows)}; expected {expected_exclude_count}"
        )
    if _duplicates(_clean_text(row.get("candidate_id")) for row in include_rows):
        failures.append("duplicate candidate_id in include rows")
    if _duplicates(_clean_text(row.get("note_id")) for row in include_rows):
        failures.append("duplicate note_id in include rows")
    if _duplicates(_clean_text(row.get("post_url")) for row in include_rows):
        failures.append("duplicate post_url in include rows")
    for row in include_rows:
        if not _clean_text(row.get("candidate_id")):
            failures.append("include row missing candidate_id")
        if not _clean_text(row.get("post_url")):
            failures.append(f"{row.get('candidate_id')}: missing post_url")
        if len(_clean_text(row.get("content_text"))) < 20:
            failures.append(f"{row.get('candidate_id')}: content_text too short")
        if row.get("author_name") or row.get("author_id"):
            failures.append(f"{row.get('candidate_id')}: contains raw author field")
        if row.get("quality_v5_formal") is True or row.get("quality_v5_formal_scope") is True:
            failures.append(f"{row.get('candidate_id')}: marked as quality_v5 formal")

    collisions = {"candidate_id": 0, "note_id": 0, "post_url": 0}
    if base_db_path.exists():
        with connect_sqlite_readonly(base_db_path) as connection:
            existing_post_ids = {
                str(row["post_id"])
                for row in connection.execute("SELECT post_id FROM posts").fetchall()
            }
            existing_note_ids = {
                str(row["legacy_note_id"])
                for row in connection.execute(
                    "SELECT legacy_note_id FROM posts WHERE legacy_note_id IS NOT NULL"
                ).fetchall()
            }
            existing_urls = {
                str(row["post_url"])
                for row in connection.execute(
                    "SELECT post_url FROM posts WHERE post_url IS NOT NULL"
                ).fetchall()
            }
        collisions = {
            "candidate_id": sum(
                1 for row in include_rows if _clean_text(row.get("candidate_id")) in existing_post_ids
            ),
            "note_id": sum(
                1 for row in include_rows if _clean_text(row.get("note_id")) in existing_note_ids
            ),
            "post_url": sum(
                1 for row in include_rows if _clean_text(row.get("post_url")) in existing_urls
            ),
        }
        for field, count in collisions.items():
            if count:
                failures.append(f"{field}_collisions={count}")

    return {
        "status": "pass" if not failures else "fail",
        "total_rows": len(rows),
        "include_rows": len(include_rows),
        "exclude_rows": len(exclude_rows),
        "collisions_with_base_db": collisions,
        "failures": failures,
    }


def prepare_quality_v6_staging_db(
    *,
    base_db_path: Path = RESEARCH_DB_PATH,
    supplemental_path: Path = SUPPLEMENTAL_REVIEWED_PATH,
    output_db_path: Path = QUALITY_V6_STAGING_DB_PATH,
    expected_include_count: int = 200,
    expected_exclude_count: int = 6,
) -> dict[str, Any]:
    validation = validate_supplemental_rows(
        supplemental_path,
        base_db_path=base_db_path,
        expected_include_count=expected_include_count,
        expected_exclude_count=expected_exclude_count,
    )
    if validation["status"] != "pass":
        raise ValueError(f"quality_v6 supplemental validation failed: {validation['failures']}")
    output_db_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_sqlite_wal(base_db_path)
    _remove_sqlite_sidecars(base_db_path)
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(output_db_path) + suffix)
        if candidate.exists():
            candidate.unlink()
    shutil.copy2(base_db_path, output_db_path)

    supplemental_rows = [
        row
        for row in _read_jsonl(supplemental_path)
        if row.get("supplemental_formalization_decision") == "include"
    ]
    connection = sqlite3.connect(output_db_path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        batch_id = _insert_import_batch(connection, supplemental_rows)
        _insert_review_run(connection)
        for row in supplemental_rows:
            post_id = _clean_text(row.get("candidate_id"))
            _insert_mapping(connection, "posts", _post_db_row(row, import_batch_id=batch_id))
            payload = _post_payload(row)
            connection.execute(
                """
                INSERT INTO reviewed_records (
                    run_id, record_id, record_type, review_phase, payload_json
                ) VALUES (?, ?, 'post', 'post_review_v2', ?)
                """,
                (
                    QUALITY_V6_REVIEW_RUN_ID,
                    post_id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            for index, unit in enumerate(payload["claim_units"]):
                connection.execute(
                    """
                    INSERT INTO claim_units (
                        record_type, record_id, claim_index, practice_unit,
                        workflow_stage_codes_json, legitimacy_codes_json,
                        basis_codes_json, boundary_codes_json, boundary_mode_codes_json,
                        evidence_json
                    ) VALUES ('post', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        index,
                        unit.get("practice_unit") or "",
                        _json_list(unit.get("workflow_stage_codes") or []),
                        _json_list(unit.get("legitimacy_codes") or []),
                        _json_list(unit.get("basis_codes") or []),
                        _json_list(unit.get("boundary_codes") or []),
                        _json_list(unit.get("boundary_mode_codes") or []),
                        _json_list(unit.get("evidence") or []),
                    ),
                )
        connection.executescript(render_views_sql())
        connection.commit()
    finally:
        connection.close()
    checkpoint_sqlite_wal(output_db_path)
    _remove_sqlite_sidecars(output_db_path)
    return {
        "status": "ok",
        "staging_db_path": str(output_db_path),
        "base_db_path": str(base_db_path),
        "supplemental_path": str(supplemental_path),
        "import_batch": QUALITY_V6_IMPORT_BATCH,
        "review_run_id": QUALITY_V6_REVIEW_RUN_ID,
        "imported_posts": len(supplemental_rows),
        "validation": validation,
    }


def _scope_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        str(row["scope_name"]): int(row["row_count"] or 0)
        for row in connection.execute(
            "SELECT scope_name, row_count FROM vw_scope_counts ORDER BY scope_name"
        ).fetchall()
    }


def _fetch_rows(connection: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql).fetchall()]


def _stage_distribution_queries(stage: str) -> dict[str, str]:
    return {
        "monthly_posts_by_workflow": f"""
            SELECT period_month, workflow_stage, post_count
            FROM {paper_quality_view("posts_by_month_workflow", stage)}
            ORDER BY period_month, workflow_stage
        """,
        "subject_distribution": f"""
            SELECT subject_label, post_count
            FROM {paper_quality_view("subject_distribution", stage)}
            ORDER BY post_count DESC, subject_label
        """,
        "workflow_distribution": f"""
            SELECT workflow_stage, post_count
            FROM {paper_quality_view("workflow_distribution", stage)}
            ORDER BY post_count DESC, workflow_stage
        """,
    }


def _stage_cross_tab_queries(stage: str) -> dict[str, str]:
    return {
        "workflow_legitimacy": f"""
            SELECT workflow_stage, legitimacy_stance, post_count
            FROM {paper_quality_view("workflow_legitimacy_cross", stage)}
            ORDER BY workflow_stage, legitimacy_stance
        """,
        "subject_workflow": f"""
            SELECT subject_label, workflow_stage, post_count
            FROM {paper_quality_view("subject_workflow_cross", stage)}
            ORDER BY post_count DESC, subject_label, workflow_stage
        """,
        "subject_legitimacy": f"""
            SELECT subject_label, legitimacy_stance, post_count
            FROM {paper_quality_view("subject_legitimacy_cross", stage)}
            ORDER BY post_count DESC, subject_label, legitimacy_stance
        """,
        "halfyear_workflow": f"""
            SELECT half_year, workflow_stage, post_count
            FROM {paper_quality_view("halfyear_workflow", stage)}
            ORDER BY half_year, workflow_stage
        """,
        "halfyear_subject": f"""
            SELECT half_year, subject_label, post_count
            FROM {paper_quality_view("halfyear_subject", stage)}
            ORDER BY half_year, subject_label
        """,
    }


def build_quality_v6_summary_payload(db_path: Path = QUALITY_V6_STAGING_DB_PATH) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path) as connection:
        counts = _scope_counts(connection)
        coverage_end_date = resolve_paper_scope_coverage_end_date(connection, stage=QUALITY_V6_STAGE)
        distributions = {
            name: _fetch_rows(connection, sql)
            for name, sql in _stage_distribution_queries(QUALITY_V6_STAGE).items()
        }
        cross_tabs = {
            name: _fetch_rows(connection, sql)
            for name, sql in _stage_cross_tab_queries(QUALITY_V6_STAGE).items()
        }
        research_counts = {
            "posts": int(connection.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"]),
            "comments": int(connection.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"]),
        }
        supplemental_imported = int(
            connection.execute(
                """
                SELECT COUNT(*) AS c
                FROM posts
                WHERE import_batch_id IN (
                    SELECT batch_id FROM import_batches WHERE batch_name = ?
                )
                """,
                (QUALITY_V6_IMPORT_BATCH,),
            ).fetchone()["c"]
        )
    return {
        "research_db": {
            **research_counts,
            "scope_counts": counts,
            "staging_db_path": project_relative_path(db_path),
        },
        "paper_quality_v5_guard": {
            "formal_posts": counts.get("paper_quality_v5_posts", 0),
            "formal_comments": counts.get("paper_quality_v5_comments", 0),
        },
        "paper_quality_v6": {
            "formal_posts": counts.get("paper_quality_v6_posts", 0),
            "formal_comments": counts.get("paper_quality_v6_comments", 0),
            "coverage_end_date": coverage_end_date,
            "source_contract": paper_scope_contract_name(QUALITY_V6_STAGE),
            "source_composition": {
                "quality_v5_posts": counts.get("paper_quality_v5_posts", 0),
                "supplemental_formalized_posts": supplemental_imported,
                "comment_review_v2": "deferred",
            },
            **distributions,
            "cross_tabs": cross_tabs,
        },
    }


def evaluate_quality_v6_consistency(
    *,
    db_path: Path = QUALITY_V6_STAGING_DB_PATH,
    checkpoint_path: Path = QUALITY_V6_FREEZE_CHECKPOINT_PATH,
    expected_quality_v5_posts: int = 514,
    expected_quality_v5_comments: int = 0,
) -> dict[str, Any]:
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    with connect_sqlite_readonly(db_path) as connection:
        counts = _scope_counts(connection)
        excluded_in_v6 = int(
            connection.execute(
                f"""
                SELECT COUNT(*) AS c
                FROM {paper_scope_view("posts", QUALITY_V6_STAGE)} p
                WHERE p.import_batch_id IN (
                    SELECT batch_id FROM import_batches WHERE batch_name = ?
                )
                  AND p.decision != '纳入'
                """,
                (QUALITY_V6_IMPORT_BATCH,),
            ).fetchone()["c"]
        )
    observed_posts = counts.get("paper_quality_v6_posts", 0)
    observed_comments = counts.get("paper_quality_v6_comments", 0)
    reference_posts = int(checkpoint["formal_posts"])
    reference_comments = int(checkpoint["formal_comments"])
    v5_guard = {
        "formal_posts": counts.get("paper_quality_v5_posts", 0),
        "formal_comments": counts.get("paper_quality_v5_comments", 0),
    }
    failures: list[str] = []
    if observed_posts != reference_posts:
        failures.append(f"v6_posts={observed_posts}; checkpoint={reference_posts}")
    if observed_comments != reference_comments:
        failures.append(f"v6_comments={observed_comments}; checkpoint={reference_comments}")
    if v5_guard != {
        "formal_posts": expected_quality_v5_posts,
        "formal_comments": expected_quality_v5_comments,
    }:
        failures.append(f"quality_v5_guard={v5_guard}")
    if excluded_in_v6:
        failures.append(f"excluded_rows_in_v6={excluded_in_v6}")
    return {
        "reference_source": project_relative_path(checkpoint_path),
        "research_db_path": project_relative_path(db_path),
        "matching_rule": "compare quality_v6 checkpoint counts with staging paper-scope views",
        "reference": {
            "checkpoint_stage": checkpoint.get("checkpoint_stage"),
            "formal_posts": reference_posts,
            "formal_comments": reference_comments,
        },
        "scope_counts": counts,
        "observed_paper_scope": {
            "formal_posts": observed_posts,
            "formal_comments": observed_comments,
        },
        "quality_v5_guard": v5_guard,
        "delta": {
            "paper_posts_minus_checkpoint": observed_posts - reference_posts,
            "paper_comments_minus_checkpoint": observed_comments - reference_comments,
        },
        "excluded_rows_in_v6": excluded_in_v6,
        "status": "aligned" if not failures else "mismatch",
        "failures": failures,
    }


def _write_freeze_checkpoint(
    summary_payload: Mapping[str, Any],
    *,
    excluded_posts: int = 6,
) -> dict[str, Any]:
    quality_v6 = summary_payload["paper_quality_v6"]
    checkpoint = {
        "checkpoint_stage": QUALITY_V6_STAGE,
        "previous_formal_stage": "quality_v5",
        "status": "post_only_formalized",
        "formal_source_contract": paper_scope_contract_name(QUALITY_V6_STAGE),
        "formal_posts": int(quality_v6["formal_posts"]),
        "formal_comments": int(quality_v6["formal_comments"]),
        "source_composition": quality_v6["source_composition"],
        "quality_v5_guard": summary_payload["paper_quality_v5_guard"],
        "comment_scope_note": "comment_review_v2 remains deferred; quality_v6 formal comments are 0 by design.",
        "supplemental_source": {
            "source_scope": SUPPLEMENTAL_SCOPE,
            "formalization_scope": SUPPLEMENTAL_FORMALIZATION_SCOPE,
            "reviewed_jsonl": project_relative_path(SUPPLEMENTAL_REVIEWED_PATH),
            "include_posts": int(quality_v6["source_composition"]["supplemental_formalized_posts"]),
            "excluded_posts": excluded_posts,
        },
        "staging_db_path": summary_payload["research_db"]["staging_db_path"],
        "paper_materials": {
            "output_dir": project_relative_path(QUALITY_V6_PAPER_MATERIALS_DIR),
            "figure_dir": project_relative_path(QUALITY_V6_FIGURE_DIR),
        },
    }
    _write_json(QUALITY_V6_FREEZE_CHECKPOINT_PATH, checkpoint)
    markdown = f"""# quality_v6 Freeze Checkpoint

- 当前阶段：`quality_v6`
- 前一冻结基线：`quality_v5`
- 正式帖子 / 正式评论：`{checkpoint["formal_posts"]} / {checkpoint["formal_comments"]}`
- 来源组合：`quality_v5 514` + `supplemental_formalization_v1 200`
- 评论层：`comment_review_v2 deferred`，`formal_comments=0` 是 v6 post-only 设计选择。
- quality_v5 guard：`{checkpoint["quality_v5_guard"]["formal_posts"]} / {checkpoint["quality_v5_guard"]["formal_comments"]}`
- Staging DB：`{checkpoint["staging_db_path"]}`
- 本 checkpoint 不覆盖 `quality_v5` freeze checkpoint，不更新 `quality_v5` consistency report。
"""
    QUALITY_V6_FREEZE_CHECKPOINT_MARKDOWN_PATH.write_text(markdown, encoding="utf-8")
    return checkpoint


def _distribution_from_rows(rows: list[dict[str, Any]], key: str, count_key: str) -> str:
    if not rows:
        return "\n无可用数据。\n"
    lines = ["| 类别 | 数量 |", "|---|---:|"]
    for row in rows[:20]:
        lines.append(f"| {row.get(key, '')} | {row.get(count_key, 0)} |")
    return "\n".join(lines)


def _write_quality_v6_tables(summary_payload: Mapping[str, Any]) -> dict[str, str]:
    quality_v6 = summary_payload["paper_quality_v6"]
    tables = {
        "workflow_distribution": quality_v6["workflow_distribution"],
        "subject_distribution": quality_v6["subject_distribution"],
        "monthly_posts_by_workflow": quality_v6["monthly_posts_by_workflow"],
        "workflow_legitimacy": quality_v6["cross_tabs"]["workflow_legitimacy"],
        "subject_workflow": quality_v6["cross_tabs"]["subject_workflow"],
    }
    paths: dict[str, str] = {}
    for name, rows in tables.items():
        json_path = QUALITY_V6_TABLE_DIR / f"{name}.json"
        csv_path = QUALITY_V6_TABLE_DIR / f"{name}.csv"
        _write_json(json_path, rows)
        _write_csv(csv_path, rows)
        paths[name] = project_relative_path(json_path)
    return paths


def _write_paper_materials(
    *,
    summary_payload: Mapping[str, Any],
    consistency_report: Mapping[str, Any],
    figure_manifest_path: Path | None,
    framework_v2_result: Mapping[str, Any],
    table_paths: Mapping[str, str],
) -> dict[str, str]:
    QUALITY_V6_PAPER_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
    quality_v6 = summary_payload["paper_quality_v6"]
    formal_posts = int(quality_v6["formal_posts"])
    formal_comments = int(quality_v6["formal_comments"])
    workflow_table = _distribution_from_rows(
        quality_v6["workflow_distribution"],
        "workflow_stage",
        "post_count",
    )
    subject_table = _distribution_from_rows(
        quality_v6["subject_distribution"],
        "subject_label",
        "post_count",
    )
    readme = f"""# quality_v6 Paper Materials

本目录是 `quality_v6` post-only 正式结果层的独立材料，不覆盖 `quality_v5`。

- 正式帖子 / 正式评论：`{formal_posts} / {formal_comments}`
- 来源组合：`quality_v5 514` + `supplemental_formalization_v1 200`
- 评论层：`comment_review_v2 deferred`
- consistency status：`{consistency_report["status"]}`
- framework_v2 materials：`{project_relative_path(Path(str(framework_v2_result["output_dir"])))}`
"""
    results = f"""# quality_v6 Results Chapter Materials

`quality_v6` 将原 `quality_v5` 的 514 条 post-only 正式帖，与 `xhs_expansion_candidate_v1` 中经 `supplemental_formalization_v1` 复核通过的 200 条补充帖合并，形成 `714 / 0` 的新 post-only 正式结果层。

本材料只描述 v6 样本结构与编码分布；不把 sidecar 评论写入正式结果，不把 `quality_v5` 覆盖为历史错误版本。

## 工作流环节分布

{workflow_table}

## 学科/主题宽口径分布

{subject_table}

## 写作边界

- 可写入结果层：帖子层样本扩展后的实践位置、介入方式、介入强度、规范评价与边界生成分布。
- 不可写入结果层：评论层统计、sidecar 评论结论、未通过 `supplemental_formalization_v1` 的 6 条 excluded 样本。
"""
    methods = f"""# quality_v6 Methods Transparency Appendix

## 样本升级链路

- 前一正式基线：`quality_v5 post-only 514 / 0`
- 补充候选来源：`xhs_expansion_candidate_v1`
- 补充 formalization：`supplemental_formalization_v1`
- 纳入 v6：`200` 条帖子
- 排除：`6` 条帖子
- v6 正式范围：`714 / 0`

## 方法边界

补充帖通过独立 staging DB 形成 `paper_scope_quality_v6`，未写回 `quality_v5` freeze checkpoint，未启动 `comment_review_v2`，也未将 sidecar 评论纳入正式结果。

## 校验状态

- consistency status：`{consistency_report["status"]}`
- quality_v5 guard：`{consistency_report["quality_v5_guard"]["formal_posts"]} / {consistency_report["quality_v5_guard"]["formal_comments"]}`
- excluded rows in v6：`{consistency_report["excluded_rows_in_v6"]}`
"""
    contract = f"""# quality_v6 Post-Only Contract

- formal_source_contract：`{paper_scope_contract_name(QUALITY_V6_STAGE)}`
- formal_posts / formal_comments：`{formal_posts} / {formal_comments}`
- comment_review_v2：`deferred`
- quality_v5 guard：`514 / 0`
- supplemental source：`xhs_expansion_candidate_v1` / `supplemental_formalization_v1`
- DB strategy：独立 staging DB，不修改 `data/processed/ai4s_legitimacy.sqlite3`。
"""
    manifest = {
        "formal_stage": QUALITY_V6_STAGE,
        "status": "post_only_formalized",
        "formal_source_contract": {
            "core_results": paper_scope_contract_name(QUALITY_V6_STAGE),
            "figures": paper_scope_contract_name(QUALITY_V6_STAGE),
        },
        "formal_posts": formal_posts,
        "formal_comments": formal_comments,
        "comment_scope_note": "comment_review_v2 deferred; formal_comments=0 is intentional.",
        "summary_path": project_relative_path(QUALITY_V6_SUMMARY_PATH),
        "consistency_path": project_relative_path(QUALITY_V6_CONSISTENCY_REPORT_PATH),
        "freeze_checkpoint_path": project_relative_path(QUALITY_V6_FREEZE_CHECKPOINT_PATH),
        "figure_dir": project_relative_path(QUALITY_V6_FIGURE_DIR),
        "figure_manifest_path": project_relative_path(figure_manifest_path)
        if figure_manifest_path
        else "",
        "framework_v2_dir": project_relative_path(Path(str(framework_v2_result["output_dir"]))),
        "table_paths": dict(table_paths),
    }
    paths = {
        "readme": QUALITY_V6_PAPER_MATERIALS_DIR / "README.md",
        "results": QUALITY_V6_PAPER_MATERIALS_DIR / "paper_results_chapter_quality_v6.md",
        "methods": QUALITY_V6_PAPER_MATERIALS_DIR
        / "paper_methods_transparency_appendix_quality_v6.md",
        "contract": QUALITY_V6_PAPER_MATERIALS_DIR / "quality_v6_post_only_contract.md",
        "manifest": QUALITY_V6_PAPER_MATERIALS_DIR / "paper_materials_manifest.json",
    }
    paths["readme"].write_text(readme, encoding="utf-8")
    paths["results"].write_text(results, encoding="utf-8")
    paths["methods"].write_text(methods, encoding="utf-8")
    paths["contract"].write_text(contract, encoding="utf-8")
    _write_json(paths["manifest"], manifest)
    return {name: project_relative_path(path) for name, path in paths.items()}


def _write_provenance(
    *,
    db_path: Path,
    summary_path: Path,
    consistency_path: Path,
    checkpoint_path: Path,
    figure_manifest_path: Path | None,
    materials_paths: Mapping[str, str],
    formal_posts: int,
    formal_comments: int,
) -> dict[str, Any]:
    files = {
        "summary": _file_record(summary_path),
        "consistency": _file_record(consistency_path),
        "freeze_checkpoint": _file_record(checkpoint_path),
    }
    for name, path in materials_paths.items():
        files[f"paper_material_{name}"] = _file_record(resolve_project_path(path))
    if figure_manifest_path is not None:
        files["figure_manifest"] = _file_record(figure_manifest_path)
    provenance = {
        "schema_version": 1,
        "formal_stage": QUALITY_V6_STAGE,
        "formal_posts": formal_posts,
        "formal_comments": formal_comments,
        "source_db": {
            "path": project_relative_path(db_path),
            "sha256": _sha256(db_path),
            "bytes": db_path.stat().st_size,
        },
        "build_command": {
            "entrypoint": "ai4s-build-quality-v6-artifacts",
            "module": "ai4s_legitimacy.analysis.quality_v6_formalization",
        },
        "files": files,
    }
    _write_json(QUALITY_V6_ARTIFACT_PROVENANCE_PATH, provenance)
    return provenance


def build_quality_v6_artifacts(
    *,
    base_db_path: Path = RESEARCH_DB_PATH,
    supplemental_path: Path = SUPPLEMENTAL_REVIEWED_PATH,
    staging_db_path: Path = QUALITY_V6_STAGING_DB_PATH,
    skip_figures: bool = False,
    expected_include_count: int = 200,
    expected_exclude_count: int = 6,
    expected_quality_v5_posts: int = 514,
    expected_quality_v5_comments: int = 0,
) -> dict[str, Any]:
    staging = prepare_quality_v6_staging_db(
        base_db_path=base_db_path,
        supplemental_path=supplemental_path,
        output_db_path=staging_db_path,
        expected_include_count=expected_include_count,
        expected_exclude_count=expected_exclude_count,
    )
    summary_payload = build_quality_v6_summary_payload(staging_db_path)
    _write_json(QUALITY_V6_SUMMARY_PATH, summary_payload)
    checkpoint = _write_freeze_checkpoint(
        summary_payload,
        excluded_posts=expected_exclude_count,
    )
    consistency_report = evaluate_quality_v6_consistency(
        db_path=staging_db_path,
        checkpoint_path=QUALITY_V6_FREEZE_CHECKPOINT_PATH,
        expected_quality_v5_posts=expected_quality_v5_posts,
        expected_quality_v5_comments=expected_quality_v5_comments,
    )
    _write_json(QUALITY_V6_CONSISTENCY_REPORT_PATH, consistency_report)
    table_paths = _write_quality_v6_tables(summary_payload)
    framework_v2 = generate_framework_v2_materials(
        db_path=staging_db_path,
        output_dir=QUALITY_V6_PAPER_MATERIALS_DIR / "framework_v2",
        stage=QUALITY_V6_STAGE,
    )
    figure_manifest_path: Path | None = None
    figure_result: dict[str, Any] | None = None
    if not skip_figures:
        figure_result = generate_submission_figures(
            db_path=staging_db_path,
            figure_dir=QUALITY_V6_FIGURE_DIR,
            coverage_end_date=summary_payload["paper_quality_v6"]["coverage_end_date"],
            stage=QUALITY_V6_STAGE,
        )
        figure_manifest_path = write_figure_manifest(
            figure_dir=Path(figure_result["figure_dir"]),
            generated_slugs=figure_result["generated_slugs"],
            formal_posts=summary_payload["paper_quality_v6"]["formal_posts"],
            formal_comments=summary_payload["paper_quality_v6"]["formal_comments"],
            coverage_end_date=summary_payload["paper_quality_v6"]["coverage_end_date"],
            stage=QUALITY_V6_STAGE,
        )
    materials_paths = _write_paper_materials(
        summary_payload=summary_payload,
        consistency_report=consistency_report,
        figure_manifest_path=figure_manifest_path,
        framework_v2_result=framework_v2,
        table_paths=table_paths,
    )
    checkpoint_sqlite_wal(base_db_path)
    _remove_sqlite_sidecars(base_db_path)
    checkpoint_sqlite_wal(staging_db_path)
    _remove_sqlite_sidecars(staging_db_path)
    provenance = _write_provenance(
        db_path=staging_db_path,
        summary_path=QUALITY_V6_SUMMARY_PATH,
        consistency_path=QUALITY_V6_CONSISTENCY_REPORT_PATH,
        checkpoint_path=QUALITY_V6_FREEZE_CHECKPOINT_PATH,
        figure_manifest_path=figure_manifest_path,
        materials_paths=materials_paths,
        formal_posts=int(summary_payload["paper_quality_v6"]["formal_posts"]),
        formal_comments=int(summary_payload["paper_quality_v6"]["formal_comments"]),
    )
    return {
        "status": consistency_report["status"],
        "staging": staging,
        "checkpoint": checkpoint,
        "summary_path": project_relative_path(QUALITY_V6_SUMMARY_PATH),
        "consistency_path": project_relative_path(QUALITY_V6_CONSISTENCY_REPORT_PATH),
        "provenance_path": project_relative_path(QUALITY_V6_ARTIFACT_PROVENANCE_PATH),
        "paper_materials": materials_paths,
        "framework_v2": framework_v2,
        "figures": figure_result,
        "provenance": provenance,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build quality_v6 post-only formal artifacts.")
    parser.add_argument("--base-db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--supplemental", type=Path, default=SUPPLEMENTAL_REVIEWED_PATH)
    parser.add_argument("--staging-db", type=Path, default=QUALITY_V6_STAGING_DB_PATH)
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument("--expected-include-count", type=int, default=200)
    parser.add_argument("--expected-exclude-count", type=int, default=6)
    parser.add_argument("--expected-quality-v5-posts", type=int, default=514)
    parser.add_argument("--expected-quality-v5-comments", type=int, default=0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = build_quality_v6_artifacts(
        base_db_path=args.base_db,
        supplemental_path=args.supplemental,
        staging_db_path=args.staging_db,
        skip_figures=args.skip_figures,
        expected_include_count=args.expected_include_count,
        expected_exclude_count=args.expected_exclude_count,
        expected_quality_v5_posts=args.expected_quality_v5_posts,
        expected_quality_v5_comments=args.expected_quality_v5_comments,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
