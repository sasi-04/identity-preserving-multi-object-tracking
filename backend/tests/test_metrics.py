"""Unit tests for MOT evaluation metrics calculation."""
import numpy as np
import pytest
from backend.app.evaluation.metrics import MOTEvaluator


def test_mot_evaluator_perfect_tracking():
    evaluator = MOTEvaluator(iou_threshold=0.5)

    # 2 ground truth objects across 3 frames
    box1 = np.array([10.0, 10.0, 50.0, 90.0])
    box2 = np.array([100.0, 100.0, 150.0, 180.0])

    gt_frames = {
        0: [(1, box1), (2, box2)],
        1: [(1, box1 + 5), (2, box2 + 5)],
        2: [(1, box1 + 10), (2, box2 + 10)]
    }

    # Exactly matching predictions with identical IDs
    pred_frames = {
        0: [(1, box1), (2, box2)],
        1: [(1, box1 + 5), (2, box2 + 5)],
        2: [(1, box1 + 10), (2, box2 + 10)]
    }

    res = evaluator.evaluate(gt_frames, pred_frames)
    assert res.mota == 100.0
    assert res.idf1 == 100.0
    assert res.idsw == 0
    assert res.mostly_tracked == 2
    assert res.mostly_lost == 0


def test_mot_evaluator_id_switch_detection():
    evaluator = MOTEvaluator(iou_threshold=0.5)

    box = np.array([10.0, 10.0, 50.0, 90.0])

    gt_frames = {
        0: [(1, box)],
        1: [(1, box + 2)],
        2: [(1, box + 4)]
    }

    # Prediction switches from ID 10 to ID 20 at frame 1
    pred_frames = {
        0: [(10, box)],
        1: [(20, box + 2)],  # ID switch occurred here!
        2: [(20, box + 4)]
    }

    res = evaluator.evaluate(gt_frames, pred_frames)
    assert res.idsw == 1
    assert res.idf1 < 100.0
