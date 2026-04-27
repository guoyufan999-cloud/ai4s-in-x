from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

import certifi

from ai4s_legitimacy.collection.canonical_schema import format_decision_reason
from ai4s_legitimacy.config.settings import LEGACY_QUERY_TEMPLATE, OUTPUTS_DIR, RESEARCH_DB_PATH
from ai4s_legitimacy.utils.db import connect_sqlite_readonly


TASK_BATCH_ID = "external_xhs_opencli_2025plus_pilot100_v1"
CODER_VERSION = "codex_ai4s_schema_v1"
DEFAULT_OUTPUT_PATH = OUTPUTS_DIR / "tables" / "external_xhs_ai4s_2025plus_pilot100.jsonl"
DEFAULT_SUMMARY_PATH = (
    OUTPUTS_DIR / "reports" / "review_v2" / "external_xhs_ai4s_2025plus_pilot100.summary.json"
)
DEFAULT_START_DATE = date(2025, 1, 1)
DEFAULT_END_DATE = date(2026, 4, 21)
DEFAULT_MAX_CODED = 100
DEFAULT_MIN_INCLUDED = 50
DEFAULT_MAX_VERIFIED = 140
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_PER_QUERY_CAP = 6
DEFAULT_PER_AUTHOR_CAP = 2
OPENCLI_TIMEOUT_SECONDS = 45

AI_CORE_TERMS = (
    "ai",
    "人工智能",
    "生成式ai",
    "大模型",
    "llm",
    "机器学习",
    "模型",
    "智能体",
    "chatgpt",
    "claude",
    "gemini",
    "copilot",
    "cursor",
    "elicit",
    "perplexity",
    "notebooklm",
    "scite",
    "alphafold",
    "deepseek",
    "kimi",
    "豆包",
    "通义",
    "元宝",
)
RESEARCH_STAGE_TERMS = (
    "科研",
    "研究",
    "课题",
    "论文",
    "审稿",
    "投稿",
    "返修",
    "文献",
    "综述",
    "实验",
    "数据",
    "复现",
    "基金申请",
    "组会",
    "开题",
    "学术",
)
STRONG_RESEARCH_PRACTICE_TERMS = (
    "文献检索",
    "查文献",
    "文献综述",
    "综述",
    "研究设计",
    "实验设计",
    "实验",
    "数据分析",
    "统计分析",
    "复现",
    "结果验证",
    "论文写作",
    "写论文",
    "投稿",
    "回复审稿",
    "审稿",
    "基金申请",
    "组会",
    "开题",
)
NON_RESEARCH_TERMS = (
    "面试",
    "求职",
    "产品经理",
    "运营",
    "副业",
    "带货",
    "电商",
    "办公",
    "作业",
    "考试",
    "课堂",
)
CONDITIONAL_TERMS = (
    "但",
    "但是",
    "前提",
    "只能",
    "需要",
    "必须",
    "先",
    "最终",
    "自己核查",
    "人工审核",
    "人工复核",
    "不能直接",
    "别直接",
)
POSITIVE_TERMS = (
    "提效",
    "效率高",
    "好用",
    "有帮助",
    "省时间",
    "有参考价值",
    "友好",
    "惊艳",
    "太香了",
    "值得用",
)
NEGATIVE_TERMS = (
    "学术不端",
    "不合适",
    "不可接受",
    "不敢",
    "风险",
    "越界",
    "胡说八道",
    "瞎编",
    "幻觉",
    "别再",
    "不能用",
    "不应该",
)
EVALUATIVE_QUESTION_TERMS = (
    "可以吗",
    "能不能",
    "靠谱吗",
    "合规吗",
)

