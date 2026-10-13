"""
ZED VISION - Occlusion Intelligence Engine (OIE)
A technically defensible algorithmic enhancement designed for dense transit gate occlusions.
Features:
- Uncertainty-aware spatial gating and gap penalty
- Adaptive visibility-modulated cost weighting
- Anti-pollution temporal appearance memory
- Ambiguity-aware candidate comparison and rejection
- Crowd-pressure diagnostics (CPI)
- Explainable structured diagnostic event logging
"""

from dataclasses import asdict, dataclass
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.app.core.config import TrackerConfig
from backend.app.detection.detector import PersonDetection
from backend.app.tracking.track import Track, TrackState


@dataclass
class DiagnosticRecord:
    event_type: str  # "RECOVERY_CONFIRMED", "AMBIGUOUS_REJECTED", "OCCLUSION_ENTER", "LOST_ENTER", "GATING_REJECTED"
    track_id: int
    frame_idx: int
    timestamp: float
    previous_bbox: List[float]
    predicted_bbox: List[float]
    candidate_bbox: Optional[List[float]]
    motion_cost: float
    appearance_cost: float
    geometry_cost: float
    final_cost: float
    decision_reason: str
    is_confirmed: bool
    ambiguity_margin: Optional[float] = None
    spatial_uncertainty_px: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CrowdPressureMetrics:
    frame_idx: int
    active_pedestrian_count: int
    mean_overlap_iou: float
    max_overlap_iou: float
    crowd_pressure_index: float  # [0.0, 1.0]
    ambiguity_rate: float
    occluded_tracks_count: int


