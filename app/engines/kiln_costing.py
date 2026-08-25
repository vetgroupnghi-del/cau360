"""
REVERSE NETBACK PRICING & PRACTITIONER DYNAMIC KILN SIMULATOR V32.0
Cơ chế Định Giá Ngược Mậu Dịch & Tính Toán Hòa Vốn Thực Chiến:
1. Nhập thông số lò thực tế: Giá tươi vườn [X], Tỷ lệ sấy kiệt [Y] (4.5 - 7.0), % Trừ cọng cuống (15 - 22%)
2. Tự động tính Điểm Hòa Vốn Sản Xuất Thực Tế tại cửa lò
3. Tự động đối soát với Giá Sỉ Đại Lục (Heiguo/Ganguo) quy đổi qua Vietcombank Live FX
4. Bóc trần chính xác Biên Lợi Nhuận Mậu Dịch Ròng mà đầu nậu trung gian đang ăn chênh lệch.
"""
from typing import Dict, Any
from app.collectors.fx_vcb import VietcombankFXCollector

class KilnBatchCalculator:
    @classmethod
    def calculate_custom_batch(
        cls,
        fresh_price: float = 20000.0,
        dry_selling_price: float = 192500.0,
        fresh_to_dry_ratio: float = 6.0, # Tỷ lệ sấy kiệt xuất khẩu Ganguo (6.0:1 hoặc 7.0:1)
        batch_weight_kg: float = 10000.0,
        raw_type: str = "BUNCH", # "BUNCH" (Cau cành) hoặc "FRUIT" (Cau trái)
        stem_tare_pct: float = 20.0, # Trừ cọng cuống đầu vụ 18 - 22% (chuẩn 20%)
        fuel_cost_per_kg_dry: float = 12000.0,
        labor_fresh_per_kg: float = 500.0, # Công thợ vặt 500 đ/kg tươi
        packaging_per_kg_dry: float = 1200.0,
        waste_rate: float = 0.04,
        china_wholesale_cny_jin: float = 102.0 # Giá sỉ hạt khô Heiguo/Ganguo đại lục
    ) -> Dict[str, Any]:
        """
        Tính toán chiết tính mẻ sấy và định giá ngược mậu dịch.
        """
        fx = VietcombankFXCollector.get_latest_verified_fx()
        cny_rate = fx.sell

        # 1. Trọng lượng cau trái thực tế vào buồng sấy
        if raw_type == "BUNCH":
            actual_fruit_weight_kg = batch_weight_kg * (1.0 - (stem_tare_pct / 100.0))
            stem_waste_weight_kg = batch_weight_kg * (stem_tare_pct / 100.0)
            total_fresh_cost = batch_weight_kg * fresh_price
            total_labor_cost = batch_weight_kg * labor_fresh_per_kg
        else:
            actual_fruit_weight_kg = batch_weight_kg
            stem_waste_weight_kg = 0.0
            total_fresh_cost = batch_weight_kg * fresh_price
            total_labor_cost = 0.0

        # 2. Sản lượng cau khô thu được
        theoretical_dry_weight = actual_fruit_weight_kg / max(1.0, fresh_to_dry_ratio)
        commercial_dry_weight = round(theoretical_dry_weight * (1.0 - waste_rate), 1)

        # 3. Chi phí chế biến hoàn thiện
        total_fuel_cost = commercial_dry_weight * fuel_cost_per_kg_dry
        total_packaging_cost = commercial_dry_weight * packaging_per_kg_dry
        total_production_cost = total_fresh_cost + total_labor_cost + total_fuel_cost + total_packaging_cost

        # 4. Giá thành sản xuất 1kg khô thực tế tại cửa lò (Giá Hòa Vốn Sản Xuất)
        true_cost_per_kg_dry = round(total_production_cost / max(1.0, commercial_dry_weight), 0)
        break_even_dry_price = true_cost_per_kg_dry

        # 5. Doanh thu & Lợi nhuận bán tại cửa khẩu / cửa lò Việt Nam
        total_revenue_vn = commercial_dry_weight * dry_selling_price
        total_net_profit_vn = round(total_revenue_vn - total_production_cost, 0)
        profit_per_kg_dry_vn = round(dry_selling_price - true_cost_per_kg_dry, 0)
        profit_margin_pct_vn = round((total_net_profit_vn / max(1.0, total_revenue_vn)) * 100.0, 1)

        # 6. ĐỊNH GIÁ NGƯỢC THƯỢNG NGUỒN ĐẠI LỤC (REVERSE NETBACK TO CHINA WHOLESALE)
        china_wholesale_vnd_kg = round(china_wholesale_cny_jin * 2.0 * cny_rate, 0)
        macro_trade_spread_per_kg = round(china_wholesale_vnd_kg - true_cost_per_kg_dry, 0)

        # 7. Điểm hòa vốn mua tươi tối đa
        remaining_rev_for_fresh = total_revenue_vn - total_fuel_cost - total_packaging_cost - total_labor_cost
        break_even_fresh_price = round(remaining_rev_for_fresh / max(1.0, batch_weight_kg), 0)

        # 8. Nhận định quyết sách đàm phán mậu dịch
        if profit_margin_pct_vn >= 15.0:
            status = "GOOD_PROFIT"
            verdict = "🟢 VÙNG AN TOÀN TUYỆT ĐỐI (BIÊN LÃI DÀY) — TỰ TIN BUNG VỐN GOM VƯỜN!"
            decision_advice = (
                f"Giá hòa vốn của bạn là {true_cost_per_kg_dry:,.0f} đ/kg khô. Bán giá {dry_selling_price:,.0f} đ bạn lãi ròng +{profit_per_kg_dry_vn:,.0f} đ/kg ({profit_margin_pct_vn}%). "
                f"Giá sỉ đại lục đang neo {china_wholesale_cny_jin} CNY/jin ({china_wholesale_vnd_kg:,.0f} đ/kg) ──► Biên mậu dịch chuỗi còn tới +{macro_trade_spread_per_kg:,.0f} đ/kg. Tự tin giữ giá!"
            )
        elif profit_margin_pct_vn >= 0.0:
            status = "MARGINAL_PROFIT"
            verdict = "🟡 VÙNG AN TOÀN CÓ ĐIỀU KIỆN (LÃI MỎNG) — CẦN ĐÀM PHÁN GIẢM GIÁ MUA TƯƠI."
            decision_advice = (
                f"Lãi ròng mỏng (+{profit_per_kg_dry_vn:,.0f} đ/kg). Điểm hòa vốn sấy là {true_cost_per_kg_dry:,.0f} đ/kg khô. "
                "Cần ép giá mua cau cành vườn xuống dưới mức trần hòa vốn để đảm bảo an toàn."
            )
        else:
            status = "LOSS"
            verdict = "🔴 CẢNH BÁO BẪY LỖ NẶNG — TUYỆT ĐỐI KHÔNG MUA VỚI MỨC GIÁ NÀY!"
            decision_advice = (
                f"Giá thành sản xuất ({true_cost_per_kg_dry:,.0f} đ/kg) đã vượt quá giá bán khô ({dry_selling_price:,.0f} đ/kg). "
                f"Bạn đang bị lỗ -{abs(profit_per_kg_dry_vn):,.0f} đ trên mỗi kg khô sấy ra!"
            )

        return {
            "raw_input_summary": {
                "raw_type": raw_type,
                "raw_type_label": "Cau Cành (Nguyên buồng)" if raw_type == "BUNCH" else "Cau Trái (Lặt rời)",
                "batch_weight_kg": batch_weight_kg,
                "stem_tare_pct": stem_tare_pct if raw_type == "BUNCH" else 0,
                "actual_fruit_weight_kg": actual_fruit_weight_kg,
                "stem_waste_weight_kg": stem_waste_weight_kg,
                "fresh_price_vnd_kg": fresh_price,
                "fresh_to_dry_ratio": fresh_to_dry_ratio
            },
            "production_output": {
                "commercial_dry_weight_kg": commercial_dry_weight,
                "true_cost_per_kg_dry": true_cost_per_kg_dry,
                "waste_rate_pct": waste_rate * 100.0
            },
            "financial_summary": {
                "total_production_cost_vnd": total_production_cost,
                "total_fresh_cost_vnd": total_fresh_cost,
                "total_labor_cost_vnd": total_labor_cost,
                "total_fuel_cost_vnd": total_fuel_cost,
                "total_revenue_vnd": total_revenue_vn,
                "total_net_profit_vnd": total_net_profit_vn,
                "profit_per_kg_dry_vnd": profit_per_kg_dry_vn,
                "profit_margin_pct": profit_margin_pct_vn
            },
            "reverse_netback_china": {
                "china_wholesale_cny_jin": china_wholesale_cny_jin,
                "china_wholesale_vnd_kg": china_wholesale_vnd_kg,
                "fx_rate_applied": cny_rate,
                "macro_trade_spread_per_kg": macro_trade_spread_per_kg
            },
            "break_even": {
                "break_even_dry_price_vnd": break_even_dry_price,
                "break_even_fresh_price_vnd": break_even_fresh_price
            },
            "status": status,
            "verdict": verdict,
            "decision_advice": decision_advice
        }

