"""Unit tests for URL rules and canonicalization."""
from __future__ import annotations

from revweb.crawl.url_rules import canonicalize, is_denied


class TestCanonicalize:
    """Tests for URL canonicalization."""

    def test_basic_url(self):
        """Basic URL is returned unchanged."""
        result = canonicalize(
            "https://example.com/page",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/page"

    def test_relative_url(self):
        """Relative URL is resolved against base."""
        result = canonicalize(
            "/speakers/john",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/speakers/john"

    def test_strips_query_params_by_default(self):
        """Query params are stripped when include_query_params=False."""
        result = canonicalize(
            "https://example.com/page?foo=bar&baz=qux",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/page"
        assert "?" not in result

    def test_preserves_query_params_when_requested(self):
        """Query params are preserved when include_query_params=True."""
        result = canonicalize(
            "https://example.com/page?foo=bar",
            base_url="https://example.com",
            include_query_params=True,
        )
        assert "foo=bar" in result

    def test_strips_fragment(self):
        """Fragment is always stripped."""
        result = canonicalize(
            "https://example.com/page#section",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert "#" not in result
        assert result == "https://example.com/page"

    def test_normalizes_trailing_slashes(self):
        """Multiple trailing slashes are normalized."""
        result = canonicalize(
            "https://example.com/page///",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/page/"

    def test_root_path(self):
        """Root path is preserved."""
        result = canonicalize(
            "https://example.com/",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/"

    def test_empty_path_gets_slash(self):
        """Empty path becomes /."""
        result = canonicalize(
            "https://example.com",
            base_url="https://example.com",
            include_query_params=False,
        )
        assert result == "https://example.com/"


class TestIsDenied:
    """Tests for URL denial patterns."""

    def test_empty_patterns(self):
        """No patterns means nothing is denied."""
        assert is_denied("https://example.com/anything", []) is False

    def test_simple_match(self):
        """Simple pattern matches URL."""
        patterns = ["/login", "/account"]
        assert is_denied("https://example.com/login", patterns) is True
        assert is_denied("https://example.com/account/settings", patterns) is True

    def test_no_match(self):
        """URL not matching any pattern is allowed."""
        patterns = ["/login", "/account"]
        assert is_denied("https://example.com/speakers", patterns) is False

    def test_regex_pattern(self):
        """Regex patterns work correctly."""
        patterns = [r".*\.(pdf|jpg|png)$"]
        assert is_denied("https://example.com/doc.pdf", patterns) is True
        assert is_denied("https://example.com/image.jpg", patterns) is True
        assert is_denied("https://example.com/page.html", patterns) is False

    def test_pattern_anchoring(self):
        """Pattern matching uses search, not just match."""
        patterns = ["/admin"]
        assert is_denied("https://example.com/admin", patterns) is True
        assert is_denied("https://example.com/path/admin/page", patterns) is True

    def test_multiple_patterns(self):
        """Multiple patterns are all checked."""
        patterns = ["/login", "/logout", "/admin"]
        assert is_denied("https://example.com/login", patterns) is True
        assert is_denied("https://example.com/logout", patterns) is True
        assert is_denied("https://example.com/admin", patterns) is True
        assert is_denied("https://example.com/public", patterns) is False
