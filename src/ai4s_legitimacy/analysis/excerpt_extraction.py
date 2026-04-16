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


def extract_excerpts_by_workflow_stage(
    stage: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    with connect_sqlite_readonly(db_path) as conn:
        rows = conn.execute(
            """
            SELECT post_id, post_date, content_text
            FROM vw_posts_paper_scope_quality_v4
            WHERE workflow_stage = ?
              AND content_text IS NOT NULL
              AND length(trim(content_text)) > 0
            ORDER BY length(content_text)
            LIMIT ?
            """,
            (stage, limit),
        ).fetchall()
    return [
        _build_excerpt_record(
            str(r["post_id"]), "post", stage,
            deidentify_text(r["content_text"], max_chars),
            str(r["post_date"]) if r["post_date"] else None,
        )
        for r in rows
    ]


def extract_excerpts_by_stance(
    stance: str,
    record_type: str = "post",
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    if record_type == "post":
        with connect_sqlite_readonly(db_path) as conn:
            rows = conn.execute(
                """
                SELECT post_id, post_date, content_text
                FROM vw_posts_paper_scope_quality_v4
                WHERE primary_legitimacy_stance = ?
                  AND content_text IS NOT NULL
                  AND length(trim(content_text)) > 0
                ORDER BY length(content_text)
                LIMIT ?
                """,
                (stance, limit),
            ).fetchall()
        return [
            _build_excerpt_record(
                str(r["post_id"]), "post", stance,
                deidentify_text(r["content_text"], max_chars),
                str(r["post_date"]) if r["post_date"] else None,
            )
            for r in rows
        ]
    else:
        with connect_sqlite_readonly(db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.comment_id, c.comment_date, c.comment_text
                FROM vw_comments_paper_scope_quality_v4 c
                WHERE c.stance = ?
                  AND c.comment_text IS NOT NULL
                  AND length(trim(c.comment_text)) > 0
                ORDER BY length(c.comment_text)
                LIMIT ?
                """,
                (stance, limit),
            ).fetchall()
        return [
            _build_excerpt_record(
                str(r["comment_id"]), "comment", stance,
                deidentify_text(r["comment_text"], max_chars),
                str(r["comment_date"]) if r["comment_date"] else None,
            )
            for r in rows
        ]


def extract_excerpts_by_boundary_code(
    code: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    db_path: Path = RESEARCH_DB_PATH,
) -> list[dict[str, str]]:
    with connect_sqlite_readonly(db_path) as conn:
        rows = conn.execute(
            """
            SELECT c.comment_id, c.comment_date, c.comment_text
            FROM vw_comments_paper_scope_quality_v4 c
            JOIN codes cd ON cd.record_id = c.comment_id AND cd.record_type = 'comment'
            WHERE cd.boundary_negotiation_code = ?
              AND c.comment_text IS NOT NULL
              AND length(trim(c.comment_text)) > 0
            ORDER BY length(c.comment_text)
            LIMIT ?
            """,
            (code, limit),
        ).fetchall()
    return [
        _build_excerpt_record(
            str(r["comment_id"]), "comment", code,
            deidentify_text(r["comment_text"], max_chars),
            str(r["comment_date"]) if r["comment_date"] else None,
        )
        for r in rows
    ]


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
    for i, ex in enumerate(excerpts, start=1):
        lines.append(f"## 摘录 {i}")
        lines.append(f"- **记录类型**：{ex['record_type']}")
        lines.append(f"- **记录 ID**：{ex['record_id']}")
        lines.append(f"- **日期**：{ex['record_date']}")
        lines.append("")
        lines.append(f"> {ex['excerpt']}")
        lines.append("")
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


def generate_all_excerpts(
    db_path: Path = RESEARCH_DB_PATH,
    output_dir: Path = EXCERPTS_DIR,
    max_chars: int = MAX_CHARS_DEFAULT,
    limit: int = 10,
    *,
    generated_at: str | None = None,
) -> list[Path]:
    generated: list[Path] = []
    with connect_sqlite_readonly(db_path) as conn:
        workflow_stages = _distinct_values(
            conn,
            "SELECT DISTINCT workflow_stage FROM vw_posts_paper_scope_quality_v4 WHERE workflow_stage IS NOT NULL",
        )
        stances = _distinct_values(
            conn,
            "SELECT DISTINCT primary_legitimacy_stance FROM vw_posts_paper_scope_quality_v4 WHERE primary_legitimacy_stance IS NOT NULL",
        )
        boundary_codes = _distinct_values(
            conn,
            """
            SELECT DISTINCT boundary_negotiation_code
            FROM codes
            WHERE record_type = 'comment'
              AND boundary_negotiation_code IS NOT NULL
              AND record_id IN (SELECT comment_id FROM vw_comments_paper_scope_quality_v4)
            """,
        )

    for stage in workflow_stages:
        slug = f"workflow_{stage.replace('/', '_').replace(' ', '_')}"
        excerpts = extract_excerpts_by_workflow_stage(stage, max_chars, limit, db_path)
        if excerpts:
            generated.append(
                export_excerpts(
                    slug,
                    excerpts,
                    output_dir,
                    generated_at=generated_at,
                )
            )

    for stance in stances:
        slug = f"post_stance_{stance.replace('/', '_').replace(' ', '_')}"
        excerpts = extract_excerpts_by_stance(stance, "post", max_chars, limit, db_path)
        if excerpts:
            generated.append(
                export_excerpts(
                    slug,
                    excerpts,
                    output_dir,
                    generated_at=generated_at,
                )
            )
        slug_c = f"comment_stance_{stance.replace('/', '_').replace(' ', '_')}"
        excerpts = extract_excerpts_by_stance(stance, "comment", max_chars, limit, db_path)
        if excerpts:
            generated.append(
                export_excerpts(
                    slug_c,
                    excerpts,
                    output_dir,
                    generated_at=generated_at,
                )
            )

    for code in boundary_codes:
        slug = f"boundary_{code.replace('.', '_')}"
        excerpts = extract_excerpts_by_boundary_code(code, max_chars, limit, db_path)
        if excerpts:
            generated.append(
                export_excerpts(
                    slug,
                    excerpts,
                    output_dir,
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
