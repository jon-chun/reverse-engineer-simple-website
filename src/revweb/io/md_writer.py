from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class WebMapStats:
    pages_visited: int
    unique_urls: int
    errors: int
    redirects: int


def write_web_map(path: str | Path, *, base_url: str, outline_lines: Iterable[str], stats: WebMapStats) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Web Map",
        "",
        f"- Generated (UTC): `{now}`",
        f"- Base URL: `{base_url}`",
        f"- Pages visited: **{stats.pages_visited}**",
        f"- Unique URLs: **{stats.unique_urls}**",
        f"- Errors: **{stats.errors}**",
        f"- Redirects: **{stats.redirects}**",
        "",
        "## Site structure (path outline)",
        "",
    ]
    lines.extend(outline_lines)
    lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")


def write_speakers_md(path: str | Path, *, speakers: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Speakers", ""]
    for s in speakers:
        sid = s.get("speaker_id", "")
        name = s.get("name", "")
        lines.append(f"## {name}")
        lines.append(f"<a id=\"speaker-{sid}\"></a>")
        lines.append("")
        bio = (s.get("bio") or "").strip()
        if bio:
            lines.append(bio)
            lines.append("")
        if s.get("profile_url"):
            lines.append(f"- Profile: {s['profile_url']}")
        lines.append("")

    p.write_text("\n".join(lines), encoding="utf-8")


def write_website_rebuild_spec(path: str | Path, *, base_url: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    content = f"""# Website Rebuild Technical Specification

- Generated (UTC): `{now}`
- Source website: `{base_url}`

## Purpose

This document describes how to recreate the speaking-events website using the scraper outputs:

- `data/speakers.csv`
- `data/roundtables.csv`
- `data/discussion_<roundtable_id>.csv`

## Recommended architecture (file-based backend)

### Option A (recommended): Static site generator (build-time rendering)

1. Convert CSV to JSON artifacts at build time:
   - `speakers.json`
   - `roundtables.json`
   - `discussions/<roundtable_id>.json`
2. Render static HTML using templates (e.g., Jinja2).
3. Deploy to static hosting (GitHub Pages / Netlify / Cloudflare Pages).

### Option B: Minimal API (FastAPI) + templates

1. Serve CSV/JSON from disk on startup.
2. Render HTML server-side or serve JSON to a thin frontend.

## Information architecture

- Speakers directory and detail pages
- Roundtables index and detail pages
- Discussions per roundtable

## Data contracts (minimum)

### speakers.csv
- speaker_id (PK), name, bio

### roundtables.csv
- roundtable_id (PK), title, description, speaker_ids (comma-separated)

### discussion_<roundtable_id>.csv
- discussion_id (PK), roundtable_id (FK), posted_at, author_name, content_text

## Referential integrity

- Every speaker referenced in roundtables must exist in speakers.csv
- Every discussion file must match an existing roundtable_id
"""
    p.write_text(content, encoding="utf-8")
