from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ai4s_legitimacy.collection.external_xhs_coding import (
    CODER_VERSION as CODER_VERSION,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    TASK_BATCH_ID as TASK_BATCH_ID,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_basis_codes as _choose_basis_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_boundary_codes as _choose_boundary_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_boundary_mode_codes as _choose_boundary_mode_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_legitimacy as _choose_legitimacy,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _choose_workflow_codes as _choose_workflow_codes,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _collect_evidence as _collect_evidence,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _confidence as _confidence,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _decision_for_page as _decision_for_page,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _discursive_mode as _discursive_mode,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _format_decision_reason as _format_decision_reason,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _looks_like_generic_tool_roundup as _looks_like_generic_tool_roundup,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _make_claim_units as _make_claim_units,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _practice_status as _practice_status,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _review_points as _review_points,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _speaker_position as _speaker_position,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _target_practice_summary as _target_practice_summary,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    _theme_summary as _theme_summary,
)
from ai4s_legitimacy.collection.external_xhs_coding import (
    encode_page as encode_page,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    DEFAULT_END_DATE as DEFAULT_END_DATE,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    OPENCLI_TIMEOUT_SECONDS as OPENCLI_TIMEOUT_SECONDS,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    DoctorStatus as DoctorStatus,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    PagePayload as PagePayload,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    PilotQuery as PilotQuery,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    SearchCandidate as SearchCandidate,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _build_ssl_context as _build_ssl_context,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _canonical_url as _canonical_url,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _contains_any as _contains_any,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _dedupe_url_key as _dedupe_url_key,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_date as _extract_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_html_title as _extract_html_title,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_json_like_field as _extract_json_like_field,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_meta as _extract_meta,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_note_id as _extract_note_id,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_structured_note_fields as _extract_structured_note_fields,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _extract_xhs_body_text as _extract_xhs_body_text,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _fetch_public_note_direct as _fetch_public_note_direct,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _load_existing_post_urls as _load_existing_post_urls,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_date as _normalize_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_space as _normalize_space,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _normalize_timestamp as _normalize_timestamp,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _parse_doctor_output as _parse_doctor_output,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _parse_search_author_and_date as _parse_search_author_and_date,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _run_opencli as _run_opencli,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _search_with_bing as _search_with_bing,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _search_with_opencli as _search_with_opencli,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _sentence_for_keywords as _sentence_for_keywords,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _sha1 as _sha1,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _split_sentences as _split_sentences,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _strip_html as _strip_html,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    _unescape_xhs_text as _unescape_xhs_text,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    build_fixed_queries as build_fixed_queries,
)
from ai4s_legitimacy.collection.external_xhs_runtime import (
    check_opencli_prerequisite as check_opencli_prerequisite,
)
from ai4s_legitimacy.config.settings import LEGACY_QUERY_TEMPLATE, OUTPUTS_DIR, RESEARCH_DB_PATH

DEFAULT_OUTPUT_PATH = OUTPUTS_DIR / "tables" / "external_xhs_ai4s_2025plus_pilot100.jsonl"
DEFAULT_SUMMARY_PATH = (
    OUTPUTS_DIR / "reports" / "review_v2" / "external_xhs_ai4s_2025plus_pilot100.summary.json"
)
DEFAULT_START_DATE = date(2025, 1, 1)
DEFAULT_MAX_CODED = 100
DEFAULT_MIN_INCLUDED = 50
DEFAULT_MAX_VERIFIED = 140
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_PER_QUERY_CAP = 6
DEFAULT_PER_AUTHOR_CAP = 2
PUBLIC_PAGE_CHROME_MARKERS = (
    "创作中心 业务合作 发现 直播 发布 通知",
    "window.__INITIAL_STATE__",
    "window.__SSR__",
    "沪ICP备",
    "营业执照",
)


def _query_file_name(query_group: str, index: int) -> str:
    group_match = re.match(r"\s*([A-Za-z])", query_group or "")
    group = group_match.group(1).lower() if group_match else "x"
    return f"query_file_{group}_{index:02d}"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _decision_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "included": sum(1 for row in rows if row.get("decision") == "纳入"),
        "review_needed": sum(1 for row in rows if row.get("decision") == "待复核"),
        "excluded": sum(1 for row in rows if row.get("decision") == "剔除"),
    }


