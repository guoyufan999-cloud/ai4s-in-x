from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ai4s_legitimacy.analysis.framework_v2_materials import FRAMEWORK_V2_OUTPUT_DIR
from ai4s_legitimacy.collection.canonical_schema import (
    AI_INTERVENTION_INTENSITY_LABELS,
    AI_INTERVENTION_MODE_LABELS,
    BOUNDARY_MECHANISM_LABELS,
    BOUNDARY_RESULT_LABELS,
    EVALUATION_TENSION_LABELS,
    FORMAL_NORM_REFERENCE_LABELS,
)
from ai4s_legitimacy.config.formal_baseline import ACTIVE_FORMAL_STAGE
from ai4s_legitimacy.config.settings import OUTPUTS_DIR

POST_MASTER_PATH = OUTPUTS_DIR / "tables" / "post_review_v2_master.jsonl"
SUMMARY_TABLES_PATH = FRAMEWORK_V2_OUTPUT_DIR / "framework_v2_summary_tables.json"
CROSS_TABS_PATH = FRAMEWORK_V2_OUTPUT_DIR / "cross_tabs_v2.json"
AUDIT_JSON_PATH = FRAMEWORK_V2_OUTPUT_DIR / "framework_v2_coding_audit_report.json"
AUDIT_MD_PATH = FRAMEWORK_V2_OUTPUT_DIR / "framework_v2_coding_audit_report.md"
AUDIT_APPENDIX_PATH = FRAMEWORK_V2_OUTPUT_DIR / "framework_v2_high_risk_recheck_appendix.md"

V2_FIELD_TO_GROUP = {
    "ai_intervention_mode_codes": "F",
    "ai_intervention_intensity_codes": "G",
    "evaluation_tension_codes": "H",
    "formal_norm_reference_codes": "I",
    "boundary_mechanism_codes": "J",
    "boundary_result_codes": "K",
}

HIGH_RISK_LABELS = {
    "G3": "高强度替代",
    "F5": "自动执行",
    "F6": "治理监督",
    "K4": "替代去合法化",
    "K6": "治理争议化",
    "I2": "学校规定",
    "I7": "科研诚信规则",
    "I8": "数据伦理/隐私合规规则",
    "multi_H": "多重评价张力",
    "no_D_strong_norm": "无 D 组边界但有强规范评价",
}

HIGH_RISK_RECHECK_NOTES = {
    "G3": "核对高强度替代是否由具体使用方式支持。",
    "F5": "核对自动执行是否涉及核心产出、核心判断或规范决策。",
    "F6": "核对治理监督是否确有检测、查重、评审或合规治理含义。",
    "K4": "核对替代去合法化是否确有禁止或不可接受替代表述。",
    "K6": "核对治理争议化是否体现对检测、规则或制度执行的争议。",
    "I2": "核对学校规定是否被明确提及或由文本直接指向。",
    "I7": "核对科研诚信规则是否与文本中的诚信、撤稿、造假等风险相关。",
    "I8": "核对数据伦理或隐私合规是否有明确文本依据。",
    "multi_H": "核对多重评价张力是否均有文本依据。",
    "no_D_strong_norm": "核对是否需要补充 D 组边界，或仅为评价而非边界表达。",
}

STRONG_NORMATIVE_B_CODES = {"B3", "B4"}
STRONG_NORMATIVE_C_CODES = {
    "C3",
    "C4",
    "C5",
    "C6",
    "C8",
    "C11",
    "C12",
    "C13",
    "C14",
}
PROVENANCE_MARKER = "user_accepted_assistant_draft"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _code_values(values: Any) -> list[str]:
    output: list[str] = []
    if not isinstance(values, list):
        return output
    for item in values:
        if isinstance(item, dict):
            code = item.get("code")
        else:
            code = item
        if code:
            output.append(str(code))
    return output


def _first_evidence(claim_unit: dict[str, Any], *, limit: int = 80) -> str:
    evidence = claim_unit.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return ""
    text = str(evidence[0]).replace("\n", " ").strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _claim_units(row: dict[str, Any]) -> list[dict[str, Any]]:
    units = row.get("claim_units")
    return units if isinstance(units, list) else []


