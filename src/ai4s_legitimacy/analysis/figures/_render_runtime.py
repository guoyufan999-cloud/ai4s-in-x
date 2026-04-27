from __future__ import annotations

from pathlib import Path
from typing import Any


def save_figure(fig: Any, base_path: Path) -> dict[str, str]:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = base_path.with_suffix(".png")
    svg_path = base_path.with_suffix(".svg")
    fig.savefig(png_path, dpi=240, bbox_inches="tight")
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    return {"png_path": str(png_path), "vector_path": str(svg_path)}


def remove_top_right_spines(ax: Any) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def configure_matplotlib() -> tuple[Any, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import font_manager

    from ai4s_legitimacy.analysis.figures.config import configure_style

    configure_style(matplotlib, font_manager)
    return plt, np
