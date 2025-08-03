import streamlit as st
import random
import os
import pickle
import pandas as pd
import numpy as np
from openai import AzureOpenAI
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')

# REMOVED st.set_page_config() - this is handled by main.py
# MOVED all st.markdown() calls to a function to avoid executing at import time

def apply_custom_styles():
    """Apply minimal custom CSS styles - let Streamlit handle the theme"""
    st.markdown("""
    <style>
        /* Only custom button styling - let Streamlit handle text colors */
        .stButton > button {
            background-color: #4169E1;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 0.5rem;
            cursor: pointer;
        }
        
        .stButton > button:hover {
            background-color: #36379C;
        }
    </style>
    """, unsafe_allow_html=True)

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
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'model_confidence' not in st.session_state:
        st.session_state.model_confidence = 0.0

# ========================================
# AZURE OPENAI CONFIGURATION
# ========================================

def init_azure_client():
    endpoint = "https://anju-mcrequpq-eastus2.cognitiveservices.azure.com/"
    deployment = "gpt-35-turbo_anju"
    subscription_key = os.getenv("AZURE_AI_KEY") # Your API key
    api_version = "2024-12-01-preview"
    
    try:
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )
        return client, deployment
    except Exception as e:
        st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        return None, None

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
        "description": "This helps us understand how familiar you are with investing environments. We tailor your experience accordingly — whether you're just getting started or already active. Our goal is to offer guidance that's effective and empowering, not overwhelming.",
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
        "description": "Your goal is the blueprint — everything else is built around it. Whether it's retirement, buying a home, or building wealth, we tailor your investments to that destination. Clear goals allow us to define success and measure progress meaningfully.",
        "options": ["Retirement", "Buying a house", "Education", "Travel", "General wealth building"],
        "key": "financial_goal",
        "type": "radio"
    },
    {
        "question": "When do you expect to need the money you're investing?",
        "description": "Timing is one of the most important elements in financial planning. The answer guides how aggressive or conservative your investment mix should be. Our goal is to make sure the money is available when you need it — without surprises.",
        "options": ["Less than 3 years", "3 - 10 years", "More than 10 years"],
        "key": "investment_timeline",
        "type": "radio"
    },
    {
        "question": "If your investments dropped 20% in value over a year, what would you do?",
        "description": "This reveals how you might react during difficult market conditions. We're not testing your knowledge — we're gauging emotional comfort with risk. The right plan should feel manageable, even during uncertain times.",
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
        "description": "This helps us tailor your experience to your comfort level with investment tools. It's not about complexity — it's about clarity and confidence. Our goal is to give you just enough detail to make informed decisions without overwhelm.",
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
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("Your personalized financial journey starts here")
        
        st.write("""
        Our AI uses machine learning and your inputs to recommend a risk profile that fits your goals and comfort level.
        """)
        
        if st.button("Start the quiz", key="start_quiz"):
            st.session_state.risk_page = 'quiz'
            st.session_state.current_question = 0
            st.rerun()
    
    with col2:
        st.write("""
        This comprehensive assessment uses a trained machine learning model to understand your financial goals, 
        your comfort with risk, and how you respond to market changes. Based on your responses, we'll assign a 
        personalized risk profile and offer tailored investment recommendations.
        """)
        st.write("""
        There are no right or wrong answers, just a smarter way to invest based on you.
        """)
    
    # Back to home button
    st.markdown("---")
    if st.button("← Back to Home", key="back_to_home_start"):
        session.page = "landing"
        st.rerun()

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
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 2, 1])
        
        with nav_col1:
            if st.session_state.current_question > 0:
                if st.button("← Previous"):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with nav_col2:
            # For number input, answer is always valid; for radio, check if selection is made
            is_answer_valid = (current_q["type"] == "number") or (current_q["type"] == "radio" and answer is not None)
            
            if st.button("Next →", disabled=not is_answer_valid):
                # Store the answer
                st.session_state.answers[current_q["key"]] = answer
                if st.session_state.current_question + 1 >= len(questions):
                    # Quiz completed - process results
                    process_results()
                    st.session_state.risk_page = 'results'
                else:
                    st.session_state.current_question += 1
                st.rerun()
        
        with nav_col4:
            if st.button("← Back to Home", key="back_to_home_quiz"):
                session.page = "landing"
                st.rerun()

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
        
        # DEBUG: Let's see what the model actually outputs
        st.write("🔍 **Model Debug Information:**")
        st.write(f"**Prediction number:** {prediction_num}")
        st.write(f"**Prediction type:** {type(prediction_num)}")
        st.write(f"**Probabilities shape:** {probabilities.shape}")
        st.write(f"**Probabilities:** {probabilities}")
        st.write(f"**Number of classes:** {len(probabilities)}")
        
        # Check if model has 2 or 3 classes
        if len(probabilities) == 2:
            # Binary classification: 0 = Conservative, 1 = Opportunistic
            risk_mapping = {0: "Conservative Investor", 1: "Opportunistic Investor"}
            st.write("**Model type:** Binary classification (2 classes)")
        else:
            # Multi-class: 0 = Conservative, 1 = Moderate, 2 = Opportunistic  
            risk_mapping = {0: "Conservative Investor", 1: "Moderate Investor", 2: "Opportunistic Investor"}
            st.write("**Model type:** Multi-class classification (3+ classes)")
        
        prediction_text = risk_mapping.get(prediction_num, "Conservative Investor")
        
        st.session_state.risk_profile = prediction_text
        st.session_state.model_confidence = confidence
        
        st.write(f"**Final prediction:** {prediction_text}")
        
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

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💬 Chat with AI Assistant", key="goto_chatbot"):
            st.session_state.risk_page = 'chatbot'
            st.rerun()
    
    with col2:
        if st.button("🔄 Retake Quiz", key="retake_quiz"):
            st.session_state.risk_page = 'start'
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.chat_messages = []
            st.rerun()
    
    with col3:
        if st.button("← Back to Home", key="back_to_home_results"):
            session.page = "landing"
            st.rerun()

    # Optional: Show reasoning behind the prediction
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

