"""
CAU360 MASTER API ROUTERS V4.0
Tình báo đa vùng, Tỷ giá Vietcombank Live, Bộ phản đòn lò sấy,
Biểu đồ 7D & Hệ Thống Quản Lý Hội Viên & Thu Phí Gói Cước (SaaS Subscription).
"""
from fastapi import APIRouter, Body, HTTPException
from app.collectors.fx_vcb import VietcombankFXCollector
from app.engines.multi_region import MultiRegionEngine
from app.engines.kiln_costing import KilnCostingEngine
from app.engines.early_radar import EarlyChinaRadar
from app.engines.tactics_suite import TacticsSuite
from app.engines.chart_engine import ChartEngine
from app.engines.intelligence_feed import IntelligenceFeedEngine
from app.core.security import AuthManager
import datetime

router = APIRouter()

# ----------------------------------------------------
# 1. AUTHENTICATION & LOGIN
# ----------------------------------------------------
@router.post("/auth/login")
def login_endpoint(username: str = Body(..., embed=True), password: str = Body(..., embed=True)):
    """Đăng nhập hệ thống CAU360 kèm kiểm tra hạn sử dụng gói cước."""
    user = AuthManager.authenticate(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác!")
    if "error" in user:
        raise HTTPException(status_code=403, detail=user["message"])
    return {"success": True, "user": user}

# ----------------------------------------------------
# 2. ADMIN SUBSCRIPTION & USER MANAGEMENT
# ----------------------------------------------------
@router.get("/admin/subscription-dashboard")
def get_subscription_dashboard():
    """Lấy thống kê tổng quan hội viên, số lượng đang dùng, sắp hết hạn (3 ngày) và doanh thu."""
    return AuthManager.get_subscription_dashboard()

@router.post("/admin/users/create")
def create_user_with_plan(
    username: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    display_name: str = Body(..., embed=True),
    phone: str = Body("", embed=True),
    role: str = Body("MEMBER", embed=True),
    plan_type: str = Body("1_MONTH", embed=True),
    custom_days: int = Body(30, embed=True),
    price_vnd: float = Body(0.0, embed=True)
):
    """Admin tạo tài khoản mới kèm gán gói cước thời hạn (1T, 3T, 6T, 12T, tùy chỉnh) và giá tiền."""
    res = AuthManager.create_user_with_plan(
        username=username, password=password, display_name=display_name,
        phone=phone, role=role, plan_type=plan_type, custom_days=custom_days, price_vnd=price_vnd
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/admin/users/renew")
def renew_user(
    user_id: str = Body(..., embed=True),
    plan_type: str = Body("1_MONTH", embed=True),
    custom_days: int = Body(30, embed=True),
    amount_paid: float = Body(0.0, embed=True)
):
    """Admin gia hạn gói cước cho hội viên."""
    res = AuthManager.renew_subscription(user_id=user_id, plan_type=plan_type, custom_days=custom_days, amount_paid_vnd=amount_paid)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/admin/users/reset-password")
def reset_password(
    user_id: str = Body(..., embed=True),
    new_password: str = Body(..., embed=True)
):
    """Admin đặt lại mật khẩu cho người dùng khi quên mật khẩu."""
    res = AuthManager.reset_password(user_id=user_id, new_password=new_password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/admin/users/toggle-status")
def toggle_status(user_id: str = Body(..., embed=True)):
    """Admin khóa hoặc mở khóa tài khoản."""
    res = AuthManager.toggle_user_status(user_id=user_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

# ----------------------------------------------------
# 3. LIVE FX & MULTI-REGION
# ----------------------------------------------------
@router.get("/fx/live")
def get_live_fx(refresh: bool = False):
    fx = VietcombankFXCollector.get_latest_verified_fx(force_refresh=refresh)
    return {
        "bank": "Vietcombank", "currency": "CNY",
        "cash_buy": fx.cash_buy, "transfer_buy": fx.transfer_buy, "sell": fx.sell,
        "analytical_mid": fx.analytical_mid, "timestamp": fx.timestamp.isoformat(),
        "source_url": fx.source_url
    }

@router.get("/market/multi-region")
def get_multi_region():
    return MultiRegionEngine.get_full_dashboard()

@router.get("/intelligence/live-24h")
def get_live_24h_intelligence():
    return IntelligenceFeedEngine.get_live_24h_feed()

@router.get("/charts/vietnam")
def get_vietnam_chart():
    return ChartEngine.get_vietnam_chart_data()

@router.get("/charts/china")
def get_china_chart():
    return ChartEngine.get_china_chart_data()

@router.get("/radar/early-china")
def get_early_china_radar():
    return EarlyChinaRadar.calculate_early_import_demand(
        hainan_yield_loss_pct=42.0, hunan_cold_storage_depletion_pct=82.0,
        packaging_order_growth_pct=25.0, additive_demand_score=80.0
    )

# ----------------------------------------------------
# 4. TACTICAL ENGINES
# ----------------------------------------------------
@router.post("/tactics/custom-batch-profit")
def calculate_custom_batch_profit(
    fresh_price: float = Body(20000.0, embed=True),
    dry_selling_price: float = Body(192500.0, embed=True),
    fresh_to_dry_ratio: float = Body(6.0, embed=True),
    batch_weight_kg: float = Body(10000.0, embed=True),
    raw_type: str = Body("BUNCH", embed=True),
    stem_tare_pct: float = Body(20.0, embed=True),
    fuel_cost_per_kg_dry: float = Body(12000.0, embed=True),
    labor_fresh_per_kg: float = Body(500.0, embed=True),
    packaging_per_kg_dry: float = Body(1200.0, embed=True),
    waste_rate: float = Body(0.04, embed=True),
    china_wholesale_cny_jin: float = Body(102.0, embed=True)
):
    return KilnCostingEngine.calculate_custom_batch_profit(
        fresh_price_vnd_kg=fresh_price, dry_selling_price_vnd_kg=dry_selling_price,
        fresh_to_dry_ratio=fresh_to_dry_ratio, batch_fresh_weight_kg=batch_weight_kg,
        raw_type=raw_type, stem_tare_pct=stem_tare_pct,
        fuel_cost_per_kg_dry=fuel_cost_per_kg_dry, labor_fresh_per_kg=labor_fresh_per_kg,
        packaging_per_kg_dry=packaging_per_kg_dry, waste_defect_rate=waste_rate,
        china_wholesale_cny_jin=china_wholesale_cny_jin
    )

@router.post("/tactics/safe-ceiling")
def safe_ceiling(expected_dry: float = Body(190000.0, embed=True), fresh_quote: float = Body(35000.0, embed=True), lunar_month: int = Body(8, embed=True)):
    return KilnCostingEngine.calculate_costing_and_ceiling(lunar_month=lunar_month, expected_dry_price_vnd=expected_dry, fresh_price_quote_vnd=fresh_quote)

@router.post("/tactics/bpr")
def bpr_calc(total_tons: float = Body(20.0, embed=True), moisture: float = Body(10.8, embed=True), days_to_peak: int = Body(40, embed=True), debt_due: float = Body(300000000.0, embed=True)):
    return TacticsSuite.calculate_liquidity_aware_bpr(total_inventory_tons=total_tons, kiln_moisture_pct=moisture, days_to_peak_season=days_to_peak, hunan_demand_urgency_score=85.0, monthly_debt_due_vnd=debt_due, current_market_price_p50_vnd_kg=190000.0)

@router.post("/tactics/passport")
def passport_calc(lot_id: str = Body("LOT_VN_001", embed=True), total_kg: float = Body(10000.0, embed=True), p_long: float = Body(0.60, embed=True), p_round: float = Body(0.30, embed=True), p_broken: float = Body(0.10, embed=True), price_long: float = Body(200000.0, embed=True), price_round: float = Body(175000.0, embed=True), price_broken: float = Body(90000.0, embed=True), lowball_offer: float = Body(165000.0, embed=True)):
    return TacticsSuite.generate_grade_split_passport(lot_id=lot_id, total_lot_kg=total_kg, pct_long=p_long, pct_round=p_round, pct_broken=p_broken, price_long_market=price_long, price_round_market=price_round, price_broken_market=price_broken, trader_lowball_offer=lowball_offer)

@router.post("/admin/users/delete")
def delete_user_endpoint(user_id: str = Body(..., embed=True)):
    """Admin xóa vĩnh viễn tài khoản hội viên."""
    res = AuthManager.delete_user(user_id=user_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

# ==========================================
# BREAKING NEWS & FIELD INTELLIGENCE DISPATCHER
# ==========================================
@router.post("/intelligence/post-news")
def post_breaking_news_endpoint(
    title: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    tag: str = Body("TIN NÓNG THỰC ĐỊA", embed=True),
    category: str = Body("FIELD", embed=True),
    impact: str = Body("POSITIVE", embed=True),
    source_name: str = Body("Chủ Lò / Trinh Sát Thực Địa", embed=True),
    source_url: str = Body("", embed=True),
    action: str = Body("Theo dõi và điều chỉnh kế hoạch thu mua.", embed=True)
):
    """Admin đăng bản tin nóng thực địa 24h đưa lên đầu bảng tin cho toàn bộ hội viên."""
    return IntelligenceFeedEngine.post_breaking_news(
        title=title, content=content, tag=tag, category=category,
        impact=impact, source_name=source_name, source_url=source_url, action=action
    )

@router.delete("/intelligence/news/{news_id}")
def delete_news_endpoint(news_id: str):
    """Admin xóa bản tin nóng đã đăng."""
    return IntelligenceFeedEngine.delete_news_item(news_id=news_id)

# ==========================================
# HOTSPOT 24H DUAL-EXPERT STRATEGIC BRIEFING
# ==========================================
from app.engines.hotspot_briefing import HotspotBriefingEngine

@router.get("/intelligence/hotspot-24h")
def get_hotspot_24h_briefing():
    """Lấy 2 bài phân tích chuyên sâu đối trọng nhau mỗi ngày (Chuyên gia VN & Chuyên gia TQ)."""
    return HotspotBriefingEngine.get_daily_hotspot_briefing()

# ==========================================
# MOISTURE & AFLATOXIN RISK GUARD
# ==========================================
from app.engines.moisture_guard import MoistureGuardEngine

@router.post("/tactics/moisture-guard")
def evaluate_moisture_guard(
    core_moisture_pct: float = Body(10.5, embed=True),
    kiln_drying_hours: int = Body(48, embed=True),
    transport_days: int = Body(4, embed=True),
    packaging_type: str = Body("PE_DOUBLE_LINED", embed=True)
):
    """Đánh giá rủi ro độ ẩm lõi hạt và cảnh báo mồ hôi container xuất khẩu."""
    return MoistureGuardEngine.evaluate_moisture_risk(
        core_moisture_pct=core_moisture_pct,
        kiln_drying_hours=kiln_drying_hours,
        transport_days=transport_days,
        packaging_type=packaging_type
    )

# ==========================================
# XINHUA ARECA NUT PRICE INDEX YOY
# ==========================================
from app.engines.xinhua_index import XinhuaIndexEngine

@router.get("/charts/xinhua-index-3years")
@router.get("/charts/xinhua-index-yoy")
def get_xinhua_index_3years():
    """Lấy dữ liệu đối soát Chỉ Số Giá Tân Hoa (Xinhua Index) 3 Năm Liên Tiếp (2024 - 2025 - 2026)."""
    return XinhuaIndexEngine.get_xinhua_3year_analytics()
