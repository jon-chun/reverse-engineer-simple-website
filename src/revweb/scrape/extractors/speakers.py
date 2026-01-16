from __future__ import annotations

from parsel import Selector

from ...models import Speaker
from .common import abs_url, id_from_url, join_text


def extract_speaker(
    selector: Selector,
    url: str,
    *,
    name_sel: str,
    bio_sel: str,
    title_sel: str,
    org_sel: str,
    headshot_sel: str,
    socials_sel: str,
    id_from_url_flag: bool,
) -> Speaker | None:
    name = (selector.css(name_sel).get() or "").strip()
    if "<" in name:
        name = join_text(selector.css(name_sel + " ::text").getall())

    if not name:
        return None

    bio = join_text(selector.css(bio_sel).getall())
    title = join_text(selector.css(title_sel).getall()) if title_sel else ""
    org = join_text(selector.css(org_sel).getall()) if org_sel else ""

    headshot = selector.css(headshot_sel).get() if headshot_sel else None
    headshot = abs_url(url, headshot)

    socials = []
    if socials_sel:
        for a in selector.css(socials_sel):
            href = a.attrib.get("href")
            if href:
                socials.append(href)
    social_links = ";".join(sorted(set(socials))) if socials else ""

    sid = id_from_url(url) if id_from_url_flag else (name.lower().replace(" ", "-"))

    return Speaker(
        speaker_id=sid,
        name=name,
        bio=bio or None,
        title=title or None,
        organization=org or None,
        profile_url=url,
        headshot_url=headshot,
        social_links=social_links or None,
    )
