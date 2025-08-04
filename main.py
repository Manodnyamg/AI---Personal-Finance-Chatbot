import streamlit as st
from modules import retirement, risk, etf, portfolio, support
import os

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
    st.rerun()  # Force immediate rerun

# --- Navigation Bar --- (with tips inside the container)
st.markdown('<div class="nav-container">', unsafe_allow_html=True)

col_logo, col_spacer, col_nav = st.columns([0.2, 0.3, 2.5])
with col_logo:
    # Only show FinSight button if NOT on landing page
    if st.session_state.page != "landing":
        if st.button("🏠", key="home_logo_button"):
            go("landing")
        st.markdown("""
        <style>
        [data-testid="stButton"][key="home_logo_button"] > button {
            font-size: 30px;
            font-weight: bold;
            color: #0068c9;
            background: none;
            border: none;
            font-family: 'Times New Roman', serif;
            margin-top: 1rem;
            padding: 10px 20px;
            border-radius: 8px;        
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
    # Create two columns: 65% for content, 35% for image
    content_col, image_col = st.columns([0.65, 0.35])
    
    with content_col:
        st.markdown("""
            <div style='color: #0068c9; padding: 80px 0px 40px 0px; font-size: 2.8rem; 
                        font-weight: bold; text-align: center; margin-bottom: 2rem; line-height: 1.2;'>
                Plan. Invest. Retire — Smarter.
            </div>
        """, unsafe_allow_html=True)
        
        # Create centered column for button (half width)
        button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
        with button_col2:
            # Get Started Button
            st.button("Get Started to assess your risk tolerance",
                      on_click=lambda: go("risk"),
                      use_container_width=True,
                      key="risk_button")

        # Button styling
        st.markdown("""
            <style>
            [data-testid="stButton"][data-widget-id="risk_button"] > button {
                background-color: #0068c9 !important;
                color: white !important;
                border: 2px solid white !important;
                font-weight: bold !important;
                font-size: 16px !important;
                border-radius: 8px !important;
                height: 50px !important;
                width: 100% !important;
                text-align: center !important;
                margin-bottom: 2rem !important;
            }
            [data-testid="stButton"][data-widget-id="risk_button"] > button:hover {
                background-color: #004494 !important;
                border: 2px solid white !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Tips section
        st.markdown("""
        <div style='margin-top: 1.5rem; background-color: #e9f3fb; padding: 15px; border-radius: 10px; border-left: 4px solid #0068c9;'>
            <strong style='color: #0068c9; font-size: 14px;'>💡 Tips for First-Time Users:</strong><br>
            <div style='line-height: 1.5; color: #2d3748; font-size: 13px; margin-top: 8px;'>
                • Start with the <em style='color: #0068c9; font-weight: 600;'>Risk Profile</em> or <em style='color: #0068c9; font-weight: 600;'>Retirement Planner</em><br>
                • Use the <em style='color: #0068c9; font-weight: 600;'>ETFs Calculator</em> to explore investment options<br>
                • <em style='color: #0068c9; font-weight: 600;'>Portfolio Simulation</em> helps visualize future performance<br>
                • Need help? Visit the <em style='color: #0068c9; font-weight: 600;'>Support</em> tab anytime!
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with image_col:
        # Add top padding to align the image with the content
        st.markdown("<div style='padding-top: 120px;'></div>", unsafe_allow_html=True)
        
        # Get the absolute path to the directory where the script is running
        current_dir = os.path.dirname(__file__)
        # Construct the full path to the image file
        image_path = os.path.join(current_dir, "assets", "hero_image.png")
        
        # Check if the file exists at the constructed path
        if os.path.exists(image_path):
            # Display the image using the absolute path
            st.image(image_path, use_container_width=True)
        else:
            # Fallback if the image is still not found
            st.warning(f"Image not found at path: {image_path}")
            st.markdown("""
            <div style='background-color: #f7fafc; border: 2px dashed #cbd5e0; border-radius: 12px;
                        height: 200px; width: 300px; display: flex; align-items: center; justify-content: center;
                        color: #718096; font-size: 14px; text-align: center;'>
                <div>
                    Image File Missing<br>
                    <small>(Check your 'assets' folder and file name)</small>
                </div>
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

# --- Render the Azure OpenAI Chatbot Popup on every page ---
# Use try-except to handle import issues gracefully
try:
    from modules.chatbot_popup import render_popup_chatbot
    render_popup_chatbot()
except ImportError as e:
    # Fallback if chatbot_popup module is not found
    st.error(f"Chatbot module not found: {e}")
    st.info("Please ensure 'chatbot_popup.py' is in the modules folder.")
except Exception as e:
    # Handle any other errors gracefully
    st.error(f"Error loading chatbot: {e}")
    # You can add a simple fallback chatbot here if needed