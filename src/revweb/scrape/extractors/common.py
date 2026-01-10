from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urljoin, urlparse


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def join_text(parts: Iterable[str]) -> str:
    return normalize_whitespace(" ".join([p for p in parts if p and normalize_whitespace(p)]))


def id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    if not path:
        return "root"
    return path.split("/")[-1]


def abs_url(base: str, maybe: str | None) -> str | None:
    if not maybe:
        return None
    return urljoin(base, maybe)
