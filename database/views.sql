DROP VIEW IF EXISTS vw_scope_counts;
DROP VIEW IF EXISTS vw_boundary_negotiation_summary;
DROP VIEW IF EXISTS vw_workflow_legitimacy_cross;
DROP VIEW IF EXISTS vw_comments_by_month_legitimacy;
DROP VIEW IF EXISTS vw_posts_by_month_workflow;
DROP VIEW IF EXISTS vw_paper_quality_v5_comments_by_month_stance;
DROP VIEW IF EXISTS vw_paper_quality_v5_workflow_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v5_subject_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v5_posts_by_month_workflow;
DROP VIEW IF EXISTS vw_comments_paper_scope_quality_v5;
DROP VIEW IF EXISTS vw_comments_research_scope;
DROP VIEW IF EXISTS vw_comments_candidate_scope;
DROP VIEW IF EXISTS vw_posts_paper_scope_quality_v5;
DROP VIEW IF EXISTS vw_posts_research_scope;
DROP VIEW IF EXISTS vw_posts_candidate_scope;
DROP VIEW IF EXISTS vw_paper_quality_v5_post_ai_tools;
DROP VIEW IF EXISTS vw_paper_quality_v5_post_risk_themes;
DROP VIEW IF EXISTS vw_paper_quality_v5_post_benefit_themes;
DROP VIEW IF EXISTS vw_paper_quality_v5_workflow_legitimacy_cross;
DROP VIEW IF EXISTS vw_paper_quality_v5_boundary_negotiation_summary;
DROP VIEW IF EXISTS vw_paper_quality_v5_subject_workflow_cross;
DROP VIEW IF EXISTS vw_paper_quality_v5_subject_legitimacy_cross;
DROP VIEW IF EXISTS vw_paper_quality_v5_comment_legitimacy_basis_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v5_halfyear_workflow;
DROP VIEW IF EXISTS vw_paper_quality_v5_halfyear_subject;
DROP VIEW IF EXISTS vw_paper_quality_v6_comments_by_month_stance;
DROP VIEW IF EXISTS vw_paper_quality_v6_workflow_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v6_subject_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v6_posts_by_month_workflow;
DROP VIEW IF EXISTS vw_comments_paper_scope_quality_v6;
DROP VIEW IF EXISTS vw_posts_paper_scope_quality_v6;
DROP VIEW IF EXISTS vw_paper_quality_v6_post_ai_tools;
DROP VIEW IF EXISTS vw_paper_quality_v6_post_risk_themes;
DROP VIEW IF EXISTS vw_paper_quality_v6_post_benefit_themes;
DROP VIEW IF EXISTS vw_paper_quality_v6_workflow_legitimacy_cross;
DROP VIEW IF EXISTS vw_paper_quality_v6_boundary_negotiation_summary;
DROP VIEW IF EXISTS vw_paper_quality_v6_subject_workflow_cross;
DROP VIEW IF EXISTS vw_paper_quality_v6_subject_legitimacy_cross;
DROP VIEW IF EXISTS vw_paper_quality_v6_comment_legitimacy_basis_distribution;
DROP VIEW IF EXISTS vw_paper_quality_v6_halfyear_workflow;
DROP VIEW IF EXISTS vw_paper_quality_v6_halfyear_subject;

CREATE VIEW vw_posts_candidate_scope AS
SELECT
    post_id,
    platform,
    legacy_note_id,
    legacy_crawl_status,
    post_url,
    author_id_hashed,
    author_name_masked,
    post_date,
    capture_date,
    title,
    content_text,
    engagement_like,
    engagement_comment,
    engagement_collect,
    keyword_query,
    is_public,
    sample_status,
    actor_type,
    qs_broad_subject,
    workflow_stage,
    primary_legitimacy_stance,
    risk_themes_json,
    ai_tools_json,
    import_batch_id,
    notes,
    decision,
    review_status
FROM posts;

CREATE VIEW vw_posts_research_scope AS
SELECT *
FROM vw_posts_candidate_scope
WHERE sample_status IN ('true', 'review_needed');

CREATE VIEW vw_posts_paper_scope_quality_v5 AS
SELECT *
FROM vw_posts_research_scope
WHERE decision = '纳入'
  AND EXISTS (
      SELECT 1
      FROM claim_units cu
      WHERE cu.record_type = 'post'
        AND cu.record_id = vw_posts_research_scope.post_id
  )
  AND COALESCE(NULLIF(actor_type, ''), 'uncertain') NOT IN ('tool_vendor_or_promotional')
  AND legacy_crawl_status = 'crawled'
  AND post_date BETWEEN '2024-01-01' AND '2026-06-30'
  AND qs_broad_subject IS NOT NULL
  AND workflow_stage IS NOT NULL
  AND primary_legitimacy_stance IS NOT NULL;

