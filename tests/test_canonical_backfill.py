from __future__ import annotations

import json
from pathlib import Path

from ai4s_legitimacy.collection.canonical_backfill import backfill_canonical_history


def test_backfill_canonical_history_migrates_legacy_note_and_preserves_summary_json(
    tmp_path: Path,
) -> None:
    tables_dir = tmp_path / "tables"
    archive_dir = tmp_path / "archive"
    tables_dir.mkdir()
    archive_dir.mkdir()

    canonical_path = tables_dir / "canonical.jsonl"
    canonical_path.write_text(
        json.dumps(
            {
                "record_type": "post",
                "record_id": "p1",
                "post_id": "p1",
                "platform": "xiaohongshu",
                "post_url": "",
                "author_id": "",
                "created_at": "",
                "language": "zh",
                "thread_id": "",
                "parent_post_id": "",
                "reply_to_post_id": "",
                "quoted_post_id": "",
                "context_available": "否",
                "context_used": "none",
                "source_text": "AI 辅助文献综述，需要人工核查。",
                "context_text": "",
                "decision": "纳入",
                "decision_reason": ["R12: 明确 AI 进入具体科研环节。"],
                "theme_summary": "AI辅助文献综述",
                "target_practice_summary": "AI辅助文献综述",
                "evidence_master": ["AI 辅助文献综述，需要人工核查。"],
                "discursive_mode": "experience_share",
                "practice_status": "actual_use",
                "speaker_position_claimed": "graduate_student",
                "workflow_dimension": {
                    "primary_dimension": ["A1"],
                    "secondary_stage": ["A1.2"],
                    "evidence": ["AI 辅助文献综述，需要人工核查。"],
                },
                "legitimacy_evaluation": {
                    "direction": ["B2"],
                    "basis": ["C8"],
                    "evidence": ["需要人工核查。"],
                },
                "boundary_expression": {
                    "present": "是",
                    "boundary_content_codes": ["D1.10"],
                    "boundary_expression_mode_codes": ["D2.5"],
                    "evidence": ["需要人工核查。"],
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
                "claim_units": [
                    {
                        "practice_unit": "AI辅助文献综述",
                        "workflow_stage_codes": ["A1.2"],
                        "legitimacy_codes": ["B2"],
                        "basis_codes": [{"code": "C8", "evidence": "需要人工核查。"}],
                        "boundary_codes": [{"code": "D1.10", "evidence": "需要人工核查。"}],
                        "boundary_mode_codes": [{"code": "D2.5", "evidence": "需要人工核查。"}],
                        "evidence": ["AI 辅助文献综述，需要人工核查。"],
                    }
                ],
                "mechanism_memo": {
                    "eligible_for_mechanism_analysis": "待定",
                    "candidate_pattern_notes": ["单帖边界表达可用于后续比较。"],
                    "comparison_keys": ["A1.2", "B2", "D1.10"],
                },
                "api_assistance": {
                    "used": "否",
                    "purpose": [],
                    "api_confidence": "无",
                    "adoption_note": "",
                },
                "notes": {
                    "multi_label": "否",
                    "ambiguity": "否",
                    "confidence": "高",
                    "review_points": [],
                    "dedup_group": "p1",
                },
                "review_status": "reviewed",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    legacy_note_path = archive_dir / "legacy_note.json"
    legacy_note_path.write_text(
        json.dumps(
            {
                "note_id": "legacy-1",
                "canonical_url": "https://www.xiaohongshu.com/explore/legacy-1",
                "title": "用 AI 做文献综述的经验",
                "sample_status": "true",
                "workflow_primary": "文献检索与综述",
                "qs_broad_subject": "Social Sciences & Management",
                "attitude_polarity": "积极但保留",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    summary_path = archive_dir / "summary.json"
    summary_path.write_text(
        json.dumps({"status": "ok", "count": 1}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = backfill_canonical_history(
        root_dirs=(tables_dir, archive_dir),
        manifest_path=tmp_path / "manifest.json",
    )

    assert manifest["converted_files"] == 2
    assert manifest["skipped_files"] == 0
    assert manifest["preserved_non_record_files"] == 1

    canonical_row = json.loads(canonical_path.read_text(encoding="utf-8").splitlines()[0])
    legacy_row = json.loads(legacy_note_path.read_text(encoding="utf-8").splitlines()[0])

    assert canonical_row["decision"] == "纳入"
    assert legacy_row["post_id"] == "legacy-1"
    assert legacy_row["decision"] == "纳入"
    assert legacy_row["workflow_dimension"]["secondary_stage"] == ["A1.2"]

    statuses = {entry["path"]: entry["status"] for entry in manifest["entries"]}
    assert statuses[str(summary_path)] == "preserved_non_record"
