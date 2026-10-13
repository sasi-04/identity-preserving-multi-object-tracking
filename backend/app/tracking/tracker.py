"""
ZED VISION - Multi-Object Tracking Engine (MOT Core)
Combines causal Kalman prediction, cascaded Hungarian association, and the Occlusion Intelligence Engine.
Supports Baseline mode and OIE mode for empirical comparison and ablation studies.
"""

import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.app.association.costs import (
    compute_appearance_cost_matrix,
    compute_iou_matrix,
    compute_motion_cost_matrix,
)
from backend.app.association.matcher import linear_assignment
from backend.app.core.config import TrackerConfig
from backend.app.detection.detector import BasePersonDetector, PersonDetection
from backend.app.tracking.oie import DiagnosticRecord, OcclusionIntelligenceEngine
from backend.app.tracking.track import Track, TrackState


class MultiObjectTracker:
    """
    Online, causal Multi-Object Tracker.
    Maintains continuous identities across dense transit crowd occlusions.
    """
    def __init__(self, config: TrackerConfig, detector: Optional[BasePersonDetector] = None):
        self.config = config
        self.detector = detector
        self.tracks: List[Track] = []
        self._next_id: int = 1

        # Occlusion Intelligence Engine
        self.oie = OcclusionIntelligenceEngine(config) if config.enable_oie else None

        # Empirical runtime performance metrics
        self.total_frames_processed: int = 0
        self.total_detections_count: int = 0
        self.total_recoveries_count: int = 0
        self.total_id_switches: int = 0
        self.last_latency_ms: float = 0.0
        self.last_fps: float = 0.0
        self.frame_latencies: List[float] = []

    def reset(self) -> None:
        """Reset tracker state and ID counter for a new video session."""
        self.tracks = []
        self._next_id = 1
        self.total_frames_processed = 0
        self.total_detections_count = 0
        self.total_recoveries_count = 0
        self.total_id_switches = 0
        self.frame_latencies = []
        if self.oie:
            self.oie.diagnostic_records = []
            self.oie.crowd_history = []

    def update(
        self,
        frame: np.ndarray,
        frame_idx: int,
        detections: Optional[List[PersonDetection]] = None
    ) -> Dict:
        """
        Process a single video frame causally.
        Returns complete frame tracking state, diagnostic records, and telemetry.
        """
        t_start = time.perf_counter()

        # 1. Detection Phase (if not provided externally by benchmark harness)
        if detections is None:
            if self.detector is not None:
                detections = self.detector.detect(frame, frame_idx)
            else:
                detections = []

        self.total_detections_count += len(detections)

        # 2. Causal Motion Prediction Phase
        # Predict state of all active (non-expired) tracks
        active_tracks = [t for t in self.tracks if t.state != TrackState.EXPIRED]
        for trk in active_tracks:
            old_state = trk.state
            trk.predict(
                lost_timeout_frames=self.config.lost_timeout_frames,
                max_lost_frames=self.config.max_lost_frames
            )
            # Log transition into OCCLUDED or LOST state
            if self.oie and old_state != trk.state:
                if trk.state == TrackState.OCCLUDED:
                    self.oie.log_lifecycle_event(
                        "OCCLUSION_ENTER", trk, frame_idx,
                        f"Missing observation for {trk.time_since_update} frames; entered OCCLUDED state."
                    )
                elif trk.state == TrackState.LOST:
                    self.oie.log_lifecycle_event(
                        "LOST_ENTER", trk, frame_idx,
                        f"Missing observation exceeded lost_timeout ({self.config.lost_timeout_frames} frames); entered LOST state."
                    )

        # 3. Crowd Pressure Telemetry
        crowd_metrics = None
        if self.oie:
            crowd_metrics = self.oie.compute_crowd_pressure(frame_idx, active_tracks, detections)

        # 4. Partition Detections by Confidence (Two-Stage ByteTrack Strategy)
        high_dets = [d for d in detections if d.confidence >= self.config.high_det_thresh]
        low_dets = [
            d for d in detections
            if self.config.low_det_thresh <= d.confidence < self.config.high_det_thresh
        ]

        # 5. Partition Tracks: Confirmed/Occluded vs Tentative
        confirmed_or_missing_tracks = [
            t for t in active_tracks
            if t.state in (TrackState.CONFIRMED, TrackState.OCCLUDED, TrackState.LOST, TrackState.RECOVERED)
        ]
        tentative_tracks = [t for t in active_tracks if t.state == TrackState.TENTATIVE]

        # 6. Stage 1: Associate Confirmed/Missing Tracks with High-Confidence Detections
        matches_s1, unmatched_tracks_s1, unmatched_dets_s1 = self._associate_stage1(
            confirmed_or_missing_tracks, high_dets, frame_idx
        )

        # Update Stage 1 matched tracks
        for trk_idx, det_idx in matches_s1:
            trk = confirmed_or_missing_tracks[trk_idx]
            det = high_dets[det_idx]
            was_missing = trk.state in (TrackState.OCCLUDED, TrackState.LOST)
            trk.update(
                det.bbox, det.confidence, det.embedding,
                crop_quality=det.crop_quality,
                overlap_index=det.overlap_index,
                min_hits_to_confirm=self.config.min_hits_to_confirm
            )
            if was_missing:
                self.total_recoveries_count += 1

        # 7. Stage 2: Associate Remaining Tracks with Low-Confidence Detections (IoU only)
        rem_tracks_s1 = [confirmed_or_missing_tracks[i] for i in unmatched_tracks_s1 if confirmed_or_missing_tracks[i].state != TrackState.LOST]
        matches_s2, unmatched_tracks_s2, _ = self._associate_stage2(rem_tracks_s1, low_dets)

        for trk_idx, det_idx in matches_s2:
            trk = rem_tracks_s1[trk_idx]
            det = low_dets[det_idx]
            trk.update(
                det.bbox, det.confidence, det.embedding,
                crop_quality=det.crop_quality,
                overlap_index=det.overlap_index,
                min_hits_to_confirm=self.config.min_hits_to_confirm
            )

        # 8. Stage 3: Associate Tentative Tracks with Remaining High-Confidence Detections
        rem_high_dets = [high_dets[i] for i in unmatched_dets_s1]
        matches_s3, _, unmatched_high_dets_final = self._associate_stage3(tentative_tracks, rem_high_dets)

        for trk_idx, det_idx in matches_s3:
            trk = tentative_tracks[trk_idx]
            det = rem_high_dets[det_idx]
            trk.update(
                det.bbox, det.confidence, det.embedding,
                crop_quality=det.crop_quality,
                overlap_index=det.overlap_index,
                min_hits_to_confirm=self.config.min_hits_to_confirm
            )

        # 9. Initialize New Tracks for Remaining Unmatched High-Confidence Detections
        for det_idx in unmatched_high_dets_final:
            det = rem_high_dets[det_idx]
            # Spawn new track in TENTATIVE state with unique ID
            new_track = Track(
                track_id=self._next_id,
                initial_bbox=det.bbox,
                confidence=det.confidence,
                embedding=det.embedding,
                crop_quality=det.crop_quality,
                gallery_size=self.config.appearance_memory_size
            )
            self._next_id += 1
            self.tracks.append(new_track)

        # 10. Clean Up Expired Tracks
        self.tracks = [t for t in self.tracks if t.state != TrackState.EXPIRED]

        # 11. Latency & Telemetry Profiling
        t_elapsed = time.perf_counter() - t_start
        self.last_latency_ms = max(0.1, t_elapsed * 1000.0)
        self.last_fps = 1.0 / t_elapsed if t_elapsed > 0 else 60.0
        self.frame_latencies.append(self.last_latency_ms)
        self.total_frames_processed += 1

        # Compile active tracks output for frontend
        visible_tracks = [t.to_dict() for t in self.tracks if t.state in (TrackState.CONFIRMED, TrackState.RECOVERED, TrackState.OCCLUDED)]
        recent_diagnostics = [d.to_dict() for d in self.oie.diagnostic_records[-10:]] if self.oie else []

        return {
            "frame_idx": frame_idx,
            "tracks": visible_tracks,
            "all_tracks_count": len(self.tracks),
            "confirmed_count": len([t for t in self.tracks if t.state == TrackState.CONFIRMED]),
            "occluded_count": len([t for t in self.tracks if t.state in (TrackState.OCCLUDED, TrackState.LOST)]),
            "recovered_count": self.total_recoveries_count,
            "total_detections": len(detections),
            "crowd_pressure": crowd_metrics.__dict__ if crowd_metrics else None,
            "diagnostics": recent_diagnostics,
            "latency_ms": round(self.last_latency_ms, 2),
            "fps": round(self.last_fps, 1)
        }

    def _associate_stage1(
        self,
        tracks: List[Track],
        detections: List[PersonDetection],
        frame_idx: int
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Stage 1: Multi-cue Hungarian assignment on high-confidence detections."""
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))

        track_bboxes = np.array([t.predicted_bbox for t in tracks], dtype=np.float32)
        det_bboxes = np.array([d.bbox for d in detections], dtype=np.float32)

        iou_matrix = compute_iou_matrix(track_bboxes, det_bboxes)
        motion_matrix = compute_motion_cost_matrix(tracks, detections)
        appearance_matrix = compute_appearance_cost_matrix(tracks, detections)

        if self.config.enable_oie and self.oie is not None:
            cost_matrix = self.oie.compute_adaptive_cost_matrix(
                tracks, detections, iou_matrix, motion_matrix, appearance_matrix
            )
        else:
            cost_matrix = (
                self.config.weight_geometry * (1.0 - iou_matrix) +
                self.config.weight_motion * motion_matrix +
                self.config.weight_appearance * appearance_matrix
            )

        candidate_matches, unmatched_trks, unmatched_dets = linear_assignment(
            cost_matrix, cost_threshold=self.config.match_iou_thresh_stage1
        )

        # If OIE enabled, apply Ambiguity-Aware Rejection filter
        if self.config.enable_oie and self.oie is not None:
            confirmed_matches, rejected_trks, rejected_dets = self.oie.filter_ambiguous_recoveries(
                candidate_matches, tracks, detections, cost_matrix,
                iou_matrix, motion_matrix, appearance_matrix, frame_idx
            )
            unmatched_trks.extend(rejected_trks)
            unmatched_dets.extend(rejected_dets)
            return confirmed_matches, unmatched_trks, unmatched_dets

        return candidate_matches, unmatched_trks, unmatched_dets

    def _associate_stage2(
        self,
        tracks: List[Track],
        detections: List[PersonDetection]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Stage 2: Geometric IoU assignment for low-confidence detections."""
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))

        track_bboxes = np.array([t.predicted_bbox for t in tracks], dtype=np.float32)
        det_bboxes = np.array([d.bbox for d in detections], dtype=np.float32)
        iou_matrix = compute_iou_matrix(track_bboxes, det_bboxes)
        cost_matrix = 1.0 - iou_matrix

        return linear_assignment(cost_matrix, cost_threshold=self.config.match_iou_thresh_stage2)

    def _associate_stage3(
        self,
        tracks: List[Track],
        detections: List[PersonDetection]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Stage 3: IoU assignment for tentative tracks."""
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))

        track_bboxes = np.array([t.predicted_bbox for t in tracks], dtype=np.float32)
        det_bboxes = np.array([d.bbox for d in detections], dtype=np.float32)
        iou_matrix = compute_iou_matrix(track_bboxes, det_bboxes)
        cost_matrix = 1.0 - iou_matrix

        return linear_assignment(cost_matrix, cost_threshold=0.60)
