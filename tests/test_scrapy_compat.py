"""Tests for Scrapy 2.13+ compatibility.

These tests verify that the pipeline and spider work correctly with the
new Scrapy API while maintaining backwards compatibility.
"""
from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest

from revweb.config import AppConfig, load_config
from revweb.scrape.pipelines import OutputPipeline
from revweb.scrape.spiders.site_spider import SiteSpider


class TestOutputPipelineScrapyCompat:
    """Tests for OutputPipeline Scrapy 2.13+ compatibility."""

    @pytest.fixture
    def config(self) -> AppConfig:
        """Load test config."""
        return load_config("config/config.yml")

    @pytest.fixture
    def mock_crawler(self, config: AppConfig) -> Mock:
        """Create a mock crawler with settings."""
        crawler = Mock()
        crawler.settings.get.return_value = config
        crawler.spider = Mock()
        crawler.spider.mode = "scrape"
        crawler.spider.seen_urls = set()
        crawler.spider._counters = Mock(pages=0, errors=0, redirects=0)
        return crawler

    def test_pipeline_stores_crawler(self, config: AppConfig, mock_crawler: Mock):
        """Pipeline stores crawler reference from from_crawler()."""
        pipeline = OutputPipeline.from_crawler(mock_crawler)
        assert pipeline.crawler is mock_crawler

    def test_pipeline_get_spider_from_argument(self, config: AppConfig):
        """_get_spider returns spider from argument when provided."""
        pipeline = OutputPipeline(config)
        spider = Mock()
        assert pipeline._get_spider(spider) is spider

    def test_pipeline_get_spider_from_crawler(self, config: AppConfig, mock_crawler: Mock):
        """_get_spider returns spider from crawler when no argument."""
        pipeline = OutputPipeline.from_crawler(mock_crawler)
        assert pipeline._get_spider() is mock_crawler.spider

    def test_pipeline_get_spider_returns_none(self, config: AppConfig):
        """_get_spider returns None when no spider or crawler."""
        pipeline = OutputPipeline(config)
        assert pipeline._get_spider() is None

    def test_open_spider_with_spider_argument(self, config: AppConfig, temp_dir):
        """open_spider works with explicit spider argument."""
        config.scrape.outputs_dir = str(temp_dir)
        config.crawl.emit_web_map_path = str(temp_dir / "web-map.md")
        pipeline = OutputPipeline(config)
        spider = Mock()
        spider.mode = "scrape"
        spider.seen_urls = set()
        spider._counters = Mock(pages=0, errors=0, redirects=0)

        # Should not raise
        pipeline.open_spider(spider)
        pipeline.close_spider(spider)

    def test_open_spider_without_spider_argument(self, config: AppConfig, mock_crawler: Mock, temp_dir):
        """open_spider works without explicit spider argument (Scrapy 2.14+ style)."""
        config.scrape.outputs_dir = str(temp_dir)
        config.crawl.emit_web_map_path = str(temp_dir / "web-map.md")
        mock_crawler.settings.get.return_value = config
        pipeline = OutputPipeline.from_crawler(mock_crawler)

        # Should not raise - gets spider from crawler
        pipeline.open_spider()
        pipeline.close_spider()

    def test_process_item_with_spider_argument(self, config: AppConfig, temp_dir):
        """process_item works with explicit spider argument."""
        config.scrape.outputs_dir = str(temp_dir)
        pipeline = OutputPipeline(config)
        spider = Mock()
        spider.mode = "crawl"  # Won't process items in crawl mode

        item = {"type": "speaker", "data": {"speaker_id": "test"}}
        result = pipeline.process_item(item, spider)
        assert result == item

    def test_process_item_without_spider_argument(self, config: AppConfig, mock_crawler: Mock, temp_dir):
        """process_item works without explicit spider argument (Scrapy 2.14+ style)."""
        config.scrape.outputs_dir = str(temp_dir)
        mock_crawler.settings.get.return_value = config
        mock_crawler.spider.mode = "crawl"
        pipeline = OutputPipeline.from_crawler(mock_crawler)

        item = {"type": "speaker", "data": {"speaker_id": "test"}}
        result = pipeline.process_item(item)  # No spider argument
        assert result == item


class TestSiteSpiderScrapyCompat:
    """Tests for SiteSpider Scrapy 2.13+ compatibility."""

    @pytest.fixture
    def config(self) -> AppConfig:
        """Load test config."""
        return load_config("config/config.yml")

    def test_spider_has_async_start_method(self, config: AppConfig):
        """Spider has async start() method for Scrapy 2.13+."""
        spider = SiteSpider(cfg=config, mode="crawl")
        assert hasattr(spider, "start")
        # Check it's a coroutine function (async def)
        import inspect
        assert inspect.isasyncgenfunction(spider.start)

    def test_spider_start_yields_requests(self, config: AppConfig):
        """Spider start() method yields Request objects."""
        spider = SiteSpider(cfg=config, mode="crawl")

        async def collect_requests():
            requests = []
            async for req in spider.start():
                requests.append(req)
            return requests

        requests = asyncio.run(collect_requests())
        assert len(requests) == len(spider.start_urls)

        for req in requests:
            assert req.callback == spider.parse
            assert "User-Agent" in req.headers.to_unicode_dict()

    def test_spider_start_respects_start_urls(self, config: AppConfig):
        """Spider start() uses configured start_urls."""
        spider = SiteSpider(cfg=config, mode="crawl")

        async def collect_urls():
            urls = []
            async for req in spider.start():
                urls.append(req.url)
            return urls

        urls = asyncio.run(collect_urls())
        assert set(urls) == set(spider.start_urls)

    def test_spider_mode_attribute(self, config: AppConfig):
        """Spider stores mode attribute correctly."""
        crawl_spider = SiteSpider(cfg=config, mode="crawl")
        assert crawl_spider.mode == "crawl"

        scrape_spider = SiteSpider(cfg=config, mode="scrape")
        assert scrape_spider.mode == "scrape"

    def test_spider_allowed_domains(self, config: AppConfig):
        """Spider sets allowed_domains from config."""
        spider = SiteSpider(cfg=config, mode="crawl")
        assert spider.allowed_domains == config.site.allowed_domains