def _read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _artifact_classification(*, output_preserved: bool, new_row_count: int) -> dict[str, Any]:
    if output_preserved and new_row_count == 0:
        return {
            "status": "diagnostic_failed_run_preserved_output",
            "formal_evidence_chain": False,
            "quality_v5_formal_scope": False,
            "reason": (
                "This run harvested no new rows and preserved an existing non-empty JSONL; "
                "keep it for diagnostics only, not paper_scope_quality_v5 evidence."
            ),
        }
    return {
        "status": "external_pilot_exploratory",
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "External XHS pilot outputs are exploratory review_v2 artifacts and are not part "
            "of the quality_v5 post-only formal evidence chain."
        ),
    }


def _load_query_template_metadata() -> dict[str, Any]:
    if not LEGACY_QUERY_TEMPLATE.exists():
        return {}
    try:
        payload = json.loads(LEGACY_QUERY_TEMPLATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload.get("metadata", {})


def _strip_public_page_chrome(text: str) -> str:
    cleaned = str(text or "").strip()
    for marker in PUBLIC_PAGE_CHROME_MARKERS:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()
    for infix in (" - 小红书 ", "_小红书 "):
        cleaned = cleaned.replace(infix, " ")
    for suffix in (" - 小红书", "_小红书"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
    return cleaned


def _prepare_public_page(page: PagePayload) -> PagePayload:
    page.title = _strip_public_page_chrome(page.title)
    page.source_text = _strip_public_page_chrome(page.source_text)
    page.raw_excerpt = _strip_public_page_chrome(page.raw_excerpt)
    return page


def _load_queries_from_file(path: Path) -> tuple[dict[str, Any], list[PilotQuery]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_queries = payload.get("queries", [])
    if not isinstance(raw_queries, list):
        raise ValueError(f"query file must contain a list at queries: {path}")
    queries: list[PilotQuery] = []
    for index, item in enumerate(raw_queries, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"query file item {index} must be an object: {path}")
        query = str(item.get("query") or "").strip()
        if not query:
            raise ValueError(f"query file item {index} is missing query: {path}")
        query_group = str(item.get("query_group") or "query_file").strip()
        queries.append(
            PilotQuery(
                name=str(item.get("name") or _query_file_name(query_group, index)),
                query=query,
                category=query_group,
            )
        )
    return payload.get("metadata", {}), queries


def _classify_fetch_exception(exc: Exception) -> str:
    text = str(exc).lower()
    if any(marker in text for marker in ("403", "401", "login", "unauthorized", "forbidden", "sec_")):
        return "login_or_access_restricted"
    return "unavailable_or_fetch_failed"


def _empty_skip_counts() -> dict[str, int]:
    return {
        "duplicate_existing_db": 0,
        "duplicate_current_run": 0,
        "author_cap": 0,
        "fetch_unavailable": 0,
        "login_or_access_restricted": 0,
        "empty_body": 0,
        "date_out_of_range": 0,
        "duplicate_title": 0,
        "invalid_url": 0,
    }


def _add_skip(skip_counts: dict[str, int], query_skip_counts: dict[str, int], key: str) -> None:
    skip_counts[key] = skip_counts.get(key, 0) + 1
    query_skip_counts[key] = query_skip_counts.get(key, 0) + 1


def _candidate_status(run_label: str) -> str:
    return f"xhs_expansion_candidate_v1_{run_label}"


def _candidate_artifact_classification(
    query_file: Path | None,
    *,
    run_label: str,
) -> dict[str, Any]:
    if query_file is None:
        return _artifact_classification(output_preserved=False, new_row_count=1)
    status = _candidate_status(run_label)
    return {
        "status": status,
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "This row was harvested with a supplemental xhs_expansion_candidate_v1 query file. "
            "It is a candidate artifact and is not imported into quality_v5 formal results."
        ),
    }


def _run_artifact_classification(
    *,
    output_preserved: bool,
    new_row_count: int,
    query_file: Path | None,
    run_label: str,
) -> dict[str, Any]:
    if query_file is None:
        return _artifact_classification(
            output_preserved=output_preserved,
            new_row_count=new_row_count,
        )
    if output_preserved and new_row_count == 0:
        return {
            "status": f"{_candidate_status(run_label)}_diagnostic_failed_run_preserved_output",
            "formal_evidence_chain": False,
            "quality_v5_formal_scope": False,
            "reason": (
                "This supplemental run harvested no new rows and preserved an existing non-empty "
                "candidate JSONL; keep it for diagnostics only, not quality_v5 formal evidence."
            ),
        }
    return {
        "status": _candidate_status(run_label),
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "xhs_expansion_candidate_v1 outputs are supplemental candidate artifacts. "
            "They are not imported into quality_v5 post-only formal results."
        ),
    }


def _decorate_candidate_row(
    row: dict[str, Any],
    *,
    query_file: Path | None,
    run_label: str,
) -> dict[str, Any]:
    if query_file is None:
        return row
    decorated = dict(row)
    decorated["formal_result_scope"] = False
    decorated["quality_v5_formal_scope"] = False
    decorated["source_phase"] = _candidate_status(run_label)
    decorated["artifact_classification"] = _candidate_artifact_classification(
        query_file,
        run_label=run_label,
    )
    return decorated


def _skip_total(query_stat: dict[str, Any]) -> int:
    return sum(int(value or 0) for value in query_stat.get("skip_counts", {}).values())


def _query_retention(query_stat: dict[str, Any]) -> float:
    hits = int(query_stat.get("search_hits") or 0)
    if hits <= 0:
        return 0.0
    return int(query_stat.get("verified_kept") or 0) / hits


def _query_stat_map(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("query") or ""): item for item in summary.get("query_stats", [])}


