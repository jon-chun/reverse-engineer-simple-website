from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from rapidfuzz import fuzz

from ..config import AppConfig
from ..crawl.map_builder import build_path_tree, render_tree_md
from ..io.csv_writer import CsvSpec, StreamingCsvWriter
from ..io.md_writer import WebMapStats, write_speakers_md, write_web_map


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


class OutputPipeline:
    # Responsibilities:
    # - aggregate speakers and roundtables (dedupe)
    # - stream discussion posts per-roundtable to separate CSVs
    # - generate docs/web-map.md from spider seen URLs

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.out_dir = Path(cfg.scrape.outputs_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.speakers: dict[str, dict] = {}
        self.roundtables: dict[str, dict] = {}
        self.roundtable_speaker_links: dict[str, set[str]] = defaultdict(set)

        self.discussion_writers: dict[str, StreamingCsvWriter] = {}

        self._speaker_fields = [
            "speaker_id", "name", "bio", "title", "organization",
            "profile_url", "headshot_url", "social_links", "source_last_seen_utc",
        ]
        self._roundtable_fields = [
            "roundtable_id", "title", "description", "roundtable_url",
            "speaker_ids", "speakers_md_link", "source_last_seen_utc",
        ]
        self._discussion_fields = [
            "discussion_id", "roundtable_id", "thread_title", "post_id",
            "author_speaker_id", "author_name", "posted_at",
            "content_text", "permalink", "source_last_seen_utc",
        ]

        self._speakers_writer = StreamingCsvWriter(CsvSpec(self.out_dir / cfg.scrape.speakers_csv, self._speaker_fields))
        self._roundtables_writer = StreamingCsvWriter(CsvSpec(self.out_dir / cfg.scrape.roundtables_csv, self._roundtable_fields))

    @classmethod
    def from_crawler(cls, crawler):
        cfg: AppConfig = crawler.settings.get("APP_CONFIG")
        return cls(cfg)

    def open_spider(self, spider):
        if getattr(spider, "mode", "") == "scrape":
            self._speakers_writer.open()
            self._roundtables_writer.open()

    def close_spider(self, spider):
        mode = getattr(spider, "mode", "")
        if mode == "scrape":
            self._finalize_roundtable_speakers()

            self._speakers_writer.close()
            self._roundtables_writer.close()

            self._rewrite_csv(self.out_dir / self.cfg.scrape.speakers_csv, self._speaker_fields, self.speakers.values(), key="speaker_id")
            self._rewrite_csv(self.out_dir / self.cfg.scrape.roundtables_csv, self._roundtable_fields, self.roundtables.values(), key="roundtable_id")

            for w in self.discussion_writers.values():
                w.close()

            speakers_list = [self.speakers[k] for k in sorted(self.speakers.keys())]
            write_speakers_md(Path("./docs/speakers.md"), speakers=speakers_list)

        seen = getattr(spider, "seen_urls", set())
        tree = build_path_tree(seen)
        outline = render_tree_md(tree)

        counters = getattr(spider, "_counters", None)
        stats = WebMapStats(
            pages_visited=getattr(counters, "pages", len(seen)),
            unique_urls=len(seen),
            errors=getattr(counters, "errors", 0),
            redirects=getattr(counters, "redirects", 0),
        )
        write_web_map(self.cfg.crawl.emit_web_map_path, base_url=self.cfg.site.base_url, outline_lines=outline, stats=stats)

    def process_item(self, item: dict, spider):
        if getattr(spider, "mode", "") != "scrape":
            return item

        typ = item.get("type")
        data = item.get("data", {})

        if typ == "speaker":
            sid = data.get("speaker_id")
            if not sid:
                return item
            existing = self.speakers.get(sid)
            if existing:
                for k, v in data.items():
                    if v and not existing.get(k):
                        existing[k] = v
            else:
                self.speakers[sid] = data
                self._speakers_writer.write_row(data)

        elif typ == "roundtable":
            rid = data.get("roundtable_id")
            if not rid:
                return item
            if self.cfg.scrape.only_roundtable_ids and rid not in set(self.cfg.scrape.only_roundtable_ids):
                return item

            existing = self.roundtables.get(rid)
            if existing:
                for k, v in data.items():
                    if v and not existing.get(k):
                        existing[k] = v
            else:
                self.roundtables[rid] = data
                self._roundtables_writer.write_row(data)

            for link in item.get("speaker_links") or []:
                self.roundtable_speaker_links[rid].add(link)

        elif typ == "discussion":
            rid = data.get("roundtable_id") or "unknown"
            if self.cfg.scrape.only_roundtable_ids and rid not in set(self.cfg.scrape.only_roundtable_ids):
                return item
            writer = self._get_discussion_writer(rid)
            writer.write_row(data)

        return item

    def _get_discussion_writer(self, roundtable_id: str) -> StreamingCsvWriter:
        if roundtable_id not in self.discussion_writers:
            fname = self.cfg.scrape.discussions_csv_pattern.format(roundtable_id=roundtable_id)
            spec = CsvSpec(self.out_dir / fname, self._discussion_fields)
            w = StreamingCsvWriter(spec)
            w.open()
            self.discussion_writers[roundtable_id] = w
        return self.discussion_writers[roundtable_id]

    def _finalize_roundtable_speakers(self) -> None:
        url_to_id: dict[str, str] = {}
        name_to_id: dict[str, str] = {}
        for sid, s in self.speakers.items():
            if s.get("profile_url"):
                url_to_id[_norm(s["profile_url"])] = sid
            name_to_id[_norm(s.get("name", ""))] = sid

        for rid, rt in self.roundtables.items():
            links = self.roundtable_speaker_links.get(rid, set())
            speaker_ids: list[str] = []
            for link in links:
                sid = url_to_id.get(_norm(link))
                if sid:
                    speaker_ids.append(sid)

            if not speaker_ids and links:
                for link in links:
                    slug = _norm(link.rstrip("/").split("/")[-1].replace("-", " "))
                    best = None
                    best_score = 0
                    for nm, sid in name_to_id.items():
                        score = fuzz.token_set_ratio(slug, nm)
                        if score > best_score:
                            best_score = score
                            best = sid
                    if best and best_score >= 90:
                        speaker_ids.append(best)

            speaker_ids = sorted(set(speaker_ids))
            rt["speaker_ids"] = ",".join(speaker_ids)
            rt["speakers_md_link"] = "./speakers.md" if speaker_ids else ""

    def _rewrite_csv(self, path: Path, fieldnames: list[str], rows: Iterable[dict], *, key: str) -> None:
        import csv
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in sorted(list(rows), key=lambda x: (x.get(key) or "")):
                w.writerow({k: r.get(k, "") for k in fieldnames})
        tmp.replace(path)