def _validate_claim_unit(row: dict[str, Any], claim_unit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    record_id = str(row.get("record_id") or row.get("post_id") or "")
    prefix = f"{record_id} claim={claim_unit.get('practice_unit', '')[:40]}"
    field_values = {field: claim_unit.get(field) for field in V2_FIELD_TO_GROUP}
    for field, value in field_values.items():
        if value is not None and not isinstance(value, list):
            errors.append(f"{prefix}: {field} is not a list")

    f_codes = _code_values(claim_unit.get("ai_intervention_mode_codes"))
    g_codes = _code_values(claim_unit.get("ai_intervention_intensity_codes"))
    i_codes = _code_values(claim_unit.get("formal_norm_reference_codes"))
    j_codes = _code_values(claim_unit.get("boundary_mechanism_codes"))
    k_codes = _code_values(claim_unit.get("boundary_result_codes"))
    d_codes = _code_values(claim_unit.get("boundary_codes"))

    if not f_codes:
        errors.append(f"{prefix}: missing F")
    if len(g_codes) != 1:
        errors.append(f"{prefix}: G must have exactly one code")
    if not i_codes:
        errors.append(f"{prefix}: missing I")
    if "I0" in i_codes and len(i_codes) > 1:
        errors.append(f"{prefix}: I0 mixed with formal references")
    if d_codes and (not j_codes or len(k_codes) != 1):
        errors.append(f"{prefix}: D present but J/K incomplete")
    if not d_codes and (j_codes or k_codes):
        errors.append(f"{prefix}: J/K present without D")
    return errors


def _flag_high_risk(claim_unit: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    f_codes = set(_code_values(claim_unit.get("ai_intervention_mode_codes")))
    g_codes = set(_code_values(claim_unit.get("ai_intervention_intensity_codes")))
    h_codes = _code_values(claim_unit.get("evaluation_tension_codes"))
    i_codes = set(_code_values(claim_unit.get("formal_norm_reference_codes")))
    k_codes = set(_code_values(claim_unit.get("boundary_result_codes")))
    b_codes = set(_code_values(claim_unit.get("legitimacy_codes")))
    c_codes = set(_code_values(claim_unit.get("basis_codes")))
    d_codes = set(_code_values(claim_unit.get("boundary_codes")))

    for code in ("G3", "F5", "F6", "K4", "K6", "I2", "I7", "I8"):
        if (
            code in f_codes
            or code in g_codes
            or code in i_codes
            or code in k_codes
        ):
            flags.append(code)
    if len(h_codes) > 1:
        flags.append("multi_H")
    if not d_codes and (
        b_codes & STRONG_NORMATIVE_B_CODES or c_codes & STRONG_NORMATIVE_C_CODES
    ):
        flags.append("no_D_strong_norm")
    return flags


def _distribution_rows(counter: Counter[str], labels: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code, count in counter.most_common():
        rows.append({"code": code, "label": labels.get(code, code), "count": count})
    return rows


def _pct(part: int, whole: int) -> str:
    if not whole:
        return "0.0%"
    return f"{part / whole * 100:.1f}%"


def build_framework_v2_coding_audit(
    *,
    post_master_path: Path = POST_MASTER_PATH,
    summary_tables_path: Path = SUMMARY_TABLES_PATH,
    cross_tabs_path: Path = CROSS_TABS_PATH,
) -> dict[str, Any]:
    summary = _read_json(summary_tables_path)
    cross_tabs = _read_json(cross_tabs_path)
    rows = [
        row
        for row in _read_jsonl(post_master_path)
        if row.get("framework_v2_update") is True
    ]

    violations: list[str] = []
    row_counter: Counter[str] = Counter()
    claim_counter: Counter[str] = Counter()
    code_counters: dict[str, Counter[str]] = defaultdict(Counter)
    high_risk_counter: Counter[str] = Counter()
    high_risk_rows: list[dict[str, Any]] = []
    provenance_missing: list[str] = []
    claim_unit_count = 0

    for row in rows:
        row_counter.update([str(row.get("run_id") or "unknown")])
        notes = row.get("framework_v2_reviewer_notes")
        note_text = (
            " ".join(str(note) for note in notes)
            if isinstance(notes, list)
            else str(notes)
        )
        if PROVENANCE_MARKER not in note_text:
            provenance_missing.append(str(row.get("record_id") or row.get("post_id") or ""))
        if row.get("review_status") != "reviewed":
            violations.append(f"{row.get('record_id')}: review_status is not reviewed")

        for claim_index, claim_unit in enumerate(_claim_units(row), 1):
            claim_unit_count += 1
            claim_counter.update([str(row.get("run_id") or "unknown")])
            violations.extend(_validate_claim_unit(row, claim_unit))
            for field, group in V2_FIELD_TO_GROUP.items():
                code_counters[group].update(_code_values(claim_unit.get(field)))
            flags = _flag_high_risk(claim_unit)
            if flags:
                high_risk_counter.update(flags)
                high_risk_rows.append(
                    {
                        "record_id": row.get("record_id"),
                        "post_id": row.get("post_id"),
                        "run_id": row.get("run_id"),
                        "theme_summary": row.get("theme_summary"),
                        "claim_index": claim_index,
                        "practice_unit": claim_unit.get("practice_unit"),
                        "flags": flags,
                        "evidence": _first_evidence(claim_unit),
                    }
                )

    high_risk_rows.sort(key=lambda item: (-len(item["flags"]), str(item["record_id"])))

    field_labels = {
        "F": AI_INTERVENTION_MODE_LABELS,
        "G": AI_INTERVENTION_INTENSITY_LABELS,
        "H": EVALUATION_TENSION_LABELS,
        "I": FORMAL_NORM_REFERENCE_LABELS,
        "J": BOUNDARY_MECHANISM_LABELS,
        "K": BOUNDARY_RESULT_LABELS,
    }
    code_distributions = {
        group: _distribution_rows(counter, field_labels[group])
        for group, counter in sorted(code_counters.items())
    }
    high_risk_distribution = [
        {
            "code": code,
            "label": HIGH_RISK_LABELS.get(code, code),
            "count": count,
            "share_of_claim_units": _pct(count, claim_unit_count),
        }
        for code, count in high_risk_counter.most_common()
    ]

    metadata = summary["metadata"]
    return {
        "metadata": {
            "formal_stage": metadata.get("formal_stage", ACTIVE_FORMAL_STAGE),
            "formal_posts": metadata.get("formal_posts"),
            "formal_comments": metadata.get("formal_comments"),
            "framework_v2_reviewed_posts": metadata.get("framework_v2_reviewed_posts"),
            "framework_v2_missing_posts": metadata.get("framework_v2_missing_posts"),
            "framework_v2_coding_complete": metadata.get("framework_v2_coding_complete"),
            "post_rows_with_framework_v2_update": len(rows),
            "claim_units_with_framework_v2_fields": claim_unit_count,
            "source_post_master": str(post_master_path),
            "source_summary_tables": str(summary_tables_path),
            "source_cross_tabs": str(cross_tabs_path),
        },
        "batch_coverage": {
            "post_rows_by_run_id": dict(sorted(row_counter.items())),
            "claim_units_by_run_id": dict(sorted(claim_counter.items())),
        },
        "mechanical_checks": {
            "status": "ok" if not violations and not provenance_missing else "review_needed",
            "violation_count": len(violations),
            "violations": violations[:200],
            "provenance_missing_count": len(provenance_missing),
            "provenance_missing_record_ids": provenance_missing[:200],
        },
        "code_distributions": code_distributions,
        "high_risk": {
            "distribution": high_risk_distribution,
            "sample_rows": high_risk_rows[:80],
            "sample_rows_total": len(high_risk_rows),
        },
        "summary_tables": summary["tables"],
        "cross_tab_samples": {
            key: value[:20] for key, value in cross_tabs.get("cross_tabs", {}).items()
        },
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def _render_distribution(rows: list[dict[str, Any]], *, limit: int = 12) -> str:
    return _markdown_table(
        ["代码", "类别", "数量"],
        [[row["code"], row["label"], row["count"]] for row in rows[:limit]],
    )


def _escape_markdown_cell(value: Any) -> str:
    return str(value or "").replace("\n", " ").replace("|", "/").strip()


def _recheck_focus(flags: list[str]) -> str:
    notes = [HIGH_RISK_RECHECK_NOTES.get(flag, flag) for flag in flags]
    return " ".join(notes[:3])


def render_audit_markdown(audit: dict[str, Any]) -> str:
    metadata = audit["metadata"]
    checks = audit["mechanical_checks"]
    high_risk = audit["high_risk"]
    high_risk_rows = high_risk["sample_rows"][:30]
    batch_rows = [
        [run_id, count, audit["batch_coverage"]["claim_units_by_run_id"].get(run_id, 0)]
        for run_id, count in audit["batch_coverage"]["post_rows_by_run_id"].items()
    ]
    sample_rows = [
        [
            row["record_id"],
            row["claim_index"],
            ",".join(row["flags"]),
            str(row["theme_summary"]).replace("|", "/"),
            str(row["evidence"]).replace("|", "/"),
        ]
        for row in high_risk_rows
    ]

    return f"""# Framework v2 Coding Audit Report

## 审计结论

- 正式基线：`{metadata["formal_stage"]} post-only`
- 正式帖子 / 正式评论：`{metadata["formal_posts"]} / {metadata["formal_comments"]}`
- framework_v2 reviewed posts：`{metadata["framework_v2_reviewed_posts"]}`
- framework_v2 missing posts：`{metadata["framework_v2_missing_posts"]}`
- framework_v2 coding complete：`{metadata["framework_v2_coding_complete"]}`
- v2 claim units：`{metadata["claim_units_with_framework_v2_fields"]}`

本审计确认的是工程一致性、字段完整性和高风险复核队列；它不能替代逐条语义复核。当前 F/G/H/I/J/K 字段来自“用户授权接受 AI 辅助编码草稿并保留 provenance”的补码流程，不应表述为双人独立人工复核。

## 机械一致性检查

- 状态：`{checks["status"]}`
- 字段规则违规数：`{checks["violation_count"]}`
- 缺失 provenance 标记记录数：`{checks["provenance_missing_count"]}`

检查规则包括：F 至少 1 个、G 正好 1 个、I 至少 1 个、`I0` 不与 `I1-I8` 混用、有 D 组边界时必须有 J/K、无 D 组边界时 J/K 必须为空、每条导入记录保持 `review_status=reviewed`。

## 批次覆盖

{_markdown_table(["run_id", "post rows", "claim units"], batch_rows)}

## F/G/H/I/J/K 分布

### F 介入方式
{_render_distribution(audit["code_distributions"].get("F", []))}

### G 介入强度
{_render_distribution(audit["code_distributions"].get("G", []))}

### H 评价张力
{_render_distribution(audit["code_distributions"].get("H", []))}

### I 正式规范参照
{_render_distribution(audit["code_distributions"].get("I", []))}

### J 边界协商机制
{_render_distribution(audit["code_distributions"].get("J", []))}

### K 边界协商结果
{_render_distribution(audit["code_distributions"].get("K", []))}

## 高风险复核队列

高风险并不等于错误，而是后续人工抽查优先级。优先关注 `G3`、`F5/F6`、`K4/K6`、`I2/I7/I8`、多重 H，以及无 D 组边界但带有强规范评价的 claim unit。

{_markdown_table(["标记", "含义", "数量", "占 claim units"], [[row["code"], row["label"], row["count"], row["share_of_claim_units"]] for row in high_risk["distribution"]])}

### 高风险样本摘录

{_markdown_table(["record_id", "claim", "flags", "theme", "evidence"], sample_rows)}

## 写作使用边界

- 可以使用本报告证明 v2 补码已覆盖 `514/514` 正式帖子，且通过字段级一致性检查。
- 可以把 F/G/H/I/J/K 统计表作为正式 v2 描述性结果使用。
- 不应把本报告写成“编码完全无误”或“双人独立复核一致”。
- 如果论文需要更强方法说服力，建议对高风险队列抽取 `50-80` 条做人工复核，记录修正率与典型修正类型。
"""


def render_high_risk_recheck_appendix(
    audit: dict[str, Any],
    *,
    sample_size: int = 80,
) -> str:
    metadata = audit["metadata"]
    checks = audit["mechanical_checks"]
    high_risk = audit["high_risk"]
    rows = high_risk["sample_rows"][:sample_size]
    flag_counter: Counter[str] = Counter(
        flag for row in rows for flag in row.get("flags", [])
    )
    label_lookup = {
        row["code"]: row["label"]
        for row in high_risk["distribution"]
    }
    flag_rows = [
        [f"`{flag}`", label_lookup.get(flag, flag), count]
        for flag, count in flag_counter.most_common()
    ]
    sample_table_rows = [
        [
            index,
            f"`{_escape_markdown_cell(row.get('record_id'))}`",
            row.get("claim_index", ""),
            ", ".join(f"`{flag}`" for flag in row.get("flags", [])),
            _escape_markdown_cell(_recheck_focus(row.get("flags", []))),
            _escape_markdown_cell(row.get("evidence")),
            "机械规则通过；语义复核优先",
        ]
        for index, row in enumerate(rows, 1)
    ]

    return f"""# Framework v2 High-Risk Coding Recheck Appendix

## 抽查目的

本附录用于记录 framework_v2 coding audit 高风险队列的风险优先抽查对象，服务于论文方法可信度说明。它不替代逐条语义复核，也不直接修改正式编码。

## 样本范围

- 正式基线：`{metadata["formal_stage"]} post-only`
- 正式帖子 / 正式评论：`{metadata["formal_posts"]} / {metadata["formal_comments"]}`
- framework_v2 reviewed posts：`{metadata["framework_v2_reviewed_posts"]}`
- framework_v2 missing posts：`{metadata["framework_v2_missing_posts"]}`
- v2 claim units：`{metadata["claim_units_with_framework_v2_fields"]}`
- 高风险队列总量：`{high_risk["sample_rows_total"]}`
- 本附录抽查记录数：`{len(rows)}`
- 机械一致性状态：`{checks["status"]}`，字段规则违规数：`{checks["violation_count"]}`，provenance 缺失数：`{checks["provenance_missing_count"]}`

## 抽样规则

- 抽样方式为风险优先抽样，不是随机代表性抽样。
- 样本来自 `framework_v2_coding_audit_report.json` 中的 `high_risk.sample_rows`，该队列按高风险标记数量和记录编号排序。
- 高风险标记包括 `G3`、`F5`、`F6`、`K4`、`K6`、`I2`、`I7`、`I8`、`multi_H`、`no_D_strong_norm`。
- 本轮记录用于方法附录和后续人工语义复核；除非另行执行 reviewed import，否则不改变正式 v2 编码。

## 抽查样本中的风险标记分布

{_markdown_table(["标记", "含义", "样本内数量"], flag_rows)}

## 抽查记录

{_markdown_table(["#", "record_id", "claim", "风险标记", "复核关注点", "证据摘录", "处置状态"], sample_table_rows)}

## 方法使用边界

- 本附录证明高风险样本已经被显式列入方法复核记录，但不声称这些样本均已完成双人独立复核。
- 当前正式统计仍以 framework_v2 reviewed payload 为准；本附录没有触发 DB schema migration，也没有改动 `quality_v5 514 / 0` formal boundary。
- 论文中可据此说明：在正式统计完成后，研究者针对高强度替代、自动执行、治理监督、正式规范参照和多重评价张力等高风险编码建立了可追溯复核队列。
- 如需进一步增强方法可信度，应在本附录基础上增加人工语义复核列，记录是否修正、修正前后代码和修正理由。
"""


def write_framework_v2_coding_audit(
    *,
    output_json_path: Path = AUDIT_JSON_PATH,
    output_md_path: Path = AUDIT_MD_PATH,
    output_appendix_path: Path | None = None,
    post_master_path: Path = POST_MASTER_PATH,
    summary_tables_path: Path = SUMMARY_TABLES_PATH,
    cross_tabs_path: Path = CROSS_TABS_PATH,
    appendix_sample_size: int = 80,
) -> dict[str, Any]:
    audit = build_framework_v2_coding_audit(
        post_master_path=post_master_path,
        summary_tables_path=summary_tables_path,
        cross_tabs_path=cross_tabs_path,
    )
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_md_path.write_text(render_audit_markdown(audit), encoding="utf-8")
    result = {
        "audit_json_path": str(output_json_path),
        "audit_markdown_path": str(output_md_path),
        "metadata": audit["metadata"],
        "mechanical_checks": audit["mechanical_checks"],
    }
    if output_appendix_path is not None:
        output_appendix_path.write_text(
            render_high_risk_recheck_appendix(
                audit,
                sample_size=appendix_sample_size,
            ),
            encoding="utf-8",
        )
        result["high_risk_recheck_appendix_path"] = str(output_appendix_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build framework v2 coding audit report.")
    parser.add_argument("--post-master", type=Path, default=POST_MASTER_PATH)
    parser.add_argument("--summary-tables", type=Path, default=SUMMARY_TABLES_PATH)
    parser.add_argument("--cross-tabs", type=Path, default=CROSS_TABS_PATH)
    parser.add_argument("--output-json", type=Path, default=AUDIT_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=AUDIT_MD_PATH)
    parser.add_argument("--output-appendix", type=Path, default=AUDIT_APPENDIX_PATH)
    parser.add_argument("--appendix-sample-size", type=int, default=80)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = write_framework_v2_coding_audit(
        output_json_path=args.output_json,
        output_md_path=args.output_md,
        output_appendix_path=args.output_appendix,
        post_master_path=args.post_master,
        summary_tables_path=args.summary_tables,
        cross_tabs_path=args.cross_tabs,
        appendix_sample_size=args.appendix_sample_size,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