CREATE VIEW vw_comments_candidate_scope AS
SELECT
    comment_id,
    post_id,
    parent_comment_id,
    comment_date,
    comment_text,
    commenter_id_hashed,
    stance,
    legitimacy_basis,
    is_reply,
    import_batch_id,
    decision,
    review_status
FROM comments;

CREATE VIEW vw_comments_research_scope AS
SELECT c.*
FROM vw_comments_candidate_scope c
JOIN vw_posts_research_scope p ON p.post_id = c.post_id;

CREATE VIEW vw_comments_paper_scope_quality_v5 AS
SELECT c.*
FROM vw_comments_candidate_scope c
JOIN vw_posts_paper_scope_quality_v5 p ON p.post_id = c.post_id
WHERE c.comment_date IS NOT NULL
  AND c.comment_date BETWEEN '2024-01-01' AND '2026-06-30'
  AND c.decision = '纳入'
  AND EXISTS (
      SELECT 1
      FROM claim_units cu
      WHERE cu.record_type IN ('comment', 'reply')
        AND cu.record_id = c.comment_id
  )
  AND c.stance IS NOT NULL;

CREATE VIEW vw_posts_paper_scope_quality_v6 AS
SELECT *
FROM vw_posts_paper_scope_quality_v5
UNION ALL
SELECT *
FROM vw_posts_research_scope
WHERE post_id NOT IN (
      SELECT post_id FROM vw_posts_paper_scope_quality_v5
  )
  AND import_batch_id IN (
      SELECT batch_id
      FROM import_batches
      WHERE batch_name = 'quality_v6_xhs_expansion_candidate_v1_supplemental_formalization_v1'
  )
  AND decision = '纳入'
  AND post_date BETWEEN '2024-01-01' AND '2026-06-30'
  AND notes LIKE '%quality_v6_formal=true%'
  AND EXISTS (
      SELECT 1
      FROM claim_units cu
      WHERE cu.record_type = 'post'
        AND cu.record_id = vw_posts_research_scope.post_id
  );

CREATE VIEW vw_comments_paper_scope_quality_v6 AS
SELECT *
FROM vw_comments_candidate_scope
WHERE 0;

CREATE VIEW vw_paper_quality_v5_posts_by_month_workflow AS
SELECT
    substr(post_date, 1, 7) AS period_month,
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5
GROUP BY substr(post_date, 1, 7), COALESCE(workflow_stage, 'uncoded')
ORDER BY period_month, workflow_stage;

CREATE VIEW vw_paper_quality_v5_subject_distribution AS
SELECT
    COALESCE(qs_broad_subject, 'uncoded') AS subject_label,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5
GROUP BY COALESCE(qs_broad_subject, 'uncoded')
ORDER BY post_count DESC, subject_label;

CREATE VIEW vw_paper_quality_v5_workflow_distribution AS
SELECT
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5
GROUP BY COALESCE(workflow_stage, 'uncoded')
ORDER BY post_count DESC, workflow_stage;

CREATE VIEW vw_paper_quality_v5_comments_by_month_stance AS
SELECT
    substr(comment_date, 1, 7) AS period_month,
    COALESCE(stance, 'uncoded') AS stance,
    COUNT(*) AS comment_count
FROM vw_comments_paper_scope_quality_v5
GROUP BY substr(comment_date, 1, 7), COALESCE(stance, 'uncoded')
ORDER BY period_month, stance;

CREATE VIEW vw_posts_by_month_workflow AS
SELECT
    substr(post_date, 1, 7) AS period_month,
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_research_scope
GROUP BY substr(post_date, 1, 7), COALESCE(workflow_stage, 'uncoded')
ORDER BY period_month, workflow_stage;

CREATE VIEW vw_comments_by_month_legitimacy AS
SELECT
    substr(comment_date, 1, 7) AS period_month,
    COALESCE(legitimacy_basis, 'uncoded') AS legitimacy_basis,
    COUNT(*) AS comment_count
FROM vw_comments_research_scope
GROUP BY substr(comment_date, 1, 7), COALESCE(legitimacy_basis, 'uncoded')
ORDER BY period_month, legitimacy_basis;

