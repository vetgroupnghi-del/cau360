# CAU360 — MARKET INTELLIGENCE & ANTI-MANIPULATION SYSTEM V1.0

Hệ thống tình báo thị trường và bộ công cụ tác chiến kinh tế chuỗi cung ứng cau Việt Nam ↔ Trung Quốc.

---

## 1. Cấu trúc thư mục

```text
cau360/
├── app/
│   ├── core/               # Cấu hình, kết nối DB, ontology & phân loại địa bàn
│   │   ├── config.py
│   │   ├── database.py
│   │   └── taxonomy.py
│   ├── models/             # Pydantic Schemas request / response
│   │   └── schemas.py
│   ├── collectors/         # Bộ thu thập tỷ giá Vietcombank & thời tiết
│   │   └── fx_vcb.py
│   ├── engines/            # Các module giải thuật & động cơ tác chiến
│   │   ├── nlp_parser.py       # Bóc tách thực thể 2 tầng (Regex + JSON)
│   │   ├── normalizer.py       # Chuẩn hóa đơn vị 1 jin = 0.5 kg & tỷ giá VCB
│   │   ├── dedup.py            # Lọc trùng lặp bài đăng mạng xã hội (SimHash)
│   │   ├── outlier.py          # Lọc giá ảo Adjusted MAD (chống lỗi mẫu nhỏ)
│   │   ├── consensus.py        # Tính giá đồng thuận P50 có trọng số (Weighted Median)
│   │   ├── scoring.py          # WSSI, CBPI, MSI & Harvestability
│   │   ├── forecast.py         # Dự báo lượng hóa 3D & 7D có điều kiện Invalidation
│   │   ├── quality_gate.py     # 7 cổng kiểm soát dữ liệu trước khi tính giá
│   │   ├── kiln_costing.py     # Định giá vốn mẻ sấy & Khóa trần mua cau tươi an toàn
│   │   ├── early_radar.py      # Radar tín hiệu sớm từ Trung Quốc trước 60 ngày
│   │   └── tactics_suite.py    # Máy đo BPR, Hộ chiếu chất lượng & Radar bẫy dìm giá
│   └── api/
│       ├── routes.py       # REST API endpoints
│       └── main.py         # FastAPI application entrypoint
├── frontend/               # Giao diện Web PWA Mobile-First
│   ├── index.html          # Command Center UI & Form nạp tin nhanh
│   ├── manifest.json       # PWA Web Manifest (cài đặt lên điện thoại)
│   ├── sw.js               # Service Worker lưu cache ngoại tuyến
│   ├── css/
│   │   └── styles.css      # Dark mode terminal styling tối ưu di động
│   └── js/
│       └── app.js          # Controller điều khiển giao diện & gọi API
├── tests/
│   └── test_all_rules.py   # Toàn bộ Unit Tests kiểm thử tự động Rules 99 - 111
└── scripts/
    └── run_all.sh          # Script khởi động tự động 1 lệnh
```

---

## 2. Hướng dẫn khởi chạy nhanh (Quick Start)

### Yêu cầu môi trường:
* Python 3.9+
* FastAPI, Uvicorn, Pydantic, NumPy, Beautifulsoup4, lxml

### Khởi động hệ thống:
```bash
# 1. Cài đặt thư viện (nếu chưa có)
pip install fastapi uvicorn pydantic numpy beautifulsoup4 lxml

# 2. Khởi động máy chủ
export PYTHONPATH=$(pwd)
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

* **Trang web ứng dụng Mobile PWA:** `http://localhost:8000/app/`
* **Tài liệu API Swagger:** `http://localhost:8000/docs`

---

## 3. Cài đặt lên màn hình điện thoại (PWA)

1. Mở trình duyệt trên điện thoại truy cập: `http://<IP_MAY_CHU>:8000/app/`
2. **Trên iPhone (Safari):** Bấm nút **Chia sẻ (Share)** $\to$ Chọn **Thêm vào MH chính** (*Add to Home Screen*).
3. **Trên Android (Chrome):** Bấm menu **3 chấm** $\to$ Chọn **Cài đặt ứng dụng** (*Install App*).
