"""
ZED VISION - Video Upload and Sample Management API Endpoints
"""

from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.core.config import config
from backend.app.tracking.video_pipeline import VideoPipeline

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("")
def list_videos():
    """List available sample videos and uploaded videos."""
    samples = []
    for p in (config.data_dir / "samples").glob("*.mp4"):
        samples.append({
            "name": p.name,
            "type": "sample",
            "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
            "path": str(p)
        })

    uploads = []
    for p in config.uploads_dir.glob("*.mp4"):
        uploads.append({
            "name": p.name,
            "type": "upload",
            "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
            "path": str(p)
        })

    return {"samples": samples, "uploads": uploads}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Validate and save uploaded video file to ephemeral uploads directory.
    Enforces format constraints and prevents path traversal.
    """
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(status_code=400, detail="Unsupported video format. Please upload MP4, AVI, or MOV.")

    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    save_path = config.uploads_dir / safe_name

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Video uploaded successfully",
        "filename": safe_name,
        "path": str(save_path),
        "size_mb": round(save_path.stat().st_size / (1024 * 1024), 2)
    }


@router.post("/generate-demo")
def generate_demo():
    """Generate a high-density synthetic transit gate scenario video."""
    target_path = config.data_dir / "samples" / "transit_gate_demo.mp4"
    VideoPipeline.create_synthetic_demo_video(target_path, num_frames=150, fps=30)
    return {
        "message": "Demo transit video generated successfully",
        "path": str(target_path),
        "filename": target_path.name
    }


@router.delete("/{filename}")
def delete_video(filename: str):
    """
    Securely delete an uploaded video file.
    Prevents path traversal and protects primary sample fixtures.
    """
    import gc
    import time
    from backend.app.api.routes_tracking import session_manager

    safe_name = Path(filename).name
    target_upload = config.uploads_dir / safe_name
    target_sample = config.data_dir / "samples" / safe_name

    target = None
    if target_upload.exists() and target_upload.is_file():
        target = target_upload
    elif target_sample.exists() and target_sample.is_file() and safe_name != "transit_gate_demo.mp4":
        target = target_sample
    else:
        raise HTTPException(status_code=404, detail="Video file not found or protected")

    # Release any active sessions holding this file
    for sid in list(session_manager.sessions.keys()):
        sess = session_manager.get_session(sid)
        if sess and (sess.video_path.name == safe_name or str(sess.video_path) == str(target)):
            session_manager.stop_session(sid)

    gc.collect()

    # Retry unlink briefly on Windows in case of OS handle release lag
    for attempt in range(5):
        try:
            target.unlink()
            break
        except PermissionError:
            time.sleep(0.15)
            gc.collect()
            if attempt == 4:
                raise

    return {"message": f"Video {safe_name} deleted successfully", "filename": safe_name}

