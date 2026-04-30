"""High-level orchestration for log clustering."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import joblib

from .cluster_classifier import ClusterSplit, split_clusters
from .cluster_model import LogClusterer
from .config import ClusteringConfig
from .dataset_loader import load_logs
from .feature_extractor import LogFeatureExtractor


@dataclass(slots=True)
class PipelineStats:
    total_trained_logs: int = 0
    good_count: int = 0
    bad_count: int = 0
    outlier_count: int = 0

    def as_dict(self) -> Dict[str, int]:
        return asdict(self)


class LogClusteringPipeline:
    """Coordinates feature extraction, clustering, and classification."""

    def __init__(self, config: ClusteringConfig | None = None) -> None:
        self.config = config or ClusteringConfig()
        self.config.ensure_dirs()
        self.feature_extractor = LogFeatureExtractor(self.config.feature)
        self.clusterer = LogClusterer(self.config)
        self.stats = PipelineStats()
        self._trained = False
        self._artifact_path = self.config.model_dir / "log_clustering_pipeline.joblib"

    # ------------------------------------------------------------------
    # Training utilities
    # ------------------------------------------------------------------

    def load_training_logs(self) -> List[str]:
        """Load log lines from the dataset directory — single read pass.

        Uses max_lines_per_file as the sole cap. No pre-counting scan needed.
        """
        return load_logs(
            dataset_dir=self.config.dataset_dir,
            max_lines_per_file=self.config.max_lines_per_file,
            total_line_cap=self.config.training_sample_size,
        )

    def train(self, logs: Iterable[str]) -> ClusterSplit:
        log_list = list(logs)
        if not log_list:
            raise ValueError("No logs provided for training.")

        features = self.feature_extractor.fit_transform(log_list)
        labels = self.clusterer.fit_predict(features)
        split = split_clusters(labels, log_list)

        self.clusterer.good_cluster_id = split.good_cluster_id
        self.stats = PipelineStats(
            total_trained_logs=len(log_list),
            good_count=len(split.good_logs),
            bad_count=len(split.bad_logs),
            outlier_count=len(split.outlier_logs),
        )
        self._trained = True
        return split

    def train_from_dataset(self) -> ClusterSplit:
        logs = self.load_training_logs()
        return self.train(logs)

    # ------------------------------------------------------------------
    # Inference utilities
    # ------------------------------------------------------------------

    def _ensure_trained(self) -> None:
        if not self._trained:
            raise RuntimeError(
                "Pipeline has not been trained. "
                "Call train() or load_artifacts() first."
            )

    def cluster_batch(self, logs: Iterable[str]) -> ClusterSplit:
        self._ensure_trained()
        log_list = [log for log in logs if log.strip()]
        if not log_list:
            return ClusterSplit([], [], [], self.clusterer.good_cluster_id, {})

        features = self.feature_extractor.transform(log_list)
        labels = self.clusterer.predict(features)
        return split_clusters(labels, log_list, good_cluster_id=self.clusterer.good_cluster_id)

    # ------------------------------------------------------------------
    # Persistence utilities
    # ------------------------------------------------------------------

    def artifacts_exist(self) -> bool:
        return self._artifact_path.exists()

    def save_artifacts(self) -> None:
        self._ensure_trained()
        payload: Dict[str, Any] = {
            "vectorizer": self.feature_extractor.vectorizer,
            "svd": getattr(self.feature_extractor, "svd", None),
            "clusterer": self.clusterer.clusterer,
            "config": self.config,
            "stats": self.stats,
            "good_cluster_id": self.clusterer.good_cluster_id,
            "best_params": self.clusterer.best_params,
        }
        joblib.dump(payload, self._artifact_path)

    def load_artifacts(self) -> None:
        if not self.artifacts_exist():
            raise FileNotFoundError(f"Artifacts not found at {self._artifact_path}")
        payload: Dict[str, Any] = joblib.load(self._artifact_path)
        self.feature_extractor.vectorizer = payload["vectorizer"]
        if "svd" in payload and payload["svd"] is not None:
            self.feature_extractor.svd = payload["svd"]
        self.clusterer.clusterer = payload["clusterer"]
        self.clusterer.is_trained = True
        self.clusterer.good_cluster_id = payload.get("good_cluster_id")
        self.clusterer.best_params = payload.get("best_params")
        self.stats = payload.get("stats", PipelineStats())
        self._trained = True

    # ------------------------------------------------------------------

    def stats_dict(self) -> Dict[str, Any]:
        data = self.stats.as_dict()
        data["trained"] = self._trained
        data["good_cluster_id"] = self.clusterer.good_cluster_id
        data["model_path"] = str(self._artifact_path)
        if self.clusterer.best_params:
            data["best_params"] = self.clusterer.best_params
        return data

    def stats_json(self) -> str:
        return json.dumps(self.stats_dict(), indent=2)
