import streamlit as st
from modules import retirement, risk, etf, portfolio, support

# Set page config
st.set_page_config(page_title="Personal Finance App", page_icon="💰", layout="wide")

# --- Initialize session state ---
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "rp_step" not in st.session_state:
    st.session_state.rp_step = 1

if "form_data" not in st.session_state:
    st.session_state.form_data = {}

# --- Helper function to navigate pages ---
def go(page, rp_step=None):
    st.session_state.page = page
    if rp_step is not None:
        st.session_state.rp_step = rp_step

# --- Navigation Bar --- (with tips inside the container)
st.markdown('<div class="nav-container">', unsafe_allow_html=True)

col_logo, col_nav = st.columns([1, 3])
with col_logo:
    if st.button("💰 FinSight", key="home_logo_button"):
        go("landing")
    st.markdown("""
    <style>
    [data-testid="stButton"][key="home_logo_button"] > button {
        font-size: 24px;
        font-weight: bold;
        color: #0068c9;
        background: none;
        border: none;
        font-family: 'Times New Roman', serif;
        padding: 0;
        margin-top: -8px;
        margin-bottom: -8px;
        box-shadow: none;
    }
    [data-testid="stButton"][key="home_logo_button"] > button:hover {
        text-decoration: underline;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)


with col_nav:
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        with st.container():
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("Retirement Planner"):
                go("retirement", rp_step=1)
            st.markdown('</div>', unsafe_allow_html=True)
    with nav2:
        with st.container():
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("ETFs Calculator"):
                go("etf")
            st.markdown('</div>', unsafe_allow_html=True)
    with nav3:
        with st.container():
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("Portfolio Simulation"):
                go("portfolio")
            st.markdown('</div>', unsafe_allow_html=True)
    with nav4:
        with st.container():
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("Support"):
                go("support")
            st.markdown('</div>', unsafe_allow_html=True)

# --- Page Routing ---
if st.session_state.page == "landing":
    st.markdown("""
        <div style='color: #0068c9; padding: 100px 0px 75px 0px; font-size: 2.5rem; 
                    font-weight: bold; text-align: center; margin-bottom: 2rem;'>
            Plan. Invest. Retire — Smarter.
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("Get Started to Assess Your Risk Tolerance",
                  on_click=lambda: go("risk"),
                  use_container_width=True,
                  key="risk_button")

    st.markdown("""
        <style>
        [data-testid="stButton"][data-widget-id="risk_button"] > button {
            background-color: black !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            height: 50px !important;
            width: 100% !important;
            text-align: center !important;
        }
        [data-testid="stButton"][data-widget-id="risk_button"] > button:hover {
            background-color: #222 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 💡 Tips for Users (placed inside nav container, styled to appear below buttons)
    st.markdown("""
    <div style='margin-top: 1rem; background-color: #e9f3fb; padding: 10px 20px; border-radius: 8px;'>
        <strong> Tips for First-Time Users:</strong><br>
        • Start with the Risk Profile quiz to get a personalized assessment of your investment style.
        • Next, use the Retirement Planner and Portfolio Simulation to see how your profile can impact your long-term goals.
        • Use the ETFs Calculator to explore specific, low-cost investment options that align with your plan.
        • Need help? Visit the Support tab anytime!
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Close nav-container

elif st.session_state.page == "retirement":
    retirement.run(st.session_state)

elif st.session_state.page == "risk":
    risk.run(st.session_state)

elif st.session_state.page == "etf":
    etf.run(st.session_state)

elif st.session_state.page == "portfolio":
    portfolio.run(st.session_state)

elif st.session_state.page == "support":
    support.run(st.session_state)