CREATE VIEW vw_workflow_legitimacy_cross AS
SELECT
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COALESCE(primary_legitimacy_stance, 'uncoded') AS legitimacy_stance,
    COUNT(*) AS post_count
FROM vw_posts_research_scope
GROUP BY COALESCE(workflow_stage, 'uncoded'), COALESCE(primary_legitimacy_stance, 'uncoded')
ORDER BY workflow_stage, legitimacy_stance;

CREATE VIEW vw_boundary_negotiation_summary AS
SELECT
    COALESCE(boundary_negotiation_code, 'uncoded') AS boundary_negotiation_code,
    COUNT(*) AS coded_count
FROM codes
WHERE record_type = 'comment'
GROUP BY COALESCE(boundary_negotiation_code, 'uncoded')
ORDER BY coded_count DESC, boundary_negotiation_code;

CREATE VIEW vw_scope_counts AS
SELECT 'candidate_posts' AS scope_name, COUNT(*) AS row_count FROM vw_posts_candidate_scope
UNION ALL
SELECT 'research_posts', COUNT(*) FROM vw_posts_research_scope
UNION ALL
SELECT 'paper_quality_v5_posts', COUNT(*) FROM vw_posts_paper_scope_quality_v5
UNION ALL
SELECT 'paper_quality_v6_posts', COUNT(*) FROM vw_posts_paper_scope_quality_v6
UNION ALL
SELECT 'candidate_comments', COUNT(*) FROM vw_comments_candidate_scope
UNION ALL
SELECT 'research_comments', COUNT(*) FROM vw_comments_research_scope
UNION ALL
SELECT 'paper_quality_v5_comments', COUNT(*) FROM vw_comments_paper_scope_quality_v5
UNION ALL
SELECT 'paper_quality_v6_comments', COUNT(*) FROM vw_comments_paper_scope_quality_v6;

CREATE VIEW vw_paper_quality_v5_post_ai_tools AS
SELECT
    p.post_id,
    j.value AS tool_key
FROM vw_posts_paper_scope_quality_v5 p, json_each(p.ai_tools_json) j
WHERE p.ai_tools_json IS NOT NULL AND p.ai_tools_json != '[]';

CREATE VIEW vw_paper_quality_v5_post_risk_themes AS
SELECT
    p.post_id,
    j.value AS risk_key
FROM vw_posts_paper_scope_quality_v5 p, json_each(p.risk_themes_json) j
WHERE p.risk_themes_json IS NOT NULL AND p.risk_themes_json != '[]';

CREATE VIEW vw_paper_quality_v5_post_benefit_themes AS
SELECT
    p.post_id,
    j.value AS benefit_key
FROM vw_posts_paper_scope_quality_v5 p, json_each(p.benefit_themes_json) j
WHERE p.benefit_themes_json IS NOT NULL AND p.benefit_themes_json != '[]';

CREATE VIEW vw_paper_quality_v5_workflow_legitimacy_cross AS
SELECT
    COALESCE(p.workflow_stage, 'uncoded') AS workflow_stage,
    COALESCE(p.primary_legitimacy_stance, 'uncoded') AS legitimacy_stance,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5 p
GROUP BY COALESCE(p.workflow_stage, 'uncoded'), COALESCE(p.primary_legitimacy_stance, 'uncoded')
ORDER BY workflow_stage, legitimacy_stance;

CREATE VIEW vw_paper_quality_v5_boundary_negotiation_summary AS
SELECT
    COALESCE(c.boundary_negotiation_code, 'uncoded') AS boundary_negotiation_code,
    COUNT(*) AS coded_count
FROM codes c
JOIN vw_comments_paper_scope_quality_v5 cm ON cm.comment_id = c.record_id
WHERE c.record_type = 'comment'
GROUP BY COALESCE(c.boundary_negotiation_code, 'uncoded')
ORDER BY coded_count DESC, boundary_negotiation_code;

