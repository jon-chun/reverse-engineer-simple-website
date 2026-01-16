from __future__ import annotations

from rapidfuzz import fuzz

from .aggregator import OutputAggregator


def _norm(s: str) -> str:
    """Normalize string for matching."""
    return " ".join((s or "").strip().lower().split())


def link_roundtable_speakers(aggregator: OutputAggregator) -> None:
    """Link speakers to roundtables using URL and fuzzy name matching."""
    url_to_id: dict[str, str] = {}
    name_to_id: dict[str, str] = {}

    for sid, s in aggregator.speakers.items():
        if s.get("profile_url"):
            url_to_id[_norm(s["profile_url"])] = sid
        name_to_id[_norm(s.get("name", ""))] = sid

    for rid, rt in aggregator.roundtables.items():
        links = aggregator.roundtable_speaker_links.get(rid, set())
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
