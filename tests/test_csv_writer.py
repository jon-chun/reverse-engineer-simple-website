"""Unit tests for CSV writer functionality."""
from __future__ import annotations

import csv

from revweb.io.csv_writer import CsvSpec, StreamingCsvWriter


class TestCsvSpec:
    """Tests for CSV specification."""

    def test_csv_spec_creation(self, temp_dir):
        """CsvSpec can be created with path and fieldnames."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name", "value"],
        )
        assert spec.path == temp_dir / "test.csv"
        assert spec.fieldnames == ["id", "name", "value"]


class TestStreamingCsvWriter:
    """Tests for streaming CSV writer."""

    def test_write_single_row(self, temp_dir):
        """Single row can be written."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "name": "Test"})
        writer.close()

        # Read and verify
        content = (temp_dir / "test.csv").read_text()
        assert "id,name" in content
        assert "1,Test" in content

    def test_write_multiple_rows(self, temp_dir):
        """Multiple rows can be written."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "name": "Alice"})
        writer.write_row({"id": "2", "name": "Bob"})
        writer.write_row({"id": "3", "name": "Charlie"})
        writer.close()

        # Read and verify
        with open(temp_dir / "test.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[2]["name"] == "Charlie"

    def test_auto_open_on_write(self, temp_dir):
        """Writer auto-opens on first write if not explicitly opened."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id"],
        )
        writer = StreamingCsvWriter(spec)
        # Don't call open(), directly write
        writer.write_row({"id": "1"})
        writer.close()

        assert (temp_dir / "test.csv").exists()

    def test_missing_fields_become_empty(self, temp_dir):
        """Missing fields in row data become empty strings."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name", "optional"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "name": "Test"})  # Missing 'optional'
        writer.close()

        with open(temp_dir / "test.csv") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["optional"] == ""

    def test_extra_fields_ignored(self, temp_dir):
        """Extra fields not in fieldnames are ignored."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "name": "Test", "extra": "ignored"})
        writer.close()

        content = (temp_dir / "test.csv").read_text()
        assert "extra" not in content
        assert "ignored" not in content

    def test_creates_parent_directories(self, temp_dir):
        """Writer creates parent directories if they don't exist."""
        spec = CsvSpec(
            path=temp_dir / "nested" / "path" / "test.csv",
            fieldnames=["id"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1"})
        writer.close()

        assert (temp_dir / "nested" / "path" / "test.csv").exists()

    def test_unicode_content(self, temp_dir):
        """Unicode content is handled correctly."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "name"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "name": "Test"})
        writer.close()

        content = (temp_dir / "test.csv").read_text(encoding="utf-8")
        assert "Test" in content

    def test_special_characters(self, temp_dir):
        """Special characters (commas, quotes) are escaped properly."""
        spec = CsvSpec(
            path=temp_dir / "test.csv",
            fieldnames=["id", "description"],
        )
        writer = StreamingCsvWriter(spec)
        writer.open()
        writer.write_row({"id": "1", "description": 'Has "quotes" and, commas'})
        writer.close()

        with open(temp_dir / "test.csv") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["description"] == 'Has "quotes" and, commas'
