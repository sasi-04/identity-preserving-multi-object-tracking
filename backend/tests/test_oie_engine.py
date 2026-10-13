"""Unit tests for the Occlusion Intelligence Engine (OIE)."""
import numpy as np
import pytest
from backend.app.core.config import TrackerConfig
from backend.app.detection.detector import PersonDetection
from backend.app.tracking.oie import OcclusionIntelligenceEngine
from backend.app.tracking.track import Track, TrackState


def test_oie_crowd_pressure_calculation():
    cfg = TrackerConfig(enable_oie=True)
    oie = OcclusionIntelligenceEngine(cfg)

    tracks = [
        Track(1, np.array([10.0, 10.0, 50.0, 90.0]), 0.9),
        Track(2, np.array([20.0, 20.0, 60.0, 100.0]), 0.9)
    ]
    dets = [
        PersonDetection(np.array([10.0, 10.0, 50.0, 90.0]), 0.9, overlap_index=0.4),
        PersonDetection(np.array([20.0, 20.0, 60.0, 100.0]), 0.9, overlap_index=0.4)
    ]

    metrics = oie.compute_crowd_pressure(frame_idx=1, tracks=tracks, detections=dets)
    assert 0.0 <= metrics.crowd_pressure_index <= 1.0
    assert metrics.active_pedestrian_count == 2
    assert metrics.mean_overlap_iou == 0.4


def test_oie_ambiguity_rejection():
    """Verify that OIE rejects recovery when best vs 2nd-best margin < threshold."""
    cfg = TrackerConfig(
        enable_oie=True,
        enable_ambiguity_rejection=True,
        ambiguity_margin_threshold=0.15
    )
    oie = OcclusionIntelligenceEngine(cfg)

    track = Track(1, np.array([100.0, 100.0, 150.0, 250.0]), 0.85)
    track.predict()
    track.state = TrackState.OCCLUDED  # In occlusion state

    det1 = PersonDetection(np.array([105.0, 105.0, 155.0, 255.0]), 0.88)
    det2 = PersonDetection(np.array([108.0, 108.0, 158.0, 258.0]), 0.85)

    # Cost matrix where candidate 1 cost is 0.20 and candidate 2 cost is 0.25 (margin = 0.05 < 0.15)
    cost_matrix = np.array([[0.20, 0.25]])
    iou_matrix = np.array([[0.80, 0.75]])
    motion_matrix = np.array([[0.10, 0.15]])
    app_matrix = np.array([[0.10, 0.12]])

    candidate_matches = [(0, 0)]  # Hungarian proposes det 0
    confirmed, rej_trks, rej_dets = oie.filter_ambiguous_recoveries(
        candidate_matches=candidate_matches,
        tracks=[track],
        detections=[det1, det2],
        cost_matrix=cost_matrix,
        iou_matrix=iou_matrix,
        motion_matrix=motion_matrix,
        appearance_matrix=app_matrix,
        frame_idx=10
    )

    # Must be rejected due to ambiguity!
    assert len(confirmed) == 0
    assert 0 in rej_trks
    assert 0 in rej_dets
    assert len(oie.diagnostic_records) == 1
    assert oie.diagnostic_records[0].event_type == "AMBIGUOUS_REJECTED"


def test_oie_anti_pollution_appearance_memory():
    track = Track(1, np.array([50.0, 50.0, 100.0, 150.0]), 0.9, gallery_size=4)
    clean_emb = np.ones(128, dtype=np.float32)
    polluted_emb = np.zeros(128, dtype=np.float32)

    # Clean update -> accepted into gallery
    track.update(
        np.array([50.0, 50.0, 100.0, 150.0]),
        confidence=0.9,
        embedding=clean_emb,
        crop_quality=0.8,
        overlap_index=0.05
    )
    assert len(track.appearance_gallery) == 1

    # Polluted crop (high crowd overlap) -> rejected by anti-pollution policy
    track.update(
        np.array([50.0, 50.0, 100.0, 150.0]),
        confidence=0.8,
        embedding=polluted_emb,
        crop_quality=0.3,
        overlap_index=0.60
    )
    # Gallery must NOT be polluted
    assert len(track.appearance_gallery) == 1
    assert np.allclose(track.appearance_gallery[0], clean_emb)
