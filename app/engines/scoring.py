"""
Specialized Market Indices Engine (Rules 31 - 36)
- WSSI: Weather Supply Stress Index (Non-linear saturation)
- Harvestability Score (0-100)
- CBPI: Chinese Buying Pressure Index + Momentum Tracker
- MSI: Market Supply Index
"""
import math
from typing import Dict, Any, Optional

class ScoringEngine:
    @staticmethod
    def calculate_wssi_and_harvestability(
        rain_24h_mm: float = 0.0,
        rain_72h_mm: float = 0.0,
        forecast_rain_72h_mm: float = 0.0,
        wind_speed_kmh: float = 0.0,
        has_typhoon_warning: bool = False,
        has_flood_warning: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates Weather Supply Stress Index (0-100) and Harvestability (0-100).
        Uses non-linear sigmoid/saturation response curves.
        """
        # 1. Non-linear Rain Stress (Logistic sigmoid saturation above 40mm)
        effective_rain = (rain_24h_mm * 0.4) + (rain_72h_mm * 0.3) + (forecast_rain_72h_mm * 0.3)
        rain_stress = 100.0 / (1.0 + math.exp(-0.05 * (effective_rain - 50.0)))
        
        # 2. Wind Stress (above 45 km/h tree damage & harvest halt occurs)
        wind_stress = min(100.0, max(0.0, (wind_speed_kmh - 20.0) * 2.0))
        
        # 3. Severe Warnings
        warning_boost = 0.0
        if has_typhoon_warning:
            warning_boost += 35.0
        if has_flood_warning:
            warning_boost += 25.0
            
        # Composite WSSI
        wssi = (0.50 * rain_stress) + (0.25 * wind_stress) + warning_boost
        wssi = round(min(100.0, max(0.0, wssi)), 1)
        
        # WSSI Status
        if wssi <= 20.0:
            status = "NORMAL"
        elif wssi <= 40.0:
            status = "WATCH"
        elif wssi <= 60.0:
            status = "MODERATE STRESS"
        elif wssi <= 80.0:
            status = "HIGH STRESS"
        else:
            status = "EXTREME"
            
        # Harvestability Score (Inverse of weather stress, dampened by warnings)
        harvestability = round(max(0.0, 100.0 - (wssi * 0.95)), 1)
        
        return {
            "wssi": wssi,
            "wssi_status": status,
            "harvestability": harvestability,
            "emergency_mode": (wssi >= 70.0 or has_typhoon_warning)
        }

    @staticmethod
    def calculate_cbpi(
        buyer_signals_count: int,
        confirmed_tx_count: int,
        bid_hikes_count: int,
        hunan_factory_utilization_pct: float = 75.0,
        historical_baseline: float = 10.0
    ) -> float:
        """
        Calculates Chinese Buying Pressure Index (0-100).
        """
        # Activity volume relative to baseline
        activity_ratio = (buyer_signals_count + (confirmed_tx_count * 2.0) + (bid_hikes_count * 3.0)) / max(1.0, historical_baseline)
        activity_score = min(100.0, activity_ratio * 35.0)
        
        # Industrial demand factor
        demand_score = min(100.0, hunan_factory_utilization_pct)
        
        # Composite CBPI
        cbpi = (0.65 * activity_score) + (0.35 * demand_score)
        return round(min(100.0, max(0.0, cbpi)), 1)

    @staticmethod
    def calculate_msi(
        seller_post_count: int,
        available_volume_tons: float,
        active_drying_kilns: int,
        baseline_volume_tons: float = 50.0
    ) -> Dict[str, Any]:
        """
        Calculates Market Supply Index (0-100).
        High MSI = Supply abundant, Low MSI = Supply tight.
        """
        vol_score = min(100.0, (available_volume_tons / max(1.0, baseline_volume_tons)) * 50.0)
        post_score = min(100.0, seller_post_count * 10.0)
        
        msi = (0.70 * vol_score) + (0.30 * post_score)
        msi = round(min(100.0, max(0.0, msi)), 1)
        
        if msi >= 70.0:
            status = "SUPPLY ABUNDANT"
        elif msi >= 40.0:
            status = "BALANCED"
        else:
            status = "SUPPLY TIGHT"
            
        return {
            "msi": msi,
            "msi_status": status
        }
