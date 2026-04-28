from __future__ import annotations

import hashlib
import re
import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import certifi

from ai4s_legitimacy.utils.db import connect_sqlite_readonly

DEFAULT_END_DATE = date(2026, 4, 21)
OPENCLI_TIMEOUT_SECONDS = 45


@dataclass(frozen=True)
class PilotQuery:
    name: str
    query: str
    category: str


@dataclass(frozen=True)
class SearchCandidate:
    query_name: str
    query_text: str
    title: str
    url: str
    author: str
    snippet: str
    source: str
    result_date: str = ""


@dataclass
class PagePayload:
    url: str
    note_id: str
    title: str
    source_text: str
    author_handle: str
    created_at: str
    status: str
    fetched_via: str
    raw_excerpt: str = ""


@dataclass(frozen=True)
class DoctorStatus:
    daemon_running: bool
    extension_connected: bool
    connectivity_ok: bool
    raw_output: str


def _build_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _canonical_url(url: str) -> str:
    stripped = (url or "").strip()
    if not stripped:
        return ""
    parsed = urlparse(stripped)
    path = parsed.path.rstrip("/")
    query = ""
    if (
        "xiaohongshu.com" in parsed.netloc
        and parsed.query
        and any(segment in path for segment in ("/explore/", "/search_result/"))
    ):
        query = f"?{parsed.query}"
    return f"{parsed.scheme}://{parsed.netloc}{path}{query}"


def _dedupe_url_key(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if "xiaohongshu.com" in parsed.netloc:
        return f"xiaohongshu:{_extract_note_id(url)}"
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _extract_note_id(url: str) -> str:
    for pattern in (r"/explore/([A-Za-z0-9]+)", r"/search_result/([A-Za-z0-9]+)"):
        match = re.search(pattern, url or "")
        if match:
            return match.group(1)
    return _sha1(url or "")[:16]


def _normalize_timestamp(raw_value: str) -> str:
    text = _normalize_space(raw_value)
    if not text.isdigit():
        return ""
    try:
        timestamp = int(text)
    except ValueError:
        return ""
    if timestamp > 10**12:
        timestamp //= 1000
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return ""


def _normalize_date(raw_value: str) -> str:
    text = _normalize_space(raw_value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return ""


def _parse_search_author_and_date(raw_author: str, *, end_date: date) -> tuple[str, str]:
    author = _normalize_space(raw_author)
    if not author:
        return "", ""

    full_match = re.search(r"(20\d{2}-\d{2}-\d{2})", author)
    if full_match:
        created_at = _normalize_date(full_match.group(1))
        cleaned = _normalize_space(author.replace(full_match.group(1), ""))
        return cleaned, created_at

    md_match = re.search(r"(?<!\d)(\d{2}-\d{2})$", author)
    if md_match:
        month, day = md_match.group(1).split("-")
        try:
            inferred = date(end_date.year, int(month), int(day))
            if inferred > end_date:
                inferred = date(end_date.year - 1, int(month), int(day))
            created_at = inferred.strftime("%Y-%m-%d")
        except ValueError:
            created_at = ""
        cleaned = _normalize_space(author[: md_match.start()])
        return cleaned, created_at

    return author, ""


def _split_sentences(text: str) -> list[str]:
    raw_parts = re.split(r"(?<=[。！？!?；;])|\n+", text)
    return [_normalize_space(part) for part in raw_parts if _normalize_space(part)]


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _sentence_for_keywords(text: str, keywords: Iterable[str]) -> str:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for sentence in _split_sentences(text):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            return sentence
    return ""


def _load_existing_post_urls(db_path: Path) -> set[str]:
    if not db_path.exists():
        return set()
    with connect_sqlite_readonly(db_path) as connection:
        rows = connection.execute(
            "SELECT post_url FROM posts WHERE post_url IS NOT NULL AND post_url != ''"
        ).fetchall()
    return {_dedupe_url_key(str(row["post_url"])) for row in rows if str(row["post_url"]).strip()}


def build_fixed_queries() -> list[PilotQuery]:
    return [
        PilotQuery("practice_ai_lit_review", "AI科研 文献综述", "practice"),
        PilotQuery("practice_ai_lit_search", "AI辅助科研 文献检索", "practice"),
        PilotQuery("practice_chatgpt_design", "ChatGPT 研究设计", "practice"),
        PilotQuery("practice_claude_analysis", "Claude 统计分析", "practice"),
        PilotQuery("practice_gemini_revision", "Gemini 回复审稿", "practice"),
        PilotQuery("practice_deepseek_review", "DeepSeek 文献综述", "practice"),
        PilotQuery("practice_cursor_code", "Cursor 代码生成 科研", "practice"),
        PilotQuery("practice_copilot_stats", "Copilot 统计分析", "practice"),
        PilotQuery("practice_perplexity_search", "Perplexity 文献检索", "practice"),
        PilotQuery("practice_elicit_review", "Elicit 文献综述", "practice"),
        PilotQuery("practice_notebooklm_group", "NotebookLM 组会", "practice"),
        PilotQuery("practice_scite_repro", "Scite 论文复现", "practice"),
        PilotQuery("boundary_ai_hallucination", "AI科研 文献综述 幻觉", "boundary"),
        PilotQuery("boundary_deepseek_fake_refs", "DeepSeek 文献综述 瞎编文献", "boundary"),
        PilotQuery("boundary_chatgpt_misconduct", "ChatGPT 论文写作 学术不端", "boundary"),
        PilotQuery("boundary_claude_review", "Claude 数据分析 人工审核", "boundary"),
        PilotQuery("boundary_ai_design_resp", "AI辅助科研 研究设计 责任", "boundary"),
        PilotQuery("boundary_ai_submission_disclose", "AI科研 投稿 披露", "boundary"),
        PilotQuery("boundary_cursor_not_replace", "Cursor 代码生成 不能替代", "boundary"),
        PilotQuery("boundary_copilot_ok", "Copilot 统计分析 可以吗", "boundary"),
        PilotQuery("salience_chatgpt_peer_review", "ChatGPT 审稿", "salience"),
        PilotQuery("salience_gemini_writing", "Gemini 写作", "salience"),
        PilotQuery("salience_cursor_repro", "Cursor 复现", "salience"),
        PilotQuery("salience_deepseek_review_risk", "DeepSeek 文献综述 幻觉", "salience"),
        PilotQuery("practice_claude_lit_review", "Claude 文献综述", "practice"),
        PilotQuery("practice_chatgpt_data_analysis", "ChatGPT 数据分析 科研", "practice"),
        PilotQuery("practice_deepseek_revision", "DeepSeek 回复审稿", "practice"),
        PilotQuery("practice_gemini_lit_search", "Gemini 文献检索", "practice"),
        PilotQuery("practice_perplexity_writing", "Perplexity 论文写作", "practice"),
        PilotQuery("boundary_ai_verification", "AI科研 结果验证 人工复核", "boundary"),
        PilotQuery("boundary_notebooklm_disclose", "NotebookLM 组会 披露", "boundary"),
        PilotQuery("boundary_scite_reliability", "Scite 复现 可靠性", "boundary"),
        PilotQuery("boundary_perplexity_fake_refs", "Perplexity 文献检索 幻觉", "boundary"),
        PilotQuery("salience_claude_peer_review", "Claude 审稿", "salience"),
        PilotQuery("salience_notebooklm_review", "NotebookLM 文献综述", "salience"),
        PilotQuery("salience_chatgpt_repro", "ChatGPT 复现", "salience"),
    ]
