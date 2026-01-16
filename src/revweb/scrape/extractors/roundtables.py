from __future__ import annotations

from parsel import Selector

from ...models import Roundtable
from .common import id_from_url, join_text


def extract_roundtable(
    selector: Selector,
    url: str,
    *,
    title_sel: str,
    desc_sel: str,
    speaker_links_sel: str,
    id_from_url_flag: bool,
) -> Roundtable | None:
    title = (selector.css(title_sel).get() or "").strip()
    if "<" in title:
        title = join_text(selector.css(title_sel + " ::text").getall())

    if not title:
        return None

    desc = join_text(selector.css(desc_sel).getall())
    rid = id_from_url(url) if id_from_url_flag else title.lower().replace(" ", "-")

    return Roundtable(
        roundtable_id=rid,
        title=title,
        description=desc or None,
        roundtable_url=url,
        speaker_ids="",
        speakers_md_link=None,
    )
