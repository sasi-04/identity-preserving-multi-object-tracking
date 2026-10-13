"""Unit tests for Kalman Filter motion model."""
import numpy as np
import pytest
from backend.app.tracking.kalman_filter import KalmanBoxTracker


def test_kalman_init_and_bbox_conversion():
    bbox = np.array([100.0, 150.0, 200.0, 350.0])  # w=100, h=200, cx=150, cy=250
    tracker = KalmanBoxTracker(bbox)

    z = tracker.bbox_to_z(bbox)
    assert np.isclose(z[0], 150.0)
    assert np.isclose(z[1], 250.0)
    assert np.isclose(z[2], 0.5)
    assert np.isclose(z[3], 200.0)

    recovered_bbox = tracker.z_to_bbox(z)
    assert np.allclose(bbox, recovered_bbox)


def test_kalman_causal_prediction_and_velocity():
    bbox = np.array([100.0, 150.0, 200.0, 350.0])
    tracker = KalmanBoxTracker(bbox)

    # First prediction with zero initial velocity
    pred = tracker.predict()
    assert len(pred) == 4
    assert np.isclose(pred[0], 100.0, atol=1.0)

    # Update with shifted bbox (simulating rightward motion)
    shifted_bbox = np.array([110.0, 150.0, 210.0, 350.0])
    tracker.update(shifted_bbox)

    # Subsequent prediction should causally anticipate positive velocity
    pred2 = tracker.predict()
    assert pred2[0] > 110.0  # Continued moving right


def test_kalman_covariance_bounded():
    bbox = np.array([100.0, 150.0, 200.0, 350.0])
    tracker = KalmanBoxTracker(bbox)

    # Predict repeatedly for 100 frames without measurement updates (simulating extended occlusion)
    for _ in range(100):
        tracker.predict()

    # Covariance must remain bounded by clamp
    assert np.all(tracker.covariance <= 1e4 + 1.0)
    assert np.all(tracker.covariance >= -1e4 - 1.0)
    assert tracker.get_spatial_uncertainty_radius() > 0.0


def test_kalman_mahalanobis_gating():
    bbox = np.array([100.0, 150.0, 200.0, 350.0])
    tracker = KalmanBoxTracker(bbox)
    tracker.predict()

    close_det = np.array([[102.0, 151.0, 202.0, 351.0]])
    distant_det = np.array([[800.0, 800.0, 900.0, 1000.0]])

    dist_close = tracker.gating_distance(close_det)[0]
    dist_distant = tracker.gating_distance(distant_det)[0]

    assert dist_close < tracker.chi2_gate_95  # Within 95% gating region
    assert dist_distant > tracker.chi2_gate_95  # Outside gating region
