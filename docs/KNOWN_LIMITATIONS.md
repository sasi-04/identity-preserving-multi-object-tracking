# ZED VISION: Known Limitations & Operational Constraints

### 1. Hardware & Platform Boundaries
- **CPU Execution Mode by Default**: Designed and optimized for zero-GPU CPU execution using lightweight ONNX Runtime / OpenCV DNN inference. When running heavy batch models on CPU, processing latency scales with frame resolution and pedestrian count.
- **Python 3.14 Compatibility**: Standard PyTorch binary wheels do not yet offer precompiled official binaries for Python 3.14 on Windows; hence, inference relies on ONNX Runtime, OpenCV DNN, and NumPy/SciPy acceleration.
- **Edge Acceleration (Jetson/TensorRT)**: TensorRT and NVIDIA DeepStream bindings are architecturally decoupled and require specific hardware runtime dependencies not present in standard host developer machines.

---

### 2. Algorithmic Assumptions & Boundary Conditions
- **Online & Causal Constraint**: The tracking engine strictly adheres to causal processing. Future frames are never queried to correct past tracks. Consequently, offline smoothing techniques (e.g., Rauch-Tung-Striebel / bidirectional Kalman smoothing) are intentionally omitted.
- **Extreme Disappearance Duration**: When a subject disappears behind a non-transparent architectural pillar or out-of-frame for more than the configured `max_lost_frames` (default: 60 frames / 2 seconds at 30 FPS), the track expires to protect against unbounded memory growth and false identity transfers.
- **Uniform Appearance Clusters**: If multiple people wear identical uniforms (e.g., security personnel or sports teams) and pass in dense overlapping groups where geometric IoU and Kalman predictions are fully coincident, appearance cosine distance cannot provide discriminative power. In such situations, the OIE conservatively marks associations as ambiguous rather than guessing.
- **Monocular Scale Ambiguity**: Without multi-camera stereoscopy or depth sensor fusion (e.g., stereo ZED camera SDK), depth is approximated through bounding box scale and footpoint ground projection.

---

### 3. Privacy & Regulatory Compliance
- **Zero Facial Biometrics**: The system intentionally does not extract facial features, age, gender, or demographic indicators.
- **Non-Persistent Identity**: IDs are purely numeric and scoped strictly to the active video processing session (`#1`, `#2`, ...). Once a session is reset or expired, all track logs and temporary video frames are permanently expunged.
- **No Cross-Camera Stitching**: The prototype is strictly a single-view, gate-level crowd analysis system.
