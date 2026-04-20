# Observo Clustering Service

This directory contains the core machine learning pipeline for Observo's log clustering and anomaly detection capabilities. It uses a combination of format-agnostic text normalization, TF-IDF vectorization, HDBSCAN clustering, and keyword-based classification.

## Directory Structure

Here is a breakdown of what each file does in the clustering pipeline:

### ⚙️ Core Configuration & Orchestration
- **`config.py`**: Defines all configuration settings via dataclasses (`FeatureConfig`, `ClusteringConfig`). Settings can be overridden using environment variables.
- **`pipeline.py`**: The high-level orchestrator. It ties everything together: loading data, applying feature extraction, running the clusterer, classifying the results, and saving/loading the trained model artifacts (`joblib`).

### 🔧 Machine Learning Pipeline
- **`feature_extractor.py`**: Handles text normalization and feature extraction. It uses a robust, format-agnostic regex pipeline to strip noise (timestamps, IPs, UUIDs, file paths, etc.) from *any* log format, then applies `TfidfVectorizer` to convert the cleaned text into a sparse feature matrix.
- **`cluster_model.py`**: A wrapper around the `HDBSCAN` algorithm. During training, it performs a fast 3-point grid search (testing small, medium, and large cluster assumptions) to automatically find the parameters that minimize noise for your specific dataset.
- **`cluster_classifier.py`**: Responsible for determining if a formed cluster represents normal behavior or an anomaly. It scans a sample of logs from each cluster against a universal set of `BAD_KEYWORDS` (e.g., "error", "timeout", "exception"). If a cluster's "bad ratio" exceeds 30%, the entire cluster is flagged as anomalous.

### 📁 Data & Execution
- **`dataset_loader.py`**: A utility to efficiently stream and load raw `.log` files from your dataset directory without reading the entire dataset into memory multiple times.
- **`train_pipeline.py`**: A standalone CLI script used to train the model from scratch using the logs in your `dataset/` directory and save the resulting artifacts to `models/`.
- **`api.py`**: A FastAPI application that exposes the clustering pipeline over HTTP. It provides endpoints for health checks (`/health`), batch inference (`/cluster/batch`), training (`/train`), and statistics (`/cluster/stats`).

## Flow Overview

1. **Input**: Raw log lines arrive (via API or dataset loader).
2. **Extraction**: `feature_extractor.py` cleans the logs and converts them to TF-IDF vectors.
3. **Clustering**: `cluster_model.py` groups similar log vectors together using HDBSCAN.
4. **Classification**: `cluster_classifier.py` inspects each group and labels it as `good` or `bad`.
5. **Output**: The split logs are returned to the caller (e.g., the Go daemon).

## Model Storage
Trained models are saved as `log_clustering_pipeline.joblib` inside the `models/` subdirectory. The pipeline will automatically load this artifact if it exists when the service starts up.
