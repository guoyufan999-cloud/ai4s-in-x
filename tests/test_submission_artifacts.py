from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
FREEZE_CHECKPOINTS_DIR = OUTPUTS_DIR / "reports" / "freeze_checkpoints"


def _resolve_repo_artifact_path(path_value: str) -> Path:
    candidate = Path(path_value)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _extract_markdown_image_paths(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)


def test_submission_manuscript_and_results_chapter_figure_paths_exist() -> None:
    targets = [
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn_clean.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        for image_path in _extract_markdown_image_paths(text):
            resolved = (path.parent / image_path).resolve()
            assert resolved.exists(), f"Missing image asset: {resolved}"
            assert OUTPUTS_DIR in resolved.parents, f"Image path should stay within outputs/: {resolved}"


def test_active_delivery_manifests_no_longer_point_to_data_exports() -> None:
    text_targets = [
        ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v5" / "paper_figures_submission_manifest.md",
        FREEZE_CHECKPOINTS_DIR / "quality_v5_freeze_checkpoint.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "quality_v5_post_only_contract.md",
    ]
    for path in text_targets:
        text = path.read_text(encoding="utf-8")
        assert "data/exports" not in text


def test_paper_materials_manifest_uses_outputs_paths_and_source_contract() -> None:
    manifest_path = ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["coverage_end_date"] == "2026-04-10"
    assert manifest["formal_stage"] == "quality_v5"
    assert manifest["status"] == "post_only_formal_scope"
    assert "comment_review_v2" in manifest["comment_scope_note"]
    assert "deferred" in manifest["comment_scope_note"]
    assert "generated_at" not in manifest
    assert "chapter_draft_path" not in manifest
    assert "discussion_draft_path" not in manifest
    assert "conclusion_draft_path" not in manifest
    assert "master_draft_path" not in manifest
    assert "llm_enabled" not in manifest
    assert "llm_manifest_path" not in manifest
    assert manifest["formal_source_contract"]["core_results"] == "paper_scope_quality_v5"
    assert manifest["formal_source_contract"]["tools_and_risk_figures"] == "paper_scope_quality_v5"
    assert not Path(manifest["submission_figure_dir"]).is_absolute()
    assert not Path(manifest["submission_figure_manifest_path"]).is_absolute()
    assert not Path(manifest["evidence_matrix_path"]).is_absolute()
    assert _resolve_repo_artifact_path(manifest["submission_figure_dir"]).exists()
    assert _resolve_repo_artifact_path(manifest["submission_figure_manifest_path"]).exists()
    assert _resolve_repo_artifact_path(manifest["evidence_matrix_path"]).exists()

    path_keys = [
        "abstract_submission_path",
        "abstract_submission_clean_path",
        "introduction_submission_path",
        "introduction_submission_clean_path",
        "submission_results_path",
        "submission_results_clean_path",
        "submission_methods_path",
        "submission_methods_clean_path",
        "methods_transparency_appendix_path",
        "methods_transparency_appendix_clean_path",
        "submission_master_path",
        "submission_master_clean_path",
        "discussion_submission_clean_path",
        "conclusion_submission_clean_path",
    ]
    for key in path_keys:
        assert not Path(manifest[key]).is_absolute()
        assert _resolve_repo_artifact_path(manifest[key]).exists()

    for chart_path in manifest["chart_paths"]:
        assert not Path(chart_path).is_absolute()
        assert _resolve_repo_artifact_path(chart_path).exists()


def test_figure_manifest_all_sources_are_paper_scope() -> None:
    manifest_path = ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v5" / "paper_figures_submission_manifest.md"
    text = manifest_path.read_text(encoding="utf-8")
    assert "`paper_scope_quality_v5`" in text
    assert "`legacy_bridge_temp`" not in text


def test_clean_submission_files_remove_internal_source_labels() -> None:
    targets = [
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_abstract_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_introduction_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_discussion_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_conclusion_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_transparency_appendix_cn_clean.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "paper_scope_quality_v5" not in text
        assert "legacy_bridge_temp" not in text
        assert "data/exports" not in text


def test_appendix_assets_and_clean_manuscript_reference_exist() -> None:
    manifest_path = ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    appendix_internal = _resolve_repo_artifact_path(manifest["methods_transparency_appendix_path"])
    appendix_clean = _resolve_repo_artifact_path(manifest["methods_transparency_appendix_clean_path"])
    manuscript_clean = ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn_clean.md"

    assert appendix_internal.exists()
    assert appendix_clean.exists()
    assert "data/exports" not in appendix_internal.read_text(encoding="utf-8")
    assert "data/exports" not in appendix_clean.read_text(encoding="utf-8")
    manuscript_text = manuscript_clean.read_text(encoding="utf-8")
    assert "方法透明度与补充材料说明" in manuscript_text


def test_reproducible_versioned_outputs_share_same_coverage_end_date() -> None:
    materials_manifest = json.loads(
        (ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    analysis_snapshot = json.loads(
        (ROOT / "outputs" / "reports" / "paper_materials" / "paper_analysis_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    collection_snapshot = json.loads(
        (ROOT / "outputs" / "reports" / "paper_materials" / "collection_status.snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    figure_manifest_text = (
        ROOT
        / "outputs"
        / "figures"
        / "paper_figures_submission"
        / "quality_v5"
        / "paper_figures_submission_manifest.md"
    ).read_text(encoding="utf-8")
    summary_payload = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "research_db_summary.json").read_text(encoding="utf-8")
    )
    consistency_report = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "quality_v5_consistency_report.json").read_text(encoding="utf-8")
    )

    assert materials_manifest["coverage_end_date"] == "2026-04-10"
    assert summary_payload["paper_quality_v5"]["coverage_end_date"] == "2026-04-10"
    assert analysis_snapshot["coverage_end_date"] == "2026-04-10"
    assert collection_snapshot["coverage_end_date"] == "2026-04-10"
    assert collection_snapshot["research_window"]["coverage_end_date"] == "2026-04-10"
    assert analysis_snapshot["status"] == "post_review_v2_imported_post_only"
    assert analysis_snapshot["formal_scope_counts"] == {"posts": 514, "comments": 0}
    assert collection_snapshot["status"] == "post_review_v2_imported_post_only"
    assert collection_snapshot["formal_scope"] == {"posts": 514, "comments": 0}
    assert collection_snapshot["canonical_corpus"] == {"posts": 5535, "comments": 12362}
    assert "generated_at" not in analysis_snapshot
    assert "as_of_date" not in analysis_snapshot
    assert "as_of_date" not in collection_snapshot
    assert "generated_at_utc" not in consistency_report
    assert "- 正式覆盖截止日：`2026-04-10`" in figure_manifest_text


def test_active_artifacts_use_repo_relative_paths_and_new_freeze_checkpoint_locations() -> None:
    assert (FREEZE_CHECKPOINTS_DIR / "research_db_summary.json").exists()
    assert (FREEZE_CHECKPOINTS_DIR / "quality_v5_consistency_report.json").exists()
    assert not (ROOT / "data" / "processed" / "research_db_summary.json").exists()
    assert not (ROOT / "data" / "interim" / "quality_v5_consistency_report.json").exists()

    freeze_checkpoint_json = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "quality_v5_freeze_checkpoint.json").read_text(encoding="utf-8")
    )
    assert freeze_checkpoint_json["status"] == "post_review_v2_imported_post_only"
    assert freeze_checkpoint_json["formal_posts"] == 514
    assert freeze_checkpoint_json["formal_comments"] == 0
    assert "deferred" in freeze_checkpoint_json["quality_watchlist"]["note"]
    assert "not a missing import" in freeze_checkpoint_json["quality_watchlist"][
        "formal_comments_zero_reason"
    ]
    assert "created_at" not in freeze_checkpoint_json
    assert not Path(freeze_checkpoint_json["collection_report_path"]).is_absolute()
    assert _resolve_repo_artifact_path(freeze_checkpoint_json["collection_report_path"]).exists()
    assert not Path(freeze_checkpoint_json["paper_materials"]["output_dir"]).is_absolute()
    assert _resolve_repo_artifact_path(freeze_checkpoint_json["paper_materials"]["manifest_path"]).exists()
    assert "chapter_draft_path" not in freeze_checkpoint_json["paper_materials"]
    assert "discussion_draft_path" not in freeze_checkpoint_json["paper_materials"]
    assert "conclusion_draft_path" not in freeze_checkpoint_json["paper_materials"]
    assert "master_draft_path" not in freeze_checkpoint_json["paper_materials"]
    assert "llm_enabled" not in freeze_checkpoint_json["paper_materials"]


