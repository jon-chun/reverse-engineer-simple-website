from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    base_url: str
    allowed_domains: list[str]
    start_urls: list[str] = Field(default_factory=list)
    start_paths: list[str] = Field(default_factory=list)
    user_agent: str = "speaking-events-scraper"
    respect_robots_txt: bool = True


class CrawlConfig(BaseModel):
    max_pages: int = 5000
    max_depth: int = 8
    include_query_params: bool = False
    deny_patterns: list[str] = Field(default_factory=list)
    emit_web_map_path: str = "./docs/web-map.md"


class ScrapeConfig(BaseModel):
    outputs_dir: str = "./data"
    speakers_csv: str = "speakers.csv"
    roundtables_csv: str = "roundtables.csv"
    discussions_csv_pattern: str = "discussion_{roundtable_id}.csv"
    only_roundtable_ids: list[str] = Field(default_factory=list)


class PatternConfig(BaseModel):
    speaker_url: str
    roundtable_url: str
    discussion_url: str


class SelectorSpeaker(BaseModel):
    id_from_url: bool = True
    name: str
    bio: str
    title: str = ""
    organization: str = ""
    headshot_url: str = ""
    social_links: str = ""


class SelectorRoundtable(BaseModel):
    id_from_url: bool = True
    title: str
    description: str
    speaker_links: str


class SelectorDiscussion(BaseModel):
    thread_title: str
    posts: str
    post_id: str
    author: str
    posted_at: str
    content: str
    permalink: str = ""


class SelectorConfig(BaseModel):
    speaker: SelectorSpeaker
    roundtable: SelectorRoundtable
    discussion: SelectorDiscussion


class PlaywrightConfig(BaseModel):
    timeout_ms: int = 30000
    wait_until: str = "networkidle"


class RenderingConfig(BaseModel):
    enable_playwright: Literal["off", "auto", "on"] = "auto"
    playwright: PlaywrightConfig = Field(default_factory=PlaywrightConfig)


class DocsConfig(BaseModel):
    tech_spec_path: str = "./docs/tech-spec-website.md"


class AppConfig(BaseModel):
    site: SiteConfig
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    scrape: ScrapeConfig = Field(default_factory=ScrapeConfig)
    patterns: PatternConfig
    selectors: SelectorConfig
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)


def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    raw: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8"))
    return AppConfig.model_validate(raw)


def ensure_paths(cfg: AppConfig) -> None:
    Path(cfg.scrape.outputs_dir).mkdir(parents=True, exist_ok=True)
    Path("./docs").mkdir(parents=True, exist_ok=True)
