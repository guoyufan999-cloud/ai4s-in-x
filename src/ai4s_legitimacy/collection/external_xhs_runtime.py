from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

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


def _parse_doctor_output(output: str) -> DoctorStatus:
    daemon_running = "[OK] Daemon:" in output and "running on port" in output
    extension_connected = "[OK] Extension: connected" in output
    connectivity_ok = "[OK] Connectivity:" in output
    return DoctorStatus(
        daemon_running=daemon_running,
        extension_connected=extension_connected,
        connectivity_ok=connectivity_ok,
        raw_output=output,
    )


def _run_opencli(*args: str) -> subprocess.CompletedProcess[str]:
    command = ["opencli", *args]
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=OPENCLI_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout
            if isinstance(exc.stdout, str)
            else (exc.stdout or b"").decode("utf-8", "ignore")
        )
        stderr = (
            exc.stderr
            if isinstance(exc.stderr, str)
            else (exc.stderr or b"").decode("utf-8", "ignore")
        )
        if not stderr:
            stderr = f"opencli {' '.join(args)} timed out after {OPENCLI_TIMEOUT_SECONDS}s"
        return subprocess.CompletedProcess(
            args=command,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
        )


def check_opencli_prerequisite() -> DoctorStatus:
    process = _run_opencli("doctor", "--sessions")
    output = process.stdout or process.stderr
    return _parse_doctor_output(output)


def _search_with_opencli(query: PilotQuery, *, limit: int) -> list[SearchCandidate]:
    process = _run_opencli(
        "xiaohongshu",
        "search",
        query.query,
        "--limit",
        str(limit),
        "-f",
        "json",
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "opencli search failed")
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"opencli xiaohongshu search returned invalid JSON for {query.query!r}"
        ) from exc
    rows = payload if isinstance(payload, list) else []
    candidates: list[SearchCandidate] = []
    for row in rows:
        url = str(row.get("url") or "").strip()
        if "/explore/" not in url and "/search_result/" not in url:
            continue
        author, result_date = _parse_search_author_and_date(
            str(row.get("author") or ""),
            end_date=DEFAULT_END_DATE,
        )
        candidates.append(
            SearchCandidate(
                query_name=query.name,
                query_text=query.query,
                title=_normalize_space(str(row.get("title") or "")),
                url=_canonical_url(url),
                author=author,
                snippet="",
                source="opencli_xiaohongshu",
                result_date=result_date,
            )
        )
    return candidates


def _search_with_bing(query: PilotQuery, *, limit: int) -> list[SearchCandidate]:
    search_query = f"site:xiaohongshu.com/explore {query.query}"
    url = f"https://www.bing.com/search?q={quote(search_query)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html_text = urlopen(request, timeout=20, context=_build_ssl_context()).read().decode(
        "utf-8", "ignore"
    )

    # Prefer direct links in result blocks. If Bing only exposes redirect wrappers,
    # fall back to display-text fragments that still contain /explore/<id>.
    direct_urls = re.findall(
        r'href="(https://www\.xiaohongshu\.com/explore/[^"#?&<> ]+)"',
        html_text,
    )
    display_pairs = re.findall(
        r"<h2><a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a></h2>.*?<p>(.*?)</p>",
        html_text,
        flags=re.S,
    )

    seen: set[str] = set()
    candidates: list[SearchCandidate] = []
    for direct_url in direct_urls:
        canonical = _canonical_url(unquote(direct_url))
        if canonical in seen:
            continue
        seen.add(canonical)
        candidates.append(
            SearchCandidate(
                query_name=query.name,
                query_text=query.query,
                title="",
                url=canonical,
                author="",
                snippet="",
                source="bing_html",
            )
        )
        if len(candidates) >= limit:
            return candidates

    for raw_url, raw_title, raw_snippet in display_pairs:
        if "xiaohongshu.com" not in raw_url and "xiaohongshu.com" not in raw_snippet:
            continue
        decoded_url = unquote(raw_url)
        match = re.search(r"https?://www\.xiaohongshu\.com/explore/[A-Za-z0-9]+", decoded_url)
        if not match:
            match = re.search(
                r"https?://www\.xiaohongshu\.com/explore/[A-Za-z0-9]+",
                unquote(raw_snippet),
            )
        if not match:
            continue
        canonical = _canonical_url(match.group(0))
        if canonical in seen:
            continue
        seen.add(canonical)
        candidates.append(
            SearchCandidate(
                query_name=query.name,
                query_text=query.query,
                title=_normalize_space(_strip_html(raw_title)),
                url=canonical,
                author="",
                snippet=_normalize_space(_strip_html(raw_snippet)),
                source="bing_html",
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def _strip_html(raw_html: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", raw_html or "")
    return html.unescape(_normalize_space(no_tags))


def _unescape_xhs_text(raw_value: str) -> str:
    return _normalize_space(
        html.unescape(raw_value or "")
        .replace("\\n", "\n")
        .replace("\\t", " ")
        .replace("\\/", "/")
        .replace('\\"', '"')
    )


def _extract_structured_note_fields(html_text: str, note_id: str) -> dict[str, str]:
    if not note_id:
        return {}

    fields: dict[str, str] = {}
    author_match = re.search(
        rf'"nickname":"([^"]+)".{{0,4000}}?"noteId":"{re.escape(note_id)}"',
        html_text,
        flags=re.S,
    )
    if author_match:
        fields["author_handle"] = _unescape_xhs_text(author_match.group(1))

    section_match = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,8000}}?"desc":"([^"]*)".{{0,2000}}?"time":(\d{{10,13}}).{{0,2000}}?"title":"([^"]*)"',
        html_text,
        flags=re.S,
    )
    if section_match:
        fields["desc"] = _unescape_xhs_text(section_match.group(1))
        fields["created_at"] = _normalize_timestamp(section_match.group(2))
        fields["title"] = _unescape_xhs_text(section_match.group(3))
        return fields

    fallback_title = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"title":"([^"]+)"',
        html_text,
        flags=re.S,
    )
    if fallback_title:
        fields["title"] = _unescape_xhs_text(fallback_title.group(1))

    fallback_desc = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"desc":"([^"]*)"',
        html_text,
        flags=re.S,
    )
    if fallback_desc:
        fields["desc"] = _unescape_xhs_text(fallback_desc.group(1))

    fallback_time = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"time":(\d{{10,13}})',
        html_text,
        flags=re.S,
    )
    if fallback_time:
        fields["created_at"] = _normalize_timestamp(fallback_time.group(1))

    return fields


