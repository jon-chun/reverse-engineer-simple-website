from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse


def canonicalize(url: str, *, base_url: str, include_query_params: bool) -> str:
    u = urljoin(base_url, url)
    p = urlparse(u)
    query = p.query if include_query_params else ""
    frag = ""
    path = p.path or "/"
    if path != "/" and path.endswith("//"):
        path = re.sub(r"/+$", "/", path)
    return urlunparse((p.scheme, p.netloc, path, "", query, frag))


def is_denied(url: str, deny_patterns: list[str]) -> bool:
    return any(re.match(pat, url) or re.search(pat, url) for pat in deny_patterns)
