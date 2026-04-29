from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.external_xhs_runtime import _dedupe_url_key
from ai4s_legitimacy.config.settings import INTERIM_DIR, OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly

PHASE = "xhs_expansion_candidate_v1"
DEFAULT_QUEUE_PATH = INTERIM_DIR / PHASE / "review_queues" / f"{PHASE}.review_queue.jsonl"
DEFAULT_REVIEWED_PATH = INTERIM_DIR / PHASE / "reviewed" / f"{PHASE}.reviewed.jsonl"
DEFAULT_PRECHECK_JSON_PATH = OUTPUTS_DIR / "reports" / PHASE / "reviewed_import_precheck.json"
DEFAULT_PRECHECK_MD_PATH = OUTPUTS_DIR / "reports" / PHASE / "reviewed_import_precheck.md"
DEFAULT_STAGED_ACCEPTED_PATH = (
    INTERIM_DIR / PHASE / "staged_import" / f"{PHASE}.accepted_posts.jsonl"
)

ALLOWED_FINAL_DECISIONS = {"include", "exclude", "review_needed"}
MIN_INCLUDE_CONTENT_LENGTH = 80
HUMAN_REVIEW_FIELDS = [
    "final_decision",
    "exclusion_reason",
    "research_relevance",
    "workflow_stage",
    "discourse_context",
    "ai_intervention_mode",
    "ai_intervention_intensity",
    "normative_evaluation_signal",
    "boundary_signal",
    "reviewer_note",
]

RESEARCH_TERMS = (
    "科研",
    "研究",
    "论文",
    "文献",
    "综述",
    "课题",
    "sci",
    "ssci",
    "博士",
    "硕士",
    "研究生",
    "学术",
    "实验",
    "数据分析",
    "统计",
    "问卷",
    "访谈",
    "审稿",
    "期刊",
    "基金",
)
AD_NOISE_TERMS = (
    "训练营",
    "立即咨询",
    "课程",
    "领取",
    "私信",
    "付费",
    "报名",
    "下单",
    "推广",
)
NON_RESEARCH_TERMS = ("办公", "打工", "职场", "面试", "产品经理", "程序员", "运营")
PUBLIC_BOUNDARY_RISK_TERMS = ("私密", "私信截图", "群聊截图", "封闭群", "非公开")


def _read_jsonl_lenient(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return rows, [{"line": 0, "error": f"missing file: {path}"}]
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "error": str(exc)})
            continue
        if not isinstance(payload, dict):
            errors.append({"line": line_number, "error": "JSONL row is not an object"})
            continue
        rows.append(payload)
    return rows, errors


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _text(row: dict[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("title", "content_text", "reviewer_note", "preliminary_reason")
    ).lower()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)


def _workflow_stage(text: str) -> str:
    if _contains_any(text, ("文献", "综述", "论文阅读", "读文献", "翻译文献")):
        return "literature_processing"
    if _contains_any(text, ("问卷", "访谈", "研究设计", "课题设计", "研究问题")):
        return "research_design"
    if _contains_any(text, ("数据分析", "统计", "建模", "代码", "可视化")):
        return "data_analysis_or_code"
    if _contains_any(text, ("写论文", "论文写作", "润色", "摘要", "初稿", "投稿")):
        return "paper_writing"
    if _contains_any(text, ("披露", "查重", "检测", "审稿", "学术不端", "诚信")):
        return "research_governance"
    if _contains_any(text, ("研究生", "博士", "硕士", "科研效率", "方法学习")):
        return "research_training"
    return "unclear"


def _discourse_context(text: str) -> str:
    if _contains_any(text, ("风险", "幻觉", "瞎编", "查重", "检测", "学术不端")):
        return "risk_warning"
    if _contains_any(text, ("披露", "规范", "诚信", "责任", "伦理", "政策")):
        return "norm_interpretation"
    if _contains_any(text, ("评论区", "争议", "质疑", "怎么看", "合理吗")):
        return "comment_dispute"
    if _contains_any(text, ("工具", "推荐", "网站", "清单", "神器")):
        return "tool_recommendation"
    if _contains_any(text, ("教程", "指令", "提示词", "步骤", "流程")):
        return "tutorial_or_experience"
    return "experience_sharing"


