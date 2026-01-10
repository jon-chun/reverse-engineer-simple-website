"""Unit tests for Pydantic models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from revweb.models import DiscussionPost, Roundtable, Speaker


class TestSpeakerModel:
    """Tests for the Speaker model."""

    def test_speaker_minimal(self):
        """Speaker can be created with just required fields."""
        speaker = Speaker(speaker_id="test-id", name="Test Name")
        assert speaker.speaker_id == "test-id"
        assert speaker.name == "Test Name"
        assert speaker.bio is None
        assert speaker.title is None

    def test_speaker_full(self, sample_speaker_data):
        """Speaker can be created with all fields."""
        speaker = Speaker(**sample_speaker_data)
        assert speaker.speaker_id == "john-doe"
        assert speaker.name == "John Doe"
        assert speaker.bio == "A test speaker bio."
        assert speaker.organization == "Test Corp"

    def test_speaker_auto_timestamp(self):
        """Speaker gets automatic timestamp on creation."""
        speaker = Speaker(speaker_id="test", name="Test")
        assert speaker.source_last_seen_utc is not None
        assert "T" in speaker.source_last_seen_utc  # ISO format

    def test_speaker_missing_required_fields(self):
        """Speaker raises error when required fields missing."""
        with pytest.raises(ValidationError):
            Speaker(speaker_id="test")  # Missing name
        with pytest.raises(ValidationError):
            Speaker(name="Test")  # Missing speaker_id

    def test_speaker_model_dump(self, sample_speaker_data):
        """Speaker can be serialized to dict."""
        speaker = Speaker(**sample_speaker_data)
        data = speaker.model_dump()
        assert data["speaker_id"] == "john-doe"
        assert "source_last_seen_utc" in data


class TestRoundtableModel:
    """Tests for the Roundtable model."""

    def test_roundtable_minimal(self):
        """Roundtable can be created with just required fields."""
        rt = Roundtable(roundtable_id="test-rt", title="Test Roundtable")
        assert rt.roundtable_id == "test-rt"
        assert rt.title == "Test Roundtable"
        assert rt.speaker_ids == ""

    def test_roundtable_full(self, sample_roundtable_data):
        """Roundtable can be created with all fields."""
        rt = Roundtable(**sample_roundtable_data)
        assert rt.roundtable_id == "test-roundtable"
        assert rt.speaker_ids == "john-doe,jane-doe"

    def test_roundtable_auto_timestamp(self):
        """Roundtable gets automatic timestamp on creation."""
        rt = Roundtable(roundtable_id="test", title="Test")
        assert rt.source_last_seen_utc is not None


class TestDiscussionPostModel:
    """Tests for the DiscussionPost model."""

    def test_discussion_post_minimal(self):
        """DiscussionPost can be created with just required fields."""
        post = DiscussionPost(discussion_id="post-1", roundtable_id="rt-1")
        assert post.discussion_id == "post-1"
        assert post.roundtable_id == "rt-1"
        assert post.content_text is None

    def test_discussion_post_full(self, sample_discussion_data):
        """DiscussionPost can be created with all fields."""
        post = DiscussionPost(**sample_discussion_data)
        assert post.discussion_id == "test-roundtable-1"
        assert post.author_name == "John Doe"
        assert "test discussion" in post.content_text

    def test_discussion_post_auto_timestamp(self):
        """DiscussionPost gets automatic timestamp on creation."""
        post = DiscussionPost(discussion_id="test", roundtable_id="rt")
        assert post.source_last_seen_utc is not None
