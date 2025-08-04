import streamlit as st
import random
import os
import pickle
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


# REMOVED st.set_page_config() - this is handled by main.py
# MOVED all st.markdown() calls to a function to avoid executing at import time

def initialize_risk_session_state():
    """Initialize session state variables specific to risk assessment"""
    if 'risk_page' not in st.session_state:
        st.session_state.risk_page = 'start'
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'risk_profile' not in st.session_state:
        st.session_state.risk_profile = ""
    if 'model_confidence' not in st.session_state:
        st.session_state.model_confidence = 0.0

# ========================================
# QUESTIONNAIRE QUESTIONS
# ========================================

questions = [
    {
        "question": "What is your age?",
        "description": "Understanding your age allows us to estimate how long your investments can grow before you begin using them. It's a foundation for deciding how much risk your portfolio can reasonably absorb. The longer your time horizon, the more flexibility we may have in seeking long-term returns.",
        "options": ["18-24", "25-34", "35-44", "45-54", "55-65", "65+"],
        "key": "age",
        "type": "radio"
    },
    {
        "question": "What is your gender?",
        "description": "This helps us consider longevity and potential life planning needs. Gender-related factors can influence retirement timelines and financial independence. It ensures the strategy we build supports your full financial journey.",
        "options": ["Male", "Female", "Other/prefer not to say"],
        "key": "gender",
        "type": "radio"
    },
    {
        "question": "What is your current employment type?",
        "description": "Employment tells us about the stability and predictability of your income. It guides how aggressively or cautiously we should approach investing. Understanding your earning structure helps us align investments with your cash flow.",
        "options": ["Salaried", "Self-Employed", "Student", "Unemployed / Other"],
        "key": "employment",
        "type": "radio"
    },
    {
        "question": "What is your highest level of education?",
        "description": "Your education level can affect how you engage with financial tools and ideas. This helps us provide recommendations at the right depth and pace. Our goal is to match your comfort level so you feel confident moving forward.",
        "options": ["High school", "Bachelor", "Master", "Doctorate"],
        "key": "education",
        "type": "radio"
    },
    {
        "question": "What's your marital status?",
        "description": "This gives us insight into shared financial responsibilities and long-term planning. Whether you're managing finances independently or jointly, your plan needs to reflect that. We want to ensure the strategy fits your real-life relationships and goals.",
        "options": ["Single", "Married", "Divorced", "Widowed"],
        "key": "marital_status",
        "type": "radio"
    },
    {
        "question": "How many children or dependents do you have?",
        "description": "Dependents shape your financial priorities and planning timeline. They often influence how much flexibility or liquidity you need. We consider this to help ensure your investments support both present and future needs.",
        "options": None,
        "key": "dependents",
        "type": "number"
    },
    {
        "question": "What is your annual income (in euros)?",
        "description": "Your income provides a practical framework for how much you can safely invest. It allows us to shape recommendations that are financially realistic and sustainable. This question ensures your investment plan fits comfortably within your means.",
        "options": ["Less than €30,000", "€30,000–€50,000", "€50,000–€70,000", "More than €70,000"],
        "key": "income",
        "type": "radio"
    },
    {
        "question": "How often do you save money?",
        "description": "Your saving habits tell us how disciplined your financial behavior is. Consistent savers often have a stronger base for long-term investing. This helps us determine how much room you have to grow your portfolio.",
        "options": ["Weekly", "Monthly", "Never", "Rarely"],
        "key": "saving_frequency",
        "type": "radio"
    },
    {
        "question": "How often do you invest in financial products (e.g., ETFs, mutual funds, pensions)?",
        "description": "This helps us understand how familiar you are with investing environments. We tailor your experience accordingly: whether you're just getting started or already active. Our goal is to offer guidance that's effective and empowering, not overwhelming.",
        "options": ["Regularly", "Occasionally", "Never"],
        "key": "investment_frequency",
        "type": "radio"
    },
    {
        "question": "Do you have a life or health insurance?",
        "description": "Insurance adds a protective layer around your financial plan. It reduces the need to draw from investments in case of emergencies. This helps us build a plan that remains intact even when life is unpredictable.",
        "options": ["Yes", "No"],
        "key": "insurance",
        "type": "radio"
    },
    {
        "question": "Are you currently repaying a loan?",
        "description": "Debt can limit how much flexibility you have in your investment strategy. It also affects your risk tolerance, especially with tight monthly budgets. We ask this to ensure your investment plan doesn't overextend your finances.",
        "options": ["Yes", "No"],
        "key": "loan_repayment",
        "type": "radio"
    },
    {
        "question": "What is your primary financial goal?",
        "description": "Your goal is the blueprint. Everything else is built around it. Whether it's retirement, buying a home, or building wealth, we tailor your investments to that destination. Clear goals allow us to define success and measure progress meaningfully.",
        "options": ["Retirement", "Buying a house", "Education", "Travel", "General wealth building"],
        "key": "financial_goal",
        "type": "radio"
    },
    {
        "question": "When do you expect to need the money you're investing?",
        "description": "Timing is one of the most important elements in financial planning. The answer guides how aggressive or conservative your investment mix should be. Our goal is to make sure the money is available when you need it, without surprises.",
        "options": ["Less than 3 years", "3 - 10 years", "More than 10 years"],
        "key": "investment_timeline",
        "type": "radio"
    },
    {
        "question": "If your investments dropped 20% in value over a year, what would you do?",
        "description": "This reveals how you might react during difficult market conditions. We're not testing your knowledge. We're gauging emotional comfort with risk. The right plan should feel manageable, even during uncertain times.",
        "options": ["Sell everything to avoid further losses", "Hold and wait it out", "Invest more while prices are low"],
        "key": "market_reaction",
        "type": "radio"
    },
    {
        "question": "Which statement best describes your attitude toward investment risk?",
        "description": "This helps us understand how much uncertainty you're willing to accept in pursuit of returns. The right level of risk ensures your strategy supports both your goals and your peace of mind.",
        "options": ["I prefer stability over high returns", "I want a balance of safety and growth", "I'm comfortable taking risks for potentially higher returns"],
        "key": "risk_attitude",
        "type": "radio"
    },
    {
        "question": "How would you rate your knowledge of financial products like ETFs or PRSAs?",
        "description": "This helps us tailor your experience to your comfort level with investment tools. It's not about complexity, it's about clarity and confidence. Our goal is to give you just enough detail to make informed decisions without overwhelm.",
        "options": ["Very poor", "Beginner", "Intermediate", "Advanced"],
        "key": "financial_knowledge",
        "type": "radio"
    }
]