def _fetch_public_note_direct(url: str) -> PagePayload | None:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.xiaohongshu.com/",
        },
    )
    with urlopen(request, timeout=25, context=_build_ssl_context()) as response:
        final_url = response.geturl()
        html_text = response.read().decode("utf-8", "ignore")

    if "error_code=300031" in final_url or "/404/sec_" in final_url:
        return None
    note_id = _extract_note_id(final_url or url)
    structured_fields = _extract_structured_note_fields(html_text, note_id)
    title = (
        structured_fields.get("title")
        or _extract_meta(html_text, "property", "og:title")
        or _extract_html_title(html_text)
    )
    description = _extract_meta(html_text, "name", "description") or _extract_meta(
        html_text, "property", "og:description"
    )
    author_handle = structured_fields.get("author_handle") or _extract_json_like_field(
        html_text,
        ("nickname", "userName", "author"),
    )
    created_at = structured_fields.get("created_at") or _extract_date(html_text)
    body_text = structured_fields.get("desc") or _extract_xhs_body_text(html_text)
    source_text = _normalize_space(body_text or description or "")
    if not source_text and not title:
        return None
    return PagePayload(
        url=_canonical_url(final_url or url),
        note_id=note_id,
        title=_normalize_space(title or ""),
        source_text=source_text,
        author_handle=_normalize_space(author_handle or ""),
        created_at=created_at,
        status="ok",
        fetched_via="direct_http",
        raw_excerpt=_normalize_space(structured_fields.get("desc") or description or source_text[:280]),
    )


def _extract_meta(html_text: str, attr_name: str, attr_value: str) -> str:
    patterns = (
        rf'<meta[^>]+{attr_name}="{re.escape(attr_value)}"[^>]+content="([^"]+)"',
        rf"<meta[^>]+{attr_name}='{re.escape(attr_value)}'[^>]+content='([^']+)'",
    )
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.I)
        if match:
            return html.unescape(match.group(1))
    return ""


def _extract_html_title(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, flags=re.I | re.S)
    return html.unescape(_normalize_space(match.group(1))) if match else ""


def _extract_json_like_field(html_text: str, field_names: tuple[str, ...]) -> str:
    for field_name in field_names:
        match = re.search(rf'"{re.escape(field_name)}"\s*:\s*"([^"]+)"', html_text)
        if match:
            return html.unescape(match.group(1))
    return ""


def _extract_date(html_text: str) -> str:
    patterns = (
        r'"publishTime"\s*:\s*"([^"]+)"',
        r'"time"\s*:\s*"(\d{4}-\d{2}-\d{2})',
        r"(\d{4}-\d{2}-\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, html_text)
        if not match:
            continue
        candidate = match.group(1)
        normalized = _normalize_date(candidate)
        if normalized:
            return normalized
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


def _extract_xhs_body_text(html_text: str) -> str:
    candidates: list[str] = []
    patterns = (
        r'"desc"\s*:\s*"([^"]{80,})"',
        r'"content"\s*:\s*"([^"]{80,})"',
        r'"noteDesc"\s*:\s*"([^"]{80,})"',
    )
    for pattern in patterns:
        candidates.extend(match.group(1) for match in re.finditer(pattern, html_text))
    cleaned = []
    for candidate in candidates:
        normalized = _unescape_xhs_text(candidate)
        if len(normalized) >= 80:
            cleaned.append(normalized)
    if cleaned:
        cleaned.sort(key=len, reverse=True)
        return cleaned[0]

    body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, flags=re.I | re.S)
    if not body_match:
        return ""
    body_text = _strip_html(body_match.group(1))
    return body_text if len(body_text) >= 120 else ""
