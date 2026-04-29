from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.xhs_expansion_review_precheck import (
    DEFAULT_REVIEWED_PATH,
    DEFAULT_STAGED_ACCEPTED_PATH,
    PHASE,
)
from ai4s_legitimacy.config.settings import OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

DEFAULT_REPORT_PATH = OUTPUTS_DIR / "reports" / PHASE / "supplemental_analysis.md"
DEFAULT_TABLE_DIR = OUTPUTS_DIR / "tables" / PHASE

TEXT_TYPE_LABELS = {
    "tool_recommendation": "工具推荐",
    "tutorial_or_experience": "教程展示/经验教程",
    "experience_sharing": "经验分享",
    "risk_warning": "风险提醒",
    "norm_interpretation": "规范解读",
    "comment_dispute": "评论争论",
    "unclear": "其他/无法判断",
    "": "其他/无法判断",
}

WORKFLOW_THEME_LABELS = {
    "literature_processing": "AI文献阅读与知识整合",
    "research_design": "AI研究设计与方法学习",
    "data_analysis_or_code": "AI数据分析与代码",
    "research_training": "AI科研训练与效率",
    "paper_writing": "AI论文写作与成果表达",
    "research_governance": "AI科研规范与治理",
    "unclear": "其他/无法判断",
    "": "其他/无法判断",
}

AI_MODE_LABELS = {
    "information_assistance": "信息辅助",
    "generation_assistance": "生成辅助",
    "analysis_modeling": "分析建模",
    "judgment_suggestion": "判断建议",
    "governance_or_supervision": "治理监督",
    "unclear": "其他/无法判断",
    "": "其他/无法判断",
}

AI_INTENSITY_LABELS = {
    "low_assistance": "低强度辅助",
    "medium_cocreation": "中强度共创",
    "high_substitution": "高强度替代",
    "unclear": "其他/无法判断",
    "": "其他/无法判断",
}

NORMATIVE_SIGNAL_LABELS = {
    "efficiency_positive": "效率认可",
    "conditional_or_boundary_signal": "条件/边界信号",
    "integrity_risk": "学术诚信风险",
    "none_or_unclear": "无明确规范评价",
    "": "无明确规范评价",
}

BOUNDARY_SIGNAL_LABELS = {
    "assistance_vs_substitution": "辅助与替代边界",
    "disclosure_boundary": "披露边界",
    "academic_integrity_boundary": "学术诚信边界",
    "none_or_unclear": "无明确边界信号",
    "": "无明确边界信号",
}

QUALITY_V5_WORKFLOW_THEME_MAP = {
    "文献调研与知识整合": "literature_processing",
    "研究构思与问题定义": "research_design",
    "研究设计与方案制定": "research_design",
    "数据获取": "data_analysis_or_code",
    "数据处理与分析建模": "data_analysis_or_code",
    "结果验证与论文复现": "data_analysis_or_code",
    "实验实施与仿真执行": "data_analysis_or_code",
    "结果解释与理论提炼": "data_analysis_or_code",
    "学术写作与成果表达": "paper_writing",
    "发表与知识扩散": "paper_writing",
    "出版与评审治理": "research_governance",
    "研究方法学习": "research_training",
    "学术阅读与写作能力训练": "research_training",
    "科研工具与技术技能训练": "research_training",
}

QUALITY_V5_TEXT_TYPE_MAP = {
    "experience_share": "经验分享",
    "question_help_seeking": "经验分享",
    "advice_guidance": "教程展示/经验教程",
    "practice_demo": "教程展示/经验教程",
    "criticism": "风险提醒",
    "policy_statement": "规范解读",
    "reflection": "经验分享",
    "unclear": "其他/无法判断",
    "": "其他/无法判断",
}

