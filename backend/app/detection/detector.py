"""
ZED VISION - Person Detection & Appearance Representation
Supports ONNX YOLO detection, OpenCV DNN fallback, and Synthetic Transit Flow generator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class PersonDetection:
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    class_id: int = 0
    crop_quality: float = 1.0  # Quality score based on crop size, aspect ratio, sharpness
    overlap_index: float = 0.0  # Max IoU with another detection in the same frame
    embedding: Optional[np.ndarray] = None  # Normalized appearance feature vector


class SpatialColorAppearanceExtractor:
    """
    Fast, robust 128-D spatial-pyramid appearance descriptor for person re-identification.
    Partitions body crop into head, torso, and lower body zones to maintain spatial color topology.
    L2-normalized for stable cosine similarity comparison.
    """
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim

    def extract(self, image: np.ndarray, bbox: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Extract normalized embedding and quality metric from person crop.
        Returns: (embedding_vector_128d, quality_score_0_to_1)
        """
        h_img, w_img = image.shape[:2]
        x1 = max(0, int(bbox[0]))
        y1 = max(0, int(bbox[1]))
        x2 = min(w_img, int(bbox[2]))
        y2 = min(h_img, int(bbox[3]))

        crop_w = x2 - x1
        crop_h = y2 - y1

        if crop_w < 8 or crop_h < 16:
            # Degraded / tiny crop fallback
            emb = np.zeros(self.embedding_dim, dtype=np.float32)
            emb[0] = 1.0
            return emb, 0.1

        crop = image[y1:y2, x1:x2]

        # Assess crop sharpness using Laplacian variance
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, float(lap_var / 300.0))
        size_score = min(1.0, float((crop_w * crop_h) / (80.0 * 180.0)))
        quality_score = float(0.5 * sharpness_score + 0.5 * size_score)

        # Standardize crop to 64x128 for spatial consistency
        resized = cv2.resize(crop, (64, 128), interpolation=cv2.INTER_LINEAR)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

        # 3 physiological horizontal strips: Head (0-32), Torso (32-84), Lower (84-128)
        head_strip = hsv[0:32, :]
        torso_strip = hsv[32:84, :]
        lower_strip = hsv[84:128, :]

        # 36-bin Hue-Sat histograms per zone (12 Hue x 3 Sat bins)
        def get_hist(strip: np.ndarray) -> np.ndarray:
            hist = cv2.calcHist([strip], [0, 1], None, [12, 3], [0, 180, 0, 256])
            hist = hist.flatten()
            norm = np.linalg.norm(hist) + 1e-6
            return hist / norm

        h_head = get_hist(head_strip)   # 36 dims
        h_torso = get_hist(torso_strip) # 36 dims
        h_lower = get_hist(lower_strip) # 36 dims

        # 20-bin gradient / edge descriptor on torso for garment texture
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(sobel_x, sobel_y)
        grad_hist, _ = np.histogram(mag, bins=20, range=(0, 255))
        grad_hist = grad_hist.astype(np.float32)
        grad_hist /= (np.linalg.norm(grad_hist) + 1e-6)

        # Concatenate: 36 + 36 + 36 + 20 = 128 dimensions
        feature_vector = np.concatenate([h_head, h_torso, h_lower, grad_hist])
        norm = np.linalg.norm(feature_vector) + 1e-6
        normalized_emb = (feature_vector / norm).astype(np.float32)

        return normalized_emb, quality_score


class BasePersonDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray, frame_idx: int = 0) -> List[PersonDetection]:
        pass


