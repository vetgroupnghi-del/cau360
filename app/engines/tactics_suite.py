"""
MODULE 3, 4, 5: TACTICAL ANTI-MANIPULATION & QUALITY PASSPORT SUITE
Bao gồm:
1. Triangulation Freeze Trap Radar (Phát hiện bẫy đóng băng giá giả tạo)
2. Bargaining Power & Liquidity-Aware Allocation (Máy đo quyền đàm phán & Cứu thanh khoản)
3. Grade Split Valuation & Quality Passport (Hộ chiếu chất lượng & Định giá bóc tách)
"""
from typing import Dict, Any, List

class TacticsSuite:
    @staticmethod
    def detect_triangulated_freeze_trap(
        days_without_buyer_quotes: int,
        daily_customs_container_count: int,
        truck_wait_hours: float,
        hunan_factory_operation_rate_pct: float,
        customs_quarantine_ban_active: bool = False
    ) -> Dict[str, Any]:
        """
        Ví dụ dẫn chứng thực tế:
        - Thương lái tại Đắk Lắk tắt máy 4 ngày không phát giá mua.
        - Dữ liệu hải quan Tân Thanh/Móng Cái: 26 xe container/ngày vẫn thông quan bình thường.
        - Thời gian chờ xe thông quan: 14 giờ (thông thoáng).
        - Xưởng kẹo Tương Đàm: Vẫn chạy 82% công suất máy.
        - Không có văn bản cấm kiểm dịch từ GACC.
        ==> CHẨN ĐOÁN: BẪY DÌM GIÁ TÂM LÝ 100%. LỆNH: GIỮ HÀNG.
        """
        is_freeze_trap = False
        is_actual_logistics_block = False
        
        if customs_quarantine_ban_active or truck_wait_hours > 72.0 or daily_customs_container_count < 5:
            is_actual_logistics_block = True
            diagnosis = "RỦI RO LOGISTICS / KIỂM DỊCH THỰC TẾ: Cửa khẩu ùn tắc hoặc siết kiểm tra nấm mốc."
            tactical_command = "DỪNG GOM CAU TƯƠI ĐẦU VÀO NGAY LẬP TỨC để tránh đọng vốn và hư hỏng hàng."
        elif days_without_buyer_quotes >= 3 and daily_customs_container_count >= 20 and hunan_factory_operation_rate_pct >= 75.0:
            is_freeze_trap = True
            diagnosis = "BẪY DÌM GIÁ TÂM LÝ (ARTIFICIAL FREEZE): Thương lái cố tình ngừng phát giá để dọa các lò yếu vốn bán tháo, trong khi hàng xuất khẩu và xưởng kẹo TQ vẫn chạy ầm ầm."
            tactical_command = "BÌNH TĨNH GIỮ CHẶT KHO TRONG 72H TỚI — TUYỆT ĐỐI KHÔNG BÁN CẮT LỖ VÌ THƯƠNG LÁI SẮP PHẢI QUAY LẠI MUA BÙ TIẾN ĐỘ."
        else:
            diagnosis = "DIỄN BIẾN GIAO DỊCH THÔNG THƯỜNG."
            tactical_command = "Duy trì xuất bán theo kế hoạch rải đinh P50."

        return {
            "is_freeze_trap": is_freeze_trap,
            "is_actual_logistics_block": is_actual_logistics_block,
            "diagnosis": diagnosis,
            "tactical_command": tactical_command,
            "evidence_snapshot": {
                "days_frozen": days_without_buyer_quotes,
                "customs_containers_daily": daily_customs_container_count,
                "truck_wait_time": f"{truck_wait_hours:.0f} giờ",
                "hunan_factory_rate": f"{hunan_factory_operation_rate_pct:.0f}%"
            }
        }

    @staticmethod
    def calculate_liquidity_aware_bpr(
        total_inventory_tons: float,
        kiln_moisture_pct: float,
        days_to_peak_season: int,
        hunan_demand_urgency_score: float,
        monthly_debt_due_vnd: float,
        current_market_price_p50_vnd_kg: float
    ) -> Dict[str, Any]:
        """
        Ví dụ dẫn chứng thực tế:
        - Lò đang có 20 tấn cau khô tồn kho đạt độ ẩm 10.8% (bảo quản an toàn 24 tháng).
        - Đếm ngược 40 ngày đến cao điểm sản xuất kẹo Tết Hồ Nam.
        - Xưởng TQ khát hàng (hunan_demand_urgency_score = 85).
        - Chủ lò có khoản nợ tiền than và ngân hàng đến hạn: 300.000.000 đ.
        - Giá thị trường P50 hôm nay: 190.000 đ/kg.
        """
        # Sức bền kho (Độ ẩm <= 11.5% là an toàn tuyệt đối)
        storage_score = 100.0 if kiln_moisture_pct <= 11.5 else (70.0 if kiln_moisture_pct <= 13.0 else 30.0)
        
        # Tỷ số BPR
        time_factor = max(0.0, min(100.0, (120 - days_to_peak_season) * 0.8))
        trader_urgency = (0.6 * time_factor) + (0.4 * hunan_demand_urgency_score)
        bpr = round(trader_urgency / max(1.0, (100.0 - storage_score + 15.0)), 2)
        
        # Tính lượng hàng cần bán để giải phóng dòng tiền trả nợ
        money_per_ton = current_market_price_p50_vnd_kg * 1000.0
        tons_needed_for_debt = round(monthly_debt_due_vnd / max(1.0, money_per_ton), 2)
        tons_to_hold = max(0.0, round(total_inventory_tons - tons_needed_for_debt, 2))
        
        return {
            "total_inventory_tons": total_inventory_tons,
            "kiln_moisture_pct": kiln_moisture_pct,
            "bargaining_power_ratio": bpr,
            "debt_due_vnd": monthly_debt_due_vnd,
            "tons_needed_to_sell_for_liquidity": tons_needed_for_debt,
            "tons_safe_to_hold_for_peak_profit": tons_to_hold,
            "tactical_plan": (
                f"BÁN ĐÚNG {tons_needed_for_debt:.2f} TẤN theo giá P50 ({current_market_price_p50_vnd_kg:,.0f} đ/kg) "
                f"để thu về {monthly_debt_due_vnd:,.0f} đ trả sạch nợ đến hạn. "
                f"GĂM GIỮ CHẶT {tons_to_hold:.2f} TẤN HÀNG ĐẸP CÒN LẠI chờ gặt đỉnh giá vào cao điểm Tết!"
            )
        }

    @staticmethod
    def generate_grade_split_passport(
        lot_id: str,
        total_lot_kg: float,
        pct_long: float,
        pct_round: float,
        pct_broken: float,
        price_long_market: float,
        price_round_market: float,
        price_broken_market: float,
        trader_lowball_offer: float
    ) -> Dict[str, Any]:
        """
        Ví dụ dẫn chứng thực tế:
        - Lô hàng 10.000 kg cau sấy xuất khẩu:
          + 60% Cau dài (6.000 kg) giá 200.000 đ/kg.
          + 30% Cau tròn (3.000 kg) giá 175.000 đ/kg.
          + 10% Cau dạt/bi (1.000 kg) giá 90.000 đ/kg.
        - Thương lái Trung Quốc chê lô có cau tròn/dạt và ép mua cào bằng giá 165.000 đ/kg.
        ==> HỘ CHIẾU CHỨNG MINH: Giá trị thực = 181.500 đ/kg. Bác bỏ mức giá 165k (tiết kiệm 165 triệu đ tiền lãi cho chủ lò!).
        """
        vol_long = total_lot_kg * pct_long
        vol_round = total_lot_kg * pct_round
        vol_broken = total_lot_kg * pct_broken
        
        val_long = vol_long * price_long_market
        val_round = vol_round * price_round_market
        val_broken = vol_broken * price_broken_market
        
        total_val = val_long + val_round + val_broken
        true_weighted_price = round(total_val / max(1.0, total_lot_kg), 0)
        
        money_saved_from_lowball = total_val - (trader_lowball_offer * total_lot_kg)
        
        return {
            "lot_id": lot_id,
            "quality_passport_title": f"HỘ CHIẾU CHẤT LƯỢNG LÔ HÀNG — {lot_id}",
            "total_lot_weight_kg": total_lot_kg,
            "true_weighted_price_vnd_kg": true_weighted_price,
            "trader_lowball_offer_vnd_kg": trader_lowball_offer,
            "loss_prevented_vnd": max(0.0, money_saved_from_lowball),
            "breakdown": [
                {"grade": "Cau Dài Loại 1 (60%)", "kg": vol_long, "unit_price": price_long_market, "subtotal": val_long},
                {"grade": "Cau Tròn Loại 2 (30%)", "kg": vol_round, "unit_price": price_round_market, "subtotal": val_round},
                {"grade": "Cau Dạt Loại 3 (10%)", "kg": vol_broken, "unit_price": price_broken_market, "subtotal": val_broken}
            ],
            "official_counter_statement": (
                f"Giá trị thực được thẩm định của lô hàng là {true_weighted_price:,.0f} đ/kg "
                f"(Tổng giá trị: {total_val:,.0f} đ). "
                f"Từ chối mức giá ép cào bằng {trader_lowball_offer:,.0f} đ/kg của thương lái!"
            )
        }