WORKFLOW_PATTERNS: dict[str, tuple[str, ...]] = {
    "A1.1": ("选题", "研究问题", "创新点", "问题定义", "课题方向"),
    "A1.2": ("文献检索", "查文献", "文献综述", "综述", "读文献", "参考文献"),
    "A1.3": ("研究设计", "实验设计", "方案制定", "protocol", "方法设计", "基金申请"),
    "A1.4": ("数据获取", "数据采集", "爬虫", "抓取数据", "问卷发放", "收集数据"),
    "A1.5": ("实验实施", "跑实验", "仿真", "simulation", "agent跑"),
    "A1.6": ("数据清洗", "统计分析", "回归", "建模", "python", "r代码", "stata", "代码生成"),
    "A1.7": ("复现", "验证结果", "benchmark", "可重复", "复核结果"),
    "A1.8": ("结果解释", "机制解释", "理论提炼", "讨论结果", "解释回归"),
    "A1.9": ("论文写作", "写论文", "润色", "摘要", "学术写作", "海报", "汇报"),
    "A1.10": ("投稿", "返修", "回复审稿", "审稿回复", "答辩"),
    "A2.1": ("项目管理", "时间线", "任务看板", "进度管理"),
    "A2.2": ("组会", "协作", "沟通协调", "会议纪要", "团队同步"),
    "A2.3": ("算力", "订阅资源", "经费", "资源配置"),
    "A2.4": ("知识库", "数据治理", "文档库", "知识资产", "引用管理"),
    "A2.5": ("伦理", "合规", "诚信", "披露", "声明使用"),
    "A2.6": ("科研评价", "能力判断", "评价标准", "是否合格"),
    "A2.7": ("审稿人", "peer review", "期刊要求", "出版规则", "同行评议"),
    "A2.8": ("传播", "社会扩散", "成果转化"),
    "A3.1": ("科研入门", "研一", "新生", "学术适应"),
    "A3.2": ("研究方法学习", "方法学习", "因果推断", "方法训练"),
    "A3.3": ("学python", "学r", "工具训练", "技术技能", "科研工具"),
    "A3.4": ("学术阅读", "写作训练", "英文写作", "怎么读论文"),
    "A3.5": ("效率提升", "习惯养成", "workflow", "科研效率"),
}
WORKFLOW_DIMENSION = {
    "A1": "科研生产工作流",
    "A2": "科研治理工作流",
    "A3": "科研训练与能力建构",
}
STAGE_TO_DIMENSION = {code: code.split(".", 1)[0] for code in WORKFLOW_PATTERNS}

BASIS_PATTERNS: dict[str, tuple[str, ...]] = {
    "C1": ("提效", "省时间", "高效", "效率", "省事"),
    "C2": ("补充", "补位", "降低门槛", "辅助能力", "不会编程"),
    "C3": ("责任", "担责", "负责", "最后还是作者", "最终责任"),
    "C4": ("原创", "原创性", "自己的研究", "核心观点"),
    "C5": ("规范", "规则", "期刊要求", "共同体", "合规"),
    "C6": ("学术不端", "造假", "编文献", "虚构", "不端"),
    "C7": ("人机分工", "AI只能", "不能替代", "该由人做", "必须自己"),
    "C8": ("可靠", "可验证", "复验", "可核查", "不完全相信"),
    "C9": ("公平", "不公平", "资源差异"),
    "C10": ("训练价值", "能力养成", "学不到", "不能外包", "训练边界"),
    "C11": ("披露", "说明使用", "声明使用", "透明"),
    "C12": ("署名", "贡献归属", "作者贡献"),
    "C13": ("隐私", "知识产权", "合规风险", "数据安全"),
    "C14": ("专业判断", "领域知识", "专业门槛", "领域经验"),
}
BOUNDARY_CONTENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "D1.1": ("辅助", "替代", "代写", "代做", "不能替代"),
    "D1.2": ("人机分工", "该由人做", "AI只能", "必须自己"),
    "D1.3": ("责任", "作者负责", "导师负责", "最后还是人"),
    "D1.4": ("规范边界", "期刊要求", "合规", "规则"),
    "D1.5": ("诚信边界", "学术不端", "造假", "虚构"),
    "D1.6": ("训练边界", "训练价值", "不能外包", "学不到"),
    "D1.7": ("披露", "说明使用", "声明使用"),
    "D1.8": ("不同环节", "查文献可以", "结论不行", "分环节"),
    "D1.9": ("署名", "贡献归属"),
    "D1.10": ("核查", "复核", "验证", "人工审核"),
    "D1.11": ("隐私", "数据安全", "知识产权", "知识资产"),
}
BOUNDARY_MODE_PATTERNS: dict[str, tuple[str, ...]] = {
    "D2.1": ("可以用", "允许", "合理使用"),
    "D2.2": ("可以但", "前提", "条件", "只能"),
    "D2.3": ("限制", "别直接", "不要直接"),
    "D2.4": ("禁止", "不能用", "不允许"),
    "D2.5": ("人工审核", "自己核查", "人工复核", "必须核查"),
    "D2.6": ("最终责任", "作者负责", "责任在你"),
    "D2.7": ("披露", "说明使用", "声明使用"),
    "D2.8": ("高风险", "低风险", "按任务风险"),
    "D2.9": ("不同环节", "分环节", "查文献可以"),
    "D2.10": ("原创性", "结论", "核心观点"),
}


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
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "ignore")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "ignore")
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
        raise RuntimeError(f"opencli xiaohongshu search returned invalid JSON for {query.query!r}") from exc
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
    # fall back to the display-text fragments that still contain /explore/<id>.
    direct_urls = re.findall(r'href="(https://www\.xiaohongshu\.com/explore/[^"#?&<> ]+)"', html_text)
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
            match = re.search(r"https?://www\.xiaohongshu\.com/explore/[A-Za-z0-9]+", unquote(raw_snippet))
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
        r'(\d{4}-\d{2}-\d{2})',
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
    # Fall back to stripped body text if the page is server-rendered.
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, flags=re.I | re.S)
    if not body_match:
        return ""
    body_text = _strip_html(body_match.group(1))
    return body_text if len(body_text) >= 120 else ""


