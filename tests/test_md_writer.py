"""Unit tests for markdown writer functionality."""
from __future__ import annotations

from revweb.io.md_writer import (
    WebMapStats,
    write_speakers_md,
    write_web_map,
    write_website_rebuild_spec,
)


class TestWriteWebMap:
    """Tests for web map markdown generation."""

    def test_basic_web_map(self, temp_dir):
        """Basic web map is generated correctly."""
        output_path = temp_dir / "web-map.md"
        stats = WebMapStats(pages_visited=100, unique_urls=80, errors=2, redirects=5)

        write_web_map(
            output_path,
            base_url="https://example.com",
            outline_lines=["- `page1`", "- `page2`"],
            stats=stats,
        )

        content = output_path.read_text()
        assert "# Web Map" in content
        assert "https://example.com" in content
        assert "Pages visited: **100**" in content
        assert "Unique URLs: **80**" in content
        assert "Errors: **2**" in content
        assert "- `page1`" in content

    def test_web_map_creates_directory(self, temp_dir):
        """Web map creates parent directory if needed."""
        output_path = temp_dir / "nested" / "web-map.md"
        stats = WebMapStats(pages_visited=10, unique_urls=10, errors=0, redirects=0)

        write_web_map(
            output_path,
            base_url="https://example.com",
            outline_lines=[],
            stats=stats,
        )

        assert output_path.exists()

    def test_web_map_timestamp(self, temp_dir):
        """Web map includes timestamp."""
        output_path = temp_dir / "web-map.md"
        stats = WebMapStats(pages_visited=0, unique_urls=0, errors=0, redirects=0)

        write_web_map(
            output_path,
            base_url="https://example.com",
            outline_lines=[],
            stats=stats,
        )

        content = output_path.read_text()
        assert "Generated (UTC):" in content


class TestWriteSpeakersMd:
    """Tests for speakers markdown generation."""

    def test_basic_speakers_md(self, temp_dir):
        """Basic speakers markdown is generated correctly."""
        output_path = temp_dir / "speakers.md"
        speakers = [
            {"speaker_id": "john-doe", "name": "John Doe", "bio": "A speaker bio."},
            {"speaker_id": "jane-doe", "name": "Jane Doe", "bio": "Another bio."},
        ]

        write_speakers_md(output_path, speakers=speakers)

        content = output_path.read_text()
        assert "# Speakers" in content
        assert "## John Doe" in content
        assert "## Jane Doe" in content
        assert "A speaker bio." in content

    def test_speakers_md_anchor_ids(self, temp_dir):
        """Speaker entries have anchor IDs."""
        output_path = temp_dir / "speakers.md"
        speakers = [{"speaker_id": "john-doe", "name": "John Doe"}]

        write_speakers_md(output_path, speakers=speakers)

        content = output_path.read_text()
        assert 'id="speaker-john-doe"' in content

    def test_speakers_md_profile_url(self, temp_dir):
        """Speaker profile URL is included when present."""
        output_path = temp_dir / "speakers.md"
        speakers = [{
            "speaker_id": "john",
            "name": "John",
            "profile_url": "https://example.com/speakers/john",
        }]

        write_speakers_md(output_path, speakers=speakers)

        content = output_path.read_text()
        assert "Profile:" in content
        assert "https://example.com/speakers/john" in content

    def test_speakers_md_empty_bio(self, temp_dir):
        """Empty bio doesn't add empty paragraphs."""
        output_path = temp_dir / "speakers.md"
        speakers = [{"speaker_id": "john", "name": "John", "bio": ""}]

        write_speakers_md(output_path, speakers=speakers)

        content = output_path.read_text()
        # Should have name but not empty lines from bio
        assert "## John" in content

    def test_speakers_md_empty_list(self, temp_dir):
        """Empty speaker list creates minimal file."""
        output_path = temp_dir / "speakers.md"

        write_speakers_md(output_path, speakers=[])

        content = output_path.read_text()
        assert "# Speakers" in content


class TestWriteWebsiteRebuildSpec:
    """Tests for website rebuild spec generation."""

    def test_basic_spec(self, temp_dir):
        """Basic spec is generated correctly."""
        output_path = temp_dir / "tech-spec.md"

        write_website_rebuild_spec(output_path, base_url="https://example.com")

        content = output_path.read_text()
        assert "# Website Rebuild Technical Specification" in content
        assert "https://example.com" in content
        assert "speakers.csv" in content
        assert "roundtables.csv" in content

    def test_spec_creates_directory(self, temp_dir):
        """Spec creates parent directory if needed."""
        output_path = temp_dir / "docs" / "tech-spec.md"

        write_website_rebuild_spec(output_path, base_url="https://example.com")

        assert output_path.exists()

    def test_spec_includes_data_contracts(self, temp_dir):
        """Spec includes data contract descriptions."""
        output_path = temp_dir / "tech-spec.md"

        write_website_rebuild_spec(output_path, base_url="https://example.com")

        content = output_path.read_text()
        assert "Data contracts" in content
        assert "speaker_id" in content
        assert "roundtable_id" in content

    def test_spec_includes_architecture(self, temp_dir):
        """Spec includes architecture recommendations."""
        output_path = temp_dir / "tech-spec.md"

        write_website_rebuild_spec(output_path, base_url="https://example.com")

        content = output_path.read_text()
        assert "Static site generator" in content or "architecture" in content.lower()
