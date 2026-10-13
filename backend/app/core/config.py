"""
ZED VISION - Core Configuration and Settings
Identity-Preserving Multi-Object Tracking Through Dense Occlusion (PS-2)
"""

from pathlib import Path
from pydantic import BaseModel, Field


class DetectorConfig(BaseModel):
    model_type: str = Field(default="opencv_dnn", description="Detector type: 'onnx', 'opencv_dnn', or 'synthetic'")
    model_path: str = Field(default="data/models/yolov8n.onnx", description="Path to ONNX weights")
    confidence_threshold: float = Field(default=0.45, ge=0.05, le=0.95, description="Detection confidence threshold")
    nms_iou_threshold: float = Field(default=0.45, ge=0.1, le=0.9, description="Non-maximum suppression IoU threshold")
    input_size: int = Field(default=640, description="Inference input resolution (square)")
    device: str = Field(default="cpu", description="Execution device: 'cpu' or 'cuda'")


class TrackerConfig(BaseModel):
    # Lifecycle
    min_hits_to_confirm: int = Field(default=3, ge=1, le=10, description="Frames required to transition TENTATIVE -> CONFIRMED")
    lost_timeout_frames: int = Field(default=15, ge=2, le=120, description="Frames before CONFIRMED transitions to LOST")
    max_lost_frames: int = Field(default=60, ge=5, le=300, description="Max occlusion frames before track EXPIRES")

    # Association thresholds
    high_det_thresh: float = Field(default=0.50, ge=0.2, le=0.9, description="High-confidence detection threshold for Stage 1")
    low_det_thresh: float = Field(default=0.15, ge=0.05, le=0.49, description="Low-confidence detection threshold for Stage 2")
    match_iou_thresh_stage1: float = Field(default=0.70, ge=0.2, le=0.95, description="Max cost / IoU threshold for Stage 1")
    match_iou_thresh_stage2: float = Field(default=0.50, ge=0.1, le=0.9, description="Max IoU cost threshold for Stage 2")

    # Cost weights (Baseline)
    weight_motion: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for motion/Mahalanobis cost")
    weight_appearance: float = Field(default=0.40, ge=0.0, le=1.0, description="Weight for appearance cosine cost")
    weight_geometry: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for geometric IoU cost")

    # Occlusion Intelligence Engine (OIE)
    enable_oie: bool = Field(default=True, description="Enable Occlusion Intelligence Engine enhancements")
    enable_uncertainty_recovery: bool = Field(default=True, description="Enable covariance-guided spatial gating & gap penalty")
    enable_adaptive_weights: bool = Field(default=True, description="Modulate appearance weight based on crop occlusion overlap")
    enable_temporal_memory: bool = Field(default=True, description="Maintain anti-pollution appearance memory gallery")
    enable_ambiguity_rejection: bool = Field(default=True, description="Reject recovery if best vs second-best margin < threshold")
    ambiguity_margin_threshold: float = Field(default=0.12, ge=0.02, le=0.40, description="Margin threshold to reject ambiguous recovery")
    appearance_memory_size: int = Field(default=8, ge=2, le=30, description="Max clean crops in temporal appearance gallery")
    gap_penalty_factor: float = Field(default=0.15, ge=0.0, le=0.5, description="Cost penalty per log-frame of occlusion")


class PrivacyConfig(BaseModel):
    ephemeral_sessions: bool = Field(default=True, description="Automatically clean up video and frame caches upon session termination")
    session_retention_minutes: int = Field(default=60, description="Session lifetime before automatic cleanup")
    store_face_biometrics: bool = Field(default=False, description="Strictly disabled: no facial features extracted or stored")


class AppConfig(BaseModel):
    app_name: str = "ZED VISION"
    app_version: str = "1.0.0"
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    uploads_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads"
    outputs_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "outputs"
    experiments_db_path: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "experiments.db"

    detector: DetectorConfig = DetectorConfig()
    tracker: TrackerConfig = TrackerConfig()
    privacy: PrivacyConfig = PrivacyConfig()


config = AppConfig()
config.uploads_dir.mkdir(parents=True, exist_ok=True)
config.outputs_dir.mkdir(parents=True, exist_ok=True)
(config.data_dir / "models").mkdir(parents=True, exist_ok=True)
(config.data_dir / "samples").mkdir(parents=True, exist_ok=True)