def _looks_like_generic_tool_roundup(text: str) -> bool:
    lowered = text.lower()
    marker_hits = sum(lowered.count(marker) for marker in (".com", "www.", "http", "⇢"))
    generic_hits = sum(text.count(marker) for marker in ("工具", "神器", "合集", "网站"))
    has_strong_research = _contains_any(text, STRONG_RESEARCH_PRACTICE_TERMS)
    return marker_hits + generic_hits >= 4 and not has_strong_research


def _format_decision_reason(code: str, note: str) -> list[str]:
    return format_decision_reason(code, note)


def _choose_workflow_codes(text: str) -> list[str]:
    lowered = text.lower()
    codes = [code for code, keywords in WORKFLOW_PATTERNS.items() if any(keyword.lower() in lowered for keyword in keywords)]
    if not codes:
        return []
    # Apply a few project-specific disambiguation rules conservatively.
    if "文献" in text and any(token in text for token in ("怎么读论文", "写作训练", "英文写作", "训练")):
        codes = [code for code in codes if code != "A1.2"]
        if "A3.4" not in codes:
            codes.append("A3.4")
    if "研究设计" in text and any(token in text for token in ("方法学习", "方法训练")):
        codes = [code for code in codes if code != "A1.3"]
        if "A3.2" not in codes:
            codes.append("A3.2")
    if any(token in text for token in ("审稿人", "期刊要求", "同行评议")) and "A2.7" not in codes:
        codes.append("A2.7")
    ordered = sorted(dict.fromkeys(codes))
    return ordered


def _choose_legitimacy(text: str) -> list[str]:
    has_positive = _contains_any(text, POSITIVE_TERMS)
    has_negative = _contains_any(text, NEGATIVE_TERMS)
    has_conditional = _contains_any(text, CONDITIONAL_TERMS)
    has_eval_question = _contains_any(text, EVALUATIVE_QUESTION_TERMS)
    if has_positive and has_negative:
        return ["B4"]
    if has_negative:
        return ["B3"]
    if has_conditional:
        return ["B2"]
    if has_positive:
        return ["B1"]
    if has_eval_question:
        return ["B5"]
    return ["B0"]


def _choose_basis_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code for code, keywords in BASIS_PATTERNS.items() if any(keyword.lower() in lowered for keyword in keywords)
    )


def _choose_boundary_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code
        for code, keywords in BOUNDARY_CONTENT_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    )


def _choose_boundary_mode_codes(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        code
        for code, keywords in BOUNDARY_MODE_PATTERNS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    )


