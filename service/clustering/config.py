"""Configuration helpers for the clustering service."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class FeatureConfig:
    """Configuration for feature extraction."""

    method: str = field(default_factory=lambda: os.getenv("CLUSTER_FEATURE_METHOD", "tfidf"))
    max_features: int = field(default_factory=lambda: int(os.getenv("CLUSTER_MAX_FEATURES", 5000)))
    ngram_range: Tuple[int, int] = (1, 2)
    analyzer: str = "word"
    lowercase: bool = True


@dataclass(slots=True)
class ClusteringConfig:
    """Top-level clustering settings."""

    dataset_dir: Path = field(default_factory=lambda: Path(os.getenv("CLUSTER_DATASET_DIR", BASE_DIR / "dataset")))
    model_dir: Path = field(default_factory=lambda: Path(os.getenv("CLUSTER_MODEL_DIR", BASE_DIR / "service" / "clustering" / "models")))
    min_cluster_size: int = field(default_factory=lambda: int(os.getenv("CLUSTER_MIN_CLUSTER_SIZE", 15)))
    min_samples: int = field(default_factory=lambda: int(os.getenv("CLUSTER_MIN_SAMPLES", 5)))
    cluster_selection_epsilon: float = field(default_factory=lambda: float(os.getenv("CLUSTER_EPSILON", 0.0)))
    feature: FeatureConfig = field(default_factory=FeatureConfig)
    training_sample_size: int = field(default_factory=lambda: int(os.getenv("CLUSTER_TRAINING_SAMPLE_SIZE", 25000)))
    max_lines_per_file: int = field(default_factory=lambda: int(os.getenv("CLUSTER_LINES_PER_FILE", 20000)))

    def ensure_dirs(self) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
