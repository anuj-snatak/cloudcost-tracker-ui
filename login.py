import streamlit as st
from auth import login

def show_login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    footer, #MainMenu, header { visibility: hidden; }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 1rem !important; max-width: 1100px !important; }
    div[data-testid="stForm"] { border: none !important; background: transparent !important; padding: 0 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 8px 32px rgba(15,23,42,0.10) !important; }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.2, 1], gap="medium")

    # ── LEFT: dark hero panel ──
    with left:
        st.markdown(
            '<div style="background:linear-gradient(155deg,#0c1f3f 0%,#1e3a5f 60%,#0f2744 100%);'
            'border-radius:20px;padding:40px 38px;overflow:hidden;position:relative;">'

            # glow blobs
            '<div style="position:absolute;top:-30px;right:-30px;width:160px;height:160px;border-radius:50%;background:rgba(245,158,11,0.10);filter:blur(40px);pointer-events:none;"></div>'
            '<div style="position:absolute;bottom:-40px;left:-20px;width:140px;height:140px;border-radius:50%;background:rgba(56,189,248,0.07);filter:blur(50px);pointer-events:none;"></div>'

            # logo
            '<div style="display:flex;align-items:center;gap:12px;margin-bottom:22px;">'
            '<div style="background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:12px;width:44px;height:44px;'
            'display:flex;align-items:center;justify-content:center;font-size:1.35em;'
            'box-shadow:0 4px 14px rgba(245,158,11,0.45);flex-shrink:0;">💰</div>'
            '<div>'
            '<div style="font-size:1.2em;font-weight:800;color:#f8fafc;letter-spacing:-0.3px;">CloudCost Tracker</div>'
            '<div style="font-size:0.65em;font-weight:700;color:#f59e0b;letter-spacing:2px;margin-top:1px;">AWS COST INTELLIGENCE</div>'
            '</div></div>'

            '<div style="width:36px;height:2px;background:linear-gradient(90deg,#f59e0b,transparent);border-radius:2px;margin-bottom:20px;"></div>'

            # features label
            '<div style="font-size:0.65em;font-weight:700;color:#475569;letter-spacing:2px;margin-bottom:10px;">FEATURES</div>'

            # feature rows — compact
            '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:8px;margin:5px 0;">'
            '<span style="font-size:1em;">📊</span>'
            '<div><div style="color:#f1f5f9;font-size:0.82em;font-weight:600;">Real-time cost monitoring & alerts</div>'
            '<div style="color:#64748b;font-size:0.7em;">Live AWS spend across all services</div></div></div>'

            '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:8px;margin:5px 0;">'
            '<span style="font-size:1em;">🔍</span>'
            '<div><div style="color:#f1f5f9;font-size:0.82em;font-weight:600;">Cost Explorer — Group by anything</div>'
            '<div style="color:#64748b;font-size:0.7em;">Service · Region · Tag · Instance Type</div></div></div>'

            '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:8px;margin:5px 0;">'
            '<span style="font-size:1em;">🔔</span>'
            '<div><div style="color:#f1f5f9;font-size:0.82em;font-weight:600;">Anomaly detection & budget alerts</div>'
            '<div style="color:#64748b;font-size:0.7em;">Slack & SES email notifications</div></div></div>'

            '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:8px;margin:5px 0;">'
            '<span style="font-size:1em;">💡</span>'
            '<div><div style="color:#f1f5f9;font-size:0.82em;font-weight:600;">Smart savings recommendations</div>'
            '<div style="color:#64748b;font-size:0.7em;">EC2 rightsizing · Savings Plans gap</div></div></div>'

            '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:8px;margin:5px 0;">'
            '<span style="font-size:1em;">📈</span>'
            '<div><div style="color:#f1f5f9;font-size:0.82em;font-weight:600;">Forecast vs benchmark tracking</div>'
            '<div style="color:#64748b;font-size:0.7em;">Projected month-end spend</div></div></div>'

            # stats
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:18px;">'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:12px 8px;text-align:center;">'
            '<div style="font-size:1.4em;font-weight:800;color:#f59e0b;line-height:1;">5</div>'
            '<div style="font-size:0.65em;color:#64748b;margin-top:3px;font-weight:500;">Smart Tabs</div></div>'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:12px 8px;text-align:center;">'
            '<div style="font-size:1.4em;font-weight:800;color:#f59e0b;line-height:1;">15+</div>'
            '<div style="font-size:0.65em;color:#64748b;margin-top:3px;font-weight:500;">Cost Metrics</div></div>'

            '<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:12px 8px;text-align:center;">'
            '<div style="font-size:1.4em;font-weight:800;color:#f59e0b;line-height:1;">100%</div>'
            '<div style="font-size:0.65em;color:#64748b;margin-top:3px;font-weight:500;">AWS Native</div></div>'

            '</div></div>',
            unsafe_allow_html=True,
        )

    # ── RIGHT: login form ──
    with right:
        with st.container(border=True):
            st.markdown(
                '<div style="padding:6px 4px 18px;">'
                '<div style="font-size:1.5em;font-weight:800;color:#0f172a;letter-spacing:-0.5px;margin-bottom:5px;">Welcome back 👋</div>'
                '<div style="color:#94a3b8;font-size:0.84em;">Sign in to your account to continue</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

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
                '<div style="text-align:center;margin-top:14px;color:#94a3b8;font-size:0.78em;">'
                'Contact your administrator to get access</div>',
                unsafe_allow_html=True,
            )
