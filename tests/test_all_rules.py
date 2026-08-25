"""
CAU360 Comprehensive Automated Unit Test Suite (Rules 99 - 111)
"""
import unittest
import datetime
from app.core.taxonomy import ProductStage, TransactionType
from app.collectors.fx_vcb import VietcombankFXCollector
from app.engines.normalizer import Normalizer
from app.engines.nlp_parser import MarketNLPParser
from app.engines.dedup import DeduplicationEngine
from app.engines.outlier import OutlierEngine
from app.engines.consensus import ConsensusEngine
from app.engines.scoring import ScoringEngine
from app.engines.forecast import ForecastEngineV1
from app.engines.quality_gate import QualityGate
from app.models.schemas import FXRateSnapshot

class TestCau360Rules(unittest.TestCase):
    def setUp(self):
        self.mock_fx = FXRateSnapshot(
            id="FX_TEST_001",
            timestamp=datetime.datetime.utcnow(),
            bank="Vietcombank",
            currency="CNY",
            cash_buy=3430.0,
            transfer_buy=3465.0,
            sell=3580.0,
            analytical_mid=3522.5
        )

    # RULE 99: Unit & Currency Conversions
    def test_rule_99_unit_and_fx_conversion(self):
        # 1 jin = 0.5 kg
        canonical, mult = Normalizer.normalize_unit_to_kg("jin")
        self.assertEqual(canonical, "JIN")
        self.assertEqual(mult, 0.5)
        
        # 35 CNY/jin = 70 CNY/kg
        # In VND: 70 * 3580 = 250,600 VND/kg
        norm_price, rate, fx_id = Normalizer.normalize_price_to_vnd_kg(
            price_val=35.0,
            currency="CNY",
            unit="JIN",
            fx_snapshot=self.mock_fx,
            use_rate_type="SELL"
        )
        self.assertEqual(norm_price, 250600.0)
        self.assertEqual(rate, 3580.0)
        self.assertEqual(fx_id, "FX_TEST_001")

    # RULE 100: Product Stage NLP Extraction
    def test_rule_100_product_nlp_extraction(self):
        raw_text = "万宁鲜槟榔35元一斤，大量收购"
        parsed = MarketNLPParser.parse_document(raw_text)
        
        self.assertEqual(parsed["product_stage"], ProductStage.FRESH_FRUIT.value)
        self.assertEqual(parsed["price_exact"], 35.0)
        self.assertEqual(parsed["currency"], "CNY")
        self.assertEqual(parsed["unit"], "JIN")
        self.assertEqual(parsed["location_id"], "CN_HAINAN_WANNING")

    # RULE 101: Transaction Type NLP Extraction
    def test_rule_101_transaction_nlp_extraction(self):
        raw_text = "Hôm nay lò cần thu mua cau sấy khô nguyên liệu tại Đắk Lắk giá 190k/kg"
        parsed = MarketNLPParser.parse_document(raw_text)
        
        self.assertEqual(parsed["product_stage"], ProductStage.DRY_RAW.value)
        self.assertEqual(parsed["transaction_type"], TransactionType.BUYER_QUOTE.value)
        self.assertEqual(parsed["price_exact"], 190000.0)
        self.assertEqual(parsed["location_id"], "VN_DAKLAK")

    # RULE 102: Wrong Aggregation Prevention
    def test_rule_102_wrong_aggregation(self):
        fresh_stage = ProductStage.FRESH_FRUIT.value
        dry_stage = ProductStage.DRY_RAW.value
        self.assertNotEqual(fresh_stage, dry_stage)
        
        # When user asks for Fresh vs Dry comparison, must use Theoretical Conversion Scenario
        scenario = Normalizer.calculate_fresh_to_dry_scenario(
            cny_per_jin=35.0,
            processing_cost_vnd_kg=8000.0,
            fx_snapshot=self.mock_fx
        )
        self.assertIn("THEORETICAL CONVERSION SCENARIO ONLY", scenario["disclaimer"])
        self.assertIn("p10", scenario["dry_equivalent_cost_vnd_kg"])
        self.assertIn("p50", scenario["dry_equivalent_cost_vnd_kg"])
        self.assertIn("p90", scenario["dry_equivalent_cost_vnd_kg"])

    # RULE 104: Outlier Detection with Adjusted MAD
    def test_rule_104_outlier_detection(self):
        prices = [188000.0, 189000.0, 190000.0, 190000.0, 191000.0, 245000.0]
        outliers = OutlierEngine.detect_outliers_adjusted_mad(prices)
        
        # 245,000 must be flagged as outlier
        self.assertFalse(outliers[0]) # 188k normal
        self.assertFalse(outliers[2]) # 190k normal
        self.assertTrue(outliers[5])  # 245k outlier

    # RULE 105: Deduplication Clustering
    def test_rule_105_deduplication(self):
        post_a = "Đắk Lắk hôm nay thu mua cau sấy 190k/kg hàng đẹp"
        post_b = "Đắk Lắk hôm nay thu mua cau sấy 190k/kg hàng đẹp liên hệ ngay"
        
        cluster_a = DeduplicationEngine.compute_semantic_simhash(post_a, 190000.0, "VN_DAKLAK")
        cluster_b = DeduplicationEngine.compute_semantic_simhash(post_b, 190000.0, "VN_DAKLAK")
        
        # Similar posts share the same cluster
        self.assertEqual(cluster_a, cluster_b)

    # RULE 109: Consensus Weighted Median
    def test_rule_109_weighted_median_consensus(self):
        # 1 buyer quote at 188k, 2 confirmed transactions at 190k, 1 seller quote at 205k
        prices = [188000.0, 190000.0, 190000.0, 205000.0]
        weights = [0.80, 1.00, 1.00, 0.45] # confirmed tx has higher weight
        
        quantiles = ConsensusEngine.calculate_weighted_quantiles(prices, weights)
        # Weighted median P50 must gravitate towards confirmed 190k, not simple average (193.25k)
        self.assertEqual(quantiles["p50"], 190000.0)

    # RULE 110: Quality Gate
    def test_rule_110_quality_gate(self):
        # Valid observation
        pass_ok, reason_ok = QualityGate.validate_observation(
            product_stage=ProductStage.DRY_RAW.value,
            location_id="VN_DAKLAK",
            currency="VND",
            unit="KG",
            price=190000.0
        )
        self.assertTrue(pass_ok)
        self.assertEqual(reason_ok, "PASS_QUALITY_GATE")
        
        # Invalid observation (unknown product stage)
        fail_stage, reason_fail = QualityGate.validate_observation(
            product_stage=ProductStage.UNKNOWN.value,
            location_id="VN_DAKLAK",
            price=190000.0
        )
        self.assertFalse(fail_stage)
        self.assertEqual(reason_fail, "FAIL_PRODUCT_STAGE_UNKNOWN")

    # RULE 111 & RULE 55: Forecast Engine
    def test_rule_111_forecast_generation(self):
        forecast_3d = ForecastEngineV1.generate_forecast(
            horizon_days=3,
            current_price_p50=190000.0,
            price_1d_pct=0.015,
            price_3d_pct=0.030,
            cbpi=75.0,
            cbpi_momentum_3d=14.0,
            wssi=65.0,
            msi=35.0,
            data_confidence=85.0
        )
        self.assertIn(forecast_3d.direction, ["UP", "STRONG_UP"])
        self.assertGreater(forecast_3d.p50, 190000.0)
        self.assertGreater(len(forecast_3d.positive_drivers), 0)
        self.assertGreater(len(forecast_3d.invalidation_conditions), 0)

if __name__ == "__main__":
    unittest.main()
