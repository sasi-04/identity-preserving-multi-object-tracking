"""
ZED VISION - Causal Kalman Filter for Bounding Box Motion Estimation
8-dimensional state space: [x, y, a, h, vx, vy, va, vh]
where (x, y) is bounding box center, a = w / h (aspect ratio), and h is height.
"""

from typing import Tuple
import numpy as np
import scipy.linalg


class KalmanBoxTracker:
    """
    Kalman filter tracking a single bounding box in image coordinates.
    Operates strictly online and causally.
    """
    chi2_gate_95 = 9.4877  # 95% confidence chi-square threshold for 4 degrees of freedom

    def __init__(self, bbox: np.ndarray):
        """
        Initialize Kalman filter from detection bbox [x1, y1, x2, y2].
        """
        # 8-state transition matrix F (dt = 1.0)
        self._motion_mat = np.eye(8, 8)
        for i in range(4):
            self._motion_mat[i, i + 4] = 1.0

        # Measurement projection matrix H (maps 8D state to 4D [cx, cy, a, h])
        self._update_mat = np.eye(4, 8)

        # Standard deviations for position and velocity uncertainty
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

        # Max covariance variance ceiling to prevent unbounded uncertainty during dense occlusion
        self._max_covariance_val = 1e4

        # Convert [x1, y1, x2, y2] to [cx, cy, a, h]
        measurement = self.bbox_to_z(bbox)

        # Initial state mean
        self.mean = np.zeros(8)
        self.mean[:4] = measurement

        # Initial covariance P
        std = [
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[3],
            1e-2,
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            1e-5,
            10 * self._std_weight_velocity * measurement[3],
        ]
        self.covariance = np.diag(np.square(std))

    @staticmethod
    def bbox_to_z(bbox: np.ndarray) -> np.ndarray:
        """Convert [x1, y1, x2, y2] to [cx, cy, a, h]."""
        w = max(1.0, float(bbox[2] - bbox[0]))
        h = max(1.0, float(bbox[3] - bbox[1]))
        x = float(bbox[0] + w / 2.0)
        y = float(bbox[1] + h / 2.0)
        a = float(w / h)
        return np.array([x, y, a, h])

    @staticmethod
    def z_to_bbox(z: np.ndarray) -> np.ndarray:
        """Convert [cx, cy, a, h] to [x1, y1, x2, y2]."""
        w = z[2] * z[3]
        h = z[3]
        x1 = z[0] - w / 2.0
        y1 = z[1] - h / 2.0
        x2 = z[0] + w / 2.0
        y2 = z[1] + h / 2.0
        return np.array([x1, y1, x2, y2])

    def predict(self) -> np.ndarray:
        """
        Advance state distribution one time step causally.
        Returns predicted bounding box [x1, y1, x2, y2].
        """
        std_pos = [
            self._std_weight_position * self.mean[3],
            self._std_weight_position * self.mean[3],
            1e-2,
            self._std_weight_position * self.mean[3],
        ]
        std_vel = [
            self._std_weight_velocity * self.mean[3],
            self._std_weight_velocity * self.mean[3],
            1e-5,
            self._std_weight_velocity * self.mean[3],
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))

        # State transition: x_{k|k-1} = F * x_{k-1}
        self.mean = np.dot(self._motion_mat, self.mean)
        # Covariance update: P_{k|k-1} = F * P * F^T + Q
        self.covariance = np.linalg.multi_dot((self._motion_mat, self.covariance, self._motion_mat.T)) + motion_cov

        # Enforce bounded uncertainty clamp
        np.clip(self.covariance, -self._max_covariance_val, self._max_covariance_val, out=self.covariance)

        return self.z_to_bbox(self.mean[:4])

    def project(self) -> Tuple[np.ndarray, np.ndarray]:
        """Project state distribution from 8D to 4D measurement space."""
        std = [
            self._std_weight_position * self.mean[3],
            self._std_weight_position * self.mean[3],
            1e-1,
            self._std_weight_position * self.mean[3],
        ]
        meas_cov = np.diag(np.square(std))

        proj_mean = np.dot(self._update_mat, self.mean)
        proj_cov = np.linalg.multi_dot((self._update_mat, self.covariance, self._update_mat.T)) + meas_cov
        # Symmetrize and add small diagonal jitter for strict positive definiteness
        proj_cov = 0.5 * (proj_cov + proj_cov.T) + np.eye(4) * 1e-4
        return proj_mean, proj_cov

    def update(self, bbox: np.ndarray) -> np.ndarray:
        """
        Update state distribution with confirmed observation [x1, y1, x2, y2].
        Returns updated bounding box [x1, y1, x2, y2].
        """
        measurement = self.bbox_to_z(bbox)
        proj_mean, proj_cov = self.project()

        # Kalman gain: K = P * H^T * (H * P * H^T + R)^-1 with robust fallback
        try:
            chol_factor, lower = scipy.linalg.cho_factor(proj_cov, lower=True, check_finite=False)
            kalman_gain = scipy.linalg.cho_solve(
                (chol_factor, lower),
                np.dot(self.covariance, self._update_mat.T).T,
                check_finite=False
            ).T
        except (scipy.linalg.LinAlgError, np.linalg.LinAlgError):
            proj_inv = np.linalg.pinv(proj_cov)
            kalman_gain = np.dot(self.covariance, np.dot(self._update_mat.T, proj_inv))

        innovation = measurement - proj_mean
        self.mean = self.mean + np.dot(innovation, kalman_gain.T)
        self.covariance = self.covariance - np.linalg.multi_dot((kalman_gain, proj_cov, kalman_gain.T))
        
        # Ensure symmetry and positive definiteness of state covariance
        self.covariance = 0.5 * (self.covariance + self.covariance.T)
        np.fill_diagonal(self.covariance, np.maximum(np.diag(self.covariance), 1e-4))

        return self.z_to_bbox(self.mean[:4])

    def gating_distance(self, measurements: np.ndarray, only_position: bool = False) -> np.ndarray:
        """
        Compute squared Mahalanobis distance between projected state and candidate measurements.
        measurements: (N, 4) array in [x1, y1, x2, y2]
        """
        if len(measurements) == 0:
            return np.empty((0,))

        z_meas = np.array([self.bbox_to_z(m) for m in measurements])
        proj_mean, proj_cov = self.project()

        if only_position:
            proj_mean = proj_mean[:2]
            proj_cov = proj_cov[:2, :2]
            z_meas = z_meas[:, :2]

        diff = z_meas - proj_mean
        try:
            cholesky_factor = np.linalg.cholesky(proj_cov)
            z_sol = scipy.linalg.solve_triangular(cholesky_factor, diff.T, lower=True, check_finite=False)
            squared_maha = np.sum(z_sol ** 2, axis=0)
        except (scipy.linalg.LinAlgError, np.linalg.LinAlgError):
            inv_cov = np.linalg.pinv(proj_cov)
            squared_maha = np.sum(np.dot(diff, inv_cov) * diff, axis=1)

        return squared_maha

    def get_spatial_uncertainty_radius(self) -> float:
        """Returns standard deviation radius in pixels of position uncertainty."""
        var_x = max(1.0, float(self.covariance[0, 0]))
        var_y = max(1.0, float(self.covariance[1, 1]))
        return float(np.sqrt(var_x + var_y))
