from __future__ import annotations

from scrapy.http import Response

from ...models import Roundtable
from .common import id_from_url, join_text


def extract_roundtable(
    response: Response,
    *,
    title_sel: str,
    desc_sel: str,
    speaker_links_sel: str,
    id_from_url_flag: bool,
) -> Roundtable | None:
    title = (response.css(title_sel).get() or "").strip()
    if "<" in title:
        title = join_text(response.css(title_sel + " ::text").getall())

    if not title:
        return None

    desc = join_text(response.css(desc_sel).getall())
    rid = id_from_url(str(response.url)) if id_from_url_flag else title.lower().replace(" ", "-")

    return Roundtable(
        roundtable_id=rid,
        title=title,
        description=desc or None,
        roundtable_url=str(response.url),
        speaker_ids="",
        speakers_md_link=None,
    )