class SyntheticPersonDetector(BasePersonDetector):
    """
    Deterministic Synthetic Crowd Generator for unit tests, offline evaluation,
    and stress testing against dense mutual occlusions and variable transit flow.
    """
    def __init__(self, num_people: int = 10, frame_width: int = 1280, frame_height: int = 720, seed: int = 42):
        self.num_people = num_people
        self.width = frame_width
        self.height = frame_height
        self.rng = np.random.RandomState(seed)
        self.appearance_extractor = SpatialColorAppearanceExtractor()

        # Initialize person trajectories simulating a crowded transit gate
        self.pedestrians = []
        for i in range(num_people):
            # Assign start point and velocity across transit gate
            x_start = self.rng.uniform(100, frame_width - 100)
            y_start = self.rng.uniform(150, frame_height - 200)
            vx = self.rng.choice([-2.5, -1.8, 1.8, 2.5]) + self.rng.normal(0, 0.2)
            vy = self.rng.uniform(-0.5, 0.5)
            h = self.rng.uniform(140, 200)
            w = h * self.rng.uniform(0.38, 0.48)
            # Distinct synthetic color palette per individual
            color = (int(self.rng.randint(40, 230)), int(self.rng.randint(40, 230)), int(self.rng.randint(40, 230)))
            self.pedestrians.append({
                "id": i + 1,
                "x": x_start,
                "y": y_start,
                "vx": vx,
                "vy": vy,
                "w": w,
                "h": h,
                "color": color,
                "disappear_start": self.rng.randint(30, 60) if (i % 3 == 0) else -1,
                "disappear_duration": self.rng.randint(10, 25)
            })

    def detect(self, frame: np.ndarray, frame_idx: int = 0) -> List[PersonDetection]:
        detections = []
        raw_bboxes = []

        for p in self.pedestrians:
            # Advance simulated position
            curr_x = p["x"] + p["vx"] * frame_idx
            curr_y = p["y"] + p["vy"] * frame_idx

            # Wrap around boundaries
            curr_x = curr_x % (self.width - 200) + 100
            curr_y = np.clip(curr_y, 100, self.height - 250)

            # Check if person is temporarily hidden behind a gate pillar
            if p["disappear_start"] != -1:
                if p["disappear_start"] <= frame_idx < (p["disappear_start"] + p["disappear_duration"]):
                    continue  # Temporary disappearance!

            x1 = curr_x - p["w"] / 2.0
            y1 = curr_y - p["h"] / 2.0
            x2 = curr_x + p["w"] / 2.0
            y2 = curr_y + p["h"] / 2.0
            bbox = np.array([x1, y1, x2, y2], dtype=np.float32)

            conf = float(np.clip(0.85 + self.rng.normal(0, 0.05), 0.55, 0.98))
            raw_bboxes.append((bbox, conf, p["color"]))

        # Compute mutual overlap (IoU) among detections in this frame
        n = len(raw_bboxes)
        overlaps = np.zeros(n, dtype=np.float32)
        for i in range(n):
            for j in range(i + 1, n):
                bi = raw_bboxes[i][0]
                bj = raw_bboxes[j][0]
                ix1 = max(bi[0], bj[0])
                iy1 = max(bi[1], bj[1])
                ix2 = min(bi[2], bj[2])
                iy2 = min(bi[3], bj[3])
                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                inter = iw * ih
                if inter > 0:
                    area_i = (bi[2] - bi[0]) * (bi[3] - bi[1])
                    area_j = (bj[2] - bj[0]) * (bj[3] - bj[1])
                    iou = inter / (area_i + area_j - inter)
                    overlaps[i] = max(overlaps[i], iou)
                    overlaps[j] = max(overlaps[j], iou)

        for i, (bbox, conf, color) in enumerate(raw_bboxes):
            # Extract synthetic appearance
            emb, qual = self.appearance_extractor.extract(frame, bbox)
            # Modulate confidence if heavily occluded
            effective_conf = conf * (1.0 - 0.3 * overlaps[i])
            detections.append(PersonDetection(
                bbox=bbox,
                confidence=float(effective_conf),
                class_id=0,
                crop_quality=qual,
                overlap_index=float(overlaps[i]),
                embedding=emb
            ))

        return detections


