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
    query_layer TEXT NOT NULL DEFAULT 'unspecified',
    source_label TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_code, query_text, query_layer, source_label),
    FOREIGN KEY(platform_code) REFERENCES platform_sources(platform_code)
);

CREATE TABLE IF NOT EXISTS workflow_domain_lookup (
    domain_code TEXT PRIMARY KEY,
    domain_name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    definition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_stage_lookup (
    stage_code TEXT PRIMARY KEY,
    stage_name TEXT NOT NULL,
    domain_code TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    definition TEXT NOT NULL,
    FOREIGN KEY(domain_code) REFERENCES workflow_domain_lookup(domain_code)
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
    decision_reason TEXT,
    actor_type TEXT,
    qs_broad_subject TEXT,
    workflow_domain TEXT CHECK (workflow_domain IN ('P', 'G', 'T') OR workflow_domain IS NULL),
    workflow_stage TEXT,
    primary_legitimacy_stance TEXT,
    has_legitimacy_evaluation INTEGER NOT NULL DEFAULT 0 CHECK (has_legitimacy_evaluation IN (0, 1)),
    primary_legitimacy_code TEXT,
    boundary_discussion INTEGER NOT NULL DEFAULT 0 CHECK (boundary_discussion IN (0, 1)),
    primary_boundary_type TEXT,
    uncertainty_note TEXT,
    risk_themes_json TEXT,
    ai_tools_json TEXT,
    benefit_themes_json TEXT,
    import_batch_id INTEGER,
    task_batch_id TEXT,
    coder_version TEXT,
    language TEXT,
    thread_id TEXT,
    parent_post_id TEXT,
    reply_to_post_id TEXT,
    quoted_post_id TEXT,
    context_available TEXT NOT NULL DEFAULT '否' CHECK (context_available IN ('是', '否')),
    context_used TEXT NOT NULL DEFAULT 'none' CHECK (context_used IN ('none', 'thread', 'quoted_post', 'reply_chain', 'user_provided_context')),
    decision TEXT NOT NULL DEFAULT '待复核' CHECK (decision IN ('纳入', '剔除', '待复核')),
    decision_reason_json TEXT NOT NULL DEFAULT '[]',
    theme_summary TEXT,
    target_practice_summary TEXT,
    evidence_master_json TEXT NOT NULL DEFAULT '[]',
    discursive_mode TEXT,
    practice_status TEXT,
    speaker_position_claimed TEXT,
    boundary_present TEXT NOT NULL DEFAULT '否' CHECK (boundary_present IN ('是', '否')),
    interaction_event_present TEXT NOT NULL DEFAULT '不适用' CHECK (interaction_event_present IN ('是', '否', '无法判断', '不适用')),
    interaction_role TEXT,
    interaction_target_claim_summary TEXT,
    interaction_event_codes_json TEXT NOT NULL DEFAULT '[]',
    interaction_event_basis_codes_json TEXT NOT NULL DEFAULT '[]',
    interaction_outcome TEXT,
    mechanism_eligible TEXT NOT NULL DEFAULT '否' CHECK (mechanism_eligible IN ('是', '否', '待定')),
    mechanism_notes_json TEXT NOT NULL DEFAULT '[]',
    comparison_keys_json TEXT NOT NULL DEFAULT '[]',
    api_assistance_used TEXT NOT NULL DEFAULT '否' CHECK (api_assistance_used IN ('是', '否')),
    api_assistance_purpose_json TEXT NOT NULL DEFAULT '[]',
    api_assistance_confidence TEXT NOT NULL DEFAULT '无' CHECK (api_assistance_confidence IN ('高', '中', '低', '无', '不可用')),
    api_assistance_note TEXT,
    notes_multi_label TEXT NOT NULL DEFAULT '否' CHECK (notes_multi_label IN ('是', '否')),
    notes_ambiguity TEXT NOT NULL DEFAULT '否' CHECK (notes_ambiguity IN ('是', '否')),
    notes_confidence TEXT NOT NULL DEFAULT '中' CHECK (notes_confidence IN ('高', '中', '低')),
    notes_review_points_json TEXT NOT NULL DEFAULT '[]',
    notes_dedup_group TEXT,
    review_status TEXT NOT NULL DEFAULT 'unreviewed' CHECK (review_status IN ('unreviewed', 'reviewed', 'revised', 'approved', 'pending_review')),
    notes TEXT,
    FOREIGN KEY(import_batch_id) REFERENCES import_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_sample_status ON posts(sample_status);
CREATE INDEX IF NOT EXISTS idx_posts_decision ON posts(decision);
CREATE INDEX IF NOT EXISTS idx_posts_review_status ON posts(review_status);
CREATE INDEX IF NOT EXISTS idx_posts_qs_broad_subject ON posts(qs_broad_subject);
CREATE INDEX IF NOT EXISTS idx_posts_workflow_domain ON posts(workflow_domain);
CREATE INDEX IF NOT EXISTS idx_posts_workflow_stage ON posts(workflow_stage);
CREATE INDEX IF NOT EXISTS idx_posts_post_date ON posts(post_date);
CREATE INDEX IF NOT EXISTS idx_posts_legacy_crawl_status ON posts(legacy_crawl_status);
CREATE INDEX IF NOT EXISTS idx_posts_primary_legitimacy_stance ON posts(primary_legitimacy_stance);
CREATE INDEX IF NOT EXISTS idx_posts_primary_legitimacy_code ON posts(primary_legitimacy_code);
CREATE INDEX IF NOT EXISTS idx_posts_boundary_discussion ON posts(boundary_discussion);

CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    parent_comment_id TEXT,
    comment_date TEXT,
    comment_text TEXT NOT NULL,
    commenter_id_hashed TEXT,
    stance TEXT,
    legitimacy_basis TEXT,
    workflow_domain TEXT CHECK (workflow_domain IN ('P', 'G', 'T') OR workflow_domain IS NULL),
    workflow_stage TEXT,
    has_legitimacy_evaluation INTEGER NOT NULL DEFAULT 0 CHECK (has_legitimacy_evaluation IN (0, 1)),
    primary_legitimacy_code TEXT,
    boundary_discussion INTEGER NOT NULL DEFAULT 0 CHECK (boundary_discussion IN (0, 1)),
    primary_boundary_type TEXT,
    uncertainty_note TEXT,
    benefit_themes_json TEXT,
    is_reply INTEGER NOT NULL DEFAULT 0 CHECK (is_reply IN (0, 1)),
    import_batch_id INTEGER,
    task_batch_id TEXT,
    coder_version TEXT,
    platform TEXT,
    post_url TEXT,
    language TEXT,
    thread_id TEXT,
    parent_post_id TEXT,
    reply_to_post_id TEXT,
    quoted_post_id TEXT,
    context_available TEXT NOT NULL DEFAULT '否' CHECK (context_available IN ('是', '否')),
    context_used TEXT NOT NULL DEFAULT 'none' CHECK (context_used IN ('none', 'thread', 'quoted_post', 'reply_chain', 'user_provided_context')),
    decision TEXT NOT NULL DEFAULT '待复核' CHECK (decision IN ('纳入', '剔除', '待复核')),
    decision_reason_json TEXT NOT NULL DEFAULT '[]',
    theme_summary TEXT,
    target_practice_summary TEXT,
    evidence_master_json TEXT NOT NULL DEFAULT '[]',
    discursive_mode TEXT,
    practice_status TEXT,
    speaker_position_claimed TEXT,
    boundary_present TEXT NOT NULL DEFAULT '否' CHECK (boundary_present IN ('是', '否')),
    interaction_event_present TEXT NOT NULL DEFAULT '不适用' CHECK (interaction_event_present IN ('是', '否', '无法判断', '不适用')),
    interaction_role TEXT,
    interaction_target_claim_summary TEXT,
    interaction_event_codes_json TEXT NOT NULL DEFAULT '[]',
    interaction_event_basis_codes_json TEXT NOT NULL DEFAULT '[]',
    interaction_outcome TEXT,
    mechanism_eligible TEXT NOT NULL DEFAULT '否' CHECK (mechanism_eligible IN ('是', '否', '待定')),
    mechanism_notes_json TEXT NOT NULL DEFAULT '[]',
    comparison_keys_json TEXT NOT NULL DEFAULT '[]',
    api_assistance_used TEXT NOT NULL DEFAULT '否' CHECK (api_assistance_used IN ('是', '否')),
    api_assistance_purpose_json TEXT NOT NULL DEFAULT '[]',
    api_assistance_confidence TEXT NOT NULL DEFAULT '无' CHECK (api_assistance_confidence IN ('高', '中', '低', '无', '不可用')),
    api_assistance_note TEXT,
    notes_multi_label TEXT NOT NULL DEFAULT '否' CHECK (notes_multi_label IN ('是', '否')),
    notes_ambiguity TEXT NOT NULL DEFAULT '否' CHECK (notes_ambiguity IN ('是', '否')),
    notes_confidence TEXT NOT NULL DEFAULT '中' CHECK (notes_confidence IN ('高', '中', '低')),
    notes_review_points_json TEXT NOT NULL DEFAULT '[]',
    notes_dedup_group TEXT,
    review_status TEXT NOT NULL DEFAULT 'unreviewed' CHECK (review_status IN ('unreviewed', 'reviewed', 'revised', 'approved', 'pending_review')),
    FOREIGN KEY(post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY(import_batch_id) REFERENCES import_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_decision ON comments(decision);
CREATE INDEX IF NOT EXISTS idx_comments_review_status ON comments(review_status);
CREATE INDEX IF NOT EXISTS idx_comments_comment_date ON comments(comment_date);
CREATE INDEX IF NOT EXISTS idx_comments_stance ON comments(stance);
CREATE INDEX IF NOT EXISTS idx_comments_legitimacy_basis ON comments(legitimacy_basis);
CREATE INDEX IF NOT EXISTS idx_comments_workflow_domain ON comments(workflow_domain);
CREATE INDEX IF NOT EXISTS idx_comments_workflow_stage ON comments(workflow_stage);
CREATE INDEX IF NOT EXISTS idx_comments_primary_legitimacy_code ON comments(primary_legitimacy_code);
CREATE INDEX IF NOT EXISTS idx_comments_boundary_discussion ON comments(boundary_discussion);

CREATE TABLE IF NOT EXISTS review_runs (
    run_id TEXT PRIMARY KEY,
    review_phase TEXT NOT NULL,
    model TEXT,
    reviewer TEXT NOT NULL,
    review_date TEXT NOT NULL,
    source_file TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS reviewed_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL CHECK (record_type IN ('post', 'comment', 'reply')),
    review_phase TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES review_runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, record_type, record_id, review_phase)
);

CREATE INDEX IF NOT EXISTS idx_reviewed_records_phase ON reviewed_records(review_phase, record_type);
CREATE INDEX IF NOT EXISTS idx_reviewed_records_record ON reviewed_records(record_type, record_id);

CREATE TABLE IF NOT EXISTS codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL CHECK (record_type IN ('post', 'comment', 'reply')),
    parent_id TEXT,
    workflow_domain_code TEXT,
    workflow_stage_code TEXT,
    ai_practice_code TEXT,
    legitimacy_code TEXT,
    boundary_discussion INTEGER NOT NULL DEFAULT 0 CHECK (boundary_discussion IN (0, 1)),
    boundary_negotiation_code TEXT,
    boundary_type_code TEXT,
    coder TEXT NOT NULL,
    coding_date TEXT NOT NULL,
    confidence REAL,
    memo TEXT
);

CREATE INDEX IF NOT EXISTS idx_codes_record ON codes(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_codes_workflow_domain_code ON codes(workflow_domain_code);
CREATE INDEX IF NOT EXISTS idx_codes_workflow_stage_code ON codes(workflow_stage_code);
CREATE INDEX IF NOT EXISTS idx_codes_ai_practice_code ON codes(ai_practice_code);
CREATE INDEX IF NOT EXISTS idx_codes_legitimacy_code ON codes(legitimacy_code);
CREATE INDEX IF NOT EXISTS idx_codes_boundary_negotiation_code ON codes(boundary_negotiation_code);
CREATE INDEX IF NOT EXISTS idx_codes_boundary_type_code ON codes(boundary_type_code);

CREATE TABLE IF NOT EXISTS claim_units (
    record_type TEXT NOT NULL CHECK (record_type IN ('post', 'comment', 'reply')),
    record_id TEXT NOT NULL,
    claim_index INTEGER NOT NULL,
    practice_unit TEXT,
    workflow_stage_codes_json TEXT NOT NULL DEFAULT '[]',
    legitimacy_codes_json TEXT NOT NULL DEFAULT '[]',
    basis_codes_json TEXT NOT NULL DEFAULT '[]',
    boundary_codes_json TEXT NOT NULL DEFAULT '[]',
    boundary_mode_codes_json TEXT NOT NULL DEFAULT '[]',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (record_type, record_id, claim_index)
);

CREATE INDEX IF NOT EXISTS idx_claim_units_record ON claim_units(record_type, record_id);

CREATE TABLE IF NOT EXISTS interaction_events (
    record_type TEXT NOT NULL CHECK (record_type IN ('post', 'comment', 'reply')),
    record_id TEXT NOT NULL,
    event_present TEXT NOT NULL DEFAULT '不适用' CHECK (event_present IN ('是', '否', '无法判断', '不适用')),
    interaction_role TEXT,
    target_claim_summary TEXT,
    event_codes_json TEXT NOT NULL DEFAULT '[]',
    event_basis_codes_json TEXT NOT NULL DEFAULT '[]',
    event_outcome TEXT,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (record_type, record_id)
);

CREATE TRIGGER IF NOT EXISTS trg_codes_validate_post_insert
BEFORE INSERT ON codes
WHEN NEW.record_type = 'post'
  AND NOT EXISTS (SELECT 1 FROM posts WHERE post_id = NEW.record_id)
BEGIN
    SELECT RAISE(ABORT, 'codes.record_id must reference an existing post');
END;

CREATE TRIGGER IF NOT EXISTS trg_codes_validate_comment_insert
BEFORE INSERT ON codes
WHEN NEW.record_type IN ('comment', 'reply')
  AND NOT EXISTS (SELECT 1 FROM comments WHERE comment_id = NEW.record_id)
BEGIN
    SELECT RAISE(ABORT, 'codes.record_id must reference an existing comment');
END;

CREATE TRIGGER IF NOT EXISTS trg_codes_validate_post_update
BEFORE UPDATE OF record_id, record_type ON codes
WHEN NEW.record_type = 'post'
  AND NOT EXISTS (SELECT 1 FROM posts WHERE post_id = NEW.record_id)
BEGIN
    SELECT RAISE(ABORT, 'codes.record_id must reference an existing post');
END;

CREATE TRIGGER IF NOT EXISTS trg_codes_validate_comment_update
BEFORE UPDATE OF record_id, record_type ON codes
WHEN NEW.record_type IN ('comment', 'reply')
  AND NOT EXISTS (SELECT 1 FROM comments WHERE comment_id = NEW.record_id)
BEGIN
    SELECT RAISE(ABORT, 'codes.record_id must reference an existing comment');
END;

CREATE TRIGGER IF NOT EXISTS trg_codes_cleanup_on_post_delete
AFTER DELETE ON posts
BEGIN
    DELETE FROM codes
    WHERE record_type = 'post' AND record_id = OLD.post_id;
    DELETE FROM claim_units
    WHERE record_type = 'post' AND record_id = OLD.post_id;
    DELETE FROM interaction_events
    WHERE record_type = 'post' AND record_id = OLD.post_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_codes_cleanup_on_comment_delete
AFTER DELETE ON comments
BEGIN
    DELETE FROM codes
    WHERE record_type IN ('comment', 'reply') AND record_id = OLD.comment_id;
    DELETE FROM claim_units
    WHERE record_type IN ('comment', 'reply') AND record_id = OLD.comment_id;
    DELETE FROM interaction_events
    WHERE record_type IN ('comment', 'reply') AND record_id = OLD.comment_id;
END;

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
