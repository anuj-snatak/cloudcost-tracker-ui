import bcrypt
import streamlit as st
from supabase import create_client
from datetime import datetime
import json
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))


def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def log_activity(user_id: int, username: str, action: str, details: str = ""):
    try:
        get_client().table("audit_logs").insert({
            "user_id": user_id,
            "username": username,
            "action": action,
            "details": details,
        }).execute()
    except Exception:
        pass


def get_audit_logs(limit: int = 100) -> list:
    try:
        result = get_client().table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception:
        return []


def get_saved_views(user_id: int) -> list:
    try:
        result = get_client().table("saved_views").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data
    except Exception:
        return []


def save_view(user_id: int, name: str, config_dict: dict) -> tuple[bool, str]:
    try:
        get_client().table("saved_views").insert({
            "user_id": user_id,
            "name": name,
            "config": config_dict,
        }).execute()
        return True, "View saved"
    except Exception as e:
        return False, str(e)


def delete_view(view_id: int) -> bool:
    try:
        get_client().table("saved_views").delete().eq("id", view_id).execute()
        return True
    except Exception:
        return False


def get_budget_alerts(user_id: int) -> list:
    try:
        result = get_client().table("budget_alerts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data
    except Exception:
        return []


def save_budget_alert(user_id: int, alert_name: str, threshold: float, slack_webhook: str = "", alert_email: str = "") -> tuple[bool, str]:
    try:
        get_client().table("budget_alerts").insert({
            "user_id": user_id,
            "alert_name": alert_name,
            "threshold": threshold,
            "slack_webhook": slack_webhook or None,
            "alert_email": alert_email or None,
        }).execute()
        return True, "Alert created"
    except Exception as e:
        return False, str(e)


def toggle_alert(alert_id: int, is_active: bool) -> bool:
    try:
        get_client().table("budget_alerts").update({"is_active": is_active}).eq("id", alert_id).execute()
        return True
    except Exception:
        return False


def delete_alert(alert_id: int) -> bool:
    try:
        get_client().table("budget_alerts").delete().eq("id", alert_id).execute()
        return True
    except Exception:
        return False


def save_report_to_history(user_id: int, report: dict) -> bool:
    try:
        safe_report = {k: v for k, v in report.items() if k not in ("client",)}
        get_client().table("reports").insert({
            "user_id": user_id,
            "account_name": report.get("account_name", ""),
            "mode": report.get("mode", ""),
            "label1": report.get("label1", ""),
            "label2": report.get("label2", ""),
            "total1": report.get("total1", 0),
            "total2": report.get("total2", 0),
            "delta": report.get("delta", 0),
            "forecast": report.get("forecast", 0),
            "benchmark": report.get("benchmark", 0),
            "current_month": report.get("current_month", 0),
            "last_month": report.get("last_month", 0),
            "anomaly_count": len(report.get("anomalies", [])),
            "report_data": json.dumps(safe_report, default=str),
        }).execute()
        return True
    except Exception:
        return False


def get_report_history(user_id: int, limit: int = 20) -> list:
    try:
        result = get_client().table("reports").select(
            "id,account_name,mode,label1,label2,total1,total2,delta,forecast,benchmark,current_month,last_month,anomaly_count,created_at"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception:
        return []


def login(username: str, password: str):
    try:
        client = get_client()
        result = client.table("users").select("*").eq("username", username).eq("is_active", True).execute()
        if not result.data:
            return None, "Invalid username or password"
        user = result.data[0]
        if not verify_password(password, user["password_hash"]):
            return None, "Invalid username or password"
        client.table("users").update({"last_login": datetime.now().isoformat()}).eq("id", user["id"]).execute()
        log_activity(user["id"], username, "login")
        return user, None
    except Exception as e:
        return None, f"Login error: {str(e)}"


def create_user(username: str, email: str, password: str, full_name: str, role: str = "user"):
    try:
        client = get_client()
        existing = client.table("users").select("id").eq("username", username).execute()
        if existing.data:
            return False, "Username already exists"
        existing_email = client.table("users").select("id").eq("email", email).execute()
        if existing_email.data:
            return False, "Email already exists"
        client.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "full_name": full_name,
            "role": role,
            "is_active": True,
        }).execute()
        current = st.session_state.get("current_user")
        if current:
            log_activity(current["id"], current["username"], "create_user", f"Created user: {username}")
        return True, "User created successfully"
    except Exception as e:
        return False, str(e)


def get_all_users():
    try:
        client = get_client()
        result = client.table("users").select("id,username,email,full_name,role,is_active,created_at,last_login").execute()
        return result.data
    except Exception:
        return []


def toggle_user_status(user_id: int, is_active: bool):
    try:
        client = get_client()
        client.table("users").update({"is_active": is_active}).eq("id", user_id).execute()
        return True
    except Exception:
        return False


def delete_user(user_id: int):
    try:
        client = get_client()
        user_data = client.table("users").select("username").eq("id", user_id).execute()
        deleted_username = user_data.data[0]["username"] if user_data.data else str(user_id)
        client.table("users").delete().eq("id", user_id).execute()
        current = st.session_state.get("current_user")
        if current:
            log_activity(current["id"], current["username"], "delete_user", f"Deleted user: {deleted_username}")
        return True
    except Exception:
        return False


def change_password(user_id: int, new_password: str):
    try:
        client = get_client()
        client.table("users").update({"password_hash": hash_password(new_password)}).eq("id", user_id).execute()
        current = st.session_state.get("current_user")
        if current:
            log_activity(current["id"], current["username"], "change_password", f"Changed password for user_id: {user_id}")
        return True
    except Exception:
        return False


def is_logged_in():
    return st.session_state.get("logged_in", False)


def get_current_user():
    return st.session_state.get("current_user", None)


def logout():
    current = st.session_state.get("current_user")
    if current:
        log_activity(current["id"], current["username"], "logout")
    for key in ["logged_in", "current_user"]:
        if key in st.session_state:
            del st.session_state[key]
