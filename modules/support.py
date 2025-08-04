import streamlit as st

def run(session):
    st.markdown("""
    <div style='font-size:30px; font-weight:700; margin-bottom:10px; color:#0068c9; font-family: Times New Roman;'>
         Support & About Us
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Who We Are")
    st.markdown("""
    We are a team of data-driven professionals dedicated to making retirement planning and investing simpler, smarter, and more accessible.  
    Our mission is to empower users to make informed financial decisions using intuitive tools, smart simulations, and explainable AI.

    This application was developed as part of a business analytics project, integrating real financial datasets and user-focused design.
    """)

    st.markdown("---")

    st.subheader("Frequently Asked Questions")
    
    # FAQ 1
    with st.expander("How are my retirement projections calculated?"):
        st.write("""
        Your projections use Monte Carlo simulation, which runs 1,000 different market scenarios based on historical data. We apply the 4% withdrawal rule (you can safely withdraw 4% of your pension pot annually in retirement), adjust all values for inflation to show real purchasing power, and include Ireland's state pension (currently ~€13,800/year from age 66). This gives you realistic ranges of possible outcomes.
        """)
    
    # FAQ 2
    with st.expander("What do the different risk profiles mean and how should I choose?"):
        st.write("""
        **Conservative**: Prefers stability over high returns. Recommended allocation: 20% stocks, 70% bonds, 10% cash. Best for those nearing retirement or uncomfortable with market volatility.
        
        **Moderate/Balanced**: Wants growth with some safety. Recommended allocation: 50% stocks, 40% bonds, 10% cash. Good for medium-term goals and moderate risk tolerance.
        
        **Opportunistic**: Comfortable with higher risk for potentially higher returns. Recommended allocation: 80% stocks, 15% bonds, 5% cash. Best for long investment horizons and growth-focused goals.
        """)
    
    # FAQ 3
    with st.expander("What's the difference between nominal and real returns in my projections?"):
        st.write("""
        Nominal returns are raw percentages without considering inflation. Real returns are adjusted for inflation and show your actual purchasing power. For example, if you earn 7% but inflation is 2%, your real return is about 5%. Our projections show real returns because €100 today won't buy the same amount in 30 years - real returns tell you what your money can actually purchase.
        """)
    
    # FAQ 4
    with st.expander("How accurate are these simulations and should I rely on them for planning?"):
        st.write("""
        These are educated estimates based on historical market patterns, not guarantees. Markets can behave differently than in the past. Use these projections as a starting point for planning, but review and adjust them annually as your circumstances change. Always consult with a qualified financial advisor before making major investment decisions, especially for retirement planning.
        """)
    
    # FAQ 5
    with st.expander("What happens if I change my contribution amount or retirement age?"):
        st.write("""
        Small changes can have big long-term impacts due to compound growth. Increasing contributions by €50/month or retiring 2 years later can significantly boost your final pension pot. Conversely, reducing contributions or retiring earlier can substantially lower your retirement income. Use our calculators to experiment with different scenarios and see how changes affect your projections.
        """)

    st.markdown("---")

    st.subheader("How Can We Help?")
    st.markdown("""
    - **Need help using the app?**  
      Go to the chatbot button in the bottom right corner of any page to ask questions.

    - **Want to understand how your projections are calculated?**  
      Use the tooltips or chat assistant to get quick explanations.

    - **Facing a bug or technical issue?**  
      Reach out to us below.
    """)

    st.markdown("---")

    st.subheader("Contact Us")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        📧 **Email**: support@finsightapp.com  
        ☎️ **Phone**: +353 1234 5678  
        💼 **LinkedIn**: [FinSight Team](https://linkedin.com)

        We're happy to hear your feedback or questions!
        """)

    with col2:
        with st.form("contact_form", clear_on_submit=True):
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            message = st.text_area("Your Message")
            submitted = st.form_submit_button("Send")

            if submitted:
                st.success("✅ Thank you! Your message has been received.")