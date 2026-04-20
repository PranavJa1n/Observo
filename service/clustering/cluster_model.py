"""Wrapper around HDBSCAN for log clustering."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from hdbscan import HDBSCAN
from hdbscan import prediction as hdbscan_prediction

from .config import ClusteringConfig
from .rl_optimizer import RLHDBSCANOptimizer, OptimizationResult

logger = logging.getLogger(__name__)


class LogClusterer:
    """Encapsulates HDBSCAN fit and inference routines with RL-based optimization."""

    def __init__(
        self,
        config: ClusteringConfig | None = None,
        use_rl_optimization: bool = True,
        rl_n_trials: int = 20,
    ) -> None:
        """Initialize LogClusterer with optional RL-based optimization.
        
        Args:
            config: Clustering configuration
            use_rl_optimization: Whether to use RL-based hyperparameter optimization
            rl_n_trials: Number of trials for RL optimization
        """
        config = config or ClusteringConfig()
        self.config = config
        self.use_rl_optimization = use_rl_optimization
        self.rl_n_trials = rl_n_trials
        
        # Clusterer will be initialized during fit_predict
        self.clusterer: Optional[HDBSCAN] = None
        
        self.is_trained = False
        self.good_cluster_id: Optional[int] = None
        self.optimization_result: Optional[OptimizationResult] = None

    def fit_predict(self, features) -> np.ndarray:
        """Fit the clusterer and predict labels.
        
        If RL optimization is enabled, will automatically optimize hyperparameters
        before training the final model.
        
        Args:
            features: Feature matrix (can be sparse or dense)
            
        Returns:
            Cluster labels
        """
        try:
            if self.use_rl_optimization and self.clusterer is None:
                logger.info("Using RL-based hyperparameter optimization for HDBSCAN")
                
                # Initialize optimizer with error handling
                try:
                    optimizer = RLHDBSCANOptimizer(
                        n_trials=self.rl_n_trials,
                        n_jobs=-1,
                        random_state=42,
                        exploration_rate=0.3,
                        sample_size_for_tuning=min(50000, features.shape[0]),
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize RL optimizer: {e}")
                    raise RuntimeError(f"RL optimizer initialization failed: {e}")
                
                # Run optimization and get optimized clusterer
                try:
                    self.clusterer, self.optimization_result = optimizer.get_optimized_clusterer(
                        features,
                        optimize_first=True,
                    )
                    
                    logger.info("RL optimization completed successfully")
                    logger.info(f"Best parameters: {self.optimization_result.best_params.to_dict()}")
                    
                except Exception as e:
                    logger.error(f"RL optimization failed: {e}")
                    logger.warning("Falling back to default hyperparameters")
                    
                    # Fallback to default parameters
                    self.clusterer = HDBSCAN(
                        min_cluster_size=self.config.min_cluster_size,
                        min_samples=self.config.min_samples,
                        cluster_selection_epsilon=self.config.cluster_selection_epsilon,
                        metric="euclidean",
                        cluster_selection_method="eom",
                        core_dist_n_jobs=-1,
                    )
                    
                    # Train with default params
                    dense = features.toarray() if hasattr(features, "toarray") else np.asarray(features)
                    labels = self.clusterer.fit_predict(dense)
                    self.is_trained = True
                    return labels
                
                # Get labels from the already-trained optimized clusterer
                labels = self.clusterer.labels_
                self.is_trained = True
                return labels
                
            else:
                # Original behavior without RL optimization or if already initialized
                logger.info("Using default HDBSCAN hyperparameters (RL optimization disabled)")
                
                # Initialize clusterer if not done yet
                if self.clusterer is None:
                    self.clusterer = HDBSCAN(
                        min_cluster_size=self.config.min_cluster_size,
                        min_samples=self.config.min_samples,
                        cluster_selection_epsilon=self.config.cluster_selection_epsilon,
                        metric="euclidean",
                        cluster_selection_method="eom",
                        core_dist_n_jobs=-1,
                    )
                
                dense = features.toarray() if hasattr(features, "toarray") else np.asarray(features)
                labels = self.clusterer.fit_predict(dense)
                self.is_trained = True
                return labels
                
        except Exception as e:
            logger.error(f"Critical error in fit_predict: {e}")
            raise RuntimeError(f"Clustering failed: {e}")

    def predict(self, features) -> np.ndarray:
        """Predict cluster labels for new data.
        
        Args:
            features: Feature matrix (can be sparse or dense)
            
        Returns:
            Predicted cluster labels
        """
        if not self.is_trained:
            raise RuntimeError("Clusterer has not been trained")

        try:
            dense = features.toarray() if hasattr(features, "toarray") else np.asarray(features)
            labels, _ = hdbscan_prediction.approximate_predict(self.clusterer, dense)
            return labels
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Failed to predict labels: {e}")
    
    def get_optimization_summary(self) -> str:
        """Get a summary of the RL optimization results.
        
        Returns:
            Human-readable summary string
        """
        if self.optimization_result is None:
            return "No optimization performed (RL optimization was disabled or failed)"
        
        return self.optimization_result.summary()