def map_user_answers_to_model_format(user_answers):
    """
    Transform user-friendly answers to the format expected by the ML model
    """
    model_data = {}
    
    # 1. AGE MAPPING
    if 'age' in user_answers:
        age_mapping = {
            "18-24": "18-24",
            "25-34": "25-34", 
            "35-44": "35-44",
            "45-54": "45-54",
            "55-65": "55-64",  # Fix this mismatch
            "65+": "65+"
        }
        model_data['age_bucket'] = age_mapping.get(user_answers['age'], user_answers['age'])
    
    # 2. INCOME MAPPING
    if 'income' in user_answers:
        income_mapping = {
            "Less than €30,000": "<30,000",
            "€30,000–€50,000": "30,000-50,000", 
            "€50,000–€70,000": "50,000-70,000",
            "More than €70,000": ">70,000"
        }
        model_data['income_bucket'] = income_mapping.get(user_answers['income'], user_answers['income'])
    
    # 3. GENDER MAPPING
    if 'gender' in user_answers:
        gender_mapping = {
            "Male": "Male",
            "Female": "Female",
            "Other/prefer not to say": "Other"
        }
        model_data['gender'] = gender_mapping.get(user_answers['gender'], user_answers['gender'])
    
    # 4. EMPLOYMENT MAPPING
    if 'employment' in user_answers:
        employment_mapping = {
            "Salaried": "Salaried",
            "Self-Employed": "Self-Employed", 
            "Student": "Student",
            "Unemployed / Other": "Unemployed"
        }
        model_data['occupation'] = employment_mapping.get(user_answers['employment'], user_answers['employment'])
    
    # 5. EDUCATION MAPPING
    if 'education' in user_answers:
        model_data['education_level'] = user_answers['education']
    
    # 6. MARITAL STATUS
    if 'marital_status' in user_answers:
        model_data['marital_status'] = user_answers['marital_status']
    
    # 7. DEPENDENTS MAPPING
    if 'dependents' in user_answers:
        model_data['number_of_dependents'] = int(user_answers['dependents'])
    
    # 8. INSURANCE MAPPING
    if 'insurance' in user_answers:
        model_data['has_insurance'] = user_answers['insurance']
    
    # 9. LOAN MAPPING
    if 'loan_repayment' in user_answers:
        model_data['has_loan'] = 1 if user_answers['loan_repayment'] == 'Yes' else 0
    
    # 10. FINANCIAL GOAL
    if 'financial_goal' in user_answers:
        model_data['financial_goal'] = user_answers['financial_goal']
    
    # 11. INVESTMENT TIMELINE MAPPING
    if 'investment_timeline' in user_answers:
        model_data['time_horizon'] = user_answers['investment_timeline']
    
    # 12. MARKET REACTION MAPPING
    if 'market_reaction' in user_answers:
        model_data['reaction_to_loss'] = user_answers['market_reaction']
    
    # 13. RISK ATTITUDE
    if 'risk_attitude' in user_answers:
        model_data['risk_attitude'] = user_answers['risk_attitude']
    
    # 14. FINANCIAL KNOWLEDGE MAPPING
    if 'financial_knowledge' in user_answers:
        model_data['financial_knowledge_level'] = user_answers['financial_knowledge']
    
    # 15. SAVING FREQUENCY
    if 'saving_frequency' in user_answers:
        model_data['saving_frequency'] = user_answers['saving_frequency']
    
    # 16. INVESTMENT FREQUENCY
    if 'investment_frequency' in user_answers:
        model_data['investment_frequency'] = user_answers['investment_frequency']
    
    # ADD MISSING FEATURES WITH DEFAULTS
    model_data['credit_score'] = 650
    model_data['job_tenure'] = 3
    model_data['loan_purpose'] = 'Personal'
    model_data['payment_history'] = 'Good'
    model_data['debt_to_income_ratio'] = 0.3
    
    return model_data

