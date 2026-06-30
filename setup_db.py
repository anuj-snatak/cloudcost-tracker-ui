"""
Run this script ONCE to create all required Supabase tables.
Usage: python3 setup_db.py
"""
import requests

import os
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SQL = """
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_name TEXT,
    mode TEXT,
    label1 TEXT,
    label2 TEXT,
    total1 FLOAT,
    total2 FLOAT,
    delta FLOAT,
    forecast FLOAT,
    benchmark FLOAT,
    current_month FLOAT,
    last_month FLOAT,
    anomaly_count INTEGER DEFAULT 0,
    report_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    action TEXT,
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_views (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alert_name TEXT NOT NULL,
    threshold FLOAT NOT NULL,
    slack_webhook TEXT,
    alert_email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
    headers=headers,
    json={"query": SQL},
)

if resp.status_code in (200, 201):
    print("✅ Tables created successfully!")
else:
    print("⚠️  Auto-create failed. Please run the following SQL in your Supabase SQL Editor:")
    print("   Go to: https://supabase.com/dashboard/project/gazjsdakepnwpqjcckdd/sql/new")
    print()
    print(SQL)
