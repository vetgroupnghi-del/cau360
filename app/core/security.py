"""
SECURITY & SUBSCRIPTION MANAGEMENT MODULE V4.5
Quản lý bảo mật đăng nhập, cấp gói cước thời hạn (1T, 3T, 6T, tùy chỉnh),
tìm kiếm hội viên, reset mật khẩu, xóa thành viên và bảo vệ quyền riêng tư.
"""
import hashlib
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.core.database import get_db_connection

SALT = "CAU360_SECURITY_SALT_2026"

def hash_password(password: str) -> str:
    """Mã hóa mật khẩu bằng SHA-256 kèm chuỗi Salt bảo mật."""
    raw = f"{password.strip()}|{SALT}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu."""
    return hash_password(plain_password) == hashed_password

class AuthManager:
    @staticmethod
    def init_auth_table():
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    phone TEXT,
                    role TEXT DEFAULT 'MEMBER',
                    plan_type TEXT DEFAULT '1_MONTH',
                    plan_price_vnd REAL DEFAULT 0,
                    subscribed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            user_cols = [c[1] for c in conn.execute("PRAGMA table_info(users)").fetchall()]
            if "phone" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN phone TEXT;")
            if "plan_type" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN plan_type TEXT DEFAULT '1_MONTH';")
            if "plan_price_vnd" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN plan_price_vnd REAL DEFAULT 0;")
            if "subscribed_at" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN subscribed_at TIMESTAMP;")
            if "expires_at" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN expires_at TIMESTAMP;")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscription_transactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    plan_type TEXT,
                    days_added INTEGER,
                    amount_paid_vnd REAL,
                    old_expires_at TIMESTAMP,
                    new_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            now = (datetime.utcnow() + timedelta(hours=7))
            # Admin vĩnh viễn (LIFETIME)
            admin_user = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
            if not admin_user:
                admin_id = f"USR_{uuid.uuid4().hex[:8]}"
                admin_pass_hash = hash_password("cau360@2026")
                forever = (now + timedelta(days=3650)).isoformat()
                conn.execute("""
                    INSERT INTO users (id, username, password_hash, display_name, phone, role, plan_type, plan_price_vnd, subscribed_at, expires_at)
                    VALUES (?, 'admin', ?, 'Chủ Lò (Tổng Quản Trị)', '0901234567', 'ADMIN', 'LIFETIME', 0, ?, ?)
                """, (admin_id, admin_pass_hash, now.isoformat(), forever))
            else:
                forever = (now + timedelta(days=3650)).isoformat()
                conn.execute("UPDATE users SET role = 'ADMIN', plan_type = 'LIFETIME', expires_at = ? WHERE username = 'admin'", (forever,))
                
            worker_user = conn.execute("SELECT id FROM users WHERE username = 'thocan'").fetchone()
            if not worker_user:
                worker_id = f"USR_{uuid.uuid4().hex[:8]}"
                worker_pass_hash = hash_password("123456")
                exp_6m = (now + timedelta(days=180)).isoformat()
                conn.execute("""
                    INSERT INTO users (id, username, password_hash, display_name, phone, role, plan_type, plan_price_vnd, subscribed_at, expires_at)
                    VALUES (?, 'thocan', ?, 'Thợ Cân Lò Sấy', '0988112233', 'MANAGER', '6_MONTHS', 1500000, ?, ?)
                """, (worker_id, worker_pass_hash, now.isoformat(), exp_6m))

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
        cls.init_auth_table()
        now = (datetime.utcnow() + timedelta(hours=7))
        with get_db_connection() as conn:
            user = conn.execute("""
                SELECT id, username, password_hash, display_name, phone, role, plan_type, plan_price_vnd, expires_at, is_active
                FROM users WHERE username = ?
            """, (username.strip().lower(),)).fetchone()
            
            if not user:
                return None
                
            if not verify_password(password, user["password_hash"]):
                return None
                
            if user["is_active"] != 1:
                return {"error": "ACCOUNT_LOCKED", "message": "Tài khoản của bạn đã bị khóa! Vui lòng liên hệ Admin."}
                
            expires_at = datetime.fromisoformat(user["expires_at"]) if user["expires_at"] else (now + timedelta(days=30))
            days_remaining = (expires_at - now).total_seconds() / 86400.0
            
            is_expired = (days_remaining < 0) and (user["role"] != "ADMIN")
            is_expiring_soon = (0 <= days_remaining <= 3.0) and (user["role"] != "ADMIN")
            
            token = f"TOKEN_{secrets.token_hex(16)}"
            return {
                "id": user["id"],
                "username": user["username"],
                "display_name": user["display_name"],
                "phone": user["phone"] or "",
                "role": user["role"],
                "plan_type": user["plan_type"],
                "expires_at_formatted": expires_at.strftime("%d/%m/%Y"),
                "days_remaining": round(days_remaining, 1),
                "is_expiring_soon": is_expiring_soon,
                "is_expired": is_expired,
                "token": token
            }

    @classmethod
    def create_user_with_plan(
        cls,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        phone: str = "",
        role: str = "SUBSCRIBER",
        plan_type: str = "1_MONTH",
        custom_days: int = 30,
        price_vnd: float = 0.0
    ) -> Dict[str, Any]:
        cls.init_auth_table()
        now = (datetime.utcnow() + timedelta(hours=7))
        
        # Tự động gán display_name nếu để trống
        final_display_name = display_name.strip() if (display_name and display_name.strip()) else f"Hội Viên ({username.strip()})"
        
        if plan_type == "1_MONTH":
            days = 30
        elif plan_type == "3_MONTHS":
            days = 90
        elif plan_type == "6_MONTHS":
            days = 180
        elif plan_type == "12_MONTHS":
            days = 365
        elif plan_type == "LIFETIME":
            days = 3650
        else:
            days = max(1, custom_days)
            
        expires_at = now + timedelta(days=days)
        user_id = f"USR_{uuid.uuid4().hex[:8]}"
        p_hash = hash_password(password)
        
        with get_db_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO users (id, username, password_hash, display_name, phone, role, plan_type, plan_price_vnd, subscribed_at, expires_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (user_id, username.strip().lower(), p_hash, final_display_name, phone.strip(), role.upper(), plan_type, price_vnd, now.isoformat(), expires_at.isoformat()))
                
                tx_id = f"TX_{uuid.uuid4().hex[:8]}"
                conn.execute("""
                    INSERT INTO subscription_transactions (id, user_id, plan_type, days_added, amount_paid_vnd, old_expires_at, new_expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tx_id, user_id, plan_type, days, price_vnd, now.isoformat(), expires_at.isoformat()))
                
                return {
                    "success": True,
                    "message": f"Tạo tài khoản '{username}' thành công! Gói {days} ngày (Hết hạn: {expires_at.strftime('%d/%m/%Y')})."
                }
            except Exception:
                return {"success": False, "message": f"Tên đăng nhập '{username}' đã tồn tại!"}

    @classmethod
    def delete_user(cls, user_id: str) -> Dict[str, Any]:
        """Xóa vĩnh viễn tài khoản hội viên khỏi hệ thống (trừ tài khoản Admin)."""
        cls.init_auth_table()
        with get_db_connection() as conn:
            user = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "message": "Không tìm thấy người dùng!"}
            if user["role"] == "ADMIN":
                return {"success": False, "message": "Không thể xóa tài khoản Tổng Quản Trị (Admin)!"}
                
            conn.execute("DELETE FROM subscription_transactions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return {"success": True, "message": f"Đã xóa vĩnh viễn tài khoản '{user['username']}' thành công!"}

    @classmethod
    def renew_subscription(cls, user_id: str, plan_type: str, custom_days: int = 30, amount_paid_vnd: float = 0.0) -> Dict[str, Any]:
        cls.init_auth_table()
        now = (datetime.utcnow() + timedelta(hours=7))
        
        if plan_type == "1_MONTH":
            days = 30
        elif plan_type == "3_MONTHS":
            days = 90
        elif plan_type == "6_MONTHS":
            days = 180
        elif plan_type == "12_MONTHS":
            days = 365
        else:
            days = max(1, custom_days)
            
        with get_db_connection() as conn:
            user = conn.execute("SELECT id, username, expires_at FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "message": "Không tìm thấy người dùng!"}
                
            current_exp = datetime.fromisoformat(user["expires_at"]) if user["expires_at"] else now
            base_time = max(now, current_exp)
            new_exp = base_time + timedelta(days=days)
            
            conn.execute("""
                UPDATE users SET expires_at = ?, plan_type = ?, plan_price_vnd = plan_price_vnd + ?, is_active = 1
                WHERE id = ?
            """, (new_exp.isoformat(), plan_type, amount_paid_vnd, user_id))
            
            tx_id = f"TX_{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT INTO subscription_transactions (id, user_id, plan_type, days_added, amount_paid_vnd, old_expires_at, new_expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, user_id, plan_type, days, amount_paid_vnd, current_exp.isoformat(), new_exp.isoformat()))
            
            return {
                "success": True,
                "message": f"Gia hạn thành công cho '{user['username']}' thêm {days} ngày! Hạn mới: {new_exp.strftime('%d/%m/%Y')}."
            }

    @classmethod
    def reset_password(cls, user_id: str, new_password: str) -> Dict[str, Any]:
        cls.init_auth_table()
        if not new_password.strip():
            return {"success": False, "message": "Mật khẩu mới không được để trống!"}
            
        p_hash = hash_password(new_password)
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (p_hash, user_id))
            return {"success": True, "message": "Đặt lại mật khẩu thành công!"}

    @classmethod
    def toggle_user_status(cls, user_id: str) -> Dict[str, Any]:
        cls.init_auth_table()
        with get_db_connection() as conn:
            user = conn.execute("SELECT is_active, role FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "message": "Không tìm thấy người dùng!"}
            if user["role"] == "ADMIN":
                return {"success": False, "message": "Không thể khóa tài khoản Tổng Quản Trị (Admin)!"}
                
            new_status = 0 if user["is_active"] == 1 else 1
            conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
            return {"success": True, "new_status": new_status, "message": "Đã khóa tài khoản!" if new_status == 0 else "Đã mở khóa tài khoản!"}

    @classmethod
    def get_subscription_dashboard(cls) -> Dict[str, Any]:
        cls.init_auth_table()
        now = (datetime.utcnow() + timedelta(hours=7))
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, display_name, phone, role, plan_type, plan_price_vnd, subscribed_at, expires_at, is_active, created_at
                FROM users ORDER BY created_at DESC
            """).fetchall()
            
            users_list = []
            expiring_soon_count = 0
            expired_count = 0
            active_count = 0
            total_revenue_vnd = 0.0
            
            for r in rows:
                item = dict(r)
                total_revenue_vnd += (r["plan_price_vnd"] or 0)
                
                exp_dt = datetime.fromisoformat(r["expires_at"]) if r["expires_at"] else (now + timedelta(days=30))
                days_left = (exp_dt - now).total_seconds() / 86400.0
                item["days_left"] = round(days_left, 1)
                item["expires_at_formatted"] = exp_dt.strftime("%d/%m/%Y")
                
                if r["role"] == "ADMIN":
                    item["status_label"] = "VĨNH VIỄN (ADMIN)"
                    item["status_color"] = "green"
                    active_count += 1
                elif r["is_active"] == 0:
                    item["status_label"] = "ĐÃ KHÓA"
                    item["status_color"] = "gray"
                elif days_left < 0:
                    item["status_label"] = "ĐÃ HẾT HẠN"
                    item["status_color"] = "red"
                    expired_count += 1
                elif days_left <= 3.0:
                    item["status_label"] = f"SẮP HẾT HẠN ({round(days_left, 1)} NGÀY)"
                    item["status_color"] = "yellow"
                    expiring_soon_count += 1
                    active_count += 1
                else:
                    item["status_label"] = f"CÒN {int(days_left)} NGÀY"
                    item["status_color"] = "green"
                    active_count += 1
                    
                users_list.append(item)
                
            return {
                "total_users": len(users_list),
                "active_users": active_count,
                "expiring_soon_count": expiring_soon_count,
                "expired_count": expired_count,
                "total_revenue_vnd": total_revenue_vnd,
                "users": users_list
            }
