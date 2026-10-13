"""
ZED VISION - Cost Matrix Computation for MOT Association
Includes IoU geometry, Mahalanobis motion distance, and Cosine appearance metrics.
"""

from typing import List
import numpy as np

from backend.app.detection.detector import PersonDetection
from backend.app.tracking.track import Track


def compute_iou_matrix(bboxes_a: np.ndarray, bboxes_b: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Intersection-over-Union (IoU) matrix.
    bboxes_a: (N, 4) in [x1, y1, x2, y2]
    bboxes_b: (M, 4) in [x1, y1, x2, y2]
    Returns: (N, M) matrix with IoU in [0.0, 1.0]
    """
    if len(bboxes_a) == 0 or len(bboxes_b) == 0:
        return np.zeros((len(bboxes_a), len(bboxes_b)), dtype=np.float32)

    # Calculate intersection corners
    x1 = np.maximum(bboxes_a[:, 0:1], bboxes_b[:, 0:1].T)
    y1 = np.maximum(bboxes_a[:, 1:2], bboxes_b[:, 1:2].T)
    x2 = np.minimum(bboxes_a[:, 2:3], bboxes_b[:, 2:3].T)
    y2 = np.minimum(bboxes_a[:, 3:4], bboxes_b[:, 3:4].T)

    inter_w = np.maximum(0.0, x2 - x1)
    inter_h = np.maximum(0.0, y2 - y1)
    intersection = inter_w * inter_h

    area_a = (bboxes_a[:, 2] - bboxes_a[:, 0]) * (bboxes_a[:, 3] - bboxes_a[:, 1])
    area_b = (bboxes_b[:, 2] - bboxes_b[:, 0]) * (bboxes_b[:, 3] - bboxes_b[:, 1])
    union = area_a[:, None] + area_b[None, :] - intersection

    return (intersection / np.maximum(union, 1e-6)).astype(np.float32)


def compute_motion_cost_matrix(tracks: List[Track], detections: List[PersonDetection]) -> np.ndarray:
    """
    Compute normalized Mahalanobis motion cost matrix.
    Normalized by 95% Chi-square gate (9.4877 for 4-DOF).
    Returns (N, M) matrix where cost in [0.0, 1.0] corresponds to gated distance.
    """
    n = len(tracks)
    m = len(detections)
    if n == 0 or m == 0:
        return np.zeros((n, m), dtype=np.float32)

    meas_bboxes = np.array([d.bbox for d in detections], dtype=np.float32)
    cost_matrix = np.zeros((n, m), dtype=np.float32)

    for i, trk in enumerate(tracks):
        try:
            sq_maha = trk.kalman_filter.gating_distance(meas_bboxes, only_position=False)
            # Normalize by Chi-square 95% threshold; values > 1.0 indicate impossible motion
            normalized = np.clip(sq_maha / trk.kalman_filter.chi2_gate_95, 0.0, 2.0)
            cost_matrix[i, :] = normalized
        except Exception:
            # Fallback to Euclidean center distance if covariance is non-positive definite
            pred = trk.predicted_bbox
            pred_cx, pred_cy = (pred[0] + pred[2]) / 2.0, (pred[1] + pred[3]) / 2.0
            for j, det in enumerate(detections):
                det_cx, det_cy = (det.bbox[0] + det.bbox[2]) / 2.0, (det.bbox[1] + det.bbox[3]) / 2.0
                dist = np.sqrt((pred_cx - det_cx)**2 + (pred_cy - det_cy)**2)
                cost_matrix[i, j] = min(2.0, dist / 200.0)

    return cost_matrix


def compute_appearance_cost_matrix(tracks: List[Track], detections: List[PersonDetection]) -> np.ndarray:
    """
    Compute Cosine distance cost matrix: Cost = 1.0 - Similarity.
    Similarity computed against track's anti-pollution appearance gallery.
    Returns (N, M) matrix with cost in [0.0, 1.0].
    """
    n = len(tracks)
    m = len(detections)
    if n == 0 or m == 0:
        return np.zeros((n, m), dtype=np.float32)

    cost_matrix = np.zeros((n, m), dtype=np.float32)
    for i, trk in enumerate(tracks):
        for j, det in enumerate(detections):
            if det.embedding is not None and len(trk.appearance_gallery) > 0:
                sim = trk.get_appearance_similarity(det.embedding)
                cost_matrix[i, j] = float(1.0 - sim)
            else:
                cost_matrix[i, j] = 0.5  # Neutral cost when appearance is absent

    return cost_matrix
