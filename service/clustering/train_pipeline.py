"""CLI utility to train the log clustering pipeline without FastAPI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import LogClusteringPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the Observo log clustering pipeline")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Retrain even if artifacts already exist",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=None,
        help="Optional override for artifact output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pipeline = LogClusteringPipeline()

    if args.artifacts is not None:
        pipeline._artifact_path = args.artifacts  # type: ignore[attr-defined]

    if pipeline.artifacts_exist() and not args.force:
        print("Artifacts already exist. Use --force to retrain.")
        return 0

    print("Loading training logs...")
    logs = pipeline.load_training_logs()
    print(f"Loaded {len(logs)} log lines for training")

    print("Fitting TF-IDF and HDBSCAN models (this may take a while)...")
    split = pipeline.train(logs)

    print("Saving artifacts...")
    pipeline.save_artifacts()

    stats = pipeline.stats_dict()
    stats["last_train_summary"] = split.summary
    print("Training complete. Stats:")
    print(json.dumps(stats, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
