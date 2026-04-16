from __future__ import annotations

from pathlib import Path

from src.config.settings import PROJECT_ROOT


def project_relative_path(path: str | Path) -> str:
    candidate = Path(path)
    resolved = candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
    normalized = resolved.resolve()
    try:
        return normalized.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return normalized.as_posix()


def resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
