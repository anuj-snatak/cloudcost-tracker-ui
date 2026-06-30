import streamlit as st
from auth import login, is_logged_in

NAVY = "#1e3a5f"
GOLD = "#c9a84c"
PRIMARY = "#1e3a5f"

def show_login_page():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ background: #f0f2f8; }}

    .login-wrapper {{
        display: flex; justify-content: center; align-items: center;
        min-height: 90vh;
    }}

    .login-hero {{
        background: linear-gradient(135deg, {NAVY} 0%, #2a5280 100%);
        border-radius: 20px 0 0 20px;
        padding: 60px 50px;
        color: white;
        min-height: 550px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    .login-brand {{
        font-family: 'Playfair Display', serif;
        font-size: 2.2em;
        font-weight: 800;
        color: white;
        margin-bottom: 8px;
    }}

    .login-tagline {{
        color: {GOLD};
        font-size: 0.95em;
        font-weight: 500;
        letter-spacing: 1px;
        margin-bottom: 40px;
    }}

    .feature-item {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 14px 0;
        color: rgba(255,255,255,0.85);
        font-size: 0.95em;
    }}

    .feature-dot {{
        width: 8px; height: 8px;
        background: {GOLD};
        border-radius: 50%;
        flex-shrink: 0;
    }}

    .login-form-box {{
        background: white;
        border-radius: 0 20px 20px 0;
        padding: 60px 50px;
        min-height: 550px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 8px 0 40px rgba(0,0,0,0.08);
    }}

    .login-form-title {{
        font-size: 1.8em;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 6px;
    }}

    .login-form-sub {{
        color: #8896a7;
        font-size: 0.9em;
        margin-bottom: 32px;
    }}

    .stat-box {{
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 40px;
        display: flex;
        gap: 30px;
    }}

    .stat-item {{ text-align: center; }}
    .stat-num {{ font-size: 1.5em; font-weight: 700; color: {GOLD}; }}
    .stat-label {{ font-size: 0.75em; color: rgba(255,255,255,0.6); margin-top: 2px; }}

    div[data-testid="stTextInput"] input {{
        border: 1.5px solid #d4d9e2 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 0.95em !important;
        color: {NAVY} !important;
        background: #f8fafc !important;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: {NAVY} !important;
        box-shadow: 0 0 0 3px rgba(30,58,95,0.1) !important;
    }}

    .stButton button {{
        background: {NAVY} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px !important;
        font-weight: 700 !important;
        font-size: 1em !important;
        width: 100% !important;
        margin-top: 8px !important;
        transition: all 0.2s !important;
    }}
    .stButton button:hover {{
        background: #2a5280 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(30,58,95,0.3) !important;
    }}

    footer {{ visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2a5280 100%);border-radius:20px 0 0 20px;padding:50px 40px;min-height:520px;display:flex;flex-direction:column;justify-content:center;">'
            '<div style="font-family:Georgia,serif;font-size:2em;font-weight:800;color:white;margin-bottom:6px;">💰 CloudCost Tracker</div>'
            '<div style="color:#c9a84c;font-size:0.9em;font-weight:600;letter-spacing:1px;margin-bottom:30px;">AWS COST MONITORING PLATFORM</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Real-time AWS cost monitoring &amp; alerts</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Daily, Weekly &amp; Monthly cost comparison</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Cost anomaly detection &amp; root cause analysis</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Forecast vs benchmark tracking</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Service-level deep dive &amp; region analysis</div>'
            '<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:rgba(255,255,255,0.85);font-size:0.9em;"><div style="width:8px;height:8px;background:#c9a84c;border-radius:50%;flex-shrink:0;"></div>Automated email reports via AWS SES</div>'
            '<div style="background:rgba(255,255,255,0.08);border-radius:12px;padding:16px 20px;margin-top:30px;display:flex;gap:30px;">'
            '<div style="text-align:center;"><div style="font-size:1.5em;font-weight:700;color:#c9a84c;">8+</div><div style="font-size:0.75em;color:rgba(255,255,255,0.6);margin-top:2px;">Dashboard Tabs</div></div>'
            '<div style="text-align:center;"><div style="font-size:1.5em;font-weight:700;color:#c9a84c;">15+</div><div style="font-size:0.75em;color:rgba(255,255,255,0.6);margin-top:2px;">Cost Metrics</div></div>'
            '<div style="text-align:center;"><div style="font-size:1.5em;font-weight:700;color:#c9a84c;">100%</div><div style="font-size:0.75em;color:rgba(255,255,255,0.6);margin-top:2px;">AWS Native</div></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div style="font-size:1.8em;font-weight:700;color:#1e3a5f;margin-bottom:6px;">Welcome back</div>'
            '<div style="color:#8896a7;font-size:0.9em;margin-bottom:28px;">Sign in to your account to continue</div>',
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
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
                            st.success(f"Welcome, {user['full_name']}!")
                            st.rerun()
                        else:
                            st.error(error)

        st.markdown("""
        <div style="text-align:center; margin-top:24px; color:#8896a7; font-size:0.8em;">
            Contact your administrator to get access
        </div>
        """, unsafe_allow_html=True)