def test_active_artifacts_do_not_embed_workspace_absolute_paths() -> None:
    targets = [
        FREEZE_CHECKPOINTS_DIR / "research_db_summary.json",
        FREEZE_CHECKPOINTS_DIR / "quality_v5_consistency_report.json",
        FREEZE_CHECKPOINTS_DIR / "quality_v5_freeze_checkpoint.json",
        FREEZE_CHECKPOINTS_DIR / "quality_v5_freeze_checkpoint.md",
        ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v5" / "paper_figures_submission_manifest.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT / "docs" / "canonical_backfill_contract.md",
    ]
    for path in targets:
        assert "/Users/guoyufan/ai4s in xhs" not in path.read_text(encoding="utf-8")


def test_freeze_checkpoint_markdown_is_stable_and_formal_only() -> None:
    text = (FREEZE_CHECKPOINTS_DIR / "quality_v5_freeze_checkpoint.md").read_text(encoding="utf-8")
    assert "生成时间" not in text
    assert "docs/paper_working/README.md" in text
    assert "不属于 freeze contract" in text
    assert "post-only artifact refresh" in text
    assert "`formal_comments=0` 是本轮设计选择" in text


def test_active_quality_v5_materials_use_post_only_contract() -> None:
    targets = [
        ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v5" / "README.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_abstract_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_abstract_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_analysis_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_introduction_submission_cn.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_introduction_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_master_manuscript_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_methods_limitations_submission_cn_clean.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_methods_transparency_appendix_cn.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_methods_transparency_appendix_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_results_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_discussion_chapter_submission_cn_clean.md",
        ROOT
        / "outputs"
        / "reports"
        / "paper_materials"
        / "paper_conclusion_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "quality_v5_post_only_contract.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "当前状态：`post_review_v2_imported_post_only`" in text
        assert "当前正式帖子 / 正式评论：`514 / 0`" in text
        assert "pending_reviewed_import" not in text
        assert "当前正式帖子 / 正式评论：`0 / 0`" not in text
        assert "评论 `27408` 条" not in text
        assert "尚未完成前" not in text


def test_active_text_materials_keep_current_canonical_corpus_counts() -> None:
    targets = [
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_abstract_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_abstract_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_analysis_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_introduction_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_introduction_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_transparency_appendix_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_transparency_appendix_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_discussion_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_conclusion_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "quality_v5_post_only_contract.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "当前 canonical corpus：帖子 `5535` 条，评论 `12362` 条" in text


def test_zero_byte_smoke_outputs_are_moved_out_of_formal_tables() -> None:
    smoke_names = [
        "external_xhs_ai4s_smoketest.jsonl",
        "external_xhs_ai4s_smoketest_after_login.jsonl",
        "external_xhs_ai4s_smoketest_after_patch.jsonl",
        "external_xhs_ai4s_smoketest_after_patch2.jsonl",
    ]
    residue_manifest = json.loads(
        (ROOT / "outputs" / "reports" / "review_v2" / "smoke_residue_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert residue_manifest["status"] == "historical_smoke_residue"
    assert residue_manifest["residue_dir"] == "outputs/reports/review_v2/smoke_residue"

    manifest_paths = {item["path"] for item in residue_manifest["files"]}
    for name in smoke_names:
        assert not (ROOT / "outputs" / "tables" / name).exists()
        residue_path = ROOT / "outputs" / "reports" / "review_v2" / "smoke_residue" / name
        assert residue_path.exists()
        assert residue_path.stat().st_size == 0
        assert f"outputs/reports/review_v2/smoke_residue/{name}" in manifest_paths


def test_active_paper_materials_distinguish_research_window_and_coverage_cutoff() -> None:
    targets = [
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_analysis_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_master_manuscript_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_methods_limitations_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_chapter_submission_cn_clean.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_conclusion_chapter_submission_cn_clean.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "2024-01-01" in text
        assert "2026-06-30" in text
        assert "2026-04-10" in text
        assert "正式覆盖截止日" in text


def test_versioned_excerpts_do_not_include_generation_timestamp() -> None:
    excerpt_dir = ROOT / "outputs" / "excerpts"
    for path in excerpt_dir.glob("*.md"):
        assert "生成时间：" not in path.read_text(encoding="utf-8")
