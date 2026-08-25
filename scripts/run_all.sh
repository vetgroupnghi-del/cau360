#!/bin/bash
set -e

echo "=== KHỞI TẠO HỆ THỐNG CAU360 ==="
export PYTHONPATH=/working_dir/c_1c54295f1115b326/cau360

echo "1. Chạy bộ kiểm thử tự động toàn diện..."
python3 /working_dir/c_1c54295f1115b326/cau360/tests/test_all_rules.py

echo "2. Khởi tạo cơ sở dữ liệu và seed dữ liệu gốc..."
python3 /working_dir/c_1c54295f1115b326/cau360/app/core/database.py

echo "3. Sẵn sàng khởi động máy chủ FastAPI..."
echo "Lệnh khởi động: uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