GAP_SPECS = {
    "科研训练材料": {
        "supplemental_field": "workflow_stage",
        "supplemental_values": {"research_training"},
        "quality_v5_theme": "research_training",
    },
    "AI数据分析材料": {
        "supplemental_field": "workflow_stage",
        "supplemental_values": {"data_analysis_or_code"},
        "quality_v5_theme": "data_analysis_or_code",
    },
    "AI使用披露讨论": {
        "supplemental_field": "boundary_signal",
        "supplemental_values": {"disclosure_boundary"},
        "quality_v5_theme": None,
    },
    "AI学术诚信讨论": {
        "supplemental_field": "normative_evaluation_signal",
        "supplemental_values": {"integrity_risk"},
        "quality_v5_theme": None,
    },
    "AI审稿/检测讨论": {
        "supplemental_field": "ai_intervention_mode",
        "supplemental_values": {"governance_or_supervision"},
        "quality_v5_theme": "research_governance",
    },
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()}) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _write_table_pair(table_dir: Path, name: str, rows: list[dict[str, Any]]) -> None:
    _write_json(table_dir / f"{name}.json", rows)
    _write_csv(table_dir / f"{name}.csv", rows)


def _value(row: dict[str, Any], field: str) -> str:
    return str(row.get(field) or "").strip()


def _distribution(
    rows: list[dict[str, Any]],
    field: str,
    *,
    labels: dict[str, str] | None = None,
    missing_label: str = "缺失/未记录",
) -> list[dict[str, Any]]:
    counter = Counter(_value(row, field) or "__missing__" for row in rows)
    total = sum(counter.values())
    output: list[dict[str, Any]] = []
    for raw_value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        value = "" if raw_value == "__missing__" else raw_value
        label = missing_label if raw_value == "__missing__" else value
        if labels is not None:
            label = missing_label if raw_value == "__missing__" else labels.get(value, value)
        output.append(
            {
                "value": value,
                "label": label,
                "count": count,
                "share": round(count / total, 4) if total else 0.0,
                "source_scope": PHASE,
            }
        )
    return output


