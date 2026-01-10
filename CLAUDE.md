# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A config-driven Python CLI and library for crawling and scraping websites for reverse engineering purposes. Outputs structured CSV data and documentation artifacts. Uses Scrapy with optional Playwright for JS-rendered pages.

## Common Commands

```bash
# Install (with uv, recommended)
uv venv && uv pip install -e ".[dev]"

# Install (with pip)
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Run CLI commands
revweb crawl --config config/config.yml   # generates docs/web-map.md
revweb scrape --config config/config.yml  # generates data/*.csv
revweb spec --config config/config.yml    # generates docs/tech-spec-website.md

# Lint and test
ruff check .
pytest
pytest tests/test_config.py -v  # run single test file

# For JS-rendered sites
python -m playwright install
```

## Architecture

### CLI -> Runner -> Spider -> Extractors -> Pipeline

1. **CLI** (`cli.py`): Three commands - `crawl`, `scrape`, `spec` - all driven by `config/config.yml`
2. **Runner** (`scrape/runner.py`): Configures Scrapy settings and launches `CrawlerProcess`
3. **SiteSpider** (`scrape/spiders/site_spider.py`): Single spider with two modes:
   - `crawl` mode: Discovers URLs, builds site map
   - `scrape` mode: Extracts data using regex URL patterns to route to extractors
4. **Extractors** (`scrape/extractors/`): Domain-specific extraction for speakers, roundtables, discussions
5. **OutputPipeline** (`scrape/pipelines.py`): Aggregates/dedupes data, writes CSVs, generates web-map.md

### Configuration-Driven Design

All site-specific behavior is in `config/config.yml`:
- `patterns.*`: Regex patterns matching speaker/roundtable/discussion URLs
- `selectors.*`: CSS selectors for extracting fields from each page type
- `rendering.enable_playwright`: Set to `"auto"` or `"on"` for JS sites

### Data Models

Pydantic models in `models.py`: `Speaker`, `Roundtable`, `DiscussionPost`

### Key Design Decisions

- URL canonicalization strips query params by default (`crawl.include_query_params: false`)
- Speaker-to-roundtable linking uses fuzzy matching (rapidfuzz) as fallback when URL matching fails
- Discussion posts stream to separate CSV files per roundtable
- Pre-commit hooks run ruff for linting/formatting
