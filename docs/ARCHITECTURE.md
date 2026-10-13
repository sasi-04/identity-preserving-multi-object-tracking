# ZED VISION: System Architecture
## Identity-Preserving Multi-Object Tracking Through Dense Occlusion (PS-2)

### 1. High-Level Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                                  USER / CLIENT                                    |
|              (React 19 + TypeScript + Vite + Tailwind CSS + Lucide + Recharts)    |
+-----------------------------------------------------------------------------------+
          |                                                       ^
     HTTP REST API                                          WebSocket Streaming
(Sessions, Config, Uploads)                             (Frames, Telemetry, Events)
          v                                                       |
+-----------------------------------------------------------------------------------+
|                            FASTAPI BACKEND SYSTEM                                 |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | /api/tracking      |   | /api/experiments      |   | /api/evaluations       |  |
|  | /api/videos        |   | /api/models           |   | /api/system            |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                           Video Pipeline & Session                          |  |
|  |            Causal Frame Decoder -> Frame Buffer -> Profile Timer            |  |
|  +-----------------------------------------------------------------------------+  |
|                                     |                                             |
|                                     v                                             |
|  +-----------------------------------------------------------------------------+  |
|  |                     Multi-Object Tracking (MOT) Core Engine                 |  |
|  |                                                                             |  |
|  |  [ Person Detector ]                                                        |  |
|  |  - ONNX / OpenCV DNN (YOLOv8n-person)                                       |  |
|  |  - Non-Maximum Suppression (NMS)                                            |  |
|  |  - Synthetic / Benchmark Generator Fallback                                 |  |
|  |                                                                             |  |
|  |  [ Motion Model: 8-State Kalman Filter ]                                    |  |
|  |  - State: [x, y, a, h, vx, vy, va, vh]                                      |  |
|  |  - Causal Prediction & Bounded Covariance Growth                            |  |
|  |  - Mahalanobis Gating Matrix                                                |  |
|  |                                                                             |  |
|  |  [ Appearance Representation ]                                              |  |
|  |  - Normalized Embedding Vector                                              |  |
|  |  - Cosine Distance Metric                                                   |  |
|  |  - Visibility & Occlusion Quality Weighting                                 |  |
|  |                                                                             |  |
|  |  [ Data Association & Assignment ]                                          |  |
|  |  - Two-Stage Cascaded Matching (High Conf -> Low Conf)                      |  |
|  |  - Hungarian Algorithm (scipy.optimize.linear_sum_assignment)               |  |
|  |  - Cost Matrix: w_mot * C_mot + w_app * C_app + w_geom * C_geom             |  |
|  |                                                                             |  |
|  |  [ Occlusion Intelligence Engine (OIE) ]                                    |  |
|  |  - Component A: Uncertainty-Aware Recovery (Covariance Gating + Gap Penalty)|  |
|  |  - Component B: Adaptive Association Weighting (Visibility-Modulated)       |  |
|  |  - Component C: Temporal Memory Gallery (Anti-Pollution FIFO)               |  |
|  |  - Component D: Ambiguity-Aware Rejection (Margin Gating vs False Transfer) |  |
|  |  - Component E: Crowd-Pressure Diagnostics (Overlap Index + Ambiguity Rate) |  |
|  |  - Component F: Explainable Diagnostic Record Logger                        |  |
|  |                                                                             |  |
|  |  [ Track Lifecycle Management ]                                             |  |
|  |  - States: TENTATIVE -> CONFIRMED -> OCCLUDED -> LOST -> RECOVERED/EXPIRED  |  |
|  |  - Zero In-Session ID Reuse Guarantee                                       |  |
|  +-----------------------------------------------------------------------------+  |
|                                     |                                             |
|                                     v                                             |
|  +-----------------------------------------------------------------------------+  |
|  |                        Evaluation & Persistence Layer                       |  |
|  |  - MOT Metrics: HOTA, MOTA, IDF1, IDSW, Track Frag, FPS, Latency            |  |
|  |  - SQLite Experiment Store (metadata, configs, metrics)                     |  |
|  |  - Privacy Manager: Ephemeral session cleanup, no facial identity storage   |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

