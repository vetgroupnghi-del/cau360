"""
TAXONOMY & MULTI-TIER SOURCE REGISTRY V12.0
Mạng lưới 12 Nguồn Tình Báo Độc Lập phân cấp 4 Tầng Kiểm Chứng.
"""
from enum import Enum
from typing import List, Dict, Any

class AuthorityLevel(str, Enum):
    LEVEL_A = "OFFICIAL_STATE_INTERNATIONAL" # Tầng 1: Cơ quan nhà nước & Tổ chức quốc tế (Trọng số 1.0)
    LEVEL_B = "INDUSTRY_ASSOCIATION_MEDIA"  # Tầng 2: Hiệp hội ngành hàng & Báo chí kinh tế (Trọng số 0.85)
    LEVEL_C = "FIELD_LOGISTICS_WEIGH_STATION"# Tầng 3: Trạm cân thực địa & Đơn vị vận tải (Trọng số 0.75)
    LEVEL_D = "KILN_ALLIANCE_LEDGER"        # Tầng 4: Sổ cái liên minh lò sấy & Admin Dispatcher (Trọng số 0.90)

class ProductStage(str, Enum):
    FRESH = "FRESH"
    BOILED_DRY = "BOILED_DRY"
    SPLIT_DRIED = "SPLIT_DRIED"
    SLICED = "SLICED"

INITIAL_LOCATIONS = [
    {"id": "VN_DAKLAK", "country": "VN", "province": "Đắk Lắk", "district": "Krông Pắc", "market_role": "ORIGIN_GARDEN", "priority": 1, "name_vi": "Đắk Lắk", "name_cn": "多乐省"},
    {"id": "VN_GIALAI", "country": "VN", "province": "Gia Lai", "district": "Chư Sê", "market_role": "ORIGIN_GARDEN", "priority": 2, "name_vi": "Gia Lai", "name_cn": "嘉莱省"},
    {"id": "VN_DAKNONG", "country": "VN", "province": "Đắk Nông", "district": "Gia Nghĩa", "market_role": "ORIGIN_GARDEN", "priority": 3, "name_vi": "Đắk Nông", "name_cn": "得农省"},
    {"id": "VN_QUANGNGAI", "country": "VN", "province": "Quảng Ngãi", "district": "Sơn Tây", "market_role": "ORIGIN_GARDEN", "priority": 2, "name_vi": "Quảng Ngãi", "name_cn": "广义省"},
    {"id": "VN_HAIPHONG", "country": "VN", "province": "Hải Phòng", "district": "Thủy Nguyên", "market_role": "PROCESSING_HUB", "priority": 1, "name_vi": "Hải Phòng", "name_cn": "海防市"},
    {"id": "VN_NAMDINH", "country": "VN", "province": "Nam Định", "district": "Hải Hậu", "market_role": "PROCESSING_HUB", "priority": 1, "name_vi": "Nam Định", "name_cn": "南定省"},
    {"id": "VN_BENTRE", "country": "VN", "province": "Bến Tre", "district": "Chợ Lách", "market_role": "ORIGIN_GARDEN", "priority": 4, "name_vi": "Bến Tre", "name_cn": "槟椥省"},
    {"id": "VN_BORDER_LANGSON", "country": "VN", "province": "Lạng Sơn", "district": "Tân Thanh", "market_role": "BORDER_GATE", "priority": 1, "name_vi": "Cửa Khẩu Tân Thanh / Hữu Nghị", "name_cn": "新清/友谊口岸"},
    {"id": "CN_WANNING", "country": "CN", "province": "Hải Nam", "district": "Vạn Ninh", "market_role": "ORIGIN_GARDEN", "priority": 1, "name_vi": "Vạn Ninh (Hải Nam)", "name_cn": "万宁市"},
    {"id": "CN_HUNAN_XIANGTAN", "country": "CN", "province": "Hồ Nam", "district": "Tương Đàm", "market_role": "CONSUMPTION_CENTER", "priority": 1, "name_vi": "Tương Đàm (Hồ Nam)", "name_cn": "湘潭市"}
]

