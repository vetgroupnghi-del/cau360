"""
CAU360 System Configuration & Parameters
"""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = "CAU360 - Market Intelligence System"
    VERSION: str = "1.0.0"
    DB_PATH: str = os.getenv("DB_PATH", "/tmp/cau360.db")
    
    # Half-life for recency decay (in hours) - Fast-moving agricultural spot market
    RECENCY_HALF_LIFE_HOURS: float = 18.0
    
    # Freshness threshold limits (in minutes)
    FRESHNESS_LIVE_MINUTES: int = 180       # <= 3 hours -> LIVE
    FRESHNESS_RECENT_MINUTES: int = 720     # <= 12 hours -> RECENT
    FRESHNESS_DELAYED_MINUTES: int = 1440   # <= 24 hours -> DELAYED
    # > 24 hours -> STALE (excluded from today consensus)
    
    # Data Confidence Thresholds
    CONFIDENCE_VERY_HIGH: float = 90.0
    CONFIDENCE_HIGH: float = 75.0
    CONFIDENCE_MODERATE: float = 60.0
    CONFIDENCE_LOW: float = 40.0
    # < 40 -> VERY LOW (Do not show as consensus, flag as low confidence signal)
    
    # Outlier threshold (MAD multiplier)
    OUTLIER_K_MAD: float = 3.0
    OUTLIER_MIN_EPSILON_PCT: float = 0.02   # 2% minimum threshold band to prevent MAD=0 breakdown
    
    # Theoretical Fresh-to-Dry Conversion Defaults
    DEFAULT_RATIO_MIN: float = 4.0
    DEFAULT_RATIO_MID: float = 4.5
    DEFAULT_RATIO_MAX: float = 5.0
    
    # Secret / API configs
    API_V1_STR: str = "/api/v1"

settings = Settings()
