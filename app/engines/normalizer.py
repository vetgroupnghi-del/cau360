"""
Price & Unit Normalization Engine (Rule 02, 03, 04, 15, 41, 42, 43)
"""
from typing import Optional, Dict, Any, Tuple
from app.models.schemas import FXRateSnapshot
from app.collectors.fx_vcb import VietcombankFXCollector

class Normalizer:
    @staticmethod
    def normalize_unit_to_kg(raw_unit: str) -> Tuple[str, float]:
        """
        Normalizes unit string and returns standard (canonical_unit, conversion_multiplier_to_kg).
        1 斤 (JIN) = 0.5 kg  => multiplier = 0.5
        1 kg / cân / kí = 1.0 kg => multiplier = 1.0
        1 tấn (TON) = 1000.0 kg => multiplier = 1000.0
        1 tạ = 100.0 kg => multiplier = 100.0
        """
        u = raw_unit.strip().upper()
        if u in ["JIN", "斤", "市斤"]:
            return "JIN", 0.5
        elif u in ["KG", "KÍ", "CÂN", "KILOGRAM", "公斤"]:
            return "KG", 1.0
        elif u in ["TON", "TẤN", "吨"]:
            return "TON", 1000.0
        elif u in ["TA", "TẠ"]:
            return "TA", 100.0
        elif u in ["PIECE", "QUẢ", "TRÁI", "颗", "个"]:
            return "PIECE", 0.025 # ~40 fruits per kg, tagged as non-mass unit
        return "KG", 1.0

    @classmethod
    def normalize_price_to_vnd_kg(
        cls,
        price_val: float,
        currency: str,
        unit: str,
        fx_snapshot: Optional[FXRateSnapshot] = None,
        use_rate_type: str = "SELL" # SELL for VN buying CNY, TRANSFER_BUY for CNY -> VND
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Converts any price in (VND, CNY) and (KG, JIN, TON) to VND/kg.
        Returns: (normalized_price_vnd_kg, fx_rate_used, fx_snapshot_id)
        """
        if price_val is None or price_val <= 0:
            return None, None, None
            
        canonical_unit, kg_multiplier = cls.normalize_unit_to_kg(unit)
        curr = currency.strip().upper()
        
        # Step 1: Normalize to base currency per KG
        if canonical_unit == "JIN":
            # Price is per Jin (0.5kg) -> Price per KG = price_val * 2.0
            price_per_kg_local = price_val * 2.0
        elif canonical_unit == "TON":
            price_per_kg_local = price_val / 1000.0
        elif canonical_unit == "TA":
            price_per_kg_local = price_val / 100.0
        else:
            price_per_kg_local = price_val
            
        # Step 2: Currency conversion
        if curr == "VND":
            return round(price_per_kg_local, 2), 1.0, "VND_BASE"
        elif curr == "CNY":
            if fx_snapshot is None:
                fx_snapshot = VietcombankFXCollector.get_latest_verified_fx()
                
            if not fx_snapshot:
                # Rule 02 & Rule 99: If FX is missing, DO NOT convert silently
                return None, None, None
                
            fx_rate = fx_snapshot.sell if use_rate_type == "SELL" else fx_snapshot.transfer_buy
            normalized_vnd_kg = price_per_kg_local * fx_rate
            return round(normalized_vnd_kg, 2), fx_rate, fx_snapshot.id
        else:
            return None, None, None

    @classmethod
    def calculate_fresh_to_dry_scenario(
        cls,
        cny_per_jin: float,
        processing_cost_vnd_kg: float = 8000.0,
        fx_snapshot: Optional[FXRateSnapshot] = None
    ) -> Dict[str, Any]:
        """
        Theoretical Conversion Model (Rule 03, 42, 43)
        Fresh China -> Dry Equivalent Scenario with P10 (4.0:1), P50 (4.5:1), P90 (5.0:1)
        """
        if fx_snapshot is None:
            fx_snapshot = VietcombankFXCollector.get_latest_verified_fx()
            
        if not fx_snapshot:
            return {"error": "NO_VERIFIED_FX"}
            
        # 1 jin = 0.5kg => Fresh CNY/kg = cny_per_jin * 2
        fresh_cny_kg = cny_per_jin * 2.0
        fresh_vnd_kg = fresh_cny_kg * fx_snapshot.sell
        
        # Dry equivalent calculation: Dry Cost = (Fresh VND/kg * ratio) + drying cost
        dry_p10 = round((fresh_vnd_kg * 4.0) + processing_cost_vnd_kg, 0)
        dry_p50 = round((fresh_vnd_kg * 4.5) + processing_cost_vnd_kg, 0)
        dry_p90 = round((fresh_vnd_kg * 5.0) + processing_cost_vnd_kg, 0)
        
        return {
            "disclaimer": "THEORETICAL CONVERSION SCENARIO ONLY - NOT OBSERVED MARKET PRICE",
            "input_fresh_cny_jin": cny_per_jin,
            "fresh_vnd_kg": fresh_vnd_kg,
            "fx_used": fx_snapshot.sell,
            "ratios": {"p10": 4.0, "p50": 4.5, "p90": 5.0},
            "dry_equivalent_cost_vnd_kg": {
                "p10": dry_p10,
                "p50": dry_p50,
                "p90": dry_p90
            }
        }
