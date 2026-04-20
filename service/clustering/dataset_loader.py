"""Utilities for loading the HDFS dataset stored under ``dataset``."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional


def iter_log_files(dataset_dir: Path, limit: Optional[int] = None) -> Iterable[Path]:
    """Yield log file paths in a deterministic order."""

    files = sorted(dataset_dir.glob("*.log"))
    count = 0
    for file_path in files:
        yield file_path
        count += 1
        if limit is not None and count >= limit:
            break


def load_hdfs_logs(
    dataset_dir: Path,
    max_files: Optional[int] = None,
    max_lines_per_file: Optional[int] = None,
    total_line_cap: Optional[int] = None,
) -> List[str]:
    """Load raw log lines from disk with basic caps to avoid OOM."""

    logs: List[str] = []
    total_lines = 0

    for file_path in iter_log_files(dataset_dir, max_files):
        if not file_path.exists():
            continue

        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for idx, line in enumerate(handle):
                if max_lines_per_file is not None and idx >= max_lines_per_file:
                    break

                clean_line = line.strip()
                if clean_line:
                    logs.append(clean_line)
                    total_lines += 1

                if total_line_cap is not None and total_lines >= total_line_cap:
                    return logs

    return logs


def count_log_lines(dataset_dir: Path, max_files: Optional[int] = None) -> int:
    """Return the total number of log lines available in the dataset."""

    total = 0
    for file_path in iter_log_files(dataset_dir, max_files):
        if not file_path.exists():
            continue
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for _ in handle:
                total += 1
    return total
