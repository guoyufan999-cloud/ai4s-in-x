from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.canonical_schema import (
    AI_INTERVENTION_INTENSITY_LABELS,
    AI_INTERVENTION_MODE_LABELS,
    BOUNDARY_CONTENT_LABELS,
    BOUNDARY_MECHANISM_LABELS,
    BOUNDARY_RESULT_LABELS,
    EVALUATION_LABELS,
    EVALUATION_TENSION_LABELS,
    FORMAL_NORM_REFERENCE_LABELS,
    LEGITIMACY_LABELS,
    WORKFLOW_STAGE_LABELS,
    normalize_claim_units,
)
from ai4s_legitimacy.config.formal_baseline import (
    ACTIVE_FORMAL_SCOPE_COMMENTS_KEY,
    ACTIVE_FORMAL_SCOPE_POSTS_KEY,
    ACTIVE_FORMAL_STAGE,
    paper_scope_view,
)
from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

FRAMEWORK_V2_OUTPUT_DIR = OUTPUTS_DIR / "reports" / "paper_materials" / "framework_v2"
MISSING_V2_FIELD_NOTE = "新增 v2 字段尚未完成正式人工编码，因此本表仅显示已有字段或为空。"
COMPLETE_V2_FIELD_NOTE = "framework_v2 正式帖子已完成人工 reviewed 补码，本表可作为正式 v2 统计使用。"

TEXT_TYPE_FROM_DISCURSIVE_MODE = {
    "experience_share": "经验分享",
    "question_help_seeking": "经验分享",
    "advice_guidance": "教程展示",
    "criticism": "风险提醒",
    "policy_statement": "规范解读",
    "unclear": "其他",
    "": "其他",
}

PRACTICE_DOMAIN_LABELS = {
    "P": "A1 科研生产",
    "G": "A2 科研治理",
    "T": "A3 科研训练与能力建构",
    "A1": "A1 科研生产",
    "A2": "A2 科研治理",
    "A3": "A3 科研训练与能力建构",
}

WORKFLOW_STAGE_CODE_TO_DOMAIN = {
    code: code.split(".", 1)[0] for code in WORKFLOW_STAGE_LABELS
}
WORKFLOW_STAGE_LABEL_TO_DOMAIN = {
    label: code.split(".", 1)[0] for code, label in WORKFLOW_STAGE_LABELS.items()
}

SUMMARY_FIELD_SPECS = {
    "ai_intervention_mode_distribution": (
        "ai_intervention_mode_codes",
        AI_INTERVENTION_MODE_LABELS,
    ),
    "ai_intervention_intensity_distribution": (
        "ai_intervention_intensity_codes",
        AI_INTERVENTION_INTENSITY_LABELS,
    ),
    "evaluation_tension_distribution": (
        "evaluation_tension_codes",
        EVALUATION_TENSION_LABELS,
    ),
    "formal_norm_reference_distribution": (
        "formal_norm_reference_codes",
        FORMAL_NORM_REFERENCE_LABELS,
    ),
    "boundary_mechanism_distribution": (
        "boundary_mechanism_codes",
        BOUNDARY_MECHANISM_LABELS,
    ),
    "boundary_result_distribution": (
        "boundary_result_codes",
        BOUNDARY_RESULT_LABELS,
    ),
}


def _load_json_list(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, list) else []
    return []


def _claim_unit_from_db_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "practice_unit": row.get("practice_unit") or "",
        "workflow_stage_codes": _load_json_list(row.get("workflow_stage_codes_json")),
        "legitimacy_codes": _load_json_list(row.get("legitimacy_codes_json")),
        "basis_codes": _load_json_list(row.get("basis_codes_json")),
        "boundary_codes": _load_json_list(row.get("boundary_codes_json")),
        "boundary_mode_codes": _load_json_list(row.get("boundary_mode_codes_json")),
        "evidence": _load_json_list(row.get("evidence_json")),
    }


def _entry_code(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("code") or "").strip()
    return str(entry or "").strip()


