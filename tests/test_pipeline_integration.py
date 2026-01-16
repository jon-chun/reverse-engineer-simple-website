"""Integration tests for the output modules."""
from __future__ import annotations

import csv

import pytest

from revweb.scrape.output import OutputAggregator, OutputWriter, link_roundtable_speakers


class TestOutputAggregator:
    """Tests for OutputAggregator."""

    def test_add_speaker_new(self, sample_speaker_data):
        """Adding a new speaker returns True."""
        agg = OutputAggregator()
        result = agg.add_speaker(sample_speaker_data.copy())
        assert result is True
        assert len(agg.speakers) == 1

    def test_add_speaker_duplicate(self, sample_speaker_data):
        """Adding duplicate speaker returns False and merges."""
        agg = OutputAggregator()
        agg.add_speaker(sample_speaker_data.copy())

        updated = sample_speaker_data.copy()
        updated["bio"] = "New bio"  # Should not override existing
        result = agg.add_speaker(updated)

        assert result is False
        assert len(agg.speakers) == 1
        # Original bio preserved
        assert agg.speakers["john-doe"]["bio"] == "A test speaker bio."

    def test_add_speaker_fills_missing(self, sample_speaker_data):
        """Adding duplicate fills in missing fields."""
        agg = OutputAggregator()

        sparse = {"speaker_id": "john-doe", "name": "John Doe"}
        agg.add_speaker(sparse)

        agg.add_speaker(sample_speaker_data.copy())

        # Bio should now be filled
        assert agg.speakers["john-doe"]["bio"] == "A test speaker bio."

    def test_add_roundtable_new(self, sample_roundtable_data):
        """Adding a new roundtable returns True."""
        agg = OutputAggregator()
        result = agg.add_roundtable(sample_roundtable_data.copy())
        assert result is True
        assert len(agg.roundtables) == 1

    def test_add_roundtable_with_speaker_links(self, sample_roundtable_data):
        """Speaker links are tracked."""
        agg = OutputAggregator()
        links = ["https://example.com/speakers/john-doe"]
        agg.add_roundtable(sample_roundtable_data.copy(), speaker_links=links)

        assert "test-roundtable" in agg.roundtable_speaker_links
        assert links[0] in agg.roundtable_speaker_links["test-roundtable"]

    def test_add_discussion(self, sample_discussion_data):
        """Discussions are stored by roundtable."""
        agg = OutputAggregator()
        result = agg.add_discussion(sample_discussion_data.copy())

        assert result is True
        discussions = agg.get_discussions("test-roundtable")
        assert len(discussions) == 1

    def test_get_speakers_sorted(self):
        """get_speakers returns sorted list."""
        agg = OutputAggregator()
        agg.add_speaker({"speaker_id": "zach", "name": "Zach"})
        agg.add_speaker({"speaker_id": "alice", "name": "Alice"})

        speakers = agg.get_speakers()
        assert speakers[0]["speaker_id"] == "alice"
        assert speakers[1]["speaker_id"] == "zach"


class TestLinkRoundtableSpeakers:
    """Tests for speaker-roundtable linking."""

    def test_link_by_url(self, sample_speaker_data, sample_roundtable_data):
        """Speakers are linked by matching profile URL."""
        agg = OutputAggregator()
        agg.add_speaker(sample_speaker_data.copy())

        rt = sample_roundtable_data.copy()
        rt["speaker_ids"] = ""
        agg.add_roundtable(rt, speaker_links=["https://example.com/speakers/john-doe"])

        link_roundtable_speakers(agg)

        linked_rt = agg.roundtables["test-roundtable"]
        assert "john-doe" in linked_rt["speaker_ids"]

    def test_link_by_fuzzy_name(self):
        """Speakers are linked by fuzzy name matching."""
        agg = OutputAggregator()
        agg.add_speaker({"speaker_id": "john-doe", "name": "John Doe", "profile_url": ""})
        agg.add_roundtable(
            {"roundtable_id": "rt1", "title": "RT1"},
            speaker_links=["https://example.com/speakers/john-doe"]
        )

        link_roundtable_speakers(agg)

        linked_rt = agg.roundtables["rt1"]
        assert "john-doe" in linked_rt["speaker_ids"]


class TestOutputWriter:
    """Tests for OutputWriter."""

    def test_write_speakers_csv(self, app_config, temp_dir, sample_speaker_data):
        """Speakers are written to CSV."""
        app_config.scrape.outputs_dir = str(temp_dir)
        writer = OutputWriter(app_config)

        agg = OutputAggregator()
        agg.add_speaker(sample_speaker_data.copy())

        writer.write_all(agg)

        speakers_csv = temp_dir / "speakers.csv"
        assert speakers_csv.exists()

        with open(speakers_csv) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["speaker_id"] == "john-doe"
        assert rows[0]["name"] == "John Doe"

    def test_write_roundtables_csv(self, app_config, temp_dir, sample_roundtable_data):
        """Roundtables are written to CSV."""
        app_config.scrape.outputs_dir = str(temp_dir)
        writer = OutputWriter(app_config)

        agg = OutputAggregator()
        agg.add_roundtable(sample_roundtable_data.copy())

        writer.write_all(agg)

        roundtables_csv = temp_dir / "roundtables.csv"
        assert roundtables_csv.exists()

        with open(roundtables_csv) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["roundtable_id"] == "test-roundtable"

    def test_write_discussions_csv(self, app_config, temp_dir, sample_discussion_data):
        """Discussions are written to separate CSV files."""
        app_config.scrape.outputs_dir = str(temp_dir)
        writer = OutputWriter(app_config)

        agg = OutputAggregator()
        agg.add_discussion(sample_discussion_data.copy())

        writer.write_all(agg)

        discussion_csv = temp_dir / "discussion_test-roundtable.csv"
        assert discussion_csv.exists()

    def test_write_web_map(self, app_config, temp_dir):
        """Web map is written correctly."""
        app_config.scrape.outputs_dir = str(temp_dir)
        app_config.crawl.emit_web_map_path = str(temp_dir / "web-map.md")
        writer = OutputWriter(app_config)

        seen_urls = {
            "https://example.com/speakers/john",
            "https://example.com/roundtables/test",
        }

        writer.write_web_map(seen_urls, pages_visited=2)

        web_map = temp_dir / "web-map.md"
        assert web_map.exists()
        content = web_map.read_text()
        assert "speakers" in content or "roundtables" in content
