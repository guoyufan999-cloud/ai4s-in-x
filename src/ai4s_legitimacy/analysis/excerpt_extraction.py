from __future__ import annotations

import argparse
import re
from pathlib import Path

from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly


EXCERPTS_DIR = OUTPUTS_DIR / "excerpts"
MAX_CHARS_DEFAULT = 120
URL_PATTERN = re.compile(r"https?://\S+")
EMAIL_PATTERN = re.compile(r"[\w.-]+@[\w.-]+\.\w+")
ID_PATTERN = re.compile(r"(?:微信号|微信|wechat|联系方式|电话|手机)[:：]\s*\S+", re.IGNORECASE)

WORKFLOW_STAGE_SQL = """
    SELECT post_id, post_date, content_text
    FROM vw_posts_paper_scope_quality_v4
    WHERE workflow_stage = ?
      AND content_text IS NOT NULL
      AND length(trim(content_text)) > 0
    ORDER BY length(content_text)
    LIMIT ?
"""

POST_STANCE_SQL = """
    SELECT post_id, post_date, content_text
    FROM vw_posts_paper_scope_quality_v4
    WHERE primary_legitimacy_stance = ?
      AND content_text IS NOT NULL
      AND length(trim(content_text)) > 0
    ORDER BY length(content_text)
    LIMIT ?
"""

COMMENT_STANCE_SQL = """
    SELECT c.comment_id, c.comment_date, c.comment_text
    FROM vw_comments_paper_scope_quality_v4 c
    WHERE c.stance = ?
      AND c.comment_text IS NOT NULL
      AND length(trim(c.comment_text)) > 0
    ORDER BY length(c.comment_text)
    LIMIT ?
"""

BOUNDARY_CODE_SQL = """
    SELECT c.comment_id, c.comment_date, c.comment_text
    FROM vw_comments_paper_scope_quality_v4 c
    JOIN codes cd ON cd.record_id = c.comment_id AND cd.record_type = 'comment'
    WHERE cd.boundary_negotiation_code = ?
      AND c.comment_text IS NOT NULL
      AND length(trim(c.comment_text)) > 0
    ORDER BY length(c.comment_text)
    LIMIT ?
"""

DISTINCT_WORKFLOW_STAGES_SQL = """
    SELECT DISTINCT workflow_stage
    FROM vw_posts_paper_scope_quality_v4
    WHERE workflow_stage IS NOT NULL
"""

DISTINCT_STANCES_SQL = """
    SELECT DISTINCT primary_legitimacy_stance
    FROM vw_posts_paper_scope_quality_v4
    WHERE primary_legitimacy_stance IS NOT NULL
"""

DISTINCT_BOUNDARY_CODES_SQL = """
    SELECT DISTINCT boundary_negotiation_code
    FROM codes
    WHERE record_type = 'comment'
      AND boundary_negotiation_code IS NOT NULL
      AND record_id IN (SELECT comment_id FROM vw_comments_paper_scope_quality_v4)
"""


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


def _select_rows(
    db_path: Path,
    sql: str,
    params: tuple[object, ...] = (),
):
    with connect_sqlite_readonly(db_path) as conn:
        return conn.execute(sql, params).fetchall()


def _query_workflow_stage_rows(stage: str, limit: int, db_path: Path):
    return _select_rows(db_path, WORKFLOW_STAGE_SQL, (stage, limit))


def _query_post_stance_rows(stance: str, limit: int, db_path: Path):
    return _select_rows(db_path, POST_STANCE_SQL, (stance, limit))


def _query_comment_stance_rows(stance: str, limit: int, db_path: Path):
    return _select_rows(db_path, COMMENT_STANCE_SQL, (stance, limit))


def _query_boundary_code_rows(code: str, limit: int, db_path: Path):
    return _select_rows(db_path, BOUNDARY_CODE_SQL, (code, limit))


