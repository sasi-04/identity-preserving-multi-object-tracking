"""Unit tests for Track Lifecycle State Machine."""
import numpy as np
import pytest
from backend.app.tracking.track import Track, TrackState


def test_track_confirmation_lifecycle():
    bbox = np.array([50.0, 50.0, 100.0, 150.0])
    track = Track(track_id=1, initial_bbox=bbox, confidence=0.85)

    # Initial state must be TENTATIVE
    assert track.state == TrackState.TENTATIVE
    assert track.hits == 1

    # Update with detection (hit 2)
    track.predict()
    track.update(bbox, confidence=0.88, min_hits_to_confirm=3)
    assert track.state == TrackState.TENTATIVE

    # Update with detection (hit 3 -> CONFIRMED)
    track.predict()
    track.update(bbox, confidence=0.90, min_hits_to_confirm=3)
    assert track.state == TrackState.CONFIRMED


def test_track_occlusion_and_recovery():
    bbox = np.array([50.0, 50.0, 100.0, 150.0])
    track = Track(track_id=2, initial_bbox=bbox, confidence=0.85)
    # Fast confirm
    track.update(bbox, confidence=0.9, min_hits_to_confirm=1)
    assert track.state == TrackState.CONFIRMED

    # Miss 1 frame -> becomes OCCLUDED
    track.predict(lost_timeout_frames=5, max_lost_frames=20)
    assert track.state == TrackState.OCCLUDED
    assert track.time_since_update == 1

    # Re-associate -> transitions to RECOVERED
    track.update(bbox, confidence=0.85)
    assert track.state == TrackState.RECOVERED
    assert track.recovery_count == 1


def test_track_lost_and_expiration():
    bbox = np.array([50.0, 50.0, 100.0, 150.0])
    track = Track(track_id=3, initial_bbox=bbox, confidence=0.85)
    track.update(bbox, confidence=0.9, min_hits_to_confirm=1)

    # Miss for 6 frames with lost_timeout = 5 -> becomes LOST
    for _ in range(6):
        track.predict(lost_timeout_frames=5, max_lost_frames=10)
    assert track.state == TrackState.LOST

    # Continue missing until exceeding max_lost_frames (10) -> becomes EXPIRED
    for _ in range(5):
        track.predict(lost_timeout_frames=5, max_lost_frames=10)
    assert track.state == TrackState.EXPIRED
