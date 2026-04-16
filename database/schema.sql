PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_name TEXT NOT NULL UNIQUE,
    source_description TEXT NOT NULL,
    source_db_path TEXT,
    source_freeze_version TEXT,
    migrated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    record_post_count INTEGER NOT NULL DEFAULT 0,
    record_comment_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS platform_sources (
    platform_code TEXT PRIMARY KEY,
    platform_name TEXT NOT NULL,
    public_scope_note TEXT,
    compliance_note TEXT
);

CREATE TABLE IF NOT EXISTS source_queries (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_code TEXT NOT NULL,
    query_text TEXT NOT NULL,
    query_layer TEXT,
    source_label TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_code, query_text),
    FOREIGN KEY(platform_code) REFERENCES platform_sources(platform_code)
);

CREATE TABLE IF NOT EXISTS workflow_stage_lookup (
    stage_code TEXT PRIMARY KEY,
    stage_name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    definition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legitimacy_dimension_lookup (
    dimension_code TEXT PRIMARY KEY,
    dimension_name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    definition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    legacy_note_id TEXT UNIQUE,
    legacy_crawl_status TEXT NOT NULL DEFAULT 'unknown',
    post_url TEXT,
    author_id_hashed TEXT,
    author_name_masked TEXT,
    post_date TEXT,
    capture_date TEXT,
    title TEXT,
    content_text TEXT,
    engagement_like INTEGER,
    engagement_comment INTEGER,
    engagement_collect INTEGER,
    keyword_query TEXT,
    is_public INTEGER NOT NULL DEFAULT 1 CHECK (is_public IN (0, 1)),
    sample_status TEXT NOT NULL DEFAULT 'review_needed' CHECK (sample_status IN ('true', 'false', 'review_needed')),
    actor_type TEXT,
    qs_broad_subject TEXT,
    workflow_stage TEXT,
    primary_legitimacy_stance TEXT,
    risk_themes_json TEXT,
    ai_tools_json TEXT,
    benefit_themes_json TEXT,
    import_batch_id INTEGER,
    notes TEXT,
    FOREIGN KEY(import_batch_id) REFERENCES import_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_sample_status ON posts(sample_status);
CREATE INDEX IF NOT EXISTS idx_posts_qs_broad_subject ON posts(qs_broad_subject);
CREATE INDEX IF NOT EXISTS idx_posts_workflow_stage ON posts(workflow_stage);
CREATE INDEX IF NOT EXISTS idx_posts_post_date ON posts(post_date);
CREATE INDEX IF NOT EXISTS idx_posts_legacy_crawl_status ON posts(legacy_crawl_status);

CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    parent_comment_id TEXT,
    comment_date TEXT,
    comment_text TEXT NOT NULL,
    commenter_id_hashed TEXT,
    stance TEXT,
    legitimacy_basis TEXT,
    benefit_themes_json TEXT,
    is_reply INTEGER NOT NULL DEFAULT 0 CHECK (is_reply IN (0, 1)),
    import_batch_id INTEGER,
    FOREIGN KEY(post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY(import_batch_id) REFERENCES import_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_comment_date ON comments(comment_date);
CREATE INDEX IF NOT EXISTS idx_comments_legitimacy_basis ON comments(legitimacy_basis);

CREATE TABLE IF NOT EXISTS codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL CHECK (record_type IN ('post', 'comment')),
    parent_id TEXT,
    workflow_stage_code TEXT,
    ai_practice_code TEXT,
    legitimacy_code TEXT,
    boundary_negotiation_code TEXT,
    coder TEXT NOT NULL,
    coding_date TEXT NOT NULL,
    confidence REAL,
    memo TEXT
);

CREATE INDEX IF NOT EXISTS idx_codes_record ON codes(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_codes_workflow_stage_code ON codes(workflow_stage_code);
CREATE INDEX IF NOT EXISTS idx_codes_legitimacy_code ON codes(legitimacy_code);
CREATE INDEX IF NOT EXISTS idx_codes_boundary_negotiation_code ON codes(boundary_negotiation_code);

CREATE TABLE IF NOT EXISTS codebook (
    code_id TEXT PRIMARY KEY,
    code_group TEXT NOT NULL,
    code_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    include_rule TEXT,
    exclude_rule TEXT,
    example TEXT
);

CREATE INDEX IF NOT EXISTS idx_codebook_group ON codebook(code_group);

CREATE TABLE IF NOT EXISTS ai_tools_lookup (
    tool_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    category TEXT,
    display_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS risk_themes_lookup (
    risk_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS benefit_themes_lookup (
    benefit_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0
);
