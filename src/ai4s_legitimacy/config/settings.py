from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATABASE_DIR = PROJECT_ROOT / "database"
REPORTS_DIR = OUTPUTS_DIR / "reports"
FREEZE_CHECKPOINTS_DIR = REPORTS_DIR / "freeze_checkpoints"

LEGACY_RUNTIME_DIR = PROJECT_ROOT / "archive" / "legacy_collection_runtime"
LEGACY_DB_PATH = LEGACY_RUNTIME_DIR / "data" / "db" / "ai4s_xhs.sqlite3"
LEGACY_QUERY_TEMPLATE = EXTERNAL_DIR / "query_dictionary_template_legacy.json"

RESEARCH_DB_PATH = PROCESSED_DIR / "ai4s_legitimacy.sqlite3"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
VIEWS_TEMPLATE_PATH = DATABASE_DIR / "views.sql.template"
VIEWS_PATH = DATABASE_DIR / "views.sql"

QUALITY_V4_CHECKPOINT = (
    OUTPUTS_DIR / "reports" / "freeze_checkpoints" / "quality_v4_freeze_checkpoint.json"
)
QUALITY_V4_PAPER_RESULTS = (
    OUTPUTS_DIR / "reports" / "paper_materials" / "paper_results_snapshot.md"
)
RESEARCH_DB_SUMMARY_PATH = FREEZE_CHECKPOINTS_DIR / "research_db_summary.json"
QUALITY_V4_CONSISTENCY_REPORT_PATH = (
    FREEZE_CHECKPOINTS_DIR / "quality_v4_consistency_report.json"
)

PLATFORM_CODE = "xiaohongshu"
PLATFORM_NAME = "小红书"

PAPER_FIGURES_SUBMISSION_DIRNAME = "paper_figures_submission"