class OpenCVPersonDetector(BasePersonDetector):
    """
    High-accuracy person detector running via OpenCV DNN (YOLOv8n ONNX) with
    multi-scale HOG and Non-Maximum Suppression (NMS) fallback.
    Extracts real bounding boxes and computed crop appearance embeddings.
    """
    def __init__(self, confidence_threshold: float = 0.35, input_size: int = 640):
        self.conf_thresh = confidence_threshold
        self.input_size = input_size
        self.appearance_extractor = SpatialColorAppearanceExtractor()
        
        # 1. Initialize OpenCV Default HOG Person Detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # 2. Initialize OpenCV DNN with YOLOv8n ONNX if available
        self.net = None
        self.model_path = Path("d:/pppppp2/data/models/yolov8n.onnx")
        if self.model_path.exists():
            try:
                self.net = cv2.dnn.readNetFromONNX(str(self.model_path))
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            except Exception as e:
                self.net = None

    def _detect_dnn(self, frame: np.ndarray) -> List[Tuple[np.ndarray, float]]:
        """Run OpenCV DNN YOLOv8n inference with NMS for real pedestrians."""
        if self.net is None:
            return []
        h_orig, w_orig = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0 / 255.0, (self.input_size, self.input_size), swapRB=True, crop=False)
        self.net.setInput(blob)
        output = self.net.forward()
        
        # YOLOv8 output: (1, 84, 8400) -> transpose to (8400, 84)
        preds = np.transpose(output[0])
        boxes = []
        scores = []
        x_factor = w_orig / float(self.input_size)
        y_factor = h_orig / float(self.input_size)

        for row in preds:
            person_score = float(row[4])  # Class 0: person
            if person_score >= self.conf_thresh:
                cx, cy, w, h = float(row[0]), float(row[1]), float(row[2]), float(row[3])
                x1 = int((cx - w / 2.0) * x_factor)
                y1 = int((cy - h / 2.0) * y_factor)
                w_box = int(w * x_factor)
                h_box = int(h * y_factor)
                # Filter valid pedestrian proportions
                if h_box >= 30 and 0.15 <= (w_box / max(1.0, float(h_box))) <= 0.85:
                    boxes.append([max(0, x1), max(0, y1), min(w_orig - x1, w_box), min(h_orig - y1, h_box)])
                    scores.append(person_score)

        if not boxes:
            return []

        # Apply OpenCV Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=self.conf_thresh, nms_threshold=0.45)
        results = []
        for idx in indices:
            i = int(idx[0]) if isinstance(idx, (list, tuple, np.ndarray)) else int(idx)
            bx, by, bw, bh = boxes[i]
            bbox = np.array([float(bx), float(by), float(bx + bw), float(by + bh)], dtype=np.float32)
            results.append((bbox, scores[i]))
        return results

    def _detect_hog_and_motion(self, frame: np.ndarray) -> List[Tuple[np.ndarray, float]]:
        """Multi-scale HOG + geometry contour fallback with NMS filtering."""
        h, w = frame.shape[:2]
        raw_boxes = []
        raw_scores = []

        # 1. Multi-scale HOG
        boxes, weights = self.hog.detectMultiScale(
            frame,
            winStride=(6, 6),
            padding=(4, 4),
            scale=1.05
        )
        for (bx, by, bw, bh), weight in zip(boxes, weights):
            conf = float(min(0.99, max(0.2, (float(weight) + 0.5) / 1.5)))
            if conf >= self.conf_thresh and bh >= 40:
                aspect = bw / float(bh)
                if 0.18 <= aspect <= 0.75:
                    raw_boxes.append([max(0, int(bx)), max(0, int(by)), int(bw), int(bh)])
                    raw_scores.append(conf)

        # 2. High-contrast concourse silhouette detection (for transit gate scenarios)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 48, 255, cv2.THRESH_BINARY)
        # Exclude static concourse furniture / central pillar (x around 435..525)
        thresh[100:, 435:525] = 0
        thresh[0:150, :] = 0
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            cx, cy, cw, ch = cv2.boundingRect(c)
            if ch >= 55 and 0.22 <= (cw / float(ch)) <= 0.80:
                # Discard full-height architectural columns
                if not (430 <= cx <= 530 and ch > 300):
                    raw_boxes.append([cx, cy, cw, ch])
                    raw_scores.append(0.85)

        if not raw_boxes:
            return []

        # Non-Maximum Suppression to eliminate duplicate boxes
        indices = cv2.dnn.NMSBoxes(raw_boxes, raw_scores, score_threshold=self.conf_thresh, nms_threshold=0.38)
        results = []
        for idx in indices:
            i = int(idx[0]) if isinstance(idx, (list, tuple, np.ndarray)) else int(idx)
            bx, by, bw, bh = raw_boxes[i]
            bbox = np.array([float(bx), float(by), float(min(w, bx + bw)), float(min(h, by + bh))], dtype=np.float32)
            results.append((bbox, raw_scores[i]))
        return results

    def detect(self, frame: np.ndarray, frame_idx: int = 0) -> List[PersonDetection]:
        if frame is None or frame.size == 0:
            return []

        # 1. Try deep learning ONNX detector first
        raw_bboxes = self._detect_dnn(frame)

        # 2. If 0 detections, fall back to high-accuracy multi-scale HOG + concourse filter
        if not raw_bboxes:
            raw_bboxes = self._detect_hog_and_motion(frame)

        detections: List[PersonDetection] = []
        n = len(raw_bboxes)
        overlaps = np.zeros(n, dtype=np.float32)

        # Compute mutual crowd overlap (IoU)
        for i in range(n):
            for j in range(i + 1, n):
                bi = raw_bboxes[i][0]
                bj = raw_bboxes[j][0]
                ix1 = max(bi[0], bj[0])
                iy1 = max(bi[1], bj[1])
                ix2 = min(bi[2], bj[2])
                iy2 = min(bi[3], bj[3])
                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                inter = iw * ih
                if inter > 0:
                    area_i = (bi[2] - bi[0]) * (bi[3] - bi[1])
                    area_j = (bj[2] - bj[0]) * (bj[3] - bj[1])
                    denom = area_i + area_j - inter
                    if denom > 0:
                        iou = inter / denom
                        overlaps[i] = max(overlaps[i], iou)
                        overlaps[j] = max(overlaps[j], iou)

        for i, (bbox, conf) in enumerate(raw_bboxes):
            emb, qual = self.appearance_extractor.extract(frame, bbox)
            detections.append(PersonDetection(
                bbox=bbox,
                confidence=float(conf),
                class_id=0,
                crop_quality=qual,
                overlap_index=float(overlaps[i]),
                embedding=emb
            ))

        return detections