def _discursive_mode(text: str) -> str:
    if "?" in text or "？" in text or any(token in text for token in ("请问", "求助")):
        return "question_help_seeking"
    if any(token in text for token in ("建议", "别再", "应该", "必须")):
        return "advice_guidance"
    if any(token in text for token in ("踩坑", "太香了", "亲测", "我用")):
        return "experience_share"
    if any(token in text for token in ("不合适", "学术不端", "风险")):
        return "criticism"
    if any(token in text for token in ("规定", "要求", "声明")):
        return "policy_statement"
    return "unclear"


def _practice_status(text: str) -> str:
    if any(token in text for token in ("我用", "用了", "我现在", "亲测", "实测")):
        return "actual_use"
    if any(token in text for token in ("打算", "准备", "想用")):
        return "intended_use"
    if any(token in text for token in ("如果", "假如", "能不能")):
        return "hypothetical_use"
    if any(token in text for token in ("规定", "要求", "声明", "期刊要求")):
        return "policy_or_rule"
    if any(token in text for token in ("看到", "听说", "吴恩达团队", "别人")):
        return "secondhand_report"
    return "unclear"


def _speaker_position(text: str) -> str:
    mapping = {
        "researcher": ("研究者", "科研人员"),
        "graduate_student": ("研究生", "博士生", "硕士"),
        "undergraduate": ("本科生", "本科科研"),
        "PI": ("导师",),
        "reviewer": ("审稿人",),
        "editor": ("编辑", "期刊编辑"),
        "institution_or_lab": ("实验室", "课题组", "学校"),
        "teacher_or_trainer": ("老师", "课程", "训练营"),
    }
    for code, keywords in mapping.items():
        if _contains_any(text, keywords):
            return code
    if re.search(r"(?<![A-Za-z])PI(?![A-Za-z])", text):
        return "PI"
    return "unclear"


def _theme_summary(title: str, workflow_codes: list[str], legitimacy_codes: list[str]) -> str:
    summary = _normalize_space(title)
    if summary:
        return summary[:120]
    if workflow_codes:
        return f"AI4S {workflow_codes[0]} 讨论"
    if legitimacy_codes and legitimacy_codes != ["B0"]:
        return f"AI科研实践 {legitimacy_codes[0]} 评价"
    return "AI科研相关帖子"


def _target_practice_summary(workflow_codes: list[str], boundary_codes: list[str]) -> str:
    if workflow_codes:
        return "; ".join(workflow_codes)
    if boundary_codes:
        return "; ".join(boundary_codes)
    return ""


def _make_claim_units(
    *,
    source_text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_codes: list[str],
    boundary_mode_codes: list[str],
) -> list[dict[str, Any]]:
    claim_units: list[dict[str, Any]] = []
    evidence_map: dict[str, str] = {}
    for code in workflow_codes:
        sentence = _sentence_for_keywords(source_text, WORKFLOW_PATTERNS[code])
        if sentence:
            evidence_map[code] = sentence
    if not evidence_map and workflow_codes:
        evidence_map[workflow_codes[0]] = _split_sentences(source_text)[0] if _split_sentences(source_text) else source_text[:160]
    for index, code in enumerate(workflow_codes or [""]):
        evidence = evidence_map.get(code, "")
        if not evidence:
            continue
        unit_basis = [
            {"code": basis, "evidence": _sentence_for_keywords(source_text, BASIS_PATTERNS[basis]) or evidence}
            for basis in basis_codes
        ]
        unit_boundary = [
            {
                "code": boundary,
                "evidence": _sentence_for_keywords(source_text, BOUNDARY_CONTENT_PATTERNS[boundary]) or evidence,
            }
            for boundary in boundary_codes
        ]
        unit_boundary_modes = [
            {
                "code": mode,
                "evidence": _sentence_for_keywords(source_text, BOUNDARY_MODE_PATTERNS[mode]) or evidence,
            }
            for mode in boundary_mode_codes
        ]
        claim_units.append(
            {
                "practice_unit": f"AI相关实践单元{index + 1}: {code}" if code else "AI相关实践单元",
                "workflow_stage_codes": [code] if code else [],
                "legitimacy_codes": legitimacy_codes,
                "basis_codes": unit_basis,
                "boundary_codes": unit_boundary,
                "boundary_mode_codes": unit_boundary_modes,
                "evidence": [evidence],
            }
        )
    return claim_units


