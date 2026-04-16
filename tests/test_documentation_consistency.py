from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_uses_cli_import_entrypoint() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "ai4s-import-legacy" in text
    assert "运行 `src/collection/import_legacy_sqlite.py`" not in text
    assert "python -m src.analysis." not in text
    assert "python -m ai4s_legitimacy.analysis." in text


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
    assert "docs/local_git_maintenance.md" in readme_text


def test_active_docs_describe_local_db_paths_as_ignored_assets() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    boundary_text = (ROOT / "docs" / "repository_boundaries.md").read_text(encoding="utf-8")
    processed_readme = (ROOT / "data" / "processed" / "README.md").read_text(encoding="utf-8")
    legacy_db_readme = (
        ROOT / "archive" / "legacy_collection_runtime" / "data" / "db" / "README.md"
    ).read_text(encoding="utf-8")
    assert "junk_review/" not in readme_text
    assert "仓库版本化的是说明文件而不是 SQLite 文件本身" in readme_text
    assert "本地研究型主库" in readme_text
    assert "SQLite 文件本身默认由 `.gitignore` 拦截" in boundary_text
    assert "默认由 Git 忽略" in processed_readme
    assert "默认由 Git 忽略" in legacy_db_readme


def test_readme_documents_bytecode_free_pytest_command() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "./.venv/bin/pip install -e '.[dev]'" in text
    assert "./.venv/bin/python -B -m pytest -q" in text
    assert "__pycache__" in text
