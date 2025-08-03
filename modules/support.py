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
        with st.form("contact_form"):
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            message = st.text_area("Your Message")
            submitted = st.form_submit_button("Send")

            if submitted:
                st.success("✅ Thank you! Your message has been received.")

