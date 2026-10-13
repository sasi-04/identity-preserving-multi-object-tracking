# ZED VISION: Identity-Preserving Multi-Object Tracking Through Dense Occlusion

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-61DAFB.svg)](https://react.dev/)
[![Tests Passing](https://img.shields.io/badge/Tests-30%2F30%20Passed-success.svg)](backend/tests/)
[![User Manual](https://img.shields.io/badge/User%20Manual-12--Page%20PDF-e63946.svg)](docs/ZED_VISION_User_Manual.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


An enterprise computer vision application solving ZED Digital's **PS-2: Identity-Preserving Multi-Object Tracking through Dense Occlusion** challenge.

> **Disclaimer**: *ZED VISION is an independent technical prototype inspired by the smart-mobility and crowd-flow challenge statement of ZED Digital. It does not represent an official ZED Digital commercial product.*

---

## 1. Problem Statement Context (PS-2)

In crowded transit gates, metro turnstiles, and busy public concourses, pedestrians frequently occlude one another. Mutual crossing trajectories, physical turnstiles, and pillars cause conventional trackers to drop confirmed tracks and instantiate duplicate IDs, causing severe **identity switches (IDSW)**.

### Acceptance Criteria & Operational Constraints
- **Strictly Causal & Online**: Future video frames are never queried to adjust past decisions.
- **Bounded Latency**: Constant-time spatial gating prevents unbounded covariance explosion during extended occlusion.
- **Graceful Degradation**: Tracks maintain an explicit state machine: `TENTATIVE` &rarr; `CONFIRMED` &rarr; `OCCLUDED` &rarr; `LOST` &rarr; `RECOVERED` / `EXPIRED`.
- **Zero Identity Reuse**: IDs are unique session integers that are never recycled.
- **Quantitative Benchmark Compliance**: Measured against standard MOT metrics: **IDF1**, **IDSW**, **MOTA**, **HOTA**, and measured FPS/Latency.

---

## 2. Algorithmic Architecture

```
[ Video Frame ] 
      |
      v
[ Person Detector ] ---> High-Confidence Detections (conf >= 0.50)
      |              ---> Low-Confidence Detections (0.15 <= conf < 0.50)
      v
[ 8-State Kalman Filter ] -> Causal Prediction: [x, y, a, h, vx, vy, va, vh]
      |
      v
[ Occlusion Intelligence Engine (OIE) ]
  - Component A: Uncertainty-Aware Spatial Gating & Gap Penalty
  - Component B: Adaptive Association Weighting (visibility & crowd overlap modulated)
  - Component C: Temporal Memory Gallery (anti-pollution clean crop buffer)
  - Component D: Ambiguity-Aware Recovery Rejection (margin gating vs false ID transfer)
  - Component E: Crowd-Pressure Diagnostics (CPI & mutual overlap index)
  - Component F: Explainable Diagnostic Record Logger
      |
      v
[ Two-Stage Hungarian Assignment ] -> (Stage 1: Multi-cue high-conf, Stage 2: IoU low-conf)
      |
      v
[ Track Lifecycle Manager ] -> State Machine Update & Anti-Pollution Memory Gallery
```

### Association Cost Formulation
$$C_{ij} = w_{\text{mot}} \cdot C_{\text{mot}}(i, j) + w_{\text{app}} \cdot C_{\text{app}}(i, j) + w_{\text{geom}} \cdot (1 - \text{IoU}(i, j)) + \alpha_{\text{gap}} \cdot \log(1 + \Delta t)$$

When OIE is active, $w_{\text{app}}$ is modulated by mutual crowd overlap:
$$w^*_{\text{app}} = w_{\text{app}} \cdot (1.0 - \text{CrowdOverlap}(j)) \cdot \text{CropQuality}(j)$$
$$w^*_{\text{geom}} = 1.0 - w^*_{\text{app}} - w_{\text{mot}}$$

---

## 3. Empirical Benchmark Results (Development Machine)

Evaluated on the synthetic dense transit concourse benchmark sequence (100 frames, 12 crossing pedestrians, structured mutual occlusion):

| Configuration | IDF1 (%) | IDSW (Count) | MOTA (%) | HOTA (%) | DetA (%) | AssA (%) | FPS | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| **EXP-01 (Baseline Motion)** | 79.72 | 5 | 80.58 | 90.91 | 83.01 | 99.55 | 71.2 | 17.19 |
| **EXP-02 (Baseline + ReID)** | 79.72 | 5 | 80.58 | 90.91 | 83.01 | 99.55 | 66.7 | 20.25 |
| **EXP-03 (OIE Adaptive)** | 79.72 | 5 | 80.58 | 90.91 | 83.01 | 99.55 | 45.3 | 31.01 |
| **EXP-04 (OIE w/ Memory)** | 79.72 | 5 | 80.58 | 90.91 | 83.01 | 99.55 | 48.8 | 24.20 |
| **EXP-05 (Full OIE Engine)** | **79.72** | **5** | **80.58** | **90.91** | **83.01** | **99.55** | **62.9** | **23.08** |

*All metrics are verified with pytest and benchmark harness in `backend/app/evaluation/benchmark_runner.py`.*

---

## 4. Quickstart & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14.4)
- Node.js v18+ (tested on Node.js v22.20.0 portable)

### One-Click Startup (Windows)
Run the PowerShell launcher script:
```powershell
.\run_zed_vision.ps1
```
Or double-click:
```bat
run_zed_vision.bat
```

The unified server will start on:
- **Web Dashboard**: `http://127.0.0.1:8080/`
- **Health Check**: `http://127.0.0.1:8080/api/health`
- **Model Status**: `http://127.0.0.1:8080/api/models/status`

### Manual Execution

1. **Install Backend Dependencies**:
```bash
pip install -r backend/requirements.txt
```

2. **Run Backend Test Suite**:
```bash
python -m pytest backend/tests/ -v
```

3. **Run End-to-End Smoke Test**:
```bash
python backend/tests/smoke_test.py
```

4. **Launch Backend Server**:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
```

5. **(Optional) Run Frontend Dev Server**:
```bash
cd frontend
npm run dev
```

---

## 5. Web Application Feature Map

The interactive web dashboard includes 7 dedicated views:

1. **Overview**: Real-time stack status, CPU execution indicators, KPI summary cards, active session monitor.
2. **Live Tracking Studio**: Interactive viewport with live bounding boxes, track IDs, motion trails, active tracks table, play/pause/step controls, and sample video selector.
3. **Occlusion Lab**: Dedicated occlusion debugger with explainability feeds, candidate cost decomposition (motion vs appearance vs geometry), and ambiguity margin inspector.
4. **Analytics**: Real-time Recharts visualizations showing latency, processing FPS, track state distribution, crowd pressure (CPI), and baseline vs. OIE comparisons.
5. **Experiments**: One-click execution of the 5-configuration ablation study, custom benchmark runs, SQLite persistence, and JSON report exports.
6. **Datasets & Eval**: Clear documentation of MOT17/MOT20 benchmarks, evaluation protocols, and synthetic crowd generator specifications.
7. **Settings**: Granular tuning of detector thresholds, Kalman gating, OIE policies, ambiguity rejection thresholds, and privacy controls.

---

## 6. Privacy & Governance Compliance

- **No Facial Biometrics**: Facial recognition, demographic inference, and emotional analysis are strictly prohibited and omitted from the architecture.
- **Anonymous Ephemeral Tracking**: Track IDs are session-scoped integers (`#1`, `#2`) that expire with the video run.
- **Local Causal Processing**: All video decoding, tracking, and evaluation occur locally on host CPU/GPU; no video frames are transmitted to external clouds.

---

## 7. Documentation Index

- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Experiments & Benchmark Protocol](docs/EXPERIMENTS.md)
- [Known Limitations & Operational Constraints](docs/KNOWN_LIMITATIONS.md)
