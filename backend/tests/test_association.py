"""Unit tests for Hungarian assignment and IoU cost matrices."""
import numpy as np
import pytest
from backend.app.association.costs import compute_iou_matrix
from backend.app.association.matcher import linear_assignment


def test_compute_iou_matrix():
    b_a = np.array([
        [0.0, 0.0, 10.0, 10.0],
        [20.0, 20.0, 30.0, 30.0]
    ])
    b_b = np.array([
        [0.0, 0.0, 10.0, 10.0],   # Exact match with b_a[0]
        [5.0, 5.0, 15.0, 15.0],   # Partial overlap with b_a[0]
        [100.0, 100.0, 110.0, 110.0]  # Disjoint
    ])

    iou = compute_iou_matrix(b_a, b_b)
    assert iou.shape == (2, 3)
    assert np.isclose(iou[0, 0], 1.0)
    assert 0.0 < iou[0, 1] < 1.0
    assert iou[0, 2] == 0.0
    assert iou[1, 2] == 0.0


def test_linear_assignment_optimal_matching():
    cost_matrix = np.array([
        [0.1, 0.9, 0.8],
        [0.7, 0.2, 0.9],
        [0.9, 0.8, 0.3]
    ])

    matches, unmatched_tracks, unmatched_dets = linear_assignment(cost_matrix, cost_threshold=0.5)
    assert len(matches) == 3
    assert (0, 0) in matches
    assert (1, 1) in matches
    assert (2, 2) in matches
    assert len(unmatched_tracks) == 0
    assert len(unmatched_dets) == 0


def test_linear_assignment_cost_gating():
    # Costs exceed the rejection threshold (e.g., implausible geometric leaps)
    cost_matrix = np.array([
        [0.85, 0.95],
        [0.92, 0.88]
    ])

    matches, unmatched_tracks, unmatched_dets = linear_assignment(cost_matrix, cost_threshold=0.5)
    assert len(matches) == 0
    assert set(unmatched_tracks) == {0, 1}
    assert set(unmatched_dets) == {0, 1}


def test_linear_assignment_empty():
    cost_matrix = np.zeros((0, 3))
    matches, unmatched_trks, unmatched_dets = linear_assignment(cost_matrix, cost_threshold=0.5)
    assert len(matches) == 0
    assert len(unmatched_trks) == 0
    assert len(unmatched_dets) == 3
