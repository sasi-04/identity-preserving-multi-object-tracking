"""
ZED VISION - Benchmarking & Dataset Evaluation API Endpoints
"""

from fastapi import APIRouter
from backend.app.evaluation.benchmark_runner import run_full_ablation_study

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.post("/run-ablation")
def run_ablation():
    """
    Run complete 5-configuration ablation study:
    1. Baseline (Motion-Only)
    2. Baseline + ReID (Appearance)
    3. OIE (Uncertainty & Adaptive Gating)
    4. OIE (w/ Temporal Memory Gallery)
    5. Full OIE Engine
    """
    results = run_full_ablation_study()
    return {"status": "SUCCESS", "results": results}


@router.get("/dataset-info")
def get_dataset_info():
    """Return documentation on supported MOT benchmark datasets and local synthetic generator."""
    return {
        "supported_benchmarks": [
            {
                "name": "MOT17 (Multiple Object Tracking Benchmark 2017)",
                "description": "Pedestrian tracking in indoor and outdoor public environments with high crowd density and camera motion.",
                "url": "https://motchallenge.net/data/MOT17/",
                "annotations_format": "CSV: [frame, id, bb_left, bb_top, bb_width, bb_height, conf, x, y, z]",
                "licensing": "Non-commercial research use only"
            },
            {
                "name": "MOT20 (Crowded Scenes Challenge)",
                "description": "Extremely dense pedestrian scenarios (transit hubs, busy shopping streets) specifically evaluating tracking under extreme mutual occlusion.",
                "url": "https://motchallenge.net/data/MOT20/",
                "annotations_format": "CSV standard MOT challenge format",
                "licensing": "Research use only"
            },
            {
                "name": "ZED Synthetic Transit Gate Benchmark",
                "description": "Deterministic local procedural generator producing dense pedestrian crossings, architectural gate turnstiles, and structured foreground occlusion pillars.",
                "availability": "Ready - Built-in zero-dependency generator",
                "metrics_supported": ["IDF1", "IDSW", "MOTA", "HOTA", "DetA", "AssA", "FPS", "Latency"]
            }
        ],
        "metrics_explanation": {
            "IDF1": "Measures continuous identity preservation through dense occlusions (harmonic mean of IDP and IDR).",
            "IDSW": "Counts the raw number of identity switches where a person is erroneously re-labeled with another track.",
            "MOTA": "Multiple Object Tracking Accuracy combining False Positives, False Negatives, and ID Switches.",
            "HOTA": "Balanced Higher Order Tracking Accuracy geometrically averaging Detection and Association Accuracy."
        }
    }
