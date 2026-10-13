"""Unit tests for Person Detection & Appearance Feature Extraction."""
import cv2
import numpy as np
import pytest
from pathlib import Path
from backend.app.detection.detector import (
    OpenCVPersonDetector,
    SyntheticPersonDetector,
    SpatialColorAppearanceExtractor,
    PersonDetection
)


def test_spatial_color_appearance_extractor():
    extractor = SpatialColorAppearanceExtractor(embedding_dim=128)
    image = np.zeros((200, 100, 3), dtype=np.uint8)
    # Head, torso, lower body with distinct colors
    image[0:50, :] = [200, 180, 160]   # Head
    image[50:140, :] = [30, 40, 200]   # Red torso
    image[140:200, :] = [30, 30, 30]   # Dark legs

    bbox = np.array([10.0, 10.0, 90.0, 190.0])
    emb, quality = extractor.extract(image, bbox)

    assert len(emb) == 128
    assert np.isclose(np.linalg.norm(emb), 1.0, atol=1e-3)
    assert 0.0 <= quality <= 1.0


def test_tiny_crop_appearance_fallback():
    extractor = SpatialColorAppearanceExtractor(embedding_dim=128)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    # Tiny 4x4 crop
    bbox = np.array([10.0, 10.0, 14.0, 14.0])
    emb, quality = extractor.extract(image, bbox)

    assert len(emb) == 128
    assert emb[0] == 1.0
    assert quality <= 0.2


def test_synthetic_detector_deterministic():
    det1 = SyntheticPersonDetector(num_people=8, seed=42)
    det2 = SyntheticPersonDetector(num_people=8, seed=42)

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    res1 = det1.detect(frame, frame_idx=5)
    res2 = det2.detect(frame, frame_idx=5)

    assert len(res1) == len(res2)
    for d1, d2 in zip(res1, res2):
        assert np.allclose(d1.bbox, d2.bbox)
        assert np.isclose(d1.confidence, d2.confidence)


def test_opencv_detector_initialization_and_onnx():
    detector = OpenCVPersonDetector()
    assert detector.hog is not None
    # Check that model path points to existing weights if downloaded
    model_path = Path("d:/pppppp2/data/models/yolov8n.onnx")
    if model_path.exists():
        assert detector.net is not None


def test_opencv_detector_empty_frame():
    detector = OpenCVPersonDetector()
    empty = np.zeros((0, 0, 3), dtype=np.uint8)
    assert detector.detect(empty) == []


def test_opencv_detector_synthetic_frame_concourse():
    detector = OpenCVPersonDetector()
    # Create synthetic frame with high-contrast pedestrian rectangle
    frame = np.full((540, 960, 3), (28, 28, 34), dtype=np.uint8)
    # Draw realistic pedestrian silhouette
    cv2.rectangle(frame, (250, 200), (310, 360), (40, 160, 60), -1)
    cv2.circle(frame, (280, 185), 15, (220, 190, 170), -1)

    dets = detector.detect(frame, frame_idx=0)
    assert isinstance(dets, list)
    # If concourse silhouette is detected, verify output format
    for d in dets:
        assert isinstance(d, PersonDetection)
        assert len(d.bbox) == 4
        assert 0.0 <= d.confidence <= 1.0
        assert len(d.embedding) == 128
