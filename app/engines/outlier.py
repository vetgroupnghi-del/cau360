"""
Adjusted MAD & Robust Outlier Detection Engine (Rules 20, 104)
"""
import numpy as np
from typing import List, Tuple, Dict, Any
from app.core.config import settings

class OutlierEngine:
    @staticmethod
    def detect_outliers_adjusted_mad(
        prices: List[float],
        k: float = settings.OUTLIER_K_MAD,
        min_epsilon_pct: float = settings.OUTLIER_MIN_EPSILON_PCT
    ) -> List[bool]:
        """
        Detects outliers using Adjusted MAD.
        Returns a list of boolean flags (True = outlier, False = normal).
        """
        if not prices or len(prices) < 3:
            # Not enough data points to reliably flag outliers
            return [False] * len(prices)
            
        arr = np.array(prices, dtype=float)
        med = float(np.median(arr))
        
        # Standard MAD
        deviations = np.abs(arr - med)
        raw_mad = float(np.median(deviations))
        
        # Small sample fallback: ensure MAD is never zero if median > 0
        min_epsilon = med * min_epsilon_pct
        adjusted_mad = max(raw_mad, min_epsilon)
        
        outlier_flags = []
        for p in arr:
            diff = abs(p - med)
            if diff > k * adjusted_mad:
                outlier_flags.append(True)
            else:
                outlier_flags.append(False)
                
        return outlier_flags

    @classmethod
    def evaluate_observation(cls, price: float, cohort_prices: List[float]) -> Tuple[bool, str]:
        """
        Checks if a single incoming price is an outlier compared to its contemporary cohort.
        """
        if not cohort_prices or len(cohort_prices) < 3:
            return False, "INSUFFICIENT_COHORT"
            
        all_prices = cohort_prices + [price]
        flags = cls.detect_outliers_adjusted_mad(all_prices)
        is_outlier = flags[-1]
        
        reason = "OUTLIER_ADJUSTED_MAD_EXCEEDED" if is_outlier else "NORMAL"
        return is_outlier, reason
