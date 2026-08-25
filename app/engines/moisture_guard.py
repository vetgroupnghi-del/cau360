"""
MOISTURE & AFLATOXIN CONTAINER SWEAT RISK RADAR V18.0
Bảng kiểm soát độ ẩm lõi hạt & Quy chuẩn đóng container xuất khẩu chính ngạch:
- Kiểm soát độ ẩm lõi <= 10.5% (an toàn tuyệt đối) vs > 12.0% (nguy cơ mốc trắng)
- Quy chuẩn lót giấy Kraft 5 mặt và túi hút ẩm Dry Pole 1kg trong container 40ft
"""
from typing import Dict, Any

class MoistureGuardEngine:
    @staticmethod
    def evaluate_moisture_risk(
        core_moisture_pct: float,
        kiln_drying_hours: int,
        transport_days: int = 4, # Số ngày xe chạy ra cửa khẩu và sang kho Hồ Nam
        packaging_type: str = "PE_DOUBLE_LINED" # "PE_DOUBLE_LINED" hoặc "JUTE_BAG"
    ) -> Dict[str, Any]:
        """
        Đánh giá rủi ro mồ hôi container và nấm mốc Aflatoxin.
        """
        if core_moisture_pct <= 10.5:
            risk_level = "AN TOÀN TUYỆT ĐỐI"
            risk_color = "green"
            status = "PASSED_EXPORT_READY"
            recommendation = (
                "Lô hàng đạt chuẩn xuất khẩu chính ngạch GACC. Lõi hạt đã chín kiệt, "
                "không có nguy cơ đọng ẩm hay mọc nấm mốc Aflatoxin trong quá trình vận chuyển."
            )
        elif core_moisture_pct <= 11.5:
            risk_level = "AN TOÀN CÓ ĐIỀU KIỆN"
            risk_color = "yellow"
            status = "BORDERLINE_ACCEPTABLE"
            recommendation = (
                "Độ ẩm chấp nhận được cho vận chuyển ngắn ngày (< 5 ngày). "
                "Bắt buộc lồng 2 lớp bao PE 0.08mm, dán kín miệng bao và treo tối thiểu 6 túi hút ẩm Dry Pole trong container."
            )
        else:
            risk_level = "NGUY CƠ MỐC TRẮNG CHÍ MẠNG (> 12%)"
            risk_color = "red"
            status = "DANGER_REDRY_REQUIRED"
            recommendation = (
                "CẢNH BÁO: Lõi quả chưa chín kiệt nước! Khi đóng container gặp chênh lệch nhiệt độ ngày đêm, "
                "hơi ẩm từ lõi thoát ra sẽ ngưng tụ trên trần container nhỏ xuống gây mốc trắng toàn bộ lô hàng. "
                "BẮT BUỘC ĐƯA VÀO LÒ SẤY LẠI THÊM 12 - 18 GIỜ TRƯỚC KHI XUẤT BÁN!"
            )

        container_spec = [
            {"item": "Quy cách bao bì", "spec": "Bao PP dệt lồng túi nilon PE nguyên sinh dày 0.08mm (50kg/bao)"},
            {"item": "Chống ẩm container", "spec": "Lót giấy Kraft dày 5 mặt (vách + trần + sàn container)"},
            {"item": "Túi hút ẩm chuyên dụng", "spec": "Treo 8 - 10 thanh hút ẩm Dry Pole 1kg chia đều 2 vách container 40ft"},
            {"item": "Kiểm tra mẫu thực địa", "spec": "Chẻ đôi ngẫu nhiên 10 quả ở giữa bao, đo độ ẩm tận tâm hạt"}
        ]

        return {
            "core_moisture_pct": core_moisture_pct,
            "kiln_drying_hours": kiln_drying_hours,
            "transport_days": transport_days,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "status": status,
            "recommendation": recommendation,
            "container_spec": container_spec
        }