def _collect_evidence(
    source_text: str,
    workflow_codes: list[str],
    legitimacy_codes: list[str],
    basis_codes: list[str],
    boundary_codes: list[str],
    boundary_mode_codes: list[str],
) -> dict[str, list[str]]:
    workflow_evidence = [
        _sentence_for_keywords(source_text, WORKFLOW_PATTERNS[code]) for code in workflow_codes
    ]
    workflow_evidence = [item for item in workflow_evidence if item]

    legitimacy_evidence: list[str] = []
    if legitimacy_codes != ["B0"]:
        for code in legitimacy_codes:
            if code == "B1":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, POSITIVE_TERMS))
            elif code == "B2":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, CONDITIONAL_TERMS))
            elif code == "B3":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, NEGATIVE_TERMS))
            elif code == "B4":
                legitimacy_evidence.append(
                    _sentence_for_keywords(source_text, POSITIVE_TERMS + NEGATIVE_TERMS)
                )
            elif code == "B5":
                legitimacy_evidence.append(_sentence_for_keywords(source_text, EVALUATIVE_QUESTION_TERMS))
    legitimacy_evidence = [item for item in legitimacy_evidence if item]

    basis_evidence = [
        _sentence_for_keywords(source_text, BASIS_PATTERNS[code]) for code in basis_codes
    ]
    basis_evidence = [item for item in basis_evidence if item]

    boundary_evidence = [
        _sentence_for_keywords(source_text, BOUNDARY_CONTENT_PATTERNS[code]) for code in boundary_codes
    ]
    boundary_evidence.extend(
        _sentence_for_keywords(source_text, BOUNDARY_MODE_PATTERNS[code]) for code in boundary_mode_codes
    )
    boundary_evidence = [item for item in boundary_evidence if item]

    return {
        "workflow": list(dict.fromkeys(workflow_evidence)),
        "legitimacy": list(dict.fromkeys(legitimacy_evidence + basis_evidence)),
        "boundary": list(dict.fromkeys(boundary_evidence)),
    }


def _decision_for_page(page: PagePayload) -> tuple[str, list[str]]:
    text = f"{page.title}\n{page.source_text}".strip()
    has_ai = _contains_any(text, AI_CORE_TERMS)
    if not has_ai:
        return "剔除", _format_decision_reason("R1", "未明确提及 AI 或可识别 AI 工具。")
    if _looks_like_generic_tool_roundup(text):
        return "剔除", _format_decision_reason("R8", "更像 AI 工具合集/产品信息，缺少具体科研实践场景。")

    workflow_codes = _choose_workflow_codes(text)
    has_research_context = _contains_any(text, RESEARCH_STAGE_TERMS)
    has_non_research = _contains_any(text, NON_RESEARCH_TERMS) and not has_research_context
    has_boundary_or_basis = bool(_choose_basis_codes(text) or _choose_boundary_codes(text))

    if has_non_research:
        return "剔除", _format_decision_reason("R4", "文本更像学习/办公/求职/一般开发场景。")
    if workflow_codes:
        return "纳入", _format_decision_reason("R12", "纳入：明确 AI 进入具体科研工作流环节。")
    if has_research_context and has_boundary_or_basis:
        return "纳入", _format_decision_reason("R12", "纳入：明确评价/边界对象指向具体科研实践。")
    if has_research_context:
        return "待复核", _format_decision_reason("R6", "科研环节可能相关，但环节识别不稳定。")
    if len(page.source_text) < 140:
        return "待复核", _format_decision_reason("R11", "可能相关但证据不足，建议复核。")
    return "剔除", _format_decision_reason("R2", "无可稳定识别的具体科研工作流环节。")


def _confidence(decision: str, workflow_codes: list[str], legitimacy_codes: list[str], boundary_codes: list[str]) -> str:
    if decision == "待复核":
        return "低"
    evidence_count = len(workflow_codes) + len([code for code in legitimacy_codes if code != "B0"]) + len(boundary_codes)
    if evidence_count >= 3:
        return "高"
    return "中"


def _review_points(decision: str, workflow_codes: list[str], legitimacy_codes: list[str]) -> list[str]:
    points: list[str] = []
    if decision == "待复核":
        if not workflow_codes:
            points.append("需复核科研工作流环节是否可稳定判定。")
        if legitimacy_codes == ["B5"]:
            points.append("疑似存在评价，但方向不清。")
    return points


