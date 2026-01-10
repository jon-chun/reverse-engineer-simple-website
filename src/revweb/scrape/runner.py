from __future__ import annotations

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from ..config import AppConfig
from .spiders.site_spider import SiteSpider


def _scrapy_settings(cfg: AppConfig, *, log_level: str = "WARNING") -> Settings:
    s = Settings()
    s.set("USER_AGENT", cfg.site.user_agent)
    s.set("ROBOTSTXT_OBEY", bool(cfg.site.respect_robots_txt))
    s.set("LOG_LEVEL", log_level)

    s.set("AUTOTHROTTLE_ENABLED", True)
    s.set("DOWNLOAD_DELAY", 0.25)

    s.set("ITEM_PIPELINES", {"revweb.scrape.pipelines.OutputPipeline": 300})
    s.set("APP_CONFIG", cfg)

    if cfg.rendering.enable_playwright in ("on", "auto"):
        s.set("DOWNLOAD_HANDLERS", {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        })
        s.set("TWISTED_REACTOR", "twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        s.set("PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT", cfg.rendering.playwright.timeout_ms)
        s.set("PLAYWRIGHT_LAUNCH_OPTIONS", {"headless": True})

    return s


def run(cfg: AppConfig, *, mode: str, log_level: str = "WARNING") -> None:
    settings = _scrapy_settings(cfg, log_level=log_level)
    process = CrawlerProcess(settings=settings)
    process.crawl(SiteSpider, cfg=cfg, mode=mode)
    process.start()