NETWORK_12_SOURCES_REGISTRY = [
    # TẦNG 1: CƠ QUAN NHÀ NƯỚC & TỔ CHỨC QUỐC TẾ (CẤP A)
    {
        "id": "SRC_01_VCB_FX",
        "tier": "TẦNG 1 (CẤP A)",
        "name": "Cổng Tỷ Giá XML Vietcombank & PBoC",
        "role": "Giám sát tỷ giá hối đoái CNY/VND/USD thời gian thực",
        "frequency": "Quét tự động mỗi giờ",
        "url": "https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia"
    },
    {
        "id": "SRC_02_NMC_CHINA",
        "tier": "TẦNG 1 (CẤP A)",
        "name": "Cục Khí Tượng Quốc Gia Trung Quốc (NMC) & Đài Vạn Ninh",
        "role": "Đo lượng mưa tích lũy 72h, bão nhiệt đới và tính chỉ số stress WSSI bờ Đông Hải Nam",
        "frequency": "Cập nhật 6 giờ/lần",
        "url": "http://www.weather.com.cn/alarm/newalarmcontent.shtml?file=101310215-20260822084023-0501.html"
    },
    {
        "id": "SRC_03_NCHMF_VN",
        "tier": "TẦNG 1 (CẤP A)",
        "name": "Trung Tâm Dự Báo Khí Tượng Thủy Văn Quốc Gia Việt Nam",
        "role": "Thời tiết mưa bão tại Tây Nguyên, Miền Trung và Bắc Bộ ảnh hưởng tiến độ sấy lò",
        "frequency": "Cập nhật 6 giờ/lần",
        "url": "https://nchmf.gov.vn"
    },
    {
        "id": "SRC_04_CUSTOMS_GACC",
        "tier": "TẦNG 1 (CẤP A)",
        "name": "Tổng Cục Hải Quan Việt Nam & Hải Quan Trung Quốc (GACC)",
        "role": "Quy định kiểm dịch thực vật Phyto, tiêu chuẩn nấm mốc Aflatoxin và chính sách biên mậu",
        "frequency": "Cập nhật hàng ngày",
        "url": "https://www.customs.gov.vn"
    },

    # TẦNG 2: HIỆP HỘI NGÀNH HÀNG & BÁO CHÍ KINH TẾ CHUYÊN SÂU (CẤP B)
    {
        "id": "SRC_05_HUNAN_ASSOCIATION",
        "tier": "TẦNG 2 (CẤP B)",
        "name": "Hiệp Hội Chế Biến Kẹo Cau Hồ Nam & Sàn Nông Sản Trung Quốc",
        "role": "Theo dõi tiến độ đơn hàng Tết, nhu cầu phụ gia keo điểm lộ, bạc hà của 300 xưởng",
        "frequency": "Hàng ngày",
        "url": "https://life.china.com/2026-08/19/content_619378.html"
    },
    {
        "id": "SRC_06_CHINESE_MEDIA",
        "tier": "TẦNG 2 (CẤP B)",
        "name": "China.com, Tân Hoa Xã & Tân Văn Xã Hải Nam",
        "role": "Báo cáo thực tế tình hình dịch bệnh vàng lá (YLD) và sản lượng thu hoạch tại Hải Nam",
        "frequency": "Hàng ngày",
        "url": "https://news.china.com"
    },
    {
        "id": "SRC_07_VN_PRESS",
        "tier": "TẦNG 2 (CẤP B)",
        "name": "Báo Tuổi Trẻ, Báo Lao Động, Báo Dân Việt & Tạp Chí Công Thương",
        "role": "Diễn biến giá cau tươi 8 tỉnh, thị trường nông sản và các vụ án biên giới",
        "frequency": "Hàng ngày",
        "url": "https://tuoitre.vn"
    },

    # TẦNG 3: TRẠM CÂN THỰC ĐỊA & LOGISTICS BIÊN MẬU (CẤP C)
    {
        "id": "SRC_08_HAINAN_WEIGH_STATIONS",
        "tier": "TẦNG 3 (CẤP C)",
        "name": "Mạng Lưới Trạm Cân Thu Mua Vạn Ninh, Quỳnh Hải, Định An (Hải Nam)",
        "role": "Báo giá mở phiên lúc 08:30 hàng ngày theo đơn vị chuẩn CNY/jin (500g)",
        "frequency": "Phiên sáng & chiều",
        "url": "field://hainan_stations"
    },
    {
        "id": "SRC_09_BORDER_LOGISTICS",
        "tier": "TẦNG 3 (CẤP C)",
        "name": "Hội Xe Container Lạnh & Đơn Vị Vận Tải Chuyên Tuyến Biên Giới",
        "role": "Thời gian xe chờ thông quan tại bãi Cốc Nam, Tân Thanh, Km3+4 Hải Yên Móng Cái",
        "frequency": "Liên tục 24/7",
        "url": "field://border_logistics"
    },
    {
        "id": "SRC_10_SUPPLY_INPUTS",
        "tier": "TẦNG 3 (CẤP C)",
        "name": "Đầu Mối Cung Ứng Than Củi, Bao Bì PE Hút Chân Không & Nhân Công Lặt Cuống",
        "role": "Cảnh báo biến động chi phí đầu vào của lò sấy để tự động điều chỉnh hàm giá trần",
        "frequency": "Hàng tuần",
        "url": "field://cost_inputs"
    },

    # TẦNG 4: SỔ CÁI LIÊN MINH LÒ SẤY & ADMIN FIELD DISPATCHER (CẤP C+)
    {
        "id": "SRC_11_KILN_ALLIANCE",
        "tier": "TẦNG 4 (CẤP C+)",
        "name": "Sổ Cái Phiếu Cân Thực Tế Từ 45 Lò Sấy Liên Minh (Đắk Lắk, Quảng Ngãi, Nam Định)",
        "role": "Ghi nhận mức giá chốt tiền tươi thực tế tại cửa lò, không qua miệng thổi giá của cò",
        "frequency": "Cập nhật theo từng mẻ cân",
        "url": "internal://kiln_ledger"
    },
    {
        "id": "SRC_12_ADMIN_DISPATCHER",
        "tier": "TẦNG 4 (CẤP C+)",
        "name": "Cổng Phát Tin Nóng Khẩn Cấp Của Admin & Trinh Sát Cửa Khẩu",
        "role": "Phát đi các thông báo đột xuất từ bãi mốc, trạm kiểm soát để toàn bộ hội viên cập nhật ngay",
        "frequency": "Thời gian thực 24/7",
        "url": "internal://admin_dispatcher"
    }
]
