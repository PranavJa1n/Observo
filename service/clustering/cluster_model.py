"""Wrapper around HDBSCAN for log clustering."""

from __future__ import annotations

from typing import Optional

import numpy as np
from hdbscan import HDBSCAN
from hdbscan import prediction as hdbscan_prediction

from .config import ClusteringConfig


class LogClusterer:
    """Encapsulates HDBSCAN fit and inference routines."""

    def __init__(self, config: ClusteringConfig | None = None) -> None:
        config = config or ClusteringConfig()
        self.clusterer = HDBSCAN(
            min_cluster_size=config.min_cluster_size,
            min_samples=config.min_samples,
            cluster_selection_epsilon=config.cluster_selection_epsilon,
            metric="euclidean",
            cluster_selection_method="eom",
        )
        self.is_trained = False
        self.good_cluster_id: Optional[int] = None

    def fit_predict(self, features) -> np.ndarray:
        labels = self.clusterer.fit_predict(features)
        self.is_trained = True
        return labels

    def predict(self, features) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Clusterer has not been trained")

        dense = features.toarray() if hasattr(features, "toarray") else np.asarray(features)
        labels, _ = hdbscan_prediction.approximate_predict(self.clusterer, dense)
        return labels
