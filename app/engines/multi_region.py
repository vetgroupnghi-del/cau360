"""
MULTI-REGION DEEP PROFILING & FIELD CALIBRATION V17.0
Bổ sung đầy đủ 12 vùng trọng điểm Trung Quốc (Toàn bộ Hải Nam & Đại xưởng Hồ Nam)
kèm 8 vùng Việt Nam bóc tách Cau Cành vs Cau Trái và các tầng giá thương lái/cửa lò/cửa khẩu.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.collectors.fx_vcb import VietcombankFXCollector

VIETNAM_REGIONS_DEEP_PROFILES = [
    {
        "id": "VN_DAKLAK",
        "name": "Đắk Lắk (Krông Pắc, Cư M'gar, Buôn Hồ, Ea Kar)",
        "zone": "Tây Nguyên (Trọng điểm #1)",
        "role": "THỦ PHỦ CAU TRÁI DÀI & LÒ SẤY LỚN NHẤT CẢ NƯỚC",
        "dry_p20": 188000, "dry_p50": 192000, "dry_p80": 196000,
        "fresh_bunch_low": 20000, "fresh_bunch_mid": 22500, "fresh_bunch_high": 25000, # Cau cành nguyên buồng
        "fresh_fruit_low": 24000, "fresh_fruit_mid": 27000, "fresh_fruit_high": 30000, # Cau trái đã vặt cuống
        "stem_tare_pct": 20.0, # Đầu vụ hao cọng cuống 18 - 22% (chuẩn 20%)
        "destem_labor_cost": 500, # Công vặt cuống: 500 đ/kg tươi
        "safe_ceiling_bunch": 29500, # Giá trần lò mua cau cành an toàn
        "safe_ceiling_fruit": 34500, # Giá trần lò mua cau trái an toàn
        "characteristics": "65-70% quả thon dài loại 1 (cau tứ quý), cùi dày, sấy than bóng đẹp, công suất 45 lò đạt 350 tấn/ngày.",
        "active_kilns": 45, "status": "CHẠY 90% CÔNG SUẤT ĐẦU VỤ",
        "logistics_to_border": "Xe lạnh ra Tân Thanh: 36-40h (cước 2.500 - 3.200 đ/kg)"
    },
    {
        "id": "VN_GIALAI",
        "name": "Gia Lai (Chư Sê, Đak Đoa, Ia Grai, Mang Yang)",
        "zone": "Tây Nguyên",
        "role": "VÙNG TRỒNG XEN CANH TIÊU & CÀ PHÊ",
        "dry_p20": 186000, "dry_p50": 190000, "dry_p80": 194000,
        "fresh_bunch_low": 19000, "fresh_bunch_mid": 21500, "fresh_bunch_high": 24000,
        "fresh_fruit_low": 23000, "fresh_fruit_mid": 26000, "fresh_fruit_high": 29000,
        "stem_tare_pct": 20.0, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 29000, "safe_ceiling_fruit": 34000,
        "characteristics": "Quả đều, cùi chắc, các vựa gom cau cành chuyển về lò Đắk Lắk sấy.",
        "active_kilns": 28, "status": "GOM HÀNG VỀ LÒ ĐẮK LẮK",
        "logistics_to_border": "Xe tải ra cửa khẩu: 34-38h"
    },
    {
        "id": "VN_DAKNONG",
        "name": "Đắk Nông (Gia Nghĩa, Đắk Mil, Tuy Đức, Đắk Song)",
        "zone": "Tây Nguyên",
        "role": "VÙNG THU HOẠCH CAU NON ĐẦU VỤ",
        "dry_p20": 185000, "dry_p50": 189000, "dry_p80": 193000,
        "fresh_bunch_low": 18000, "fresh_bunch_mid": 21000, "fresh_bunch_high": 23500,
        "fresh_fruit_low": 22000, "fresh_fruit_mid": 25500, "fresh_fruit_high": 28500,
        "stem_tare_pct": 21.0, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 28500, "safe_ceiling_fruit": 33500,
        "characteristics": "Cau non nhiều nước, tỷ lệ sấy hao hụt cao R=5.4 - 5.8.",
        "active_kilns": 18, "status": "THƯƠNG LÁI ĐẶT CỌC VƯỜN",
        "logistics_to_border": "Vận chuyển ra Bắc: 38-42h"
    },
    {
        "id": "VN_QUANGNGAI",
        "name": "Quảng Ngãi (Sơn Tây, Nghĩa Hành, Bình Sơn, Ba Tơ)",
        "zone": "Miền Trung",
        "role": "THỦ PHỦ CAU TRUYỀN THỐNG MIỀN TRUNG",
        "dry_p20": 187000, "dry_p50": 191000, "dry_p80": 195000,
        "fresh_bunch_low": 18000, "fresh_bunch_mid": 20500, "fresh_bunch_high": 23000,
        "fresh_fruit_low": 22000, "fresh_fruit_mid": 25000, "fresh_fruit_high": 28000,
        "stem_tare_pct": 19.5, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 29200, "safe_ceiling_fruit": 34200,
        "characteristics": "Cây cau bản địa lâu năm, mùi thơm đậm đà, 40% quả tròn.",
        "active_kilns": 32, "status": "THU HÁI RỘ TOÀN TỈNH",
        "logistics_to_border": "Xe ra Tân Thanh: 22-26h (cước 2.000 đ/kg)"
    },
    {
        "id": "VN_HAIPHONG",
        "name": "Hải Phòng (Thủy Nguyên, An Lão, Tiên Lãng, Vĩnh Bảo)",
        "zone": "Miền Bắc",
        "role": "ĐẦU MỐI SẤY ĐIỆN & TRUNG CHUYỂN MÓNG CÁI",
        "dry_p20": 192000, "dry_p50": 195000, "dry_p80": 199000,
        "fresh_bunch_low": 22000, "fresh_bunch_mid": 24500, "fresh_bunch_high": 27000,
        "fresh_fruit_low": 26000, "fresh_fruit_mid": 29000, "fresh_fruit_high": 32000,
        "stem_tare_pct": 19.0, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 30200, "safe_ceiling_fruit": 35200,
        "characteristics": "Lò sấy điện công nghệ mới, kiểm soát độ ẩm khắt khe <= 10.5% chuyên làm hàng trắng xuất khẩu.",
        "active_kilns": 50, "status": "GOM HÀNG SẤY BÙ ĐƠN",
        "logistics_to_border": "Sát Móng Cái/Hữu Nghị: 3-5h (cước chỉ 600 đ/kg)"
    },
    {
        "id": "VN_NAMDINH",
        "name": "Nam Định (Hải Hậu, Nghĩa Hưng, Giao Thủy, Trực Ninh)",
        "zone": "Miền Bắc",
        "role": "LÀNG NGHỀ SẤY CAU TRUYỀN THỐNG TRĂM NĂM",
        "dry_p20": 191000, "dry_p50": 194000, "dry_p80": 198000,
        "fresh_bunch_low": 21000, "fresh_bunch_mid": 23500, "fresh_bunch_high": 26000,
        "fresh_fruit_low": 25000, "fresh_fruit_mid": 28000, "fresh_fruit_high": 31000,
        "stem_tare_pct": 19.0, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 30000, "safe_ceiling_fruit": 35000,
        "characteristics": "Kỹ thuật sấy than củi dẻo dai, đen nhánh, vỏ không cháy khét.",
        "active_kilns": 38, "status": "CHẠY 95% CÔNG SUẤT",
        "logistics_to_border": "Vận chuyển ra Lạng Sơn: 4-6h"
    },
    {
        "id": "VN_BENTRE",
        "name": "Bến Tre (Chợ Lách, Mỏ Cày Nam, Giồng Trôm, Châu Thành)",
        "zone": "Miền Tây Nam Bộ",
        "role": "VÙNG THU HOẠCH SỚM CẢ NƯỚC",
        "dry_p20": 184000, "dry_p50": 188000, "dry_p80": 192000,
        "fresh_bunch_low": 16000, "fresh_bunch_mid": 18500, "fresh_bunch_high": 21000,
        "fresh_fruit_low": 20000, "fresh_fruit_mid": 23000, "fresh_fruit_high": 26000,
        "stem_tare_pct": 21.5, "destem_labor_cost": 500,
        "safe_ceiling_bunch": 28000, "safe_ceiling_fruit": 33000,
        "characteristics": "Cau mọng nước, thường chuyển xô cau cành ra các lò phía Bắc.",
        "active_kilns": 15, "status": "BÁN QUẢ TƯƠI RA BẮC",
        "logistics_to_border": "Chở Bắc - Nam: 48-52h"
    },
    {
        "id": "VN_BORDER_LANGSON",
        "name": "Cửa Khẩu Lạng Sơn & Quảng Ninh (Tân Thanh, Hữu Nghị, Móng Cái)",
        "zone": "Biên Giới Việt - Trung",
        "role": "CỬA NGÕ THÔNG QUAN CHÍNH NGẠCH DUY NHẤT",
        "dry_p20": 196000, "dry_p50": 200000, "dry_p80": 205000,
        "fresh_bunch_low": 0, "fresh_bunch_mid": 0, "fresh_bunch_high": 0,
        "fresh_fruit_low": 0, "fresh_fruit_mid": 0, "fresh_fruit_high": 0,
        "stem_tare_pct": 0, "destem_labor_cost": 0,
        "safe_ceiling_bunch": 0, "safe_ceiling_fruit": 0,
        "characteristics": "Điểm chốt giao dịch tiền tươi trực tiếp giữa chủ lò VN và đầu nậu TQ.",
        "active_kilns": 0, "status": "THÔNG QUAN 28 CONTAINER/NGÀY",
        "logistics_to_border": "Kiểm dịch thực vật: 14-18h"
    }
]

CHINA_REGIONS_DEEP_PROFILES = [
    # TOP 1 - 5 VÙNG TRỌNG ĐIỂM HẢI NAM
    {
        "id": "CN_WANNING", "name": "Vạn Ninh (万宁市)", "province": "Hải Nam", "role": "THỦ PHỦ CAU TRUNG QUỐC (#1 THỊ PHẦN)",
        "fresh_cny_p20": 34.0, "fresh_cny_p50": 35.5, "fresh_cny_p80": 37.5,
        "characteristics": "Chiếm 50% sản lượng Hải Nam, vùng chỉ dẫn địa lý độc quyền của kẹo Hòa Thành Thiên Hạ (和成天下). Dịch vàng lá hụt 42% sản lượng.",
        "wssi": 58, "harvestability": 45, "status": "ÁP THẤP NHIỆT ĐỚI GÂY MƯA LỚN"
    },
    {
        "id": "CN_QIONGHAI", "name": "Quỳnh Hải (琼海市)", "province": "Hải Nam", "role": "TRUNG TÂM THU MUA PHÍA ĐÔNG (#2)",
        "fresh_cny_p20": 32.5, "fresh_cny_p50": 34.0, "fresh_cny_p80": 36.0,
        "characteristics": "Đầu mối các trạm cân lớn trung chuyển về Hồ Nam, giá bám sát Vạn Ninh nhưng chiết khấu 1.0 - 1.5 CNY/jin.",
        "wssi": 52, "harvestability": 50, "status": "TRẠM CÂN HOẠT ĐỘNG 80%"
    },
    {
        "id": "CN_DINGAN", "name": "Định An (定安县)", "province": "Hải Nam", "role": "VÙNG NGUYÊN LIỆU PHÍA BẮC (#3)",
        "fresh_cny_p20": 32.0, "fresh_cny_p50": 33.5, "fresh_cny_p80": 35.5,
        "characteristics": "Vùng trồng tập trung, trái đồng đều, các thương lái trung gian hay gom hàng xô tại đây.",
        "wssi": 48, "harvestability": 55, "status": "GOM HÀNG ĐỀU"
    },
    {
        "id": "CN_LINGSHUI", "name": "Lăng Thủy (陵水黎族自治县)", "province": "Hải Nam", "role": "VÙNG THU HOẠCH SỚM PHÍA NAM (#4)",
        "fresh_cny_p20": 31.5, "fresh_cny_p50": 33.0, "fresh_cny_p80": 35.0,
        "characteristics": "Khí hậu nhiệt đới gió mùa, thu hoạch sớm hơn Vạn Ninh 2-3 tuần, quả ngọt đậm vị.",
        "wssi": 45, "harvestability": 60, "status": "GIÁ VƯỜN DUY TRÌ CAO"
    },
    {
        "id": "CN_QIONGZHONG", "name": "Quỳnh Trung (琼中黎族苗族自治县)", "province": "Hải Nam", "role": "VÙNG ĐỒI NÚI TRUNG TÂM (#5)",
        "fresh_cny_p20": 30.0, "fresh_cny_p50": 32.0, "fresh_cny_p80": 34.0,
        "characteristics": "Địa hình dốc núi, chi phí hái cao, quả nhỏ hơn Vạn Ninh, dùng cho phân khúc chế biến bình dân.",
        "wssi": 40, "harvestability": 65, "status": "HÀNG XÔ TẠI VƯỜN"
    },

    # CÁC VÙNG TRỒNG NHIỀU CAU BỔ SUNG MỚI TẠI HẢI NAM
    {
        "id": "CN_SANYA", "name": "Tam Á (三亚市)", "province": "Hải Nam", "role": "VÙNG CAU VEN BIỂN CỰC NAM",
        "fresh_cny_p20": 32.0, "fresh_cny_p50": 33.5, "fresh_cny_p80": 35.5,
        "characteristics": "Nhiệt độ cao quanh năm, mùa vụ ra quả sớm nhất đảo, trái to mọng nước.",
        "wssi": 42, "harvestability": 65, "status": "VÀO VỤ THU HOẠCH"
    },
    {
        "id": "CN_DANZHOU", "name": "Đam Châu (儋州市)", "province": "Hải Nam", "role": "VÙNG TRỒNG LỚN PHÍA TÂY BẮC",
        "fresh_cny_p20": 31.0, "fresh_cny_p50": 32.5, "fresh_cny_p80": 34.5,
        "characteristics": "Diện tích canh tác lớn, đất bazan màu mỡ, sản lượng dồi dào cung cấp cho các trạm sấy khô sơ cấp.",
        "wssi": 38, "harvestability": 70, "status": "GOM HÀNG SẤY SƠ BỘ"
    },
    {
        "id": "CN_BAOTING", "name": "Bảo Đình (保亭黎族苗族自治县)", "province": "Hải Nam", "role": "THUNG LŨNG CAU RỪNG NGUYÊN SINH",
        "fresh_cny_p20": 30.5, "fresh_cny_p50": 32.0, "fresh_cny_p80": 34.0,
        "characteristics": "Cây cau mọc tự nhiên kết hợp vườn trồng, cùi dày, hàm lượng arecoline cao.",
        "wssi": 44, "harvestability": 60, "status": "THƯƠNG LÁI GOM ĐỀU"
    },
    {
        "id": "CN_LEDONG", "name": "Lạc Đông (乐东黎族自治县)", "province": "Hải Nam", "role": "VÙNG NGUYÊN LIỆU PHÍA TÂY NAM",
        "fresh_cny_p20": 30.0, "fresh_cny_p50": 31.5, "fresh_cny_p80": 33.5,
        "characteristics": "Vùng trồng ven đồi, sản lượng thu hoạch rộ vào tháng 8-9, chất lượng đồng đều.",
        "wssi": 39, "harvestability": 65, "status": "GIAO DỊCH TÍCH CỰC"
    },
    {
        "id": "CN_TUNCHANG", "name": "Đồn Xương (屯昌县)", "province": "Hải Nam", "role": "TRUNG TÂM SƠ CHẾ & GOM QUẢ NON",
        "fresh_cny_p20": 31.5, "fresh_cny_p50": 33.0, "fresh_cny_p80": 35.0,
        "characteristics": "Nơi tập kết hàng nghìn tấn cau non của các huyện lân cận để phân loại chuyển về Hồ Nam.",
        "wssi": 46, "harvestability": 55, "status": "TRẠM PHÂN LOẠI CHẠY 85%"
    },

    # TRUNG TÂM ĐẠI XƯỞNG CHẾ BIẾN KẸO CAU TỈNH HỒ NAM
    {
        "id": "CN_HUNAN_XIANGTAN", "name": "Tương Đàm (湘潭市)", "province": "Hồ Nam", "role": "THỦ PHỦ ĐẠI XƯỞNG KẸO CAU SỐ 1 TRUNG QUỐC",
        "characteristics": "Quy tụ 300 tập đoàn kẹo khổng lồ (Hòa Thành Thiên Hạ, Khẩu Vị Vương, Trương Tân Phát, Ngũ Tử Tú), tiêu thụ 80% cau khô Việt Nam.",
        "factory_utilization": "85%", "active_buyers": 22, "procurement_focus": "DRY_RAW (Cau khô VN)",
        "status": "CHẠY NƯỚC RÚT ĐƠN HÀNG MÙA ĐÔNG & TẾT"
    },
    {
        "id": "CN_HUNAN_YIYANG", "name": "Ích Dương (益阳市)", "province": "Hồ Nam", "role": "TRUNG TÂM CHẾ BIẾN THỨ CẤP & ĐÓNG GÓI",
        "characteristics": "Chuyên thu mua cau sấy than (hàng đen) và cau dạt về tẩm ướp gia vị phân khúc bán lẻ bình dân.",
        "factory_utilization": "78%", "active_buyers": 14, "procurement_focus": "DRY_BLACK & DRY_WHITE",
        "status": "NHU CẦU ỔN ĐỊNH"
    }
]

class MultiRegionEngine:
    @classmethod
    def get_full_dashboard(cls) -> Dict[str, Any]:
        fx = VietcombankFXCollector.get_latest_verified_fx()
        rate_sell = fx.sell
        now = datetime.utcnow() + timedelta(hours=7)
        
        china_calculated = []
        for cn in CHINA_REGIONS_DEEP_PROFILES:
            item = dict(cn)
            if "fresh_cny_p50" in item:
                item["vnd_equivalent_kg"] = round(item["fresh_cny_p50"] * 2.0 * rate_sell, 0)
                item["vnd_p20_kg"] = round(item["fresh_cny_p20"] * 2.0 * rate_sell, 0)
                item["vnd_p80_kg"] = round(item["fresh_cny_p80"] * 2.0 * rate_sell, 0)
            china_calculated.append(item)
            
        return {
            "timestamp": now.isoformat(),
            "current_season_year": now.year,
            "system_version": "CAU360_DYNAMIC_MULTI_SEASON_V17.0",
            "fx_snapshot": {
                "bank": "Vietcombank",
                "transfer_buy": fx.transfer_buy,
                "sell": fx.sell,
                "cash_buy": fx.cash_buy,
                "analytical_mid": fx.analytical_mid,
                "source_time": fx.timestamp.strftime("%d/%m/%Y %H:%M ICT")
            },
            "vietnam_provinces": VIETNAM_REGIONS_DEEP_PROFILES,
            "china_regions": china_calculated
        }
