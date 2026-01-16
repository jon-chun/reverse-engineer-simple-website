from __future__ import annotations

import asyncio
from dataclasses import dataclass

from crawlee import ConcurrencySettings
from crawlee.crawlers import ParselCrawler

from ..config import AppConfig
from ..scrape.output import OutputWriter, link_roundtable_speakers
from .handlers import CrawlState, create_handler


@dataclass
class CrawlResult:
    """Result of a crawl operation."""

    pages_visited: int
    unique_urls: int
    errors: int
    redirects: int
    seen_urls: set[str]


async def run_async(cfg: AppConfig, *, mode: str) -> CrawlResult:
    """Run the crawler asynchronously."""
    state = CrawlState(cfg=cfg, mode=mode)
    handler = create_handler(state)

    concurrency = ConcurrencySettings(
        max_concurrency=10,
        min_concurrency=1,
    )

    crawler = ParselCrawler(
        request_handler=handler,
        max_requests_per_crawl=cfg.crawl.max_pages,
        max_request_retries=2,
        concurrency_settings=concurrency,
    )

    start_urls = cfg.site.start_urls or [
        cfg.site.base_url.rstrip("/") + p for p in cfg.site.start_paths
    ]

    await crawler.run(start_urls)

    if mode == "scrape":
        link_roundtable_speakers(state.aggregator)
        writer = OutputWriter(cfg)
        writer.write_all(state.aggregator)

    writer = OutputWriter(cfg)
    writer.write_web_map(
        state.seen,
        pages_visited=state.counters.pages,
        errors=state.counters.errors,
        redirects=state.counters.redirects,
    )

    return CrawlResult(
        pages_visited=state.counters.pages,
        unique_urls=len(state.seen),
        errors=state.counters.errors,
        redirects=state.counters.redirects,
        seen_urls=state.seen,
    )


def run(cfg: AppConfig, *, mode: str, log_level: str = "WARNING") -> CrawlResult:
    """Run the crawler synchronously."""
    return asyncio.run(run_async(cfg, mode=mode))
