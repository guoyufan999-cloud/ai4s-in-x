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


def test_working_drafts_live_under_docs_not_formal_outputs() -> None:
    working_dir = ROOT / "docs" / "paper_working"
    formal_dir = ROOT / "outputs" / "reports" / "paper_materials"
    assert (working_dir / "README.md").exists()
    assert (working_dir / "paper_master_manuscript_draft.md").exists()
    assert (working_dir / "paper_master_manuscript_llm.md").exists()
    assert not list(formal_dir.glob("paper_*_draft.md"))
    assert not list(formal_dir.glob("paper_*_llm.md"))
    assert not (formal_dir / "paper_master_manuscript_llm_merged.md").exists()


def test_only_submission_figure_bundle_is_versioned() -> None:
    figure_dir = ROOT / "outputs" / "figures"
    assert not list(figure_dir.glob("*.png"))
    assert (figure_dir / "paper_figures_submission" / "quality_v4").exists()
