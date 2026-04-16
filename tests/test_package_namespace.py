from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_uses_project_specific_python_package_namespace() -> None:
    package = importlib.import_module("ai4s_legitimacy")
    build_module = importlib.import_module("ai4s_legitimacy.cli.build_artifacts")
    importlib.import_module("ai4s_legitimacy.cli.import_legacy")

    assert package.__file__ is not None
    assert build_module.__file__ is not None

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert scripts["ai4s-build-artifacts"] == "ai4s_legitimacy.cli.build_artifacts:main"
    assert scripts["ai4s-import-legacy"] == "ai4s_legitimacy.cli.import_legacy:main"
    assert pyproject["tool"]["setuptools"]["package-dir"][""] == "src"
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "ai4s_legitimacy*"
    ]


def test_active_docs_use_new_module_execution_namespace() -> None:
    targets = [
        ROOT / "README.md",
        ROOT / "data" / "processed" / "README.md",
        ROOT / "archive" / "legacy_collection_runtime" / "data" / "db" / "README.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "python -m src." not in text

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python -m ai4s_legitimacy.analysis.reporting" in readme_text
    assert "python -m ai4s_legitimacy.analysis.quality_v4_consistency" in readme_text
    assert "python -m ai4s_legitimacy.analysis.excerpt_extraction --batch" in readme_text
