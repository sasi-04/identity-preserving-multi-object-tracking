# ZED VISION: Implementation Plan
## Identity-Preserving Multi-Object Tracking Through Dense Occlusion (PS-2)

### 1. Executive Summary & Objective
ZED VISION is an enterprise-grade technical prototype designed to address ZED Digital's PS-2 challenge: maintaining stable, identity-preserving multi-object tracking (MOT) through dense crowd occlusions, mutual shadowing, and temporary disappearances at transit gates and crowded public venues.

The core deliverable consists of:
1. **Core Tracking Algorithm**: An online, causal MOT engine combining lightweight person detection, Kalman filter motion prediction, appearance feature representation, and multi-stage global data association (Hungarian algorithm).
2. **Occlusion Intelligence Engine (OIE)**: An innovative algorithmic enhancement featuring uncertainty-aware recovery, adaptive association weighting, temporal appearance memory, ambiguity-aware candidate rejection, and crowd-pressure diagnostics.
3. **Evaluation & Benchmarking Engine**: Standard MOT metrics calculation (IDF1, IDSW, MOTA, HOTA, FPS, latency), baseline vs. OIE comparison, and stress testing against variable crowd density and occlusion severity.
4. **FastAPI Backend Services**: Causal frame processing pipeline, video upload management, WebSocket real-time telemetry streaming, SQLite experiment store, and privacy-first ephemeral storage.
5. **Enterprise React/TypeScript Frontend**: Dark charcoal / ZED-inspired red aesthetic, 7 core views (Overview, Live Tracking Studio, Occlusion Lab, Analytics, Experiments, Datasets & Evaluation, Settings).

---

### 2. Implementation Checklist & Phased Roadmap

- [x] **Phase 1: Repository Audit & Foundation**
  - Verify Python 3.14 environment, Node.js v22 portable binary, and installed packages (`fastapi`, `opencv-python`, `onnxruntime`, `numpy`, `scipy`, `scikit-learn`, `pytest`).
  - Establish complete documentation: `IMPLEMENTATION_PLAN.md`, `ARCHITECTURE.md`, `EXPERIMENTS.md`, `KNOWN_LIMITATIONS.md`.

- [x] **Phase 2: Core Computer Vision & Tracking Engine**
  - Implement person detection abstraction (`ONNXPersonDetector`, `OpenCVDNNPersonDetector`, `SyntheticDetector`).
  - Implement 8-state Kalman Filter motion model (`[x, y, a, h, vx, vy, va, vh]`) with causal prediction, bounded covariance growth, and Mahalanobis gating.
  - Implement appearance representation with L2-normalized crop embeddings and cosine similarity.
  - Implement cascaded global data association (Hungarian / `scipy.optimize.linear_sum_assignment`).
  - Implement explicit track lifecycle states (`TENTATIVE`, `CONFIRMED`, `OCCLUDED`, `LOST`, `RECOVERED`, `EXPIRED`).

- [x] **Phase 3: Occlusion Intelligence Engine (OIE)**
  - Component A: Uncertainty-aware recovery with covariance spatial expansion and gap penalty.
  - Component B: Adaptive association weighting based on crop visibility and crowd overlap.
  - Component C: Temporal memory with quality-filtered appearance gallery (anti-corruption).
  - Component D: Ambiguity-aware candidate gating (best vs second-best margin threshold).
  - Component E: Crowd-pressure diagnostic indexing (density, mutual overlap, ambiguity rate).
  - Component F: Explainable event logger recording every recovery/occlusion decision.

- [x] **Phase 4: Backend Integration & APIs**
  - Causal video decoding, frame-by-frame inference, and annotated frame rendering.
  - FastAPI endpoints for sessions, videos, experiments, evaluations, and hardware status.
  - WebSocket telemetry endpoint for real-time live tracking streaming.
  - SQLite persistence for experiments and ablation runs.
  - Privacy and ephemeral data retention policy enforcement.

- [x] **Phase 5: High-Performance Frontend Application**
  - Initialize Vite + React + TypeScript application with custom enterprise dark design system.
  - Build application shell: Compact sidebar, top status bar, ZED dark/red visual identity.
  - Implement View 1: **Overview** (system status, KPIs, recent runs).
  - Implement View 2: **Live Tracking Studio** (video playback, canvas overlays, tracks table, controls).
  - Implement View 3: **Occlusion Lab** (occlusion timeline, recovery inspector, cost breakdown).
  - Implement View 4: **Analytics** (FPS, latency, state distribution, IDSW, crowd pressure).
  - Implement View 5: **Experiments** (run creator, baseline vs OIE comparator, exports).
  - Implement View 6: **Datasets & Evaluation** (MOT benchmark docs, synthetic generator, HOTA/MOTA).
  - Implement View 7: **Settings** (hyperparameter tuning, device selection, privacy options).

- [x] **Phase 6: Evaluation, Stress Testing & Ablation Studies**
  - Implement HOTA, MOTA, IDF1, and IDSW evaluation metrics on ground-truth sequences.
  - Build synthetic dense crowd occlusion test generator for reproducible automated testing.
  - Execute baseline vs. OIE ablation runs and record metrics in `docs/EXPERIMENTS.md`.

- [x] **Phase 7: Verification, Testing & QA**
  - Run backend unit and integration test suite (`pytest`) -> 30/30 passed in 6.05s.
  - Added dedicated detector tests (`test_detector.py`) for YOLOv8n ONNX and NMS filtering.
  - Added video deletion (`DELETE /api/videos/{filename}`) and default video auto-run integration tests.
  - Verify frontend type checking and production build (`npm run build`) -> exit code 0 (1.77s).
  - End-to-end API smoke tests and latency profiling -> 100% verified.

- [x] **Phase 8: Documentation & Engineering Handoff**
  - Complete architectural documentation and operational guides.
  - Document verified benchmark results and known technical limitations.
  - Persistent SQLite experiment metadata across 5 ablation configurations.