def _format_query_list(items: list[dict[str, Any]], *, limit: int = 8) -> list[str]:
    lines: list[str] = []
    for item in items[:limit]:
        lines.append(
            "- `{query}`：verified_kept={kept}, search_hits={hits}, skipped={skips}".format(
                query=item.get("query", ""),
                kept=item.get("verified_kept", 0),
                hits=item.get("search_hits", 0),
                skips=_skip_total(item),
            )
        )
    return lines or ["- 暂无。"]


def _better_queries(
    summary: dict[str, Any],
    comparison_summary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    current = _query_stat_map(summary)
    if not comparison_summary:
        return sorted(
            current.values(),
            key=lambda item: (int(item.get("verified_kept") or 0), _query_retention(item)),
            reverse=True,
        )
    previous = _query_stat_map(comparison_summary)
    improved = []
    for query, item in current.items():
        previous_kept = int(previous.get(query, {}).get("verified_kept") or 0)
        kept = int(item.get("verified_kept") or 0)
        if kept > previous_kept:
            enriched = dict(item)
            enriched["pilot_delta"] = kept - previous_kept
            improved.append(enriched)
    return sorted(
        improved,
        key=lambda item: (int(item.get("pilot_delta") or 0), int(item.get("verified_kept") or 0)),
        reverse=True,
    )


def _noisy_queries(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        summary.get("query_stats", []),
        key=lambda item: (_skip_total(item), -int(item.get("verified_kept") or 0)),
        reverse=True,
    )


def _downweight_queries(summary: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for item in summary.get("query_stats", []):
        hits = int(item.get("search_hits") or 0)
        kept = int(item.get("verified_kept") or 0)
        skips = _skip_total(item)
        retention = _query_retention(item)
        if hits > 0 and (kept == 0 or (retention < 0.25 and skips >= 5)):
            candidates.append(item)
    return sorted(candidates, key=lambda item: (int(item.get("verified_kept") or 0), -_skip_total(item)))


def _contains_theme(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _theme_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    themes = {
        "AI文献阅读": ("文献阅读", "读文献", "文献综述", "总结论文", "论文阅读", "翻译文献"),
        "AI论文写作": ("写论文", "论文写作", "论文润色", "论文修改", "论文初稿", "论文摘要", "投稿信", "sci"),
        "AI数据分析": ("数据分析", "统计分析", "辅助建模", "结果解释", "科研代码", "写代码"),
        "AI科研训练": ("研究生", "博士", "硕士", "科研入门", "方法学习", "科研效率", "学术阅读"),
        "AI使用披露": ("披露", "声明", "使用披露", "透明", "标注"),
        "AI学术诚信": ("学术不端", "代写", "查重", "诚信", "原创性", "瞎编"),
        "AI审稿或AI检测": ("审稿", "检测", "ai率", "生成内容检测", "aigc检测"),
    }
    counts = dict.fromkeys(themes, 0)
    for row in rows:
        text = " ".join(
            str(row.get(key) or "")
            for key in ("source_text", "theme_summary", "target_practice_summary")
        )
        for theme, terms in themes.items():
            if _contains_theme(text, terms):
                counts[theme] += 1
    return counts


def _discourse_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    patterns = {
        "工具推荐": ("工具", "推荐", "宝藏", "网站", "清单", "指令", "提示词"),
        "经验分享": ("我用", "经验", "分享", "教程", "方法", "流程", "实测"),
        "风险提醒": ("风险", "幻觉", "瞎编", "不端", "检测", "查重", "警惕", "不能直接"),
        "规范讨论": ("披露", "规范", "诚信", "责任", "伦理", "政策", "规则", "学术不端"),
        "评论争论": ("评论区", "争议", "质疑", "吵", "怎么看", "合理吗"),
    }
    counts = dict.fromkeys(patterns, 0)
    for row in rows:
        text = " ".join(str(row.get(key) or "") for key in ("source_text", "theme_summary"))
        for mode, terms in patterns.items():
            if _contains_theme(text, terms):
                counts[mode] += 1
    return counts


def _review_recommendation(summary: dict[str, Any]) -> str:
    row_count = int(summary.get("row_count") or 0)
    included = int(summary.get("included_count") or 0)
    review_needed = int(summary.get("review_needed_count") or 0)
    restricted = int(summary.get("skip_counts", {}).get("login_or_access_restricted") or 0)
    fallback = bool(summary.get("fallback_used"))
    useful_ratio = (included + review_needed) / row_count if row_count else 0.0
    if row_count >= 200 and useful_ratio >= 0.6 and restricted == 0 and not fallback:
        return "值得进入人工 review 队列；建议先抽查 50 条校准噪声类别，再分批 review。"
    if row_count >= 100 and useful_ratio >= 0.45:
        return "可以进入小规模人工 review 试队列，但应先降权高噪声查询词。"
    return "暂不建议进入正式人工 review 队列，应先调整查询词或访问策略。"


def _scale500_recommendation(summary: dict[str, Any]) -> str:
    row_count = int(summary.get("row_count") or 0)
    included = int(summary.get("included_count") or 0)
    restricted = int(summary.get("skip_counts", {}).get("login_or_access_restricted") or 0)
    fallback = bool(summary.get("fallback_used"))
    included_ratio = included / row_count if row_count else 0.0
    if row_count >= 250 and included_ratio >= 0.45 and restricted == 0 and not fallback:
        return "可以考虑扩大到 500 条，但应先完成 candidate300 的人工噪声抽查与去重审计。"
    return "不建议立即扩大到 500 条；应先复核 candidate300 的噪声率、主题覆盖和重复结构。"


def _load_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _render_pilot_report(
    summary: dict[str, Any],
    *,
    rows: list[dict[str, Any]] | None = None,
    comparison_summary: dict[str, Any] | None = None,
) -> str:
    decision_counts = {
        "纳入": summary.get("included_count", 0),
        "待复核": summary.get("review_needed_count", 0),
        "剔除": summary.get("excluded_count", 0),
    }
    skip_counts = summary.get("skip_counts", {})
    query_rows = []
    for item in summary.get("query_stats", []):
        query_rows.append(
            "| {query} | {category} | {hits} | {kept} | {skips} |".format(
                query=item.get("query", ""),
                category=item.get("category", ""),
                hits=item.get("search_hits", 0),
                kept=item.get("verified_kept", 0),
                skips=sum(int(value or 0) for value in item.get("skip_counts", {}).values()),
            )
        )
    if not query_rows:
        query_rows.append("| 无 | 无 | 0 | 0 | 0 |")

    included_count = int(summary.get("included_count", 0) or 0)
    row_count = int(summary.get("row_count", 0) or 0)
    fallback_used = bool(summary.get("fallback_used"))
    max_coded_target = int(summary.get("max_coded_target") or 0)
    run_label = Path(str(summary.get("output_path") or "pilot")).stem or "pilot"
    if max_coded_target >= 300:
        if row_count < max_coded_target:
            scale_recommendation = (
                f"本轮未达到 `{max_coded_target}` 条目标，实际获得 `{row_count}` 条；"
                "瓶颈主要来自重复、日期过滤和部分查询词命中耗尽。"
            )
        else:
            scale_recommendation = "本轮已达到 candidate 扩展目标，下一步应先做人工抽查而不是继续扩量。"
    elif row_count >= 50 and included_count >= 20 and not fallback_used:
        scale_recommendation = "建议下一轮扩大到 200 条；暂不直接跳到 300 条，先复核噪声率与重复率。"
    elif row_count >= 30 and included_count >= 10:
        scale_recommendation = "可先扩大到 200 条，但应同步抽查剔除原因和广告噪声。"
    else:
        scale_recommendation = "暂不建议扩大到 200 或 300 条；应先调整查询词和公开访问策略。"
    rows = rows or []
    better_queries = _better_queries(summary, comparison_summary)
    noisy_queries = _noisy_queries(summary)
    downweight_queries = _downweight_queries(summary)
    theme_counts = _theme_counts(rows)
    discourse_counts = _discourse_counts(rows)
    if comparison_summary:
        comparison_note = (
            f"对比基线：`{comparison_summary.get('output_path', 'comparison summary')}`；"
            f"pilot row_count={comparison_summary.get('row_count', 0)}, "
            f"included={comparison_summary.get('included_count', 0)}。"
        )
    else:
        comparison_note = "未提供对比 summary；以下按本轮 verified_kept 和跳过结构排序。"

    lines = [
        f"# xhs_expansion_candidate_v1 {run_label} 采集报告",
        "",
        "本报告只描述小红书补充样本候选集 `xhs_expansion_candidate_v1` 的试采集过程，不构成论文发现，不写入 `quality_v5` formal baseline，也不写入正式研究主库。",
        "",
        "## 1. 查询词使用",
        "",
        f"- 载入查询词数量：`{summary.get('query_count', 0)}`",
        f"- 实际执行检索的查询词数量：`{summary.get('executed_query_count', 0)}`",
        f"- 查询来源：`{summary.get('query_source', 'fixed')}`",
        f"- 查询词文件：`{summary.get('query_file_path') or '未使用'}`",
        "",
        "## 2. 每个查询词搜索命中",
        "",
        "| query | query_group/category | search_hits | verified_kept | skipped |",
        "| --- | --- | ---: | ---: | ---: |",
        *query_rows,
        "",
        "## 3. 验证与编码结果",
        "",
        f"- 成功验证的公开帖子数量：`{summary.get('row_count', 0)}`",
        f"- 目标候选数量：`{summary.get('max_coded_target', 0)}`",
        f"- 纳入 / 待复核 / 剔除：`{decision_counts['纳入']} / {decision_counts['待复核']} / {decision_counts['剔除']}`",
        f"- 与现有 `data/processed/ai4s_legitimacy.sqlite3` 的重复数量：`{skip_counts.get('duplicate_existing_db', 0)}`",
        "",
        "## 4. 跳过原因",
        "",
        f"- 不可访问或抓取失败：`{skip_counts.get('fetch_unavailable', 0)}`",
        f"- 登录限制或访问受限：`{skip_counts.get('login_or_access_restricted', 0)}`",
        f"- 无正文：`{skip_counts.get('empty_body', 0)}`",
        f"- 日期不符合：`{skip_counts.get('date_out_of_range', 0)}`",
        f"- 当前轮重复：`{skip_counts.get('duplicate_current_run', 0)}`",
        f"- 作者上限过滤：`{skip_counts.get('author_cap', 0)}`",
        f"- 标题/正文近似重复：`{skip_counts.get('duplicate_title', 0)}`",
        f"- 无效 URL：`{skip_counts.get('invalid_url', 0)}`",
        "",
        "## 5. fallback 状态",
        "",
        f"- 是否触发 fallback：`{str(fallback_used).lower()}`",
        f"- 实际 provider：`{summary.get('provider_used', '')}`",
        "",
        "## 6. 合规风险说明",
        "",
        "- 本轮只处理公开可访问帖子材料，不绕过登录、验证码、风控、限流或封禁机制。",
        "- 不使用私信、封闭群组、非公开主页或受限内容。",
        "- 不保存浏览器 cookie、本地登录态或可识别个人身份信息。",
        "- 输出是 candidate / supplemental，不进入 `quality_v5` 正式结果。",
        "",
        "## 7. 下一步建议",
        "",
        f"- {scale_recommendation}",
        f"- 是否值得进入人工 review 队列：{_review_recommendation(summary)}",
        f"- 是否建议继续扩大到 500 条：{_scale500_recommendation(summary)}",
        "",
        "## 8. 查询词表现与 pilot 对比",
        "",
        comparison_note,
        "",
        "表现更好的查询词：",
        *_format_query_list(better_queries),
        "",
        "带来较多噪声或重复的查询词：",
        *_format_query_list(noisy_queries),
        "",
        "建议降权或删除的查询词：",
        *_format_query_list(downweight_queries),
        "",
        "## 9. 主题覆盖",
        "",
        *[f"- {theme}：`{count}`" for theme, count in theme_counts.items()],
        "",
        "## 10. 话语类型初步判断",
        "",
        *[f"- {mode}：`{count}`" for mode, count in discourse_counts.items()],
        "",
        "说明：上述主题和话语类型只用于候选集采集质量评估，不是论文发现；正式解释仍需人工 review。",
    ]
    return "\n".join(lines) + "\n"


def run_external_xhs_pilot(
    *,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    db_path: Path = RESEARCH_DB_PATH,
    max_coded: int = DEFAULT_MAX_CODED,
    min_included: int = DEFAULT_MIN_INCLUDED,
    max_verified: int = DEFAULT_MAX_VERIFIED,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
    per_query_cap: int = DEFAULT_PER_QUERY_CAP,
    per_author_cap: int = DEFAULT_PER_AUTHOR_CAP,
    start_date: date = DEFAULT_START_DATE,
    end_date: date = DEFAULT_END_DATE,
    max_queries: int | None = None,
    query_file: Path | None = None,
    report_path: Path | None = None,
    comparison_summary_path: Path | None = None,
) -> tuple[Path, Path]:
    doctor_status = check_opencli_prerequisite()
    query_source = "query_file" if query_file is not None else "fixed"
    if query_file is not None:
        query_template_metadata, queries = _load_queries_from_file(query_file)
    else:
        query_template_metadata = _load_query_template_metadata()
        queries = build_fixed_queries()
    if max_queries is not None:
        queries = queries[: max(0, int(max_queries))]
    run_label = output_path.stem if query_file is not None else "external_pilot"
    existing_urls = _load_existing_post_urls(db_path)

    provider_name = "opencli_xiaohongshu" if doctor_status.extension_connected else "bing_fallback"
    candidates_seen: set[str] = set()
    title_hash_seen: set[str] = set()
    author_counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    query_stats: list[dict[str, Any]] = []
    skip_counts = _empty_skip_counts()
    verified_count = 0
    included_count = 0

    for query in queries:
        if len(rows) >= max_coded and included_count >= min_included:
            break
        if verified_count >= max_verified:
            break

        if doctor_status.extension_connected:
            try:
                search_results = _search_with_opencli(query, limit=search_limit)
            except Exception as exc:  # pragma: no cover - runtime integration branch
                search_results = []
                query_stats.append(
                    {
                        "query": query.query,
                        "query_name": query.name,
                        "category": query.category,
                        "search_provider": provider_name,
                        "status": "search_failed",
                        "error": str(exc),
                        "search_hits": 0,
                        "verified_kept": 0,
                        "skip_counts": _empty_skip_counts(),
                    }
                )
                continue
        else:
            try:
                search_results = _search_with_bing(query, limit=search_limit)
            except Exception as exc:
                search_results = []
                query_stats.append(
                    {
                        "query": query.query,
                        "query_name": query.name,
                        "category": query.category,
                        "search_provider": provider_name,
                        "status": "search_failed",
                        "error": str(exc),
                        "search_hits": 0,
                        "verified_kept": 0,
                        "skip_counts": _empty_skip_counts(),
                    }
                )
                continue

        retained_this_query = 0
        verified_this_query = 0
        query_skip_counts = _empty_skip_counts()
        for candidate in search_results:
            if retained_this_query >= per_query_cap:
                break
            if len(rows) >= max_coded and included_count >= min_included:
                break
            if verified_count >= max_verified:
                break
            fetch_url = _canonical_url(candidate.url)
            dedupe_key = _dedupe_url_key(fetch_url)
            if not fetch_url:
                _add_skip(skip_counts, query_skip_counts, "invalid_url")
                continue
            if dedupe_key in existing_urls:
                _add_skip(skip_counts, query_skip_counts, "duplicate_existing_db")
                continue
            if dedupe_key in candidates_seen:
                _add_skip(skip_counts, query_skip_counts, "duplicate_current_run")
                continue
            author_key = _sha1(candidate.author) if candidate.author else ""
            if author_key and author_counts.get(author_key, 0) >= per_author_cap:
                _add_skip(skip_counts, query_skip_counts, "author_cap")
                continue

            fetch_skip_key = ""
            try:
                page = _fetch_public_note_direct(fetch_url)
            except Exception as exc:
                fetch_skip_key = _classify_fetch_exception(exc)
                _add_skip(skip_counts, query_skip_counts, fetch_skip_key)
                page = None
            if page is None:
                if not fetch_skip_key:
                    _add_skip(skip_counts, query_skip_counts, "fetch_unavailable")
                continue
            page = _prepare_public_page(page)
            if not _normalize_space(page.source_text):
                _add_skip(skip_counts, query_skip_counts, "empty_body")
                continue
            if (not page.title or page.title.startswith("小红书_")) and candidate.title:
                page.title = candidate.title
            if not page.author_handle and candidate.author:
                page.author_handle = candidate.author
            if not page.created_at and candidate.result_date:
                page.created_at = candidate.result_date
            if page.created_at:
                try:
                    created_date = datetime.strptime(page.created_at, "%Y-%m-%d").date()
                    if created_date < start_date or created_date > end_date:
                        _add_skip(skip_counts, query_skip_counts, "date_out_of_range")
                        continue
                except ValueError:
                    pass
            title_hash = _sha1(f"{page.title}\n{page.source_text[:200]}")
            if title_hash in title_hash_seen:
                _add_skip(skip_counts, query_skip_counts, "duplicate_title")
                continue

            row = _decorate_candidate_row(
                encode_page(page=page, candidate=candidate, end_date=end_date),
                query_file=query_file,
                run_label=run_label,
            )
            if query_file is not None:
                row["query"] = query.query
                row["query_group"] = query.category
                row["query_name"] = query.name
                row["source_method"] = provider_name
            rows.append(row)
            candidates_seen.add(dedupe_key)
            title_hash_seen.add(title_hash)
            verified_count += 1
            verified_this_query += 1
            retained_this_query += 1
            if row["decision"] == "纳入":
                included_count += 1
            if author_key:
                author_counts[author_key] = author_counts.get(author_key, 0) + 1

        query_stats.append(
            {
                "query": query.query,
                "query_name": query.name,
                "category": query.category,
                "search_provider": provider_name,
                "search_hits": len(search_results),
                "verified_kept": verified_this_query,
                "skip_counts": query_skip_counts,
            }
        )

    rows.sort(key=lambda item: (item["created_at"] or "9999-99-99", item["post_id"]))
    output_preserved = False
    output_rows = rows
    if rows or not output_path.exists() or output_path.stat().st_size == 0:
        _write_jsonl(output_path, rows)
    else:
        output_preserved = True
        output_rows = _read_jsonl_rows(output_path)
    output_row_count = len(output_rows)
    row_decision_counts = _decision_counts(rows)
    output_decision_counts = _decision_counts(output_rows)

    summary = {
        "task_batch_id": TASK_BATCH_ID,
        "coder_version": CODER_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "opencli_doctor": {
            "daemon_running": doctor_status.daemon_running,
            "extension_connected": doctor_status.extension_connected,
            "connectivity_ok": doctor_status.connectivity_ok,
            "raw_output": doctor_status.raw_output,
        },
        "provider_used": provider_name,
        "fallback_used": not doctor_status.extension_connected,
        "query_source": query_source,
        "query_file_path": str(query_file) if query_file is not None else "",
        "comparison_summary_path": (
            str(comparison_summary_path) if comparison_summary_path is not None else ""
        ),
        "query_template_metadata": query_template_metadata,
        "query_count": len(queries),
        "executed_query_count": len(query_stats),
        "max_coded_target": max_coded,
        "min_included_target": min_included,
        "max_verified_limit": max_verified,
        "row_count": len(rows),
        "output_row_count": output_row_count,
        "included_count": included_count,
        "review_needed_count": row_decision_counts["review_needed"],
        "excluded_count": row_decision_counts["excluded"],
        "output_included_count": output_decision_counts["included"],
        "output_review_needed_count": output_decision_counts["review_needed"],
        "output_excluded_count": output_decision_counts["excluded"],
        "query_stats": query_stats,
        "skip_counts": skip_counts,
        "duplicate_existing_db_count": skip_counts["duplicate_existing_db"],
        "formal_result_scope": False,
        "quality_v5_formal_scope": False,
        "limitations": (
            [
                "OpenCLI Browser Bridge was not connected; the run fell back to Bing discovery plus direct public-note fetch.",
            ]
            if not doctor_status.extension_connected
            else []
        ),
        "artifact_classification": _run_artifact_classification(
            output_preserved=output_preserved,
            new_row_count=len(rows),
            query_file=query_file,
            run_label=run_label,
        ),
        "output_preserved": output_preserved,
        "output_path": str(output_path),
        "report_path": str(report_path) if report_path is not None else "",
    }
    if output_preserved:
        summary["preserved_existing_row_count"] = output_row_count
        summary["preserved_existing_decision_counts"] = output_decision_counts
        summary["limitations"].append(
            "No rows were harvested in this run; existing non-empty JSONL output was preserved."
        )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _render_pilot_report(
                summary,
                rows=output_rows,
                comparison_summary=_load_summary(comparison_summary_path),
            ),
            encoding="utf-8",
        )
    return output_path, summary_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Harvest and code a strict JSONL pilot corpus for external Xiaohongshu AI4S posts."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--db", type=Path, default=RESEARCH_DB_PATH)
    parser.add_argument("--max-coded", type=int, default=DEFAULT_MAX_CODED)
    parser.add_argument("--min-included", type=int, default=DEFAULT_MIN_INCLUDED)
    parser.add_argument("--max-verified", type=int, default=DEFAULT_MAX_VERIFIED)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--per-query-cap", type=int, default=DEFAULT_PER_QUERY_CAP)
    parser.add_argument("--per-author-cap", type=int, default=DEFAULT_PER_AUTHOR_CAP)
    parser.add_argument("--start-date", type=str, default=str(DEFAULT_START_DATE))
    parser.add_argument("--end-date", type=str, default=str(DEFAULT_END_DATE))
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--query-file", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--comparison-summary", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    output_path, summary_path = run_external_xhs_pilot(
        output_path=args.output,
        summary_path=args.summary,
        db_path=args.db,
        max_coded=args.max_coded,
        min_included=args.min_included,
        max_verified=args.max_verified,
        search_limit=args.search_limit,
        per_query_cap=args.per_query_cap,
        per_author_cap=args.per_author_cap,
        start_date=start_date,
        end_date=end_date,
        max_queries=args.max_queries,
        query_file=args.query_file,
        report_path=args.report,
        comparison_summary_path=args.comparison_summary,
    )
    print(output_path)
    print(summary_path, file=sys.stderr)


if __name__ == "__main__":
    main()