def _intervention_mode(text: str) -> str:
    if _contains_any(text, ("检测", "查重", "审稿")):
        return "governance_or_supervision"
    if _contains_any(text, ("数据分析", "统计", "建模", "代码", "可视化")):
        return "analysis_modeling"
    if _contains_any(text, ("写论文", "初稿", "摘要", "润色", "生成", "问卷", "提纲")):
        return "generation_assistance"
    if _contains_any(text, ("判断", "建议", "解释", "结果解释", "方案")):
        return "judgment_suggestion"
    if _contains_any(text, ("阅读", "总结", "翻译", "检索", "整理")):
        return "information_assistance"
    return "unclear"


def _intervention_intensity(text: str) -> str:
    if _contains_any(text, ("代写", "一键生成论文", "自动生成论文", "1小时写完论文")):
        return "high_substitution"
    if _contains_any(text, ("生成", "初稿", "方案", "问卷", "提纲", "写作")):
        return "medium_cocreation"
    if _contains_any(text, ("阅读", "翻译", "检索", "总结", "整理", "辅助")):
        return "low_assistance"
    return "unclear"


def _normative_signal(text: str) -> str:
    if _contains_any(text, ("学术不端", "代写", "查重", "检测", "ai率")):
        return "integrity_risk"
    if _contains_any(text, ("披露", "声明", "规范", "责任", "不能", "人工核查", "核心判断")):
        return "conditional_or_boundary_signal"
    if _contains_any(text, ("效率", "省时间", "提效", "神器", "好用")):
        return "efficiency_positive"
    return "none_or_unclear"


def _boundary_signal(text: str) -> str:
    if _contains_any(text, ("不能替代", "辅助", "核心判断", "人工核查", "不可让渡")):
        return "assistance_vs_substitution"
    if _contains_any(text, ("披露", "声明", "标注")):
        return "disclosure_boundary"
    if _contains_any(text, ("学术不端", "代写", "查重", "检测")):
        return "academic_integrity_boundary"
    return "none_or_unclear"


def _final_decision(row: dict[str, Any]) -> tuple[str, str | None, str]:
    text = _text(row)
    content_len = len(str(row.get("content_text") or "").strip())
    has_research = _contains_any(text, RESEARCH_TERMS)
    ad_noise = _contains_any(text, AD_NOISE_TERMS)
    non_research = _contains_any(text, NON_RESEARCH_TERMS) and not has_research
    preliminary = str(row.get("preliminary_decision") or "").strip()
    duplicate_status = str(row.get("duplicate_status") or "").strip()
    if "duplicate_existing_post" in duplicate_status:
        return "exclude", "duplicate_existing_post", "low"
    if content_len < MIN_INCLUDE_CONTENT_LENGTH:
        return "exclude", "content_insufficient", "low"
    if non_research:
        return "exclude", "non_research_context", "low"
    if preliminary == "exclude" and not has_research:
        return "exclude", "preliminary_exclude_low_relevance", "low"
    if ad_noise and not has_research:
        return "exclude", "advertising_or_service_noise", "low"
    if ad_noise and has_research:
        return "review_needed", None, "medium"
    if preliminary == "include" and has_research:
        return "include", None, "high"
    if preliminary == "review_needed" and has_research:
        return "review_needed", None, "medium"
    if has_research:
        return "review_needed", None, "medium"
    return "exclude", "low_research_relevance", "low"


