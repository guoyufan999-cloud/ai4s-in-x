from __future__ import annotations

import html
import re
from urllib.request import Request, urlopen

from .external_xhs_runtime_common import (
    PagePayload,
    _build_ssl_context,
    _canonical_url,
    _extract_note_id,
    _normalize_date,
    _normalize_space,
    _normalize_timestamp,
)


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
        flags=re.DOTALL,
    )
    if author_match:
        fields["author_handle"] = _unescape_xhs_text(author_match.group(1))

    section_match = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,8000}}?"desc":"([^"]*)".{{0,2000}}?"time":(\d{{10,13}}).{{0,2000}}?"title":"([^"]*)"',
        html_text,
        flags=re.DOTALL,
    )
    if section_match:
        fields["desc"] = _unescape_xhs_text(section_match.group(1))
        fields["created_at"] = _normalize_timestamp(section_match.group(2))
        fields["title"] = _unescape_xhs_text(section_match.group(3))
        return fields

    fallback_title = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"title":"([^"]+)"',
        html_text,
        flags=re.DOTALL,
    )
    if fallback_title:
        fields["title"] = _unescape_xhs_text(fallback_title.group(1))

    fallback_desc = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"desc":"([^"]*)"',
        html_text,
        flags=re.DOTALL,
    )
    if fallback_desc:
        fields["desc"] = _unescape_xhs_text(fallback_desc.group(1))

    fallback_time = re.search(
        rf'"noteId":"{re.escape(note_id)}".{{0,4000}}?"time":(\d{{10,13}})',
        html_text,
        flags=re.DOTALL,
    )
    if fallback_time:
        fields["created_at"] = _normalize_timestamp(fallback_time.group(1))

    return fields


def _extract_meta(html_text: str, attr_name: str, attr_value: str) -> str:
    patterns = (
        rf'<meta[^>]+{attr_name}="{re.escape(attr_value)}"[^>]+content="([^"]+)"',
        rf"<meta[^>]+{attr_name}='{re.escape(attr_value)}'[^>]+content='([^']+)'",
    )
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE)
        if match:
            return html.unescape(match.group(1))
    return ""


def _extract_html_title(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
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

    body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not body_match:
        return ""
    body_text = _strip_html(body_match.group(1))
    return body_text if len(body_text) >= 120 else ""


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
