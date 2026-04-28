from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

V2_TERMS = (
    "话语情境",
    "实践位置",
    "介入方式",
    "规范评价",
    "边界生成",
)

V2_FILES = (
    ROOT / "docs" / "theoretical_framework_v2.md",
    ROOT / "docs" / "paper_outline_v2.md",
    ROOT / "research_brief.md",
    ROOT / "analysis_plan.md",
    ROOT / "codebook" / "codebook.md",
    ROOT / "codebook" / "coding_rules.md",
)


def test_framework_v2_docs_exist() -> None:
    assert (ROOT / "docs" / "theoretical_framework_v2.md").exists()
    assert (ROOT / "docs" / "paper_outline_v2.md").exists()


def test_core_docs_use_framework_v2_terms() -> None:
    for path in V2_FILES:
        text = path.read_text(encoding="utf-8")
        for term in V2_TERMS:
            assert term in text, f"{path} missing framework v2 term: {term}"


def test_active_docs_do_not_present_legacy_triad_as_current_framework() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in V2_FILES)

    assert "当前活跃框架不再是旧的“科研工作流—合法性评价—边界协商”" in combined
    assert "旧 `A. 科研工作流环节识别`" in combined
    assert "当前活跃框架为“科研工作流—合法性评价—边界协商”" not in combined
    assert "当前活跃口径：科研工作流—合法性评价—边界协商" not in combined


def test_framework_v2_docs_preserve_quality_v5_post_only_boundaries() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in V2_FILES)

    assert "quality_v5 post-only" in combined
    assert "正式帖子 `514`" in combined
    assert "正式评论 `0`" in combined
    assert "514 / 0" in combined
    assert "comment_review_v2 deferred" in combined
    assert "quality_v4 historical audit" in combined
