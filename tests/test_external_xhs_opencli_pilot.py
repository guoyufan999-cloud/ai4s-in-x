from __future__ import annotations

from datetime import date

from ai4s_legitimacy.collection.external_xhs_opencli_pilot import (
    PagePayload,
    SearchCandidate,
    TASK_BATCH_ID,
    _canonical_url,
    _extract_note_id,
    _parse_doctor_output,
    _parse_search_author_and_date,
    build_fixed_queries,
    encode_page,
)


def test_build_fixed_queries_returns_expected_query_set() -> None:
    queries = build_fixed_queries()
    assert len(queries) == 36
    assert len({query.name for query in queries}) == 36
    assert {query.category for query in queries} == {"practice", "boundary", "salience"}


def test_parse_doctor_output_detects_extension_disconnect() -> None:
    status = _parse_doctor_output(
        """
opencli v1.4.1 doctor

[OK] Daemon: running on port 19825
[MISSING] Extension: not connected
[FAIL] Connectivity: failed (Daemon is running but the Browser Extension is not connected.)
"""
    )
    assert status.daemon_running is True
    assert status.extension_connected is False
    assert status.connectivity_ok is False


def test_encode_page_builds_strict_record_shape_for_included_post() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/abc123",
        note_id="abc123",
        title="DeepSeek 文献综述踩坑：瞎编文献后我只敢人工复核",
        source_text=(
            "DeepSeek 做文献综述时给我瞎编了两篇参考文献。"
            "现在我只把它当作文献检索辅助，最终必须自己核查原文和引用。"
        ),
        author_handle="researcher_demo",
        created_at="2025-03-15",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="boundary_deepseek_fake_refs",
        query_text="DeepSeek 文献综述 瞎编文献",
        title=page.title,
        url=page.url,
        author="researcher_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=page.created_at and __import__("datetime").date(2026, 4, 21))

    assert row["task_batch_id"] == TASK_BATCH_ID
    assert row["decision"] == "纳入"
    assert row["platform"] == "xiaohongshu"
    assert row["context_available"] == "否"
    assert row["context_used"] == "none"
    assert row["interaction_level"]["event_present"] == "不适用"
    assert "A1.2" in row["workflow_dimension"]["secondary_stage"]
    assert row["boundary_expression"]["present"] == "是"
    assert row["claim_units"]
    assert row["review_status"] == "unreviewed"


def test_encode_page_excludes_non_research_post() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/nonresearch1",
        note_id="nonresearch1",
        title="ChatGPT 帮我准备产品经理面试",
        source_text="ChatGPT 帮我整理产品经理面试题，做办公汇报提效很多。",
        author_handle="career_demo",
        created_at="2025-05-02",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="practice_chatgpt_design",
        query_text="ChatGPT 研究设计",
        title=page.title,
        url=page.url,
        author="career_demo",
        snippet="",
        source="bing_html",
    )

    row = encode_page(page=page, candidate=candidate, end_date=__import__("datetime").date(2026, 4, 21))

    assert row["decision"] == "剔除"
    assert row["decision_reason"][0].startswith("R4")
    assert row["workflow_dimension"]["secondary_stage"] == []


def test_encode_page_excludes_generic_ai_tool_roundup() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/search_result/roundup1?xsec_token=abc&xsec_source=",
        note_id="roundup1",
        title="24個ChatGPT 神級組合，每一個都生產力爆表",
        source_text=(
            "文本庫⇢ notion.com 平面設計⇢ canva.com AI編程⇢ cline.bot "
            "圖表生成⇢ napkin.ai #ai #人类高质量科研工具 #生产力提升"
        ),
        author_handle="tools_demo",
        created_at="2025-03-07",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="practice_chatgpt_design",
        query_text="ChatGPT 研究设计",
        title=page.title,
        url=page.url,
        author="tools_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["decision"] == "剔除"
    assert row["decision_reason"][0].startswith("R8")


def test_search_result_urls_keep_tokens_and_note_ids() -> None:
    url = (
        "https://www.xiaohongshu.com/search_result/69cfa5d7000000001a034f60"
        "?xsec_token=abc123&xsec_source="
    )
    assert _canonical_url(url) == url
    assert _extract_note_id(url) == "69cfa5d7000000001a034f60"


def test_parse_search_author_and_date_extracts_visible_result_date() -> None:
    author, created_at = _parse_search_author_and_date("极客老黑聊AI04-11", end_date=date(2026, 4, 21))
    assert author == "极客老黑聊AI"
    assert created_at == "2026-04-11"

    author2, created_at2 = _parse_search_author_and_date(
        "UU的百宝箱2025-02-04",
        end_date=date(2026, 4, 21),
    )
    assert author2 == "UU的百宝箱"
    assert created_at2 == "2025-02-04"
