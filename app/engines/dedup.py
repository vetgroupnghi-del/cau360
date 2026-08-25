"""
Deduplication & Clustering Engine (Rules 19, 105)
Identifies reposts, viral chatter copies, and groups them into 1 primary observation cluster.
"""
import hashlib
import re
from typing import Tuple, Optional
from app.core.database import get_db_connection

class DeduplicationEngine:
    STOPWORDS = {"hôm", "nay", "ngày", "ngay", "liên", "hệ", "alo", "inbox", "nhé", "nè", "ơi", "ah", "nha", "chấm", "bác", "bạn", "ạ"}

    @staticmethod
    def compute_document_hash(text: str, author_or_url: str = "") -> str:
        """Computes SHA-256 hash for raw document immutability."""
        content = f"{text.strip()}|{author_or_url.strip()}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def compute_semantic_simhash(cls, text: str, price: Optional[float], location_id: Optional[str]) -> str:
        """
        Creates a cluster hash based on location, normalized price, and core semantic keywords.
        """
        clean_text = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [w for w in clean_text.split() if len(w) > 1 and w not in cls.STOPWORDS]
        # Keep top distinguishing market tokens
        core_tokens = sorted(list(set(tokens)))[:5]
        core_str = "_".join(core_tokens)
        
        cluster_raw = f"{location_id or 'UNKNOWN'}_{price or 0.0}_{core_str}".encode("utf-8")
        return hashlib.md5(cluster_raw).hexdigest()

    @classmethod
    def process_and_cluster(cls, raw_text: str, price: Optional[float], location_id: Optional[str]) -> Tuple[str, bool]:
        """
        Returns (cluster_id, is_duplicate).
        If cluster already exists in DB within past 24 hours, is_duplicate = True.
        """
        cluster_id = cls.compute_semantic_simhash(raw_text, price, location_id)
        
        with get_db_connection() as conn:
            existing = conn.execute("""
                SELECT id FROM market_observations
                WHERE duplicate_cluster_id = ? AND datetime(created_at) >= datetime('now', '-24 hours')
                LIMIT 1
            """, (cluster_id,)).fetchone()
            
            is_dup = existing is not None
            return cluster_id, is_dup
