from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ai4s_legitimacy.collection import external_xhs_opencli_pilot as pilot
from ai4s_legitimacy.collection.external_xhs_opencli_pilot import (
    TASK_BATCH_ID,
    DoctorStatus,
    PagePayload,
    PilotQuery,
    SearchCandidate,
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

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["task_batch_id"] == TASK_BATCH_ID
    assert row["record_type"] == "post"
    assert row["record_id"] == page.note_id
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


def test_encode_page_recognizes_common_gpt_variants() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/gptvariant1",
        note_id="gptvariant1",
        title="Peer reviewer是用chat gpt的要怎么办",
        source_text=(
            "第三个peer review明显是直接chat gpt生成。"
            "他让我加几篇和研究不相关的reference，我写response letter越写越无语。"
            "这算不算学术不端？"
        ),
        author_handle="review_demo",
        created_at="2025-02-11",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="salience_chatgpt_peer_review",
        query_text="ChatGPT 审稿",
        title=page.title,
        url=page.url,
        author="review_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["decision"] == "纳入"
    assert row["decision_reason"][0].startswith("R12")
    assert "A2.7" in row["workflow_dimension"]["secondary_stage"]


def test_encode_page_uses_search_title_for_decision_when_page_title_is_placeholder() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/fallbacktitle1",
        note_id="fallbacktitle1",
        title="小红书_精选笔记",
        source_text="我现在只把它当作文献检索辅助，最后会自己核查原文和引用。",
        author_handle="researcher_demo",
        created_at="2025-03-15",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="practice_ai_lit_search",
        query_text="AI辅助科研 文献检索",
        title="DeepSeek 辅助科研文献检索的人工复核流程",
        url=page.url,
        author="researcher_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["decision"] == "纳入"
    assert row["theme_summary"] == candidate.title
    assert "A1.2" in row["workflow_dimension"]["secondary_stage"]


def test_encode_page_demotes_boundary_signal_without_stable_research_workflow() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/platformrisk1",
        note_id="platformrisk1",
        title="Claude开始查护照了，用户担心账号风险",
        source_text=(
            "Anthropic上线身份验证功能，要求用户提供护照和实时自拍。"
            "Persona KYC系统引发用户担忧，尤其是数据安全和隐私问题。"
        ),
        author_handle="platform_demo",
        created_at="2026-04-16",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="boundary_claude_review",
        query_text="Claude 数据分析 人工审核",
        title=page.title,
        url=page.url,
        author="platform_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["decision"] == "待复核"
    assert row["claim_units"] == []
    assert row["decision_reason"][0].startswith("R6")


def test_encode_page_maps_result_verification_to_reproduction_workflow() -> None:
    page = PagePayload(
        url="https://www.xiaohongshu.com/explore/verifyresult1",
        note_id="verifyresult1",
        title="AI科研结果验证必须人工复核",
        source_text="我用AI辅助科研做结果验证，但最终必须人工复核，不能直接相信模型结论。",
        author_handle="verify_demo",
        created_at="2026-03-20",
        status="ok",
        fetched_via="direct_http",
    )
    candidate = SearchCandidate(
        query_name="boundary_ai_verification",
        query_text="AI科研 结果验证 人工复核",
        title=page.title,
        url=page.url,
        author="verify_demo",
        snippet="",
        source="opencli_xiaohongshu",
    )

    row = encode_page(page=page, candidate=candidate, end_date=date(2026, 4, 21))

    assert row["decision"] == "纳入"
    assert "A1.7" in row["workflow_dimension"]["secondary_stage"]
    assert row["claim_units"]


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


def test_run_external_xhs_pilot_accepts_supplemental_query_file_and_writes_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    query_file = tmp_path / "xhs_expansion_candidate_v1_queries.json"
    query_file.write_text(
        json.dumps(
            {
                "metadata": {
                    "dictionary_id": "xhs_expansion_candidate_v1_queries",
                    "quality_v5_formal_scope": False,
                },
                "queries": [
                    {
                        "query": "AI文献综述",
                        "query_group": "B. 文献处理与知识整合类",
                        "intent": "test",
                        "expected_workflow_stage": "A1",
                        "notes": "test",
                    },
                    {
                        "query": "AI统计分析",
                        "query_group": "D. 数据分析与代码类",
                        "intent": "test",
                        "expected_workflow_stage": "A1",
                        "notes": "test",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pilot,
        "check_opencli_prerequisite",
        lambda: DoctorStatus(True, True, True, "opencli ok"),
    )
    monkeypatch.setattr(
        pilot,
        "build_fixed_queries",
        lambda: (_ for _ in ()).throw(AssertionError("default queries should not be used")),
    )

    def fake_search(query: PilotQuery, *, limit: int) -> list[SearchCandidate]:
        query_slug = "".join(ch for ch in query.name if ch.isalnum())
        return [
            SearchCandidate(
                query_name=query.name,
                query_text=query.query,
                title=f"{query.query} test {index}",
                url=f"https://www.xiaohongshu.com/explore/{query_slug}{index}",
                author=f"author_{query.name}_{index}",
                snippet="",
                source="opencli_xiaohongshu",
                result_date="2025-03-15",
            )
            for index in range(2)
        ]

    def fake_fetch(url: str) -> PagePayload:
        note_id = url.rstrip("/").rsplit("/", 1)[-1]
        if note_id.endswith("1"):
            return PagePayload(
                url=url,
                note_id=note_id,
                title="AI科研空正文",
                source_text="",
                author_handle="author_empty",
                created_at="2025-03-15",
                status="ok",
                fetched_via="test",
            )
        return PagePayload(
            url=url,
            note_id=note_id,
            title=f"AI辅助科研文献综述 {note_id}",
            source_text=f"我用AI辅助科研做文献综述 {note_id}，但最后必须自己核查原文和引用。",
            author_handle="author_ok",
            created_at="2025-03-15",
            status="ok",
            fetched_via="test",
        )

    monkeypatch.setattr(pilot, "_search_with_opencli", fake_search)
    monkeypatch.setattr(pilot, "_fetch_public_note_direct", fake_fetch)

    output_path, summary_path = pilot.run_external_xhs_pilot(
        output_path=tmp_path / "pilot50.jsonl",
        summary_path=tmp_path / "pilot50.summary.json",
        report_path=tmp_path / "pilot50.report.md",
        db_path=tmp_path / "missing.sqlite3",
        query_file=query_file,
        max_coded=4,
        min_included=4,
        max_verified=4,
        search_limit=2,
        per_query_cap=2,
        max_queries=2,
    )

    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = (tmp_path / "pilot50.report.md").read_text(encoding="utf-8")

    assert len(rows) == 2
    assert rows[0]["formal_result_scope"] is False
    assert rows[0]["quality_v5_formal_scope"] is False
    assert rows[0]["artifact_classification"]["status"] == "xhs_expansion_candidate_v1_pilot50"
    assert rows[0]["query"] in {"AI文献综述", "AI统计分析"}
    assert rows[0]["query_group"] in {"B. 文献处理与知识整合类", "D. 数据分析与代码类"}
    assert rows[0]["source_method"] == "opencli_xiaohongshu"
    assert summary["query_source"] == "query_file"
    assert summary["query_count"] == 2
    assert summary["executed_query_count"] == 2
    assert summary["query_template_metadata"]["dictionary_id"] == "xhs_expansion_candidate_v1_queries"
    assert summary["skip_counts"]["empty_body"] == 2
    assert summary["formal_result_scope"] is False
    assert summary["quality_v5_formal_scope"] is False
    assert summary["artifact_classification"]["status"] == "xhs_expansion_candidate_v1_pilot50"
    assert "载入查询词数量：`2`" in report
    assert "实际执行检索的查询词数量：`2`" in report
    assert "不构成论文发现" in report


def test_run_external_xhs_pilot_report_compares_with_previous_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    query_file = tmp_path / "xhs_expansion_candidate_v1_queries.json"
    query_file.write_text(
        json.dumps(
            {
                "metadata": {"dictionary_id": "xhs_expansion_candidate_v1_queries"},
                "queries": [
                    {
                        "query": "AI文献综述",
                        "query_group": "B. 文献处理与知识整合类",
                        "intent": "test",
                        "expected_workflow_stage": "A1",
                        "notes": "test",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    comparison_summary = tmp_path / "pilot50.summary.json"
    comparison_summary.write_text(
        json.dumps(
            {
                "output_path": "outputs/tables/xhs_expansion_candidate_v1/pilot50.jsonl",
                "row_count": 1,
                "included_count": 1,
                "query_stats": [
                    {"query": "AI文献综述", "search_hits": 2, "verified_kept": 1, "skip_counts": {}}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pilot,
        "check_opencli_prerequisite",
        lambda: DoctorStatus(True, True, True, "opencli ok"),
    )

    def fake_search(query: PilotQuery, *, limit: int) -> list[SearchCandidate]:
        return [
            SearchCandidate(
                query_name=query.name,
                query_text=query.query,
                title=f"{query.query} test {index}",
                url=f"https://www.xiaohongshu.com/explore/compare{index}",
                author=f"author_{index}",
                snippet="",
                source="opencli_xiaohongshu",
                result_date="2025-03-15",
            )
            for index in range(3)
        ]

    def fake_fetch(url: str) -> PagePayload:
        note_id = url.rstrip("/").rsplit("/", 1)[-1]
        return PagePayload(
            url=url,
            note_id=note_id,
            title=f"AI文献综述 {note_id}",
            source_text=f"我用AI读文献并写文献综述 {note_id}，这是经验分享，也提醒要人工核查。",
            author_handle=f"author_{note_id}",
            created_at="2025-03-15",
            status="ok",
            fetched_via="test",
        )

    monkeypatch.setattr(pilot, "_search_with_opencli", fake_search)
    monkeypatch.setattr(pilot, "_fetch_public_note_direct", fake_fetch)

    _, summary_path = pilot.run_external_xhs_pilot(
        output_path=tmp_path / "candidate300.jsonl",
        summary_path=tmp_path / "candidate300.summary.json",
        report_path=tmp_path / "candidate300.report.md",
        comparison_summary_path=comparison_summary,
        db_path=tmp_path / "missing.sqlite3",
        query_file=query_file,
        max_coded=3,
        min_included=2,
        max_verified=3,
        search_limit=3,
        per_query_cap=3,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = (tmp_path / "candidate300.report.md").read_text(encoding="utf-8")
    assert summary["artifact_classification"]["status"] == "xhs_expansion_candidate_v1_candidate300"
    assert summary["comparison_summary_path"] == str(comparison_summary)
    assert "查询词表现与 pilot 对比" in report
    assert "表现更好的查询词" in report
    assert "主题覆盖" in report
    assert "话语类型初步判断" in report


def test_run_external_xhs_pilot_preserves_existing_output_on_empty_failed_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_path = tmp_path / "existing.jsonl"
    summary_path = tmp_path / "summary.json"
    existing_payload = (
        '{"post_id": "existing", "record_type": "post", "record_id": "existing", '
        '"decision": "纳入"}\n'
    )
    output_path.write_text(existing_payload, encoding="utf-8")

    monkeypatch.setattr(
        pilot,
        "check_opencli_prerequisite",
        lambda: DoctorStatus(
            daemon_running=False,
            extension_connected=False,
            connectivity_ok=False,
            raw_output="offline",
        ),
    )
    monkeypatch.setattr(
        pilot,
        "build_fixed_queries",
        lambda: [PilotQuery("practice_ai_lit_review", "AI科研 文献综述", "practice")],
    )

    def fail_search(_query: PilotQuery, *, limit: int) -> list[SearchCandidate]:
        raise RuntimeError(f"offline limit={limit}")

    monkeypatch.setattr(pilot, "_search_with_bing", fail_search)

    pilot.run_external_xhs_pilot(
        output_path=output_path,
        summary_path=summary_path,
        db_path=tmp_path / "missing.sqlite3",
        max_coded=2,
        min_included=1,
        max_verified=2,
        search_limit=1,
        max_queries=1,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert output_path.read_text(encoding="utf-8") == existing_payload
    assert summary["row_count"] == 0
    assert summary["output_row_count"] == 1
    assert summary["output_preserved"] is True
    assert summary["preserved_existing_row_count"] == 1
    assert summary["included_count"] == 0
    assert summary["output_included_count"] == 1
    assert summary["preserved_existing_decision_counts"] == {
        "included": 1,
        "review_needed": 0,
        "excluded": 0,
    }
    assert summary["artifact_classification"] == {
        "status": "diagnostic_failed_run_preserved_output",
        "formal_evidence_chain": False,
        "quality_v5_formal_scope": False,
        "reason": (
            "This run harvested no new rows and preserved an existing non-empty JSONL; "
            "keep it for diagnostics only, not paper_scope_quality_v5 evidence."
        ),
    }
    assert "existing non-empty JSONL output was preserved" in summary["limitations"][-1]
