from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ai4s_legitimacy.config.formal_baseline import paper_scope_view
from ai4s_legitimacy.config.settings import OUTPUTS_DIR

EXCERPTS_DIR = OUTPUTS_DIR / "excerpts"
MAX_CHARS_DEFAULT = 120
ExcerptRecordType = Literal["post", "comment"]


@dataclass(frozen=True)
class ExcerptQuerySpec:
    sql: str
    record_type: ExcerptRecordType
    record_id_key: str
    text_key: str
    date_key: str


@dataclass(frozen=True)
class ExcerptBatchSpec:
    distinct_values_sql: str
    query_spec: ExcerptQuerySpec
    slug_builder: Callable[[str], str]


WORKFLOW_STAGE_SQL = f"""
    SELECT post_id, post_date, content_text
    FROM {paper_scope_view('posts')}
    WHERE workflow_stage = ?
      AND content_text IS NOT NULL
      AND length(trim(content_text)) > 0
    ORDER BY length(content_text)
    LIMIT ?
"""

POST_STANCE_SQL = f"""
    SELECT post_id, post_date, content_text
    FROM {paper_scope_view('posts')}
    WHERE primary_legitimacy_stance = ?
      AND content_text IS NOT NULL
      AND length(trim(content_text)) > 0
    ORDER BY length(content_text)
    LIMIT ?
"""

COMMENT_STANCE_SQL = f"""
    SELECT c.comment_id, c.comment_date, c.comment_text
    FROM {paper_scope_view('comments')} c
    WHERE c.stance = ?
      AND c.comment_text IS NOT NULL
      AND length(trim(c.comment_text)) > 0
      ORDER BY length(c.comment_text)
    LIMIT ?
"""

BOUNDARY_CODE_SQL = f"""
    SELECT c.comment_id, c.comment_date, c.comment_text
    FROM {paper_scope_view('comments')} c
    JOIN codes cd ON cd.record_id = c.comment_id AND cd.record_type = 'comment'
    WHERE cd.boundary_negotiation_code = ?
      AND c.comment_text IS NOT NULL
      AND length(trim(c.comment_text)) > 0
    ORDER BY length(c.comment_text)
    LIMIT ?
"""

DISTINCT_WORKFLOW_STAGES_SQL = f"""
    SELECT DISTINCT workflow_stage
    FROM {paper_scope_view('posts')}
    WHERE workflow_stage IS NOT NULL
"""

DISTINCT_STANCES_SQL = f"""
    SELECT DISTINCT primary_legitimacy_stance
    FROM {paper_scope_view('posts')}
    WHERE primary_legitimacy_stance IS NOT NULL
"""

DISTINCT_BOUNDARY_CODES_SQL = f"""
    SELECT DISTINCT boundary_negotiation_code
    FROM codes
    WHERE record_type = 'comment'
      AND boundary_negotiation_code IS NOT NULL
      AND record_id IN (SELECT comment_id FROM {paper_scope_view('comments')})
"""

WORKFLOW_STAGE_QUERY_SPEC = ExcerptQuerySpec(
    sql=WORKFLOW_STAGE_SQL,
    record_type="post",
    record_id_key="post_id",
    text_key="content_text",
    date_key="post_date",
)

POST_STANCE_QUERY_SPEC = ExcerptQuerySpec(
    sql=POST_STANCE_SQL,
    record_type="post",
    record_id_key="post_id",
    text_key="content_text",
    date_key="post_date",
)

COMMENT_STANCE_QUERY_SPEC = ExcerptQuerySpec(
    sql=COMMENT_STANCE_SQL,
    record_type="comment",
    record_id_key="comment_id",
    text_key="comment_text",
    date_key="comment_date",
)

BOUNDARY_CODE_QUERY_SPEC = ExcerptQuerySpec(
    sql=BOUNDARY_CODE_SQL,
    record_type="comment",
    record_id_key="comment_id",
    text_key="comment_text",
    date_key="comment_date",
)


def workflow_stage_slug(stage: str) -> str:
    return f"workflow_{stage.replace('/', '_').replace(' ', '_')}"


def post_stance_slug(stance: str) -> str:
    return f"post_stance_{stance.replace('/', '_').replace(' ', '_')}"


def comment_stance_slug(stance: str) -> str:
    return f"comment_stance_{stance.replace('/', '_').replace(' ', '_')}"


def boundary_code_slug(code: str) -> str:
    return f"boundary_{code.replace('.', '_')}"


WORKFLOW_BATCH_SPEC = ExcerptBatchSpec(
    distinct_values_sql=DISTINCT_WORKFLOW_STAGES_SQL,
    query_spec=WORKFLOW_STAGE_QUERY_SPEC,
    slug_builder=workflow_stage_slug,
)

POST_STANCE_BATCH_SPEC = ExcerptBatchSpec(
    distinct_values_sql=DISTINCT_STANCES_SQL,
    query_spec=POST_STANCE_QUERY_SPEC,
    slug_builder=post_stance_slug,
)

COMMENT_STANCE_BATCH_SPEC = ExcerptBatchSpec(
    distinct_values_sql=DISTINCT_STANCES_SQL,
    query_spec=COMMENT_STANCE_QUERY_SPEC,
    slug_builder=comment_stance_slug,
)

BOUNDARY_BATCH_SPEC = ExcerptBatchSpec(
    distinct_values_sql=DISTINCT_BOUNDARY_CODES_SQL,
    query_spec=BOUNDARY_CODE_QUERY_SPEC,
    slug_builder=boundary_code_slug,
)

BATCH_EXPORT_SPECS: tuple[ExcerptBatchSpec, ...] = (
    WORKFLOW_BATCH_SPEC,
    POST_STANCE_BATCH_SPEC,
    COMMENT_STANCE_BATCH_SPEC,
    BOUNDARY_BATCH_SPEC,
)
