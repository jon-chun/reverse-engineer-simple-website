from __future__ import annotations

from scrapy.http import Response

from ...models import Speaker
from .common import abs_url, id_from_url, join_text


def extract_speaker(
    response: Response,
    *,
    name_sel: str,
    bio_sel: str,
    title_sel: str,
    org_sel: str,
    headshot_sel: str,
    socials_sel: str,
    id_from_url_flag: bool,
) -> Speaker | None:
    name = (response.css(name_sel).get() or "").strip()
    if "<" in name:
        name = join_text(response.css(name_sel + " ::text").getall())

    if not name:
        return None

    bio = join_text(response.css(bio_sel).getall())
    title = join_text(response.css(title_sel).getall()) if title_sel else ""
    org = join_text(response.css(org_sel).getall()) if org_sel else ""

    headshot = response.css(headshot_sel).get() if headshot_sel else None
    headshot = abs_url(str(response.url), headshot)

    socials = []
    if socials_sel:
        for a in response.css(socials_sel):
            href = a.attrib.get("href")
            if href:
                socials.append(href)
    social_links = ";".join(sorted(set(socials))) if socials else ""

    sid = id_from_url(str(response.url)) if id_from_url_flag else (name.lower().replace(" ", "-"))

    return Speaker(
        speaker_id=sid,
        name=name,
        bio=bio or None,
        title=title or None,
        organization=org or None,
        profile_url=str(response.url),
        headshot_url=headshot,
        social_links=social_links or None,
    )
