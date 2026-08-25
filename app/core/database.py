"""
CAU360 Database Engine & Schema Management (SQLite & PostgreSQL Compatible)
"""
import sqlite3
import json
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional
from app.core.config import settings
from app.core.taxonomy import INITIAL_LOCATIONS, ProductStage, AuthorityLevel

DDL_STATEMENTS = """
-- 1. Locations
CREATE TABLE IF NOT EXISTS market_locations (
    id TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    province TEXT NOT NULL,
    district TEXT,
    market_role TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    name_vi TEXT,
    name_cn TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sources Registry
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    url TEXT,
    language TEXT NOT NULL,
    expected_update_frequency_minutes INTEGER DEFAULT 360,
    freshness_limit_minutes INTEGER DEFAULT 720,
    last_success_at TIMESTAMP,
    last_data_at TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    reliability_score REAL DEFAULT 0.8,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Crawler Runs
CREATE TABLE IF NOT EXISTS crawler_runs (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id),
    status TEXT NOT NULL,
    records_fetched INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

-- 4. Raw Documents (Immutable)
CREATE TABLE IF NOT EXISTS raw_documents (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id),
    url TEXT,
    content_text TEXT NOT NULL,
    content_html TEXT,
    screenshot_ref TEXT,
    document_hash TEXT UNIQUE NOT NULL,
    language TEXT,
    metadata_json TEXT,
    retrieved_at TIMESTAMP NOT NULL,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. FX Rates (Snapshots - No overwrites)
CREATE TABLE IF NOT EXISTS fx_rates (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    bank TEXT NOT NULL,
    currency TEXT NOT NULL,
    cash_buy REAL,
    transfer_buy REAL,
    sell REAL,
    source_url TEXT,
    source_timestamp TIMESTAMP,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Product Master
CREATE TABLE IF NOT EXISTS product_master (
    id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    name_vi TEXT NOT NULL,
    name_cn TEXT NOT NULL,
    description TEXT
);

-- 7. Market Observations
CREATE TABLE IF NOT EXISTS market_observations (
    id TEXT PRIMARY KEY,
    raw_id TEXT REFERENCES raw_documents(id),
    observed_at TIMESTAMP NOT NULL,
    published_at TIMESTAMP,
    country TEXT NOT NULL,
    location_id TEXT REFERENCES market_locations(id),
    province TEXT,
    district TEXT,
    product_stage TEXT NOT NULL,
    product_name_raw TEXT,
    grade TEXT,
    size TEXT,
    moisture TEXT,
    process TEXT,
    price_low REAL,
    price_high REAL,
    price_exact REAL,
    currency TEXT NOT NULL,
    unit TEXT NOT NULL,
    normalized_price_vnd_kg REAL,
    fx_rate_used REAL,
    fx_snapshot_id TEXT REFERENCES fx_rates(id),
    transaction_type TEXT NOT NULL,
    volume REAL,
    volume_unit TEXT,
    buyer TEXT,
    seller TEXT,
    source_id TEXT REFERENCES sources(id),
    extract_confidence REAL DEFAULT 0.0,
    classification_confidence REAL DEFAULT 0.0,
    evidence_score REAL DEFAULT 0.0,
    verification_status TEXT DEFAULT 'PENDING', -- PENDING, VERIFIED, REJECTED
    duplicate_cluster_id TEXT,
    is_outlier INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Observation Corrections
CREATE TABLE IF NOT EXISTS observation_corrections (
    id TEXT PRIMARY KEY,
    observation_id TEXT REFERENCES market_observations(id),
    old_value_json TEXT NOT NULL,
    new_value_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Weather Observations
CREATE TABLE IF NOT EXISTS weather_observations (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    country TEXT NOT NULL,
    location_id TEXT REFERENCES market_locations(id),
    temperature REAL,
    humidity REAL,
    rain_1h REAL,
    rain_24h REAL,
    rain_72h REAL,
    wind_speed REAL,
    wind_gust REAL,
    warning_type TEXT,
    warning_level TEXT,
    source_id TEXT REFERENCES sources(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Weather Forecasts
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id TEXT PRIMARY KEY,
    issued_at TIMESTAMP NOT NULL,
    valid_time TIMESTAMP NOT NULL,
    location_id TEXT REFERENCES market_locations(id),
    forecast_rain REAL,
    rain_probability REAL,
    wind REAL,
    gust REAL,
    storm_probability REAL,
    warning_level TEXT,
    forecast_horizon_hours INTEGER,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Daily Market Consensus
CREATE TABLE IF NOT EXISTS daily_market_consensus (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    location_id TEXT REFERENCES market_locations(id),
    product_stage TEXT NOT NULL,
    currency TEXT NOT NULL,
    unit TEXT NOT NULL,
    price_p10 REAL,
    price_p20 REAL,
    price_p50 REAL, -- Main Consensus
    price_p80 REAL,
    price_p90 REAL,
    observation_count INTEGER NOT NULL,
    confirmed_tx_count INTEGER NOT NULL,
    buyer_quote_count INTEGER NOT NULL,
    seller_quote_count INTEGER NOT NULL,
    data_confidence_score REAL NOT NULL,
    confidence_label TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, location_id, product_stage)
);

-- 12. Market Indices (WSSI, CBPI, MSI, Harvestability)
CREATE TABLE IF NOT EXISTS market_indices (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    location_id TEXT REFERENCES market_locations(id),
    wssi REAL,               -- Weather Supply Stress Index (0-100)
    harvestability REAL,     -- 0-100 (100 = optimal)
    cbpi REAL,               -- Chinese Buying Pressure Index (0-100)
    cbpi_momentum_1d REAL,
    cbpi_momentum_3d REAL,
    cbpi_momentum_7d REAL,
    msi REAL,                -- Market Supply Index (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, location_id)
);

-- 13. Forecasts
CREATE TABLE IF NOT EXISTS forecasts (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date TEXT NOT NULL,
    horizon_days INTEGER NOT NULL, -- 3 or 7
    location_id TEXT REFERENCES market_locations(id),
    product_stage TEXT NOT NULL,
    p10 REAL NOT NULL,
    p50 REAL NOT NULL,
    p90 REAL NOT NULL,
    direction TEXT NOT NULL, -- STRONG_UP, UP, SIDEWAYS, DOWN, STRONG_DOWN
    forecast_confidence REAL NOT NULL,
    base_case_prob REAL,
    bullish_prob REAL,
    bearish_prob REAL,
    positive_drivers_json TEXT,
    negative_drivers_json TEXT,
    invalidation_conditions_json TEXT,
    model_version TEXT NOT NULL,
    features_snapshot_json TEXT
);

-- 14. Forecast Evaluation (Backtesting)
CREATE TABLE IF NOT EXISTS forecast_results (
    id TEXT PRIMARY KEY,
    forecast_id TEXT REFERENCES forecasts(id),
    actual_price REAL,
    absolute_error REAL,
    percentage_error REAL,
    direction_correct INTEGER,
    range_hit INTEGER,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL, -- INFO, WARNING, CRITICAL
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    location_id TEXT,
    data_json TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ultra-fast query performance
CREATE INDEX IF NOT EXISTS idx_obs_location_stage_time ON market_observations(location_id, product_stage, observed_at);
CREATE INDEX IF NOT EXISTS idx_obs_hash ON raw_documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_consensus_date ON daily_market_consensus(date, location_id);
CREATE INDEX IF NOT EXISTS idx_fx_timestamp ON fx_rates(timestamp);
CREATE INDEX IF NOT EXISTS idx_forecasts_target ON forecasts(target_date, horizon_days);
"""

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        conn.executescript(DDL_STATEMENTS)
        
        # Seed Initial Locations
        for loc in INITIAL_LOCATIONS:
            conn.execute("""
                INSERT OR IGNORE INTO market_locations (id, country, province, district, market_role, priority, name_vi, name_cn)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (loc["id"], loc["country"], loc["province"], loc["district"], loc["market_role"], loc["priority"], loc["name_vi"], loc["name_cn"]))
        
        # Seed Product Master
        products = [
            ("FRESH_FRUIT", "FRESH_FRUIT", "Cau tươi", "鲜槟榔 / 鲜果", "Cau tươi nguyên buồng hoặc xô hái tại vườn"),
            ("GREEN_FRUIT", "GREEN_FRUIT", "Cau xanh", "青果 / 生果", "Cau quả xanh đạt chuẩn kích thước chuẩn bị chế biến"),
            ("DRY_RAW", "DRY_RAW", "Cau khô nguyên liệu", "干槟榔 / 干果", "Cau sấy khô nguyên liệu xuất khẩu"),
            ("DRY_BLACK", "DRY_BLACK", "Cau sấy than (hàng đen)", "黑果 / 炙烤果", "Cau sấy bằng lò than truyền thống"),
            ("DRY_WHITE", "DRY_WHITE", "Cau sấy điện (hàng trắng)", "白果 / 电烤果", "Cau sấy lò điện/hơi công nghệ mới"),
            ("FINISHED_PRODUCT", "FINISHED_PRODUCT", "Cau thành phẩm", "槟榔制品", "Kẹo cau, cau ngâm gia vị thành phẩm đóng gói")
        ]
        for p in products:
            conn.execute("""
                INSERT OR IGNORE INTO product_master (id, stage, name_vi, name_cn, description)
                VALUES (?, ?, ?, ?, ?)
            """, p)
            
        # Seed Baseline Sources
        sources = [
            ("SRC_VCB_FX", "Vietcombank Official FX", "VN", "OFFICIAL_API", "OFFICIAL", AuthorityLevel.LEVEL_A, "https://vietcombank.com.vn", "VI", 60, 180, 1.0),
            ("SRC_NMC_WEATHER", "China National Meteorological Center", "CN", "OFFICIAL_API", "WEATHER", AuthorityLevel.LEVEL_A, "http://www.nmc.cn", "ZH", 180, 360, 1.0),
            ("SRC_NCHMF_WEATHER", "VN National Center for Hydro-Meteorological Forecasting", "VN", "OFFICIAL_API", "WEATHER", AuthorityLevel.LEVEL_A, "https://nchmf.gov.vn", "VI", 180, 360, 1.0),
            ("SRC_FIELD_AGENT_BOT", "Cau360 Verified Field Telegram/Zalo Bot", "VN", "BOT", "DIRECT_TRADER", AuthorityLevel.LEVEL_C, "tg://cau360_field_bot", "VI", 60, 720, 0.85),
            ("SRC_DOUYIN_MARKET", "Douyin Hainan Areca Market Hub", "CN", "SOCIAL", "PUBLIC_SIGNAL", AuthorityLevel.LEVEL_D, "https://www.douyin.com", "ZH", 120, 720, 0.50),
            ("SRC_FB_ARECA_VN", "Hội Cau Sấy Việt Nam Facebook Signal", "VN", "SOCIAL", "PUBLIC_SIGNAL", AuthorityLevel.LEVEL_D, "https://facebook.com", "VI", 120, 720, 0.50)
        ]
        for s in sources:
            conn.execute("""
                INSERT OR IGNORE INTO sources (id, name, country, platform, source_type, authority_level, url, language, expected_update_frequency_minutes, freshness_limit_minutes, reliability_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, s)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
