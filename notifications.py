import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime

NAVY = "#0c1f3f"
GOLD = "#c9a84c"
DANGER = "#b91c1c"
SUCCESS = "#1a7a5c"
WARNING = "#b45309"


def send_slack_alert(webhook_url: str, report: dict) -> tuple[bool, str]:
    delta = report.get("delta", 0)
    total2 = report.get("total2", 0)
    forecast = report.get("forecast", 0)
    benchmark = report.get("benchmark", 0)
    account = report.get("account_name", "AWS Account")
    anomaly_count = len(report.get("anomalies", []))

    if delta > 5:
        color = "#b91c1c"
        emoji = "🚨"
        trend_text = f"*+{abs(delta):.1f}% increase*"
    elif delta < -5:
        color = "#1a7a5c"
        emoji = "✅"
        trend_text = f"*{delta:.1f}% decrease*"
    else:
        color = "#b45309"
        emoji = "ℹ️"
        trend_text = f"*{delta:+.1f}% change*"

    fc_status = "⚠️ Over Budget" if forecast > benchmark else "✅ On Track"

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"{emoji} CloudCost Alert — {account}"},
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Cost Change:*\n{trend_text}"},
                            {"type": "mrkdwn", "text": f"*Current Period:*\n${total2:,.2f}"},
                            {"type": "mrkdwn", "text": f"*Forecast:*\n${forecast:,.2f} — {fc_status}"},
                            {"type": "mrkdwn", "text": f"*Anomalies:*\n{anomaly_count} detected"},
                        ],
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"CloudCost Tracker · {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                        ],
                    },
                ],
            }
        ]
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True, "Slack alert sent"
        return False, f"Slack error: {resp.status_code} {resp.text}"
    except Exception as e:
        return False, f"Slack exception: {e}"


def build_alert_email_html(report: dict, alert_name: str) -> str:
    delta = report.get("delta", 0)
    dc = DANGER if delta > 0 else SUCCESS
    trend_text = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"
    fc_status = "Exceeding" if report.get("forecast", 0) > report.get("benchmark", 0) else "Below"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: Inter, sans-serif; background: #f8f9fc; color: {NAVY}; padding: 24px; }}
.box {{ background: white; border-radius: 10px; padding: 24px; margin: 12px 0;
        border-left: 4px solid {GOLD}; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
h2 {{ color: {NAVY}; border-bottom: 3px solid {GOLD}; padding-bottom: 8px; }}
.metric {{ display: inline-block; margin: 8px 16px 8px 0; }}
.metric-label {{ font-size: 0.75em; color: #5a6577; text-transform: uppercase; letter-spacing: 1px; }}
.metric-value {{ font-size: 1.4em; font-weight: 700; color: {NAVY}; }}
</style></head><body>
<h2>🔔 Budget Alert: {alert_name}</h2>
<div class="box">
  <div class="metric"><div class="metric-label">Account</div><div class="metric-value">{report.get("account_name","")}</div></div>
  <div class="metric"><div class="metric-label">Cost Change</div>
    <div class="metric-value" style="color:{dc};">{delta:+.2f}% {trend_text}</div></div>
  <div class="metric"><div class="metric-label">Current Period</div><div class="metric-value">${report.get("total2",0):,.2f}</div></div>
  <div class="metric"><div class="metric-label">This Month</div><div class="metric-value">${report.get("current_month",0):,.2f}</div></div>
  <div class="metric"><div class="metric-label">Forecast</div><div class="metric-value">${report.get("forecast",0):,.2f} — {fc_status} budget</div></div>
  <div class="metric"><div class="metric-label">Anomalies</div><div class="metric-value">{len(report.get("anomalies",[]))}</div></div>
</div>
<p style="font-size:11px;color:#8896a7;">* AWS cost data may update for up to 72 hours.</p>
</body></html>"""


def send_budget_alert_email(ses_client, sender: str, recipients: list[str], alert_name: str, report: dict) -> tuple[bool, str]:
    delta = report.get("delta", 0)
    account = report.get("account_name", "AWS")
    if delta > 1:
        subject = f"🚨 [{account}] Budget Alert: Cost Up {abs(delta):.1f}%"
    elif delta < -1:
        subject = f"✅ [{account}] Budget Alert: Cost Down {abs(delta):.1f}%"
    else:
        subject = f"ℹ️ [{account}] Budget Alert: {alert_name}"

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("CloudCost Alerts", sender))
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(build_alert_email_html(report, alert_name), "html"))

    try:
        ses_client.send_raw_email(
            Source=sender,
            Destinations=recipients,
            RawMessage={"Data": msg.as_string()},
        )
        return True, "Email alert sent"
    except Exception as e:
        return False, f"Email error: {e}"


def check_and_trigger_alerts(report: dict, alerts: list, ses_client=None, sender: str = "") -> list[dict]:
    import os
    from supabase import create_client
    import streamlit as st
    SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))

    current_month = report.get("current_month", 0)
    triggered = []

    for alert in alerts:
        if not alert.get("is_active"):
            continue
        threshold = alert.get("threshold", 0)
        if current_month < threshold:
            continue

        result = {"alert_name": alert["alert_name"], "threshold": threshold, "current": current_month, "results": []}

        if alert.get("slack_webhook"):
            ok, msg = send_slack_alert(alert["slack_webhook"], report)
            result["results"].append({"channel": "slack", "ok": ok, "msg": msg})

        if alert.get("alert_email") and ses_client and sender:
            recipients = [e.strip() for e in alert["alert_email"].split(",")]
            ok, msg = send_budget_alert_email(ses_client, sender, recipients, alert["alert_name"], report)
            result["results"].append({"channel": "email", "ok": ok, "msg": msg})

        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            client.table("budget_alerts").update({"last_triggered": datetime.now().isoformat()}).eq("id", alert["id"]).execute()
        except Exception:
            pass

        triggered.append(result)

    return triggered