### 2. Algorithmic Formulations

#### 2.1 Motion Model (Kalman Filter)
Each track maintains a continuous state vector:
$$\mathbf{x} = [x, y, a, h, v_x, v_y, v_a, v_h]^T$$
where:
- $(x, y)$ is the 2D bounding box center.
- $a = w / h$ is the aspect ratio.
- $h$ is the bounding box height.
- $(v_x, v_y, v_a, v_h)$ are the corresponding velocities.

State transition is purely causal:
$$\mathbf{x}_{k|k-1} = \mathbf{F} \mathbf{x}_{k-1|k-1}$$
$$\mathbf{P}_{k|k-1} = \mathbf{F} \mathbf{P}_{k-1|k-1} \mathbf{F}^T + \mathbf{Q}$$

To prevent covariance explosion during extended occlusion, a bounded uncertainty clamp is enforced:
$$\mathbf{P}_{k|k-1} = \min(\mathbf{P}_{k|k-1}, \mathbf{P}_{\max})$$

#### 2.2 Association Cost Matrix
The cost between track $i$ and detection $j$ combines geometry, motion, and appearance:
$$C_{ij} = w_{\text{mot}} \cdot C_{\text{mot}}(i, j) + w_{\text{app}} \cdot C_{\text{app}}(i, j) + w_{\text{geom}} \cdot (1 - \text{IoU}(i, j))$$

When OIE is enabled, the adaptive weights $w^*_{\text{app}}$ and $w^*_{\text{mot}}$ are modulated by the track's occlusion state and detection quality:
$$w^*_{\text{app}} = w_{\text{app}} \cdot (1 - \text{CrowdOverlap}(j)) \cdot \text{CropQuality}(j)$$
$$w^*_{\text{geom}} = 1.0 - w^*_{\text{app}} - w_{\text{mot}}$$

#### 2.3 OIE Ambiguity-Aware Rejection
Given candidate detections $j_1$ (lowest cost) and $j_2$ (second lowest cost) for a lost track $i$:
$$\Delta C = C_{i, j_2} - C_{i, j_1}$$
If $\Delta C < \tau_{\text{ambiguity}}$, the recovery is flagged as ambiguous. The tracker refuses to assign the identity to prevent identity switches in dense clusters, preserving the original track identity in the `OCCLUDED` state instead.

---

### 3. Track Lifecycle State Machine

```
              [New Detection]
                     |
                     v
             +---------------+
             |   TENTATIVE   |
             +---------------+
               /           \
   (Hits >= N) /             \ (Unmatched in 1-2 frames)
             v               v
     +---------------+  +---------------+
     |   CONFIRMED   |  |    EXPIRED    |
     +---------------+  +---------------+
       |           ^
(Miss) |           | (OIE Re-association)
       v           |
     +---------------+
     |   OCCLUDED    |
     +---------------+
       |           ^
(Time) |           | (Long-gap candidate match)
       v           |
     +---------------+
     |     LOST      |
     +---------------+
             |
   (Frames > MaxAge)
             v
     +---------------+
     |    EXPIRED    |
     +---------------+
```

---

### 4. Privacy, Security & Operational Boundaries
- **Anonymous Tracking Only**: Tracks are labeled strictly with ephemeral session integer IDs (e.g., `#1`, `#2`).
- **No Face Recognition**: Crop features encode coarse body appearance only; no facial landmarking or biometrics are computed or stored.
- **Session Ephemerality**: Video files and rendered debug frames are stored in temporary session directories and pruned upon session reset or timeout.
- **Local Causal Processing**: All models run locally on CPU/available GPU; no video frames are transmitted to external cloud APIs.