# ========================================
# APP SCREENS
# ========================================

def show_start_screen(session):
    # Move header above the columns
    st.header("Your personalized financial journey starts here")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.write("""
        Our AI uses machine learning and your inputs to recommend a risk profile that fits your goals and comfort level.
        """)
        
        # Add spacing before button
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Start the quiz", key="start_quiz", use_container_width=True):
            st.session_state.risk_page = 'quiz'
            st.session_state.current_question = 0
            #st.rerun()
    
    with col2:
        st.write("""
        This comprehensive assessment uses a trained machine learning model to understand your financial goals, 
        your comfort with risk, and how you respond to market changes. Based on your responses, we'll assign a 
        personalized risk profile and offer tailored investment recommendations.
        """)
        st.write("""
        There are no right or wrong answers, just a smarter way to invest based on you.
        """)
    
        
    col_back1, col_back2, col_back3 = st.columns([2, 1, 2])
    

def show_quiz(session):
    if st.session_state.current_question < len(questions):
        current_q = questions[st.session_state.current_question]
        
        # Progress indicator
        progress = (st.session_state.current_question + 1) / len(questions)
        st.progress(progress)
        st.write(f"Question {st.session_state.current_question + 1} of {len(questions)}")
        
        # Create two columns for question and description
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Question
            st.subheader(current_q["question"])
            
            # Handle different question types
            if current_q["type"] == "radio":
                # Radio button options
                answer = st.radio(
                    "Choose your answer:", 
                    current_q["options"], 
                    key=f"q_{st.session_state.current_question}",
                    index=None,
                    label_visibility="collapsed"
                )
            elif current_q["type"] == "number":
                # Number input for dependents
                answer = st.number_input(
                    "Enter number of dependents:",
                    min_value=0,
                    max_value=20,
                    value=0,
                    step=1,
                    key=f"q_{st.session_state.current_question}",
                    label_visibility="collapsed"
                )
                # For number input, we always have a valid answer (default 0)
                if answer is not None:
                    answer = str(answer)  # Convert to string for consistency
        
        with col2:
            # Description on the right side
            st.subheader("Why am I being asked this question?")
            st.write(current_q["description"])
        
        # Add spacing before navigation buttons
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation buttons with better spacing
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1.5, 1.5, 3, 1.5])
        
        with nav_col1:
            if st.session_state.current_question > 0:
                if st.button("← Previous", use_container_width=True):
                    st.session_state.current_question -= 1
                    #st.rerun()
        
        with nav_col2:
            # For number input, answer is always valid; for radio, check if selection is made
            is_answer_valid = (current_q["type"] == "number") or (current_q["type"] == "radio" and answer is not None)
            
            if st.button("Next →", disabled=not is_answer_valid, use_container_width=True):
                # Store the answer
                st.session_state.answers[current_q["key"]] = answer
                if st.session_state.current_question + 1 >= len(questions):
                    # Quiz completed - process results
                    process_results()
                    st.session_state.risk_page = 'results'
                else:
                    st.session_state.current_question += 1
                #st.rerun()
        
        