def _codes_from_unit(unit: dict[str, Any], field_name: str) -> list[str]:
    values = unit.get(field_name) or []
    codes = [_entry_code(value) for value in values]
    return list(dict.fromkeys(code for code in codes if code))


def _distribution(counter: Counter[str], labels: dict[str, str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        rows.append(
            {
                "code": value if labels and value in labels else "",
                "label": labels.get(value, value) if labels else value,
                "count": count,
            }
        )
    return rows


def _practice_domain_label(post: dict[str, Any]) -> str:
    raw_domain = str(post.get("workflow_domain") or "").strip()
    if raw_domain in PRACTICE_DOMAIN_LABELS:
        return PRACTICE_DOMAIN_LABELS[raw_domain]

    stage = str(post.get("workflow_stage") or "").strip()
    domain_code = WORKFLOW_STAGE_CODE_TO_DOMAIN.get(stage) or WORKFLOW_STAGE_LABEL_TO_DOMAIN.get(stage)
    if domain_code:
        return PRACTICE_DOMAIN_LABELS[domain_code]
    return "uncoded"


def _cross_tab(
    claim_units: list[dict[str, Any]],
    *,
    left_field: str,
    right_field: str,
    left_labels: dict[str, str],
    right_labels: dict[str, str],
) -> list[dict[str, Any]]:
    counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    for unit in claim_units:
        left_codes = _codes_from_unit(unit, left_field)
        right_codes = _codes_from_unit(unit, right_field)
        for left, right in product(left_codes, right_codes):
            counts[(left, right)] += 1
    return [
        {
            "left_code": left,
            "left_label": left_labels.get(left, left),
            "right_code": right,
            "right_label": right_labels.get(right, right),
            "count": count,
        }
        for (left, right), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _load_reviewed_payloads(connection) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for row in connection.execute(
        """
        SELECT record_id, payload_json
        FROM reviewed_records
        WHERE review_phase = 'post_review_v2' AND record_type = 'post'
        ORDER BY id
        """
    ).fetchall():
        payload = json.loads(str(row["payload_json"]))
        payloads[str(row["record_id"])] = payload
    return payloads


def _load_db_claim_units(connection, formal_post_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in connection.execute(
        """
        SELECT *
        FROM claim_units
        WHERE record_type = 'post'
        ORDER BY record_id, claim_index
        """
    ).fetchall():
        record_id = str(row["record_id"])
        if record_id not in formal_post_ids:
            continue
        grouped[record_id].append(_claim_unit_from_db_row(dict(row)))
    return {record_id: normalize_claim_units(units) for record_id, units in grouped.items()}


def _load_formal_posts(connection) -> list[dict[str, Any]]:
    scope_view = paper_scope_view("posts")
    return [
        dict(row)
        for row in connection.execute(
            f"""
            SELECT p.*
            FROM posts p
            JOIN {scope_view} s ON s.post_id = p.post_id
            ORDER BY p.post_date, p.post_id
            """
        ).fetchall()
    ]


def _load_scope_counts(connection) -> dict[str, int]:
    return {
        str(row["scope_name"]): int(row["row_count"] or 0)
        for row in connection.execute(
            "SELECT scope_name, row_count FROM vw_scope_counts ORDER BY scope_name"
        ).fetchall()
    }


def _build_summary_tables(
    posts: list[dict[str, Any]],
    claim_units: list[dict[str, Any]],
    *,
    scope_counts: dict[str, int],
    framework_v2_reviewed_posts: int,
    framework_v2_coding_complete: bool,
) -> dict[str, Any]:
    text_type_counts = Counter(
        TEXT_TYPE_FROM_DISCURSIVE_MODE.get(str(post.get("discursive_mode") or ""), "其他")
        for post in posts
    )
    domain_counts = Counter(_practice_domain_label(post) for post in posts)
    workflow_counts = Counter(str(post.get("workflow_stage") or "uncoded") for post in posts)
    legitimacy_counts = Counter(
        code for unit in claim_units for code in _codes_from_unit(unit, "legitimacy_codes")
    )
    standard_counts = Counter(
        code for unit in claim_units for code in _codes_from_unit(unit, "basis_codes")
    )
    boundary_counts = Counter(
        code for unit in claim_units for code in _codes_from_unit(unit, "boundary_codes")
    )

    tables = {
        "text_type_distribution": _distribution(text_type_counts),
        "research_activity_field_distribution": _distribution(domain_counts),
        "workflow_stage_distribution": _distribution(workflow_counts),
        "normative_evaluation_standard_distribution": _distribution(
            standard_counts,
            EVALUATION_LABELS,
        ),
        "normative_evaluation_tendency_distribution": _distribution(
            legitimacy_counts,
            LEGITIMACY_LABELS,
        ),
        "boundary_type_distribution": _distribution(boundary_counts, BOUNDARY_CONTENT_LABELS),
    }
    for table_name, (field_name, labels) in SUMMARY_FIELD_SPECS.items():
        counter = Counter(code for unit in claim_units for code in _codes_from_unit(unit, field_name))
        tables[table_name] = _distribution(counter, labels)

    formal_posts = int(scope_counts.get(ACTIVE_FORMAL_SCOPE_POSTS_KEY, 0))
    note = COMPLETE_V2_FIELD_NOTE if framework_v2_coding_complete else MISSING_V2_FIELD_NOTE
    return {
        "metadata": {
            "formal_stage": ACTIVE_FORMAL_STAGE,
            "formal_posts": formal_posts,
            "formal_comments": int(scope_counts.get(ACTIVE_FORMAL_SCOPE_COMMENTS_KEY, 0)),
            "source_contract": f"paper_scope_{ACTIVE_FORMAL_STAGE}",
            "framework_v2_reviewed_posts": framework_v2_reviewed_posts,
            "framework_v2_missing_posts": max(formal_posts - framework_v2_reviewed_posts, 0),
            "framework_v2_coding_complete": framework_v2_coding_complete,
            "note": note,
        },
        "tables": tables,
    }


def _build_cross_tabs(claim_units: list[dict[str, Any]], *, note: str) -> dict[str, Any]:
    return {
        "metadata": {"note": note},
        "cross_tabs": {
            "workflow_stage_x_ai_intervention_mode": _cross_tab(
                claim_units,
                left_field="workflow_stage_codes",
                right_field="ai_intervention_mode_codes",
                left_labels=WORKFLOW_STAGE_LABELS,
                right_labels=AI_INTERVENTION_MODE_LABELS,
            ),
            "ai_intervention_mode_x_normative_standard": _cross_tab(
                claim_units,
                left_field="ai_intervention_mode_codes",
                right_field="basis_codes",
                left_labels=AI_INTERVENTION_MODE_LABELS,
                right_labels=EVALUATION_LABELS,
            ),
            "ai_intervention_intensity_x_normative_tendency": _cross_tab(
                claim_units,
                left_field="ai_intervention_intensity_codes",
                right_field="legitimacy_codes",
                left_labels=AI_INTERVENTION_INTENSITY_LABELS,
                right_labels=LEGITIMACY_LABELS,
            ),
            "normative_standard_x_boundary_type": _cross_tab(
                claim_units,
                left_field="basis_codes",
                right_field="boundary_codes",
                left_labels=EVALUATION_LABELS,
                right_labels=BOUNDARY_CONTENT_LABELS,
            ),
            "evaluation_tension_x_boundary_mechanism": _cross_tab(
                claim_units,
                left_field="evaluation_tension_codes",
                right_field="boundary_mechanism_codes",
                left_labels=EVALUATION_TENSION_LABELS,
                right_labels=BOUNDARY_MECHANISM_LABELS,
            ),
            "formal_norm_reference_x_boundary_type": _cross_tab(
                claim_units,
                left_field="formal_norm_reference_codes",
                right_field="boundary_codes",
                left_labels=FORMAL_NORM_REFERENCE_LABELS,
                right_labels=BOUNDARY_CONTENT_LABELS,
            ),
            "boundary_mechanism_x_boundary_result": _cross_tab(
                claim_units,
                left_field="boundary_mechanism_codes",
                right_field="boundary_result_codes",
                left_labels=BOUNDARY_MECHANISM_LABELS,
                right_labels=BOUNDARY_RESULT_LABELS,
            ),
        },
    }


def _markdown_table(
    rows: list[dict[str, Any]],
    *,
    label_key: str = "label",
    empty_note: str = MISSING_V2_FIELD_NOTE,
) -> str:
    if not rows:
        return f"\n{empty_note}\n"
    lines = ["| 类别 | 数量 |", "|---|---:|"]
    for row in rows[:20]:
        lines.append(f"| {row[label_key]} | {row['count']} |")
    return "\n".join(lines)


def _write_readme(output_dir: Path, summary: dict[str, Any]) -> Path:
    metadata = summary["metadata"]
    text = f"""# Framework v2 Paper Materials

本目录服务于论文新框架：“话语情境 -> 实践位置 -> 介入方式 -> 规范评价 -> 边界生成”。

- 正式基线：`{ACTIVE_FORMAL_STAGE} post-only`
- 正式帖子 / 正式评论：`{metadata["formal_posts"]} / {metadata["formal_comments"]}`
- 数据来源：`{metadata["source_contract"]}`
- framework_v2 已 reviewed 正式帖子：`{metadata["framework_v2_reviewed_posts"]}`
- framework_v2 是否完成：`{metadata["framework_v2_coding_complete"]}`
- 说明：{metadata["note"]}

本目录不启动评论层正式结果，不改写 `quality_v5` artifacts，不把 `quality_v4` 写作当前正式口径。
"""
    path = output_dir / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_alignment(output_dir: Path) -> Path:
    text = f"""# Framework v2 Codebook Alignment

## 旧框架到新框架的映射

| 新五层框架 | 当前承载方式 | 说明 |
|---|---|---|
| 话语情境 | `platform`、`actor_type`、`discursive_mode`、`record_type`、`context_used` | 使用已有 canonical/source 字段映射，不新增重复字段。 |
| 实践位置 | A 组 `workflow_dimension` / `workflow_stage_codes` | A1 科研生产、A2 科研治理、A3 科研训练与能力建构被解释为实践位置。 |
| 介入方式 | F 组 `ai_intervention_mode_codes` | 需要后续人工编码；当前不自动推断。 |
| 介入强度 | G 组 `ai_intervention_intensity_codes` | 强度由具体使用方式决定，不由工具名称决定。 |
| 规范评价 | B 组倾向 + C 组标准 | “合法性”保留为历史术语，当前操作化为规范评价。 |
| 评价张力 | H 组 `evaluation_tension_codes` | 需要后续人工编码。 |
| 正式规范参照 | I 组 `formal_norm_reference_codes` | 需要后续人工编码。 |
| 边界生成 | D 组边界类型 + J/K 组机制与结果 | D 组保留，J/K 用于机制与结果扩展。 |

## 当前状态

{MISSING_V2_FIELD_NOTE}
"""
    path = output_dir / "framework_v2_codebook_alignment.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_chapter_materials(output_dir: Path, summary: dict[str, Any]) -> Path:
    tables = summary["tables"]
    note = summary["metadata"]["note"]
    text = f"""# Framework v2 Chapter Materials

## 第四章：话语情境与实践图谱

可用材料包括文本类型分布、科研活动场域分布与工作流环节分布。

### 文本类型分布
{_markdown_table(tables["text_type_distribution"], empty_note=note)}

### 科研活动场域分布
{_markdown_table(tables["research_activity_field_distribution"], empty_note=note)}

### 工作流环节分布
{_markdown_table(tables["workflow_stage_distribution"], empty_note=note)}

## 第五章：介入方式、介入强度与规范评价

当前 B/C 组已有正式人工编码，可用于规范评价倾向与标准。F/G/H 组尚需后续人工编码。

### 规范评价标准分布
{_markdown_table(tables["normative_evaluation_standard_distribution"], empty_note=note)}

### 规范评价倾向分布
{_markdown_table(tables["normative_evaluation_tendency_distribution"], empty_note=note)}

## 第六章：边界协商机制

D 组边界类型已有兼容编码；J/K 机制与结果字段尚需人工编码。

### 边界类型分布
{_markdown_table(tables["boundary_type_distribution"], empty_note=note)}

## 数据不足提醒

{note}
"""
    path = output_dir / "framework_v2_chapter_materials.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_writing_memo(output_dir: Path, *, note: str) -> Path:
    text = f"""# Framework v2 Writing Memo

## 可写主题

- 第四章可写：话语情境与实践位置的描述性图谱。支持字段：`discursive_mode`、`workflow_stage` 及由 A 组环节推导的 A1/A2/A3 场域。
- 第五章可写：已有 B/C 组支持的规范评价倾向与评价标准。支持字段：`legitimacy_codes`、`basis_codes`。
- 第六章可写：已有 D 组支持的边界类型。支持字段：`boundary_codes`、`boundary_mode_codes`。

## 可用典型摘录文件

- `outputs/excerpts/workflow_*.md`
- `outputs/excerpts/post_stance_*.md`
- `outputs/excerpts/boundary_*.md`

## 数据不足提醒

{note}

## 不应过度解释

- 不把 comment corpus 写成当前正式评论结果。
- 不把空的 F/G/H/I/J/K 表解释为“没有相关现象”。
- 不把 `quality_v4` 审计快照写成当前活跃正式结果。
- 不自动生成论文结论；这里只提供可写作提示和字段索引。
"""
    path = output_dir / "writing_memo_v2.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_framework_v2_materials(
    *,
    db_path: Path = RESEARCH_DB_PATH,
    output_dir: Path = FRAMEWORK_V2_OUTPUT_DIR,
    immutable: bool = False,
) -> dict[str, Any]:
    with connect_sqlite_readonly(db_path, immutable=immutable) as connection:
        posts = _load_formal_posts(connection)
        scope_counts = _load_scope_counts(connection)
        formal_post_ids = {str(post["post_id"]) for post in posts}
        reviewed_payloads = _load_reviewed_payloads(connection)
        reviewed_units = {
            record_id: normalize_claim_units(payload.get("claim_units"))
            for record_id, payload in reviewed_payloads.items()
        }
        framework_v2_reviewed_post_ids = {
            record_id
            for record_id, payload in reviewed_payloads.items()
            if record_id in formal_post_ids and payload.get("framework_v2_update") is True
        }
        db_units = _load_db_claim_units(connection, formal_post_ids)

    grouped_units = {
        post_id: reviewed_units.get(post_id) or db_units.get(post_id, [])
        for post_id in formal_post_ids
    }
    claim_units = [unit for units in grouped_units.values() for unit in units]
    framework_v2_coding_complete = bool(formal_post_ids) and formal_post_ids.issubset(
        framework_v2_reviewed_post_ids
    )
    summary = _build_summary_tables(
        posts,
        claim_units,
        scope_counts=scope_counts,
        framework_v2_reviewed_posts=len(framework_v2_reviewed_post_ids),
        framework_v2_coding_complete=framework_v2_coding_complete,
    )
    cross_tabs = _build_cross_tabs(claim_units, note=summary["metadata"]["note"])

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "framework_v2_summary_tables.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    cross_tabs_path = output_dir / "cross_tabs_v2.json"
    cross_tabs_path.write_text(json.dumps(cross_tabs, ensure_ascii=False, indent=2), encoding="utf-8")

    paths = {
        "readme": str(_write_readme(output_dir, summary)),
        "alignment": str(_write_alignment(output_dir)),
        "chapter_materials": str(_write_chapter_materials(output_dir, summary)),
        "summary_tables": str(summary_path),
        "cross_tabs": str(cross_tabs_path),
        "writing_memo": str(_write_writing_memo(output_dir, note=summary["metadata"]["note"])),
    }
    return {
        "output_dir": str(output_dir),
        "formal_posts": summary["metadata"]["formal_posts"],
        "formal_comments": summary["metadata"]["formal_comments"],
        "paths": paths,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build framework v2 paper materials.")
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--output-dir", type=Path, default=FRAMEWORK_V2_OUTPUT_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = generate_framework_v2_materials(db_path=args.db, output_dir=args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
