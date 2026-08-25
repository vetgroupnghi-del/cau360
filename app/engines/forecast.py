"""
CAU360 Forecast Engine V1 & Scenario Builder (Rules 46 - 60)
3-Day & 7-Day Quantile Forecasts (P10, P50, P90) with Explainability & Invalidation Triggers.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.models.schemas import ForecastItem, ScenarioProb

class ForecastEngineV1:
    MODEL_VERSION = "ForecastEngine_v1.0_RuleQuantile"

    @classmethod
    def generate_forecast(
        cls,
        horizon_days: int, # 3 or 7
        current_price_p50: float,
        price_1d_pct: float,
        price_3d_pct: float,
        cbpi: float,
        cbpi_momentum_3d: float,
        wssi: float,
        msi: float,
        fx_change_pct: float = 0.0,
        data_confidence: float = 80.0
    ) -> ForecastItem:
        """
        Generates structured 3D or 7D Quantile Forecast with Scenarios & Invalidation Conditions.
        """
        now = (datetime.utcnow() + timedelta(hours=7))
        target_date = (now + timedelta(days=horizon_days)).strftime("%Y-%m-%d")
        
        # 1. Evaluate Net Market Pressure Signal (-1.0 to +1.0)
        w_cbpi = (cbpi - 50.0) / 50.0 # -1 to 1
        w_cbpi_mom = min(1.0, max(-1.0, cbpi_momentum_3d / 15.0))
        w_weather = (wssi - 30.0) / 70.0 # >30 creates upward supply squeeze pressure
        w_supply = (50.0 - msi) / 50.0 # low MSI (<50) = upward pressure
        w_mom = min(1.0, max(-1.0, price_3d_pct / 0.05))
        
        if horizon_days == 3:
            net_signal = (0.35 * w_cbpi_mom) + (0.25 * w_weather) + (0.20 * w_supply) + (0.20 * w_mom)
            expected_drift_pct = net_signal * 0.04 # max +/- 4% in 3 days
            spread_band_pct = 0.030 # +/- 3.0% quantile spread
            up_threshold = 0.012
            strong_up_threshold = 0.030
        else: # 7 days
            net_signal = (0.30 * w_cbpi) + (0.25 * w_weather) + (0.25 * w_supply) + (0.20 * w_mom)
            expected_drift_pct = net_signal * 0.08 # max +/- 8% in 7 days
            spread_band_pct = 0.060 # +/- 6.0% quantile spread
            up_threshold = 0.025
            strong_up_threshold = 0.055
            
        # 2. Determine Direction Label
        if expected_drift_pct >= up_threshold:
            direction = "STRONG_UP" if expected_drift_pct >= strong_up_threshold else "UP"
        elif expected_drift_pct <= -up_threshold:
            direction = "STRONG_DOWN" if expected_drift_pct <= -strong_up_threshold else "DOWN"
        else:
            direction = "SIDEWAYS"
            
        # 3. Calculate Quantiles (P10, P50, P90)
        p50 = round(current_price_p50 * (1.0 + expected_drift_pct), 0)
        p10 = round(p50 * (1.0 - spread_band_pct), 0)
        p90 = round(p50 * (1.0 + spread_band_pct), 0)
        
        # 4. Determine Scenarios & Probabilities
        if direction in ["UP", "STRONG_UP"]:
            base_prob = 0.60
            bull_prob = 0.25
            bear_prob = 0.15
        elif direction in ["DOWN", "STRONG_DOWN"]:
            base_prob = 0.60
            bull_prob = 0.15
            bear_prob = 0.25
        else:
            base_prob = 0.70
            bull_prob = 0.15
            bear_prob = 0.15
            
        # 5. Extract Explainability Drivers
        positive_drivers = []
        negative_drivers = []
        invalidation = []
        
        if cbpi_momentum_3d > 5.0:
            positive_drivers.append(f"Áp lực mua từ Trung Quốc (CBPI) tăng mạnh +{cbpi_momentum_3d:.1f} điểm trong 3 ngày qua.")
            invalidation.append("CBPI giảm đột ngột > 10 điểm trong 24h tới.")
        if wssi >= 50.0:
            positive_drivers.append(f"Chỉ số rủi ro thời tiết Hải Nam (WSSI={wssi:.0f}) ở mức cao, cản trở thu hoạch tại Vạn Ninh.")
            invalidation.append("Cảnh báo bão/mưa tại Hải Nam được gỡ bỏ sớm hơn dự kiến.")
        if msi < 40.0:
            positive_drivers.append("Nguồn cung cau khô tồn kho tại các vựa và lò sấy nội địa đang ở mức khan hiếm.")
        if price_3d_pct > 0.02:
            positive_drivers.append(f"Quán tính giá 3 ngày duy trì đà tăng (+{price_3d_pct*100:.1f}%).")
            
        if cbpi_momentum_3d < -5.0:
            negative_drivers.append(f"Nhu cầu thu mua chững lại, CBPI giảm {cbpi_momentum_3d:.1f} điểm.")
        if msi >= 65.0:
            negative_drivers.append("Lượng hàng về lò sấy dồi dào, áp lực xả hàng ngắn hạn.")
        if not negative_drivers:
            negative_drivers.append("Tỷ giá CNY/VND duy trì ổn định, logistics thông suốt tại các cửa khẩu.")
            
        if not invalidation:
            invalidation.append("Xuất hiện lượng hàng lớn đột biến từ các vùng thu hoạch mới.")
            invalidation.append("Thương lái Trung Quốc dừng báo giá mua đột ngột.")

        # Forecast Confidence Score (Rule 55)
        forecast_confidence = round(max(30.0, min(95.0, data_confidence * 0.85 + (100.0 - wssi) * 0.10)), 1)
        
        return ForecastItem(
            horizon=f"{horizon_days}D",
            target_date=target_date,
            direction=direction,
            p10=p10,
            p50=p50,
            p90=p90,
            currency="VND",
            unit="KG",
            forecast_confidence=forecast_confidence,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            invalidation_conditions=invalidation,
            scenarios=ScenarioProb(
                base_case={"probability": base_prob, "range": f"{p10:,.0f} - {p90:,.0f}"},
                bullish={"probability": bull_prob, "range": f"> {p90:,.0f}"},
                bearish={"probability": bear_prob, "range": f"< {p10:,.0f}"}
            )
        )
