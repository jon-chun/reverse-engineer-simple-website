from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider

from ...config import AppConfig
from ...crawl.url_rules import canonicalize, is_denied
from ..extractors.discussions import extract_discussion_posts
from ..extractors.roundtables import extract_roundtable
from ..extractors.speakers import extract_speaker


@dataclass
class CrawlCounters:
    pages: int = 0
    errors: int = 0
    redirects: int = 0


class SiteSpider(Spider):
    name = "speaking_events_site"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "LOG_LEVEL": "WARNING",
        "DOWNLOAD_TIMEOUT": 30,
        "RETRY_TIMES": 2,
    }

    def __init__(self, *, cfg: AppConfig, mode: str, **kwargs):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.mode = mode  # "crawl" or "scrape"
        self.allowed_domains = cfg.site.allowed_domains
        self.start_urls = cfg.site.start_urls or [cfg.site.base_url.rstrip("/") + p for p in cfg.site.start_paths]
        self._seen: set[str] = set()
        self._edges: dict[str, set[str]] = {}
        self._counters = CrawlCounters()

        self._speaker_re = re.compile(cfg.patterns.speaker_url)
        self._roundtable_re = re.compile(cfg.patterns.roundtable_url)
        self._discussion_re = re.compile(cfg.patterns.discussion_url)

        self._link_extractor = LinkExtractor(allow_domains=self.allowed_domains)

    def start_requests(self) -> Iterable[Request]:
        headers = {"User-Agent": self.cfg.site.user_agent}
        for u in self.start_urls:
            yield Request(u, headers=headers, callback=self.parse, dont_filter=True)

    def _canon(self, url: str) -> str:
        return canonicalize(
            url,
            base_url=self.cfg.site.base_url,
            include_query_params=self.cfg.crawl.include_query_params,
        )

    def _track_edge(self, src: str, dst: str) -> None:
        self._edges.setdefault(src, set()).add(dst)

    def parse(self, response: Response, **kwargs):
        self._counters.pages += 1

        canon = self._canon(str(response.url))
        if canon in self._seen:
            return
        self._seen.add(canon)

        for link in self._link_extractor.extract_links(response):
            dst = self._canon(link.url)
            if is_denied(dst, self.cfg.crawl.deny_patterns):
                continue
            self._track_edge(canon, dst)
            depth = int(response.meta.get("depth", 0))
            if depth >= self.cfg.crawl.max_depth:
                continue
            if len(self._seen) >= self.cfg.crawl.max_pages:
                continue
            yield response.follow(dst, callback=self.parse)

        if self.mode != "scrape":
            return

        url = str(response.url)

        if self._speaker_re.match(url):
            s = extract_speaker(
                response,
                name_sel=self.cfg.selectors.speaker.name,
                bio_sel=self.cfg.selectors.speaker.bio,
                title_sel=self.cfg.selectors.speaker.title,
                org_sel=self.cfg.selectors.speaker.organization,
                headshot_sel=self.cfg.selectors.speaker.headshot_url,
                socials_sel=self.cfg.selectors.speaker.social_links,
                id_from_url_flag=self.cfg.selectors.speaker.id_from_url,
            )
            if s:
                yield {"type": "speaker", "data": s.model_dump()}
            return

        if self._roundtable_re.match(url):
            r = extract_roundtable(
                response,
                title_sel=self.cfg.selectors.roundtable.title,
                desc_sel=self.cfg.selectors.roundtable.description,
                speaker_links_sel=self.cfg.selectors.roundtable.speaker_links,
                id_from_url_flag=self.cfg.selectors.roundtable.id_from_url,
            )
            if r:
                speaker_links = []
                for a in response.css(self.cfg.selectors.roundtable.speaker_links):
                    href = a.attrib.get("href")
                    if href:
                        speaker_links.append(response.urljoin(href))
                yield {"type": "roundtable", "data": r.model_dump(), "speaker_links": sorted(set(speaker_links))}

                for link in self._link_extractor.extract_links(response):
                    if self._discussion_re.match(link.url):
                        yield response.follow(link.url, callback=self.parse_discussion, meta={"roundtable_id": r.roundtable_id})
            return

        if self._discussion_re.match(url):
            rid = response.meta.get("roundtable_id") or "unknown"
            yield from self.parse_discussion(response, roundtable_id=rid)

    def parse_discussion(self, response: Response, roundtable_id: str | None = None, **kwargs):
        rid = roundtable_id or response.meta.get("roundtable_id") or "unknown"
        posts = extract_discussion_posts(
            response,
            roundtable_id=rid,
            thread_title_sel=self.cfg.selectors.discussion.thread_title,
            posts_sel=self.cfg.selectors.discussion.posts,
            post_id_sel=self.cfg.selectors.discussion.post_id,
            author_sel=self.cfg.selectors.discussion.author,
            posted_at_sel=self.cfg.selectors.discussion.posted_at,
            content_sel=self.cfg.selectors.discussion.content,
            permalink_sel=self.cfg.selectors.discussion.permalink,
        )
        for p in posts:
            yield {"type": "discussion", "data": p.model_dump()}

    @property
    def seen_urls(self) -> set[str]:
        return self._seen

    @property
    def edges(self) -> dict[str, set[str]]:
        return self._edges
