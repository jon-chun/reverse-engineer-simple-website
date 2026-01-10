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


class TestEntityUrlPatterns:
    """Tests for entity URL pattern matching (speakers, roundtables).

    These tests ensure URL patterns correctly match individual entity pages
    while excluding aggregate listing pages (like year-based listings).
    """

    def test_speaker_pattern_matches_slug(self):
        """Speaker pattern matches slug-based URLs."""
        import re
        pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        assert pattern.match("https://example.com/participants/john-doe/")
        assert pattern.match("https://example.com/participants/jane-smith")
        assert pattern.match("https://example.com/participants/mark-epstein/")

    def test_speaker_pattern_rejects_year_listing(self):
        """Speaker pattern does NOT match year-based listing pages."""
        import re
        pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        # Year-based listings should NOT match
        assert not pattern.match("https://example.com/participants/2012/")
        assert not pattern.match("https://example.com/participants/2023/")
        assert not pattern.match("https://example.com/participants/2019")
        assert not pattern.match("https://example.com/participants/2020/")

    def test_roundtable_pattern_matches_slug(self):
        """Roundtable pattern matches slug-based URLs."""
        import re
        pattern = re.compile(r".*/roundtables/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        assert pattern.match("https://example.com/roundtables/neurodiversity/")
        assert pattern.match("https://example.com/roundtables/consciousness")
        assert pattern.match("https://example.com/roundtables/the-future-of-ai/")

    def test_roundtable_pattern_rejects_year_listing(self):
        """Roundtable pattern does NOT match year-based listing pages."""
        import re
        pattern = re.compile(r".*/roundtables/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        # Year-based listings should NOT match
        assert not pattern.match("https://example.com/roundtables/2012/")
        assert not pattern.match("https://example.com/roundtables/2021/")
        assert not pattern.match("https://example.com/roundtables/2018")
        assert not pattern.match("https://example.com/roundtables/2023/")

    def test_pattern_rejects_index_pages(self):
        """Patterns do NOT match index/listing pages."""
        import re
        speaker_pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        roundtable_pattern = re.compile(r".*/roundtables/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")

        # Index pages should NOT match
        assert not speaker_pattern.match("https://example.com/participants/")
        assert not roundtable_pattern.match("https://example.com/roundtables/")

    def test_pattern_rejects_query_params(self):
        """Patterns do NOT match URLs with query parameters in path segment."""
        import re
        pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        # Query params after slug should still match (query is stripped elsewhere)
        assert pattern.match("https://example.com/participants/john-doe/")
        # But query params should be handled correctly
        assert not pattern.match("https://example.com/participants/john-doe?page=2")

    def test_slug_with_numbers_still_matches(self):
        """Slugs containing numbers (but not pure 4-digit years) still match."""
        import re
        speaker_pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        roundtable_pattern = re.compile(r".*/roundtables/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")

        # Mixed alphanumeric slugs should match
        assert speaker_pattern.match("https://example.com/participants/speaker2023/")
        assert speaker_pattern.match("https://example.com/participants/john-doe-2/")
        assert roundtable_pattern.match("https://example.com/roundtables/ai-2024-edition/")
        assert roundtable_pattern.match("https://example.com/roundtables/event123/")

    def test_pattern_rejects_single_letter_alphabetical(self):
        """Patterns do NOT match single-letter alphabetical listing pages."""
        import re
        speaker_pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")
        roundtable_pattern = re.compile(r".*/roundtables/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")

        # Single uppercase letter should NOT match (alphabetical listings)
        assert not speaker_pattern.match("https://example.com/participants/A/")
        assert not speaker_pattern.match("https://example.com/participants/Z/")
        assert not speaker_pattern.match("https://example.com/participants/M")
        assert not roundtable_pattern.match("https://example.com/roundtables/B/")

    def test_lowercase_slugs_still_match(self):
        """Lowercase single-letter slugs still match (rare but valid)."""
        import re
        speaker_pattern = re.compile(r".*/participants/(?!\d{4}/?$)(?![A-Z]/?$)[^/?#]+/?$")

        # Lowercase single letter should match (not the same as alphabetical listings)
        assert speaker_pattern.match("https://example.com/participants/a/")
        assert speaker_pattern.match("https://example.com/participants/x-ray/")
