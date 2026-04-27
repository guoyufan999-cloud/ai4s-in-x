from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
TEMPLATE_FIELDS = (
    "Status: template",
    "Purpose:",
    "Suggested inputs:",
    "Recommended command/module:",
    "Expected outputs or follow-up artifacts:",
)


def _load_notebook(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dependency_helper_files_are_convenience_wrappers_not_lockfiles() -> None:
    assert not (ROOT / "requirements.lock").exists()
    assert not (ROOT / "requirements.txt").exists()

    requirements_dev = ROOT / "requirements.dev.txt"
    environment_yml = ROOT / "environment.yml"
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert requirements_dev.exists()
    requirements_dev_text = requirements_dev.read_text(encoding="utf-8")
    environment_yml_text = environment_yml.read_text(encoding="utf-8")

    assert "requirements.lock" not in requirements_dev_text
    assert "lockfile" not in requirements_dev_text.lower()
    assert "convenience wrapper" in requirements_dev_text.lower()
    assert "convenience" in environment_yml_text.lower()
    assert "./.venv/bin/pip install -e '.[dev]'" in readme_text
    assert "requirements.dev.txt" in readme_text
    assert "requirements.txt" not in readme_text


def test_notebook_templates_are_unexecuted_and_not_formal_delivery_artifacts() -> None:
    notebook_readme = (NOTEBOOK_DIR / "README.md").read_text(encoding="utf-8")
    assert "只保留本地审查模板" in notebook_readme
    assert "不作为正式交付链" in notebook_readme
    assert "outputs/reports/freeze_checkpoints/" in notebook_readme
    assert "outputs/reports/paper_materials/" in notebook_readme

    notebook_paths = sorted(NOTEBOOK_DIR.glob("0*.ipynb"))
    assert len(notebook_paths) == 4

    for path in notebook_paths:
        notebook = _load_notebook(path)
        cells = notebook["cells"]
        assert cells, f"{path} should contain template cells"

        first_cell = cells[0]
        assert first_cell["cell_type"] == "markdown"
        first_cell_text = "".join(first_cell["source"])
        for field in TEMPLATE_FIELDS:
            assert field in first_cell_text, f"{path} missing template field: {field}"

        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        assert code_cells, f"{path} should keep one unexecuted template code cell"
        for cell in code_cells:
            assert cell["execution_count"] is None
            assert cell["outputs"] == []


def test_planning_docs_keep_current_next_steps_in_sync_with_latest_head() -> None:
    backlog_text = (ROOT / "tasks" / "backlog.md").read_text(encoding="utf-8")
    roadmap_text = (ROOT / "tasks" / "roadmap.md").read_text(encoding="utf-8")

    backlog_current = backlog_text.split("## 当前下一步入口", 1)[1].split("## P0", 1)[0]
    roadmap_current = roadmap_text.split("## 当前下一步入口", 1)[1].split("## 阶段 1", 1)[0]

    for current_entry in (backlog_current, roadmap_current):
        assert "quality_v5" in current_entry
        assert "staging" in current_entry
        assert "review queue" in current_entry
        assert "reviewed import" in current_entry
        assert "analysis/figures/queries.py" not in current_entry
        assert "analysis/figures/render.py" not in current_entry
        assert "collection/import_legacy_sqlite.py" not in current_entry
        assert "analysis/excerpt_extraction.py" not in current_entry
        assert "analysis/reporting.py" not in current_entry
        assert "analysis/figures/manifest.py" not in current_entry
