from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_archive_runtime_cache_assets_are_not_kept_in_repo() -> None:
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "data" / "chrome-profile").exists()
    assert not (
        ROOT / "archive" / "legacy_collection_runtime" / "opencli-main" / "node_modules"
    ).exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "opencli-main").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "opencli").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "ai4s-xhs").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "ai4s_xhs").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "docker").exists()
    assert not (
        ROOT / "archive" / "legacy_collection_runtime" / "docker-compose.yml"
    ).exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "scripts").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "config").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "pyproject.toml").exists()
    assert not (ROOT / "archive" / "legacy_collection_runtime" / "requirements.lock").exists()
    assert not (
        ROOT / "archive" / "legacy_collection_runtime" / "requirements.multimodal.lock"
    ).exists()
    assert not (
        ROOT / "archive" / "legacy_collection_runtime" / "data" / "runtime_state"
    ).exists()
    assert not (
        ROOT / "archive" / "legacy_collection_runtime" / "data" / "db" / ".gitkeep"
    ).exists()
    assert not (ROOT / "archive" / "legacy_exports" / "exports_legacy").exists()
    assert not (ROOT / "archive" / "legacy_exports" / "grounded_pilot").exists()
    assert not (ROOT / "archive" / "legacy_exports" / "legacy_analysis_exports").exists()
    assert not (ROOT / "archive" / "legacy_tests" / "tests_legacy_runtime").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "CODING_MANUAL.md").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "COLLECTION_METHOD.md").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "DATABASE_MANUAL.md").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "PROJECT_SPEC_legacy_runtime.md").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "README_legacy_runtime.md").exists()
    assert not (ROOT / "archive" / "legacy_specs" / "paper_llm_manifest.json").exists()
    assert not list(
        (ROOT / "archive" / "legacy_collection_runtime" / "data" / "db").glob("*.sqlite3-wal")
    )
    assert not list(
        (ROOT / "archive" / "legacy_collection_runtime" / "data" / "db").glob("*.sqlite3-shm")
    )
