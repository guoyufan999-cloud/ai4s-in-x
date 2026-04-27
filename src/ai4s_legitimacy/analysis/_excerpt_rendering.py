from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from ai4s_legitimacy.analysis._excerpt_specs import EXCERPTS_DIR, MAX_CHARS_DEFAULT

URL_PATTERN = re.compile(r"https?://\S+")
EMAIL_PATTERN = re.compile(r"[\w.-]+@[\w.-]+\.\w+")
ID_PATTERN = re.compile(r"(?:微信号|微信|wechat|联系方式|电话|手机)[:：]\s*\S+", re.IGNORECASE)


def deidentify_text(text: str | None, max_chars: int = MAX_CHARS_DEFAULT) -> str:
    if not text:
        return ""
    cleaned = str(text)
    cleaned = URL_PATTERN.sub("[URL]", cleaned)
    cleaned = EMAIL_PATTERN.sub("[email]", cleaned)
    cleaned = ID_PATTERN.sub("[ID]", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rsplit(" ", 1)[0] + "..."
    return cleaned


def _render_excerpt_sections(excerpts: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for index, excerpt in enumerate(excerpts, start=1):
        lines.append(f"## 摘录 {index}")
        lines.append(f"- **记录类型**：{excerpt['record_type']}")
        lines.append(f"- **记录 ID**：{excerpt['record_id']}")
        lines.append(f"- **日期**：{excerpt['record_date']}")
        lines.append("")
        lines.append(f"> {excerpt['excerpt']}")
        lines.append("")
    return lines


def _render_excerpt_header_lines(
    excerpts: Sequence[dict[str, str]],
    *,
    category_label: str,
    generated_at: str | None,
) -> list[str]:
    lines = [
        f"# {category_label} — 分析摘录",
        "",
    ]
    if generated_at is not None:
        lines.append(f"- 生成时间：{generated_at}")
    lines.extend(
        [
            f"- 记录数：{len(excerpts)}",
            "",
            "---",
            "",
        ]
    )
    return lines


def format_excerpts_markdown(
    excerpts: list[dict[str, str]],
    category_label: str,
    *,
    generated_at: str | None = None,
) -> str:
    lines = _render_excerpt_header_lines(
        excerpts,
        category_label=category_label,
        generated_at=generated_at,
    )
    lines.extend(_render_excerpt_sections(excerpts))
    return "\n".join(lines)


def _excerpt_output_path(category_slug: str, output_dir: Path) -> Path:
    return output_dir / f"{category_slug}.md"


def _display_category_label(category_slug: str) -> str:
    return category_slug.replace("_", " ")


def export_excerpts(
    category_slug: str,
    excerpts: list[dict[str, str]],
    output_dir: Path = EXCERPTS_DIR,
    *,
    generated_at: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _excerpt_output_path(category_slug, output_dir)
    output_path.write_text(
        format_excerpts_markdown(
            excerpts,
            _display_category_label(category_slug),
            generated_at=generated_at,
        ),
        encoding="utf-8",
    )
    return output_path
