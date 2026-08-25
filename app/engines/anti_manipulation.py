"""
CAU360 Anti-Manipulation & Kiln Proactive Tactics Engine
Specialized algorithms to protect Vietnamese drying kiln owners from Chinese traders' price manipulation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class AntiManipulationEngine:
    @staticmethod
    def calculate_safe_fresh_buying_ceiling(
        expected_dry_price_vnd_kg: float,
        drying_cost_vnd_kg: float = 12000.0, # Tiền than/điện, nhân công lặt cuống, hao hụt
        fresh_to_dry_ratio: float = 4.5,     # kg tươi / 1 kg khô
        target_profit_margin_pct: float = 0.15 # 15% biên lãi ròng tối thiểu của chủ lò
    ) -> Dict[str, Any]:
        """
        Feature 1: Tính toán Giá Trần Thu Mua Cau Tươi An Toàn Tại Vườn (Safe Buying Ceiling)
        Ngăn chặn chủ lò dính bẫy mua cau tươi giá đỉnh đầu vụ.
        """
        # Doanh thu kỳ vọng từ 1kg cau khô trừ đi lợi nhuận mục tiêu và chi phí sấy
        target_profit_vnd = expected_dry_price_vnd_kg * target_profit_margin_pct
        max_allowable_fresh_budget_per_kg_dry = expected_dry_price_vnd_kg - target_profit_vnd - drying_cost_vnd_kg
        
        safe_fresh_ceiling_vnd_kg = max_allowable_fresh_budget_per_kg_dry / max(1.0, fresh_to_dry_ratio)
        break_even_fresh_price_vnd_kg = (expected_dry_price_vnd_kg - drying_cost_vnd_kg) / max(1.0, fresh_to_dry_ratio)
        
        return {
            "expected_dry_price_vnd_kg": expected_dry_price_vnd_kg,
            "drying_cost_vnd_kg": drying_cost_vnd_kg,
            "fresh_to_dry_ratio": fresh_to_dry_ratio,
            "target_profit_margin_pct": f"{target_profit_margin_pct*100:.0f}%",
            "safe_fresh_buying_ceiling_vnd_kg": round(safe_fresh_ceiling_vnd_kg, 0),
            "break_even_fresh_price_vnd_kg": round(break_even_fresh_price_vnd_kg, 0),
            "tactical_rule": f"TUYỆT ĐỐI KHÔNG MUA CAU TƯƠI > {safe_fresh_ceiling_vnd_kg:,.0f} đ/kg nếu giá cau khô xuất bán kỳ vọng là {expected_dry_price_vnd_kg:,.0f} đ/kg."
        }

    @staticmethod
    def calculate_bargaining_power_ratio(
        days_to_peak_season: int,          # Đếm ngược ngày tới cao điểm Tết (tháng 10-11 âm lịch)
        hunan_factory_utilization_pct: float, # Công suất chạy máy của xưởng kẹo TQ (e.g. 85%)
        kiln_moisture_content_pct: float,     # Độ ẩm mẻ cau sấy của lò (e.g. 10.5%)
        kiln_debt_pressure_score: float = 30.0 # Áp lực trả nợ ngân hàng (0: không nợ, 100: nợ siết hàng ngày)
    ) -> Dict[str, Any]:
        """
        Feature 2: Máy Đo Áp Lực Đơn Hàng Thương Lái vs Sức Bền Kho (Bargaining Power Ratio - BPR)
        """
        # 1. Tính độ khát hàng của thương lái / nhà máy TQ (Trader Urgency: 0 - 100)
        time_factor = max(0.0, min(100.0, (120 - days_to_peak_season) * 0.8))
        trader_urgency = (0.6 * time_factor) + (0.4 * hunan_factory_utilization_pct)
        trader_urgency = round(min(100.0, max(0.0, trader_urgency)), 1)
        
        # 2. Tính sức bền cầm giữ kho của chủ lò (Kiln Holding Power: 0 - 100)
        # Độ ẩm <= 11% bảo quản được 24 tháng (điểm tối đa 100), >14% có nguy cơ mốc (điểm sụt nhanh)
        if kiln_moisture_content_pct <= 11.5:
            storage_quality_score = 100.0
        elif kiln_moisture_content_pct <= 13.0:
            storage_quality_score = 70.0
        else:
            storage_quality_score = 30.0
            
        kiln_holding_power = (0.65 * storage_quality_score) + (0.35 * (100.0 - kiln_debt_pressure_score))
        kiln_holding_power = round(min(100.0, max(0.0, kiln_holding_power)), 1)
        
        # 3. Tính tỷ số sức mạnh đàm phán BPR
        bpr = round(trader_urgency / max(1.0, (100.0 - kiln_holding_power + 10.0)), 2)
        
        # Chiến thuật hành động
        if bpr >= 1.4:
            recommendation = "THƯƠNG LÁI ĐANG RẤT VỘI HÀNG — GIỮ HÀNG, ĐÒI TĂNG GIÁ (+3K ĐẾN +5K/KG), KHÔNG BÁN VỘI."
            strategy_stance = "AGGRESSIVE_HOLD"
        elif bpr >= 0.9:
            recommendation = "THỊ TRƯỜNG CÂN BẰNG — BÁN ĐỀU ĐẶN THEO GIÁ P50 ĐỂ THU TIỀN VỀ."
            strategy_stance = "TRANCHE_SELL"
        else:
            recommendation = "THƯƠNG LÁI ĐANG ĐỦNG ĐỈNH — CHỦ ĐỘNG BÁN 30-40% HÀNG ĐỂ THU HỒI GỐC, KHÔNG GĂM HÀNG ĐẦY KHO."
            strategy_stance = "DEFENSIVE_LIQUIDATE"
            
        return {
            "trader_urgency_score": trader_urgency,
            "kiln_holding_power_score": kiln_holding_power,
            "bargaining_power_ratio": bpr,
            "strategy_stance": strategy_stance,
            "tactical_action": recommendation
        }

    @staticmethod
    def calculate_grade_split_valuation(
        total_volume_kg: float,
        pct_long_grade: float = 0.60,      # Tỷ lệ cau dài loại 1 (60%)
        pct_round_grade: float = 0.30,     # Tỷ lệ cau tròn loại 2 (30%)
        pct_broken_grade: float = 0.10,    # Tỷ lệ cau bi/cau dạt (10%)
        price_long_quote: float = 200000.0,# Giá cau dài
        price_round_quote: float = 175000.0,# Giá cau tròn
        price_broken_quote: float = 90000.0 # Giá cau dạt
    ) -> Dict[str, Any]:
        """
        Feature 3: Định Giá Bóc Tách Theo Quy Cách (Chống Chiêu Ép Giá Cào Bằng Toàn Lô)
        """
        vol_long = total_volume_kg * pct_long_grade
        vol_round = total_volume_kg * pct_round_grade
        vol_broken = total_volume_kg * pct_broken_grade
        
        val_long = vol_long * price_long_quote
        val_round = vol_round * price_round_quote
        val_broken = vol_broken * price_broken_quote
        
        total_val = val_long + val_round + val_broken
        weighted_avg_price = total_val / max(1.0, total_volume_kg)
        
        return {
            "total_volume_kg": total_volume_kg,
            "breakdown": {
                "long_grade_type1": {"volume_kg": vol_long, "price": price_long_quote, "subtotal": val_long},
                "round_grade_type2": {"volume_kg": vol_round, "price": price_round_quote, "subtotal": val_round},
                "broken_grade_type3": {"volume_kg": vol_broken, "price": price_broken_quote, "subtotal": val_broken}
            },
            "total_actual_value_vnd": total_val,
            "true_weighted_price_vnd_kg": round(weighted_avg_price, 0),
            "counter_argument": f"Lô hàng {total_volume_kg:,.0f} kg có giá trị thực là {weighted_avg_price:,.0f} đ/kg. Thương lái không được dùng 10% cau dạt để dìm giá cả lô xuống dưới {weighted_avg_price:,.0f} đ/kg."
        }

    @staticmethod
    def detect_artificial_freeze_signal(
        days_without_buyer_quotes: int,
        border_gate_container_count_daily: int,
        hunan_demand_active: bool = True
    ) -> Dict[str, Any]:
        """
        Feature 4: Nhận Diện Bẫy Đóng Băng Giá Giả Tạo (Artificial Freeze Trap)
        """
        is_trap = False
        reason = "DIỄN BIẾN BÌNH THƯỜNG"
        
        if days_without_buyer_quotes >= 3 and border_gate_container_count_daily >= 20 and hunan_demand_active:
            is_trap = True
            reason = "BẪY DÌM GIÁ TÂM LÝ: Thương lái cố tình dừng phát giá 3-5 ngày để tạo hoảng loạn, nhưng thực tế hàng vẫn thông quan đều đặn tại cửa khẩu và xưởng TQ vẫn chạy."
            action = "BÌNH TĨNH GIỮ HÀNG — KHÔNG BÁN CẮT LỖ TRONG 72H TỚI VÌ ĐÂY LÀ ĐÒN TÂM LÝ CỦA THƯƠNG LÁI."
        else:
            action = "THEO DÕI SÁT TÍN HIỆU TIÊU THỤ."
            
        return {
            "is_artificial_freeze_trap": is_trap,
            "diagnosis": reason,
            "tactical_instruction": action
        }
