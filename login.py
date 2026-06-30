import streamlit as st
from auth import login

def show_login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

    .stApp { background: #0f172a !important; }
    footer, #MainMenu, header { visibility: hidden; }

    /* hide default streamlit padding */
    .block-container { padding: 0 !important; max-width: 100% !important; }
    section[data-testid="stMain"] > div { padding: 0 !important; }

    /* inputs */
    div[data-testid="stTextInput"] input {
        background: #1e293b !important;
        border: 1.5px solid #334155 !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        padding: 12px 16px !important;
        font-size: 0.95em !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 3px rgba(245,158,11,0.15) !important;
        background: #1e293b !important;
    }
    div[data-testid="stTextInput"] input::placeholder { color: #64748b !important; }
    div[data-testid="stTextInput"] label { color: #94a3b8 !important; font-size: 0.82em !important; font-weight: 600 !important; }

    /* sign in button */
    .stButton button {
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px !important;
        font-weight: 800 !important;
        font-size: 0.95em !important;
        width: 100% !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 14px rgba(245,158,11,0.3) !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(245,158,11,0.45) !important;
    }

    /* form */
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    /* alert/error */
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])

    # ── LEFT PANEL ──
    with left:
        st.markdown(
            '<div style="'
            'min-height:100vh;'
            'background:linear-gradient(160deg,#0f172a 0%,#1e3a5f 60%,#0f2744 100%);'
            'padding:60px 56px;'
            'display:flex;flex-direction:column;justify-content:center;'
            'position:relative;overflow:hidden;'
            '">'

            # Decorative circles
            '<div style="position:absolute;top:-60px;right:-60px;width:280px;height:280px;'
            'border-radius:50%;background:rgba(245,158,11,0.06);"></div>'
            '<div style="position:absolute;bottom:-80px;left:-40px;width:220px;height:220px;'
            'border-radius:50%;background:rgba(99,179,237,0.05);"></div>'
            '<div style="position:absolute;top:40%;right:10%;width:100px;height:100px;'
            'border-radius:50%;background:rgba(245,158,11,0.04);"></div>'

            # Logo
            '<div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">'
            '<div style="background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:14px;'
            'width:52px;height:52px;display:flex;align-items:center;justify-content:center;'
            'font-size:1.6em;box-shadow:0 4px 20px rgba(245,158,11,0.4);">💰</div>'
            '<div>'
            '<div style="font-size:1.55em;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;">CloudCost Tracker</div>'
            '<div style="font-size:0.72em;font-weight:600;color:#f59e0b;letter-spacing:2px;margin-top:1px;">AWS COST INTELLIGENCE</div>'
            '</div></div>'

            '<div style="width:48px;height:3px;background:linear-gradient(90deg,#f59e0b,transparent);border-radius:2px;margin:20px 0 32px;"></div>'

            # Features
            '<div style="font-size:0.78em;font-weight:700;color:#64748b;letter-spacing:1.5px;margin-bottom:16px;">WHAT YOU GET</div>'

            '<div style="display:flex;align-items:center;gap:14px;margin:12px 0;">'
            '<div style="background:rgba(245,158,11,0.12);border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;">📊</div>'
            '<div><div style="color:#f1f5f9;font-size:0.88em;font-weight:600;">Real-time cost monitoring & alerts</div>'
            '<div style="color:#64748b;font-size:0.75em;margin-top:2px;">Live AWS spend across all services</div></div></div>'

            '<div style="display:flex;align-items:center;gap:14px;margin:12px 0;">'
            '<div style="background:rgba(245,158,11,0.12);border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;">🔍</div>'
            '<div><div style="color:#f1f5f9;font-size:0.88em;font-weight:600;">Cost Explorer — Group by anything</div>'
            '<div style="color:#64748b;font-size:0.75em;margin-top:2px;">Service, Region, Tag, Instance Type</div></div></div>'

            '<div style="display:flex;align-items:center;gap:14px;margin:12px 0;">'
            '<div style="background:rgba(245,158,11,0.12);border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;">🔔</div>'
            '<div><div style="color:#f1f5f9;font-size:0.88em;font-weight:600;">Anomaly detection & budget alerts</div>'
            '<div style="color:#64748b;font-size:0.75em;margin-top:2px;">Slack & SES email notifications</div></div></div>'

            '<div style="display:flex;align-items:center;gap:14px;margin:12px 0;">'
            '<div style="background:rgba(245,158,11,0.12);border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;">💡</div>'
            '<div><div style="color:#f1f5f9;font-size:0.88em;font-weight:600;">Smart savings recommendations</div>'
            '<div style="color:#64748b;font-size:0.75em;margin-top:2px;">EC2 rightsizing, Savings Plans gap</div></div></div>'

            '<div style="display:flex;align-items:center;gap:14px;margin:12px 0;">'
            '<div style="background:rgba(245,158,11,0.12);border-radius:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;">📈</div>'
            '<div><div style="color:#f1f5f9;font-size:0.88em;font-weight:600;">Forecast vs benchmark tracking</div>'
            '<div style="color:#64748b;font-size:0.75em;margin-top:2px;">Projected month-end spend</div></div></div>'

            # Stats
            '<div style="margin-top:36px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">'

            '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);'
            'border-radius:12px;padding:16px 12px;text-align:center;">'
            '<div style="font-size:1.6em;font-weight:800;color:#f59e0b;">5</div>'
            '<div style="font-size:0.7em;color:#64748b;margin-top:3px;font-weight:500;">Smart Tabs</div>'
            '</div>'

            '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);'
            'border-radius:12px;padding:16px 12px;text-align:center;">'
            '<div style="font-size:1.6em;font-weight:800;color:#f59e0b;">15+</div>'
            '<div style="font-size:0.7em;color:#64748b;margin-top:3px;font-weight:500;">Cost Metrics</div>'
            '</div>'

            '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);'
            'border-radius:12px;padding:16px 12px;text-align:center;">'
            '<div style="font-size:1.6em;font-weight:800;color:#f59e0b;">100%</div>'
            '<div style="font-size:0.7em;color:#64748b;margin-top:3px;font-weight:500;">AWS Native</div>'
            '</div>'

            '</div></div>',
            unsafe_allow_html=True,
        )

    # ── RIGHT PANEL ──
    with right:
        st.markdown(
            '<div style="min-height:100vh;background:#0f172a;display:flex;'
            'align-items:center;justify-content:center;padding:40px 48px;">'
            '<div style="width:100%;max-width:400px;">'

            '<div style="margin-bottom:32px;">'
            '<div style="font-size:1.7em;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;margin-bottom:8px;">Welcome back 👋</div>'
            '<div style="color:#64748b;font-size:0.88em;">Sign in to your account to continue</div>'
            '</div>'

            '</div></div>',
            unsafe_allow_html=True,
        )

        # Spacer to align form vertically
        st.markdown('<div style="height:22vh;"></div>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("USERNAME", placeholder="Enter your username")
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            password = st.text_input("PASSWORD", type="password", placeholder="Enter your password")
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
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
            '<div style="text-align:center;margin-top:20px;color:#475569;font-size:0.78em;">'
            'Contact your administrator to get access</div>',
            unsafe_allow_html=True,
        )
