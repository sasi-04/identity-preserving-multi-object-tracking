"""
ZED VISION - Active Session Manager & Video Processing Service
Coordinates live streaming, frame stepping, WebSocket dispatch, and ephemeral session cleanup.
"""

import asyncio
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional
import uuid
import cv2

from backend.app.core.config import TrackerConfig, config
from backend.app.detection.detector import OpenCVPersonDetector, SyntheticPersonDetector
from backend.app.services.experiment_store import ExperimentStore
from backend.app.tracking.tracker import MultiObjectTracker
from backend.app.tracking.video_pipeline import VideoPipeline


class TrackingSession:
    def __init__(self, session_id: str, video_path: Path, tracker_config: TrackerConfig, detector_type: str = "opencv"):
        self.session_id: str = session_id
        self.video_path: Path = video_path
        self.config: TrackerConfig = tracker_config
        self.detector_type: str = detector_type
        self._lock = threading.Lock()

        # Initialize detector
        if detector_type == "synthetic":
            self.detector = SyntheticPersonDetector()
        else:
            self.detector = OpenCVPersonDetector()

        self.tracker = MultiObjectTracker(tracker_config, detector=self.detector)
        self.pipeline = VideoPipeline(self.tracker)

        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        self.total_frames: int = 0
        self.video_fps: float = 30.0
        self.current_frame_idx: int = 0

        self.is_running: bool = False
        self.is_paused: bool = False
        self.is_finished: bool = False

        self.last_frame_base64: str = ""
        self.last_telemetry: Optional[dict] = None
        self.diagnostic_events: List[dict] = []
        self.created_at: float = time.time()

        self._init_video()

    def _init_video(self) -> None:
        if self.video_path.exists():
            self.cap = cv2.VideoCapture(str(self.video_path))
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 150
            fps_val = self.cap.get(cv2.CAP_PROP_FPS)
            self.video_fps = float(fps_val) if fps_val and fps_val > 0 else 30.0
        else:
            self.cap = None
            self.total_frames = 150

    def step(
        self,
        draw_bboxes: bool = True,
        draw_ids: bool = True,
        draw_trails: bool = True
    ) -> Optional[dict]:
        """
        Process the next frame causally.
        Returns dict with base64 image and telemetry, or None if end of video reached.
        Thread-safe to prevent FFmpeg libavcodec async_lock assertion crashes.
        """
        with self._lock:
            if self.is_finished:
                return None

            if self.cap is None or not self.cap.isOpened():
                # Fallback to generating synthetic frames dynamically
                frame = np.full((540, 960, 3), 30, dtype=np.uint8)
            else:
                try:
                    ret, frame = self.cap.read()
                except Exception:
                    self.is_finished = True
                    self.is_running = False
                    return None

                if not ret or frame is None:
                    self.is_finished = True
                    self.is_running = False
                    return None

            # Execute tracking & rendering
            annotated_frame, telemetry = self.pipeline.process_frame(
                frame,
                self.current_frame_idx,
                draw_bboxes=draw_bboxes,
                draw_ids=draw_ids,
                draw_trails=draw_trails
            )

            self.last_frame_base64 = self.pipeline.frame_to_base64_jpeg(annotated_frame, quality=75)
            self.last_telemetry = telemetry
            self.current_frame_idx += 1

            # Collect any new diagnostic events from OIE
            if self.tracker.oie:
                self.diagnostic_events = [d.to_dict() for d in self.tracker.oie.diagnostic_records]

            return {
                "session_id": self.session_id,
                "frame_idx": self.current_frame_idx,
                "total_frames": self.total_frames,
                "image": self.last_frame_base64,
                "telemetry": telemetry,
                "is_finished": self.is_finished
            }

    def reset(self) -> None:
        with self._lock:
            self.current_frame_idx = 0
            self.is_running = False
            self.is_paused = False
            self.is_finished = False
            self.tracker.reset()
            self.diagnostic_events = []
            if self.cap and self.cap.isOpened():
                try:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                except Exception:
                    pass

    def close(self) -> None:
        with self._lock:
            self.is_running = False
            self.is_finished = True
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None


class SessionManager:
    def __init__(self, store: Optional[ExperimentStore] = None):
        self.store = store or ExperimentStore()
        self.sessions: Dict[str, TrackingSession] = {}
        self._lock = threading.Lock()
        self._ensure_sample_demo_video()

    def _ensure_sample_demo_video(self) -> Path:
        demo_path = config.data_dir / "samples" / "transit_gate_demo.mp4"
        if not demo_path.exists():
            VideoPipeline.create_synthetic_demo_video(demo_path, num_frames=150, fps=30)
        return demo_path

    def create_session(
        self,
        video_path: Optional[Path] = None,
        tracker_config: Optional[TrackerConfig] = None,
        detector_type: str = "opencv"
    ) -> TrackingSession:
        with self._lock:
            # Gracefully release and pop any older active sessions
            for old_id in list(self.sessions.keys()):
                old_session = self.sessions.pop(old_id, None)
                if old_session:
                    try:
                        old_session.close()
                    except Exception:
                        pass

            session_id = str(uuid.uuid4())[:8]
            if video_path is None or not video_path.exists():
                video_path = self._ensure_sample_demo_video()

            cfg = tracker_config or TrackerConfig()
            session = TrackingSession(session_id, video_path, cfg, detector_type=detector_type)
            self.sessions[session_id] = session

        # Persist session in SQLite
        self.store.save_session(
            session_id=session_id,
            video_name=video_path.name,
            is_oie=cfg.enable_oie,
            status="INITIALIZED"
        )
        return session

    def get_session(self, session_id: str) -> Optional[TrackingSession]:
        with self._lock:
            return self.sessions.get(session_id)

    def stop_session(self, session_id: str) -> bool:
        with self._lock:
            session = self.sessions.pop(session_id, None)
            if session:
                try:
                    session.close()
                except Exception:
                    pass
                return True
            return False

    def list_sample_videos(self) -> List[dict]:
        self._ensure_sample_demo_video()
        samples_dir = config.data_dir / "samples"
        videos = []
        for p in samples_dir.glob("*.mp4"):
            videos.append({
                "name": p.name,
                "path": str(p),
                "size_mb": round(p.stat().st_size / (1024 * 1024), 2)
            })
        return videos
