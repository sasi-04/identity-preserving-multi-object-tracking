"""
ZED VISION - Causal Video Pipeline & Annotation Engine
Handles frame streaming, real-time visual rendering, and telemetry dispatch.
"""

import base64
from pathlib import Path
import time
from typing import Callable, Dict, Generator, Optional
import cv2
import numpy as np

from backend.app.core.config import TrackerConfig
from backend.app.detection.detector import BasePersonDetector, OpenCVPersonDetector, SyntheticPersonDetector
from backend.app.tracking.tracker import MultiObjectTracker


class VideoPipeline:
    """
    Streaming and batch video processing pipeline.
    Renders enterprise-grade visual analytics and outputs real-time frame telemetry.
    """
    # Color palette (BGR for OpenCV)
    COLOR_CONFIRMED = (80, 200, 120)    # Emerald Green
    COLOR_OCCLUDED = (20, 160, 245)     # Amber Orange
    COLOR_RECOVERED = (50, 50, 235)     # ZED Crimson Red
    COLOR_TENTATIVE = (220, 180, 20)    # Cyan / Steel
    COLOR_TRAIL = (200, 120, 80)        # Lavender trail

    def __init__(self, tracker: MultiObjectTracker):
        self.tracker = tracker
        self.is_running: bool = False
        self.is_paused: bool = False

    def process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        draw_bboxes: bool = True,
        draw_ids: bool = True,
        draw_trails: bool = True,
        draw_hud: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Run tracking on a single frame and render visual overlays.
        """
        # Execute causal tracker update
        telemetry = self.tracker.update(frame, frame_idx)

        annotated_frame = frame.copy()
        h, w = frame.shape[:2]

        if draw_trails:
            # Draw smooth trajectory trails
            for trk in self.tracker.tracks:
                if len(trk.trajectory) > 1:
                    pts = np.array(list(trk.trajectory), dtype=np.int32)
                    cv2.polylines(annotated_frame, [pts], isClosed=False, color=self.COLOR_TRAIL, thickness=2, lineType=cv2.LINE_AA)

        if draw_bboxes:
            for trk in self.tracker.tracks:
                state_str = trk.state.value
                if state_str == "CONFIRMED":
                    color = self.COLOR_CONFIRMED
                elif state_str in ("OCCLUDED", "LOST"):
                    color = self.COLOR_OCCLUDED
                elif state_str == "RECOVERED":
                    color = self.COLOR_RECOVERED
                else:
                    color = self.COLOR_TENTATIVE

                bbox = trk.last_bbox
                x1, y1 = max(0, int(bbox[0])), max(0, int(bbox[1]))
                x2, y2 = min(w, int(bbox[2])), min(h, int(bbox[3]))

                # Main bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

                # Draw uncertainty halo if occluded
                if state_str in ("OCCLUDED", "LOST"):
                    unc_radius = int(trk.get_spatial_uncertainty())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    cv2.circle(annotated_frame, (cx, cy), max(15, unc_radius), color, 1, cv2.LINE_AA)

                if draw_ids:
                    # Clean label badge
                    label = f"ID #{trk.track_id} | {state_str[:3]} {trk.confidence:.2f}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.45
                    thickness = 1
                    (txt_w, txt_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

                    badge_y1 = max(0, y1 - txt_h - 8)
                    badge_y2 = y1
                    badge_x2 = min(w, x1 + txt_w + 10)

                    # Semi-transparent dark background badge
                    cv2.rectangle(annotated_frame, (x1, badge_y1), (badge_x2, badge_y2), (20, 20, 24), -1)
                    cv2.rectangle(annotated_frame, (x1, badge_y1), (badge_x2, badge_y2), color, 1)
                    cv2.putText(
                        annotated_frame, label, (x1 + 5, badge_y2 - 4),
                        font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA
                    )

        if draw_hud:
            # Top HUD Bar
            hud_bg = np.zeros((40, w, 3), dtype=np.uint8)
            annotated_frame[0:40, 0:w] = cv2.addWeighted(annotated_frame[0:40, 0:w], 0.3, hud_bg, 0.7, 0)
            cv2.line(annotated_frame, (0, 40), (w, 40), (45, 45, 55), 1)

            hud_text = (
                f"ZED VISION | Frame {frame_idx:04d} | "
                f"Active: {telemetry['all_tracks_count']} | "
                f"Confirmed: {telemetry['confirmed_count']} | "
                f"Occluded: {telemetry['occluded_count']} | "
                f"Recovered: {telemetry['recovered_count']} | "
                f"Latency: {telemetry['latency_ms']}ms ({telemetry['fps']} FPS)"
            )
            cv2.putText(
                annotated_frame, hud_text, (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 240), 1, cv2.LINE_AA
            )

        return annotated_frame, telemetry

    @staticmethod
    def frame_to_base64_jpeg(frame: np.ndarray, quality: int = 80) -> str:
        """Encode OpenCV frame to Base64 JPEG data URL for streaming to web client."""
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, buffer = cv2.imencode(".jpg", frame, encode_params)
        if not success:
            return ""
        b64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    @classmethod
    def create_synthetic_demo_video(
        cls,
        output_path: Path,
        num_frames: int = 150,
        fps: int = 30,
        width: int = 960,
        height: int = 540
    ) -> Path:
        """
        Generate a photorealistic synthetic transit gate video with dense crowd crossings,
        pillars causing occlusions, and floor perspective markings.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        rng = np.random.RandomState(42)
        # Create 12 simulated people crossing a transit gate
        pedestrians = []
        palette = [
            (50, 70, 200), (200, 80, 50), (40, 160, 60), (160, 50, 180),
            (210, 170, 40), (50, 180, 210), (120, 120, 120), (80, 40, 150)
        ]
        for i in range(12):
            pedestrians.append({
                "x": rng.uniform(80, width - 80),
                "y": rng.uniform(180, height - 120),
                "vx": rng.choice([-3.0, -2.0, 2.0, 3.0]),
                "vy": rng.uniform(-0.4, 0.4),
                "h": rng.uniform(130, 180),
                "w": rng.uniform(50, 70),
                "color": palette[i % len(palette)],
                "disappear_start": 40 + (i * 12) % 60 if i % 2 == 0 else -1,
                "disappear_duration": 18
            })

        for frame_idx in range(num_frames):
            # Render architectural scene (transit concourse)
            frame = np.full((height, width, 3), (28, 28, 34), dtype=np.uint8)

            # Perspective floor tiles
            for y_line in range(160, height, 40):
                cv2.line(frame, (0, y_line), (width, y_line), (38, 38, 46), 1)
            for x_line in range(0, width, 80):
                cv2.line(frame, (x_line, 160), (int(x_line * 1.2), height), (38, 38, 46), 1)

            # Turnstile / Gate barriers
            cv2.rectangle(frame, (180, 140), (220, 320), (55, 55, 68), -1)
            cv2.rectangle(frame, (460, 140), (500, 320), (55, 55, 68), -1)
            cv2.rectangle(frame, (740, 140), (780, 320), (55, 55, 68), -1)
            cv2.putText(frame, "GATE A", (185, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 140), 1)
            cv2.putText(frame, "GATE B", (465, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 140), 1)
            cv2.putText(frame, "GATE C", (745, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 140), 1)

            # Sort pedestrians by Y coordinate for correct occlusion depth layering
            pedestrians.sort(key=lambda p: p["y"])

            # Render pedestrians
            for p in pedestrians:
                # Update position
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                if p["x"] < 50 or p["x"] > width - 50:
                    p["vx"] *= -1

                # Disappearance logic
                if p["disappear_start"] != -1:
                    if p["disappear_start"] <= frame_idx < (p["disappear_start"] + p["disappear_duration"]):
                        continue  # Hidden behind architectural pillar

                px, py = int(p["x"]), int(p["y"])
                pw, ph = int(p["w"]), int(p["h"])

                # Draw body (torso)
                cv2.rectangle(frame, (px - pw // 2, py - ph // 2 + 25), (px + pw // 2, py + ph // 2), p["color"], -1)
                # Draw head
                head_radius = max(8, pw // 4)
                cv2.circle(frame, (px, py - ph // 2 + 15), head_radius, (220, 190, 170), -1)
                # Draw legs
                cv2.line(frame, (px - pw // 4, py + ph // 2), (px - pw // 4, py + ph // 2 + 20), (30, 30, 35), 4)
                cv2.line(frame, (px + pw // 4, py + ph // 2), (px + pw // 4, py + ph // 2 + 20), (30, 30, 35), 4)

            # Architectural occlusion pillar in foreground (causes dense mutual occlusion)
            cv2.rectangle(frame, (440, 120), (520, height), (42, 42, 52), -1)
            cv2.rectangle(frame, (440, 120), (520, height), (70, 70, 85), 2)
            cv2.putText(frame, "CENTRAL PILLAR", (445, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 140, 160), 1)

            writer.write(frame)

        writer.release()
        return output_path