class OcclusionIntelligenceEngine:
    """
    Proposed innovation module implementing uncertainty-aware, adaptive association,
    and anti-pollution temporal memory for dense occlusion tracking.
    """
    def __init__(self, config: TrackerConfig):
        self.config = config
        self.diagnostic_records: List[DiagnosticRecord] = []
        self.crowd_history: List[CrowdPressureMetrics] = []

    def compute_crowd_pressure(
        self,
        frame_idx: int,
        tracks: List[Track],
        detections: List[PersonDetection]
    ) -> CrowdPressureMetrics:
        """
        Component E: Compute instantaneous crowd pressure diagnostics.
        """
        active_count = len([t for t in tracks if t.state != TrackState.EXPIRED])
        occluded_count = len([t for t in tracks if t.state in (TrackState.OCCLUDED, TrackState.LOST)])

        overlaps = [d.overlap_index for d in detections] if detections else [0.0]
        mean_overlap = float(np.mean(overlaps)) if overlaps else 0.0
        max_overlap = float(np.max(overlaps)) if overlaps else 0.0

        # Density factor normalized relative to typical transit gate capacity (e.g., 20 people)
        density_factor = min(1.0, active_count / 20.0)

        # Composite Crowd Pressure Index (CPI) in [0.0, 1.0]
        cpi = float(np.clip(
            0.45 * density_factor + 0.35 * mean_overlap + 0.20 * (occluded_count / max(1, active_count)),
            0.0,
            1.0
        ))

        metrics = CrowdPressureMetrics(
            frame_idx=frame_idx,
            active_pedestrian_count=active_count,
            mean_overlap_iou=round(mean_overlap, 3),
            max_overlap_iou=round(max_overlap, 3),
            crowd_pressure_index=round(cpi, 3),
            ambiguity_rate=0.0,
            occluded_tracks_count=occluded_count
        )
        self.crowd_history.append(metrics)
        return metrics

    def compute_adaptive_cost_matrix(
        self,
        tracks: List[Track],
        detections: List[PersonDetection],
        iou_matrix: np.ndarray,
        motion_matrix: np.ndarray,
        appearance_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Component B: Dynamically balance motion, appearance, and geometry costs.
        Reduces appearance weight when person crop is degraded or occluded by crowd overlap.
        """
        n, m = len(tracks), len(detections)
        cost_matrix = np.zeros((n, m), dtype=np.float32)

        base_w_mot = self.config.weight_motion
        base_w_app = self.config.weight_appearance
        base_w_geom = self.config.weight_geometry

        for i, trk in enumerate(tracks):
            # Compute gap penalty for extended disappearances
            gap_penalty = 0.0
            if self.config.enable_uncertainty_recovery and trk.time_since_update > 1:
                gap_penalty = self.config.gap_penalty_factor * float(np.log1p(trk.time_since_update))

            for j, det in enumerate(detections):
                geom_cost = 1.0 - iou_matrix[i, j]
                mot_cost = motion_matrix[i, j]
                app_cost = appearance_matrix[i, j]

                if self.config.enable_adaptive_weights:
                    # Scale down appearance weight if crop is overlapping another person or degraded
                    vis_factor = max(0.1, (1.0 - det.overlap_index) * det.crop_quality)
                    w_app = base_w_app * vis_factor
                    # Reallocate residual weight into geometry and motion
                    residual = base_w_app - w_app
                    w_geom = base_w_geom + residual * 0.6
                    w_mot = base_w_mot + residual * 0.4
                else:
                    w_mot, w_app, w_geom = base_w_mot, base_w_app, base_w_geom

                total_cost = w_geom * geom_cost + w_mot * mot_cost + w_app * app_cost + gap_penalty
                cost_matrix[i, j] = float(total_cost)

        return cost_matrix

    def filter_ambiguous_recoveries(
        self,
        candidate_matches: List[Tuple[int, int]],
        tracks: List[Track],
        detections: List[PersonDetection],
        cost_matrix: np.ndarray,
        iou_matrix: np.ndarray,
        motion_matrix: np.ndarray,
        appearance_matrix: np.ndarray,
        frame_idx: int
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Component D & F: Ambiguity-Aware Recovery Verification & Explainability Logging.
        Compares best match vs second-best match for recovering tracks.
        Rejects matches where the margin is below the threshold to avoid identity switches.
        """
        confirmed_matches: List[Tuple[int, int]] = []
        rejected_track_indices: List[int] = []
        rejected_det_indices: List[int] = []

        m_detections = cost_matrix.shape[1] if cost_matrix.size > 0 else 0

        for trk_idx, det_idx in candidate_matches:
            trk = tracks[trk_idx]
            det = detections[det_idx]
            final_cost = float(cost_matrix[trk_idx, det_idx])
            geom_cost = float(1.0 - iou_matrix[trk_idx, det_idx])
            mot_cost = float(motion_matrix[trk_idx, det_idx])
            app_cost = float(appearance_matrix[trk_idx, det_idx])
            unc_px = trk.get_spatial_uncertainty()

            # Check if this track is currently in occlusion recovery
            is_recovering = trk.state in (TrackState.OCCLUDED, TrackState.LOST)

            if is_recovering and self.config.enable_ambiguity_rejection and m_detections > 1:
                # Find the second-lowest cost candidate for this track
                all_costs = cost_matrix[trk_idx, :]
                sorted_costs = np.sort(all_costs)
                best_cost = sorted_costs[0]
                second_best_cost = sorted_costs[1]
                margin = float(second_best_cost - best_cost)

                if margin < self.config.ambiguity_margin_threshold:
                    # AMBIGUOUS CANDIDATE DETECTED!
                    reason = (
                        f"Rejected ambiguous recovery: margin {margin:.3f} between best ({best_cost:.3f}) "
                        f"and 2nd-best ({second_best_cost:.3f}) below threshold {self.config.ambiguity_margin_threshold:.3f}. "
                        f"Preventing potential identity switch."
                    )
                    self.diagnostic_records.append(DiagnosticRecord(
                        event_type="AMBIGUOUS_REJECTED",
                        track_id=trk.track_id,
                        frame_idx=frame_idx,
                        timestamp=time.time(),
                        previous_bbox=[round(float(c), 1) for c in trk.last_bbox],
                        predicted_bbox=[round(float(c), 1) for c in trk.predicted_bbox],
                        candidate_bbox=[round(float(c), 1) for c in det.bbox],
                        motion_cost=round(mot_cost, 3),
                        appearance_cost=round(app_cost, 3),
                        geometry_cost=round(geom_cost, 3),
                        final_cost=round(final_cost, 3),
                        decision_reason=reason,
                        is_confirmed=False,
                        ambiguity_margin=round(margin, 3),
                        spatial_uncertainty_px=round(unc_px, 1)
                    ))
                    rejected_track_indices.append(trk_idx)
                    rejected_det_indices.append(det_idx)
                    continue

            # Valid match confirmed
            if is_recovering:
                reason = (
                    f"Confirmed recovery after {trk.time_since_update} frames of occlusion. "
                    f"Combined cost {final_cost:.3f} supported by motion ({mot_cost:.3f}) and appearance ({app_cost:.3f})."
                )
                self.diagnostic_records.append(DiagnosticRecord(
                    event_type="RECOVERY_CONFIRMED",
                    track_id=trk.track_id,
                    frame_idx=frame_idx,
                    timestamp=time.time(),
                    previous_bbox=[round(float(c), 1) for c in trk.last_bbox],
                    predicted_bbox=[round(float(c), 1) for c in trk.predicted_bbox],
                    candidate_bbox=[round(float(c), 1) for c in det.bbox],
                    motion_cost=round(mot_cost, 3),
                    appearance_cost=round(app_cost, 3),
                    geometry_cost=round(geom_cost, 3),
                    final_cost=round(final_cost, 3),
                    decision_reason=reason,
                    is_confirmed=True,
                    ambiguity_margin=None,
                    spatial_uncertainty_px=round(unc_px, 1)
                ))

            confirmed_matches.append((trk_idx, det_idx))

        return confirmed_matches, rejected_track_indices, rejected_det_indices

    def log_lifecycle_event(self, event_type: str, track: Track, frame_idx: int, reason: str) -> None:
        """Log state transition events (e.g. entering occlusion or lost state)."""
        self.diagnostic_records.append(DiagnosticRecord(
            event_type=event_type,
            track_id=track.track_id,
            frame_idx=frame_idx,
            timestamp=time.time(),
            previous_bbox=[round(float(c), 1) for c in track.last_bbox],
            predicted_bbox=[round(float(c), 1) for c in track.predicted_bbox],
            candidate_bbox=None,
            motion_cost=0.0,
            appearance_cost=0.0,
            geometry_cost=0.0,
            final_cost=0.0,
            decision_reason=reason,
            is_confirmed=(event_type == "RECOVERY_CONFIRMED"),
            ambiguity_margin=None,
            spatial_uncertainty_px=round(track.get_spatial_uncertainty(), 1)
        ))
