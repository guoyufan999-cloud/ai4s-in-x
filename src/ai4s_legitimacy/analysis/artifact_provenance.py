from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_ARTIFACT_PROVENANCE_PATH,
    ACTIVE_CHECKPOINT_PATH,
    ACTIVE_FORMAL_STAGE,
)
from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.paths import project_relative_path

PAPER_MATERIALS_MANIFEST_PATH = (
    OUTPUTS_DIR / "reports" / "paper_materials" / "paper_materials_manifest.json"
)
PROVENANCE_SCHEMA_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def _file_record(path: Path) -> dict[str, Any]:
    resolved = Path(path)
    record: dict[str, Any] = {
        "path": project_relative_path(resolved),
        "exists": resolved.exists(),
    }
    if not resolved.exists():
        return record
    record.update(
        {
            "sha256": _sha256(resolved),
            "bytes": resolved.stat().st_size,
            "line_count": _line_count(resolved),
        }
    )
    return record


def build_artifact_provenance(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    checkpoint_path: Path = ACTIVE_CHECKPOINT_PATH,
    summary_payload: Mapping[str, Any],
    consistency_report: Mapping[str, Any],
    summary_path: Path,
    consistency_path: Path,
    canonical_corpus: Mapping[str, Any],
    skip_figures: bool,
    figure_manifest_path: Path,
    paper_materials_manifest_path: Path = PAPER_MATERIALS_MANIFEST_PATH,
) -> dict[str, Any]:
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    formal_summary = summary_payload[f"paper_{ACTIVE_FORMAL_STAGE}"]
    files = {
        "summary": _file_record(summary_path),
        "consistency": _file_record(consistency_path),
        "post_review_v2_master": _file_record(Path(str(canonical_corpus["post_master_path"]))),
        "comment_review_v2_master": _file_record(
            Path(str(canonical_corpus["comment_master_path"]))
        ),
        "post_review_v2_delta_report": _file_record(
            Path(str(canonical_corpus["delta_report_path"]))
        ),
        "figure_manifest": _file_record(figure_manifest_path),
        "paper_materials_manifest": _file_record(paper_materials_manifest_path),
    }
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "formal_stage": ACTIVE_FORMAL_STAGE,
        "formal_stage_status": checkpoint.get("status"),
        "consistency_status": consistency_report.get("status"),
        "formal_posts": int(formal_summary["formal_posts"]),
        "formal_comments": int(formal_summary["formal_comments"]),
        "coverage_end_date": str(formal_summary["coverage_end_date"]),
        "source_db": {
            "path": project_relative_path(db_path),
            "sha256": _sha256(db_path),
            "bytes": Path(db_path).stat().st_size,
        },
        "build_command": {
            "entrypoint": "ai4s-build-artifacts",
            "module": "ai4s_legitimacy.cli.build_artifacts",
            "skip_figures": skip_figures,
        },
        "files": files,
    }


def write_artifact_provenance(
    provenance: Mapping[str, Any],
    output_path: Path = ACTIVE_ARTIFACT_PROVENANCE_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
