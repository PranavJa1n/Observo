"""RL-Based Hyperparameter Optimization for HDBSCAN clustering.

This module implements Reinforcement Learning-inspired hyperparameter optimization
for HDBSCAN to efficiently handle large datasets (600k+ rows).
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from hdbscan import HDBSCAN, validity_index
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)

# Suppress HDBSCAN warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="hdbscan")
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


@dataclass
class HDBSCANParams:
    """Container for HDBSCAN hyperparameters."""
    
    min_cluster_size: int
    min_samples: int
    cluster_selection_epsilon: float
    metric: str = "euclidean"
    cluster_selection_method: str = "eom"
    alpha: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_cluster_size": self.min_cluster_size,
            "min_samples": self.min_samples,
            "cluster_selection_epsilon": self.cluster_selection_epsilon,
            "metric": self.metric,
            "cluster_selection_method": self.cluster_selection_method,
            "alpha": self.alpha,
        }


@dataclass
class OptimizationResult:
    """Results from hyperparameter optimization."""
    
    best_params: HDBSCANParams
    best_score: float
    all_trials: List[Dict[str, Any]]
    optimization_history: List[float]
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Optimization Complete:\n"
            f"  Best Score: {self.best_score:.4f}\n"
            f"  Best Parameters:\n"
            f"    min_cluster_size: {self.best_params.min_cluster_size}\n"
            f"    min_samples: {self.best_params.min_samples}\n"
            f"    cluster_selection_epsilon: {self.best_params.cluster_selection_epsilon:.4f}\n"
            f"    alpha: {self.best_params.alpha:.4f}\n"
            f"  Total Trials: {len(self.all_trials)}\n"
        )


class RLHDBSCANOptimizer:
    """RL-inspired optimizer for HDBSCAN hyperparameters.
    
    Uses a reward-based approach with exploration-exploitation balance
    to find optimal HDBSCAN parameters for large-scale clustering.
    """
    
    def __init__(
        self,
        n_trials: int = 20,
        n_jobs: int = -1,
        random_state: Optional[int] = 42,
        exploration_rate: float = 0.3,
        sample_size_for_tuning: int = 50000,
    ):
        """Initialize the RL-based optimizer.
        
        Args:
            n_trials: Number of optimization trials to run
            n_jobs: Number of parallel jobs for HDBSCAN (-1 for all cores)
            random_state: Random seed for reproducibility
            exploration_rate: Rate of exploration vs exploitation (0-1)
            sample_size_for_tuning: Sample size for hyperparameter tuning
        """
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.exploration_rate = exploration_rate
        self.sample_size_for_tuning = sample_size_for_tuning
        self.rng = np.random.RandomState(random_state)
        
        # RL-style state tracking
        self.trial_history: List[Dict[str, Any]] = []
        self.reward_history: List[float] = []
        self.best_reward = -np.inf
        self.best_params: Optional[HDBSCANParams] = None
        
        # Parameter search space
        self.param_space = {
            "min_cluster_size": (5, 100),
            "min_samples": (1, 50),
            "cluster_selection_epsilon": (0.0, 0.5),
            "alpha": (0.5, 2.0),
        }
    
    def _calculate_reward(
        self,
        clusterer: HDBSCAN,
        features: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """Calculate reward for a clustering result.
        
        Combines multiple metrics into a single reward signal:
        - Cluster validity index (DBCV)
        - Silhouette score
        - Noise penalty
        - Number of clusters penalty
        
        Args:
            clusterer: Trained HDBSCAN instance
            features: Feature matrix
            labels: Cluster labels
            
        Returns:
            Reward score (higher is better)
        """
        try:
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = np.sum(labels == -1)
            noise_ratio = n_noise / len(labels) if len(labels) > 0 else 1.0
            
            # Base reward components
            reward = 0.0
            
            # Component 1: DBCV (Density-Based Clustering Validation)
            # This is the primary quality metric for HDBSCAN
            try:
                dbcv = validity_index(features, labels, metric="euclidean")
                if not np.isnan(dbcv) and not np.isinf(dbcv):
                    reward += 2.0 * max(dbcv, 0)  # Weight: 2.0
            except Exception as e:
                logger.debug(f"DBCV calculation failed: {e}")
            
            # Component 2: Silhouette score (if enough clusters)
            if n_clusters >= 2 and n_noise < len(labels):
                try:
                    valid_mask = labels != -1
                    if np.sum(valid_mask) > 1:
                        silhouette = silhouette_score(
                            features[valid_mask],
                            labels[valid_mask],
                            sample_size=min(10000, np.sum(valid_mask)),
                        )
                        reward += 1.0 * max(silhouette, 0)  # Weight: 1.0
                except Exception as e:
                    logger.debug(f"Silhouette calculation failed: {e}")
            
            # Component 3: Calinski-Harabasz score (variance ratio)
            if n_clusters >= 2 and n_noise < len(labels):
                try:
                    valid_mask = labels != -1
                    if np.sum(valid_mask) > n_clusters:
                        ch_score = calinski_harabasz_score(
                            features[valid_mask],
                            labels[valid_mask],
                        )
                        # Normalize to 0-1 range (typical values: 10-1000)
                        reward += 0.5 * min(ch_score / 1000, 1.0)  # Weight: 0.5
                except Exception as e:
                    logger.debug(f"Calinski-Harabasz calculation failed: {e}")
            
            # Penalty 1: Too much noise
            noise_penalty = noise_ratio * 1.5
            reward -= noise_penalty
            
            # Penalty 2: Too many or too few clusters
            if n_clusters < 2:
                reward -= 1.0  # Penalize no meaningful clusters
            elif n_clusters > 50:
                reward -= 0.5 * (n_clusters - 50) / 50  # Penalize excessive fragmentation
            
            # Penalty 3: Davies-Bouldin index (lower is better)
            if n_clusters >= 2 and n_noise < len(labels):
                try:
                    valid_mask = labels != -1
                    if np.sum(valid_mask) > n_clusters:
                        db_score = davies_bouldin_score(
                            features[valid_mask],
                            labels[valid_mask],
                        )
                        # Typical range: 0-3, lower is better
                        reward -= 0.3 * min(db_score / 3.0, 1.0)  # Weight: 0.3
                except Exception as e:
                    logger.debug(f"Davies-Bouldin calculation failed: {e}")
            
            return float(reward)
            
        except Exception as e:
            logger.error(f"Error calculating reward: {e}")
            return -10.0  # Heavy penalty for failure
    
    def _sample_params(self, trial_num: int) -> HDBSCANParams:
        """Sample hyperparameters using exploration-exploitation strategy.
        
        Args:
            trial_num: Current trial number
            
        Returns:
            Sampled hyperparameters
        """
        # Exploration: Random sampling
        if self.rng.random() < self.exploration_rate or trial_num < 3:
            min_cluster_size = self.rng.randint(
                self.param_space["min_cluster_size"][0],
                self.param_space["min_cluster_size"][1] + 1,
            )
            min_samples = self.rng.randint(
                self.param_space["min_samples"][0],
                self.param_space["min_samples"][1] + 1,
            )
            cluster_selection_epsilon = self.rng.uniform(
                self.param_space["cluster_selection_epsilon"][0],
                self.param_space["cluster_selection_epsilon"][1],
            )
            alpha = self.rng.uniform(
                self.param_space["alpha"][0],
                self.param_space["alpha"][1],
            )
        else:
            # Exploitation: Sample around best params with noise
            if self.best_params is None:
                return self._sample_params(0)  # Fallback to exploration
            
            # Add Gaussian noise to best parameters
            min_cluster_size = int(np.clip(
                self.best_params.min_cluster_size + self.rng.randn() * 10,
                self.param_space["min_cluster_size"][0],
                self.param_space["min_cluster_size"][1],
            ))
            min_samples = int(np.clip(
                self.best_params.min_samples + self.rng.randn() * 5,
                self.param_space["min_samples"][0],
                self.param_space["min_samples"][1],
            ))
            cluster_selection_epsilon = float(np.clip(
                self.best_params.cluster_selection_epsilon + self.rng.randn() * 0.05,
                self.param_space["cluster_selection_epsilon"][0],
                self.param_space["cluster_selection_epsilon"][1],
            ))
            alpha = float(np.clip(
                self.best_params.alpha + self.rng.randn() * 0.2,
                self.param_space["alpha"][0],
                self.param_space["alpha"][1],
            ))
        
        return HDBSCANParams(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            cluster_selection_epsilon=cluster_selection_epsilon,
            alpha=alpha,
        )
    
    def _prepare_sample(self, features: np.ndarray) -> np.ndarray:
        """Prepare a sample for hyperparameter tuning.
        
        Args:
            features: Full feature matrix
            
        Returns:
            Sampled features for tuning
        """
        n_samples = features.shape[0]
        
        if n_samples <= self.sample_size_for_tuning:
            return features
        
        # Stratified sampling for better representation
        indices = self.rng.choice(
            n_samples,
            size=self.sample_size_for_tuning,
            replace=False,
        )
        return features[indices]
    
    def optimize(
        self,
        features: np.ndarray,
        verbose: bool = True,
    ) -> OptimizationResult:
        """Run RL-based hyperparameter optimization.
        
        Args:
            features: Feature matrix (can be full dataset or sample)
            verbose: Whether to print progress
            
        Returns:
            Optimization results with best parameters
        """
        if verbose:
            logger.info(f"Starting RL-based HDBSCAN optimization with {self.n_trials} trials")
            logger.info(f"Feature matrix shape: {features.shape}")
        
        # Prepare sample for tuning if dataset is too large
        sample_features = self._prepare_sample(features)
        
        if verbose and sample_features.shape[0] != features.shape[0]:
            logger.info(f"Using sample of {sample_features.shape[0]} rows for tuning")
        
        # Convert to dense array if sparse
        if hasattr(sample_features, "toarray"):
            sample_features = sample_features.toarray()
        
        # Run trials
        for trial_num in range(self.n_trials):
            try:
                # Sample parameters
                params = self._sample_params(trial_num)
                
                # Train HDBSCAN
                clusterer = HDBSCAN(
                    min_cluster_size=params.min_cluster_size,
                    min_samples=params.min_samples,
                    cluster_selection_epsilon=params.cluster_selection_epsilon,
                    metric=params.metric,
                    cluster_selection_method=params.cluster_selection_method,
                    alpha=params.alpha,
                    core_dist_n_jobs=self.n_jobs,
                )
                
                labels = clusterer.fit_predict(sample_features)
                
                # Calculate reward
                reward = self._calculate_reward(clusterer, sample_features, labels)
                
                # Update history
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                n_noise = np.sum(labels == -1)
                
                trial_info = {
                    "trial": trial_num,
                    "params": params.to_dict(),
                    "reward": reward,
                    "n_clusters": n_clusters,
                    "n_noise": int(n_noise),
                    "noise_ratio": float(n_noise / len(labels)),
                }
                self.trial_history.append(trial_info)
                self.reward_history.append(reward)
                
                # Update best params
                if reward > self.best_reward:
                    self.best_reward = reward
                    self.best_params = params
                    if verbose:
                        logger.info(
                            f"Trial {trial_num + 1}/{self.n_trials}: "
                            f"New best reward = {reward:.4f} "
                            f"(clusters={n_clusters}, noise={n_noise})"
                        )
                else:
                    if verbose:
                        logger.info(
                            f"Trial {trial_num + 1}/{self.n_trials}: "
                            f"Reward = {reward:.4f} "
                            f"(clusters={n_clusters}, noise={n_noise})"
                        )
                
            except Exception as e:
                logger.error(f"Trial {trial_num} failed: {e}")
                self.trial_history.append({
                    "trial": trial_num,
                    "params": None,
                    "reward": -10.0,
                    "error": str(e),
                })
                self.reward_history.append(-10.0)
        
        if self.best_params is None:
            raise RuntimeError("Optimization failed: No successful trials")
        
        result = OptimizationResult(
            best_params=self.best_params,
            best_score=self.best_reward,
            all_trials=self.trial_history,
            optimization_history=self.reward_history,
        )
        
        if verbose:
            logger.info("\n" + result.summary())
        
        return result
    
    def get_optimized_clusterer(
        self,
        features: np.ndarray,
        optimize_first: bool = True,
    ) -> Tuple[HDBSCAN, OptimizationResult]:
        """Get an optimized HDBSCAN clusterer.
        
        Args:
            features: Feature matrix for optimization
            optimize_first: Whether to run optimization (False uses existing best params)
            
        Returns:
            Tuple of (trained HDBSCAN clusterer, optimization result)
        """
        if optimize_first or self.best_params is None:
            result = self.optimize(features, verbose=True)
        else:
            if self.best_params is None:
                raise RuntimeError("No best params available. Run optimize() first.")
            result = OptimizationResult(
                best_params=self.best_params,
                best_score=self.best_reward,
                all_trials=self.trial_history,
                optimization_history=self.reward_history,
            )
        
        # Create and train final clusterer with best params
        clusterer = HDBSCAN(
            min_cluster_size=result.best_params.min_cluster_size,
            min_samples=result.best_params.min_samples,
            cluster_selection_epsilon=result.best_params.cluster_selection_epsilon,
            metric=result.best_params.metric,
            cluster_selection_method=result.best_params.cluster_selection_method,
            alpha=result.best_params.alpha,
            core_dist_n_jobs=self.n_jobs,
        )
        
        # Train on full dataset
        logger.info("Training final HDBSCAN model with optimized parameters on full dataset...")
        if hasattr(features, "toarray"):
            features = features.toarray()
        
        clusterer.fit(features)
        logger.info("Training complete!")
        
        return clusterer, result
