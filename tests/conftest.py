"""Shared fixtures for tests."""
from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from revweb.config import AppConfig, load_config


@pytest.fixture
def app_config() -> AppConfig:
    """Load the default config for testing."""
    return load_config("config/config.yml")


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_speaker_data() -> dict:
    """Sample speaker data for testing."""
    return {
        "speaker_id": "john-doe",
        "name": "John Doe",
        "bio": "A test speaker bio.",
        "title": "Software Engineer",
        "organization": "Test Corp",
        "profile_url": "https://example.com/speakers/john-doe",
        "headshot_url": "https://example.com/images/john-doe.jpg",
        "social_links": "https://twitter.com/johndoe;https://linkedin.com/in/johndoe",
    }


@pytest.fixture
def sample_roundtable_data() -> dict:
    """Sample roundtable data for testing."""
    return {
        "roundtable_id": "test-roundtable",
        "title": "Test Roundtable Discussion",
        "description": "A roundtable about testing.",
        "roundtable_url": "https://example.com/roundtables/test-roundtable",
        "speaker_ids": "john-doe,jane-doe",
        "speakers_md_link": "./speakers.md",
    }


@pytest.fixture
def sample_discussion_data() -> dict:
    """Sample discussion post data for testing."""
    return {
        "discussion_id": "test-roundtable-1",
        "roundtable_id": "test-roundtable",
        "thread_title": "Welcome Thread",
        "post_id": "post-001",
        "author_name": "John Doe",
        "posted_at": "2024-01-15T10:30:00Z",
        "content_text": "This is a test discussion post.",
        "permalink": "https://example.com/roundtables/test-roundtable/discussions/1#post-001",
    }


@pytest.fixture
def minimal_config_dict() -> dict:
    """Minimal config dictionary for testing config loading."""
    return {
        "site": {
            "base_url": "https://test.example.com",
            "allowed_domains": ["test.example.com"],
        },
        "patterns": {
            "speaker_url": ".*/speakers?/[^/?#]+/?$",
            "roundtable_url": ".*/roundtables?/[^/?#]+/?$",
            "discussion_url": ".*/roundtables?/[^/?#]+/discussions?/.*$",
        },
        "selectors": {
            "speaker": {
                "name": "h1::text",
                "bio": ".bio::text",
            },
            "roundtable": {
                "title": "h1::text",
                "description": ".description::text",
                "speaker_links": "a[href*='/speaker']",
            },
            "discussion": {
                "thread_title": "h1::text",
                "posts": ".post",
                "post_id": "::attr(id)",
                "author": ".author::text",
                "posted_at": "time::text",
                "content": ".content::text",
            },
        },
    }