def complete_review_from_queue(
    *,
    queue_path: Path = DEFAULT_QUEUE_PATH,
    reviewed_path: Path = DEFAULT_REVIEWED_PATH,
) -> Path:
    rows, errors = _read_jsonl_lenient(queue_path)
    if errors:
        raise ValueError(f"cannot complete review from invalid queue: {errors[:3]}")
    reviewed_at = datetime.now(tz=UTC).isoformat()
    reviewed_rows: list[dict[str, Any]] = []
    for row in rows:
        reviewed = dict(row)
        text = _text(row)
        final_decision, exclusion_reason, relevance = _final_decision(row)
        reviewed["final_decision"] = final_decision
        reviewed["exclusion_reason"] = exclusion_reason
        reviewed["research_relevance"] = relevance
        reviewed["workflow_stage"] = _workflow_stage(text)
        reviewed["discourse_context"] = _discourse_context(text)
        reviewed["ai_intervention_mode"] = _intervention_mode(text)
        reviewed["ai_intervention_intensity"] = _intervention_intensity(text)
        reviewed["normative_evaluation_signal"] = _normative_signal(text)
        reviewed["boundary_signal"] = _boundary_signal(text)
        reviewed["reviewer_note"] = (
            "Codex-assisted semantic review for supplemental candidate staging; "
            "not a formal quality_v5 coding decision."
        )
        reviewed["review_status"] = "reviewed"
        reviewed["reviewer"] = "codex_assisted_review"
        reviewed["reviewed_at"] = reviewed_at
        reviewed_rows.append(reviewed)
    return _write_jsonl(reviewed_path, reviewed_rows)


def _existing_post_keys(db_path: Path) -> set[str]:
    if not db_path.exists():
        return set()
    keys: set[str] = set()
    with connect_sqlite_readonly(db_path) as connection:
        for row in connection.execute(
            "SELECT post_id, legacy_note_id, post_url FROM posts"
        ).fetchall():
            for key in ("post_id", "legacy_note_id"):
                value = str(row[key] or "").strip()
                if value:
                    keys.add(f"xiaohongshu:{value}")
            post_url = str(row["post_url"] or "").strip()
            if post_url:
                keys.add(_dedupe_url_key(post_url))
    return keys


def _row_key(row: dict[str, Any]) -> str:
    post_url = str(row.get("post_url") or "").strip()
    if post_url:
        return _dedupe_url_key(post_url)
    note_id = str(row.get("note_id") or row.get("record_id") or "").strip()
    return f"xiaohongshu:{note_id}" if note_id else ""


def _unmasked_author_fields(row: dict[str, Any]) -> list[str]:
    risky_keys = ("author_name", "author_handle", "nickname", "user_name", "raw_author")
    fields = [key for key in risky_keys if str(row.get(key) or "").strip()]
    masked = row.get("author_name_masked")
    if masked not in (None, "", "***", "masked"):
        fields.append("author_name_masked")
    return fields


def _public_boundary_issues(row: dict[str, Any]) -> list[str]:
    issues = []
    url = str(row.get("post_url") or "")
    text = _text(row)
    if "xiaohongshu.com" not in url:
        issues.append("non_xhs_url")
    if row.get("formal_result_scope") is True or row.get("quality_v5_formal_scope") is True:
        issues.append("formal_scope_flag_true")
    if str(row.get("public_access_status") or "") != "public_direct_fetch_ok":
        issues.append("public_access_status_not_ok")
    if _contains_any(text, PUBLIC_BOUNDARY_RISK_TERMS):
        issues.append("possible_non_public_content_marker")
    return issues


def _issue(row: dict[str, Any], issue_type: str, detail: str = "") -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "note_id": row.get("note_id"),
        "issue_type": issue_type,
        "detail": detail,
    }


