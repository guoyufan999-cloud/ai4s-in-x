from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ai4s_legitimacy.collection.audit_snapshot import export_quality_v4_audit_snapshot
from ai4s_legitimacy.collection.review_batch_prep import prepare_review_batches
from ai4s_legitimacy.collection.review_queue import export_review_queue
from ai4s_legitimacy.collection.reviewed_import import import_reviewed_file
from ai4s_legitimacy.config.research_scope import render_views_sql
from ai4s_legitimacy.config.settings import SCHEMA_PATH
from ai4s_legitimacy.utils.db import init_sqlite_db


def _seed_staging_db(db_path: Path) -> None:
    init_sqlite_db(db_path, SCHEMA_PATH, views_sql=render_views_sql())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO import_batches (batch_name, source_description) VALUES ('rebaseline_quality_v5_staging', 'test')"
        )
        connection.execute(
            "INSERT INTO platform_sources (platform_code, platform_name) VALUES ('xiaohongshu', '小红书')"
        )
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p1', 'xiaohongshu', 'crawled', '2025-01-15', 'review_needed',
                '标题', '重新审查这个帖子', '[]', '[]', '[]', 1
            )
            """
        )
        connection.execute(
            """
            INSERT INTO comments (
                comment_id, post_id, comment_date, comment_text, benefit_themes_json, import_batch_id
            ) VALUES (
                'c1', 'p1', '2025-01-16', '评论文本', '[]', 1
            )
            """
        )
        connection.commit()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_export_review_queue_and_import_reviewed_records_updates_staging_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    queue_path = tmp_path / "queues" / "rescreen_posts.jsonl"
    _seed_staging_db(db_path)

    exported_queue = export_review_queue(
        db_path=db_path,
        phase="rescreen_posts",
        output_path=queue_path,
    )
    exported_rows = [json.loads(line) for line in exported_queue.read_text(encoding="utf-8").splitlines()]
    assert exported_rows[0]["review_phase"] == "rescreen_posts"
    assert exported_rows[0]["sample_status"] == "review_needed"

    reviewed_rescreen = tmp_path / "reviewed_rescreen.jsonl"
    _write_jsonl(
        reviewed_rescreen,
        [
            {
                "run_id": "run-rescreen",
                "review_phase": "rescreen_posts",
                "review_status": "approved",
                "reviewer": "human-a",
                "review_date": "2026-04-18",
                "post_id": "p1",
                "sample_status": "true",
                "actor_type": "graduate_student",
                "model": "gpt-5",
            }
        ],
    )
    import_reviewed_file(reviewed_path=reviewed_rescreen, db_path=db_path)

    reviewed_post_v2 = tmp_path / "reviewed_post_v2.jsonl"
    _write_jsonl(
        reviewed_post_v2,
        [
            {
                "run_id": "run-post-review-v2",
                "review_phase": "post_review_v2",
                "review_status": "approved",
                "reviewer": "human-a",
                "review_date": "2026-04-18",
                "post_id": "p1",
                "decision": "纳入",
                "decision_reason": ["R12: 明确展示 AI 进入研究问题定义环节。"],
                "theme_summary": "AI 参与研究问题定义",
                "target_practice_summary": "AI辅助研究构思",
                "source_text": "研究生分享如何用 ChatGPT 讨论课题方向，并要求人工最终核查。",
                "discursive_mode": "experience_share",
                "practice_status": "actual_use",
                "speaker_position_claimed": "graduate_student",
                "actor_type": "graduate_student",
                "qs_broad_subject": "Engineering & Technology",
                "workflow_dimension": {
                    "primary_dimension": ["A1"],
                    "secondary_stage": ["A1.1"],
                    "evidence": ["用 ChatGPT 讨论课题方向"],
                },
                "legitimacy_evaluation": {
                    "direction": ["B2"],
                    "basis": ["C1", "C7"],
                    "evidence": ["它能提效，但最终判断还得自己做。"],
                },
                "boundary_expression": {
                    "present": "是",
                    "boundary_content_codes": ["D1.2", "D1.10"],
                    "boundary_expression_mode_codes": ["D2.5", "D2.6"],
                    "evidence": ["AI 只能辅助构思，最终必须自己核查。"],
                },
                "claim_units": [
                    {
                        "practice_unit": "AI辅助研究构思",
                        "workflow_stage_codes": ["A1.1"],
                        "legitimacy_codes": ["B2"],
                        "basis_codes": [
                            {"code": "C1", "evidence": "它能提效。"},
                            {"code": "C7", "evidence": "最终判断还得自己做。"},
                        ],
                        "boundary_codes": [
                            {"code": "D1.2", "evidence": "AI 只能辅助构思。"},
                            {"code": "D1.10", "evidence": "最终必须自己核查。"},
                        ],
                        "boundary_mode_codes": [
                            {"code": "D2.5", "evidence": "最终必须自己核查。"},
                            {"code": "D2.6", "evidence": "最终判断还得自己做。"},
                        ],
                        "evidence": ["用 ChatGPT 讨论课题方向。"],
                    }
                ],
            }
        ],
    )
    import_reviewed_file(reviewed_path=reviewed_post_v2, db_path=db_path)

    reviewed_comment_v2 = tmp_path / "reviewed_comment_v2.jsonl"
    _write_jsonl(
        reviewed_comment_v2,
        [
            {
                "run_id": "run-comment-review-v2",
                "review_phase": "comment_review_v2",
                "review_status": "approved",
                "reviewer": "human-b",
                "review_date": "2026-04-19",
                "comment_id": "c1",
                "post_id": "p1",
                "decision": "纳入",
                "decision_reason": ["R12: 评论明确回应 AI 辅助研究构思的边界。"],
                "source_text": "这个思路有帮助，但最终责任还是研究者自己承担。",
                "workflow_dimension": {
                    "primary_dimension": ["A1"],
                    "secondary_stage": ["A1.1"],
                    "evidence": ["这个思路有帮助。"],
                },
                "legitimacy_evaluation": {
                    "direction": ["B2"],
                    "basis": ["C3"],
                    "evidence": ["最终责任还是研究者自己承担。"],
                },
                "boundary_expression": {
                    "present": "是",
                    "boundary_content_codes": ["D1.3"],
                    "boundary_expression_mode_codes": ["D2.6"],
                    "evidence": ["最终责任还是研究者自己承担。"],
                },
                "claim_units": [
                    {
                        "practice_unit": "评论回应研究者责任边界",
                        "workflow_stage_codes": ["A1.1"],
                        "legitimacy_codes": ["B2"],
                        "basis_codes": [{"code": "C3", "evidence": "最终责任还是研究者自己承担。"}],
                        "boundary_codes": [{"code": "D1.3", "evidence": "最终责任还是研究者自己承担。"}],
                        "boundary_mode_codes": [{"code": "D2.6", "evidence": "最终责任还是研究者自己承担。"}],
                        "evidence": ["最终责任还是研究者自己承担。"],
                    }
                ],
            }
        ],
    )
    import_reviewed_file(reviewed_path=reviewed_comment_v2, db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        post = connection.execute("SELECT * FROM posts WHERE post_id = 'p1'").fetchone()
        comment = connection.execute("SELECT * FROM comments WHERE comment_id = 'c1'").fetchone()
        claim_units = connection.execute(
            "SELECT COUNT(*) AS c FROM claim_units WHERE record_id IN ('p1', 'c1')"
        ).fetchone()["c"]
        interaction_events = connection.execute(
            "SELECT COUNT(*) AS c FROM interaction_events WHERE record_id IN ('p1', 'c1')"
        ).fetchone()["c"]
        review_runs = connection.execute("SELECT COUNT(*) AS c FROM review_runs").fetchone()["c"]
        reviewed_records = connection.execute(
            "SELECT COUNT(*) AS c FROM reviewed_records"
        ).fetchone()["c"]

    assert post["sample_status"] == "true"
    assert post["actor_type"] == "graduate_student"
    assert post["qs_broad_subject"] == "Engineering & Technology"
    assert post["decision"] == "纳入"
    assert post["boundary_present"] == "是"
    assert comment["decision"] == "纳入"
    assert comment["stance"] == "有条件接受"
    assert comment["legitimacy_basis"] == "责任归属"
    assert claim_units == 2
    assert interaction_events == 2
    assert review_runs == 3
    assert reviewed_records == 3


def test_import_reviewed_file_rejects_unapproved_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "staging.sqlite3"
    reviewed_path = tmp_path / "suggestion_only.jsonl"
    _seed_staging_db(db_path)
    _write_jsonl(
        reviewed_path,
        [
            {
                "run_id": "run-pending",
                "review_phase": "rescreen_posts",
                "review_status": "pending",
                "reviewer": "human-a",
                "review_date": "2026-04-18",
                "post_id": "p1",
                "sample_status": "true",
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match="review_status in",
    ):
        import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)


@pytest.mark.parametrize(
    ("reviewed_rows", "error_match"),
    [
        (
            [
                {
                    "run_id": "run-missing-rescreen-status",
                    "review_phase": "rescreen_posts",
                    "review_status": "approved",
                    "reviewer": "human-a",
                    "review_date": "2026-04-18",
                    "post_id": "p1",
                }
            ],
            "sample_status",
        ),
        (
            [
                {
                    "run_id": "run-missing-v2-decision",
                    "review_phase": "post_review_v2",
                    "review_status": "approved",
                    "reviewer": "human-a",
                    "review_date": "2026-04-18",
                    "post_id": "p1",
                    "reason": "信息不足，无法支持纳入。",
                }
            ],
            "inclusion_decision",
        ),
        (
            [
                {
                    "run_id": "run-missing-v2-reason",
                    "review_phase": "comment_review_v2",
                    "review_status": "approved",
                    "reviewer": "human-a",
                    "review_date": "2026-04-18",
                    "comment_id": "c1",
                    "inclusion_decision": "剔除",
                }
            ],
            "纳入或剔除理由",
        ),
    ],
)
def test_import_reviewed_file_rejects_approved_rows_without_phase_decision_fields(
    tmp_path: Path,
    reviewed_rows: list[dict[str, object]],
    error_match: str,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    reviewed_path = tmp_path / "invalid_approved.jsonl"
    _seed_staging_db(db_path)
    _write_jsonl(reviewed_path, reviewed_rows)

    with pytest.raises(ValueError, match=error_match):
        import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        post_status = connection.execute(
            "SELECT sample_status FROM posts WHERE post_id = 'p1'"
        ).fetchone()[0]
        review_runs = connection.execute("SELECT COUNT(*) FROM review_runs").fetchone()[0]
        reviewed_records = connection.execute(
            "SELECT COUNT(*) FROM reviewed_records"
        ).fetchone()[0]

    assert post_status == "review_needed"
    assert review_runs == 0
    assert reviewed_records == 0


def test_import_reviewed_file_preserves_multiple_rows_for_same_run_id(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    reviewed_path = tmp_path / "reviewed_same_run.jsonl"
    _seed_staging_db(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO posts (
                post_id, platform, legacy_crawl_status, post_date, sample_status,
                title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                import_batch_id
            ) VALUES (
                'p2', 'xiaohongshu', 'crawled', '2025-01-17', 'review_needed',
                '标题2', '第二个帖子', '[]', '[]', '[]', 1
            )
            """
        )
        connection.commit()

    _write_jsonl(
        reviewed_path,
        [
            {
                "run_id": "run-post-review-v2-batch",
                "review_phase": "post_review_v2",
                "review_status": "reviewed",
                "reviewer": "human-a",
                "review_date": "2026-04-24",
                "post_id": "p1",
                "decision": "纳入",
                "decision_reason": ["R12: 明确展示 AI 进入研究问题定义环节。"],
                "source_text": "研究生分享如何用 ChatGPT 讨论课题方向。",
                "workflow_dimension": {
                    "primary_dimension": ["A1"],
                    "secondary_stage": ["A1.1"],
                    "evidence": ["用 ChatGPT 讨论课题方向。"],
                },
                "legitimacy_evaluation": {
                    "direction": ["B0"],
                    "basis": ["C1"],
                    "evidence": ["提升选题效率。"],
                },
                "claim_units": [
                    {
                        "practice_unit": "AI辅助研究构思",
                        "workflow_stage_codes": ["A1.1"],
                        "legitimacy_codes": ["B0"],
                        "basis_codes": [{"code": "C1", "evidence": "提升选题效率。"}],
                        "boundary_codes": [],
                        "boundary_mode_codes": [],
                        "evidence": ["用 ChatGPT 讨论课题方向。"],
                    }
                ],
            },
            {
                "run_id": "run-post-review-v2-batch",
                "review_phase": "post_review_v2",
                "review_status": "reviewed",
                "reviewer": "human-a",
                "review_date": "2026-04-24",
                "post_id": "p2",
                "decision": "剔除",
                "decision_reason": ["R1: 未明确提及 AI 或 AI 工具。"],
                "source_text": "第二个帖子不涉及AI。",
                "theme_summary": "第二个帖子",
            },
        ],
    )

    import_reviewed_file(reviewed_path=reviewed_path, db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        reviewed_records = connection.execute(
            "SELECT COUNT(*) FROM reviewed_records WHERE run_id = 'run-post-review-v2-batch'"
        ).fetchone()[0]
        review_runs = connection.execute(
            "SELECT COUNT(*) FROM review_runs WHERE run_id = 'run-post-review-v2-batch'"
        ).fetchone()[0]
        claim_units = connection.execute(
            """
            SELECT COUNT(*)
            FROM claim_units
            WHERE record_type = 'post' AND record_id IN ('p1', 'p2')
            """
        ).fetchone()[0]

    assert review_runs == 1
    assert reviewed_records == 2
    assert claim_units == 1


def test_prepare_review_batches_creates_batch_files_review_template_and_memo(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    _seed_staging_db(db_path)

    with sqlite3.connect(db_path) as connection:
        for index in range(2, 4):
            connection.execute(
                """
                INSERT INTO posts (
                    post_id, platform, legacy_crawl_status, post_date, sample_status,
                    title, content_text, ai_tools_json, risk_themes_json, benefit_themes_json,
                    import_batch_id
                ) VALUES (?, 'xiaohongshu', 'crawled', ?, 'review_needed', ?, ?, '[]', '[]', '[]', 1)
                """,
                (
                    f"p{index}",
                    f"2025-01-1{4 + index}",
                    f"标题{index}",
                    f"重新审查这个帖子 {index}",
                ),
            )
        connection.commit()

    manifest_path = prepare_review_batches(
        db_path=db_path,
        phase="rescreen_posts",
        batch_size=2,
        reviewer="guoyufan",
        queue_dir=tmp_path / "queues",
        reviewed_dir=tmp_path / "reviewed",
        memos_dir=tmp_path / "memos",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["phase"] == "rescreen_posts"
    assert manifest["row_count"] == 3
    assert manifest["batch_count"] == 2
    assert manifest["preflight"]["counts"] == {
        "posts": 3,
        "comments": 1,
        "codes": 0,
        "paper_scope_posts": 0,
        "paper_scope_comments": 0,
    }
    assert [batch["row_count"] for batch in manifest["batches"]] == [2, 1]

    queue_path = Path(manifest["queue_path"])
    batch0_path = Path(manifest["batches"][0]["path"])
    batch1_path = Path(manifest["batches"][1]["path"])
    review_template_path = Path(manifest["review_template_path"])
    memo_template_path = Path(manifest["memo_template_path"])

    assert queue_path.exists()
    assert batch0_path.exists()
    assert batch1_path.exists()
    assert review_template_path.exists()
    assert memo_template_path.exists()

    batch0_rows = _load_jsonl(batch0_path)
    batch1_rows = _load_jsonl(batch1_path)
    review_template_rows = _load_jsonl(review_template_path)
    memo_text = memo_template_path.read_text(encoding="utf-8")

    assert [row["post_id"] for row in batch0_rows] == ["p1", "p2"]
    assert [row["post_id"] for row in batch1_rows] == ["p3"]
    assert all(row["run_id"] == "qv5_rescreen_batch_00" for row in review_template_rows)
    assert all(row["review_phase"] == "rescreen_posts" for row in review_template_rows)
    assert all(row["review_status"] == "unreviewed" for row in review_template_rows)
    assert all(row["reviewer"] == "guoyufan" for row in review_template_rows)
    assert "研究相关但宣传账号" in memo_text
    assert "qv5_rescreen_batch_00" in memo_text


def test_prepare_review_batches_post_review_v2_includes_structured_template_and_self_check_memo(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    _seed_staging_db(db_path)

    manifest_path = prepare_review_batches(
        db_path=db_path,
        phase="post_review_v2",
        batch_size=2,
        reviewer="guoyufan",
        queue_dir=tmp_path / "queues",
        reviewed_dir=tmp_path / "reviewed",
        memos_dir=tmp_path / "memos",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    review_template_path = Path(manifest["review_template_path"])
    memo_template_path = Path(manifest["memo_template_path"])

    review_template_rows = _load_jsonl(review_template_path)
    memo_text = memo_template_path.read_text(encoding="utf-8")

    assert review_template_rows[0]["review_phase"] == "post_review_v2"
    assert review_template_rows[0]["workflow_dimension"] == {
        "primary_dimension": [],
        "secondary_stage": [],
        "evidence": [],
    }
    assert review_template_rows[0]["legitimacy_evaluation"] == {
        "direction": [],
        "basis": [],
        "evidence": [],
    }
    assert review_template_rows[0]["boundary_expression"] == {
        "present": "否",
        "boundary_content_codes": [],
        "boundary_expression_mode_codes": [],
        "evidence": [],
    }
    assert review_template_rows[0]["claim_unit_template"]["ai_intervention_mode_codes"] == []
    assert review_template_rows[0]["claim_unit_template"]["boundary_result_codes"] == []
    assert "1. 话语情境" in memo_text
    assert "2. 实践位置" in memo_text
    assert "5. 边界生成" in memo_text
    assert "F/G/H/I/J/K 只能作为人工 reviewed draft/正式字段保留" in memo_text


def test_quality_v4_audit_snapshot_falls_back_to_active_views_when_qv4_views_absent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "staging.sqlite3"
    checkpoint_path = tmp_path / "quality_v4_checkpoint.json"
    output_path = tmp_path / "quality_v4_audit_snapshot.json"
    _seed_staging_db(db_path)

    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_stage": "quality_v4",
                "formal_posts": 0,
                "formal_comments": 0,
                "queued": 1,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    snapshot_path = export_quality_v4_audit_snapshot(
        db_path=db_path,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
    )
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot["view_source"] == {
        "posts": "vw_posts_paper_scope_quality_v5",
        "comments": "vw_comments_paper_scope_quality_v5",
    }
    assert snapshot["formal_ids"]["posts"] == []
    assert snapshot["formal_ids"]["comments"] == []
