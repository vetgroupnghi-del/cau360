"""
Pydantic Data Models & Request/Response Schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from app.core.taxonomy import ProductStage, TransactionType, AuthorityLevel

# FX Schemas
class FXRateSnapshot(BaseModel):
    id: str
    timestamp: datetime
    bank: str = "Vietcombank"
    currency: str = "CNY"
    cash_buy: float
    transfer_buy: float
    sell: float
    analytical_mid: Optional[float] = None
    source_url: Optional[str] = None
    source_timestamp: Optional[datetime] = None

# Market Observation Ingest & Read
class ObservationCreate(BaseModel):
    source_id: str
    content_text: str
    url: Optional[str] = None
    screenshot_ref: Optional[str] = None
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    country: str = "VN"
    location_id: str
    province: Optional[str] = None
    district: Optional[str] = None
    product_stage: ProductStage
    product_name_raw: Optional[str] = None
    grade: Optional[str] = None
    process: Optional[str] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    price_exact: Optional[float] = None
    currency: str = "VND"
    unit: str = "KG"
    transaction_type: TransactionType = TransactionType.UNKNOWN
    volume: Optional[float] = None
    volume_unit: Optional[str] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None

class ObservationRead(BaseModel):
    id: str
    raw_id: Optional[str] = None
    observed_at: datetime
    country: str
    location_id: str
    location_name: Optional[str] = None
    product_stage: ProductStage
    product_name_raw: Optional[str] = None
    grade: Optional[str] = None
    process: Optional[str] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    price_exact: Optional[float] = None
    currency: str
    unit: str
    normalized_price_vnd_kg: Optional[float] = None
    fx_rate_used: Optional[float] = None
    transaction_type: TransactionType
    volume: Optional[float] = None
    volume_unit: Optional[str] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    source_id: str
    source_name: Optional[str] = None
    source_authority: Optional[str] = None
    evidence_score: float = 0.0
    verification_status: str = "PENDING"
    is_outlier: bool = False
    original_text: Optional[str] = None

# Consensus Price
class PriceConsensus(BaseModel):
    low: float      # P20
    consensus: float# P50
    high: float     # P80
    p10: Optional[float] = None
    p90: Optional[float] = None
    currency: str
    unit: str

class EvidenceSummary(BaseModel):
    observations: int
    transactions: int
    buyer_quotes: int
    seller_quotes: int
    confidence: float
    confidence_label: str

class LocationConsensusResponse(BaseModel):
    market: str
    location_id: str
    location_name: str
    country: str
    product_stage: ProductStage
    price: PriceConsensus
    evidence: EvidenceSummary
    change_1d_pct: Optional[float] = None
    change_3d_pct: Optional[float] = None
    change_7d_pct: Optional[float] = None
    updated_at: datetime

# Market Indices (WSSI, CBPI, MSI)
class MarketIndicesResponse(BaseModel):
    date: str
    location_id: str
    wssi: float # Weather Supply Stress Index (0-100)
    wssi_status: str # NORMAL, WATCH, MODERATE, HIGH_STRESS, EXTREME
    harvestability: float # 0-100 (100 = full)
    cbpi: float # Chinese Buying Pressure Index (0-100)
    cbpi_trend: str # SURGING, RISING, STABLE, EASING
    cbpi_momentum_1d: float
    cbpi_momentum_3d: float
    cbpi_momentum_7d: float
    msi: float # Market Supply Index (0-100)
    msi_status: str

# Weather Risk
class WeatherRiskResponse(BaseModel):
    location_id: str
    location_name: str
    country: str
    rain_24h_mm: float
    rain_72h_mm: float
    forecast_rain_72h_mm: float
    wind_speed_kmh: float
    warning_type: Optional[str] = None
    warning_level: Optional[str] = None
    wssi: float
    harvestability: float
    emergency_mode: bool = False

# Forecast
class ScenarioProb(BaseModel):
    base_case: Dict[str, Any]
    bullish: Dict[str, Any]
    bearish: Dict[str, Any]

class ForecastItem(BaseModel):
    horizon: str # 3D or 7D
    target_date: str
    direction: str # STRONG_UP, UP, SIDEWAYS, DOWN, STRONG_DOWN
    p10: float
    p50: float
    p90: float
    currency: str
    unit: str
    forecast_confidence: float
    positive_drivers: List[str]
    negative_drivers: List[str]
    invalidation_conditions: List[str]
    scenarios: ScenarioProb

# Full Market Snapshot
class MarketSnapshotResponse(BaseModel):
    timestamp: datetime
    vietnam_dry: LocationConsensusResponse
    china_fresh: LocationConsensusResponse
    china_dry: Optional[LocationConsensusResponse] = None
    hunan_demand: Dict[str, Any]
    fx: FXRateSnapshot
    indices: MarketIndicesResponse
    weather_risk: WeatherRiskResponse
    forecast_3d: ForecastItem
    forecast_7d: ForecastItem
    executive_summary: Dict[str, Any]
    alerts: List[Dict[str, Any]] = []

# Ingestion Bot Payload (Field Submission)
class IngestionBotSubmission(BaseModel):
    reporter_id: str
    raw_message: str
    image_url: Optional[str] = None
    detected_country: Optional[str] = "VN"
    detected_location: Optional[str] = None
    timestamp: Optional[datetime] = None
