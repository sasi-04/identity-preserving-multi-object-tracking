"""
ZED VISION - Benchmark Runner & Ablation Suite
Executes reproducible evaluations comparing Baseline vs OIE across increasing crowd density and occlusion.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np

from backend.app.core.config import TrackerConfig
from backend.app.detection.detector import PersonDetection, SpatialColorAppearanceExtractor
from backend.app.evaluation.metrics import MOTEvaluator, MOTMetricsResult
from backend.app.tracking.tracker import MultiObjectTracker


def generate_benchmark_scenario(
    num_people: int = 12,
    num_frames: int = 100,
    occlusion_duration: int = 15,
    seed: int = 42
) -> Tuple[Dict[int, List[Tuple[int, np.ndarray]]], Dict[int, List[PersonDetection]]]:
    """
    Generate ground truth annotations and realistic synthetic detections for reproducible MOT benchmarking.
    Returns:
        gt_frames: {frame_idx: [(gt_id, bbox), ...]}
        det_frames: {frame_idx: [PersonDetection, ...]}
    """
    rng = np.random.RandomState(seed)
    appearance_extractor = SpatialColorAppearanceExtractor()

    # Create synthetic mock frame for appearance generation
    dummy_frame = np.full((720, 1280, 3), 40, dtype=np.uint8)

    pedestrians = []
    for i in range(num_people):
        # Position and velocity simulating crossing paths at a gate
        x_init = rng.uniform(150, 1100)
        y_init = rng.uniform(200, 520)
        vx = rng.choice([-3.2, -2.0, 2.0, 3.2]) + rng.normal(0, 0.15)
        vy = rng.uniform(-0.3, 0.3)
        h = rng.uniform(140, 190)
        w = h * rng.uniform(0.40, 0.46)
        color = (int(rng.randint(50, 230)), int(rng.randint(50, 230)), int(rng.randint(50, 230)))

        # Temporary disappearance behind gate pillar (occlusion stress)
        disappear_start = int(rng.randint(25, 60)) if (i % 2 == 0) else -1

        pedestrians.append({
            "id": i + 1,
            "x": x_init,
            "y": y_init,
            "vx": vx,
            "vy": vy,
            "w": w,
            "h": h,
            "color": color,
            "disappear_start": disappear_start,
            "disappear_duration": occlusion_duration
        })

    gt_frames: Dict[int, List[Tuple[int, np.ndarray]]] = {}
    det_frames: Dict[int, List[PersonDetection]] = {}

    for f in range(num_frames):
        gt_list = []
        det_list = []
        raw_dets = []

        for p in pedestrians:
            cx = p["x"] + p["vx"] * f
            cy = p["y"] + p["vy"] * f
            # Boundary wrap
            cx = cx % 1000 + 100
            cy = np.clip(cy, 150, 550)

            x1 = cx - p["w"] / 2.0
            y1 = cy - p["h"] / 2.0
            x2 = cx + p["w"] / 2.0
            y2 = cy + p["h"] / 2.0
            bbox = np.array([x1, y1, x2, y2], dtype=np.float32)

            # Ground truth records real physical presence
            gt_list.append((p["id"], bbox))

            # Check if occluded/disappeared in video detector view
            if p["disappear_start"] != -1:
                if p["disappear_start"] <= f < (p["disappear_start"] + p["disappear_duration"]):
                    continue  # Detection missing during mutual occlusion!

            # Add slight sensor noise to bounding box
            noise_x = rng.normal(0, 1.2)
            noise_y = rng.normal(0, 1.2)
            det_bbox = np.array([x1 + noise_x, y1 + noise_y, x2 + noise_x, y2 + noise_y], dtype=np.float32)

            conf = float(np.clip(0.88 + rng.normal(0, 0.04), 0.55, 0.98))
            raw_dets.append((p["id"], det_bbox, conf, p["color"]))

        # Mutual overlap calculation
        n = len(raw_dets)
        overlaps = np.zeros(n, dtype=np.float32)
        for i in range(n):
            for j in range(i + 1, n):
                bi = raw_dets[i][1]
                bj = raw_dets[j][1]
                ix1, iy1 = max(bi[0], bj[0]), max(bi[1], bj[1])
                ix2, iy2 = min(bi[2], bj[2]), min(bi[3], bj[3])
                iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
                inter = iw * ih
                if inter > 0:
                    ai = (bi[2] - bi[0]) * (bi[3] - bi[1])
                    aj = (bj[2] - bj[0]) * (bj[3] - bj[1])
                    iou = inter / (ai + aj - inter)
                    overlaps[i] = max(overlaps[i], iou)
                    overlaps[j] = max(overlaps[j], iou)

        for i, (pid, dbox, conf, col) in enumerate(raw_dets):
            # Render color patch on dummy frame to generate real appearance embedding
            cv2.rectangle(
                dummy_frame,
                (max(0, int(dbox[0])), max(0, int(dbox[1]))),
                (min(1280, int(dbox[2])), min(720, int(dbox[3]))),
                col, -1
            )
            emb, qual = appearance_extractor.extract(dummy_frame, dbox)
            det_list.append(PersonDetection(
                bbox=dbox,
                confidence=conf,
                class_id=0,
                crop_quality=qual,
                overlap_index=float(overlaps[i]),
                embedding=emb
            ))

        gt_frames[f] = gt_list
        det_frames[f] = det_list

    return gt_frames, det_frames


def run_single_benchmark(
    config: TrackerConfig,
    gt_frames: Dict[int, List[Tuple[int, np.ndarray]]],
    det_frames: Dict[int, List[PersonDetection]]
) -> MOTMetricsResult:
    """Run tracking evaluation for a specific configuration on ground truth sequence."""
    tracker = MultiObjectTracker(config)
    evaluator = MOTEvaluator(iou_threshold=0.5)

    pred_frames: Dict[int, List[Tuple[int, np.ndarray]]] = {}
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    num_frames = len(det_frames)
    for f in range(num_frames):
        dets = det_frames[f]
        out = tracker.update(dummy_frame, f, detections=dets)

        # Collect active confirmed and recovered tracks for evaluation
        active_preds = []
        for trk_dict in out["tracks"]:
            active_preds.append((trk_dict["track_id"], np.array(trk_dict["bbox"], dtype=np.float32)))
        pred_frames[f] = active_preds

    avg_fps = float(np.mean([1000.0 / max(0.1, lat) for lat in tracker.frame_latencies])) if tracker.frame_latencies else 30.0
    avg_latency = float(np.mean(tracker.frame_latencies)) if tracker.frame_latencies else 33.3

    return evaluator.evaluate(
        gt_frames, pred_frames,
        measured_fps=avg_fps,
        measured_latency_ms=avg_latency
    )


def run_full_ablation_study() -> Dict[str, dict]:
    """
    Run complete 5-configuration ablation study under dense transit crowd occlusion.
    """
    gt_frames, det_frames = generate_benchmark_scenario(
        num_people=12,
        num_frames=100,
        occlusion_duration=18,
        seed=42
    )

    experiments = {
        "EXP-01_Baseline_MotionOnly": TrackerConfig(
            enable_oie=False,
            weight_motion=0.5,
            weight_appearance=0.0,
            weight_geometry=0.5
        ),
        "EXP-02_Baseline_With_ReID": TrackerConfig(
            enable_oie=False,
            weight_motion=0.3,
            weight_appearance=0.4,
            weight_geometry=0.3
        ),
        "EXP-03_OIE_Adaptive_No_Memory": TrackerConfig(
            enable_oie=True,
            enable_uncertainty_recovery=True,
            enable_adaptive_weights=True,
            enable_temporal_memory=False,
            enable_ambiguity_rejection=False
        ),
        "EXP-04_OIE_With_Memory": TrackerConfig(
            enable_oie=True,
            enable_uncertainty_recovery=True,
            enable_adaptive_weights=True,
            enable_temporal_memory=True,
            enable_ambiguity_rejection=False
        ),
        "EXP-05_Full_OIE_Engine": TrackerConfig(
            enable_oie=True,
            enable_uncertainty_recovery=True,
            enable_adaptive_weights=True,
            enable_temporal_memory=True,
            enable_ambiguity_rejection=True,
            ambiguity_margin_threshold=0.12
        ),
    }

    results = {}
    for exp_id, cfg in experiments.items():
        res = run_single_benchmark(cfg, gt_frames, det_frames)
        results[exp_id] = res.to_dict()

    return results


if __name__ == "__main__":
    from backend.app.services.experiment_store import ExperimentStore
    import uuid
    store = ExperimentStore()
    matrix = run_full_ablation_study()
    print("=== MOT Ablation Benchmark Matrix ===")
    print(f"{'Config':<32} | {'IDF1 (%)':<8} | {'IDSW':<5} | {'MOTA (%)':<8} | {'HOTA (%)':<8} | {'FPS':<6}")
    print("-" * 80)
    for name, r in matrix.items():
        print(f"{name:<32} | {r['idf1']:<8.2f} | {r['idsw']:<5} | {r['mota']:<8.2f} | {r['hota']:<8.2f} | {r['fps']:<6.1f}")
        is_oie = "OIE" in name
        store.save_experiment(
            exp_id=str(uuid.uuid4())[:8],
            name=name,
            video_name="Transit Gate Concourse Benchmark",
            is_oie=is_oie,
            config_dict={"name": name, "is_oie": is_oie},
            metrics_dict=r,
            status="COMPLETED"
        )
    print("All 5 ablation configurations persisted to experiments.db!")