def _build_excerpt_record(
    record_id: str,
    record_type: str,
    coding_label: str,
    deidentified_text: str,
    record_date: str | None,
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "record_type": record_type,
        "coding_label": coding_label,
        "excerpt": deidentified_text,
        "record_date": record_date or "",
    }


def _build_excerpt_from_row(
    row,
    *,
    record_id_key: str,
    text_key: str,
    date_key: str,
    record_type: str,
    coding_label: str,
    max_chars: int,
) -> dict[str, str]:
    return _build_excerpt_record(
        str(row[record_id_key]),
        record_type,
        coding_label,
        deidentify_text(row[text_key], max_chars),
        str(row[date_key]) if row[date_key] else None,
    )


def _build_post_excerpts(
    rows,
    *,
    coding_label: str,
    max_chars: int,
) -> list[dict[str, str]]:
    return [
        _build_excerpt_from_row(
            row,
            record_id_key="post_id",
            text_key="content_text",
            date_key="post_date",
            record_type="post",
            coding_label=coding_label,
            max_chars=max_chars,
        )
        for row in rows
    ]


def _build_comment_excerpts(
    rows,
    *,
    coding_label: str,
    max_chars: int,
) -> list[dict[str, str]]:
    return [
        _build_excerpt_from_row(
            row,
            record_id_key="comment_id",
            text_key="comment_text",
            date_key="comment_date",
            record_type="comment",
            coding_label=coding_label,
            max_chars=max_chars,
        )
        for row in rows
    ]


