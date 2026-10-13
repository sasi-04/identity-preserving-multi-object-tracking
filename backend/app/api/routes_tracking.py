"""
ZED VISION - Live Tracking Session and WebSocket Streaming Endpoints
"""

import asyncio
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.core.config import TrackerConfig, config
from backend.app.services.session_manager import SessionManager, TrackingSession

router = APIRouter(prefix="/api/tracking-sessions", tags=["tracking"])
session_manager = SessionManager()


class CreateSessionRequest(BaseModel):
    video_path: Optional[str] = None
    detector_type: str = "opencv"  # "opencv" or "synthetic"
    config: Optional[TrackerConfig] = None


@router.post("")
def create_session(req: CreateSessionRequest):
    """Initialize a new tracking session."""
    v_path = Path(req.video_path) if req.video_path else None
    session = session_manager.create_session(
        video_path=v_path,
        tracker_config=req.config,
        detector_type=req.detector_type
    )
    return {
        "session_id": session.session_id,
        "video_name": session.video_path.name,
        "total_frames": session.total_frames,
        "fps": session.video_fps,
        "is_oie": session.config.enable_oie
    }


@router.get("")
def list_sessions():
    """List recent tracking sessions."""
    return session_manager.store.list_sessions()


@router.get("/{session_id}")
def get_session(session_id: str):
    """Retrieve session state and telemetry."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "current_frame": session.current_frame_idx,
        "total_frames": session.total_frames,
        "is_running": session.is_running,
        "is_paused": session.is_paused,
        "is_finished": session.is_finished,
        "telemetry": session.last_telemetry
    }


@router.post("/{session_id}/step")
def step_frame(
    session_id: str,
    draw_bboxes: bool = True,
    draw_ids: bool = True,
    draw_trails: bool = True
):
    """Advance processing by exactly one frame causally."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = session.step(draw_bboxes=draw_bboxes, draw_ids=draw_ids, draw_trails=draw_trails)
    if not result:
        return {"session_id": session_id, "is_finished": True, "message": "End of video reached"}
    return result


@router.post("/{session_id}/start")
def start_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_running = True
    session.is_paused = False
    return {"session_id": session_id, "status": "running"}


@router.post("/{session_id}/pause")
def pause_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_paused = True
    return {"session_id": session_id, "status": "paused"}


@router.post("/{session_id}/resume")
def resume_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_paused = False
    return {"session_id": session_id, "status": "running"}


@router.post("/{session_id}/reset")
def reset_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.reset()
    return {"session_id": session_id, "status": "reset", "current_frame": 0}


@router.post("/{session_id}/stop")
def stop_session(session_id: str):
    success = session_manager.stop_session(session_id)
    return {"session_id": session_id, "status": "stopped" if success else "already_stopped"}


@router.get("/{session_id}/events")
def get_session_events(session_id: str):
    """Retrieve Occlusion Lab explainable diagnostic records."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "events": session.diagnostic_events}


@router.get("/{session_id}/metrics")
def get_session_metrics(session_id: str):
    """Retrieve session performance metrics."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    latencies = session.tracker.frame_latencies
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    avg_fps = 1000.0 / avg_latency if avg_latency > 0 else 0.0

    return {
        "session_id": session_id,
        "processed_frames": session.current_frame_idx,
        "total_frames": session.total_frames,
        "avg_fps": round(avg_fps, 1),
        "avg_latency_ms": round(avg_latency, 2),
        "total_detections": session.tracker.total_detections_count,
        "total_recoveries": session.tracker.total_recoveries_count,
        "active_tracks": len([t for t in session.tracker.tracks if t.state.value != "EXPIRED"])
    }


@router.websocket("/{session_id}/ws")
async def websocket_tracking_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket live streaming endpoint.
    Transmits annotated frame JPEG data and real-time telemetry at requested FPS.
    """
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    session.is_running = True

    try:
        while True:
            # Check client commands or keep streaming
            if session.is_paused:
                await asyncio.sleep(0.1)
                continue

            if session.is_finished:
                await websocket.send_json({"type": "FINISHED", "session_id": session_id})
                break

            result = session.step(draw_bboxes=True, draw_ids=True, draw_trails=True)
            if result is None:
                await websocket.send_json({"type": "FINISHED", "session_id": session_id})
                break

            payload = {
                "type": "FRAME",
                "session_id": session_id,
                "frame_idx": result["frame_idx"],
                "total_frames": result["total_frames"],
                "image": result["image"],
                "telemetry": result["telemetry"]
            }
            await websocket.send_json(payload)

            # Throttle to simulate real-time playback (e.g. 30 fps = 33ms)
            await asyncio.sleep(0.033)

    except WebSocketDisconnect:
        session.is_running = False
    except Exception as e:
        session.is_running = False
