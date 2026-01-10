"""Unit tests for common extractor utilities."""
from __future__ import annotations

from revweb.scrape.extractors.common import (
    abs_url,
    id_from_url,
    join_text,
    normalize_whitespace,
)


class TestNormalizeWhitespace:
    """Tests for whitespace normalization."""

    def test_basic_normalization(self):
        """Multiple spaces are collapsed."""
        assert normalize_whitespace("a  b  c") == "a b c"

    def test_newlines_normalized(self):
        """Newlines become spaces."""
        assert normalize_whitespace("a\nb\nc") == "a b c"

    def test_tabs_normalized(self):
        """Tabs become spaces."""
        assert normalize_whitespace("a\tb\tc") == "a b c"

    def test_mixed_whitespace(self):
        """Mixed whitespace is normalized."""
        assert normalize_whitespace(" a  b \n c \t d ") == "a b c d"

    def test_empty_string(self):
        """Empty string returns empty."""
        assert normalize_whitespace("") == ""

    def test_none_input(self):
        """None input returns empty string."""
        assert normalize_whitespace(None) == ""

    def test_only_whitespace(self):
        """Only whitespace returns empty."""
        assert normalize_whitespace("   \n\t  ") == ""


class TestJoinText:
    """Tests for text joining."""

    def test_basic_join(self):
        """Basic list joining."""
        assert join_text(["a", "b", "c"]) == "a b c"

    def test_filters_empty(self):
        """Empty strings are filtered out."""
        assert join_text(["a", "", "b", "  ", "c"]) == "a b c"

    def test_normalizes_items(self):
        """Items are normalized before joining."""
        assert join_text(["  a  ", "\n b \n", "c"]) == "a b c"

    def test_empty_list(self):
        """Empty list returns empty string."""
        assert join_text([]) == ""

    def test_all_empty(self):
        """List of empty strings returns empty."""
        assert join_text(["", "  ", "\n"]) == ""

    def test_single_item(self):
        """Single item list returns that item."""
        assert join_text(["hello"]) == "hello"


class TestIdFromUrl:
    """Tests for extracting ID from URL."""

    def test_simple_path(self):
        """Simple path returns last segment."""
        assert id_from_url("https://example.com/speakers/john-doe") == "john-doe"

    def test_trailing_slash(self):
        """Trailing slash is stripped."""
        assert id_from_url("https://example.com/speakers/john-doe/") == "john-doe"

    def test_nested_path(self):
        """Nested path returns last segment."""
        url = "https://example.com/events/2024/roundtables/ai-future"
        assert id_from_url(url) == "ai-future"

    def test_root_url(self):
        """Root URL returns 'root'."""
        assert id_from_url("https://example.com/") == "root"
        assert id_from_url("https://example.com") == "root"

    def test_query_params_ignored(self):
        """Query params are part of urlparse.path, but we use path only."""
        # Note: query params are NOT part of path, so this works
        url = "https://example.com/speakers/john?tab=bio"
        assert id_from_url(url) == "john"


class TestAbsUrl:
    """Tests for absolute URL construction."""

    def test_relative_url(self):
        """Relative URL is resolved."""
        result = abs_url("https://example.com/page", "/images/photo.jpg")
        assert result == "https://example.com/images/photo.jpg"

    def test_absolute_url(self):
        """Absolute URL is returned unchanged."""
        result = abs_url("https://example.com/page", "https://cdn.example.com/photo.jpg")
        assert result == "https://cdn.example.com/photo.jpg"

    def test_none_input(self):
        """None input returns None."""
        assert abs_url("https://example.com", None) is None

    def test_empty_string(self):
        """Empty string returns None."""
        assert abs_url("https://example.com", "") is None

    def test_protocol_relative(self):
        """Protocol-relative URL is resolved."""
        result = abs_url("https://example.com/page", "//cdn.example.com/photo.jpg")
        assert result == "https://cdn.example.com/photo.jpg"
