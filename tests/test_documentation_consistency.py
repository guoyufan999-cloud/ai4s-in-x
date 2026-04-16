from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_uses_cli_import_entrypoint() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "ai4s-import-legacy" in text
    assert "运行 `src/collection/import_legacy_sqlite.py`" not in text


def test_active_docs_no_longer_claim_formal_figures_depend_on_legacy_exports() -> None:
    text = (ROOT / "data" / "data_schema.md").read_text(encoding="utf-8")
    assert "paper_scope_quality_v4" in text
    assert "仍主要保留在 legacy 导出物中" not in text


def test_database_and_boundary_docs_describe_static_archive_and_rendered_views() -> None:
    database_text = (ROOT / "database" / "README.md").read_text(encoding="utf-8")
    boundary_text = (ROOT / "docs" / "repository_boundaries.md").read_text(encoding="utf-8")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "render_views_sql()" in database_text
    assert "不承诺 archive 可直接运行" in boundary_text
    assert "不再保留 legacy 代码快照、旧测试" in readme_text
    assert "outputs/reports/freeze_checkpoints/" in readme_text


def test_readme_documents_bytecode_free_pytest_command() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "./.venv/bin/python -B -m pytest -q" in text
    assert "__pycache__" in text
