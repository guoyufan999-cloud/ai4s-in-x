from __future__ import annotations

from src.cleaning.normalization import hash_identifier, join_unique, mask_name, normalize_date, normalize_text, parse_engagement_text


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text(" AI   辅助 \n 科研 ") == "AI 辅助 科研"


def test_normalize_date_extracts_day() -> None:
    assert normalize_date("2026-04-13T12:30:45") == "2026-04-13"
    assert normalize_date("2026/04/13") == "2026-04-13"


def test_hash_identifier_is_stable() -> None:
    assert hash_identifier("user-001") == hash_identifier("user-001")


def test_mask_name_obscures_middle_characters() -> None:
    assert mask_name("张三丰") == "张*丰"
    assert mask_name("AI") == "A*"


def test_parse_engagement_text_understands_wan() -> None:
    assert parse_engagement_text("1.2万") == 12000
    assert parse_engagement_text("3,210") == 3210


def test_join_unique_preserves_order() -> None:
    assert join_unique(["文献", "写作", "文献"]) == "文献 | 写作"