def extract_excerpts_by_workflow_stage(
    stage: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    return _build_post_excerpts(
        _query_workflow_stage_rows(stage, limit, db_path),
        coding_label=stage,
        max_chars=max_chars,
    )


def extract_excerpts_by_stance(
    stance: str,
    record_type: str = "post",
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    if record_type == "post":
        return _build_post_excerpts(
            _query_post_stance_rows(stance, limit, db_path),
            coding_label=stance,
            max_chars=max_chars,
        )
    return _build_comment_excerpts(
        _query_comment_stance_rows(stance, limit, db_path),
        coding_label=stance,
        max_chars=max_chars,
    )


def extract_excerpts_by_boundary_code(
    code: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    return _build_comment_excerpts(
        _query_boundary_code_rows(code, limit, db_path),
        coding_label=code,
        max_chars=max_chars,
    )


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


def format_excerpts_markdown(
    excerpts: list[dict[str, str]],
    category_label: str,
    *,
    generated_at: str | None = None,
) -> str:
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
    lines.extend(_render_excerpt_sections(excerpts))
    return "\n".join(lines)


def export_excerpts(
    category_slug: str,
    excerpts: list[dict[str, str]],
    output_dir: Path = EXCERPTS_DIR,
    *,
    generated_at: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{category_slug}.md"
    output_path.write_text(
        format_excerpts_markdown(
            excerpts,
            category_slug.replace("_", " "),
            generated_at=generated_at,
        ),
        encoding="utf-8",
    )
    return output_path


def _distinct_values(conn, sql: str) -> list[str]:
    return [str(row[0]) for row in conn.execute(sql).fetchall() if row[0] is not None]


def _load_excerpt_categories(
    db_path: Path,
) -> tuple[list[str], list[str], list[str]]:
    with connect_sqlite_readonly(db_path) as conn:
        return (
            _distinct_values(conn, DISTINCT_WORKFLOW_STAGES_SQL),
            _distinct_values(conn, DISTINCT_STANCES_SQL),
            _distinct_values(conn, DISTINCT_BOUNDARY_CODES_SQL),
        )


def _workflow_stage_slug(stage: str) -> str:
    return f"workflow_{stage.replace('/', '_').replace(' ', '_')}"


def _post_stance_slug(stance: str) -> str:
    return f"post_stance_{stance.replace('/', '_').replace(' ', '_')}"


def _comment_stance_slug(stance: str) -> str:
    return f"comment_stance_{stance.replace('/', '_').replace(' ', '_')}"


def _boundary_code_slug(code: str) -> str:
    return f"boundary_{code.replace('.', '_')}"


def _append_export_if_present(
    generated: list[Path],
    *,
    category_slug: str,
    excerpts: list[dict[str, str]],
    output_dir: Path,
    generated_at: str | None,
) -> None:
    if excerpts:
        generated.append(
            export_excerpts(
                category_slug,
                excerpts,
                output_dir,
                generated_at=generated_at,
            )
        )


def _generate_workflow_excerpt_paths(
    workflow_stages: list[str],
    *,
    db_path: Path,
    output_dir: Path,
    max_chars: int,
    limit: int,
    generated_at: str | None,
) -> list[Path]:
    generated: list[Path] = []
    for stage in workflow_stages:
        _append_export_if_present(
            generated,
            category_slug=_workflow_stage_slug(stage),
            excerpts=extract_excerpts_by_workflow_stage(stage, max_chars, limit, db_path),
            output_dir=output_dir,
            generated_at=generated_at,
        )
    return generated


def _generate_stance_excerpt_paths(
    stances: list[str],
    *,
    db_path: Path,
    output_dir: Path,
    max_chars: int,
    limit: int,
    generated_at: str | None,
) -> list[Path]:
    generated: list[Path] = []
    for stance in stances:
        _append_export_if_present(
            generated,
            category_slug=_post_stance_slug(stance),
            excerpts=extract_excerpts_by_stance(stance, "post", max_chars, limit, db_path),
            output_dir=output_dir,
            generated_at=generated_at,
        )
        _append_export_if_present(
            generated,
            category_slug=_comment_stance_slug(stance),
            excerpts=extract_excerpts_by_stance(stance, "comment", max_chars, limit, db_path),
            output_dir=output_dir,
            generated_at=generated_at,
        )
    return generated


def _generate_boundary_excerpt_paths(
    boundary_codes: list[str],
    *,
    db_path: Path,
    output_dir: Path,
    max_chars: int,
    limit: int,
    generated_at: str | None,
) -> list[Path]:
    generated: list[Path] = []
    for code in boundary_codes:
        _append_export_if_present(
            generated,
            category_slug=_boundary_code_slug(code),
            excerpts=extract_excerpts_by_boundary_code(code, max_chars, limit, db_path),
            output_dir=output_dir,
            generated_at=generated_at,
        )
    return generated


def generate_all_excerpts(
    db_path: Path = RESEARCH_DB_PATH,
    output_dir: Path = EXCERPTS_DIR,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    *,
    generated_at: str | None = None,
) -> list[Path]:
    workflow_stages, stances, boundary_codes = _load_excerpt_categories(db_path)
    generated = _generate_workflow_excerpt_paths(
        workflow_stages,
        db_path=db_path,
        output_dir=output_dir,
        max_chars=max_chars,
        limit=limit,
        generated_at=generated_at,
    )
    generated.extend(
        _generate_stance_excerpt_paths(
            stances,
            db_path=db_path,
            output_dir=output_dir,
            max_chars=max_chars,
            limit=limit,
            generated_at=generated_at,
        )
    )
    generated.extend(
        _generate_boundary_excerpt_paths(
            boundary_codes,
            db_path=db_path,
            output_dir=output_dir,
            max_chars=max_chars,
            limit=limit,
            generated_at=generated_at,
        )
    )
    return generated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract anonymized excerpts from the research DB for coding categories.")
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output-dir", type=Path, default=EXCERPTS_DIR)
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS_DEFAULT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--batch", action="store_true", help="Generate excerpts for all known categories")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.batch:
        paths = generate_all_excerpts(args.db, args.output_dir, args.max_chars, args.limit)
        for p in paths:
            print(p)
    else:
        print("Use --batch to generate all excerpt files.")


if __name__ == "__main__":
    main()
