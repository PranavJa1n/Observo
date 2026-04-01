"""Cluster post-processing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import numpy as np


@dataclass(slots=True)
class ClusterSplit:
    good_logs: List[str]
    bad_logs: List[str]
    outlier_logs: List[str]
    good_cluster_id: Optional[int]
    label_counts: Dict[int, int]

    @property
    def summary(self) -> Dict[str, int]:
        return {
            "good": len(self.good_logs),
            "bad": len(self.bad_logs),
            "outliers": len(self.outlier_logs),
        }


def split_clusters(labels: Iterable[int], logs: List[str], good_cluster_id: Optional[int] = None) -> ClusterSplit:
    label_array = np.asarray(labels)

    if label_array.size == 0 or not logs:
        return ClusterSplit([], [], [], good_cluster_id, {})

    positive_mask = label_array >= 0
    positive_labels = label_array[positive_mask]
    positive_values, positive_counts = np.unique(positive_labels, return_counts=True) if positive_labels.size else (np.array([]), np.array([]))

    resolved_good_cluster = good_cluster_id
    if resolved_good_cluster is None and positive_values.size:
        resolved_good_cluster = int(positive_values[np.argmax(positive_counts)])

    good_logs: List[str] = []
    bad_logs: List[str] = []
    outlier_logs: List[str] = []

    label_counts: Dict[int, int] = {}

    for log, label in zip(logs, label_array):
        label_counts[int(label)] = label_counts.get(int(label), 0) + 1

        if label == -1:
            outlier_logs.append(log)
        elif resolved_good_cluster is not None and label == resolved_good_cluster:
            good_logs.append(log)
        else:
            bad_logs.append(log)

    return ClusterSplit(good_logs, bad_logs, outlier_logs, resolved_good_cluster, label_counts)
