from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ...config import AppConfig
from ...crawl.map_builder import build_path_tree, render_tree_md
from ...io.csv_writer import CsvSpec, StreamingCsvWriter
from ...io.md_writer import WebMapStats, write_speakers_md, write_web_map
from .aggregator import OutputAggregator


class OutputWriter:
    """Writes aggregated data to CSV and Markdown files."""

    SPEAKER_FIELDS = [
        "speaker_id",
        "name",
        "bio",
        "title",
        "organization",
        "profile_url",
        "headshot_url",
        "social_links",
        "source_last_seen_utc",
    ]
    ROUNDTABLE_FIELDS = [
        "roundtable_id",
        "title",
        "description",
        "roundtable_url",
        "speaker_ids",
        "speakers_md_link",
        "source_last_seen_utc",
    ]
    DISCUSSION_FIELDS = [
        "discussion_id",
        "roundtable_id",
        "thread_title",
        "post_id",
        "author_speaker_id",
        "author_name",
        "posted_at",
        "content_text",
        "permalink",
        "source_last_seen_utc",
    ]

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.out_dir = Path(cfg.scrape.outputs_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def write_all(self, aggregator: OutputAggregator) -> None:
        """Write all aggregated data to files."""
        self._write_speakers_csv(aggregator.get_speakers())
        self._write_roundtables_csv(aggregator.get_roundtables())

        for rid in aggregator.discussions:
            self._write_discussions_csv(rid, aggregator.get_discussions(rid))

        write_speakers_md(
            Path("./docs/speakers.md"), speakers=aggregator.get_speakers()
        )

    def write_web_map(
        self,
        seen_urls: set[str],
        pages_visited: int = 0,
        errors: int = 0,
        redirects: int = 0,
    ) -> None:
        """Write the web map documentation."""
        tree = build_path_tree(seen_urls)
        outline = render_tree_md(tree)

        stats = WebMapStats(
            pages_visited=pages_visited or len(seen_urls),
            unique_urls=len(seen_urls),
            errors=errors,
            redirects=redirects,
        )
        write_web_map(
            self.cfg.crawl.emit_web_map_path,
            base_url=self.cfg.site.base_url,
            outline_lines=outline,
            stats=stats,
        )

    def _write_speakers_csv(self, speakers: list[dict]) -> None:
        """Write speakers to CSV."""
        path = self.out_dir / self.cfg.scrape.speakers_csv
        self._write_csv(path, self.SPEAKER_FIELDS, speakers, key="speaker_id")

    def _write_roundtables_csv(self, roundtables: list[dict]) -> None:
        """Write roundtables to CSV."""
        path = self.out_dir / self.cfg.scrape.roundtables_csv
        self._write_csv(
            path, self.ROUNDTABLE_FIELDS, roundtables, key="roundtable_id"
        )

    def _write_discussions_csv(
        self, roundtable_id: str, discussions: list[dict]
    ) -> None:
        """Write discussions for a roundtable to CSV."""
        fname = self.cfg.scrape.discussions_csv_pattern.format(
            roundtable_id=roundtable_id
        )
        path = self.out_dir / fname
        self._write_csv(path, self.DISCUSSION_FIELDS, discussions, key="discussion_id")

    def _write_csv(
        self,
        path: Path,
        fieldnames: list[str],
        rows: Iterable[dict],
        *,
        key: str,
    ) -> None:
        """Write rows to a CSV file, sorted by key."""
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in sorted(list(rows), key=lambda x: (x.get(key) or "")):
                w.writerow({k: r.get(k, "") for k in fieldnames})
        tmp.replace(path)
