import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import calendar
from auth import (
    is_logged_in, get_current_user, logout, create_user, get_all_users,
    toggle_user_status, delete_user, change_password,
    log_activity, get_audit_logs,
    get_saved_views, save_view, delete_view,
    get_budget_alerts, save_budget_alert, toggle_alert, delete_alert,
    save_report_to_history, get_report_history,
)
from login import show_login_page
from aws_utils import (
    get_ce_client, get_ses_client, assume_role,
    fetch_daily_cost, fetch_period_cost,
    get_forecast, get_last_month_total, get_current_month_spend,
    get_anomalies, get_date_ranges, fetch_daily_trend, fetch_service_daily_trend,
    fetch_cost_by_region, fetch_cost_by_account, fetch_cost_by_usage_type,
    fetch_custom_range_cost, get_savings_plans_utilization, get_reservation_utilization,
    fetch_service_detail, fetch_multi_service_trend,
    fetch_available_tag_keys, fetch_cost_by_tag, fetch_cost_by_tag_and_service,
    fetch_s3_bucket_cost, fetch_ec2_instance_type_cost,
)
from charts import top_services, short_name
from notifications import check_and_trigger_alerts, send_slack_alert
from recommendations import get_rightsizing_recommendations, detect_idle_services, compute_savings_opportunity, get_static_tips
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

