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
    assert "paper_scope_quality_v5" in text
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


def test_active_docs_treat_manual_coding_fields_as_future_reserve() -> None:
    schema_text = (ROOT / "data" / "data_schema.md").read_text(encoding="utf-8")
    legacy_mapping_text = (ROOT / "codebook" / "legacy_mapping.md").read_text(encoding="utf-8")

    assert "`ai_practice_code / legitimacy_code / boundary_negotiation_code`" in schema_text
    assert "当前 `paper_scope_quality_v5` 的活跃重建链不再把 `ai_practice` 作为正式主轴" in legacy_mapping_text
    assert "正式筛选与编码以 canonical JSONL 中的 `claim_units` 和帖子/评论层归并摘要为准" in legacy_mapping_text


def test_active_docs_describe_abcd_baseline_instead_of_ai_practice_main_axis() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    coding_rules_text = (ROOT / "codebook" / "coding_rules.md").read_text(encoding="utf-8")
    codebook_text = (ROOT / "codebook" / "codebook.md").read_text(encoding="utf-8")

    assert "1. `A` 科研工作流环节" in readme_text
    assert "2. `B` 合法性评价" in readme_text
    assert "3. `C` 评价标准" in readme_text
    assert "4. `D` 边界协商" in readme_text
    assert "再判 AI 实践方式" not in coding_rules_text
    assert "2. AI 实践方式" not in codebook_text
    assert "A. 科研工作流环节识别" in coding_rules_text
    assert "当前活跃框架" in codebook_text


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