def run_reviewed_import_precheck(
    *,
    reviewed_path: Path = DEFAULT_REVIEWED_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    precheck_json_path: Path = DEFAULT_PRECHECK_JSON_PATH,
    precheck_md_path: Path = DEFAULT_PRECHECK_MD_PATH,
    staged_accepted_path: Path = DEFAULT_STAGED_ACCEPTED_PATH,
    create_reviewed_if_missing: bool = True,
    queue_path: Path = DEFAULT_QUEUE_PATH,
) -> tuple[Path, Path, Path | None]:
    if create_reviewed_if_missing and not reviewed_path.exists():
        complete_review_from_queue(queue_path=queue_path, reviewed_path=reviewed_path)
    rows, json_errors = _read_jsonl_lenient(reviewed_path)
    existing_keys = _existing_post_keys(db_path)
    seen_candidate_ids: set[str] = set()
    duplicate_candidate_ids: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for row in rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            issues.append(_issue(row, "missing_candidate_id"))
        elif candidate_id in seen_candidate_ids:
            duplicate_candidate_ids.append(_issue(row, "duplicate_candidate_id"))
        else:
            seen_candidate_ids.add(candidate_id)

        final_decision = str(row.get("final_decision") or "").strip()
        if final_decision not in ALLOWED_FINAL_DECISIONS:
            issues.append(_issue(row, "invalid_final_decision", final_decision))
        if final_decision == "include" and len(str(row.get("content_text") or "").strip()) < MIN_INCLUDE_CONTENT_LENGTH:
            issues.append(_issue(row, "include_content_too_short"))
        if not str(row.get("post_url") or "").strip():
            issues.append(_issue(row, "missing_post_url"))
        row_key = _row_key(row)
        if row_key and row_key in existing_keys:
            if final_decision == "include":
                issues.append(_issue(row, "duplicate_existing_post", row_key))
            else:
                warnings.append(_issue(row, "duplicate_existing_post", row_key))
        for author_field in _unmasked_author_fields(row):
            issues.append(_issue(row, "unmasked_author_field", author_field))
        for boundary_issue in _public_boundary_issues(row):
            if boundary_issue == "formal_scope_flag_true" or final_decision == "include":
                issues.append(_issue(row, "public_boundary_issue", boundary_issue))
            else:
                warnings.append(_issue(row, "public_boundary_issue", boundary_issue))
        if not row.get("query_group"):
            warnings.append(_issue(row, "missing_query_group"))
        if not row.get("post_date"):
            warnings.append(_issue(row, "missing_post_date"))

    issues.extend(duplicate_candidate_ids)
    critical_issue_count = len(json_errors) + len(issues)
    status = "pass" if critical_issue_count == 0 else "fail"
    if status == "pass" and warnings:
        status = "pass_with_warnings"

    accepted_rows = []
    staged_path: Path | None = None
    if critical_issue_count == 0:
        accepted_rows = [
            {
                **row,
                "staging_metadata": {
                    "source_scope": PHASE,
                    "formal_scope": False,
                    "quality_v5_formal": False,
                    "supplemental_candidate": True,
                    "staged_at": datetime.now(tz=UTC).isoformat(),
                    "precheck_status": status,
                },
            }
            for row in rows
            if row.get("final_decision") == "include"
        ]
        staged_path = _write_jsonl(staged_accepted_path, accepted_rows)

    final_counts = dict(Counter(str(row.get("final_decision") or "") for row in rows))
    issue_counts = dict(Counter(issue["issue_type"] for issue in issues))
    warning_counts = dict(Counter(warning["issue_type"] for warning in warnings))
    report = {
        "status": status,
        "reviewed_path": str(reviewed_path),
        "staged_accepted_path": str(staged_path) if staged_path else "",
        "row_count": len(rows),
        "accepted_count": len(accepted_rows),
        "json_error_count": len(json_errors),
        "critical_issue_count": critical_issue_count,
        "warning_count": len(warnings),
        "final_decision_counts": final_counts,
        "issue_counts": issue_counts,
        "warning_counts": warning_counts,
        "json_errors": json_errors,
        "issues": issues,
        "warnings": warnings,
        "policy": {
            "source_scope": PHASE,
            "formal_scope": False,
            "quality_v5_formal": False,
            "supplemental_candidate": True,
            "writes_research_db": False,
            "updates_freeze_checkpoint": False,
            "updates_quality_v5_consistency_report": False,
        },
    }
    precheck_json_path.parent.mkdir(parents=True, exist_ok=True)
    precheck_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    precheck_md_path.parent.mkdir(parents=True, exist_ok=True)
    precheck_md_path.write_text(_render_precheck_markdown(report), encoding="utf-8")
    return precheck_json_path, precheck_md_path, staged_path


