from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from datetime import datetime


def normalize_text(value: str | None) -> str:
    """输入任意文本，输出去掉多余空白后的规范文本。"""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_date(value: str | None) -> str | None:
    """输入 legacy 日期字符串，输出 YYYY-MM-DD；无法识别时返回 None。"""
    text = normalize_text(value)
    if not text:
        return None
    candidate = text.replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(candidate[:19], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    if len(candidate) >= 10:
        short = candidate[:10]
        try:
            return datetime.strptime(short, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def hash_identifier(value: str | None) -> str | None:
    """输入原始标识，输出稳定的 SHA1 哈希。"""
    text = normalize_text(value)
    if not text:
        return None
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def mask_name(name: str | None) -> str | None:
    """输入用户名，输出掩码化名称。"""
    text = normalize_text(name)
    if not text:
        return None
    if len(text) == 1:
        return "*"
    if len(text) == 2:
        return text[0] + "*"
    return text[0] + ("*" * (len(text) - 2)) + text[-1]


def parse_engagement_text(value: str | None) -> int | None:
    """输入平台展示热度文本，输出整数计数；无法判断时返回 None。"""
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace(",", "")
    if text.endswith("万"):
        try:
            return int(float(text[:-1]) * 10000)
        except ValueError:
            return None
    lowered = text.lower()
    if lowered.endswith("w"):
        try:
            return int(float(lowered[:-1]) * 10000)
        except ValueError:
            return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def join_unique(values: Iterable[str | None], separator: str = " | ") -> str | None:
    """输入字符串序列，输出按出现顺序去重后的连接文本。"""
    seen: list[str] = []
    for value in values:
        text = normalize_text(value)
        if text and text not in seen:
            seen.append(text)
    return separator.join(seen) if seen else None
