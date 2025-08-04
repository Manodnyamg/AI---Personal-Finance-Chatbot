import streamlit as st
import streamlit.components.v1 as components
from openai import AzureOpenAI
import os

def init_azure_client():
    """Initialize Azure OpenAI client"""
    endpoint = "https://anju-mcrequpq-eastus2.cognitiveservices.azure.com/"
    deployment = "gpt-35-turbo_anju"
    subscription_key = os.getenv("AZURE_AI_KEY") 
    api_version = "2024-12-01-preview"
    
    try:
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )
        return client, deployment
    except Exception as e:
        return None, None

def create_system_prompt():
    """Create system prompt based on user profile from ALL sections"""
    base_prompt = """You are a knowledgeable financial advisor assistant for Wealth Wisperer app. 
    Provide helpful, accurate financial advice. Keep responses conversational and under 3 paragraphs.
    
    You help with: investment strategies, retirement planning, budgeting, ETFs, portfolio advice.
    Always remind users to consult qualified advisors for personalized advice."""
    
    # Collect user profile from multiple sources
    profile_sections = []
    
    # 1. RISK PROFILE DATA
    if hasattr(st.session_state, 'risk_profile') and st.session_state.risk_profile:
        profile_sections.append(f"Risk Profile: {st.session_state.risk_profile}")
        
        if hasattr(st.session_state, 'model_confidence'):
            confidence = getattr(st.session_state, 'model_confidence', 0)
            profile_sections.append(f"ML Confidence: {confidence:.1%}")
    
    # 2. COMPREHENSIVE RISK QUIZ ANSWERS
    if hasattr(st.session_state, 'answers') and st.session_state.answers:
        risk_data = []
        key_mapping = {
            'age': 'Age', 'financial_goal': 'Primary Goal', 'investment_timeline': 'Timeline', 
            'income': 'Income Level', 'risk_attitude': 'Risk Attitude', 'employment': 'Employment',
            'marital_status': 'Marital Status', 'dependents': 'Dependents', 'insurance': 'Insurance',
            'financial_knowledge': 'Financial Knowledge', 'saving_frequency': 'Saving Frequency',
            'investment_frequency': 'Investment Experience', 'loan_repayment': 'Has Loans',
            'market_reaction': 'Market Volatility Response', 'gender': 'Gender', 'education': 'Education'
        }
        
        for key, label in key_mapping.items():
            if key in st.session_state.answers:
                risk_data.append(f"{label}: {st.session_state.answers[key]}")
        
        if risk_data:
            profile_sections.append("Risk Assessment: " + ", ".join(risk_data))
    
    # 3. RETIREMENT PLANNING DATA
    if hasattr(st.session_state, 'form_data') and st.session_state.form_data:
        retirement_data = []
        fd = st.session_state.form_data
        
        # Key retirement planning metrics
        if 'age' in fd:
            retirement_data.append(f"Current Age: {fd['age']}")
        if 'retirement_age' in fd:
            retirement_data.append(f"Planned Retirement Age: {fd['retirement_age']}")
            if 'age' in fd:
                years_to_retire = fd['retirement_age'] - fd['age']
                retirement_data.append(f"Years to Retirement: {years_to_retire}")
        if 'income' in fd:
            retirement_data.append(f"Annual Income: €{fd['income']:,}")
        if 'pension_balance' in fd or 'pension_pot' in fd:
            balance = fd.get('pension_balance', fd.get('pension_pot', 0))
            retirement_data.append(f"Current Pension Balance: €{balance:,}")
        if 'contribution' in fd:
            retirement_data.append(f"Pension Contribution Rate: {fd['contribution']}%")
            if 'income' in fd:
                monthly_contrib = (fd['income'] * fd['contribution'] / 100) / 12
                retirement_data.append(f"Monthly Contribution: €{monthly_contrib:,.0f}")
        if 'target_income' in fd or 'monthly_goal' in fd:
            target = fd.get('target_income', fd.get('monthly_goal', 0))
            retirement_data.append(f"Target Retirement Income: €{target:,}/month")
        if 'sector' in fd:
            retirement_data.append(f"Work Sector: {fd['sector']}")
        
        if retirement_data:
            profile_sections.append("Retirement Planning: " + ", ".join(retirement_data))
    
    # 4. PORTFOLIO ALLOCATION DATA
    portfolio_data = []
    if hasattr(st.session_state, 'equity_slider'):
        equity = getattr(st.session_state, 'equity_slider', 0)
        bonds = getattr(st.session_state, 'bond_slider', 0)
        cash = getattr(st.session_state, 'cash_slider', 0)
        if equity or bonds or cash:
            portfolio_data.append(f"Portfolio Allocation: {equity}% Equities, {bonds}% Bonds, {cash}% Cash")
    
    if hasattr(st.session_state, 'last_preset'):
        preset = getattr(st.session_state, 'last_preset', None)
        if preset:
            portfolio_data.append(f"Investment Strategy: {preset}")
    
    if portfolio_data:
        profile_sections.append("Portfolio Configuration: " + ", ".join(portfolio_data))
    
    # 5. APP USAGE CONTEXT
    additional_data = []
    
    # Check retirement planning progress
    if hasattr(st.session_state, 'rp_step'):
        step = getattr(st.session_state, 'rp_step', 0)
        if step >= 8:
            additional_data.append("Completed Retirement Planning")
        elif step > 1:
            additional_data.append(f"Partially Completed Retirement Planning (Step {step}/8)")
    
    # Check current page context
    if hasattr(st.session_state, 'page'):
        current_page = getattr(st.session_state, 'page', 'landing')
        additional_data.append(f"Currently on: {current_page.title()} page")
    
    if additional_data:
        profile_sections.append("App Usage: " + ", ".join(additional_data))
    
    # Add all collected profile data to system prompt
    if profile_sections:
        base_prompt += f"\n\nCOMPREHENSIVE USER PROFILE:\n" + "\n".join([f"• {section}" for section in profile_sections])
        base_prompt += f"\n\nIMPORTANT: Use this detailed profile information to provide highly personalized advice. Reference specific details from their financial situation, risk profile, and planning data when relevant."
    else:
        base_prompt += f"\n\nNote: User hasn't completed detailed profiling yet. Encourage them to complete the Risk Assessment and Retirement Planning sections for more personalized advice."
    
    return base_prompt

