"""
ZED VISION - Official Multi-Object Tracking Evaluation Engine
Calculates IDF1, IDSW, MOTA, and HOTA against ground-truth track sequences.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List, Set, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass
class MOTMetricsResult:
    idf1: float          # ID F1-score (0 - 100%)
    idp: float           # ID Precision (0 - 100%)
    idr: float           # ID Recall (0 - 100%)
    idsw: int            # Identity Switches count
    mota: float          # Multi-Object Tracking Accuracy (-inf to 100%)
    hota: float          # Higher Order Tracking Accuracy (0 - 100%)
    deta: float          # Detection Accuracy
    assa: float          # Association Accuracy
    mostly_tracked: int  # MT: tracked > 80% of lifespan
    mostly_lost: int     # ML: tracked < 20% of lifespan
    total_gt_ids: int
    total_pred_ids: int
    fps: float
    latency_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


class MOTEvaluator:
    """
    Standard MOT metric calculation engine complying with MOTChallenge / CLEAR MOT standards.
    Operates on ground-truth and predicted bounding box sequences.
    """
    def __init__(self, iou_threshold: float = 0.5):
        self.iou_thresh = iou_threshold

    @staticmethod
    def _compute_iou(b1: np.ndarray, b2: np.ndarray) -> float:
        ix1 = max(b1[0], b2[0])
        iy1 = max(b1[1], b2[1])
        ix2 = min(b1[2], b2[2])
        iy2 = min(b1[3], b2[3])
        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        inter = iw * ih
        if inter <= 0:
            return 0.0
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        return float(inter / (a1 + a2 - inter))

    def evaluate(
        self,
        gt_frames: Dict[int, List[Tuple[int, np.ndarray]]],
        pred_frames: Dict[int, List[Tuple[int, np.ndarray]]],
        measured_fps: float = 30.0,
        measured_latency_ms: float = 33.3
    ) -> MOTMetricsResult:
        """
        gt_frames: {frame_idx: [(gt_id, np.array([x1, y1, x2, y2])), ...]}
        pred_frames: {frame_idx: [(pred_id, np.array([x1, y1, x2, y2])), ...]}
        """
        all_frames = sorted(set(gt_frames.keys()).union(pred_frames.keys()))

        total_gt_boxes = 0
        total_fp = 0
        total_fn = 0
        total_tp = 0
        id_switches = 0

        # Mapping for ID switch detection
        last_matched_pred_for_gt: Dict[int, int] = {}
        gt_lifespans: Dict[int, int] = {}
        gt_hits: Dict[int, int] = {}

        # Global matching matrices for IDF1
        all_gt_ids: Set[int] = set()
        all_pred_ids: Set[int] = set()
        overlap_counts: Dict[Tuple[int, int], int] = {}

        for f in all_frames:
            gts = gt_frames.get(f, [])
            preds = pred_frames.get(f, [])

            total_gt_boxes += len(gts)
            for gid, _ in gts:
                all_gt_ids.add(gid)
                gt_lifespans[gid] = gt_lifespans.get(gid, 0) + 1

            for pid, _ in preds:
                all_pred_ids.add(pid)

            if not gts and not preds:
                continue

            if not gts:
                total_fp += len(preds)
                continue

            if not preds:
                total_fn += len(gts)
                continue

            # Build frame IoU distance matrix for bipartite matching
            cost_mat = np.ones((len(gts), len(preds)), dtype=np.float32)
            for i, (_, gbox) in enumerate(gts):
                for j, (_, pbox) in enumerate(preds):
                    iou = self._compute_iou(gbox, pbox)
                    if iou >= self.iou_thresh:
                        cost_mat[i, j] = 1.0 - iou

            row_ind, col_ind = linear_sum_assignment(cost_mat)

            matched_gts = set()
            matched_preds = set()

            for r, c in zip(row_ind, col_ind):
                if cost_mat[r, c] < (1.0 - self.iou_thresh):
                    gid = gts[r][0]
                    pid = preds[c][0]
                    matched_gts.add(r)
                    matched_preds.add(c)
                    total_tp += 1
                    gt_hits[gid] = gt_hits.get(gid, 0) + 1

                    # Count for global IDF1 bipartite alignment
                    overlap_counts[(gid, pid)] = overlap_counts.get((gid, pid), 0) + 1

                    # Detect ID Switches
                    if gid in last_matched_pred_for_gt:
                        if last_matched_pred_for_gt[gid] != pid:
                            id_switches += 1
                    last_matched_pred_for_gt[gid] = pid

            total_fn += (len(gts) - len(matched_gts))
            total_fp += (len(preds) - len(matched_preds))

        # 1. MOTA calculation
        if total_gt_boxes > 0:
            mota = max(-100.0, 100.0 * (1.0 - (total_fn + total_fp + id_switches) / total_gt_boxes))
        else:
            mota = 100.0 if total_fp == 0 else 0.0

        # 2. IDF1 calculation (Global optimal bipartite matching between GT and Pred IDs)
        gt_id_list = list(all_gt_ids)
        pred_id_list = list(all_pred_ids)

        if gt_id_list and pred_id_list:
            sim_mat = np.zeros((len(gt_id_list), len(pred_id_list)), dtype=np.float32)
            for i, gid in enumerate(gt_id_list):
                for j, pid in enumerate(pred_id_list):
                    sim_mat[i, j] = overlap_counts.get((gid, pid), 0)

            # Maximize overlap counts via Hungarian algorithm
            r_idx, c_idx = linear_sum_assignment(-sim_mat)
            idtp = sum(sim_mat[r, c] for r, c in zip(r_idx, c_idx))
            idfp = total_tp + total_fp - idtp
            idfn = total_gt_boxes - idtp

            idp = (idtp / (idtp + idfp)) * 100.0 if (idtp + idfp) > 0 else 0.0
            idr = (idtp / (idtp + idfn)) * 100.0 if (idtp + idfn) > 0 else 0.0
            idf1 = (2.0 * idtp / (2.0 * idtp + idfp + idfn)) * 100.0 if (2.0 * idtp + idfp + idfn) > 0 else 0.0
        else:
            idp, idr, idf1 = 0.0, 0.0, 0.0

        # 3. Detection and Association Accuracy for HOTA
        deta = (total_tp / max(1, total_tp + total_fn + total_fp)) * 100.0
        assa = (total_tp / max(1, total_tp + id_switches)) * 100.0
        hota = float(np.sqrt((deta / 100.0) * (assa / 100.0)) * 100.0)

        # 4. Mostly Tracked (MT) and Mostly Lost (ML)
        mostly_tracked = 0
        mostly_lost = 0
        for gid, total_frames in gt_lifespans.items():
            hits = gt_hits.get(gid, 0)
            ratio = hits / max(1, total_frames)
            if ratio >= 0.8:
                mostly_tracked += 1
            elif ratio <= 0.2:
                mostly_lost += 1

        return MOTMetricsResult(
            idf1=float(round(idf1, 2)),
            idp=float(round(idp, 2)),
            idr=float(round(idr, 2)),
            idsw=int(id_switches),
            mota=float(round(mota, 2)),
            hota=float(round(hota, 2)),
            deta=float(round(deta, 2)),
            assa=float(round(assa, 2)),
            mostly_tracked=int(mostly_tracked),
            mostly_lost=int(mostly_lost),
            total_gt_ids=int(len(all_gt_ids)),
            total_pred_ids=int(len(all_pred_ids)),
            fps=float(round(measured_fps, 1)),
            latency_ms=float(round(measured_latency_ms, 2))
        )
