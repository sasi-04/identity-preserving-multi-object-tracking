"""
ZED VISION - Global Hungarian Data Association
Solves optimal bipartite matching with SciPy linear_sum_assignment and cost threshold gating.
"""

from typing import List, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment


def linear_assignment(
    cost_matrix: np.ndarray,
    cost_threshold: float
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Perform optimal bipartite assignment using Hungarian algorithm.
    Any matched pair with cost > cost_threshold is rejected.

    Returns:
        matches: List of (track_index, detection_index)
        unmatched_tracks: List of track indices
        unmatched_detections: List of detection indices
    """
    if cost_matrix.size == 0:
        return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    matches: List[Tuple[int, int]] = []
    unmatched_tracks: List[int] = list(range(cost_matrix.shape[0]))
    unmatched_detections: List[int] = list(range(cost_matrix.shape[1]))

    for r, c in zip(row_indices, col_indices):
        if cost_matrix[r, c] <= cost_threshold:
            matches.append((int(r), int(c)))
            if r in unmatched_tracks:
                unmatched_tracks.remove(r)
            if c in unmatched_detections:
                unmatched_detections.remove(c)

    return matches, unmatched_tracks, unmatched_detections
