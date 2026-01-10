from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Speaker(BaseModel):
    speaker_id: str
    name: str
    bio: str | None = None
    title: str | None = None
    organization: str | None = None
    profile_url: str | None = None
    headshot_url: str | None = None
    social_links: str | None = None
    source_last_seen_utc: str = Field(default_factory=_utc_now_iso)


class Roundtable(BaseModel):
    roundtable_id: str
    title: str
    description: str | None = None
    roundtable_url: str | None = None
    speaker_ids: str = ""
    speakers_md_link: str | None = None
    source_last_seen_utc: str = Field(default_factory=_utc_now_iso)


class DiscussionPost(BaseModel):
    discussion_id: str
    roundtable_id: str
    thread_title: str | None = None
    post_id: str | None = None
    author_speaker_id: str | None = None
    author_name: str | None = None
    posted_at: str | None = None
    content_text: str | None = None
    permalink: str | None = None
    source_last_seen_utc: str = Field(default_factory=_utc_now_iso)