def show_chatbot(session):
    """Complete chatbot implementation with Azure OpenAI"""
    # Initialize Azure client
    client, deployment = init_azure_client()
    
    if client is None or deployment is None:
        st.error("❌ Please configure your Azure OpenAI API key in the code.")
        st.info("💡 The API key is already configured in this version.")
        if st.button("← Back to Results"):
            st.session_state.risk_page = 'results'
            st.rerun()
        return
    
    st.title("💰 Your Personal Financial Assistant")
    
    # Show personalized greeting
    confidence_emoji = "🟢" if st.session_state.model_confidence >= 0.7 else "🟡" if st.session_state.model_confidence >= 0.4 else "🔴"
    st.write(f"""
    Based on your **{st.session_state.risk_profile}** profile {confidence_emoji} 
    (predicted with {st.session_state.model_confidence:.1%} confidence), I'm here to provide 
    personalized financial advice tailored to your specific situation.
    """)
    
    # Display user profile summary in sidebar
    with st.sidebar:
        st.header("📊 Your Profile")
        st.markdown(f"**Risk Profile:** {st.session_state.risk_profile}")
        st.markdown(f"**ML Confidence:** {st.session_state.model_confidence:.1%}")
        
        if 'financial_goal' in st.session_state.answers:
            st.markdown(f"**Goal:** {st.session_state.answers['financial_goal']}")
        if 'investment_timeline' in st.session_state.answers:
            st.markdown(f"**Timeline:** {st.session_state.answers['investment_timeline']}")
        if 'income' in st.session_state.answers:
            st.markdown(f"**Income:** {st.session_state.answers['income']}")
        if 'age' in st.session_state.answers:
            st.markdown(f"**Age:** {st.session_state.answers['age']}")
        
        st.markdown("---")
        
        # Quick action buttons
        st.header("💡 Quick Questions")
        quick_questions = [
            "What investments match my risk profile?",
            "How much should I save monthly?",
            "Should I start investing now?",
            "How to build an emergency fund?",
            "Best retirement planning strategy?",
            "Should I pay off debt first?",
            "Explain my risk assessment",
            "Investment portfolio suggestions"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{hash(question)}"):
                st.session_state.chat_messages.append({"role": "user", "content": question})
                st.rerun()
        
        st.markdown("---")
        
        # Clear chat and navigation
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()
            
        if st.button("← Back to Results"):
            st.session_state.risk_page = 'results'
            st.rerun()
    
    # Add main navigation buttons
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← Back to Results", key="back_to_results_main"):
            st.session_state.risk_page = 'results'
            st.rerun()
    
    with col3:
        if st.button("← Back to Home", key="back_to_home_chatbot"):
            session.page = "landing"
            st.rerun()
    
    # Initialize chat with welcome message if empty
    if not st.session_state.chat_messages:
        goal = st.session_state.answers.get('financial_goal', 'financial planning')
        welcome_msg = f"""Hello! I'm your personal financial assistant powered by AI. 

Based on our ML analysis, you have a **{st.session_state.risk_profile}** profile with {st.session_state.model_confidence:.1%} confidence. I understand your goal is **{goal}** and I'm here to provide tailored advice.

What would you like to know about your finances? I can help with:
• Investment strategies matching your risk profile
• Budgeting and saving tips
• Retirement planning
• Portfolio recommendations
• Market insights

Ask me anything! 💭"""
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about investments, budgeting, planning..."):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Analyzing your question..."):
                try:
                    # Create system prompt with user profile
                    system_prompt = create_personalized_system_prompt()
                    
                    # Prepare messages for API call
                    api_messages = [{"role": "system", "content": system_prompt}]
                    
                    # Add recent conversation history (last 8 messages to avoid token limits)
                    recent_messages = st.session_state.chat_messages[-8:]
                    for msg in recent_messages:
                        if msg["role"] != "system":  # Don't include system messages
                            api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Make API call to Azure OpenAI
                    response = client.chat.completions.create(
                        messages=api_messages,
                        max_tokens=800,
                        temperature=0.7,
                        top_p=0.9,
                        model=deployment
                    )
                    
                    # Get and display response
                    assistant_response = response.choices[0].message.content
                    st.markdown(assistant_response)
                    
                    # Add to chat history
                    st.session_state.chat_messages.append({"role": "assistant", "content": assistant_response})
                    
                except Exception as e:
                    st.error(f"❌ Error connecting to AI assistant: {str(e)}")
                    st.info("💡 Please check your API configuration.")
                    
                    # Provide a fallback response with updated risk profile names
                    fallback_response = f"""I apologize, but I'm having trouble connecting to the AI service right now. 
                    
However, based on your **{st.session_state.risk_profile}** profile, here are some general recommendations:

**For {st.session_state.risk_profile} investors:**
{"• Focus on stable investments like bonds and savings accounts" if "Conservative" in st.session_state.risk_profile else "• Consider a balanced mix of stocks and bonds" if "Moderate" in st.session_state.risk_profile else "• Growth stocks and aggressive portfolios may suit your tolerance"}
• Diversify your investments across different asset classes
• Consider your {st.session_state.answers.get('investment_timeline', 'investment timeline')}
• Start with small amounts if you're new to investing

Please try your question again, or contact support if the issue persists."""
                    
                    st.markdown(fallback_response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": fallback_response})

def create_personalized_system_prompt():
    """Create a personalized system prompt based on user's questionnaire answers and ML prediction"""
    
    # Base system prompt
    base_prompt = f"""You are a knowledgeable and personalized financial advisor assistant. You provide helpful, accurate, and tailored financial advice based on the user's specific profile and ML-predicted risk assessment.

IMPORTANT: This user has been assessed using a machine learning model with {st.session_state.model_confidence:.1%} confidence as having a {st.session_state.risk_profile} profile."""
    
    # Add user profile information
    profile_info = f"\n\nUSER PROFILE:\n- Risk Profile: {st.session_state.risk_profile} (ML Confidence: {st.session_state.model_confidence:.1%})"
    
    key_answers = {
        'age': 'Age',
        'financial_goal': 'Primary Financial Goal',
        'investment_timeline': 'Investment Timeline',
        'income': 'Annual Income',
        'marital_status': 'Marital Status',
        'dependents': 'Number of Dependents',
        'employment': 'Employment Type',
        'saving_frequency': 'Saving Frequency',
        'investment_frequency': 'Investment Experience',
        'insurance': 'Insurance Coverage',
        'loan_repayment': 'Current Loans',
        'market_reaction': 'Market Volatility Response',
        'risk_attitude': 'Risk Attitude',
        'financial_knowledge': 'Financial Knowledge Level'
    }
    
    for key, label in key_answers.items():
        if key in st.session_state.answers and st.session_state.answers[key]:
            profile_info += f"\n- {label}: {st.session_state.answers[key]}"
    
    # Add specific guidance based on risk profile with updated names
    risk_guidance = ""
    if "Conservative" in st.session_state.risk_profile:
        risk_guidance = "\n\nFOCUS AREAS: Conservative investment strategies, capital preservation, bonds, high-yield savings accounts, CDs, stable value funds, and dividend-paying stocks. Emphasize safety over returns and explain the importance of emergency funds."
    elif "Moderate" in st.session_state.risk_profile:
        risk_guidance = "\n\nFOCUS AREAS: Balanced portfolios with 60/40 or 70/30 stock-to-bond ratios, diversified index funds, target-date funds, and moderate growth strategies. Balance risk and return while explaining diversification benefits."
    else:
        risk_guidance = "\n\nFOCUS AREAS: Growth investments, aggressive portfolios (80/20 or 90/10 stock-to-bond), individual growth stocks, sector ETFs, international markets, and emerging markets. Discuss higher-risk/higher-reward strategies while emphasizing the importance of diversification."
    
    # Add behavioral guidance based on answers
    behavioral_guidance = ""
    if 'financial_knowledge' in st.session_state.answers:
        knowledge_level = st.session_state.answers['financial_knowledge'].lower()
        if 'poor' in knowledge_level or 'beginner' in knowledge_level:
            behavioral_guidance += "\n\nCOMMUNICATION STYLE: The user is new to investing. Explain concepts clearly, avoid jargon, provide simple examples, and build up complexity gradually. Always explain financial terms."
        elif 'advanced' in knowledge_level:
            behavioral_guidance += "\n\nCOMMUNICATION STYLE: The user has advanced financial knowledge. You can discuss complex strategies, technical analysis, specific ratios, and detailed investment mechanics."
        else:
            behavioral_guidance += "\n\nCOMMUNICATION STYLE: The user has intermediate knowledge. Balance technical details with clear explanations."
    
    # Add timeline-specific guidance
    timeline_guidance = ""
    if 'investment_timeline' in st.session_state.answers:
        timeline = st.session_state.answers['investment_timeline']
        if 'Less than 3 years' in timeline:
            timeline_guidance = "\n\nTIMELINE CONSIDERATION: Short-term timeline requires liquid, low-risk investments. Focus on savings accounts, CDs, and money market funds."
        elif '3 - 10 years' in timeline:
            timeline_guidance = "\n\nTIMELINE CONSIDERATION: Medium-term timeline allows for moderate risk. Suggest balanced funds and moderate portfolio allocation."
        else:
            timeline_guidance = "\n\nTIMELINE CONSIDERATION: Long-term timeline allows for higher risk tolerance. Can recommend growth-focused strategies and weather market volatility."
    
    full_prompt = base_prompt + profile_info + risk_guidance + behavioral_guidance + timeline_guidance
    
    full_prompt += f"""\n\nGUIDELINES:
- Always reference their ML-predicted {st.session_state.risk_profile} profile when making recommendations
- Provide practical, actionable advice tailored to their specific situation
- If discussing specific investments, remind them to do their own research and consider consulting a professional
- Keep responses conversational but informative (aim for 2-4 paragraphs)
- Consider their goals ({st.session_state.answers.get('financial_goal', 'financial planning')}), timeline, and risk tolerance in all recommendations
- If they ask about strategies outside their risk profile, gently explain why it might not suit them and offer alternatives
- Always mention the confidence level of their ML prediction when relevant
- Provide specific examples and numbers when possible"""
    
    return full_prompt

# ========================================
# MAIN APP LOGIC
# ========================================

def run(session):
    """Main entry point for the risk assessment module"""
    # Apply custom styles first
    apply_custom_styles()
    
    # Initialize risk-specific session state
    initialize_risk_session_state()
    
    # Route to appropriate screen based on risk_page state
    if st.session_state.risk_page == 'start':
        show_start_screen(session)
    elif st.session_state.risk_page == 'quiz':
        show_quiz(session)
    elif st.session_state.risk_page == 'results':
        show_results(session)
    elif st.session_state.risk_page == 'chatbot':
        show_chatbot(session)