class KilnCostingEngine:
    @classmethod
    def calculate_custom_batch_profit(
        cls,
        fresh_price_vnd_kg: float = 20000.0,
        dry_selling_price_vnd_kg: float = 192500.0,
        fresh_to_dry_ratio: float = 6.0,
        batch_fresh_weight_kg: float = 10000.0,
        raw_type: str = "BUNCH",
        stem_tare_pct: float = 20.0,
        fuel_cost_per_kg_dry: float = 12000.0,
        labor_fresh_per_kg: float = 500.0,
        packaging_per_kg_dry: float = 1200.0,
        waste_defect_rate: float = 0.04,
        china_wholesale_cny_jin: float = 102.0
    ) -> Dict[str, Any]:
        return KilnBatchCalculator.calculate_custom_batch(
            fresh_price=fresh_price_vnd_kg,
            dry_selling_price=dry_selling_price_vnd_kg,
            fresh_to_dry_ratio=fresh_to_dry_ratio,
            batch_weight_kg=batch_fresh_weight_kg,
            raw_type=raw_type,
            stem_tare_pct=stem_tare_pct,
            fuel_cost_per_kg_dry=fuel_cost_per_kg_dry,
            labor_fresh_per_kg=labor_fresh_per_kg,
            packaging_per_kg_dry=packaging_per_kg_dry,
            waste_rate=waste_defect_rate,
            china_wholesale_cny_jin=china_wholesale_cny_jin
        )
