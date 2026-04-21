"""Script to test the trained model's inference speed and results on the full dataset."""

import time
from pathlib import Path

from service.clustering.pipeline import LogClusteringPipeline
from service.clustering.config import ClusteringConfig

def main():
    pipeline = LogClusteringPipeline()
    print("Loading trained artifacts...")
    try:
        pipeline.load_artifacts()
    except FileNotFoundError:
        print("Model not found! Run train_pipeline first.")
        return

    config = ClusteringConfig()
    dataset_dir = config.dataset_dir
    
    total_logs = 0
    total_good = 0
    total_bad = 0
    total_outliers = 0
    
    # Process in batches to keep memory usage low
    batch_size = 20000
    current_batch = []
    
    print(f"Starting inference on all logs in {dataset_dir} ...")
    start_time = time.time()
    
    for file_path in dataset_dir.glob("*.log"):
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                clean_line = line.strip()
                if not clean_line:
                    continue
                    
                current_batch.append(clean_line)
                
                if len(current_batch) >= batch_size:
                    split = pipeline.cluster_batch(current_batch)
                    total_good += len(split.good_logs)
                    total_bad += len(split.bad_logs)
                    total_outliers += len(split.outlier_logs)
                    total_logs += len(current_batch)
                    
                    print(f"Processed {total_logs:,} logs... (Good: {total_good:,}, Bad: {total_bad:,}, Outliers: {total_outliers:,})")
                    current_batch = []
                    
    # Process remaining logs in the last batch
    if current_batch:
        split = pipeline.cluster_batch(current_batch)
        total_good += len(split.good_logs)
        total_bad += len(split.bad_logs)
        total_outliers += len(split.outlier_logs)
        total_logs += len(current_batch)

    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*40)
    print("INFERENCE COMPLETE")
    print("="*40)
    print(f"Total Logs Processed : {total_logs:,}")
    print(f"Good Logs (Normal)   : {total_good:,}")
    print(f"Bad Logs (Anomalies) : {total_bad:,}")
    print(f"Outlier Logs (Noise) : {total_outliers:,}")
    print(f"Time Taken           : {duration:.2f} seconds")
    if duration > 0:
        print(f"Inference Speed      : {total_logs / duration:,.0f} logs/second")
    print("="*40)

if __name__ == "__main__":
    main()
