"""Utilities for loading log files from the dataset directory.

Loads raw log lines from .log files with a per-file line cap and an optional
total cap.  A single sequential read pass is used — no pre-counting scan.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional


def iter_log_files(dataset_dir: Path, limit: Optional[int] = None) -> Iterable[Path]:
    """Yield .log file paths in deterministic (sorted) order.

    Args:
        dataset_dir: Directory to search for .log files.
        limit:       Optional maximum number of files to yield.

    Yields:
        Path objects for each .log file found.
    """
    count = 0
    for file_path in sorted(dataset_dir.glob("*.log")):
        yield file_path
        count += 1
        if limit is not None and count >= limit:
            break


def load_logs(
    dataset_dir: Path,
    max_files: Optional[int] = None,
    max_lines_per_file: Optional[int] = None,
    total_line_cap: Optional[int] = None,
) -> List[str]:
    """Load raw log lines from disk in a single sequential pass.

    Args:
        dataset_dir:       Directory containing .log files.
        max_files:         Maximum number of files to read (None = all).
        max_lines_per_file: Maximum lines to read from each file (None = all).
        total_line_cap:    Hard cap on total lines loaded across all files (None = no cap).

    Returns:
        List of non-empty log line strings.
    """
    logs: List[str] = []
    total = 0

    for file_path in iter_log_files(dataset_dir, max_files):
        if not file_path.exists():
            continue

        with file_path.open("r", encoding="utf-8", errors="ignore") as fh:
            for idx, line in enumerate(fh):
                if max_lines_per_file is not None and idx >= max_lines_per_file:
                    break

                clean = line.strip()
                if not clean:
                    continue

                logs.append(clean)
                total += 1

                if total_line_cap is not None and total >= total_line_cap:
                    return logs

    return logs


# Backward-compatible alias used by older code paths
load_hdfs_logs = load_logs
