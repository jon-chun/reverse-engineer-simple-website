from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext

from ..config import AppConfig
from ..scrape.extractors.discussions import extract_discussion_posts
from ..scrape.extractors.roundtables import extract_roundtable
from ..scrape.extractors.speakers import extract_speaker
from ..scrape.output import OutputAggregator
from .url_rules import canonicalize, is_denied

if TYPE_CHECKING:
    from parsel import Selector


@dataclass
class CrawlCounters:
    """Counters for crawl statistics."""

    pages: int = 0
    errors: int = 0
    redirects: int = 0


@dataclass
class CrawlState:
    """Shared state for the crawler."""

    cfg: AppConfig
    mode: str  # "crawl" or "scrape"
    seen: set[str] = field(default_factory=set)
    edges: dict[str, set[str]] = field(default_factory=dict)
    counters: CrawlCounters = field(default_factory=CrawlCounters)
    aggregator: OutputAggregator = field(default_factory=OutputAggregator)

    speaker_re: re.Pattern | None = None
    roundtable_re: re.Pattern | None = None
    discussion_re: re.Pattern | None = None

    def __post_init__(self) -> None:
        self.speaker_re = re.compile(self.cfg.patterns.speaker_url)
        self.roundtable_re = re.compile(self.cfg.patterns.roundtable_url)
        self.discussion_re = re.compile(self.cfg.patterns.discussion_url)

    def canon(self, url: str) -> str:
        return canonicalize(
            url,
            base_url=self.cfg.site.base_url,
            include_query_params=self.cfg.crawl.include_query_params,
        )

    def track_edge(self, src: str, dst: str) -> None:
        self.edges.setdefault(src, set()).add(dst)


def create_handler(state: CrawlState):
    """Create the request handler for the crawler."""

    async def handler(context: ParselCrawlingContext) -> None:
        state.counters.pages += 1
        url = str(context.request.url)
        canon = state.canon(url)

        if canon in state.seen:
            return
        state.seen.add(canon)

        selector = context.selector
        await _extract_and_enqueue_links(context, state, canon, selector)

        if state.mode != "scrape":
            return

        await _extract_content(context, state, url, selector)

    return handler


async def _extract_and_enqueue_links(
    context: ParselCrawlingContext,
    state: CrawlState,
    canon: str,
    selector: "Selector",
) -> None:
    """Extract links and enqueue them for crawling."""
    depth = context.request.user_data.get("depth", 0)
    requests_to_add: list[Request] = []

    for link in selector.css("a::attr(href)").getall():
        if not link:
            continue

        abs_link = urljoin(str(context.request.url), link)
        dst = state.canon(abs_link)

        if is_denied(dst, state.cfg.crawl.deny_patterns):
            continue

        parsed = urlparse(dst)
        if parsed.netloc not in state.cfg.site.allowed_domains:
            continue

        state.track_edge(canon, dst)

        if depth >= state.cfg.crawl.max_depth:
            continue
        if len(state.seen) >= state.cfg.crawl.max_pages:
            continue

        requests_to_add.append(
            Request.from_url(dst, user_data={"depth": depth + 1})
        )

    if requests_to_add:
        await context.add_requests(requests_to_add)


async def _extract_content(
    context: ParselCrawlingContext,
    state: CrawlState,
    url: str,
    selector: "Selector",
) -> None:
    """Extract content based on URL patterns."""
    if state.speaker_re and state.speaker_re.match(url):
        speaker = extract_speaker(
            selector,
            url,
            name_sel=state.cfg.selectors.speaker.name,
            bio_sel=state.cfg.selectors.speaker.bio,
            title_sel=state.cfg.selectors.speaker.title,
            org_sel=state.cfg.selectors.speaker.organization,
            headshot_sel=state.cfg.selectors.speaker.headshot_url,
            socials_sel=state.cfg.selectors.speaker.social_links,
            id_from_url_flag=state.cfg.selectors.speaker.id_from_url,
        )
        if speaker:
            state.aggregator.add_speaker(speaker.model_dump())
        return

    if state.roundtable_re and state.roundtable_re.match(url):
        roundtable = extract_roundtable(
            selector,
            url,
            title_sel=state.cfg.selectors.roundtable.title,
            desc_sel=state.cfg.selectors.roundtable.description,
            speaker_links_sel=state.cfg.selectors.roundtable.speaker_links,
            id_from_url_flag=state.cfg.selectors.roundtable.id_from_url,
        )
        if roundtable:
            speaker_links = []
            for a in selector.css(state.cfg.selectors.roundtable.speaker_links):
                href = a.attrib.get("href")
                if href:
                    speaker_links.append(urljoin(url, href))
            state.aggregator.add_roundtable(
                roundtable.model_dump(), speaker_links=speaker_links
            )

            # Enqueue discussion links
            if state.discussion_re:
                discussion_requests: list[Request] = []
                for link in selector.css("a::attr(href)").getall():
                    if not link:
                        continue
                    abs_link = urljoin(url, link)
                    if state.discussion_re.match(abs_link):
                        discussion_requests.append(
                            Request.from_url(
                                abs_link,
                                user_data={
                                    "roundtable_id": roundtable.roundtable_id,
                                    "depth": context.request.user_data.get("depth", 0) + 1,
                                },
                            )
                        )
                if discussion_requests:
                    await context.add_requests(discussion_requests)
        return

    if state.discussion_re and state.discussion_re.match(url):
        rid = context.request.user_data.get("roundtable_id") or "unknown"
        posts = extract_discussion_posts(
            selector,
            url,
            roundtable_id=rid,
            thread_title_sel=state.cfg.selectors.discussion.thread_title,
            posts_sel=state.cfg.selectors.discussion.posts,
            post_id_sel=state.cfg.selectors.discussion.post_id,
            author_sel=state.cfg.selectors.discussion.author,
            posted_at_sel=state.cfg.selectors.discussion.posted_at,
            content_sel=state.cfg.selectors.discussion.content,
            permalink_sel=state.cfg.selectors.discussion.permalink,
        )
        for p in posts:
            state.aggregator.add_discussion(p.model_dump())
