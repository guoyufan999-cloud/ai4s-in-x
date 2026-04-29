from __future__ import annotations

from pathlib import Path

from ai4s_legitimacy.config.settings import (
    FREEZE_CHECKPOINTS_DIR,
    INTERIM_DIR,
    OUTPUTS_DIR,
    RESEARCH_DB_PATH,
)

ACTIVE_FORMAL_STAGE = "quality_v5"
LEGACY_AUDIT_STAGE = "quality_v4"
QUALITY_V6_STAGE = "quality_v6"

ACTIVE_FORMAL_LABEL = f"{ACTIVE_FORMAL_STAGE} 正式重建基线"
LEGACY_AUDIT_LABEL = f"{LEGACY_AUDIT_STAGE} 审计快照"

ACTIVE_FORMAL_SUMMARY_KEY = f"paper_{ACTIVE_FORMAL_STAGE}"
ACTIVE_FORMAL_SOURCE_CONTRACT = f"paper_scope_{ACTIVE_FORMAL_STAGE}"
ACTIVE_FORMAL_SCOPE_POSTS_KEY = f"paper_{ACTIVE_FORMAL_STAGE}_posts"
ACTIVE_FORMAL_SCOPE_COMMENTS_KEY = f"paper_{ACTIVE_FORMAL_STAGE}_comments"

ACTIVE_CHECKPOINT_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{ACTIVE_FORMAL_STAGE}_freeze_checkpoint.json"
)
ACTIVE_CHECKPOINT_MARKDOWN_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{ACTIVE_FORMAL_STAGE}_freeze_checkpoint.md"
)
ACTIVE_CONSISTENCY_REPORT_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{ACTIVE_FORMAL_STAGE}_consistency_report.json"
)
ACTIVE_ARTIFACT_PROVENANCE_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{ACTIVE_FORMAL_STAGE}_artifact_provenance.json"
)
LEGACY_AUDIT_SNAPSHOT_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{LEGACY_AUDIT_STAGE}_audit_snapshot.json"
)

ACTIVE_FIGURE_DIR = (
    OUTPUTS_DIR / "figures" / "paper_figures_submission" / ACTIVE_FORMAL_STAGE
)
QUALITY_V6_FIGURE_DIR = (
    OUTPUTS_DIR / "figures" / "paper_figures_submission" / QUALITY_V6_STAGE
)

QUALITY_V6_DIR = INTERIM_DIR / QUALITY_V6_STAGE
QUALITY_V6_STAGING_DB_PATH = QUALITY_V6_DIR / "ai4s_legitimacy_quality_v6.sqlite3"
QUALITY_V6_FREEZE_CHECKPOINT_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{QUALITY_V6_STAGE}_freeze_checkpoint.json"
)
QUALITY_V6_FREEZE_CHECKPOINT_MARKDOWN_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{QUALITY_V6_STAGE}_freeze_checkpoint.md"
)
QUALITY_V6_CONSISTENCY_REPORT_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{QUALITY_V6_STAGE}_consistency_report.json"
)
QUALITY_V6_ARTIFACT_PROVENANCE_PATH = (
    FREEZE_CHECKPOINTS_DIR / f"{QUALITY_V6_STAGE}_artifact_provenance.json"
)
QUALITY_V6_PAPER_MATERIALS_DIR = (
    OUTPUTS_DIR / "reports" / "paper_materials" / QUALITY_V6_STAGE
)

REBASELINE_DIR = INTERIM_DIR / f"rebaseline_{ACTIVE_FORMAL_STAGE}"
REBASELINE_SUGGESTIONS_DIR = REBASELINE_DIR / "suggestions"
REBASELINE_REVIEW_QUEUE_DIR = REBASELINE_DIR / "review_queues"
REBASELINE_REVIEWED_DIR = REBASELINE_DIR / "reviewed"
REBASELINE_MEMOS_DIR = REBASELINE_DIR / "memos"
REBASELINE_STAGING_DB_PATH = RESEARCH_DB_PATH


def paper_scope_contract_name(stage: str = ACTIVE_FORMAL_STAGE) -> str:
    return f"paper_scope_{stage}"


def paper_scope_view(entity: str, stage: str = ACTIVE_FORMAL_STAGE) -> str:
    return f"vw_{entity}_paper_scope_{stage}"


def paper_quality_view(name: str, stage: str = ACTIVE_FORMAL_STAGE) -> str:
    return f"vw_paper_{stage}_{name}"


def stage_figure_dir(stage: str) -> Path:
    return OUTPUTS_DIR / "figures" / "paper_figures_submission" / stage
