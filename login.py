import streamlit as st
from auth import login

def show_login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

    .stApp { background: #f1f5f9 !important; }
    footer, #MainMenu, header { visibility: hidden; }
    .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }

    div[data-testid="stTextInput"] input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 0.95em !important;
        color: #0f172a !important;
        background: #f8fafc !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #1e3a5f !important;
        box-shadow: 0 0 0 3px rgba(30,58,95,0.1) !important;
        background: #fff !important;
    }
    div[data-testid="stTextInput"] label {
        color: #64748b !important;
        font-size: 0.8em !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2a5280 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px !important;
        font-weight: 700 !important;
        font-size: 0.95em !important;
        width: 100% !important;
        box-shadow: 0 4px 14px rgba(30,58,95,0.35) !important;
        transition: all 0.2s !important;
        letter-spacing: 0.3px !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(30,58,95,0.45) !important;
    }

    div[data-testid="stForm"] { border: none !important; background: transparent !important; padding: 0 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 24px rgba(15,23,42,0.08) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    left, gap, right = st.columns([1.1, 0.05, 0.95])

    # ── LEFT PANEL ──
    with left:
        st.markdown(
            '<div style="background:linear-gradient(155deg,#0f172a 0%,#1e3a5f 55%,#0f2744 100%);'
            'border-radius:20px;padding:48px 44px;position:relative;overflow:hidden;">'

            # Glow blobs
            '<div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;'
            'border-radius:50%;background:rgba(245,158,11,0.08);filter:blur(30px);"></div>'
            '<div style="position:absolute;bottom:-50px;left:-30px;width:180px;height:180px;'
            'border-radius:50%;background:rgba(56,189,248,0.06);filter:blur(40px);"></div>'

            # Logo row
            '<div style="display:flex;align-items:center;gap:14px;margin-bottom:28px;">'
            '<div style="background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:14px;'
            'width:48px;height:48px;display:flex;align-items:center;justify-content:center;'
            'font-size:1.5em;box-shadow:0 4px 16px rgba(245,158,11,0.4);flex-shrink:0;">💰</div>'
            '<div>'
            '<div style="font-size:1.3em;font-weight:800;color:#f8fafc;letter-spacing:-0.3px;line-height:1.1;">CloudCost Tracker</div>'
            '<div style="font-size:0.68em;font-weight:700;color:#f59e0b;letter-spacing:2px;margin-top:2px;">AWS COST INTELLIGENCE</div>'
            '</div></div>'

            # Divider
            '<div style="width:40px;height:2px;background:linear-gradient(90deg,#f59e0b,transparent);'
            'border-radius:2px;margin-bottom:26px;"></div>'

            # Features label
            '<div style="font-size:0.68em;font-weight:700;color:#475569;letter-spacing:2px;margin-bottom:14px;">FEATURES</div>'

            # Feature 1
            '<div style="display:flex;align-items:flex-start;gap:12px;margin:10px 0;padding:10px 12px;'
            'background:rgba(255,255,255,0.04);border-radius:10px;">'
            '<span style="font-size:1.1em;margin-top:1px;">📊</span>'
            '<div><div style="color:#f1f5f9;font-size:0.85em;font-weight:600;">Real-time cost monitoring</div>'
            '<div style="color:#64748b;font-size:0.73em;margin-top:2px;">Live AWS spend across all services</div></div></div>'

            # Feature 2
            '<div style="display:flex;align-items:flex-start;gap:12px;margin:10px 0;padding:10px 12px;'
            'background:rgba(255,255,255,0.04);border-radius:10px;">'
            '<span style="font-size:1.1em;margin-top:1px;">🔍</span>'
            '<div><div style="color:#f1f5f9;font-size:0.85em;font-weight:600;">Cost Explorer — Group by anything</div>'
            '<div style="color:#64748b;font-size:0.73em;margin-top:2px;">Service · Region · Tag · Instance Type</div></div></div>'

            # Feature 3
            '<div style="display:flex;align-items:flex-start;gap:12px;margin:10px 0;padding:10px 12px;'
            'background:rgba(255,255,255,0.04);border-radius:10px;">'
            '<span style="font-size:1.1em;margin-top:1px;">🔔</span>'
            '<div><div style="color:#f1f5f9;font-size:0.85em;font-weight:600;">Anomaly detection & budget alerts</div>'
            '<div style="color:#64748b;font-size:0.73em;margin-top:2px;">Slack & SES email notifications</div></div></div>'

            # Feature 4
            '<div style="display:flex;align-items:flex-start;gap:12px;margin:10px 0;padding:10px 12px;'
            'background:rgba(255,255,255,0.04);border-radius:10px;">'
            '<span style="font-size:1.1em;margin-top:1px;">💡</span>'
            '<div><div style="color:#f1f5f9;font-size:0.85em;font-weight:600;">Smart savings recommendations</div>'
            '<div style="color:#64748b;font-size:0.73em;margin-top:2px;">EC2 rightsizing · Savings Plans gap</div></div></div>'

            # Feature 5
            '<div style="display:flex;align-items:flex-start;gap:12px;margin:10px 0;padding:10px 12px;'
            'background:rgba(255,255,255,0.04);border-radius:10px;">'
            '<span style="font-size:1.1em;margin-top:1px;">📈</span>'
            '<div><div style="color:#f1f5f9;font-size:0.85em;font-weight:600;">Forecast vs benchmark tracking</div>'
            '<div style="color:#64748b;font-size:0.73em;margin-top:2px;">Projected month-end spend</div></div></div>'

            # Stats
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:24px;">'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:12px;padding:14px 10px;text-align:center;">'
            '<div style="font-size:1.5em;font-weight:800;color:#f59e0b;line-height:1;">5</div>'
            '<div style="font-size:0.68em;color:#64748b;margin-top:4px;font-weight:500;">Smart Tabs</div></div>'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:12px;padding:14px 10px;text-align:center;">'
            '<div style="font-size:1.5em;font-weight:800;color:#f59e0b;line-height:1;">15+</div>'
            '<div style="font-size:0.68em;color:#64748b;margin-top:4px;font-weight:500;">Cost Metrics</div></div>'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:12px;padding:14px 10px;text-align:center;">'
            '<div style="font-size:1.5em;font-weight:800;color:#f59e0b;line-height:1;">100%</div>'
            '<div style="font-size:0.68em;color:#64748b;margin-top:4px;font-weight:500;">AWS Native</div></div>'

            '</div></div>',
            unsafe_allow_html=True,
        )

    # ── RIGHT PANEL ──
    with right:
        with st.container(border=True):
            st.markdown(
                '<div style="padding:8px 4px 20px;">'
                '<div style="font-size:1.55em;font-weight:800;color:#0f172a;letter-spacing:-0.5px;margin-bottom:6px;">Welcome back 👋</div>'
                '<div style="color:#94a3b8;font-size:0.85em;">Sign in to your account to continue</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("USERNAME", placeholder="Enter your username")
                password = st.text_input("PASSWORD", type="password", placeholder="Enter your password")
                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In →", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please enter username and password")
                    else:
                        with st.spinner("Authenticating..."):
                            user, error = login(username, password)
                            if user:
                                st.session_state["logged_in"] = True
                                st.session_state["current_user"] = user
                                st.rerun()
                            else:
                                st.error(error or "Invalid credentials")

            st.markdown(
                '<div style="text-align:center;margin-top:16px;color:#94a3b8;font-size:0.78em;">'
                'Contact your administrator to get access</div>',
                unsafe_allow_html=True,
            )
