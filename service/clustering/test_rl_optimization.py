"""Test script for RL-based HDBSCAN optimization.

Run this script from the project root:
    python -m service.clustering.test_rl_optimization
"""

import logging
import sys
from pathlib import Path

import numpy as np
from sklearn.datasets import make_blobs

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def test_rl_optimizer_basic():
    """Test basic functionality of RL optimizer."""
    from service.clustering.rl_optimizer import RLHDBSCANOptimizer
    
    logger.info("=" * 60)
    logger.info("TEST 1: Basic RL Optimizer Functionality")
    logger.info("=" * 60)
    
    # Create synthetic data
    logger.info("Creating synthetic dataset (1000 samples, 3 clusters)...")
    X, y = make_blobs(n_samples=1000, n_features=50, centers=3, random_state=42)
    
    # Initialize optimizer
    logger.info("Initializing RL optimizer with 10 trials...")
    optimizer = RLHDBSCANOptimizer(
        n_trials=10,
        n_jobs=-1,
        random_state=42,
        exploration_rate=0.3,
        sample_size_for_tuning=1000,
    )
    
    # Run optimization
    logger.info("Running optimization...")
    result = optimizer.optimize(X, verbose=True)
    
    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("OPTIMIZATION RESULTS:")
    logger.info("=" * 60)
    logger.info(result.summary())
    
    # Verify results
    assert result.best_params is not None, "Best params should not be None"
    assert result.best_score > -10, f"Best score too low: {result.best_score}"
    assert len(result.all_trials) == 10, f"Expected 10 trials, got {len(result.all_trials)}"
    
    logger.info("✓ Basic RL optimizer test PASSED\n")
    return True


def test_large_dataset():
    """Test RL optimizer with large dataset."""
    from service.clustering.rl_optimizer import RLHDBSCANOptimizer
    
    logger.info("=" * 60)
    logger.info("TEST 2: Large Dataset (100k samples)")
    logger.info("=" * 60)
    
    # Create larger synthetic data
    logger.info("Creating large synthetic dataset (100,000 samples, 5 clusters)...")
    X, y = make_blobs(n_samples=100000, n_features=50, centers=5, random_state=42)
    
    # Initialize optimizer
    logger.info("Initializing RL optimizer with 15 trials...")
    optimizer = RLHDBSCANOptimizer(
        n_trials=15,
        n_jobs=-1,
        random_state=42,
        exploration_rate=0.3,
        sample_size_for_tuning=30000,  # Use sampling for tuning
    )
    
    # Run optimization
    logger.info("Running optimization (this may take a few minutes)...")
    result = optimizer.optimize(X, verbose=True)
    
    # Get optimized clusterer
    logger.info("\nTraining final model with optimized parameters...")
    clusterer, _ = optimizer.get_optimized_clusterer(X, optimize_first=False)
    
    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("LARGE DATASET RESULTS:")
    logger.info("=" * 60)
    logger.info(result.summary())
    logger.info(f"Final clusterer trained on {len(X)} samples")
    logger.info(f"Number of clusters found: {len(set(clusterer.labels_)) - (1 if -1 in clusterer.labels_ else 0)}")
    logger.info(f"Noise points: {np.sum(clusterer.labels_ == -1)}")
    
    logger.info("✓ Large dataset test PASSED\n")
    return True


def test_integration_with_pipeline():
    """Test integration with LogClusteringPipeline."""
    from service.clustering.cluster_model import LogClusterer
    from service.clustering.config import ClusteringConfig
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    logger.info("=" * 60)
    logger.info("TEST 3: Integration with LogClusterer")
    logger.info("=" * 60)
    
    # Create sample log data
    logger.info("Creating sample log messages...")
    logs = [
        "ERROR: Connection timeout on server1",
        "ERROR: Connection timeout on server2",
        "ERROR: Connection timeout on server3",
        "WARNING: High memory usage detected",
        "WARNING: High memory usage on node5",
        "INFO: Service started successfully",
        "INFO: Service running normally",
        "CRITICAL: Database connection failed",
        "CRITICAL: Database unreachable",
    ] * 200  # Repeat to get ~1800 samples
    
    logger.info(f"Generated {len(logs)} log messages")
    
    # Vectorize logs
    logger.info("Vectorizing logs with TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
    features = vectorizer.fit_transform(logs)
    logger.info(f"Feature matrix shape: {features.shape}")
    
    # Test with RL optimization enabled
    logger.info("\nTesting with RL optimization ENABLED...")
    config = ClusteringConfig()
    clusterer_rl = LogClusterer(config, use_rl_optimization=True, rl_n_trials=10)
    
    labels_rl = clusterer_rl.fit_predict(features)
    n_clusters_rl = len(set(labels_rl)) - (1 if -1 in labels_rl else 0)
    n_noise_rl = np.sum(labels_rl == -1)
    
    logger.info(f"RL-optimized results:")
    logger.info(f"  Clusters found: {n_clusters_rl}")
    logger.info(f"  Noise points: {n_noise_rl}")
    logger.info(f"  Noise ratio: {n_noise_rl / len(labels_rl):.2%}")
    
    if clusterer_rl.optimization_result:
        logger.info(f"  Best optimization score: {clusterer_rl.optimization_result.best_score:.4f}")
    
    # Test prediction
    logger.info("\nTesting prediction on new data...")
    test_logs = [
        "ERROR: Connection timeout on server99",
        "WARNING: High memory usage detected",
        "INFO: Service started successfully",
    ] * 10
    test_features = vectorizer.transform(test_logs)
    test_labels = clusterer_rl.predict(test_features)
    logger.info(f"Predicted labels for {len(test_logs)} test samples: {len(set(test_labels))} unique clusters")
    
    logger.info("✓ Integration test PASSED\n")
    return True


def test_error_handling():
    """Test error handling in RL optimizer."""
    from service.clustering.rl_optimizer import RLHDBSCANOptimizer
    
    logger.info("=" * 60)
    logger.info("TEST 4: Error Handling")
    logger.info("=" * 60)
    
    # Test with very small dataset
    logger.info("Testing with minimal dataset (10 samples)...")
    X_small = np.random.randn(10, 5)
    
    optimizer = RLHDBSCANOptimizer(
        n_trials=5,
        n_jobs=-1,
        random_state=42,
    )
    
    try:
        result = optimizer.optimize(X_small, verbose=False)
        logger.info(f"Optimizer handled small dataset: best_score={result.best_score:.4f}")
        logger.info("✓ Error handling test PASSED\n")
        return True
    except Exception as e:
        logger.error(f"✗ Error handling test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("STARTING RL OPTIMIZATION TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("Basic RL Optimizer", test_rl_optimizer_basic),
        ("Large Dataset", test_large_dataset),
        ("Pipeline Integration", test_integration_with_pipeline),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            logger.exception("Traceback:")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUITE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed}/{len(tests)}")
    logger.info(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        logger.info("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