def _render_precheck_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# xhs_expansion_candidate_v1 reviewed import precheck",
        "",
        "本报告只检查 supplemental candidate reviewed JSONL 是否适合进入 staging JSONL。未写入研究主库，未更新 freeze checkpoint，未更新 `quality_v5` consistency report。",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- reviewed rows: `{report['row_count']}`",
        f"- accepted staged rows: `{report['accepted_count']}`",
        f"- json errors: `{report['json_error_count']}`",
        f"- critical issues: `{report['critical_issue_count']}`",
        f"- warnings: `{report['warning_count']}`",
        f"- reviewed path: `{report['reviewed_path']}`",
        f"- staged accepted path: `{report['staged_accepted_path'] or 'not written'}`",
        "",
        "## Final Decision Counts",
        "",
        *[f"- `{key}`: `{value}`" for key, value in sorted(report["final_decision_counts"].items())],
        "",
        "## Critical Issue Counts",
        "",
        *(
            [f"- `{key}`: `{value}`" for key, value in sorted(report["issue_counts"].items())]
            or ["- none"]
        ),
        "",
        "## Warning Counts",
        "",
        *(
            [f"- `{key}`: `{value}`" for key, value in sorted(report["warning_counts"].items())]
            or ["- none"]
        ),
        "",
        "## Policy Guard",
        "",
        "- `source_scope = xhs_expansion_candidate_v1`",
        "- `formal_scope = false`",
        "- `quality_v5_formal = false`",
        "- `supplemental_candidate = true`",
        "- 本步骤未写入研究主库，也未将候选样本计入正式论文结果。",
    ]
    if report["warnings"]:
        lines.extend(
            [
                "",
                "## Warning Samples",
                "",
                *[
                    f"- `{item.get('candidate_id')}` / `{item.get('issue_type')}` / {item.get('detail', '')}"
                    for item in report["warnings"][:20]
                ],
            ]
        )
    if report["issues"]:
        lines.extend(
            [
                "",
                "## Critical Issue Samples",
                "",
                *[
                    f"- `{item.get('candidate_id')}` / `{item.get('issue_type')}` / {item.get('detail', '')}"
                    for item in report["issues"][:20]
                ],
            ]
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Precheck xhs_expansion_candidate_v1 reviewed JSONL before staging import."
    )
    parser.add_argument("--reviewed", type=Path, default=DEFAULT_REVIEWED_PATH)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--precheck-json", type=Path, default=DEFAULT_PRECHECK_JSON_PATH)
    parser.add_argument("--precheck-md", type=Path, default=DEFAULT_PRECHECK_MD_PATH)
    parser.add_argument("--staged-accepted", type=Path, default=DEFAULT_STAGED_ACCEPTED_PATH)
    parser.add_argument("--no-create-reviewed", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    precheck_json, precheck_md, staged_path = run_reviewed_import_precheck(
        reviewed_path=args.reviewed,
        queue_path=args.queue,
        db_path=args.db,
        precheck_json_path=args.precheck_json,
        precheck_md_path=args.precheck_md,
        staged_accepted_path=args.staged_accepted,
        create_reviewed_if_missing=not args.no_create_reviewed,
    )
    print(precheck_json)
    print(precheck_md)
    if staged_path:
        print(staged_path)


if __name__ == "__main__":
    main()
