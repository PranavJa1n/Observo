"""HDBSCAN clusterer with adaptive 3-point grid search.

Instead of full hyperparameter optimization (RL or Bayesian), we run three
HDBSCAN fits covering small / medium / large cluster sizes and pick the
configuration with the lowest noise ratio.  This adapts automatically to
different log volumes without adding significant complexity.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
from hdbscan import HDBSCAN
from hdbscan import prediction as hdbscan_prediction

from .config import ClusteringConfig

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 3-point parameter grid                                                       #
# --------------------------------------------------------------------------- #

_PARAM_GRID: List[Dict] = [
    {"min_cluster_size": 15,  "min_samples":  5},   # small  — catches rare patterns
    {"min_cluster_size": 50,  "min_samples": 10},   # medium — balanced default
    {"min_cluster_size": 100, "min_samples": 20},   # large  — broad groups, fewer clusters
]

_HDBSCAN_DEFAULTS = {
    "metric": "euclidean",
    "cluster_selection_method": "eom",
    "core_dist_n_jobs": -1,
    "prediction_data": True,   # required for approximate_predict at inference time
}


# --------------------------------------------------------------------------- #
# Grid search helper                                                            #
# --------------------------------------------------------------------------- #

def _noise_ratio(labels: np.ndarray) -> float:
    """Fraction of points labelled as noise (label == -1)."""
    return float(np.sum(labels == -1) / labels.size) if labels.size else 1.0


def _select_best_params(features) -> Dict:
    """Run 3 HDBSCAN fits and return the params with the lowest noise ratio.

    Fewer noise points means more logs are assigned to a meaningful cluster,
    which is the right optimisation target for general log data where most
    lines belong to some recognisable pattern.

    Args:
        features: Sparse or dense feature matrix.

    Returns:
        The parameter dict from _PARAM_GRID that produced the least noise.
    """
    best_params = _PARAM_GRID[1]   # fallback: medium
    best_noise = 1.0

    for params in _PARAM_GRID:
        try:
            model = HDBSCAN(**params, **_HDBSCAN_DEFAULTS)
            labels = model.fit_predict(features)
            noise = _noise_ratio(labels)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            logger.info(
                f"Grid search | min_cluster_size={params['min_cluster_size']:>3d} "
                f"min_samples={params['min_samples']:>2d} → "
                f"clusters={n_clusters:>3d}  noise_ratio={noise:.3f}"
            )
            if noise < best_noise:
                best_noise = noise
                best_params = params
        except Exception as exc:
            logger.warning(f"Grid search trial failed ({params}): {exc}")

    logger.info(
        f"Selected params: {best_params}  (noise_ratio={best_noise:.3f})"
    )
    return best_params


# --------------------------------------------------------------------------- #
# LogClusterer                                                                  #
# --------------------------------------------------------------------------- #

class LogClusterer:
    """HDBSCAN clusterer with adaptive parameter selection via grid search."""

    def __init__(self, config: ClusteringConfig | None = None) -> None:
        self.config = config or ClusteringConfig()
        self.clusterer: Optional[HDBSCAN] = None
        self.is_trained: bool = False
        self.good_cluster_id: Optional[int] = None
        self.best_params: Optional[Dict] = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit_predict(self, features) -> np.ndarray:
        """Select parameters via grid search, fit HDBSCAN, return labels.

        Args:
            features: Sparse TF-IDF matrix or dense numpy array.

        Returns:
            Integer cluster labels (-1 = noise/outlier).
        """
        logger.info("Running 3-point grid search to select HDBSCAN parameters…")
        self.best_params = _select_best_params(features)

        self.clusterer = HDBSCAN(**self.best_params, **_HDBSCAN_DEFAULTS)
        labels = self.clusterer.fit_predict(features)
        self.is_trained = True

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        logger.info(
            f"Training complete — clusters={n_clusters}  "
            f"noise={int(np.sum(labels == -1))}  total={len(labels)}"
        )
        return labels

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, features) -> np.ndarray:
        """Predict cluster labels for new log data.

        Uses HDBSCAN's approximate_predict so the model is never re-fitted
        on incoming batches.

        Args:
            features: Sparse TF-IDF matrix or dense numpy array.

        Returns:
            Integer cluster labels (-1 = does not belong to any known cluster).
        """
        if not self.is_trained or self.clusterer is None:
            raise RuntimeError("Clusterer has not been trained yet.")

        labels, _ = hdbscan_prediction.approximate_predict(self.clusterer, features)
        return labels

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def params_summary(self) -> str:
        if self.best_params is None:
            return "Not trained yet."
        return (
            f"min_cluster_size={self.best_params['min_cluster_size']}  "
            f"min_samples={self.best_params['min_samples']}"
        )