CREATE VIEW vw_paper_quality_v5_subject_workflow_cross AS
SELECT
    COALESCE(p.qs_broad_subject, 'uncoded') AS subject_label,
    COALESCE(p.workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5 p
GROUP BY COALESCE(p.qs_broad_subject, 'uncoded'), COALESCE(p.workflow_stage, 'uncoded')
ORDER BY post_count DESC, subject_label, workflow_stage;

CREATE VIEW vw_paper_quality_v5_subject_legitimacy_cross AS
SELECT
    COALESCE(p.qs_broad_subject, 'uncoded') AS subject_label,
    COALESCE(p.primary_legitimacy_stance, 'uncoded') AS legitimacy_stance,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5 p
GROUP BY COALESCE(p.qs_broad_subject, 'uncoded'), COALESCE(p.primary_legitimacy_stance, 'uncoded')
ORDER BY post_count DESC, subject_label, legitimacy_stance;

CREATE VIEW vw_paper_quality_v5_comment_legitimacy_basis_distribution AS
SELECT
    COALESCE(cm.legitimacy_basis, 'uncoded') AS legitimacy_basis,
    COUNT(*) AS comment_count
FROM vw_comments_paper_scope_quality_v5 cm
GROUP BY COALESCE(cm.legitimacy_basis, 'uncoded')
ORDER BY comment_count DESC, legitimacy_basis;

CREATE VIEW vw_paper_quality_v5_halfyear_workflow AS
SELECT
    CASE
        WHEN post_date BETWEEN '2024-01-01' AND '2024-06-30' THEN '2024H1'
        WHEN post_date BETWEEN '2024-07-01' AND '2024-12-31' THEN '2024H2'
        WHEN post_date BETWEEN '2025-01-01' AND '2025-06-30' THEN '2025H1'
        WHEN post_date BETWEEN '2025-07-01' AND '2025-12-31' THEN '2025H2'
        WHEN post_date BETWEEN '2026-01-01' AND '2026-06-30' THEN '2026H1'
    END AS half_year,
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5
WHERE post_date IS NOT NULL
GROUP BY half_year, COALESCE(workflow_stage, 'uncoded')
HAVING half_year IS NOT NULL
ORDER BY half_year, workflow_stage;

CREATE VIEW vw_paper_quality_v5_halfyear_subject AS
SELECT
    CASE
        WHEN post_date BETWEEN '2024-01-01' AND '2024-06-30' THEN '2024H1'
        WHEN post_date BETWEEN '2024-07-01' AND '2024-12-31' THEN '2024H2'
        WHEN post_date BETWEEN '2025-01-01' AND '2025-06-30' THEN '2025H1'
        WHEN post_date BETWEEN '2025-07-01' AND '2025-12-31' THEN '2025H2'
        WHEN post_date BETWEEN '2026-01-01' AND '2026-06-30' THEN '2026H1'
    END AS half_year,
    COALESCE(qs_broad_subject, 'uncoded') AS subject_label,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v5
WHERE post_date IS NOT NULL
GROUP BY half_year, COALESCE(qs_broad_subject, 'uncoded')
HAVING half_year IS NOT NULL
ORDER BY half_year, subject_label;

CREATE VIEW vw_paper_quality_v6_posts_by_month_workflow AS
SELECT
    substr(post_date, 1, 7) AS period_month,
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6
GROUP BY substr(post_date, 1, 7), COALESCE(workflow_stage, 'uncoded')
ORDER BY period_month, workflow_stage;

CREATE VIEW vw_paper_quality_v6_subject_distribution AS
SELECT
    COALESCE(qs_broad_subject, 'uncoded') AS subject_label,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6
GROUP BY COALESCE(qs_broad_subject, 'uncoded')
ORDER BY post_count DESC, subject_label;

CREATE VIEW vw_paper_quality_v6_workflow_distribution AS
SELECT
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6
GROUP BY COALESCE(workflow_stage, 'uncoded')
ORDER BY post_count DESC, workflow_stage;

CREATE VIEW vw_paper_quality_v6_comments_by_month_stance AS
SELECT
    substr(comment_date, 1, 7) AS period_month,
    COALESCE(stance, 'uncoded') AS stance,
    COUNT(*) AS comment_count
FROM vw_comments_paper_scope_quality_v6
GROUP BY substr(comment_date, 1, 7), COALESCE(stance, 'uncoded')
ORDER BY period_month, stance;

CREATE VIEW vw_paper_quality_v6_post_ai_tools AS
SELECT
    p.post_id,
    j.value AS tool_key
FROM vw_posts_paper_scope_quality_v6 p, json_each(p.ai_tools_json) j
WHERE p.ai_tools_json IS NOT NULL AND p.ai_tools_json != '[]';

CREATE VIEW vw_paper_quality_v6_post_risk_themes AS
SELECT
    p.post_id,
    j.value AS risk_key
FROM vw_posts_paper_scope_quality_v6 p, json_each(p.risk_themes_json) j
WHERE p.risk_themes_json IS NOT NULL AND p.risk_themes_json != '[]';

CREATE VIEW vw_paper_quality_v6_post_benefit_themes AS
SELECT
    p.post_id,
    j.value AS benefit_key
FROM vw_posts_paper_scope_quality_v6 p, json_each(p.benefit_themes_json) j
WHERE p.benefit_themes_json IS NOT NULL AND p.benefit_themes_json != '[]';

CREATE VIEW vw_paper_quality_v6_workflow_legitimacy_cross AS
SELECT
    COALESCE(p.workflow_stage, 'uncoded') AS workflow_stage,
    COALESCE(p.primary_legitimacy_stance, 'uncoded') AS legitimacy_stance,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6 p
GROUP BY COALESCE(p.workflow_stage, 'uncoded'), COALESCE(p.primary_legitimacy_stance, 'uncoded')
ORDER BY workflow_stage, legitimacy_stance;

CREATE VIEW vw_paper_quality_v6_boundary_negotiation_summary AS
SELECT
    COALESCE(c.boundary_negotiation_code, 'uncoded') AS boundary_negotiation_code,
    COUNT(*) AS coded_count
FROM codes c
JOIN vw_comments_paper_scope_quality_v6 cm ON cm.comment_id = c.record_id
WHERE c.record_type = 'comment'
GROUP BY COALESCE(c.boundary_negotiation_code, 'uncoded')
ORDER BY coded_count DESC, boundary_negotiation_code;

CREATE VIEW vw_paper_quality_v6_subject_workflow_cross AS
SELECT
    COALESCE(p.qs_broad_subject, 'uncoded') AS subject_label,
    COALESCE(p.workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6 p
GROUP BY COALESCE(p.qs_broad_subject, 'uncoded'), COALESCE(p.workflow_stage, 'uncoded')
ORDER BY post_count DESC, subject_label, workflow_stage;

CREATE VIEW vw_paper_quality_v6_subject_legitimacy_cross AS
SELECT
    COALESCE(p.qs_broad_subject, 'uncoded') AS subject_label,
    COALESCE(p.primary_legitimacy_stance, 'uncoded') AS legitimacy_stance,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6 p
GROUP BY COALESCE(p.qs_broad_subject, 'uncoded'), COALESCE(p.primary_legitimacy_stance, 'uncoded')
ORDER BY post_count DESC, subject_label, legitimacy_stance;

CREATE VIEW vw_paper_quality_v6_comment_legitimacy_basis_distribution AS
SELECT
    COALESCE(cm.legitimacy_basis, 'uncoded') AS legitimacy_basis,
    COUNT(*) AS comment_count
FROM vw_comments_paper_scope_quality_v6 cm
GROUP BY COALESCE(cm.legitimacy_basis, 'uncoded')
ORDER BY comment_count DESC, legitimacy_basis;

CREATE VIEW vw_paper_quality_v6_halfyear_workflow AS
SELECT
    CASE
        WHEN post_date BETWEEN '2024-01-01' AND '2024-06-30' THEN '2024H1'
        WHEN post_date BETWEEN '2024-07-01' AND '2024-12-31' THEN '2024H2'
        WHEN post_date BETWEEN '2025-01-01' AND '2025-06-30' THEN '2025H1'
        WHEN post_date BETWEEN '2025-07-01' AND '2025-12-31' THEN '2025H2'
        WHEN post_date BETWEEN '2026-01-01' AND '2026-06-30' THEN '2026H1'
    END AS half_year,
    COALESCE(workflow_stage, 'uncoded') AS workflow_stage,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6
WHERE post_date IS NOT NULL
GROUP BY half_year, COALESCE(workflow_stage, 'uncoded')
HAVING half_year IS NOT NULL
ORDER BY half_year, workflow_stage;

CREATE VIEW vw_paper_quality_v6_halfyear_subject AS
SELECT
    CASE
        WHEN post_date BETWEEN '2024-01-01' AND '2024-06-30' THEN '2024H1'
        WHEN post_date BETWEEN '2024-07-01' AND '2024-12-31' THEN '2024H2'
        WHEN post_date BETWEEN '2025-01-01' AND '2025-06-30' THEN '2025H1'
        WHEN post_date BETWEEN '2025-07-01' AND '2025-12-31' THEN '2025H2'
        WHEN post_date BETWEEN '2026-01-01' AND '2026-06-30' THEN '2026H1'
    END AS half_year,
    COALESCE(qs_broad_subject, 'uncoded') AS subject_label,
    COUNT(*) AS post_count
FROM vw_posts_paper_scope_quality_v6
WHERE post_date IS NOT NULL
GROUP BY half_year, COALESCE(qs_broad_subject, 'uncoded')
HAVING half_year IS NOT NULL
ORDER BY half_year, subject_label;
