@echo off
title ZED VISION - Occlusion Intelligence MOT Engine
echo =====================================================
echo   ZED VISION: Occlusion Intelligence MOT Engine
echo   PS-2: Dense Occlusion Multi-Object Tracking
echo =====================================================
echo.
echo Starting ZED VISION Unified Web Server on http://127.0.0.1:8080 ...
echo.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
pause
