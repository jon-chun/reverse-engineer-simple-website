"""Integration tests for the output pipeline."""
from __future__ import annotations

import csv
from unittest.mock import MagicMock

import pytest

from revweb.scrape.pipelines import OutputPipeline


class MockSpider:
    """Mock spider for pipeline testing."""

    def __init__(self, mode: str = "scrape"):
        self.mode = mode
        self.seen_urls = set()
        self._counters = MagicMock(pages=0, errors=0, redirects=0)


@pytest.fixture
def pipeline_with_temp_dir(app_config, temp_dir):
    """Create a pipeline with temporary output directory."""
    app_config.scrape.outputs_dir = str(temp_dir)
    app_config.crawl.emit_web_map_path = str(temp_dir / "web-map.md")
    pipeline = OutputPipeline(app_config)
    return pipeline, temp_dir


class TestOutputPipelineIntegration:
    """Integration tests for OutputPipeline."""

    def test_speaker_processing(self, pipeline_with_temp_dir, sample_speaker_data):
        """Speakers are processed and deduplicated."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)

        # Process same speaker twice
        item1 = {"type": "speaker", "data": sample_speaker_data.copy()}
        item2 = {"type": "speaker", "data": sample_speaker_data.copy()}
        item2["data"]["bio"] = "Updated bio"  # Should not override existing

        pipeline.process_item(item1, spider)
        pipeline.process_item(item2, spider)

        pipeline.close_spider(spider)

        # Check only one speaker in output
        assert len(pipeline.speakers) == 1
        # Original bio should be preserved
        assert pipeline.speakers["john-doe"]["bio"] == "A test speaker bio."

    def test_roundtable_processing(self, pipeline_with_temp_dir, sample_roundtable_data):
        """Roundtables are processed and stored."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)

        item = {"type": "roundtable", "data": sample_roundtable_data.copy(), "speaker_links": []}
        pipeline.process_item(item, spider)

        pipeline.close_spider(spider)

        assert len(pipeline.roundtables) == 1
        assert "test-roundtable" in pipeline.roundtables

    def test_discussion_processing(self, pipeline_with_temp_dir, sample_discussion_data):
        """Discussion posts are written to separate CSV files."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)

        item = {"type": "discussion", "data": sample_discussion_data.copy()}
        pipeline.process_item(item, spider)

        pipeline.close_spider(spider)

        # Check discussion CSV was created
        discussion_file = temp_dir / "discussion_test-roundtable.csv"
        assert discussion_file.exists()

    def test_csv_output_format(self, pipeline_with_temp_dir, sample_speaker_data):
        """CSV files are properly formatted."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)
        item = {"type": "speaker", "data": sample_speaker_data.copy()}
        pipeline.process_item(item, spider)
        pipeline.close_spider(spider)

        # Verify CSV structure
        speakers_csv = temp_dir / "speakers.csv"
        assert speakers_csv.exists()

        with open(speakers_csv) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["speaker_id"] == "john-doe"
        assert rows[0]["name"] == "John Doe"

    def test_web_map_generation(self, pipeline_with_temp_dir):
        """Web map is generated on spider close."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="crawl")
        spider.seen_urls = {
            "https://example.com/speakers/john",
            "https://example.com/roundtables/test",
        }

        pipeline.open_spider(spider)
        pipeline.close_spider(spider)

        web_map = temp_dir / "web-map.md"
        assert web_map.exists()
        content = web_map.read_text()
        assert "speakers" in content or "roundtables" in content

    def test_speaker_roundtable_linking(self, pipeline_with_temp_dir, sample_speaker_data, sample_roundtable_data):
        """Speakers are linked to roundtables correctly."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)

        # Add speaker
        speaker_item = {"type": "speaker", "data": sample_speaker_data.copy()}
        pipeline.process_item(speaker_item, spider)

        # Add roundtable with speaker link
        rt_item = {
            "type": "roundtable",
            "data": {
                "roundtable_id": "test-rt",
                "title": "Test RT",
                "description": "Test",
                "roundtable_url": "https://example.com/roundtables/test-rt",
                "speaker_ids": "",
                "speakers_md_link": None,
            },
            "speaker_links": ["https://example.com/speakers/john-doe"],
        }
        pipeline.process_item(rt_item, spider)

        pipeline.close_spider(spider)

        # Check speaker was linked
        rt = pipeline.roundtables.get("test-rt")
        assert rt is not None
        assert "john-doe" in rt.get("speaker_ids", "")

    def test_crawl_mode_no_csv(self, pipeline_with_temp_dir):
        """In crawl mode, CSV writers are not opened."""
        pipeline, temp_dir = pipeline_with_temp_dir
        spider = MockSpider(mode="crawl")

        pipeline.open_spider(spider)
        pipeline.close_spider(spider)

        # CSV files should not have data (or may not exist)
        speakers_csv = temp_dir / "speakers.csv"
        if speakers_csv.exists():
            with open(speakers_csv) as f:
                content = f.read()
            # Should only have header or be empty
            lines = content.strip().split("\n")
            assert len(lines) <= 1  # At most header line

    def test_only_roundtable_ids_filter(self, app_config, temp_dir, sample_discussion_data):
        """Only specified roundtable IDs are processed when filter is set."""
        app_config.scrape.outputs_dir = str(temp_dir)
        app_config.scrape.only_roundtable_ids = ["allowed-rt"]
        app_config.crawl.emit_web_map_path = str(temp_dir / "web-map.md")

        pipeline = OutputPipeline(app_config)
        spider = MockSpider(mode="scrape")

        pipeline.open_spider(spider)

        # This should be filtered out
        item = {"type": "discussion", "data": sample_discussion_data.copy()}
        pipeline.process_item(item, spider)

        pipeline.close_spider(spider)

        # Discussion file for test-roundtable should not exist
        discussion_file = temp_dir / "discussion_test-roundtable.csv"
        assert not discussion_file.exists()
