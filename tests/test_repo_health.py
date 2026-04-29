from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_HEALTH_SCRIPT = ROOT / "scripts" / "repo_health.py"
ARTIFACT_HEALTH_SCRIPT = ROOT / "scripts" / "artifact_health.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _file_record(root: Path, relative_path: str) -> dict[str, object]:
    path = root / relative_path
    return {
        "path": relative_path,
        "exists": True,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "line_count": _line_count(path),
    }


def _create_health_fixture(root: Path) -> None:
    source_db_path = root / "data" / "processed" / "ai4s_legitimacy.sqlite3"
    source_db_path.parent.mkdir(parents=True, exist_ok=True)
    source_db_path.write_bytes(b"fixture-db")

    summary_path = _write_json(
        root / "outputs" / "reports" / "freeze_checkpoints" / "research_db_summary.json",
        {
            "paper_quality_v5": {
                "formal_posts": 514,
                "formal_comments": 0,
                "coverage_end_date": "2026-04-10",
            }
        },
    )
    consistency_path = _write_json(
        root
        / "outputs"
        / "reports"
        / "freeze_checkpoints"
        / "quality_v5_consistency_report.json",
        {
            "status": "aligned",
            "delta": {
                "paper_posts_minus_checkpoint": 0,
                "paper_comments_minus_checkpoint": 0,
            },
        },
    )
    residue_path = root / "outputs" / "reports" / "review_v2" / "smoke_residue" / "empty.jsonl"
    residue_path.parent.mkdir(parents=True, exist_ok=True)
    residue_path.write_text("", encoding="utf-8")
    _write_json(
        root / "outputs" / "reports" / "review_v2" / "smoke_residue_manifest.json",
        {
            "schema_version": 1,
            "status": "historical_smoke_residue",
            "files": [{"path": "outputs/reports/review_v2/smoke_residue/empty.jsonl", "bytes": 0}],
        },
    )
    _write_json(
        root
        / "outputs"
        / "reports"
        / "freeze_checkpoints"
        / "quality_v5_artifact_provenance.json",
        {
            "schema_version": 1,
            "formal_stage": "quality_v5",
            "formal_posts": 514,
            "formal_comments": 0,
            "source_db": {
                "path": "data/processed/ai4s_legitimacy.sqlite3",
                "sha256": _sha256(source_db_path),
                "bytes": source_db_path.stat().st_size,
            },
            "files": {
                "summary": _file_record(
                    root,
                    "outputs/reports/freeze_checkpoints/research_db_summary.json",
                ),
                "consistency": _file_record(
                    root,
                    "outputs/reports/freeze_checkpoints/quality_v5_consistency_report.json",
                ),
            },
        },
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    assert summary_path.exists()
    assert consistency_path.exists()


def _run_repo_health(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_HEALTH_SCRIPT), "--root", str(root), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_artifact_health(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ARTIFACT_HEALTH_SCRIPT), "--root", str(root), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )


def test_repo_health_accepts_formal_fixture_and_manifested_zero_byte_residue(tmp_path: Path) -> None:
    _create_health_fixture(tmp_path)

    process = _run_repo_health(tmp_path)
    payload = json.loads(process.stdout)

    assert process.returncode == 0
    assert payload["status"] == "ok"
    assert payload["checks"]["formal_counts"]["formal_posts"] == 514
    assert payload["checks"]["zero_byte_tracked_files"]["zero_byte_tracked_count"] == 1


def test_repo_health_rejects_unmanifested_zero_byte_tracked_file(tmp_path: Path) -> None:
    _create_health_fixture(tmp_path)
    bad_path = tmp_path / "outputs" / "tables" / "bad_empty.jsonl"
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

    process = _run_repo_health(tmp_path)
    payload = json.loads(process.stdout)

    assert process.returncode == 1
    assert payload["status"] == "fail"
    assert "outputs/tables/bad_empty.jsonl" in payload["failures"]["zero_byte_tracked_files"]


def test_artifact_health_runs_only_artifact_checks(tmp_path: Path) -> None:
    _create_health_fixture(tmp_path)

    process = _run_artifact_health(tmp_path)
    payload = json.loads(process.stdout)

    assert process.returncode == 0
    assert payload["status"] == "ok"
    assert set(payload["checks"]) == {
        "formal_counts",
        "provenance",
        "zero_byte_tracked_files",
        "wal_shm",
    }
    assert "ignored_cache_size" not in payload["checks"]


def test_artifact_health_accepts_quality_v6_submission_manifest_with_quality_v5_guard(
    tmp_path: Path,
) -> None:
    _create_health_fixture(tmp_path)
    manifest_relative = "outputs/reports/paper_materials/paper_materials_manifest.json"
    manifest_path = tmp_path / manifest_relative
    _write_json(
        manifest_path,
        {
            "formal_stage": "quality_v5",
            "formal_posts": 514,
            "formal_comments": 0,
        },
    )
    provenance_path = (
        tmp_path / "outputs" / "reports" / "freeze_checkpoints" / "quality_v5_artifact_provenance.json"
    )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["files"]["paper_materials_manifest"] = _file_record(tmp_path, manifest_relative)
    _write_json(provenance_path, provenance)
    _write_json(
        manifest_path,
        {
            "formal_stage": "quality_v6",
            "previous_formal_stage": "quality_v5",
            "formal_posts": 714,
            "formal_comments": 0,
            "quality_v5_guard_counts": {"posts": 514, "comments": 0},
            "comment_scope_note": "comment_review_v2 deferred",
        },
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

    process = _run_artifact_health(tmp_path)
    payload = json.loads(process.stdout)

    assert process.returncode == 0
    assert payload["status"] == "ok"
    assert payload["checks"]["provenance"]["status"] == "ok"
