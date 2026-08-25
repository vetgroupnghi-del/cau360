"""
2-Stage NLP & Pattern-Driven Market Parser (Rules 06, 14, 84, 100, 101)
Stage 1: Fast Regex Filter
Stage 2: Multilingual Semantic & Entity Extractor with Structured JSON Output
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from app.core.taxonomy import ProductStage, TransactionType, SLANG_DICTIONARY, INITIAL_LOCATIONS

class MarketNLPParser:
    # Stage 1 Regex: Must match areca keywords or price signals
    ARECA_FAST_REGEX = re.compile(
        r"(槟榔|鲜果|青果|干果|黑果|白果|cau|sấy|buồng|vựa|lò|giá|thu mua|cần mua|bán|cân|chốt|斤|kg|kí|k|đ|元|块)",
        re.IGNORECASE
    )

    @classmethod
    def quick_filter(cls, text: str) -> bool:
        """Stage 1: Discards non-market noise instantly."""
        return bool(cls.ARECA_FAST_REGEX.search(text))

    @classmethod
    def parse_document(cls, text: str, default_country: str = "VN") -> Dict[str, Any]:
        """
        Stage 2: Full Entity Extraction & Taxonomy Classification
        """
        text_clean = text.strip()
        is_chinese = bool(re.search(r"[\u4e00-\u9fff]", text_clean))
        
        # 1. Product Stage Classification
        product_stage = cls._detect_product_stage(text_clean, is_chinese)
        
        # 2. Transaction Type Classification
        tx_type, tx_confidence = cls._detect_transaction_type(text_clean, is_chinese)
        
        # 3. Location Detection
        location_id, loc_confidence = cls._detect_location(text_clean, is_chinese, default_country)
        
        # 4. Price & Unit Extraction (Separates volume from unit price)
        price_exact, price_low, price_high, currency, unit = cls._extract_price_and_unit(text_clean, is_chinese)
        
        # Quality score of extraction
        extract_confidence = 0.4
        if price_exact or (price_low and price_high):
            extract_confidence += 0.3
        if location_id:
            extract_confidence += 0.2
        if product_stage != ProductStage.UNKNOWN:
            extract_confidence += 0.1
            
        return {
            "is_market_signal": True,
            "product_stage": product_stage.value,
            "transaction_type": tx_type.value,
            "location_id": location_id,
            "price_exact": price_exact,
            "price_low": price_low,
            "price_high": price_high,
            "currency": currency,
            "unit": unit,
            "extract_confidence": round(min(extract_confidence, 1.0), 2),
            "tx_confidence": tx_confidence,
            "needs_review": (product_stage == ProductStage.UNKNOWN or not location_id or (not price_exact and not price_low))
        }

    @classmethod
    def _detect_product_stage(cls, text: str, is_chinese: bool) -> ProductStage:
        t = text.lower()
        if is_chinese:
            if any(k in text for k in SLANG_DICTIONARY["chinese"]["DRY_BLACK"]):
                return ProductStage.DRY_BLACK
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["DRY_WHITE"]):
                return ProductStage.DRY_WHITE
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["DRY_RAW"]):
                return ProductStage.DRY_RAW
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["FRESH_FRUIT"]):
                return ProductStage.FRESH_FRUIT
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["FINISHED_PRODUCT"]):
                return ProductStage.FINISHED_PRODUCT
        else:
            if any(k in t for k in SLANG_DICTIONARY["vietnamese"]["DRY_BLACK"]):
                return ProductStage.DRY_BLACK
            elif any(k in t for k in SLANG_DICTIONARY["vietnamese"]["DRY_WHITE"]):
                return ProductStage.DRY_WHITE
            elif any(k in t for k in SLANG_DICTIONARY["vietnamese"]["DRY_RAW"]):
                return ProductStage.DRY_RAW
            elif any(k in t for k in SLANG_DICTIONARY["vietnamese"]["FRESH_FRUIT"]):
                return ProductStage.FRESH_FRUIT
        return ProductStage.UNKNOWN

    @classmethod
    def _detect_transaction_type(cls, text: str, is_chinese: bool) -> Tuple[TransactionType, float]:
        t = text.lower()
        if is_chinese:
            if any(k in text for k in ["成交", "已结", "已装车", "现款点清"]):
                return TransactionType.CONFIRMED_TRANSACTION, 0.95
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["PROCUREMENT"]):
                return TransactionType.BUYER_QUOTE, 0.85
            elif any(k in text for k in SLANG_DICTIONARY["chinese"]["SELLING"]):
                return TransactionType.SELLER_QUOTE, 0.75
            elif any(k in text for k in ["求购", "寻货", "大量要"]):
                return TransactionType.WANTED, 0.70
        else:
            if any(k in t for k in ["đã chốt", "cân xong", "đã chuyển khoản", "tiền tươi xong"]):
                return TransactionType.CONFIRMED_TRANSACTION, 0.95
            elif any(k in t for k in ["thu mua", "lò cần", "thu mua tận vườn", "giá mua hôm nay"]):
                return TransactionType.BUYER_QUOTE, 0.85
            elif any(k in t for k in ["bán", "xuất lò", "sẵn hàng", "báo giá rao", "giao tại lò"]):
                return TransactionType.SELLER_QUOTE, 0.75
            elif any(k in t for k in ["cần mua", "tìm mối", "tìm nguồn"]):
                return TransactionType.WANTED, 0.70
        return TransactionType.REFERENCE, 0.50

    @classmethod
    def _detect_location(cls, text: str, is_chinese: bool, default_country: str) -> Tuple[Optional[str], float]:
        for loc in INITIAL_LOCATIONS:
            if is_chinese and loc.get("name_cn") and loc["name_cn"] in text:
                return loc["id"], 0.9
            if not is_chinese and loc.get("name_vi") and loc["name_vi"].lower() in text.lower():
                return loc["id"], 0.9
        if is_chinese:
            if "海南" in text or "万宁" in text:
                return "CN_HAINAN_WANNING", 0.7
            if "湖南" in text or "湘潭" in text:
                return "CN_HUNAN_XIANGTAN", 0.7
        else:
            if "đắk lắk" in text.lower() or "dak lak" in text.lower():
                return "VN_DAKLAK", 0.85
            if "bến tre" in text.lower() or "ben tre" in text.lower():
                return "VN_BENTRE", 0.85
            if "hải phòng" in text.lower() or "hai phong" in text.lower():
                return "VN_HAIPHONG", 0.85
            if "quảng ngãi" in text.lower() or "quang ngai" in text.lower():
                return "VN_QUANGNGAI", 0.85
        return None, 0.0

    @classmethod
    def _extract_price_and_unit(cls, text: str, is_chinese: bool) -> Tuple[Optional[float], Optional[float], Optional[float], str, str]:
        if is_chinese:
            currency = "CNY"
            unit = "JIN"
            match_range = re.search(r"(\d+(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*(?:元|块)?", text)
            if match_range:
                low = float(match_range.group(1))
                high = float(match_range.group(2))
                return None, low, high, currency, unit
                
            match_single = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|块)?\s*(?:一|/|每)?\s*(斤|公斤|kg)?", text)
            if match_single:
                val = float(match_single.group(1))
                u = match_single.group(2)
                if u and u.lower() in ["公斤", "kg"]:
                    unit = "KG"
                return val, None, None, currency, unit
            return None, None, None, currency, unit
        else:
            currency = "VND"
            unit = "KG"
            # Mask out volume prefixes (vd: "10 tấn", "5 tạ", "2 container") before searching price
            text_masked = re.sub(r"\b\d+\s*(?:tấn|tạ|container|xe|bao)\b", " ", text, flags=re.IGNORECASE)
            
            # Check price range: vd "188 - 192k", "188.000 - 192.000"
            match_range = re.search(r"(\d+(?:[.,]\d+)?)\s*[-~đến]\s*(\d+(?:[.,]\d+)?)\s*(k|nghìn|tr)?", text_masked, re.IGNORECASE)
            if match_range:
                low_raw = float(match_range.group(1).replace(",", "."))
                high_raw = float(match_range.group(2).replace(",", "."))
                suffix = match_range.group(3) or ""
                low = low_raw * 1000 if (low_raw < 1000 or "k" in suffix.lower()) else low_raw
                high = high_raw * 1000 if (high_raw < 1000 or "k" in suffix.lower()) else high_raw
                return None, low, high, currency, unit
                
            # Check single price: vd "giá 190k", "191k/kg", "190.000", "190k"
            match_single = re.search(r"(?:giá\s*)?(\d+(?:[.,]\d+)?)\s*(k|nghìn|đ|vnd)?\s*(?:/|mỗi)?\s*(kg|kí|cân)?", text_masked, re.IGNORECASE)
            if match_single:
                val_raw = float(match_single.group(1).replace(",", "."))
                suffix = match_single.group(2) or ""
                val = val_raw * 1000 if (val_raw < 1000 or "k" in suffix.lower()) else val_raw
                return val, None, None, currency, unit
                
            return None, None, None, currency, unit
