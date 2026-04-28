from __future__ import annotations

import json
import re
import subprocess
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

from .external_xhs_runtime_common import (
    DEFAULT_END_DATE,
    OPENCLI_TIMEOUT_SECONDS,
    DoctorStatus,
    PilotQuery,
    SearchCandidate,
    _build_ssl_context,
    _canonical_url,
    _normalize_space,
    _parse_search_author_and_date,
)
from .external_xhs_runtime_html import _strip_html


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

    direct_urls = re.findall(
        r'href="(https://www\.xiaohongshu\.com/explore/[^"#?&<> ]+)"',
        html_text,
    )
    display_pairs = re.findall(
        r"<h2><a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a></h2>.*?<p>(.*?)</p>",
        html_text,
        flags=re.DOTALL,
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
