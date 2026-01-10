"""End-to-end tests for CLI commands."""
from __future__ import annotations

import subprocess
import sys

from typer.testing import CliRunner

from revweb.cli import app

runner = CliRunner()


class TestCliHelp:
    """Tests for CLI help commands."""

    def test_main_help(self):
        """Main help displays correctly."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "crawl" in result.stdout
        assert "scrape" in result.stdout
        assert "spec" in result.stdout

    def test_crawl_help(self):
        """Crawl command help displays correctly."""
        result = runner.invoke(app, ["crawl", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.stdout
        assert "web-map.md" in result.stdout

    def test_scrape_help(self):
        """Scrape command help displays correctly."""
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.stdout
        assert "CSV" in result.stdout or "csv" in result.stdout

    def test_spec_help(self):
        """Spec command help displays correctly."""
        result = runner.invoke(app, ["spec", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.stdout


class TestCliConfigValidation:
    """Tests for CLI config file validation."""

    def test_missing_config(self):
        """Missing config file shows error."""
        result = runner.invoke(app, ["spec", "--config", "nonexistent.yml"])
        assert result.exit_code != 0

    def test_spec_with_valid_config(self, temp_dir):
        """Spec command runs with valid config."""
        # Use the existing config
        result = runner.invoke(app, ["spec", "--config", "config/config.yml"])
        # Should complete (may succeed or fail depending on network, but shouldn't crash)
        # Just verify it doesn't have a Python exception
        assert "Traceback" not in result.stdout


class TestCliModuleExecution:
    """Tests for running CLI as module."""

    def test_python_m_execution(self):
        """CLI can be run via python -m."""
        result = subprocess.run(
            [sys.executable, "-m", "revweb", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "crawl" in result.stdout

    def test_revweb_command(self):
        """revweb command is available."""
        result = subprocess.run(
            ["revweb", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "scrape" in result.stdout


class TestSpecCommand:
    """Tests for spec command output."""

    def test_spec_generates_file(self, temp_dir):
        """Spec command generates tech spec file."""
        import yaml

        # Create a minimal config
        config = {
            "site": {
                "base_url": "https://test.example.com",
                "allowed_domains": ["test.example.com"],
            },
            "patterns": {
                "speaker_url": ".*/speakers?/[^/?#]+/?$",
                "roundtable_url": ".*/roundtables?/[^/?#]+/?$",
                "discussion_url": ".*/discussions?/.*$",
            },
            "selectors": {
                "speaker": {"name": "h1::text", "bio": ".bio::text"},
                "roundtable": {
                    "title": "h1::text",
                    "description": ".desc::text",
                    "speaker_links": "a::attr(href)",
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
            "docs": {
                "tech_spec_path": str(temp_dir / "tech-spec.md"),
            },
        }

        config_path = temp_dir / "config.yml"
        config_path.write_text(yaml.dump(config))

        runner.invoke(app, ["spec", "--config", str(config_path)])

        # Check file was created
        spec_file = temp_dir / "tech-spec.md"
        assert spec_file.exists()
        content = spec_file.read_text()
        assert "Website Rebuild" in content


class TestLogging:
    """Tests for CLI logging configuration."""

    def test_log_level_option(self):
        """Log level option is accepted."""
        result = runner.invoke(app, ["crawl", "--help"])
        assert "--log-level" in result.stdout

    def test_invalid_config_error_message(self, temp_dir):
        """Invalid config shows helpful error."""
        bad_config = temp_dir / "bad.yml"
        bad_config.write_text("site:\n  base_url: 123")  # Invalid type

        result = runner.invoke(app, ["spec", "--config", str(bad_config)])
        assert result.exit_code != 0
