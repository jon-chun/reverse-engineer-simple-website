"""Unit tests for configuration loading and validation."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from revweb.config import (
    AppConfig,
    CrawlConfig,
    RenderingConfig,
    ScrapeConfig,
    SiteConfig,
    ensure_paths,
    load_config,
)


class TestLoadConfig:
    """Tests for loading configuration files."""

    def test_load_default_config(self):
        """Default config file loads successfully."""
        cfg = load_config("config/config.yml")
        assert isinstance(cfg, AppConfig)
        assert cfg.site.base_url
        assert cfg.patterns.speaker_url

    def test_load_config_from_path(self):
        """Config can be loaded from Path object."""
        cfg = load_config(Path("config/config.yml"))
        assert isinstance(cfg, AppConfig)

    def test_load_missing_config(self):
        """Loading missing config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent/config.yml")

    def test_load_minimal_config(self, minimal_config_dict, temp_dir):
        """Minimal config loads with defaults for optional fields."""
        config_path = temp_dir / "config.yml"
        config_path.write_text(yaml.dump(minimal_config_dict))

        cfg = load_config(config_path)
        assert cfg.site.base_url == "https://test.example.com"
        # Check defaults
        assert cfg.crawl.max_pages == 5000
        assert cfg.scrape.outputs_dir == "./data"

    def test_invalid_yaml(self, temp_dir):
        """Invalid YAML raises error."""
        config_path = temp_dir / "bad.yml"
        config_path.write_text("{ invalid yaml [[[")

        with pytest.raises(yaml.YAMLError):
            load_config(config_path)


class TestSiteConfig:
    """Tests for site configuration."""

    def test_site_config_required_fields(self):
        """SiteConfig requires base_url and allowed_domains."""
        cfg = SiteConfig(
            base_url="https://example.com",
            allowed_domains=["example.com"],
        )
        assert cfg.base_url == "https://example.com"

    def test_site_config_defaults(self):
        """SiteConfig has sensible defaults."""
        cfg = SiteConfig(
            base_url="https://example.com",
            allowed_domains=["example.com"],
        )
        assert cfg.respect_robots_txt is True
        assert cfg.user_agent == "speaking-events-scraper"

    def test_site_config_custom_user_agent(self):
        """Custom user agent can be set."""
        cfg = SiteConfig(
            base_url="https://example.com",
            allowed_domains=["example.com"],
            user_agent="custom-agent/1.0",
        )
        assert cfg.user_agent == "custom-agent/1.0"


class TestCrawlConfig:
    """Tests for crawl configuration."""

    def test_crawl_config_defaults(self):
        """CrawlConfig has sensible defaults."""
        cfg = CrawlConfig()
        assert cfg.max_pages == 5000
        assert cfg.max_depth == 8
        assert cfg.include_query_params is False

    def test_crawl_config_custom_values(self):
        """CrawlConfig accepts custom values."""
        cfg = CrawlConfig(max_pages=100, max_depth=3)
        assert cfg.max_pages == 100
        assert cfg.max_depth == 3

    def test_crawl_config_deny_patterns(self):
        """Deny patterns can be configured."""
        cfg = CrawlConfig(deny_patterns=["/login", "/admin"])
        assert "/login" in cfg.deny_patterns
        assert "/admin" in cfg.deny_patterns


class TestScrapeConfig:
    """Tests for scrape configuration."""

    def test_scrape_config_defaults(self):
        """ScrapeConfig has sensible defaults."""
        cfg = ScrapeConfig()
        assert cfg.outputs_dir == "./data"
        assert cfg.speakers_csv == "speakers.csv"

    def test_scrape_config_only_roundtable_ids(self):
        """Can filter to specific roundtable IDs."""
        cfg = ScrapeConfig(only_roundtable_ids=["rt-1", "rt-2"])
        assert "rt-1" in cfg.only_roundtable_ids


class TestRenderingConfig:
    """Tests for rendering configuration."""

    def test_rendering_config_defaults(self):
        """RenderingConfig has sensible defaults."""
        cfg = RenderingConfig()
        assert cfg.enable_playwright == "auto"
        assert cfg.playwright.timeout_ms == 30000

    def test_rendering_config_values(self):
        """RenderingConfig accepts valid values."""
        for value in ["off", "auto", "on"]:
            cfg = RenderingConfig(enable_playwright=value)
            assert cfg.enable_playwright == value

    def test_rendering_config_invalid_value(self):
        """RenderingConfig rejects invalid values."""
        with pytest.raises(ValidationError):
            RenderingConfig(enable_playwright="invalid")


class TestEnsurePaths:
    """Tests for path creation."""

    def test_ensure_paths_creates_directories(self, app_config, temp_dir):
        """ensure_paths creates required directories."""
        # Modify config to use temp directory
        app_config.scrape.outputs_dir = str(temp_dir / "data")
        ensure_paths(app_config)

        assert (temp_dir / "data").exists()
        assert Path("./docs").exists()
