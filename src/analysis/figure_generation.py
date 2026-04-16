from __future__ import annotations

import json

from src.analysis.figures.manifest import write_figure_manifest
from src.analysis.figures.render import generate_submission_figures

__all__ = ["generate_submission_figures", "write_figure_manifest"]


if __name__ == "__main__":
    print(json.dumps(generate_submission_figures(), ensure_ascii=False, indent=2))