st.set_page_config(page_title="CloudCost Tracker", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

if not is_logged_in():
    show_login_page()
    st.stop()

current_user = get_current_user()
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

# ── COLORS ──
PRIMARY       = "#1e3a5f"
PRIMARY_LIGHT = "#2a5280"
SUCCESS       = "#1a7a5c"
DANGER        = "#b91c1c"
WARNING       = "#b45309"
INFO          = "#1e40af"
GOLD          = "#c9a84c"
NAVY          = "#0c1f3f"
CREAM         = "#faf8f4"

plotly_tpl   = "plotly_white"
plotly_paper = "rgba(0,0,0,0)"
plotly_plot  = "rgba(0,0,0,0)"

# ── GLOBAL CSS ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* {{ font-family: 'Inter', sans-serif !important; box-sizing: border-box; }}

.stApp {{ background: #f0f2f6 !important; }}
section[data-testid="stSidebar"] > div {{ background: #ffffff; border-right: 1px solid #e2e6ea; padding-top: 0; }}

/* ── HEADER ── */
.app-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 24px; background: #ffffff;
    border-bottom: 1px solid #e2e6ea;
    margin: -1rem -1rem 1.5rem -1rem;
}}
.app-title {{ font-size: 1.25em; font-weight: 700; color: {NAVY}; display: flex; align-items: center; gap: 8px; }}
.app-sub   {{ font-size: 0.75em; color: #6c757d; margin-top: 2px; }}

/* ── KPI CARDS ── */
.kpi-grid {{ display: grid; grid-template-columns: repeat(6,1fr); gap: 12px; margin-bottom: 20px; }}
.kpi-card {{
    background: #fff; border-radius: 8px; padding: 16px 18px;
    border: 1px solid #e2e6ea; border-top: 3px solid {PRIMARY};
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}}
.kpi-card.green  {{ border-top-color: {SUCCESS}; }}
.kpi-card.red    {{ border-top-color: {DANGER}; }}
.kpi-card.amber  {{ border-top-color: {WARNING}; }}
.kpi-card.blue   {{ border-top-color: {INFO}; }}
.kpi-card.teal   {{ border-top-color: #0891b2; }}
.kpi-label {{ font-size: 0.68em; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }}
.kpi-value {{ font-size: 1.5em; font-weight: 700; color: {NAVY}; line-height: 1; }}
.kpi-sub   {{ font-size: 0.72em; color: #8896a7; margin-top: 5px; }}
.kpi-badge-up   {{ display:inline-block; background:#fef2f2; color:{DANGER}; padding:2px 8px; border-radius:12px; font-size:0.72em; font-weight:700; margin-top:4px; }}
.kpi-badge-down {{ display:inline-block; background:#f0fdf4; color:{SUCCESS}; padding:2px 8px; border-radius:12px; font-size:0.72em; font-weight:700; margin-top:4px; }}
.kpi-badge-neu  {{ display:inline-block; background:#f8fafc; color:#5a6577; padding:2px 8px; border-radius:12px; font-size:0.72em; font-weight:700; margin-top:4px; }}

/* ── SECTION HEADER ── */
.sec-hdr {{
    font-size: 0.8em; font-weight: 700; color: #6c757d;
    text-transform: uppercase; letter-spacing: 1px;
    border-bottom: 1px solid #e2e6ea; padding-bottom: 8px; margin-bottom: 16px;
}}

/* ── BUDGET BAR ── */
.bbar-wrap {{ background:#e9ecef; border-radius:6px; height:22px; overflow:hidden; margin:6px 0; }}
.bbar-fill  {{ height:100%; border-radius:6px; display:flex; align-items:center; justify-content:center;
               font-size:0.75em; font-weight:700; color:#fff; }}

/* ── ALERT CARD ── */
.alert-item {{
    background:#fff; border:1px solid #e2e6ea; border-radius:8px;
    padding:14px 16px; margin:8px 0; display:flex; align-items:flex-start; gap:12px;
}}
.alert-icon {{ font-size:1.3em; flex-shrink:0; }}
.alert-body {{ flex:1; }}
.alert-title {{ font-weight:600; color:{NAVY}; font-size:0.9em; }}
.alert-detail {{ font-size:0.8em; color:#6c757d; margin-top:3px; }}

/* ── SIDEBAR NAV ── */
.sidebar-user {{
    background: linear-gradient(135deg,{PRIMARY},{PRIMARY_LIGHT});
    border-radius:8px; padding:14px 16px; margin-bottom:16px; color:white;
}}
.sidebar-label {{ font-size:0.68em; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:{GOLD}; }}
.sidebar-name  {{ font-size:0.95em; font-weight:700; margin-top:4px; }}
.sidebar-role  {{ font-size:0.72em; color:rgba(255,255,255,0.55); margin-top:2px; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ gap:2px; border-bottom: 2px solid #e2e6ea !important; background:transparent; padding:0; }}
.stTabs [data-baseweb="tab"] {{
    background:transparent; border-radius:6px 6px 0 0; padding:10px 18px;
    font-weight:600; font-size:0.85em; color:#6c757d; border:none;
}}
.stTabs [data-baseweb="tab"]:hover {{ color:{PRIMARY}; background:rgba(30,58,95,0.04); }}
.stTabs [aria-selected="true"] {{
    background:#fff !important; color:{PRIMARY} !important;
    border-top:2px solid {PRIMARY} !important; border-left:1px solid #e2e6ea !important;
    border-right:1px solid #e2e6ea !important; border-radius:6px 6px 0 0 !important;
    box-shadow: none !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: #e2e6ea !important; border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}}
</style>
""", unsafe_allow_html=True)

if st.session_state["dark_mode"]:
    st.markdown("""
    <style>
    .stApp, section[data-testid="stSidebar"] > div { background:#0d1117 !important; color:#c9d1d9 !important; border-color:#30363d !important; }
    .app-header, .kpi-card { background:#161b22 !important; border-color:#30363d !important; }
    .kpi-value, .app-title { color:#e6edf3 !important; }
    .kpi-label, .kpi-sub, .sec-hdr { color:#8b949e !important; }
    .stTabs [data-baseweb="tab-list"] { border-color:#30363d !important; }
    .stTabs [aria-selected="true"] { background:#161b22 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:#161b22 !important; border-color:#30363d !important; }
    .bbar-wrap { background:#21262d !important; }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{PRIMARY},{PRIMARY_LIGHT});border-radius:8px;'
        f'padding:14px 16px;margin-bottom:12px;color:white;">'
        f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:{GOLD};">Signed in as</div>'
        f'<div style="font-size:0.95em;font-weight:700;margin-top:4px;">{current_user["full_name"]}</div>'
        f'<div style="font-size:11px;color:rgba(255,255,255,0.6);margin-top:2px;">'
        f'{current_user["role"].upper()} · {current_user["email"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_lo, col_dk = st.columns(2)
    with col_lo:
        if st.button("Sign out", use_container_width=True):
            logout(); st.rerun()
    with col_dk:
        dk = st.toggle("Dark", value=st.session_state["dark_mode"])
        if dk != st.session_state["dark_mode"]:
            st.session_state["dark_mode"] = dk; st.rerun()

    st.divider()
    st.markdown("**AWS Connection**")
    access_key = st.text_input("Access Key ID", type="password", placeholder="AKIA...")
    secret_key = st.text_input("Secret Access Key", type="password", placeholder="Secret key")
    region = st.selectbox("Region", [
        "ap-south-1","us-east-1","us-west-2","eu-west-1","eu-central-1",
        "ap-southeast-1","ap-southeast-2","ap-northeast-1","sa-east-1",
    ])
    use_assume_role = st.checkbox("Use Assume Role")
    role_arn = st.text_input("Role ARN") if use_assume_role else ""

    st.divider()
    st.markdown("**Report Settings**")
    account_name = st.text_input("Account Label", value="My AWS Account")
    mode = st.segmented_control("Period", ["Daily", "Weekly", "Monthly"], default="Monthly")
    ref_date = st.date_input("Reference Date", value=date.today() - timedelta(days=1))
    benchmark = st.number_input("Monthly Budget ($)", value=10000, step=500, min_value=0)
    trend_days = st.select_slider("Trend Days", [7, 14, 30], value=14)

    st.divider()
    st.markdown("**Notifications**")
    sender    = st.text_input("SES Sender Email", placeholder="noreply@company.com")
    recipients = st.text_input("Recipients", placeholder="a@co.com, b@co.com")
    slack_webhook = st.text_input("Slack Webhook", placeholder="https://hooks.slack.com/...", type="password")

    st.divider()
    generate_btn = st.button("▶  Run Report", type="primary", use_container_width=True)


# ══════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 0 4px;">'
        '<span style="font-size:1.5em;">💰</span>'
        '<div>'
        '<div style="font-size:1.15em;font-weight:800;color:#0c1f3f;">CloudCost Tracker</div>'
        '<div style="font-size:0.75em;color:#6c757d;">AWS Cost Explorer · Anomaly Detection · Forecasting</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f'<div style="text-align:right;font-size:0.8em;color:#6c757d;padding-top:14px;">'
        f'Account: <strong style="color:#0c1f3f;">{account_name}</strong><br>'
        f'Region: <strong style="color:#0c1f3f;">{region}</strong></div>',
        unsafe_allow_html=True,
    )
st.markdown('<hr style="margin:8px 0 16px;border:none;border-top:1px solid #e2e6ea;">', unsafe_allow_html=True)


# ══════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════
def render_kpi(col, label, value, sub, border_color, badge=None):
    if badge is not None and badge != 0:
        bc  = DANGER if badge > 0 else SUCCESS
        bgc = "#fef2f2" if badge > 0 else "#f0fdf4"
        arr = "▲" if badge > 0 else "▼"
        badge_html = (f'<div style="display:inline-block;background:{bgc};color:{bc};'
                      f'padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;margin-top:4px;">'
                      f'{arr} {abs(badge):.1f}%</div>')
    else:
        badge_html = ""
    with col:
        st.markdown(
            f'<div style="background:#fff;border-radius:8px;padding:16px 18px;border:1px solid #e2e6ea;'
            f'border-top:3px solid {border_color};box-shadow:0 1px 4px rgba(0,0,0,0.04);">'
            f'<div style="font-size:11px;font-weight:600;color:#6c757d;text-transform:uppercase;'
            f'letter-spacing:0.8px;margin-bottom:6px;">{label}</div>'
            f'<div style="font-size:1.45em;font-weight:700;color:#0c1f3f;line-height:1;">{value}</div>'
            f'<div style="font-size:11px;color:#8896a7;margin-top:5px;">{sub}</div>'
            f'{badge_html}</div>',
            unsafe_allow_html=True,
        )

def render_budget_bar(current, budget):
    pct   = min((current / budget) * 100, 100) if budget > 0 else 0
    color = SUCCESS if pct < 70 else WARNING if pct < 90 else DANGER
    left  = abs(budget - current)
    label = "left" if current < budget else "over"
    st.markdown(
        f'<div style="font-size:11px;font-weight:600;color:#6c757d;margin-bottom:4px;">'
        f'BUDGET UTILIZATION &nbsp; ${current:,.0f} of ${budget:,.0f}</div>'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="flex:1;background:#e9ecef;border-radius:6px;height:20px;overflow:hidden;">'
        f'<div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:6px;'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:11px;font-weight:700;color:#fff;">{pct:.1f}%</div></div>'
        f'<span style="font-size:12px;font-weight:600;color:{color};min-width:80px;">'
        f'${left:,.0f} {label}</span></div>',
        unsafe_allow_html=True,
    )

def build_email_html(r):
    dc = DANGER if r["delta"] > 0 else SUCCESS
    trend = "increase" if r["delta"] > 0 else "decrease" if r["delta"] < 0 else "no change"
    fc_status = "Exceeding" if r["forecast"] > r["benchmark"] else "Below"
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    body{{font-family:Inter,sans-serif;background:#f0f2f6;color:{NAVY};padding:24px;}}
    .box{{background:#fff;border-radius:8px;padding:20px;margin:12px 0;border-left:4px solid {GOLD};}}
    h2{{color:{NAVY};border-bottom:2px solid {GOLD};padding-bottom:8px;}}
    table{{border-collapse:collapse;width:100%;margin:12px 0;}}
    th{{background:{PRIMARY};color:#fff;padding:9px;text-align:left;font-size:0.85em;}}
    td{{padding:8px;border-bottom:1px solid #e2e6ea;font-size:0.85em;}}
    </style></head><body>
    <h2>💰 {r['account_name']} — {r['mode']} Cost Report</h2>
    <div class="box">
    <p><b>Period 1:</b> {r['label1']} → ${r['total1']:,.2f}</p>
    <p><b>Period 2:</b> {r['label2']} → ${r['total2']:,.2f}</p>
    <p><b>Change:</b> <span style="color:{dc};font-weight:700;">{abs(r['delta']):.2f}% {trend}</span></p>
    <p><b>Forecast:</b> ${r['forecast']:,.2f} — {fc_status} budget (${r['benchmark']:,.0f})</p>
    <p><b>Current Month:</b> ${r.get('current_month',0):,.2f}</p>
    </div>"""
    all_svcs = sorted(set(r["services1"])|set(r["services2"]), key=lambda s: r["services2"].get(s,0), reverse=True)
    html += "<table><tr><th>Service</th><th>Period 1</th><th>Period 2</th><th>Change</th></tr>"
    for svc in all_svcs:
        v1,v2 = r["services1"].get(svc,0), r["services2"].get(svc,0)
        if abs(v1)<0.01 and abs(v2)<0.01: continue
        d = f"{((v2-v1)/v1)*100:.1f}%" if v1>0 else ("New" if v2>0 else "0%")
        c = DANGER if v2>v1 else SUCCESS
        html += f"<tr><td>{short_name(svc)}</td><td>${v1:.2f}</td><td>${v2:.2f}</td><td style='color:{c};font-weight:600;'>{d}</td></tr>"
    html += "</table><p style='font-size:11px;color:#8896a7;'>* AWS cost data may update up to 72h.</p></body></html>"
    return html


# ══════════════════════════════════════════
#  DATA FETCH
# ══════════════════════════════════════════
if generate_btn:
    if not access_key or not secret_key:
        st.error("Enter AWS credentials in the sidebar.")
        st.stop()

    bar = st.progress(0, "Connecting to AWS...")
    try:
        client = assume_role(access_key, secret_key, role_arn, region) if (use_assume_role and role_arn) \
                 else get_ce_client(access_key, secret_key, region)
        bar.progress(10, "Fetching cost data...")

        date1, date2, period_start, period_end = get_date_ranges(mode, ref_date)
        if mode == "Daily":
            total1, services1 = fetch_daily_cost(client, date1)
            total2, services2 = fetch_daily_cost(client, date2)
            label1, label2 = date1, date2
        else:
            total1, services1 = fetch_period_cost(client, date1, date2)
            total2, services2 = fetch_period_cost(client, period_start, period_end)
            display_prev_end = (datetime.strptime(date2, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            display_curr_end = (datetime.strptime(period_end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            label1 = f"{date1} → {display_prev_end}"
            label2 = f"{period_start} → {display_curr_end}"
        bar.progress(25, "Fetching forecast...")

        forecast     = get_forecast(client)
        last_month   = get_last_month_total(client)
        current_month = get_current_month_spend(client)
        bar.progress(40, "Checking anomalies...")

        anomalies    = get_anomalies(client, date1, date2)
        bar.progress(55, "Loading trends...")

        trend_data    = fetch_daily_trend(client, trend_days)
        svc_trend_data = fetch_service_daily_trend(client, trend_days)
        bar.progress(68, "Loading breakdowns...")

        eff_start = period_start if mode != "Daily" else date2
        eff_end   = period_end   if mode != "Daily" else str((datetime.strptime(date2,"%Y-%m-%d")+timedelta(days=1)).date())
        region_costs     = fetch_cost_by_region(client, eff_start, eff_end)
        account_costs    = fetch_cost_by_account(client, eff_start, eff_end)
        usage_type_costs = fetch_cost_by_usage_type(client, eff_start, eff_end)
        bar.progress(80, "Loading savings data...")

        savings_plans = get_savings_plans_utilization(client)
        reservations  = get_reservation_utilization(client)
        bar.progress(90, "Finalising...")

        delta = 0.0 if total1 == 0 else ((total2 - total1) / total1) * 100

        # Day-over-day spikes
        spikes = []
        if trend_data and len(trend_data) > 1:
            for i in range(1, len(trend_data)):
                pc, cc = trend_data[i-1]["cost"], trend_data[i]["cost"]
                if pc > 0:
                    chg = ((cc - pc) / pc) * 100
                    if abs(chg) > 10:
                        spikes.append({"date": trend_data[i]["date"], "prev_date": trend_data[i-1]["date"],
                                       "cost": cc, "prev_cost": pc, "change_pct": round(chg,2),
                                       "change_amt": round(cc - pc, 2)})
            spikes.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

        today = date.today()
        days_elapsed = (today - today.replace(day=1)).days or 1
        _, days_in_month = calendar.monthrange(today.year, today.month)
        daily_rate      = current_month / days_elapsed
        projected_month = round(daily_rate * days_in_month, 2)

        report = {
            "total1": total1, "total2": total2, "delta": delta,
            "services1": services1, "services2": services2,
            "forecast": forecast, "last_month": last_month, "current_month": current_month,
            "benchmark": benchmark, "anomalies": anomalies,
            "label1": label1, "label2": label2, "mode": mode, "account_name": account_name,
            "trend": trend_data, "svc_trend": svc_trend_data, "trend_days": trend_days,
            "region_costs": region_costs, "account_costs": account_costs,
            "usage_type_costs": usage_type_costs,
            "savings_plans": savings_plans, "reservations": reservations,
            "spikes": spikes, "projected_month": projected_month, "daily_rate": daily_rate,
            "date1": date1, "date2": date2,
        }
        st.session_state["report"] = report
        st.session_state["client"] = client
        st.session_state["email_cfg"] = {
            "access_key": access_key, "secret_key": secret_key, "region": region,
            "sender": sender, "recipients": recipients, "slack_webhook": slack_webhook,
        }

        save_report_to_history(current_user["id"], report)
        log_activity(current_user["id"], current_user["username"], "generate_report",
                     f"{account_name} · {mode} · {label2}")

        alerts = get_budget_alerts(current_user["id"])
        if alerts:
            ses_cl = get_ses_client(access_key, secret_key, region) if sender else None
            triggered = check_and_trigger_alerts(report, alerts, ses_cl, sender)
            if triggered:
                st.session_state["alert_triggered"] = triggered

        bar.progress(100, "Done!")
    except Exception as e:
        bar.empty()
        st.error(f"❌ {e}")
        st.stop()


# ══════════════════════════════════════════
#  GUARD: nothing shown until report exists
# ══════════════════════════════════════════
if "report" not in st.session_state:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                padding:100px 20px;color:#8896a7;text-align:center;">
        <div style="font-size:3.5em;margin-bottom:12px;">💰</div>
        <div style="font-size:1.2em;font-weight:700;color:#1e3a5f;">Welcome to CloudCost Tracker</div>
        <div style="margin-top:8px;max-width:400px;">Enter your AWS credentials in the sidebar and click <strong>Run Report</strong> to get started.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

r = st.session_state["report"]

# Alert banner
if st.session_state.get("alert_triggered"):
    for trig in st.session_state["alert_triggered"]:
        st.warning(f"🔔 Alert **{trig['alert_name']}** triggered — spend ${trig['current']:,.2f} exceeded ${trig['threshold']:,.2f}")
    del st.session_state["alert_triggered"]


# ══════════════════════════════════════════
#  KPI BAR
# ══════════════════════════════════════════
kpi_cols = st.columns(6)
render_kpi(kpi_cols[0], "PREVIOUS PERIOD", f"${r['total1']:,.2f}", r['label1'], PRIMARY)
render_kpi(kpi_cols[1], "CURRENT PERIOD",  f"${r['total2']:,.2f}", r['label2'],
           DANGER if r['delta']>0 else SUCCESS if r['delta']<0 else PRIMARY, r['delta'])
render_kpi(kpi_cols[2], "MONTH-TO-DATE",   f"${r['current_month']:,.2f}", "Actual spend", INFO)
render_kpi(kpi_cols[3], "LAST MONTH",      f"${r['last_month']:,.2f}",    "Total",        PRIMARY)
render_kpi(kpi_cols[4], "FORECAST",        f"${r['forecast']:,.2f}",
           "Over budget" if r['forecast']>r['benchmark'] else "On track",
           DANGER if r['forecast']>r['benchmark'] else SUCCESS)
render_kpi(kpi_cols[5], "ANOMALIES",       str(len(r['anomalies'])),
           "Detected" if r['anomalies'] else "All clear",
           WARNING if r['anomalies'] else SUCCESS)

st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
render_budget_bar(r["current_month"], r["benchmark"])
st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  TABS  (5 tabs like AWS Cost Explorer)
# ══════════════════════════════════════════
tab_labels = ["📊 Overview", "🔍 Cost Explorer", "📈 Trends", "🔔 Anomalies & Alerts", "💡 Insights"]
if current_user["role"] == "admin":
    tab_labels.append("👑 Admin")

tabs = st.tabs(tab_labels)
t_overview, t_explorer, t_trends, t_anom, t_insights = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]
t_admin = tabs[5] if current_user["role"] == "admin" else None


# ══════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ══════════════════════════════════════════
with t_overview:
    row1, row2 = st.columns([3, 2])

    with row1:
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Cost Comparison</div>', unsafe_allow_html=True)
            top_svcs = top_services(r["services1"], r["services2"], r["total2"])
            if top_svcs:
                svc_labels = [short_name(s) for s in top_svcs]
                v1s = [r["services1"].get(s,0) for s in top_svcs]
                v2s = [r["services2"].get(s,0) for s in top_svcs]
                fig = go.Figure()
                fig.add_trace(go.Bar(name=r["label1"], x=svc_labels, y=v1s, marker_color=PRIMARY,
                                     text=[f"${v:,.0f}" for v in v1s], textposition="outside"))
                fig.add_trace(go.Bar(name=r["label2"], x=svc_labels, y=v2s, marker_color=GOLD,
                                     text=[f"${v:,.0f}" for v in v2s], textposition="outside"))
                fig.update_layout(barmode="group", template=plotly_tpl, height=360,
                                  paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                  yaxis_title="Cost (USD)", margin=dict(t=20,b=10),
                                  legend=dict(orientation="h",y=-0.18))
                st.plotly_chart(fig, use_container_width=True)

    with row2:
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Forecast vs Budget</div>', unsafe_allow_html=True)
            fig_fc = go.Figure()
            labels_fc = ["Last Month", "This Month", "Forecast"]
            vals_fc   = [r["last_month"], r["current_month"], r["forecast"]]
            colors_fc = [PRIMARY, PRIMARY_LIGHT, DANGER if r["forecast"]>r["benchmark"] else SUCCESS]
            fig_fc.add_trace(go.Bar(x=labels_fc, y=vals_fc, marker_color=colors_fc,
                                    text=[f"${v:,.0f}" for v in vals_fc], textposition="outside"))
            fig_fc.add_hline(y=r["benchmark"], line_dash="dash", line_color=GOLD, line_width=2,
                             annotation_text=f"Budget ${r['benchmark']:,.0f}", annotation_font_color=GOLD)
            fig_fc.update_layout(template=plotly_tpl, height=360, showlegend=False,
                                 paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                 yaxis_title="USD", margin=dict(t=20,b=10))
            st.plotly_chart(fig_fc, use_container_width=True)

    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Top Services — Period Comparison</div>', unsafe_allow_html=True)
        all_svcs = sorted(set(r["services1"])|set(r["services2"]),
                          key=lambda s: r["services2"].get(s,0), reverse=True)
        rows = []
        for svc in all_svcs:
            v1,v2 = r["services1"].get(svc,0), r["services2"].get(svc,0)
            if abs(v1)<0.01 and abs(v2)<0.01: continue
            diff = v2-v1
            pct  = f"{((v2-v1)/v1)*100:+.1f}%" if v1>0 else ("New" if v2>0 else "0%")
            rows.append({"Service": short_name(svc), "Previous": round(v1,2),
                         "Current": round(v2,2), "Δ ($)": round(diff,2), "Δ (%)": pct})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                         column_config={"Previous": st.column_config.NumberColumn(format="$%.2f"),
                                        "Current":  st.column_config.NumberColumn(format="$%.2f"),
                                        "Δ ($)":    st.column_config.NumberColumn(format="$%.2f")})

    # Export section inside Overview
    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Export & Email</div>', unsafe_allow_html=True)
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            html_report = build_email_html(r)
            st.download_button("⬇ Download HTML", data=html_report,
                               file_name=f"cost_report_{datetime.now().strftime('%Y%m%d')}.html",
                               mime="text/html", use_container_width=True)
        with ex2:
            if rows:
                csv = pd.DataFrame(rows).to_csv(index=False)
                st.download_button("⬇ Download CSV", data=csv,
                                   file_name=f"cost_data_{datetime.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv", use_container_width=True)
        with ex3:
            cfg = st.session_state.get("email_cfg", {})
            if cfg.get("sender") and cfg.get("recipients"):
                if st.button("📧 Send Email Report", use_container_width=True, type="primary"):
                    with st.spinner("Sending..."):
                        try:
                            ses = get_ses_client(cfg["access_key"], cfg["secret_key"], cfg["region"])
                            d = r["delta"]
                            subj = (f"🚨 [{r['account_name']}] Cost Up {abs(d):.1f}%" if d>1 else
                                    f"✅ [{r['account_name']}] Cost Down {abs(d):.1f}%" if d<-1 else
                                    f"ℹ️ [{r['account_name']}] Cost Report")
                            msg = MIMEMultipart("alternative")
                            msg["From"] = formataddr(("CloudCost Bot", cfg["sender"]))
                            recip_list = [x.strip() for x in cfg["recipients"].split(",")]
                            msg["To"] = ", ".join(recip_list)
                            msg["Subject"] = subj
                            msg.attach(MIMEText(build_email_html(r), "html"))
                            ses.send_raw_email(Source=cfg["sender"], Destinations=recip_list,
                                               RawMessage={"Data": msg.as_string()})
                            st.success("Email sent!")
                        except Exception as e:
                            st.error(f"❌ {e}")
            else:
                st.info("Set sender & recipients in sidebar to enable email.")


# ══════════════════════════════════════════
#  TAB 2 — COST EXPLORER
# ══════════════════════════════════════════
with t_explorer:
    with st.container(border=True):
        # Control bar — like AWS Cost Explorer
        ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 1])
        with ctrl1:
            group_by = st.selectbox("Group by", [
                "Service", "Region", "Linked Account", "Usage Type",
                "Tag", "S3 Usage Type", "EC2 Instance Type",
            ], key="explorer_group")
        with ctrl2:
            ex_start = st.date_input("From", value=date.today() - timedelta(days=30), key="ex_start")
        with ctrl3:
            ex_end = st.date_input("To", value=date.today(), key="ex_end")
        with ctrl4:
            chart_type = st.selectbox("Chart", ["Bar", "Line", "Area"], key="ex_chart")

        # Tag key picker (only when group_by=Tag)
        tag_key_selected = None
        if group_by == "Tag":
            tag_keys = fetch_available_tag_keys(st.session_state["client"]) if "client" in st.session_state else []
            if tag_keys:
                tag_key_selected = st.selectbox("Tag Key", tag_keys, key="explorer_tag_key")
            else:
                st.warning("No tag keys found on this account.")

        if st.button("🔍 Explore", type="primary", use_container_width=True, key="explorer_btn"):
            with st.spinner(f"Fetching cost by {group_by}..."):
                s, e = str(ex_start), str(ex_end)
                cl = st.session_state.get("client")
                if not cl:
                    st.error("Generate a report first to establish AWS connection.")
                else:
                    if group_by == "Service":
                        data = {}
                        _, svcs = fetch_custom_range_cost(cl, s, e)
                        data = {short_name(k): round(v,2) for k,v in svcs.items() if v > 0.01}
                    elif group_by == "Region":
                        data = fetch_cost_by_region(cl, s, e)
                    elif group_by == "Linked Account":
                        data = fetch_cost_by_account(cl, s, e)
                    elif group_by == "Usage Type":
                        data = fetch_cost_by_usage_type(cl, s, e)
                    elif group_by == "Tag" and tag_key_selected:
                        data = fetch_cost_by_tag(cl, tag_key_selected, s, e)
                    elif group_by == "S3 Usage Type":
                        data = fetch_s3_bucket_cost(cl, s, e)
                    elif group_by == "EC2 Instance Type":
                        data = fetch_ec2_instance_type_cost(cl, s, e)
                    else:
                        data = {}
                    st.session_state["explorer_data"]  = data
                    st.session_state["explorer_group_used"] = group_by

    if "explorer_data" in st.session_state:
        data = st.session_state["explorer_data"]
        grp  = st.session_state.get("explorer_group_used","")
        if not data:
            st.info("No data found for the selected period.")
        else:
            total_ex = sum(data.values())
            sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
            labels = [k for k,_ in sorted_data]
            values = [v for _,v in sorted_data]

            with st.container(border=True):
                st.markdown(f'<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Cost by {grp} &nbsp;|&nbsp; {ex_start} → {ex_end} &nbsp;|&nbsp; Total: ${total_ex:,.2f}</div>', unsafe_allow_html=True)

                fig_ex = go.Figure()
                if chart_type == "Bar":
                    fig_ex.add_trace(go.Bar(
                        x=labels[:30], y=values[:30],
                        marker_color=[PRIMARY if i < 3 else PRIMARY_LIGHT if i < 6 else GOLD for i in range(len(labels[:30]))],
                        text=[f"${v:,.2f}" for v in values[:30]], textposition="outside",
                    ))
                    fig_ex.update_layout(xaxis_tickangle=-30)
                elif chart_type == "Line":
                    fig_ex.add_trace(go.Scatter(
                        x=labels[:30], y=values[:30], mode="lines+markers+text",
                        line=dict(color=PRIMARY, width=3), marker=dict(size=7, color=NAVY),
                        text=[f"${v:,.0f}" for v in values[:30]], textposition="top center",
                    ))
                else:  # Area
                    fig_ex.add_trace(go.Scatter(
                        x=labels[:30], y=values[:30], mode="lines",
                        line=dict(color=PRIMARY, width=2), fill="tozeroy",
                        fillcolor="rgba(30,58,95,0.12)",
                    ))
                fig_ex.update_layout(template=plotly_tpl, height=400,
                                     paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                     yaxis_title="Cost (USD)", margin=dict(t=20,b=40))
                st.plotly_chart(fig_ex, use_container_width=True)

            with st.container(border=True):
                st.markdown(f'<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Breakdown Table — {grp}</div>', unsafe_allow_html=True)
                tbl_rows = [{"Name": k, "Cost (USD)": round(v,2),
                             "Share": f"{(v/total_ex*100):.1f}%",
                             "Bar": v/total_ex if total_ex>0 else 0} for k,v in sorted_data]
                st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True,
                             column_config={
                                 "Cost (USD)": st.column_config.NumberColumn(format="$%.2f"),
                                 "Bar": st.column_config.ProgressColumn(label="Share", format="%.1f%%", min_value=0, max_value=1),
                             })

    # Deep Dive section
    with st.expander("🔎 Service Deep Dive", expanded=False):
        active_services = sorted([s for s in r["services2"] if r["services2"].get(s,0)>0.5],
                                  key=lambda s: r["services2"].get(s,0), reverse=True)
        if active_services:
            dd_svc = st.selectbox("Select service", active_services,
                                   format_func=lambda s: f"{short_name(s)} — ${r['services2'].get(s,0):,.2f}",
                                   key="dd_svc_exp")
            ddc1, ddc2 = st.columns(2)
            with ddc1: dd_start = st.date_input("From", value=date.today()-timedelta(days=trend_days), key="dd_start_exp")
            with ddc2: dd_end   = st.date_input("To",   value=date.today(), key="dd_end_exp")

            if st.button("Analyze", key="dd_btn_exp", use_container_width=True):
                with st.spinner("Fetching..."):
                    det = fetch_service_detail(st.session_state["client"], dd_svc, start_date=dd_start, end_date=dd_end)
                    st.session_state["dd_detail"] = det
                    st.session_state["dd_svc_name"] = dd_svc

            if "dd_detail" in st.session_state:
                det = st.session_state["dd_detail"]
                sn  = short_name(st.session_state["dd_svc_name"])
                dd_col1, dd_col2, dd_col3 = st.columns(3)
                dd_col1.metric("Total", f"${det['total']:,.2f}")
                dd_col2.metric("Regions", str(len(det["regions"])))
                dd_col3.metric("Usage Types", str(len(det["usage_types"])))

                if det["trend"]:
                    df_det = pd.DataFrame(det["trend"])
                    fig_det = go.Figure(go.Scatter(
                        x=df_det["date"], y=df_det["cost"], mode="lines+markers",
                        line=dict(color=PRIMARY, width=3), fill="tozeroy",
                        fillcolor="rgba(30,58,95,0.08)",
                    ))
                    fig_det.update_layout(template=plotly_tpl, height=280,
                                          paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                          margin=dict(t=10,b=20))
                    st.plotly_chart(fig_det, use_container_width=True)

                rc1, rc2 = st.columns(2)
                with rc1:
                    if det["regions"]:
                        region_rows = [{"Region":k,"Cost":round(v,2)} for k,v in det["regions"].items()]
                        st.dataframe(pd.DataFrame(region_rows), use_container_width=True, hide_index=True,
                                     column_config={"Cost": st.column_config.NumberColumn(format="$%.2f")})
                with rc2:
                    if det["usage_types"]:
                        ut_rows = [{"Usage Type":k,"Cost":round(v,2)} for k,v in list(det["usage_types"].items())[:10]]
                        st.dataframe(pd.DataFrame(ut_rows), use_container_width=True, hide_index=True,
                                     column_config={"Cost": st.column_config.NumberColumn(format="$%.2f")})


# ══════════════════════════════════════════
#  TAB 3 — TRENDS
# ══════════════════════════════════════════
with t_trends:
    with st.container(border=True):
        st.markdown(f'<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Daily Cost Trend — Last {r["trend_days"]} Days</div>', unsafe_allow_html=True)
        if r["trend"]:
            df_trend = pd.DataFrame(r["trend"])
            avg = df_trend["cost"].mean()

            fig_tr = go.Figure()
            fig_tr.add_trace(go.Scatter(
                x=df_trend["date"], y=df_trend["cost"], mode="lines+markers",
                line=dict(color=PRIMARY, width=3), marker=dict(size=6, color=NAVY),
                fill="tozeroy", fillcolor="rgba(30,58,95,0.07)",
                hovertemplate="Date: %{x}<br>Cost: $%{y:,.2f}<extra></extra>",
            ))
            fig_tr.add_hline(y=avg, line_dash="dot", line_color=GOLD,
                             annotation_text=f"Avg ${avg:,.2f}", annotation_font_color=GOLD)
            fig_tr.update_layout(template=plotly_tpl, height=340,
                                 paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                 yaxis_title="Cost (USD)", margin=dict(t=20,b=20))
            st.plotly_chart(fig_tr, use_container_width=True)

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Daily Average", f"${avg:,.2f}")
            mc2.metric("Peak Day",      f"${df_trend['cost'].max():,.2f}")
            mc3.metric("Lowest Day",    f"${df_trend['cost'].min():,.2f}")
            mc4.metric("Period Total",  f"${df_trend['cost'].sum():,.2f}")

    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Service Cost Trend (Top 8 Services)</div>', unsafe_allow_html=True)
        if r["svc_trend"]:
            df_st = pd.DataFrame(r["svc_trend"])
            svc_totals = df_st.groupby("service")["cost"].sum().sort_values(ascending=False)
            top8 = svc_totals.head(8).index.tolist()
            df_st = df_st[df_st["service"].isin(top8)].copy()
            df_st["service"] = df_st["service"].apply(short_name)
            fig_st = px.area(df_st, x="date", y="cost", color="service", template=plotly_tpl, height=380,
                             color_discrete_sequence=[PRIMARY,GOLD,SUCCESS,DANGER,WARNING,"#457b9d","#8896a7","#5a6577"])
            fig_st.update_layout(paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                                 yaxis_title="Cost (USD)", margin=dict(t=20,b=20),
                                 legend=dict(orientation="h",y=-0.2))
            st.plotly_chart(fig_st, use_container_width=True)

    if r.get("spikes"):
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Day-over-Day Spikes (> 10% change)</div>', unsafe_allow_html=True)
            for spike in r["spikes"][:5]:
                c = DANGER if spike["change_pct"] > 0 else SUCCESS
                icon = "🔴" if spike["change_pct"] > 0 else "🟢"
                amt_sign = "+" if spike["change_amt"] > 0 else ""
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #e2e6ea;border-radius:8px;'
                    f'padding:12px 16px;margin:6px 0;display:flex;align-items:center;gap:12px;border-left:3px solid {c};">'
                    f'<span style="font-size:1.2em;">{icon}</span>'
                    f'<div><div style="font-weight:600;color:#0c1f3f;font-size:0.9em;">{spike["date"]} &nbsp;'
                    f'<span style="color:{c};">{spike["change_pct"]:+.1f}%</span></div>'
                    f'<div style="font-size:0.8em;color:#6c757d;">${spike["prev_cost"]:,.2f} → ${spike["cost"]:,.2f}'
                    f' &nbsp;(<span style="color:{c};">{amt_sign}${spike["change_amt"]:,.2f}</span>)</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════
#  TAB 4 — ANOMALIES & ALERTS
# ══════════════════════════════════════════
with t_anom:
    left_col, right_col = st.columns([3, 2])

    with left_col:
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">AWS Cost Anomalies</div>', unsafe_allow_html=True)
            if r["anomalies"]:
                total_impact = sum(abs(a["impact"]) for a in r["anomalies"])
                ai1, ai2 = st.columns(2)
                ai1.metric("Total Anomalies", len(r["anomalies"]))
                ai2.metric("Total Impact",    f"${total_impact:,.2f}")
                for i, anom in enumerate(r["anomalies"], 1):
                    icon = "🔴" if anom["impact"]>0 else "🟢"
                    c    = DANGER if anom["impact"]>0 else SUCCESS
                    end  = anom.get("end_date", "ongoing")
                    st.markdown(
                        f'<div style="background:#fff;border:1px solid #e2e6ea;border-radius:8px;'
                        f'padding:12px 16px;margin:6px 0;display:flex;align-items:center;gap:12px;border-left:3px solid {c};">'
                        f'<span style="font-size:1.2em;">{icon}</span>'
                        f'<div><div style="font-weight:600;color:#0c1f3f;font-size:0.9em;">Anomaly #{i} — '
                        f'<span style="color:{c};">${abs(anom["impact"]):,.2f}</span></div>'
                        f'<div style="font-size:0.8em;color:#6c757d;">{anom["start_date"]} → {end}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    if anom["root_causes"]:
                        st.dataframe(pd.DataFrame(anom["root_causes"]), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No cost anomalies detected.")

        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Service Threshold Alert</div>', unsafe_allow_html=True)
            svc_thr = st.number_input("Alert if service exceeds ($)", value=500, step=50, key="svc_thr")
            exceeded = sorted([(short_name(s), v) for s,v in r["services2"].items() if v > svc_thr],
                              key=lambda x: x[1], reverse=True)
            if exceeded:
                st.warning(f"⚠️ {len(exceeded)} services exceeded ${svc_thr:,.0f}")
                for sn, cost in exceeded:
                    pct_over = ((cost - svc_thr) / svc_thr) * 100
                    st.markdown(
                        f'<div style="background:#fff;border:1px solid #e2e6ea;border-radius:8px;'
                        f'padding:12px 16px;margin:6px 0;display:flex;align-items:center;gap:12px;border-left:3px solid {DANGER};">'
                        f'<span style="font-size:1.2em;">🔴</span>'
                        f'<div><div style="font-weight:600;color:#0c1f3f;font-size:0.9em;">{sn} — '
                        f'<span style="color:{DANGER};">${cost:,.2f}</span></div>'
                        f'<div style="font-size:0.8em;color:#6c757d;">{pct_over:.0f}% over threshold</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success(f"✅ No services exceeded ${svc_thr:,.0f}")

    with right_col:
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Budget Alert Rules</div>', unsafe_allow_html=True)
            with st.expander("➕ New Alert", expanded=False):
                new_name  = st.text_input("Name", placeholder="e.g. Monthly Budget", key="new_al_name")
                new_thr   = st.number_input("Threshold ($)", value=1000, step=100, key="new_al_thr")
                new_slack = st.text_input("Slack Webhook", placeholder="https://hooks.slack.com/...", key="new_al_slack")
                new_email = st.text_input("Email", placeholder="team@co.com", key="new_al_email")
                ab1, ab2  = st.columns(2)
                with ab1:
                    if st.button("✅ Create", type="primary", use_container_width=True, key="create_al"):
                        if new_name:
                            ok, msg = save_budget_alert(current_user["id"], new_name, new_thr, new_slack, new_email)
                            st.success(msg) if ok else st.error(msg)
                            st.rerun()
                        else:
                            st.warning("Name required")
                with ab2:
                    if new_slack and st.button("🧪 Test Slack", use_container_width=True, key="test_slack"):
                        test_r = r if "report" in st.session_state else {
                            "delta":5.2,"total2":1234,"forecast":2500,"benchmark":2000,
                            "account_name":"Test","anomalies":[]}
                        ok, msg = send_slack_alert(new_slack, test_r)
                        st.success(msg) if ok else st.error(msg)

            my_alerts = get_budget_alerts(current_user["id"])
            if my_alerts:
                for alert in my_alerts:
                    channels = []
                    if alert.get("slack_webhook"): channels.append("Slack")
                    if alert.get("alert_email"):   channels.append("Email")
                    status = "🟢" if alert["is_active"] else "⚫"
                    al1, al2, al3 = st.columns([4, 1, 1])
                    with al1:
                        st.markdown(f"{status} **{alert['alert_name']}** — ${alert['threshold']:,.0f}<br>"
                                    f"<small style='color:#6c757d;'>{', '.join(channels) or 'No channel'}</small>",
                                    unsafe_allow_html=True)
                    with al2:
                        if st.button("⏸" if alert["is_active"] else "▶", key=f"tog_{alert['id']}"):
                            toggle_alert(alert["id"], not alert["is_active"]); st.rerun()
                    with al3:
                        if st.button("🗑", key=f"del_{alert['id']}"):
                            delete_alert(alert["id"]); st.rerun()
                    st.divider()
            else:
                st.info("No alerts yet.")

        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Report History</div>', unsafe_allow_html=True)
            history = get_report_history(current_user["id"], limit=10)
            if history:
                hist_rows = [{"Date": h["created_at"][:10], "Period": h["label2"],
                              "Cost": round(h["total2"],2), "Δ%": round(h["delta"],1),
                              "Anomalies": h["anomaly_count"]} for h in history]
                st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True,
                             column_config={"Cost": st.column_config.NumberColumn(format="$%.2f"),
                                            "Δ%":   st.column_config.NumberColumn(format="%.1f%%")})
            else:
                st.info("No history yet.")


# ══════════════════════════════════════════
#  TAB 5 — INSIGHTS
# ══════════════════════════════════════════
with t_insights:
    # Cost Projection
    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Cost Projection</div>', unsafe_allow_html=True)
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Daily Avg", f"${r['daily_rate']:,.2f}")
        pc2.metric("Projected Month", f"${r['projected_month']:,.2f}")
        pc3.metric("AWS Forecast",    f"${r['forecast']:,.2f}")
        budget_diff = r['benchmark'] - r['projected_month']
        pc4.metric("vs Budget", f"${abs(budget_diff):,.0f}",
                   delta=f"{'Under' if budget_diff>0 else 'Over'} budget")

        fig_proj = go.Figure(go.Bar(
            x=["Last Month","Current","Projected","AWS Forecast","Budget"],
            y=[r["last_month"],r["current_month"],r["projected_month"],r["forecast"],r["benchmark"]],
            marker_color=[PRIMARY, PRIMARY_LIGHT, WARNING,
                          DANGER if r["forecast"]>r["benchmark"] else SUCCESS, GOLD],
            text=[f"${v:,.0f}" for v in [r["last_month"],r["current_month"],r["projected_month"],r["forecast"],r["benchmark"]]],
            textposition="outside",
        ))
        fig_proj.update_layout(template=plotly_tpl, height=320,
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_plot,
                               yaxis_title="USD", margin=dict(t=20,b=10), showlegend=False)
        st.plotly_chart(fig_proj, use_container_width=True)

    # Savings Plans & RI
    sp = r.get("savings_plans")
    ri = r.get("reservations")
    if sp or ri:
        with st.container(border=True):
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Savings Plans & Reserved Instances</div>', unsafe_allow_html=True)
            if sp:
                s1, s2, s3 = st.columns(3)
                s1.metric("SP Utilization",       f"{sp['utilization']}%")
                s2.metric("SP Net Savings",        f"${sp['savings']:,.2f}")
                s3.metric("SP Unused Commitment",  f"${sp['unused_commitment']:,.2f}")
            if ri:
                r1, r2, r3 = st.columns(3)
                r1.metric("RI Utilization",   f"{ri['utilization']}%")
                r2.metric("RI Net Savings",   f"${ri['net_savings']:,.2f}")
                r3.metric("RI Unused Hours",  f"{ri['unused_hours']:,.0f}")

    # Recommendations
    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Cost Optimization Recommendations</div>', unsafe_allow_html=True)
        sev_color = {"high": DANGER, "medium": WARNING, "low": INFO}
        savings_tips = compute_savings_opportunity(r["services2"], r.get("savings_plans"), r.get("reservations"))
        static_tips  = get_static_tips(r["services2"], r["total2"])
        idle_svcs    = detect_idle_services(r["services2"])

        if savings_tips:
            total_pot = sum(t.get("estimated_savings",0) for t in savings_tips)
            st.success(f"💰 Potential savings identified: **${total_pot:,.2f}/month**")
            for tip in savings_tips:
                c    = sev_color.get(tip["severity"], INFO)
                icon = "🔴" if tip["severity"]=="high" else "🟡" if tip["severity"]=="medium" else "🔵"
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #e2e6ea;border-radius:8px;'
                    f'padding:12px 16px;margin:6px 0;display:flex;align-items:flex-start;gap:12px;border-left:3px solid {c};">'
                    f'<span style="font-size:1.2em;flex-shrink:0;">{icon}</span>'
                    f'<div><div style="font-weight:600;color:#0c1f3f;font-size:0.9em;">[{tip["severity"].upper()}] {tip["category"]} — '
                    f'<span style="color:{SUCCESS};font-weight:700;">save ${tip["estimated_savings"]:,.2f}/mo</span></div>'
                    f'<div style="font-size:0.8em;color:#6c757d;margin-top:3px;">{tip["issue"]} → {tip["action"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        for tip in static_tips:
            c = sev_color.get(tip["severity"], INFO)
            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e6ea;border-radius:6px;'
                f'padding:10px 14px;margin:5px 0;border-left:3px solid {c};font-size:0.85em;">'
                f'{tip["icon"]} {tip["text"]}</div>',
                unsafe_allow_html=True,
            )

        if idle_svcs:
            st.markdown("**🔴 Potentially Idle Services (< $1/day)**")
            st.dataframe(pd.DataFrame([{"Service":s["service"],"Daily Cost":s["cost"],"Suggestion":s["suggestion"]} for s in idle_svcs]),
                         use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">EC2 Rightsizing</div>', unsafe_allow_html=True)
        if st.button("Fetch AWS Rightsizing Recommendations", use_container_width=True, key="rs_btn"):
            with st.spinner("Fetching..."):
                rs = get_rightsizing_recommendations(st.session_state.get("client"))
                st.session_state["rightsizing"] = rs
        if "rightsizing" in st.session_state:
            rs = st.session_state["rightsizing"]
            if not rs:
                st.success("✅ No rightsizing recommendations — EC2 fleet looks well-sized!")
            else:
                total_rs = sum(x.get("monthly_savings",0) for x in rs)
                st.metric("Total Potential Monthly Savings", f"${total_rs:,.2f}")
                st.dataframe(pd.DataFrame(rs), use_container_width=True, hide_index=True,
                             column_config={
                                 "monthly_cost":    st.column_config.NumberColumn(format="$%.2f"),
                                 "monthly_savings": st.column_config.NumberColumn(format="$%.2f"),
                             })

    # Custom date range comparison
    with st.container(border=True):
        st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Custom Date Range Comparison</div>', unsafe_allow_html=True)
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1: cs1 = st.date_input("Range 1 Start", value=date.today()-timedelta(days=14), key="cs1")
        with cc2: ce1 = st.date_input("Range 1 End",   value=date.today()-timedelta(days=7),  key="ce1")
        with cc3: cs2 = st.date_input("Range 2 Start", value=date.today()-timedelta(days=7),  key="cs2")
        with cc4: ce2 = st.date_input("Range 2 End",   value=date.today(),                    key="ce2")

        if st.button("Compare", use_container_width=True, key="cmp_btn"):
            cl = st.session_state.get("client")
            if cl:
                with st.spinner("Fetching..."):
                    t1,s1 = fetch_custom_range_cost(cl, str(cs1), str(ce1))
                    t2,s2 = fetch_custom_range_cost(cl, str(cs2), str(ce2))
                    cdelta = ((t2-t1)/t1*100) if t1>0 else 0
                    mc1,mc2,mc3 = st.columns(3)
                    mc1.metric(f"{cs1} → {ce1}", f"${t1:,.2f}")
                    mc2.metric(f"{cs2} → {ce2}", f"${t2:,.2f}")
                    mc3.metric("Change", f"{cdelta:+.1f}%", delta=f"${t2-t1:+,.2f}")

                    all_cmp = sorted(set(s1)|set(s2), key=lambda s: s2.get(s,0), reverse=True)
                    cmp_rows = [{"Service":short_name(s), "Range 1":round(s1.get(s,0),2),
                                  "Range 2":round(s2.get(s,0),2),
                                  "Diff":round(s2.get(s,0)-s1.get(s,0),2)}
                                 for s in all_cmp if abs(s1.get(s,0))>0.01 or abs(s2.get(s,0))>0.01]
                    if cmp_rows:
                        st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True,
                                     column_config={"Range 1":st.column_config.NumberColumn(format="$%.2f"),
                                                    "Range 2":st.column_config.NumberColumn(format="$%.2f"),
                                                    "Diff":   st.column_config.NumberColumn(format="$%.2f")})
            else:
                st.error("Generate a report first.")


# ══════════════════════════════════════════
#  ADMIN TAB
# ══════════════════════════════════════════
if current_user["role"] == "admin" and t_admin:
    with t_admin:
        sec1, sec2 = st.columns([3, 2])

        with sec1:
            with st.container(border=True):
                st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">User Management</div>', unsafe_allow_html=True)
                with st.expander("➕ Add New User"):
                    nc1, nc2 = st.columns(2)
                    with nc1:
                        nu  = st.text_input("Username",  key="nu")
                        ne  = st.text_input("Email",     key="ne")
                        nfn = st.text_input("Full Name", key="nfn")
                    with nc2:
                        np  = st.text_input("Password", type="password", key="np")
                        nr  = st.selectbox("Role", ["user","admin"], key="nr")
                    if st.button("Create User", type="primary", use_container_width=True, key="create_usr"):
                        if nu and ne and np and nfn:
                            ok, msg = create_user(nu, ne, np, nfn, nr)
                            st.success(msg) if ok else st.error(msg)
                            if ok: st.rerun()
                        else:
                            st.warning("All fields required")

                users = get_all_users()
                if users:
                    for u in users:
                        uc1,uc2,uc3,uc4 = st.columns([3,2,1,1])
                        with uc1:
                            st.markdown(f"**{u['full_name']}** `{u['username']}`<br>"
                                        f"<small style='color:#6c757d;'>{u['email']} · {u['role'].upper()}</small>",
                                        unsafe_allow_html=True)
                        with uc2:
                            st.markdown("🟢 Active" if u["is_active"] else "🔴 Inactive")
                        with uc3:
                            if u["username"] != current_user["username"]:
                                if st.button("Toggle", key=f"tog_u_{u['id']}"):
                                    toggle_user_status(u["id"], not u["is_active"]); st.rerun()
                        with uc4:
                            if u["username"] != current_user["username"]:
                                if st.button("🗑", key=f"del_u_{u['id']}"):
                                    delete_user(u["id"]); st.rerun()
                        st.divider()

            with st.container(border=True):
                st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Change Password</div>', unsafe_allow_html=True)
                users = get_all_users()
                cp1, cp2 = st.columns(2)
                with cp1: cp_user = st.selectbox("User", [u["username"] for u in users], key="cp_u")
                with cp2: cp_pass = st.text_input("New Password", type="password", key="cp_p")
                if st.button("Update Password", use_container_width=True, key="upd_pwd"):
                    if cp_user and cp_pass:
                        uid = next((u["id"] for u in users if u["username"]==cp_user), None)
                        st.success("✅ Updated") if uid and change_password(uid, cp_pass) else st.error("❌ Failed")

        with sec2:
            with st.container(border=True):
                st.markdown('<div style="font-size:15px;font-weight:800;color:#0c1f3f;border-bottom:2px solid #e2e6ea;padding-bottom:10px;margin-bottom:16px;">Audit Log</div>', unsafe_allow_html=True)
                al_limit  = st.selectbox("Show last", [50,100,250], key="al_lim")
                al_filter = st.selectbox("Action", ["All","login","logout","generate_report","create_user","delete_user","change_password"], key="al_fil")
                audit_logs = get_audit_logs(limit=int(al_limit))
                if al_filter != "All":
                    audit_logs = [a for a in audit_logs if a.get("action")==al_filter]
                if audit_logs:
                    audit_rows = [{"Time":a["created_at"][:16].replace("T"," "),
                                   "User":a["username"],"Action":a["action"],
                                   "Details":a.get("details","")} for a in audit_logs]
                    st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No entries yet.")


# ── FOOTER ──
st.markdown(
    '<div style="text-align:center;color:#8896a7;font-size:11px;padding:20px 0 8px;'
    'border-top:1px solid #e2e6ea;margin-top:30px;">'
    '💰 CloudCost Tracker v3.0 &nbsp;·&nbsp; AWS Cost Monitoring &nbsp;·&nbsp; '
    'Forecasting &nbsp;·&nbsp; Anomaly Detection &nbsp;·&nbsp; Recommendations<br>'
    '⚠️ AWS cost data may update for up to 72 hours.</div>',
    unsafe_allow_html=True,
)
