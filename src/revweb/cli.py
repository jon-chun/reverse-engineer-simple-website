from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .config import ensure_paths, load_config
from .logging import configure_logging
from .scrape.runner import run as run_scrapy
from .spec.website_rebuild import generate as generate_spec

app = typer.Typer(add_completion=False, help="Crawl and scrape websites into CSV and docs artifacts for reverse engineering.")
console = Console()


@app.command()
def crawl(
    config: str = typer.Option("config/config.yml", "--config", "-c", help="Path to config.yml"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
):
    """Crawl the website and generate ./docs/web-map.md"""
    logger = configure_logging(log_level, name="revweb")
    cfg = load_config(config)
    ensure_paths(cfg)
    logger.info(f"Crawling site: {cfg.site.base_url}")
    run_scrapy(cfg, mode="crawl", log_level="WARNING")
    console.print(f"Wrote {cfg.crawl.emit_web_map_path}")


@app.command()
def scrape(
    config: str = typer.Option("config/config.yml", "--config", "-c", help="Path to config.yml"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
):
    """Scrape speakers, roundtables, and discussions into ./data/*.csv"""
    logger = configure_logging(log_level, name="revweb")
    cfg = load_config(config)
    ensure_paths(cfg)
    logger.info(f"Scraping site: {cfg.site.base_url}")
    run_scrapy(cfg, mode="scrape", log_level="WARNING")
    console.print(f"Wrote {Path(cfg.scrape.outputs_dir) / cfg.scrape.speakers_csv}")
    console.print(f"Wrote {Path(cfg.scrape.outputs_dir) / cfg.scrape.roundtables_csv}")
    console.print(f"Wrote discussions as {cfg.scrape.discussions_csv_pattern}")


@app.command()
def spec(
    config: str = typer.Option("config/config.yml", "--config", "-c", help="Path to config.yml"),
):
    """Generate ./docs/tech-spec-website.md"""
    cfg = load_config(config)
    ensure_paths(cfg)
    generate_spec(cfg)
    console.print(f"Wrote {cfg.docs.tech_spec_path}")