def _decision_counts(reviewed_rows: list[dict[str, Any]], staged_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_rows = reviewed_rows if reviewed_rows else staged_rows
    counter = Counter(_value(row, "final_decision") or "include" for row in source_rows)
    total = sum(counter.values())
    return [
        {
            "final_decision": decision,
            "count": counter.get(decision, 0),
            "share": round(counter.get(decision, 0) / total, 4) if total else 0.0,
            "count_source": "reviewed_jsonl" if reviewed_rows else "staged_accepted_jsonl",
            "source_scope": PHASE,
        }
        for decision in ("include", "review_needed", "exclude")
    ]


def _post_month_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter()
    missing = 0
    for row in rows:
        post_date = _value(row, "post_date")
        if len(post_date) >= 7:
            counter[post_date[:7]] += 1
        else:
            missing += 1
    if missing:
        counter["缺失/未记录"] += missing
    total = sum(counter.values())
    return [
        {
            "post_month": month,
            "count": count,
            "share": round(count / total, 4) if total else 0.0,
            "source_scope": PHASE,
        }
        for month, count in sorted(counter.items())
    ]


def _theme_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _distribution(
        rows,
        "workflow_stage",
        labels=WORKFLOW_THEME_LABELS,
        missing_label="其他/无法判断",
    )


def _load_quality_v5_rows(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    with connect_sqlite_readonly(db_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT p.post_id, p.post_date, p.workflow_stage, p.discursive_mode,
                       p.title, p.content_text
                FROM posts p
                JOIN vw_posts_paper_scope_quality_v5 s ON s.post_id = p.post_id
                ORDER BY p.post_date, p.post_id
                """
            ).fetchall()
        ]


def _quality_v5_theme_distribution(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        QUALITY_V5_WORKFLOW_THEME_MAP.get(_value(row, "workflow_stage"), "unclear")
        for row in rows
    )


def _quality_v5_text_type_distribution(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        QUALITY_V5_TEXT_TYPE_MAP.get(_value(row, "discursive_mode"), "其他/无法判断")
        for row in rows
    )


def _quality_v5_comparison(
    staged_rows: list[dict[str, Any]],
    quality_v5_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    supplemental_counter = Counter(_value(row, "workflow_stage") or "unclear" for row in staged_rows)
    quality_v5_counter = _quality_v5_theme_distribution(quality_v5_rows)
    supplemental_total = sum(supplemental_counter.values())
    quality_v5_total = sum(quality_v5_counter.values())
    theme_codes = sorted(set(WORKFLOW_THEME_LABELS) | set(supplemental_counter) | set(quality_v5_counter))
    output: list[dict[str, Any]] = []
    for theme_code in theme_codes:
        if theme_code == "":
            continue
        supplemental_count = supplemental_counter.get(theme_code, 0)
        quality_v5_count = quality_v5_counter.get(theme_code, 0)
        output.append(
            {
                "theme_code": theme_code,
                "theme_label": WORKFLOW_THEME_LABELS.get(theme_code, theme_code),
                "supplemental_count": supplemental_count,
                "supplemental_share": round(supplemental_count / supplemental_total, 4)
                if supplemental_total
                else 0.0,
                "quality_v5_count": quality_v5_count,
                "quality_v5_share": round(quality_v5_count / quality_v5_total, 4)
                if quality_v5_total
                else 0.0,
                "share_delta_supplemental_minus_quality_v5": round(
                    (supplemental_count / supplemental_total if supplemental_total else 0.0)
                    - (quality_v5_count / quality_v5_total if quality_v5_total else 0.0),
                    4,
                ),
            }
        )
    return sorted(output, key=lambda row: (-abs(row["share_delta_supplemental_minus_quality_v5"]), row["theme_code"]))


def _quality_v5_text_type_comparison(
    staged_rows: list[dict[str, Any]],
    quality_v5_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    supplemental_counter = Counter(
        TEXT_TYPE_LABELS.get(_value(row, "discourse_context"), _value(row, "discourse_context"))
        for row in staged_rows
    )
    quality_v5_counter = _quality_v5_text_type_distribution(quality_v5_rows)
    supplemental_total = sum(supplemental_counter.values())
    quality_v5_total = sum(quality_v5_counter.values())
    labels = sorted(set(supplemental_counter) | set(quality_v5_counter))
    output: list[dict[str, Any]] = []
    for label in labels:
        supplemental_count = supplemental_counter.get(label, 0)
        quality_v5_count = quality_v5_counter.get(label, 0)
        output.append(
            {
                "text_type": label,
                "supplemental_count": supplemental_count,
                "supplemental_share": round(supplemental_count / supplemental_total, 4)
                if supplemental_total
                else 0.0,
                "quality_v5_count": quality_v5_count,
                "quality_v5_share": round(quality_v5_count / quality_v5_total, 4)
                if quality_v5_total
                else 0.0,
                "share_delta_supplemental_minus_quality_v5": round(
                    (supplemental_count / supplemental_total if supplemental_total else 0.0)
                    - (quality_v5_count / quality_v5_total if quality_v5_total else 0.0),
                    4,
                ),
            }
        )
    return sorted(
        output,
        key=lambda row: (-abs(row["share_delta_supplemental_minus_quality_v5"]), row["text_type"]),
    )


def _supplemental_count(rows: list[dict[str, Any]], field: str, values: set[str]) -> int:
    return sum(1 for row in rows if _value(row, field) in values)


def _gap_assessment(
    staged_rows: list[dict[str, Any]],
    quality_v5_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    quality_v5_themes = _quality_v5_theme_distribution(quality_v5_rows)
    rows: list[dict[str, Any]] = []
    for gap_label, spec in GAP_SPECS.items():
        supplemental_count = _supplemental_count(
            staged_rows,
            str(spec["supplemental_field"]),
            set(spec["supplemental_values"]),
        )
        quality_v5_theme = spec["quality_v5_theme"]
        quality_v5_count = (
            quality_v5_themes.get(str(quality_v5_theme), 0) if quality_v5_theme else None
        )
        if supplemental_count >= 10:
            assessment = "有一定补充价值，建议进入人工编码评估。"
        elif supplemental_count > 0:
            assessment = "有少量补充，但不足以直接支撑主结果。"
        else:
            assessment = "当前补充样本未明显覆盖该方向。"
        rows.append(
            {
                "gap_direction": gap_label,
                "supplemental_count": supplemental_count,
                "quality_v5_comparable_count": quality_v5_count,
                "assessment": assessment,
                "source_scope": PHASE,
            }
        )
    return rows


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], limit: int = 20) -> str:
    if not rows:
        return "\n无可用数据。\n"
    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, separator]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return "\n".join(lines)


def _recommendation(gap_rows: list[dict[str, Any]], accepted_count: int, review_needed_count: int) -> str:
    has_useful_supplement = any(int(row["supplemental_count"]) >= 10 for row in gap_rows)
    if accepted_count == 0:
        return "暂不纳入论文主结果；当前没有通过 staging 的 include 样本。"
    if has_useful_supplement or review_needed_count:
        return (
            "建议先作为补充材料并进入人工编码；暂不直接进入论文主结果。"
            "若后续完成 supplemental formalization，可再讨论是否启动 quality_v6。"
        )
    return "建议只作为补充材料；暂不进入新的 quality_v6。"


def _render_report(
    *,
    staged_rows: list[dict[str, Any]],
    reviewed_rows: list[dict[str, Any]],
    quality_v5_rows: list[dict[str, Any]],
    tables: dict[str, list[dict[str, Any]]],
    staged_path: Path,
    reviewed_path: Path,
) -> str:
    decision_lookup = {
        row["final_decision"]: int(row["count"]) for row in tables["supplemental_decision_counts"]
    }
    accepted_count = decision_lookup.get("include", len(staged_rows))
    review_needed_count = decision_lookup.get("review_needed", 0)
    recommendation = _recommendation(
        tables["supplemental_gap_assessment"],
        accepted_count,
        review_needed_count,
    )
    coding_focus = (
        "可以进入下一轮人工编码，尤其是对 `review_needed` 与边界/规范信号较强样本做复核。"
        if review_needed_count
        else "可以进入下一轮人工编码，重点复核已 include 样本中的边界/规范信号较强材料。"
    )
    query_note = (
        "本轮 staging 行缺失逐条 `query_group`，因此查询词组分布只能显示为缺失，"
        "不能据此判断查询词组表现。"
        if any(row["label"] == "缺失/未记录" for row in tables["supplemental_query_group_distribution"])
        else "查询词组元数据可用于后续抽样评估。"
    )
    reviewed_source = "reviewed JSONL" if reviewed_rows else "staged accepted JSONL"
    text = f"""# xhs_expansion_candidate_v1 supplemental analysis

本报告只描述 `xhs_expansion_candidate_v1` 补充候选样本结构，不生成论文结论，不把候选样本混同为 `quality_v5` 正式结果。

## Scope Guard

- source_scope: `xhs_expansion_candidate_v1`
- staged include input: `{staged_path}`
- decision count source: `{reviewed_source}`
- reviewed input: `{reviewed_path}`
- quality_v5 comparison source: `vw_posts_paper_scope_quality_v5`
- quality_v5 formal scope remains: `514 / 0`
- 本报告未写入研究主库，未更新 freeze checkpoint，未更新 `quality_v5` consistency report。

## 1. 补充样本总量

- staged accepted posts: `{len(staged_rows)}`
- reviewed candidate rows: `{len(reviewed_rows) if reviewed_rows else len(staged_rows)}`
- quality_v5 formal posts for comparison: `{len(quality_v5_rows)}`

## 2. include / review_needed / exclude 数量

{_markdown_table(tables["supplemental_decision_counts"], [("final_decision", "decision"), ("count", "count"), ("share", "share")])}

## 3. 查询词组分布

{query_note}

{_markdown_table(tables["supplemental_query_group_distribution"], [("label", "query_group"), ("count", "count"), ("share", "share")])}

## 4. 发帖时间分布

{_markdown_table(tables["supplemental_post_month_distribution"], [("post_month", "month"), ("count", "count"), ("share", "share")])}

## 5. 文本类型初步分布

该分布来自 supplemental reviewed/staging 中的 `discourse_context`，属于初步结构描述，不等于正式论文发现。

{_markdown_table(tables["supplemental_text_type_distribution"], [("label", "text_type"), ("count", "count"), ("share", "share")])}

## 6. AI科研实践主题初步分布

该分布来自 `workflow_stage` 的 supplemental 初步人工/半人工 review 字段，仅用于判断补充样本结构。

{_markdown_table(tables["supplemental_research_theme_distribution"], [("label", "theme"), ("count", "count"), ("share", "share")])}

## 7. 与 quality_v5 现有 514 条样本的差异

下表只比较主题结构比例，不表示理论规律。

{_markdown_table(tables["supplemental_quality_v5_theme_comparison"], [("theme_label", "theme"), ("supplemental_count", "supplemental_n"), ("supplemental_share", "supplemental_share"), ("quality_v5_count", "quality_v5_n"), ("quality_v5_share", "quality_v5_share"), ("share_delta_supplemental_minus_quality_v5", "share_delta")])}

文本类型结构对比如下。注意：supplemental 的文本类型来自 `discourse_context`，
`quality_v5` 的文本类型来自 `discursive_mode` 映射，二者不是完全同构字段；
例如 `工具推荐` 在 `quality_v5` 旧字段中没有直接同名类别。

{_markdown_table(tables["supplemental_quality_v5_text_type_comparison"], [("text_type", "text_type"), ("supplemental_count", "supplemental_n"), ("supplemental_share", "supplemental_share"), ("quality_v5_count", "quality_v5_n"), ("quality_v5_share", "quality_v5_share"), ("share_delta_supplemental_minus_quality_v5", "share_delta")])}

## 8. 对既有样本不足方向的补充价值

{_markdown_table(tables["supplemental_gap_assessment"], [("gap_direction", "direction"), ("supplemental_count", "supplemental_n"), ("quality_v5_comparable_count", "quality_v5_comparable_n"), ("assessment", "assessment")])}

## 9. 纳入建议

{recommendation}

建议口径：

- 当前只作为 `xhs_expansion_candidate_v1` 补充材料和候选样本结构报告。
- {coding_focus}
- 不建议直接并入 `quality_v5` 主结果。
- 是否进入新的 `quality_v6`，应在完成去重、query metadata 修复、人工编码和 supplemental formalization 方案后单独决定。

## Additional Tables

- AI介入方式：`supplemental_ai_intervention_mode_distribution.*`
- AI介入强度：`supplemental_ai_intervention_intensity_distribution.*`
- 规范评价信号：`supplemental_normative_signal_distribution.*`
- 边界信号：`supplemental_boundary_signal_distribution.*`

所有表格均标注 `source_scope = xhs_expansion_candidate_v1`，不得作为 `quality_v5` 正式统计引用。
"""
    return text


def generate_xhs_expansion_supplemental_analysis(
    *,
    staged_path: Path = DEFAULT_STAGED_ACCEPTED_PATH,
    reviewed_path: Path = DEFAULT_REVIEWED_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    table_dir: Path = DEFAULT_TABLE_DIR,
) -> dict[str, Any]:
    staged_rows = _read_jsonl(staged_path)
    reviewed_rows = _read_jsonl(reviewed_path)
    quality_v5_rows = _load_quality_v5_rows(db_path)

    tables = {
        "supplemental_decision_counts": _decision_counts(reviewed_rows, staged_rows),
        "supplemental_query_group_distribution": _distribution(staged_rows, "query_group"),
        "supplemental_post_month_distribution": _post_month_distribution(staged_rows),
        "supplemental_text_type_distribution": _distribution(
            staged_rows,
            "discourse_context",
            labels=TEXT_TYPE_LABELS,
            missing_label="其他/无法判断",
        ),
        "supplemental_research_theme_distribution": _theme_distribution(staged_rows),
        "supplemental_ai_intervention_mode_distribution": _distribution(
            staged_rows,
            "ai_intervention_mode",
            labels=AI_MODE_LABELS,
            missing_label="其他/无法判断",
        ),
        "supplemental_ai_intervention_intensity_distribution": _distribution(
            staged_rows,
            "ai_intervention_intensity",
            labels=AI_INTENSITY_LABELS,
            missing_label="其他/无法判断",
        ),
        "supplemental_normative_signal_distribution": _distribution(
            staged_rows,
            "normative_evaluation_signal",
            labels=NORMATIVE_SIGNAL_LABELS,
            missing_label="无明确规范评价",
        ),
        "supplemental_boundary_signal_distribution": _distribution(
            staged_rows,
            "boundary_signal",
            labels=BOUNDARY_SIGNAL_LABELS,
            missing_label="无明确边界信号",
        ),
        "supplemental_quality_v5_theme_comparison": _quality_v5_comparison(
            staged_rows,
            quality_v5_rows,
        ),
        "supplemental_quality_v5_text_type_comparison": _quality_v5_text_type_comparison(
            staged_rows,
            quality_v5_rows,
        ),
        "supplemental_gap_assessment": _gap_assessment(staged_rows, quality_v5_rows),
    }
    table_dir.mkdir(parents=True, exist_ok=True)
    for table_name, rows in tables.items():
        _write_table_pair(table_dir, table_name, rows)

    summary = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_scope": PHASE,
        "formal_scope": False,
        "quality_v5_formal": False,
        "supplemental_candidate": True,
        "staged_path": str(staged_path),
        "reviewed_path": str(reviewed_path),
        "report_path": str(report_path),
        "summary_path": str(table_dir / "supplemental_analysis_summary.json"),
        "staged_accepted_count": len(staged_rows),
        "reviewed_count": len(reviewed_rows),
        "quality_v5_comparison_count": len(quality_v5_rows),
        "table_files": {
            name: {
                "json": str(table_dir / f"{name}.json"),
                "csv": str(table_dir / f"{name}.csv"),
            }
            for name in tables
        },
        "notes": [
            "Only describes xhs_expansion_candidate_v1 sample structure.",
            "Does not write to research DB or quality_v5 formal scope.",
            "Does not generate theoretical findings or paper conclusions.",
        ],
    }
    _write_json(table_dir / "supplemental_analysis_summary.json", summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            staged_rows=staged_rows,
            reviewed_rows=reviewed_rows,
            quality_v5_rows=quality_v5_rows,
            tables=tables,
            staged_path=staged_path,
            reviewed_path=reviewed_path,
        ),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build xhs_expansion_candidate_v1 supplemental sample analysis."
    )
    parser.add_argument("--staged", type=Path, default=DEFAULT_STAGED_ACCEPTED_PATH)
    parser.add_argument("--reviewed", type=Path, default=DEFAULT_REVIEWED_PATH)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = generate_xhs_expansion_supplemental_analysis(
        staged_path=args.staged,
        reviewed_path=args.reviewed,
        db_path=args.db,
        report_path=args.report,
        table_dir=args.table_dir,
    )
    print(summary["report_path"])
    print(summary["summary_path"])


if __name__ == "__main__":
    main()
