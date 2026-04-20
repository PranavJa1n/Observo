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
from .dataset_loader import count_log_lines, load_hdfs_logs
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

    def __init__(
        self,
        config: ClusteringConfig | None = None,
        use_rl_optimization: bool | None = None,
        rl_n_trials: int | None = None,
    ) -> None:
        """Initialize the pipeline with optional RL-based optimization.
        
        Args:
            config: Clustering configuration
            use_rl_optimization: Whether to use RL-based hyperparameter optimization
                                (overrides config if provided)
            rl_n_trials: Number of trials for RL optimization (overrides config if provided)
        """
        self.config = config or ClusteringConfig()
        self.config.ensure_dirs()
        self.feature_extractor = LogFeatureExtractor(self.config.feature)
        
        # Use provided values or fall back to config
        _use_rl = self.config.use_rl_optimization if use_rl_optimization is None else use_rl_optimization
        _n_trials = self.config.rl_n_trials if rl_n_trials is None else rl_n_trials
        
        self.clusterer = LogClusterer(
            self.config,
            use_rl_optimization=_use_rl,
            rl_n_trials=_n_trials,
        )
        self.stats = PipelineStats()
        self._trained = False
        self._artifact_path = self.config.model_dir / "log_clustering_pipeline.joblib"

    # ------------------------------------------------------------------
    # Training utilities
    # ------------------------------------------------------------------
    def load_training_logs(self) -> List[str]:
        dataset_dir = self.config.dataset_dir
        total_line_cap: Optional[int] = None

        if self.config.training_fraction and self.config.training_fraction > 0:
            total_lines = count_log_lines(dataset_dir)
            fraction_cap = max(1, int(total_lines * self.config.training_fraction))
            total_line_cap = fraction_cap

        if self.config.training_sample_size:
            if total_line_cap is None:
                total_line_cap = self.config.training_sample_size
            else:
                total_line_cap = min(total_line_cap, self.config.training_sample_size)

        return load_hdfs_logs(
            dataset_dir=dataset_dir,
            max_lines_per_file=self.config.max_lines_per_file,
            total_line_cap=total_line_cap,
        )

    def train(self, logs: Iterable[str]) -> ClusterSplit:
        log_list = list(logs)
        if not log_list:
            raise ValueError("No logs provided for training")

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
            raise RuntimeError("Pipeline has not been trained. Train or load artifacts before clustering batches.")

    def cluster_batch(self, logs: Iterable[str]) -> ClusterSplit:
        self._ensure_trained()
        log_list = [log for log in logs if log.strip()]
        if not log_list:
            return ClusterSplit([], [], [], self.clusterer.good_cluster_id, {})

        features = self.feature_extractor.transform(log_list)
        labels = self.clusterer.predict(features)
        split = split_clusters(labels, log_list, good_cluster_id=self.clusterer.good_cluster_id)
        return split

    # ------------------------------------------------------------------
    # Persistence utilities
    # ------------------------------------------------------------------
    def artifacts_exist(self) -> bool:
        return self._artifact_path.exists()

    def save_artifacts(self) -> None:
        self._ensure_trained()
        payload: Dict[str, Any] = {
            "vectorizer": self.feature_extractor.vectorizer,
            "clusterer": self.clusterer.clusterer,
            "config": self.config,
            "stats": self.stats,
            "good_cluster_id": self.clusterer.good_cluster_id,
            "optimization_result": getattr(self.clusterer, "optimization_result", None),
        }
        joblib.dump(payload, self._artifact_path)

    def load_artifacts(self) -> None:
        if not self.artifacts_exist():
            raise FileNotFoundError(f"Artifacts not found at {self._artifact_path}")
        payload: Dict[str, Any] = joblib.load(self._artifact_path)
        self.feature_extractor.vectorizer = payload["vectorizer"]
        self.clusterer.clusterer = payload["clusterer"]
        self.clusterer.is_trained = True
        self.clusterer.good_cluster_id = payload.get("good_cluster_id")
        self.clusterer.optimization_result = payload.get("optimization_result")
        self.stats = payload.get("stats", PipelineStats())
        self._trained = True

    # ------------------------------------------------------------------
    def stats_dict(self) -> Dict[str, Any]:
        data = self.stats.as_dict()
        data["trained"] = self._trained
        data["good_cluster_id"] = self.clusterer.good_cluster_id
        data["model_path"] = str(self._artifact_path)
        if hasattr(self.clusterer, "optimization_result") and self.clusterer.optimization_result:
            data["rl_optimization"] = {
                "best_score": self.clusterer.optimization_result.best_score,
                "best_params": self.clusterer.optimization_result.best_params.to_dict(),
                "n_trials": len(self.clusterer.optimization_result.all_trials),
            }
        return data

    def stats_json(self) -> str:
        return json.dumps(self.stats_dict(), indent=2)
