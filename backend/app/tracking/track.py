"""
ZED VISION - Track State Machine & Lifecycle Management
Maintains continuous identity, trajectory history, and anti-pollution appearance memory.
"""

from collections import deque
from enum import Enum
from typing import Deque, List, Optional, Tuple
import numpy as np

from backend.app.tracking.kalman_filter import KalmanBoxTracker


class TrackState(str, Enum):
    TENTATIVE = "TENTATIVE"       # Initial candidate state, needs confirmation
    CONFIRMED = "CONFIRMED"       # Stable, active tracked identity
    OCCLUDED = "OCCLUDED"         # Temporarily missing (1 to lost_timeout frames)
    LOST = "LOST"                 # Extended disappearance within max recovery window
    RECOVERED = "RECOVERED"       # Successfully re-associated after occlusion/loss
    EXPIRED = "EXPIRED"           # Exceeded max recovery window, terminated


class Track:
    """
    Online, causal representation of a tracked individual.
    Guarantees stable unique IDs with zero in-session ID reuse.
    """
    _count_lock = 0

    def __init__(
        self,
        track_id: int,
        initial_bbox: np.ndarray,
        confidence: float,
        embedding: Optional[np.ndarray] = None,
        crop_quality: float = 1.0,
        max_trajectory_len: int = 30,
        gallery_size: int = 8
    ):
        self.track_id: int = track_id
        self.state: TrackState = TrackState.TENTATIVE

        # Bounding box motion state
        self.kalman_filter = KalmanBoxTracker(initial_bbox)
        self.last_bbox: np.ndarray = initial_bbox.copy()
        self.predicted_bbox: np.ndarray = initial_bbox.copy()

        # Lifecycle metrics
        self.hits: int = 1
        self.age: int = 1
        self.time_since_update: int = 0
        self.confidence: float = confidence
        self.frames_occluded_count: int = 0
        self.recovery_count: int = 0

        # Trajectory trail [(cx, cy), ...]
        self.trajectory: Deque[Tuple[float, float]] = deque(maxlen=max_trajectory_len)
        cx = (initial_bbox[0] + initial_bbox[2]) / 2.0
        cy = (initial_bbox[1] + initial_bbox[3]) / 2.0
        self.trajectory.append((float(cx), float(cy)))

        # Appearance gallery (bounded anti-pollution memory)
        self.appearance_gallery: Deque[np.ndarray] = deque(maxlen=gallery_size)
        if embedding is not None:
            self.appearance_gallery.append(embedding.copy())

        # Quality metrics
        self.last_crop_quality: float = crop_quality
        self.occlusion_overlap: float = 0.0

    def predict(self, lost_timeout_frames: int = 15, max_lost_frames: int = 60) -> np.ndarray:
        """
        Predict next bounding box position causally and update lifecycle state.
        """
        self.predicted_bbox = self.kalman_filter.predict()
        self.age += 1
        self.time_since_update += 1

        # Evaluate lifecycle state transitions
        if self.time_since_update > max_lost_frames:
            self.state = TrackState.EXPIRED
        elif self.time_since_update > lost_timeout_frames:
            if self.state in (TrackState.CONFIRMED, TrackState.OCCLUDED):
                self.state = TrackState.LOST
        elif self.time_since_update > 0:
            if self.state == TrackState.CONFIRMED:
                self.state = TrackState.OCCLUDED
                self.frames_occluded_count += 1
            elif self.state == TrackState.OCCLUDED:
                self.frames_occluded_count += 1

        return self.predicted_bbox

    def update(
        self,
        bbox: np.ndarray,
        confidence: float,
        embedding: Optional[np.ndarray] = None,
        crop_quality: float = 1.0,
        overlap_index: float = 0.0,
        min_hits_to_confirm: int = 3
    ) -> None:
        """
        Update state with matched observation and perform lifecycle transitions.
        """
        # Determine if this is a successful recovery
        was_missing = self.state in (TrackState.OCCLUDED, TrackState.LOST)

        # Kalman state correction
        self.last_bbox = self.kalman_filter.update(bbox)
        self.confidence = confidence
        self.last_crop_quality = crop_quality
        self.occlusion_overlap = overlap_index
        self.time_since_update = 0
        self.hits += 1

        # Record trajectory
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        self.trajectory.append((float(cx), float(cy)))

        # Anti-pollution appearance memory: only store clean observations
        if embedding is not None and overlap_index < 0.25 and crop_quality > 0.4:
            self.appearance_gallery.append(embedding.copy())

        # State transitions
        if was_missing:
            self.state = TrackState.RECOVERED
            self.recovery_count += 1
        elif self.state == TrackState.TENTATIVE and self.hits >= min_hits_to_confirm:
            self.state = TrackState.CONFIRMED
        elif self.state == TrackState.RECOVERED:
            # Transition RECOVERED back to stable CONFIRMED upon continuous observation
            self.state = TrackState.CONFIRMED

    def get_appearance_similarity(self, candidate_emb: np.ndarray) -> float:
        """
        Compute maximum cosine similarity between candidate embedding and gallery.
        Cosine similarity: dot product of L2-normalized vectors in [-1.0, 1.0].
        Returns float in [0.0, 1.0].
        """
        if candidate_emb is None or len(self.appearance_gallery) == 0:
            return 0.5  # Neutral default when no appearance is available

        sims = [float(np.dot(candidate_emb, g)) for g in self.appearance_gallery]
        max_sim = max(sims)
        # Rescale [-1, 1] to [0, 1]
        return float(np.clip((max_sim + 1.0) / 2.0, 0.0, 1.0))

    def get_spatial_uncertainty(self) -> float:
        """Get standard deviation position uncertainty radius from Kalman filter."""
        return self.kalman_filter.get_spatial_uncertainty_radius()

    def to_dict(self) -> dict:
        """Serialize track state for frontend streaming and diagnostic export."""
        return {
            "track_id": self.track_id,
            "state": self.state.value,
            "bbox": [round(float(c), 2) for c in self.last_bbox],
            "confidence": round(float(self.confidence), 3),
            "hits": self.hits,
            "age": self.age,
            "time_since_update": self.time_since_update,
            "trajectory": [[round(x, 1), round(y, 1)] for x, y in list(self.trajectory)[-15:]],
            "crop_quality": round(float(self.last_crop_quality), 2),
            "occlusion_overlap": round(float(self.occlusion_overlap), 2),
            "uncertainty_radius": round(self.get_spatial_uncertainty(), 2),
            "recovery_count": self.recovery_count
        }
