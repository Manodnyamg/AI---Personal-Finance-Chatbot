import streamlit as st

def run(session):
    st.header("Tax Computation")
    st.write("🛠️ Placeholder — Future tax estimator module.")
    if st.button("← Back to Home"):
        session.page = "landing"
