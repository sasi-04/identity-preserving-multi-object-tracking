"""
ZED VISION - Health and System Status API Endpoints
"""

import os
import platform
import time
from fastapi import APIRouter
from backend.app.core.config import config

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "app_name": config.app_name,
        "version": config.app_version,
        "timestamp": time.time()
    }


@router.get("/models/status")
def get_model_status():
    return {
        "detector": {
            "name": "OpenCV HOG / ONNX Multi-scale Person Detector",
            "type": config.detector.model_type,
            "status": "operational",
            "class_filter": "person (class 0)",
            "confidence_threshold": config.detector.confidence_threshold,
            "device": "CPU"
        },
        "reid_appearance": {
            "name": "128-D Spatial-Pyramid HSV + Texture Descriptor",
            "metric": "Cosine Distance",
            "status": "operational",
            "temporal_gallery_size": config.tracker.appearance_memory_size,
            "anti_pollution_active": config.tracker.enable_temporal_memory
        },
        "motion_model": {
            "name": "8-State Constant Velocity Kalman Filter",
            "status": "operational",
            "gating": "95% Chi-square Mahalanobis Gate (4-DOF)"
        },
        "oie_engine": {
            "name": "Occlusion Intelligence Engine",
            "status": "active" if config.tracker.enable_oie else "disabled",
            "components": [
                "Uncertainty-Aware Spatial Gating",
                "Adaptive Visibility Weighting",
                "Anti-Pollution Temporal Memory",
                "Ambiguity-Aware Recovery Rejection",
                "Crowd-Pressure Diagnostics (CPI)",
                "Explainable Diagnostic Logging"
            ]
        }
    }


@router.get("/system/status")
def get_system_status():
    return {
        "os": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "processor": platform.processor() or "x86_64",
        "working_directory": str(config.base_dir),
        "ephemeral_storage_path": str(config.uploads_dir),
        "database_connected": config.experiments_db_path.exists()
    }
