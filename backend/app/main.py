"""
ZED VISION - FastAPI Master Server
Identity-Preserving Multi-Object Tracking Through Dense Occlusion (PS-2)
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes_evaluations import router as eval_router
from backend.app.api.routes_experiments import router as exp_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_tracking import router as tracking_router
from backend.app.api.routes_videos import router as video_router
from backend.app.core.config import config
from backend.app.services.session_manager import SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure sample demo videos are created on startup
    sm = SessionManager()
    sm._ensure_sample_demo_video()
    yield


app = FastAPI(
    title="ZED VISION - Occlusion Intelligence & MOT Engine",
    description="Identity-Preserving Multi-Object Tracking Through Dense Occlusion (PS-2)",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) for Vite/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routers
app.include_router(health_router)
app.include_router(video_router)
app.include_router(tracking_router)
app.include_router(exp_router)
app.include_router(eval_router)


@app.get("/manual.pdf", tags=["Documentation"])
@app.get("/api/manual", tags=["Documentation"])
async def get_user_manual_pdf():
    manual_path = config.base_dir / "docs" / "ZED_VISION_User_Manual.pdf"
    if manual_path.exists():
        return FileResponse(
            str(manual_path),
            media_type="application/pdf",
            filename="ZED_VISION_User_Manual.pdf"
        )
    return JSONResponse(status_code=404, content={"error": "User manual PDF not found"})


@app.get("/presentation.pdf", tags=["Documentation"])
@app.get("/api/presentation", tags=["Documentation"])
async def get_presentation_pdf():
    pres_path = config.base_dir / "docs" / "ZED_VISION_10Min_HR_Presentation.pdf"
    if pres_path.exists():
        return FileResponse(
            str(pres_path),
            media_type="application/pdf",
            filename="ZED_VISION_10Min_HR_Presentation.pdf"
        )
    return JSONResponse(status_code=404, content={"error": "Presentation PDF not found"})



# Mount frontend production build if present
frontend_dist = config.base_dir / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_root():
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"error": "Frontend build not found"})

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return JSONResponse(status_code=404, content={"error": "Not Found"})
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"error": "Frontend build not found"})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "detail": str(exc), "path": str(request.url.path)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8080, reload=True)
