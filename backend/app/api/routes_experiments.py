"""
ZED VISION - Experiment Management API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.app.core.config import TrackerConfig
from backend.app.evaluation.benchmark_runner import generate_benchmark_scenario, run_single_benchmark
from backend.app.services.experiment_store import ExperimentStore

router = APIRouter(prefix="/api/experiments", tags=["experiments"])
store = ExperimentStore()


class RunExperimentRequest(BaseModel):
    name: str
    video_name: str = "Dense Transit Concourse (Benchmark)"
    num_people: int = 12
    num_frames: int = 100
    occlusion_duration: int = 18
    config: Optional[TrackerConfig] = None


@router.get("")
def list_experiments():
    return store.list_experiments()


@router.post("/run")
def run_experiment(req: RunExperimentRequest):
    """Execute a quantitative MOT tracking run and record full metrics to SQLite."""
    cfg = req.config or TrackerConfig()
    exp_id = f"EXP_{req.name.replace(' ', '_')}_{cfg.enable_oie}"

    gt_frames, det_frames = generate_benchmark_scenario(
        num_people=req.num_people,
        num_frames=req.num_frames,
        occlusion_duration=req.occlusion_duration,
        seed=42
    )

    metrics = run_single_benchmark(cfg, gt_frames, det_frames)
    metrics_dict = metrics.to_dict()

    store.save_experiment(
        exp_id=exp_id,
        name=req.name,
        video_name=req.video_name,
        is_oie=cfg.enable_oie,
        config_dict=cfg.dict(),
        metrics_dict=metrics_dict
    )

    return {
        "id": exp_id,
        "name": req.name,
        "is_oie": cfg.enable_oie,
        "metrics": metrics_dict,
        "status": "COMPLETED"
    }


@router.get("/{exp_id}")
def get_experiment(exp_id: str):
    exp = store.get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.get("/{exp_id}/export")
def export_experiment(exp_id: str):
    exp = store.get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return JSONResponse(
        content=exp,
        headers={"Content-Disposition": f"attachment; filename=zed_experiment_{exp_id}.json"}
    )
