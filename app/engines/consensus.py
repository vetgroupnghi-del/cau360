"""
Weighted Median Consensus & Market Data Confidence Engine (Rules 21, 22, 23, 24, 109)
"""
import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.taxonomy import TRANSACTION_WEIGHTS, AUTHORITY_WEIGHTS, TransactionType

class ConsensusEngine:
    @classmethod
    def calculate_observation_weight(
        cls,
        source_authority: str,
        transaction_type: str,
        observed_at: datetime,
        is_verified: bool = False,
        is_duplicate: bool = False
    ) -> float:
        """
        Calculates composite weight for an individual observation (Rule 21).
        W = w_source * w_tx * exp(-age_hours / half_life) * w_verified * w_duplicate
        """
        # Source weight
        w_source = AUTHORITY_WEIGHTS.get(source_authority, 0.50)
        
        # Transaction weight
        w_tx = TRANSACTION_WEIGHTS.get(transaction_type, 0.35)
        
        # Recency exponential decay
        now = (datetime.utcnow() + timedelta(hours=7))
        age_hours = max(0.0, (now - observed_at).total_seconds() / 3600.0)
        w_recency = math.exp(-age_hours / settings.RECENCY_HALF_LIFE_HOURS)
        
        # Verification weight
        w_verify = 1.2 if is_verified else 1.0
        
        # Duplicate penalty (if repost, downweight by 80%)
        w_dup = 0.2 if is_duplicate else 1.0
        
        composite_weight = w_source * w_tx * w_recency * w_verify * w_dup
        return max(0.001, composite_weight)

    @classmethod
    def calculate_weighted_quantiles(
        cls,
        values: List[float],
        weights: List[float],
        quantiles: List[float] = [0.10, 0.20, 0.50, 0.80, 0.90]
    ) -> Dict[str, float]:
        """
        Calculates Weighted Quantiles (Weighted Median = P50, Low = P20, High = P80).
        """
        if not values:
            return {f"p{int(q*100)}": 0.0 for q in quantiles}
            
        if len(values) == 1:
            val = float(values[0])
            return {f"p{int(q*100)}": val for q in quantiles}
            
        data = sorted(zip(values, weights), key=lambda x: x[0])
        sorted_vals = np.array([x[0] for x in data], dtype=float)
        sorted_weights = np.array([x[1] for x in data], dtype=float)
        
        total_w = np.sum(sorted_weights)
        if total_w <= 0:
            total_w = 1.0
            sorted_weights = np.ones_like(sorted_weights)
            
        cum_weights = np.cumsum(sorted_weights) / total_w
        
        results = {}
        for q in quantiles:
            idx = np.searchsorted(cum_weights, q)
            idx = min(idx, len(sorted_vals) - 1)
            results[f"p{int(q*100)}"] = round(float(sorted_vals[idx]), 2)
            
        return results

    @classmethod
    def calculate_market_confidence(
        cls,
        observations: List[Dict[str, Any]],
        quantiles: Dict[str, float]
    ) -> Tuple[float, str]:
        """
        Data Confidence Score (Rule 23, 24):
        25% source diversity + 25% confirmed transaction confirmation +
        20% cross-source agreement + 15% recency + 10% sample size + 5% specification completeness
        """
        n = len(observations)
        if n == 0:
            return 0.0, "NO_DATA"
            
        # 1. Source Diversity (distinct sources / max(5, n))
        sources = set(o.get("source_id") for o in observations if o.get("source_id"))
        diversity = min(1.0, len(sources) / 4.0) * 100.0
        
        # 2. Confirmed Transaction Confirmation
        confirmed_count = sum(1 for o in observations if o.get("transaction_type") in [
            TransactionType.CONFIRMED_TRANSACTION.value,
            TransactionType.CONFIRMED_PURCHASE.value
        ])
        tx_confirmation = min(1.0, (confirmed_count * 2.0) / max(1, n)) * 100.0
        
        # 3. Cross-Source Agreement (Spread P80 - P20 relative to P50)
        p50 = quantiles.get("p50", 1.0)
        p20 = quantiles.get("p20", p50)
        p80 = quantiles.get("p80", p50)
        if p50 > 0:
            spread_pct = (p80 - p20) / p50
            # Narrow spread (< 5%) = 100 score, wide spread (> 20%) = low score
            agreement = max(0.0, min(100.0, (1.0 - (spread_pct / 0.20)) * 100.0))
        else:
            agreement = 50.0
            
        # 4. Recency (average recency weight)
        avg_recency = np.mean([o.get("recency_weight", 0.5) for o in observations]) * 100.0
        
        # 5. Sample Size (n >= 10 is 100%)
        sample_size_score = min(1.0, n / 8.0) * 100.0
        
        # 6. Specification Completeness
        spec_complete = sum(1 for o in observations if o.get("grade") or o.get("process")) / max(1, n) * 100.0
        
        # Weighted Total
        total_score = (
            0.25 * diversity +
            0.25 * tx_confirmation +
            0.20 * agreement +
            0.15 * avg_recency +
            0.10 * sample_size_score +
            0.05 * spec_complete
        )
        total_score = round(min(100.0, max(0.0, total_score)), 1)
        
        # Label
        if total_score >= settings.CONFIDENCE_VERY_HIGH:
            label = "VERY HIGH"
        elif total_score >= settings.CONFIDENCE_HIGH:
            label = "HIGH"
        elif total_score >= settings.CONFIDENCE_MODERATE:
            label = "MODERATE"
        elif total_score >= settings.CONFIDENCE_LOW:
            label = "LOW"
        else:
            label = "VERY LOW"
            
        return total_score, label
