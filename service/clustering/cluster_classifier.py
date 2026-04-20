"""Cluster post-processing: keyword-based good/bad classification.

After HDBSCAN groups logs by similarity, each cluster is independently
classified as 'good' (normal) or 'bad' (anomalous) by scanning a sample
of its logs for bad keywords.

This keyword set is universal — the same error/failure vocabulary appears
in Java (log4j), Python (logging), nginx, syslog, Docker, and Go logs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


# --------------------------------------------------------------------------- #
# Bad-cluster keyword set — universal across log frameworks                    #
# --------------------------------------------------------------------------- #

BAD_KEYWORDS: frozenset = frozenset({
    # Standard log levels
    "error", "err", "fatal", "critical", "crit",
    # Failure vocabulary
    "fail", "failed", "failure", "exception",
    "traceback", "panic", "crash", "abort",
    # Connectivity problems
    "timeout", "timed", "refused", "unreachable",
    # Auth / access
    "denied", "unauthorized", "forbidden",
    # System stress
    "oom", "killed", "segfault", "deadlock",
    # HTTP server errors
    "500", "502", "503", "504",
})

# A cluster is BAD if this fraction of sampled logs contain a bad keyword.
BAD_RATIO_THRESHOLD: float = 0.30

# Max logs to sample per cluster for classification (avoids scanning huge clusters).
_SAMPLE_SIZE: int = 50


# --------------------------------------------------------------------------- #
# Data containers                                                              #
# --------------------------------------------------------------------------- #

@dataclass(slots=True)
class ClusterSplit:
    good_logs: List[str]
    bad_logs: List[str]
    outlier_logs: List[str]
    good_cluster_id: Optional[int]  # largest good cluster id (for artifact compat)
    label_counts: Dict[int, int]

    @property
    def summary(self) -> Dict[str, int]:
        return {
            "good": len(self.good_logs),
            "bad": len(self.bad_logs),
            "outliers": len(self.outlier_logs),
        }


# --------------------------------------------------------------------------- #
# Classification helpers                                                        #
# --------------------------------------------------------------------------- #

def classify_cluster(logs: List[str]) -> str:
    """Classify a single cluster as 'good' or 'bad'.

    Samples up to _SAMPLE_SIZE logs and checks what fraction contain at
    least one bad keyword.  If >= BAD_RATIO_THRESHOLD → 'bad'.

    Args:
        logs: All log lines belonging to one HDBSCAN cluster.

    Returns:
        'bad' if the cluster appears anomalous, 'good' otherwise.
    """
    if not logs:
        return "good"

    sample = logs[:_SAMPLE_SIZE]
    bad_count = sum(
        1
        for log in sample
        if any(kw in log.lower() for kw in BAD_KEYWORDS)
    )
    ratio = bad_count / len(sample)
    return "bad" if ratio >= BAD_RATIO_THRESHOLD else "good"


def split_clusters(
    labels,
    logs: List[str],
    good_cluster_id: Optional[int] = None,  # noqa: ARG001 — kept for API compat
) -> ClusterSplit:
    """Split logs into good, bad, and outlier buckets using keyword classification.

    Each non-noise cluster is independently classified. The old
    'largest cluster = good' heuristic is removed — it fails whenever
    error logs outnumber info logs in a batch (e.g. during an incident).

    Args:
        labels:          HDBSCAN cluster labels (array-like, -1 = noise/outlier).
        logs:            Raw log lines corresponding to each label.
        good_cluster_id: Ignored — kept for backward-compatibility with callers.

    Returns:
        ClusterSplit with logs partitioned into good / bad / outlier lists.
    """
    label_array = np.asarray(labels)

    if label_array.size == 0 or not logs:
        return ClusterSplit([], [], [], None, {})

    # --- Group logs by cluster id ---
    cluster_map: Dict[int, List[str]] = {}
    label_counts: Dict[int, int] = {}
    outlier_logs: List[str] = []

    for log, label in zip(logs, label_array):
        lbl = int(label)
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
        if lbl == -1:
            outlier_logs.append(log)
        else:
            cluster_map.setdefault(lbl, []).append(log)

    # --- Classify each cluster independently ---
    good_logs: List[str] = []
    bad_logs: List[str] = []
    good_cluster_ids: List[int] = []

    for cluster_id, cluster_logs in cluster_map.items():
        if classify_cluster(cluster_logs) == "bad":
            bad_logs.extend(cluster_logs)
        else:
            good_logs.extend(cluster_logs)
            good_cluster_ids.append(cluster_id)

    # Pick the largest good cluster id (saved in artifacts for compat)
    resolved_good_id: Optional[int] = None
    if good_cluster_ids:
        resolved_good_id = max(
            good_cluster_ids,
            key=lambda cid: label_counts.get(cid, 0),
        )

    return ClusterSplit(good_logs, bad_logs, outlier_logs, resolved_good_id, label_counts)
