from __future__ import annotations

import json
import sqlite3
import tomllib
from datetime import date
from pathlib import Path

from ai4s_legitimacy.collection import xhs_expansion_candidate_v1 as expansion
from ai4s_legitimacy.collection.xhs_expansion_candidate_v1 import (
    TASK_BATCH_ID,
    DoctorStatus,
    PagePayload,
    SearchCandidate,
    run_xhs_expansion_candidate_v1,
)
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _seed_quality_v5_guard_db(db_path: Path) -> None:
    init_sqlite_db(db_path, SCHEMA_PATH, views_sql=render_views_sql())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO import_batches (batch_name, source_description) VALUES ('test_batch', 'test')"
        )
        connection.execute(
            "INSERT INTO platform_sources (platform_code, platform_name) VALUES ('xiaohongshu', '小红书')"
        )
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                actor_type, qs_broad_subject, workflow_stage, primary_legitimacy_stance,
                decision, review_status, title, content_text, ai_tools_json,
                risk_themes_json, benefit_themes_json, import_batch_id
            ) VALUES (
                'p_formal', 'xiaohongshu', 'crawled', '2024-01-15', 'true',
                'graduate_student', 'Engineering & Technology', '文献调研与知识整合',
                '有条件接受', '纳入', 'reviewed', '标题',
                '用AI梳理综述框架但人工复核', '["ChatGPT"]', '[]', '["efficiency"]', 1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO claim_units (
                record_type, record_id, claim_index, practice_unit,
                workflow_stage_codes_json, legitimacy_codes_json, evidence_json
            ) VALUES (
                'post', 'p_formal', 0, 'AI辅助文献综述',
                '["A1.2"]', '["B2"]', '["用AI梳理综述框架但人工复核"]'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, decision, review_status,
                stance, legitimacy_basis, import_batch_id
            ) VALUES (
                'c_unformal', 'p_formal', '2024-01-16', '评论只作为现有语料存在',
                '待复核', 'unreviewed', '有条件接受', '责任归属', 1
            )
            """
        )
        connection.commit()


def _fake_doctor() -> DoctorStatus:
    return DoctorStatus(
        daemon_running=True,
        extension_connected=True,
        connectivity_ok=True,
        raw_output="opencli test ok",
    )


def _fake_search(query, *, limit: int) -> list[SearchCandidate]:
    query_slug = "".join(ch for ch in query.name if ch.isalnum())
    return [
        SearchCandidate(
            query_name=query.name,
            query_text=query.query,
            title=f"{query.name} AI科研 文献综述 {index}",
            url=f"https://www.xiaohongshu.com/explore/{query_slug}{index:03d}",
            author=f"author_{query_slug}_{index}",
            snippet="",
            source="opencli_xiaohongshu",
            result_date="2025-03-15",
        )
        for index in range(limit)
    ]


def _fake_fetch(url: str) -> PagePayload:
    note_id = url.rstrip("/").rsplit("/", 1)[-1]
    return PagePayload(
        url=url,
        note_id=note_id,
        title=f"DeepSeek 文献综述人工复核 {note_id}",
        source_text=f"我用 DeepSeek 做科研文献综述 {note_id}，但最后必须自己核查原文和引用。",
        author_handle=f"author_{note_id}",
        created_at="2025-03-15",
        status="ok",
        fetched_via="test",
    )


def _fake_comment_sidecar(
    *,
    page: PagePayload,
    candidate: SearchCandidate,
    doctor_status: DoctorStatus,
) -> list[dict[str, object]]:
    return [
        {
            "record_type": "comment",
            "comment_id": f"{page.note_id}:comment:0001",
            "comment_text": "评论认为AI只能辅助，不能替代研究者。",
            "parent_post_id": page.note_id,
            "parent_post_url": page.url,
            "parent_query_name": candidate.query_name,
            "parent_query_text": candidate.query_text,
            "comment_fetch_status": "ok",
            "source_strategy": "mock_browser_session",
            "formal_result_scope": False,
            "review_status": "unreviewed",
        }
    ]


def test_xhs_expansion_candidate_v1_runs_500_post_target_with_comment_sidecar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_quality_v5_guard_db(db_path)
    monkeypatch.setattr(expansion, "check_opencli_prerequisite", _fake_doctor)
    monkeypatch.setattr(expansion, "_search_with_opencli", _fake_search)
    monkeypatch.setattr(expansion, "_fetch_public_note_direct", _fake_fetch)
    monkeypatch.setattr(expansion, "_fetch_comments_with_browser_session", _fake_comment_sidecar)

    post_path, comment_path, summary_path = run_xhs_expansion_candidate_v1(
        post_output_path=tmp_path / "outputs" / "posts.jsonl",
        comment_output_path=tmp_path / "outputs" / "comments.jsonl",
        summary_path=tmp_path / "reports" / "summary.json",
        review_queue_dir=tmp_path / "queues",
        db_path=db_path,
        max_coded=500,
        max_verified=700,
        search_limit=30,
        per_query_cap=20,
        per_author_cap=99,
        max_comment_probes=500,
        batch_size=100,
    )

    posts = _read_jsonl(post_path)
    comments = _read_jsonl(comment_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(posts) == 500
    assert len(comments) == 500
    assert posts[0]["task_batch_id"] == TASK_BATCH_ID
    assert posts[0]["formal_result_scope"] is False
    assert posts[0]["artifact_classification"]["status"] == "xhs_expansion_candidate_v1"
    assert comments[0]["parent_post_id"]
    assert comments[0]["comment_fetch_status"] == "ok"
    assert comments[0]["formal_result_scope"] is False
    assert summary["max_coded_target"] == 500
    assert summary["max_comment_probes"] == 500
    assert summary["comment_probe_count"] == 500
    assert summary["post_row_count"] == 500
    assert summary["artifact_status"] == "xhs_expansion_candidate_v1"
    assert summary["comment_fetch_status_counts"] == {"ok": 500}
    assert summary["formal_baseline_guard_counts"]["paper_quality_v5_posts"] == 1
    assert summary["formal_baseline_guard_counts"]["paper_quality_v5_comments"] == 0
    assert summary["review_queue"]["batch_count"] == 5
    assert Path(summary["review_queue"]["batches"][0]["review_template_path"]).exists()

    with sqlite3.connect(db_path) as connection:
        counts = dict(connection.execute("SELECT scope_name, row_count FROM vw_scope_counts"))
    assert counts["paper_quality_v5_posts"] == 1
    assert counts["paper_quality_v5_comments"] == 0


def test_xhs_expansion_candidate_v1_comment_failure_writes_status_row_without_blocking_post(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_quality_v5_guard_db(db_path)
    monkeypatch.setattr(
        expansion,
        "check_opencli_prerequisite",
        lambda: DoctorStatus(False, False, False, "extension missing"),
    )
    monkeypatch.setattr(expansion, "_search_with_bing", _fake_search)
    monkeypatch.setattr(expansion, "_fetch_public_note_direct", _fake_fetch)

    post_path, comment_path, summary_path = run_xhs_expansion_candidate_v1(
        post_output_path=tmp_path / "outputs" / "posts.jsonl",
        comment_output_path=tmp_path / "outputs" / "comments.jsonl",
        summary_path=tmp_path / "reports" / "summary.json",
        review_queue_dir=tmp_path / "queues",
        db_path=db_path,
        max_coded=1,
        max_verified=1,
        search_limit=1,
        per_query_cap=1,
        max_comment_probes=1,
        start_date=date(2024, 1, 1),
    )

    posts = _read_jsonl(post_path)
    comments = _read_jsonl(comment_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(posts) == 1
    assert len(comments) == 1
    assert comments[0]["record_type"] == "comment_fetch_status"
    assert comments[0]["comment_fetch_status"] == "browser_session_unavailable"
    assert summary["post_row_count"] == 1
    assert summary["comment_fetch_status_counts"] == {"browser_session_unavailable": 1}


def test_xhs_expansion_candidate_v1_defers_comment_probe_after_limit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_quality_v5_guard_db(db_path)
    monkeypatch.setattr(expansion, "check_opencli_prerequisite", _fake_doctor)
    monkeypatch.setattr(expansion, "_search_with_opencli", _fake_search)
    monkeypatch.setattr(expansion, "_fetch_public_note_direct", _fake_fetch)
    monkeypatch.setattr(expansion, "_fetch_comments_with_browser_session", _fake_comment_sidecar)

    _, comment_path, summary_path = run_xhs_expansion_candidate_v1(
        post_output_path=tmp_path / "outputs" / "posts.jsonl",
        comment_output_path=tmp_path / "outputs" / "comments.jsonl",
        summary_path=tmp_path / "reports" / "summary.json",
        review_queue_dir=tmp_path / "queues",
        db_path=db_path,
        max_coded=3,
        max_verified=3,
        search_limit=3,
        per_query_cap=3,
        per_author_cap=99,
        max_comment_probes=1,
    )

    comments = _read_jsonl(comment_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(comments) == 3
    assert summary["comment_probe_count"] == 1
    assert summary["comment_fetch_status_counts"] == {
        "ok": 1,
        "comment_fetch_deferred_after_probe_limit": 2,
    }


def test_xhs_expansion_candidate_v1_strips_public_page_chrome_noise(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "research.sqlite3"
    _seed_quality_v5_guard_db(db_path)

    def fake_fetch_with_page_chrome(url: str) -> PagePayload:
        note_id = url.rstrip("/").rsplit("/", 1)[-1]
        return PagePayload(
            url=url,
            note_id=note_id,
            title="DeepSeek 文献综述",
            source_text=(
                "DeepSeek 文献综述 - 小红书 创作中心 业务合作 发现 直播 发布 通知 "
                "沪ICP备13030189号 window.__SSR__={}"
            ),
            author_handle="author_noise",
            created_at="2025-03-15",
            status="ok",
            fetched_via="test",
            raw_excerpt="DeepSeek 文献综述 - 小红书 营业执照",
        )

    monkeypatch.setattr(expansion, "check_opencli_prerequisite", _fake_doctor)
    monkeypatch.setattr(expansion, "_search_with_opencli", _fake_search)
    monkeypatch.setattr(expansion, "_fetch_public_note_direct", fake_fetch_with_page_chrome)

    post_path, _, summary_path = run_xhs_expansion_candidate_v1(
        post_output_path=tmp_path / "outputs" / "posts.jsonl",
        comment_output_path=tmp_path / "outputs" / "comments.jsonl",
        summary_path=tmp_path / "reports" / "summary.json",
        review_queue_dir=tmp_path / "queues",
        db_path=db_path,
        max_coded=1,
        max_verified=1,
        search_limit=1,
        per_query_cap=1,
        max_comment_probes=0,
    )

    post = _read_jsonl(post_path)[0]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "创作中心" not in post["source_text"]
    assert "沪ICP备" not in post["source_text"]
    assert "window.__SSR__" not in post["source_text"]
    assert post["artifact_classification"]["quality_v5_formal_scope"] is False
    assert summary["artifact_status"] == "xhs_expansion_candidate_v1"


def test_xhs_expansion_candidate_v1_replaces_aborted_comment_extension_registry() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    assert "ai4s-xhs-expansion-candidate-v1" in scripts
    assert "ai4s-prepare-comment-extension-v1-batches" not in scripts
    assert "ai4s-build-comment-extension-v1-materials" not in scripts
