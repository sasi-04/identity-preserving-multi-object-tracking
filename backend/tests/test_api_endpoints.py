"""Integration tests for FastAPI endpoints."""
from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "ZED VISION"


def test_model_status_endpoint():
    response = client.get("/api/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "detector" in data
    assert "reid_appearance" in data
    assert "motion_model" in data
    assert "oie_engine" in data
    assert data["detector"]["status"] == "operational"


def test_videos_list():
    response = client.get("/api/videos")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert "uploads" in data


def test_dataset_info_endpoint():
    response = client.get("/api/evaluations/dataset-info")
    assert response.status_code == 200
    data = response.json()
    assert "supported_benchmarks" in data
    assert "metrics_explanation" in data


def test_tracking_session_lifecycle():
    # 1. Create session with synthetic detector
    create_resp = client.post("/api/tracking-sessions", json={"detector_type": "synthetic"})
    assert create_resp.status_code == 200
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_id

    # 2. Step 1 frame
    step_resp = client.post(f"/api/tracking-sessions/{session_id}/step")
    assert step_resp.status_code == 200
    step_data = step_resp.json()
    assert "frame_idx" in step_data
    assert "image" in step_data
    assert "telemetry" in step_data

    # 3. Get session events
    events_resp = client.get(f"/api/tracking-sessions/{session_id}/events")
    assert events_resp.status_code == 200

    # 4. Pause and resume
    pause_resp = client.post(f"/api/tracking-sessions/{session_id}/pause")
    assert pause_resp.status_code == 200
    resume_resp = client.post(f"/api/tracking-sessions/{session_id}/resume")
    assert resume_resp.status_code == 200

    # 5. Stop session
    stop_resp = client.post(f"/api/tracking-sessions/{session_id}/stop")
    assert stop_resp.status_code == 200


def test_opencv_tracking_session():
    """Verify session creation and stepping with default OpenCV detector."""
    create_resp = client.post("/api/tracking-sessions", json={"detector_type": "opencv"})
    assert create_resp.status_code == 200
    sid = create_resp.json()["session_id"]
    assert sid

    step_resp = client.post(f"/api/tracking-sessions/{sid}/step")
    assert step_resp.status_code == 200
    data = step_resp.json()
    assert data["frame_idx"] == 1
    assert "telemetry" in data


def test_video_delete_flow():
    """Verify video upload, deletion, and protection of core fixtures."""
    from backend.app.core.config import config
    from pathlib import Path

    # Create temporary dummy file in uploads
    dummy_path = config.uploads_dir / "test_api_del.mp4"
    dummy_path.write_bytes(b"dummy_test_video_content")

    # 1. Verify it appears in uploads
    list_resp = client.get("/api/videos")
    assert list_resp.status_code == 200
    uploads = [v["name"] for v in list_resp.json()["uploads"]]
    assert "test_api_del.mp4" in uploads

    # 2. Delete it
    del_resp = client.delete("/api/videos/test_api_del.mp4")
    assert del_resp.status_code == 200
    assert not dummy_path.exists()

    # 3. Verify core sample fixture cannot be deleted
    del_protect_resp = client.delete("/api/videos/transit_gate_demo.mp4")
    assert del_protect_resp.status_code == 404


def test_experiments_list_endpoint():
    """Verify experiment database query endpoint."""
    resp = client.get("/api/experiments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

