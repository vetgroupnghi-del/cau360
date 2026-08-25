"""
MODULE 2: EARLY CHINA LEADING RADAR (TÍN HIỆU SỚM TRƯỚC 60-90 NGÀY)
Đo lường các chỉ số dẫn dắt từ Trung Quốc để dự báo thị trường trước khi mở lò tại Việt Nam.
"""
from typing import Dict, Any

class EarlyChinaRadar:
    @staticmethod
    def calculate_early_import_demand(
        hainan_yield_loss_pct: float,            # Tỷ lệ thất thu sản lượng Hải Nam (do bệnh vàng lá + bão sớm)
        hunan_cold_storage_depletion_pct: float, # Tỷ lệ cạn kiệt kho lạnh bảo ôn kẹo cau Hồ Nam (0 - 100%)
        packaging_order_growth_pct: float,       # Tốc độ tăng trưởng đơn in bao bì kẹo cau tại Quảng Đông/Hồ Nam
        additive_demand_score: float             # Điểm nhu cầu phụ gia kẹo (bạc hà, keo điểm lộ) (0 - 100)
    ) -> Dict[str, Any]:
        """
        Ví dụ dẫn chứng thực tế:
        - Tháng 5 DL (trước vụ VN 2 tháng):
          + Vạn Ninh bị bệnh vàng lá làm hỏng 42% sản lượng (hainan_yield_loss_pct = 42%).
          + Tồn kho cũ tại kho lạnh Tương Đàm đã cạn kiệt 82% (hunan_cold_storage_depletion_pct = 82%).
          + Đơn đặt in bao bì kẹo Tết tăng 25% (packaging_order_growth_pct = 25%).
          + Chỉ số phụ gia đạt 80/100 (additive_demand_score = 80).
        """
        # Trọng số tổng hợp
        w_hainan = min(100.0, hainan_yield_loss_pct * 1.5)
        w_storage = hunan_cold_storage_depletion_pct
        w_pack = min(100.0, max(0.0, 50.0 + packaging_order_growth_pct * 2.0))
        w_additive = additive_demand_score
        
        eid_score = (0.35 * w_hainan) + (0.30 * w_storage) + (0.20 * w_pack) + (0.15 * w_additive)
        eid_score = round(min(100.0, max(0.0, eid_score)), 1)
        
        if eid_score >= 75.0:
            market_regime = "STRONG_BULLISH_EARLY"
            outlook = "SÓNG TĂNG MẠNH ĐẦU VỤ: Trung Quốc thiếu hụt nguồn cung nghiêm trọng. Dự kiến xưởng Hồ Nam sẽ sang VN gom hàng sớm và đẩy giá cao."
            tactical_action = "Tự tin chuẩn bị kho bãi, nâng cấp lò sấy, chuẩn bị nguồn vốn sẵn sàng mở lò."
        elif eid_score >= 50.0:
            market_regime = "MODERATE_BALANCED"
            outlook = "THỊ TRƯỜNG CÂN BẰNG: Nhu cầu ổn định tương đương các vụ trước."
            tactical_action = "Duy trì công suất lò bình thường, không vay mượn mở rộng ồ ạt."
        else:
            market_regime = "BEARISH_CAUTION"
            outlook = "THỊ TRƯỜNG CẨN TRỌNG: Tồn kho cũ bên TQ còn nhiều, nguồn cung Hải Nam phục hồi. Dự kiến thương lái TQ sẽ dìm giá đầu vụ."
            tactical_action = "Phòng thủ vốn, chỉ mua cau tươi khi đè được giá vườn thật thấp."

        return {
            "early_import_demand_index": eid_score,
            "market_regime": market_regime,
            "outlook": outlook,
            "tactical_action": tactical_action,
            "signals": {
                "hainan_supply_deficit": f"{hainan_yield_loss_pct:.1f}% thất thu",
                "hunan_inventory_drain": f"{hunan_cold_storage_depletion_pct:.1f}% cạn kiệt",
                "packaging_growth": f"+{packaging_order_growth_pct:.1f}%"
            }
        }
