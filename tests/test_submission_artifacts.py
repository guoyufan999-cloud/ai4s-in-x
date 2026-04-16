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
        ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v4" / "paper_figures_submission_manifest.md",
        ROOT / "outputs" / "reports" / "freeze_checkpoints" / "quality_v4_freeze_checkpoint.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "quality_v4_evidence_matrix.md",
    ]
    for path in text_targets:
        text = path.read_text(encoding="utf-8")
        assert "data/exports" not in text


def test_paper_materials_manifest_uses_outputs_paths_and_source_contract() -> None:
    manifest_path = ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["coverage_end_date"] == "2026-04-10"
    assert "generated_at" not in manifest
    assert "chapter_draft_path" not in manifest
    assert "discussion_draft_path" not in manifest
    assert "conclusion_draft_path" not in manifest
    assert "master_draft_path" not in manifest
    assert "llm_enabled" not in manifest
    assert "llm_manifest_path" not in manifest
    assert manifest["formal_source_contract"]["core_results"] == "paper_scope_quality_v4"
    assert manifest["formal_source_contract"]["tools_and_risk_figures"] == "paper_scope_quality_v4"
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
    manifest_path = ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v4" / "paper_figures_submission_manifest.md"
    text = manifest_path.read_text(encoding="utf-8")
    assert "`paper_scope_quality_v4`" in text
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
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "paper_scope_quality_v4" not in text
        assert "legacy_bridge_temp" not in text
        assert "data/exports" not in text


def test_appendix_assets_and_clean_manuscript_reference_exist() -> None:
    manifest_path = ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    appendix_internal = Path(manifest["methods_transparency_appendix_path"])
    appendix_clean = Path(manifest["methods_transparency_appendix_clean_path"])
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
        / "quality_v4"
        / "paper_figures_submission_manifest.md"
    ).read_text(encoding="utf-8")
    summary_payload = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "research_db_summary.json").read_text(encoding="utf-8")
    )
    consistency_report = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "quality_v4_consistency_report.json").read_text(encoding="utf-8")
    )

    assert materials_manifest["coverage_end_date"] == "2026-04-10"
    assert summary_payload["paper_quality_v4"]["coverage_end_date"] == "2026-04-10"
    assert analysis_snapshot["coverage_end_date"] == "2026-04-10"
    assert collection_snapshot["coverage_end_date"] == "2026-04-10"
    assert collection_snapshot["research_window"]["coverage_end_date"] == "2026-04-10"
    assert "generated_at" not in analysis_snapshot
    assert "as_of_date" not in analysis_snapshot
    assert "as_of_date" not in collection_snapshot
    assert "generated_at_utc" not in consistency_report
    assert "- 正式覆盖截止日：`2026-04-10`" in figure_manifest_text


def test_active_artifacts_use_repo_relative_paths_and_new_freeze_checkpoint_locations() -> None:
    assert (FREEZE_CHECKPOINTS_DIR / "research_db_summary.json").exists()
    assert (FREEZE_CHECKPOINTS_DIR / "quality_v4_consistency_report.json").exists()
    assert not (ROOT / "data" / "processed" / "research_db_summary.json").exists()
    assert not (ROOT / "data" / "interim" / "quality_v4_consistency_report.json").exists()

    freeze_checkpoint_json = json.loads(
        (FREEZE_CHECKPOINTS_DIR / "quality_v4_freeze_checkpoint.json").read_text(encoding="utf-8")
    )
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
        FREEZE_CHECKPOINTS_DIR / "quality_v4_consistency_report.json",
        FREEZE_CHECKPOINTS_DIR / "quality_v4_freeze_checkpoint.json",
        FREEZE_CHECKPOINTS_DIR / "quality_v4_freeze_checkpoint.md",
        ROOT / "outputs" / "figures" / "paper_figures_submission" / "quality_v4" / "paper_figures_submission_manifest.md",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_materials_manifest.json",
        ROOT / "outputs" / "reports" / "paper_materials" / "paper_results_snapshot.md",
    ]
    for path in targets:
        assert "/Users/guoyufan/ai4s in xhs" not in path.read_text(encoding="utf-8")


def test_freeze_checkpoint_markdown_is_stable_and_formal_only() -> None:
    text = (FREEZE_CHECKPOINTS_DIR / "quality_v4_freeze_checkpoint.md").read_text(encoding="utf-8")
    assert "生成时间" not in text
    assert "docs/paper_working/README.md" in text
    assert "不属于 freeze contract" in text


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
