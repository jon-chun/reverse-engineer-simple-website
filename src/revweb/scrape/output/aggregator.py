from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class OutputAggregator:
    """Aggregates and deduplicates scraped data."""

    speakers: dict[str, dict] = field(default_factory=dict)
    roundtables: dict[str, dict] = field(default_factory=dict)
    roundtable_speaker_links: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    discussions: dict[str, list[dict]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_speaker(self, data: dict) -> bool:
        """Add or merge speaker data. Returns True if new speaker."""
        sid = data.get("speaker_id")
        if not sid:
            return False

        existing = self.speakers.get(sid)
        if existing:
            for k, v in data.items():
                if v and not existing.get(k):
                    existing[k] = v
            return False
        else:
            self.speakers[sid] = data
            return True

    def add_roundtable(
        self, data: dict, speaker_links: list[str] | None = None
    ) -> bool:
        """Add or merge roundtable data. Returns True if new roundtable."""
        rid = data.get("roundtable_id")
        if not rid:
            return False

        existing = self.roundtables.get(rid)
        if existing:
            for k, v in data.items():
                if v and not existing.get(k):
                    existing[k] = v
            is_new = False
        else:
            self.roundtables[rid] = data
            is_new = True

        if speaker_links:
            for link in speaker_links:
                self.roundtable_speaker_links[rid].add(link)

        return is_new

    def add_discussion(self, data: dict) -> bool:
        """Add discussion post. Returns True if added."""
        rid = data.get("roundtable_id") or "unknown"
        self.discussions[rid].append(data)
        return True

    def get_speakers(self) -> list[dict]:
        """Get all speakers sorted by ID."""
        return [self.speakers[k] for k in sorted(self.speakers.keys())]

    def get_roundtables(self) -> list[dict]:
        """Get all roundtables sorted by ID."""
        return [self.roundtables[k] for k in sorted(self.roundtables.keys())]

    def get_discussions(self, roundtable_id: str) -> list[dict]:
        """Get discussions for a roundtable."""
        return self.discussions.get(roundtable_id, [])