def get_ai_response(user_message):
    """Get response from Azure OpenAI"""
    client, deployment = init_azure_client()
    
    if not client:
        return "Sorry, I'm having trouble connecting. Please try again or contact support."
    
    try:
        system_prompt = create_system_prompt()
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history (last 6 messages)
        if 'chat_messages' in st.session_state:
            recent_messages = st.session_state.chat_messages[-6:]
            for msg in recent_messages:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Call Azure OpenAI
        response = client.chat.completions.create(
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            model=deployment
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I'm experiencing technical difficulties. Please try again. Error: {str(e)[:100]}..."

def render_popup_chatbot():
    """Main function to render floating chatbot with sidebar popup"""
    
    # Initialize session state
    if 'chatbot_open' not in st.session_state:
        st.session_state.chatbot_open = False
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_initialized' not in st.session_state:
        st.session_state.chat_initialized = False
    if 'message_counter' not in st.session_state:
        st.session_state.message_counter = 0
    
    # Initialize welcome message
    if not st.session_state.chat_initialized:
        risk_profile = getattr(st.session_state, 'risk_profile', None)
        if risk_profile:
            welcome = f"👋 Hello! I'm your AI assistant. I see you have a **{risk_profile}** profile. How can I help with your finances today?"
        else:
            welcome = "👋 Welcome to Wealth Wisperer! I'm your AI financial assistant. I can help with investments, retirement planning, budgeting, and more. What would you like to know?"
        
        st.session_state.chat_messages = [{"role": "assistant", "content": welcome}]
        st.session_state.chat_initialized = True
    
    # Floating button with proper styling
    chatbot_html = """
    <style>
    .chatbot-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4CAF50, #45a049);
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        transition: all 0.3s ease;
        animation: pulse 2s infinite;
    }
    
    .chatbot-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        animation: none;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    
    @media (max-width: 768px) {
        .chatbot-button {
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            font-size: 20px;
        }
    }
    </style>
    
    <div class="chatbot-button" onclick="toggleChat()" title="Chat Bot">
        💬
    </div>
    
    <script>
    function toggleChat() {
        const hiddenBtn = parent.document.querySelector('button[data-testid="stButton-chat_toggle_hidden"]');
        if (hiddenBtn) {
            hiddenBtn.click();
        }
    }
    </script>
    """
    
    # Render the chatbot HTML
    components.html(chatbot_html, height=0)
    
    # Hidden button for state management
    if st.button("Ask SAM", key="chat_toggle_hidden", help="Ask Anything – SAM is Here to Help"):
        st.session_state.chatbot_open = not st.session_state.chatbot_open
        st.rerun()
    
    # Hide the toggle button completely
    st.markdown("""
    <style>
    [data-testid="stButton"][key="chat_toggle_hidden"] { 
        display: none !important; 
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show chat interface in SIDEBAR when open
    if st.session_state.chatbot_open:
        show_chat_sidebar()

def show_chat_sidebar():
    """Display chat interface in the LEFT SIDEBAR"""
    
    # Use SIDEBAR for chat interface
    with st.sidebar:
        st.markdown("### 💬 Chatbot Assistant")
        
        # Display chat messages with better styling
        st.markdown("""
        <style>
        .sidebar .element-container {
            margin-bottom: 10px;
        }
        .user-message {
            background-color: #007bff;
            color: white;
            padding: 8px 12px;
            border-radius: 15px;
            margin: 5px 0;
            text-align: right;
        }
        .assistant-message {
            background-color: #f8f9fa;
            color: #333;
            padding: 8px 12px;
            border-radius: 15px;
            margin: 5px 0;
            border: 1px solid #dee2e6;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        if st.session_state.chat_messages:
            st.markdown("**Conversation:**")
            
            # Display messages
            for i, msg in enumerate(st.session_state.chat_messages):
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <strong>Assistant:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Chat input with form for Enter key support
        st.markdown("**Ask me anything:**")
        
        with st.form(key=f"chat_form_{st.session_state.message_counter}", clear_on_submit=True):
            user_input = st.text_input(
                "Type your message...", 
                placeholder="Ask about investments, retirement, budgeting...",
                label_visibility="collapsed",
                key=f"chat_input_{st.session_state.message_counter}"
            )
            
            # Two buttons: Send and Clear
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Send", use_container_width=True)
            with col2:
                clear_clicked = st.form_submit_button("Clear", use_container_width=True)
            
            # Handle clear button - clear chat messages
            if clear_clicked:
                st.session_state.chat_messages = []
                st.session_state.chat_initialized = False
                st.session_state.message_counter += 1
                st.rerun()
            
            # Process message when form is submitted
            if submitted and user_input and user_input.strip():
                # Increment counter for unique keys
                st.session_state.message_counter += 1
                
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": user_input.strip()})
                
                # Get AI response
                with st.spinner("🤔 Thinking..."):
                    response = get_ai_response(user_input.strip())
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                
                # Rerun to update the chat

                st.rerun()
