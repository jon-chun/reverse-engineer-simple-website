# revweb (PyPI-ready)

This repository provides:

- A Python **library** (`revweb`) for crawling and scraping websites for reverse engineering.
- A **CLI** (`revweb`) that outputs:
  - `./docs/web-map.md`
  - `./data/speakers.csv`
  - `./data/roundtables.csv`
  - `./data/discussion_<roundtable_id>.csv` (one per roundtable)
  - `./docs/tech-spec-website.md` (how to rebuild the website from outputs)

## Requirements

- Python 3.10+
- Recommended: `uv` for fast, reproducible environments.
- For JS-rendered sites: Playwright browsers (see below).

## Quick start (recommended with uv)

```bash
uv venv
uv pip install -e ".[dev]"
revweb crawl --config config/config.yml
revweb scrape --config config/config.yml
revweb spec --config config/config.yml
```

If you prefer pip/venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
revweb crawl --config config/config.yml
```

## Playwright setup (optional)

For JS-heavy sites, set `rendering.enable_playwright: "auto"` or `"on"` in `config/config.yml`.

```bash
python -m playwright install
```

## Configuration

Central configuration is in `config/config.yml`. Adjust `patterns.*` and `selectors.*` for the target site.

## Legal and ethical notes

You are responsible for complying with the website's Terms of Service and robots.txt.