def encode_page(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    end_date: date,
) -> dict[str, Any]:
    page_title = page.title
    if not page_title or page_title.startswith("小红书_"):
        page_title = candidate.title or page_title
    author_handle = page.author_handle or candidate.author
    combined_text = _normalize_space(f"{page_title}\n{page.source_text}")
    workflow_codes = _choose_workflow_codes(combined_text)
    legitimacy_codes = _choose_legitimacy(combined_text)
    basis_codes = _choose_basis_codes(combined_text)
    boundary_codes = _choose_boundary_codes(combined_text)
    boundary_mode_codes = _choose_boundary_mode_codes(combined_text)
    decision, decision_reason = _decision_for_page(page)
    if decision != "纳入":
        workflow_codes = workflow_codes if decision == "待复核" else []
        legitimacy_codes = legitimacy_codes if decision == "待复核" else []
        basis_codes = basis_codes if decision == "待复核" else []
        boundary_codes = boundary_codes if decision == "待复核" else []
        boundary_mode_codes = boundary_mode_codes if decision == "待复核" else []
    evidence_groups = _collect_evidence(
        combined_text,
        workflow_codes,
        legitimacy_codes,
        basis_codes,
        boundary_codes,
        boundary_mode_codes,
    )
    claim_units = (
        _make_claim_units(
            source_text=combined_text,
            workflow_codes=workflow_codes,
            legitimacy_codes=legitimacy_codes,
            basis_codes=basis_codes,
            boundary_codes=boundary_codes,
            boundary_mode_codes=boundary_mode_codes,
        )
        if decision == "纳入"
        else []
    )
    primary_dimensions = sorted({STAGE_TO_DIMENSION[code] for code in workflow_codes})
    evidence_master = list(
        dict.fromkeys(
            claim_evidence
            for claim in claim_units
            for claim_evidence in claim.get("evidence", [])
            if claim_evidence
        )
    )
    boundary_present = "是" if boundary_codes or boundary_mode_codes else "否"
    ambiguity = "是" if decision == "待复核" or legitimacy_codes == ["B5"] else "否"
    confidence = _confidence(decision, workflow_codes, legitimacy_codes, boundary_codes)
    mechanism_eligible = "待定" if decision == "纳入" and boundary_present == "是" else "否"
    theme_summary = _theme_summary(page_title, workflow_codes, legitimacy_codes)
    target_practice_summary = _target_practice_summary(workflow_codes, boundary_codes)
    created_at = page.created_at or candidate.result_date
    if created_at:
        try:
            created_date = datetime.strptime(created_at, "%Y-%m-%d").date()
            if created_date > end_date:
                created_at = ""
        except ValueError:
            created_at = ""

    return {
        "post_id": page.note_id,
        "task_batch_id": TASK_BATCH_ID,
        "coder_version": CODER_VERSION,
        "platform": "xiaohongshu",
        "post_url": page.url,
        "author_id": _sha1(author_handle) if author_handle else "",
        "created_at": created_at,
        "language": "zh",
        "thread_id": "",
        "parent_post_id": "",
        "reply_to_post_id": "",
        "quoted_post_id": "",
        "context_available": "否",
        "context_used": "none",
        "source_text": combined_text,
        "context_text": "",
        "decision": decision,
        "decision_reason": decision_reason,
        "theme_summary": theme_summary,
        "target_practice_summary": target_practice_summary,
        "evidence_master": evidence_master,
        "discursive_mode": _discursive_mode(combined_text),
        "practice_status": _practice_status(combined_text),
        "speaker_position_claimed": _speaker_position(combined_text),
        "workflow_dimension": {
            "primary_dimension": primary_dimensions,
            "secondary_stage": workflow_codes,
            "evidence": evidence_groups["workflow"],
        },
        "legitimacy_evaluation": {
            "direction": legitimacy_codes if decision != "剔除" else [],
            "basis": basis_codes if decision != "剔除" else [],
            "evidence": evidence_groups["legitimacy"],
        },
        "boundary_expression": {
            "present": boundary_present if decision != "剔除" else "否",
            "boundary_content_codes": boundary_codes if decision != "剔除" else [],
            "boundary_expression_mode_codes": boundary_mode_codes if decision != "剔除" else [],
            "evidence": evidence_groups["boundary"],
        },
        "interaction_level": {
            "event_present": "不适用",
            "interaction_role": "unclear",
            "target_claim_summary": "",
            "event_codes": [],
            "event_basis_codes": [],
            "event_outcome": "",
            "evidence": [],
        },
        "claim_units": claim_units,
        "mechanism_memo": {
            "eligible_for_mechanism_analysis": mechanism_eligible,
            "candidate_pattern_notes": (
                ["单帖存在边界表达，可与其他帖子做后续比较；不得直接视为机制。"]
                if mechanism_eligible == "待定"
                else []
            ),
            "comparison_keys": workflow_codes + legitimacy_codes + boundary_codes,
        },
        "api_assistance": {
            "used": "否",
            "purpose": [],
            "api_confidence": "无",
            "adoption_note": "No external model used; conservative rule-based coding only.",
        },
        "notes": {
            "multi_label": "是" if len(workflow_codes) > 1 or len(claim_units) > 1 else "否",
            "ambiguity": ambiguity,
            "confidence": confidence,
            "review_points": _review_points(decision, workflow_codes, legitimacy_codes),
            "dedup_group": page.note_id,
        },
        "review_status": "unreviewed",
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _load_query_template_metadata() -> dict[str, Any]:
    if not LEGACY_QUERY_TEMPLATE.exists():
        return {}
    try:
        payload = json.loads(LEGACY_QUERY_TEMPLATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload.get("metadata", {})


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
) -> tuple[Path, Path]:
    doctor_status = check_opencli_prerequisite()
    query_template_metadata = _load_query_template_metadata()
    queries = build_fixed_queries()
    if max_queries is not None:
        queries = queries[: max(0, int(max_queries))]
    existing_urls = _load_existing_post_urls(db_path)

    provider_name = "opencli_xiaohongshu" if doctor_status.extension_connected else "bing_fallback"
    candidates_seen: set[str] = set()
    title_hash_seen: set[str] = set()
    author_counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    query_stats: list[dict[str, Any]] = []
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
                    }
                )
                continue

        retained_this_query = 0
        verified_this_query = 0
        for candidate in search_results:
            if retained_this_query >= per_query_cap:
                break
            if len(rows) >= max_coded and included_count >= min_included:
                break
            if verified_count >= max_verified:
                break
            fetch_url = _canonical_url(candidate.url)
            dedupe_key = _dedupe_url_key(fetch_url)
            if not fetch_url or dedupe_key in existing_urls or dedupe_key in candidates_seen:
                continue
            author_key = _sha1(candidate.author) if candidate.author else ""
            if author_key and author_counts.get(author_key, 0) >= per_author_cap:
                continue

            try:
                page = _fetch_public_note_direct(fetch_url)
            except Exception:
                page = None
            if page is None:
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
                        continue
                except ValueError:
                    pass
            title_hash = _sha1(f"{page.title}\n{page.source_text[:200]}")
            if title_hash in title_hash_seen:
                continue

            row = encode_page(page=page, candidate=candidate, end_date=end_date)
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
            }
        )

    rows.sort(key=lambda item: (item["created_at"] or "9999-99-99", item["post_id"]))
    _write_jsonl(output_path, rows)

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
        "query_template_metadata": query_template_metadata,
        "query_count": len(queries),
        "max_coded_target": max_coded,
        "min_included_target": min_included,
        "max_verified_limit": max_verified,
        "row_count": len(rows),
        "included_count": included_count,
        "review_needed_count": sum(1 for row in rows if row["decision"] == "待复核"),
        "excluded_count": sum(1 for row in rows if row["decision"] == "剔除"),
        "query_stats": query_stats,
        "limitations": (
            [
                "OpenCLI Browser Bridge was not connected; the run fell back to Bing discovery plus direct public-note fetch.",
            ]
            if not doctor_status.extension_connected
            else []
        ),
        "output_path": str(output_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
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
    )
    print(output_path)
    print(summary_path, file=sys.stderr)


if __name__ == "__main__":
    main()
