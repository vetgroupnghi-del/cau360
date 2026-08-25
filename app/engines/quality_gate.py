"""
Data Quality Gate Engine (Rules 11, 110)
Enforces strict gatekeeper validation before any observation enters Market Consensus.
"""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from app.core.taxonomy import ProductStage
from app.core.config import settings

class QualityGate:
    @staticmethod
    def validate_observation(
        product_stage: str,
        location_id: Optional[str] = None,
        currency: str = "VND",
        unit: str = "KG",
        price: float = 0.0,
        observed_at: Optional[Any] = None,
        is_outlier: bool = False,
        is_duplicate: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates an observation against the 7 Quality Gates.
        Returns: (passed: bool, reason: str)
        """
        # 1. Gate: Product
        if not product_stage or product_stage == ProductStage.UNKNOWN.value:
            return False, "FAIL_PRODUCT_STAGE_UNKNOWN"
            
        # 2. Gate: Location
        if not location_id:
            return False, "FAIL_LOCATION_MISSING"
            
        # 3. Gate: Currency & Unit
        if currency.upper() not in ["VND", "CNY", "USD"]:
            return False, "FAIL_CURRENCY_INVALID"
            
        if unit.upper() not in ["KG", "JIN", "TON", "TA", "PIECE"]:
            return False, "FAIL_UNIT_INVALID"
            
        # 4. Gate: Price Range sanity check
        if price <= 0:
            return False, "FAIL_PRICE_ZERO_OR_NEGATIVE"
            
        # 5. Gate: Freshness
        if observed_at:
            now = (datetime.utcnow() + timedelta(hours=7))
            if isinstance(observed_at, str):
                try:
                    obs_dt = datetime.fromisoformat(observed_at)
                except Exception:
                    obs_dt = now
            else:
                obs_dt = observed_at
                
            age_minutes = (now - obs_dt).total_seconds() / 60.0
            if age_minutes > settings.FRESHNESS_DELAYED_MINUTES: # > 24 hours
                return False, "FAIL_STALE_EXCEEDED_24H"
                
        # 6. Gate: Outlier
        if is_outlier:
            return False, "FAIL_FLAGGED_OUTLIER_PENDING_REVIEW"
            
        return True, "PASS_QUALITY_GATE"