def process_results():
    """Process the quiz results using backend mapping"""
    try:
        # Transform user answers to model format
        model_ready_data = map_user_answers_to_model_format(st.session_state.answers)
        
        # Create DataFrame with exact features model expects
        model_features = [
            'age_bucket', 'income_bucket', 'gender', 'occupation', 'education_level',
            'marital_status', 'has_loan', 'credit_score', 'job_tenure', 'number_of_dependents',
            'loan_purpose', 'payment_history', 'debt_to_income_ratio', 'reaction_to_loss',
            'financial_knowledge_level', 'saving_frequency', 'investment_frequency',
            'has_insurance', 'financial_goal', 'time_horizon'
        ]
        
        # Create input data
        input_data = {}
        for feature in model_features:
            input_data[feature] = [model_ready_data.get(feature, 0)]
        
        df_input = pd.DataFrame(input_data)
        
        # Load model and predict
        with open("final_pipeline_trained_on_real_data_knn.pkl", "rb") as f:
            pipeline = pickle.load(f)
        
        prediction_num = pipeline.predict(df_input)[0]
        probabilities = pipeline.predict_proba(df_input)[0]
        confidence = probabilities.max()
        
        # Check if model has 2 or 3 classes
        if len(probabilities) == 2:
            # Binary classification: 0 = Conservative, 1 = Opportunistic
            risk_mapping = {0: "Conservative Investor", 1: "Opportunistic Investor"}
        else:
            # Multi-class: 0 = Conservative, 1 = Moderate, 2 = Opportunistic  
            risk_mapping = {0: "Conservative Investor", 1: "Moderate Investor", 2: "Opportunistic Investor"}
        
        prediction_text = risk_mapping.get(prediction_num, "Conservative Investor")
        
        st.session_state.risk_profile = prediction_text
        st.session_state.model_confidence = confidence
        
    except FileNotFoundError:
        st.error("❌ Model file not found!")
        st.session_state.risk_profile = "Conservative Investor"
        st.session_state.model_confidence = 0.5
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.session_state.risk_profile = "Conservative Investor"
        st.session_state.model_confidence = 0.5

def show_results(session):
    risk_profile = st.session_state.risk_profile
    confidence = st.session_state.model_confidence

    st.title("Your Risk Profile Assessment is ready")
    st.markdown(f"Your predicted risk profile: **{risk_profile}**")

    # Description
    if "Conservative" in risk_profile:
        description = "You prefer stable, conservative investments with lower returns and minimal risk. Consider options like bonds and high-yield savings."
    elif "Moderate" in risk_profile:
        description = "You're comfortable with moderate risk for potentially higher returns. A balanced mix of stocks and bonds would suit your profile."
    else:
        description = "You're open to higher risks in pursuit of higher rewards. Growth-focused portfolios and stocks may align with your goals."

    st.write(description)

    # Add spacing before buttons
    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation buttons with proper spacing and styling
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        if st.button("🔄 Retake Quiz", key="retake_quiz", use_container_width=True):
            st.session_state.risk_page = 'start'
            st.session_state.current_question = 0
            st.session_state.answers = {}
            #st.rerun()
    
    

    # Add spacing after buttons
    st.markdown("<br>", unsafe_allow_html=True)

    # Show reasoning behind the prediction
    with st.expander("Why was this profile assigned?"):
        st.write("The machine learning model considered these key factors:")
        
        key_factors = [
            ('Age', 'age'),
            ('Investment Timeline', 'investment_timeline'),
            ('Risk Attitude', 'risk_attitude'),
            ('Market Reaction', 'market_reaction'),
            ('Financial Goal', 'financial_goal'),
            ('Income Level', 'income'),
            ('Investment Experience', 'investment_frequency')
        ]
        
        for display_name, key in key_factors:
            if key in st.session_state.answers:
                st.write(f"• **{display_name}**: {st.session_state.answers[key]}")

# ========================================
# MAIN APP LOGIC
# ========================================

def run(session):
    """Main entry point for the risk assessment module"""
    
    # Initialize risk-specific session state
    initialize_risk_session_state()
    
    # Route to appropriate screen based on risk_page state
    if st.session_state.risk_page == 'start':
        show_start_screen(session)
    elif st.session_state.risk_page == 'quiz':
        show_quiz(session)
    elif st.session_state.risk_page == 'results':
        show_results(session)