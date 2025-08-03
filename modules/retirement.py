import streamlit as st
import numpy as np
import pandas as pd
import os
import plotly.graph_objs as go

def load_salary_data():
    csv_path = os.path.join("assets", "earnings_data.csv")
    df = pd.read_csv(csv_path)
    df = df.dropna()
    df['Value'] = df['Value'].astype(float)
    return df

salary_df = load_salary_data()

def get_age_group(age):
    if age < 25:
        return "15 - 24 years"
    elif age <= 29:
        return "25 - 29 years"
    elif age <= 39:
        return "30 - 39 years"
    elif age <= 49:
        return "40 - 49 years"
    elif age <= 59:
        return "50 - 59 years"
    else:
        return "60 years and over"

def next_step():
    st.session_state.rp_step += 1

def prev_step():
    st.session_state.rp_step -= 1

def button_row(show_back=True, show_next=True, submit=False):
    col1, _, col3 = st.columns([1, 6, 1])
    go_back = go_next = go_submit = False

    with col1:
        if show_back:
            go_back = st.button("← Back", key=f"back-{st.session_state.rp_step}")
    with col3:
        if submit:
            go_submit = st.button("Submit", key=f"submit-{st.session_state.rp_step}")
        elif show_next:
            go_next = st.button("Next →", key=f"next-{st.session_state.rp_step}")

    if go_back:
        prev_step()
        st.rerun()
    if go_next:
        next_step()
        st.rerun()
    if go_submit:
        next_step()
        st.rerun()

def run(session):
    fd = session.form_data

    if session.rp_step == 1:
        st.markdown("""
        <div style='font-size:30px; font-weight:700; margin-bottom:20px;color:#0068c9;font-family: Times New Roman;'>
        Let’s make sure you’re on track to enjoy the future you’re working for. Tell us a bit about yourself to get started.
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='font-size:25px; font-weight:700;'>1. What is your current age?</div>", unsafe_allow_html=True)
        fd["age"] = st.slider("", 18, 60, 30, 1)
        button_row(show_back=False)

    elif session.rp_step == 2:
        st.markdown("<div style='font-size:25px; font-weight:700;'>2. At what age do you plan to retire?</div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:15px; font-weight:700; font-family: Times New Roman; margin-bottom: 20px;'>
        (According to the CSO, 68% of workers expect to retire between the ages of 60 and 69. Feel free to adjust the slider to match your plans.)
        </div>""", unsafe_allow_html=True)
        fd["retirement_age"] = st.slider("", 60, 75, 65, 1)
        button_row()

    elif session.rp_step == 3:
        st.markdown("<div style='font-size:25px; font-weight:700;'>3. What is your annual income (€)?</div>", unsafe_allow_html=True)
        fd["income"] = st.slider("", 25, 500, 60, 1, format="€%dK") * 1000
        button_row()

    elif session.rp_step == 4:
        st.markdown("<div style='font-size:25px; font-weight:700;'>4. What is the current value of your existing pension pot?</div>", unsafe_allow_html=True)
        fd["pension_pot"] = st.slider("", 0, 500, 0, 5, format="€%dK") * 1000
        button_row()

    elif session.rp_step == 5:
        st.markdown("<div style='font-size:25px; font-weight:700;'>5. What % of your salary do you contribute to pension?</div>", unsafe_allow_html=True)
        fd["contribution"] = st.slider("", 0, 40, 15, 1, format="%d%%")
        button_row()

    elif session.rp_step == 6:
        st.markdown("<div style='font-size:25px; font-weight:700;'>6. What sector do you work in?</div>", unsafe_allow_html=True)
        sectors = salary_df["NACE Sector"].dropna().unique().tolist()
        fd["sector"] = st.selectbox("Choose your sector", sectors)
        button_row()

    elif session.rp_step == 7:
        st.markdown("<div style='font-size:25px; font-weight:700;'>7. What is your target monthly retirement income?</div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:15px; font-weight:700; font-family: Times New Roman; margin-bottom: 20px;'>
        (Many aim for around 40% of their current income. OECD reports Ireland’s average net pension replacement rate is 36%–40%.)
        </div>""", unsafe_allow_html=True)
        fd["target_income"] = int(st.slider("", 1.2, 5.0, 2.0, 0.1, format="€%.1fK") * 1000)
        button_row(submit=True)

    elif session.rp_step == 8:
        st.header("Simulation Result")

        # Inputs
        age = fd["age"]
        retirement_age = fd["retirement_age"]
        years = retirement_age - age
        income = fd["income"]
        balance = fd["pension_pot"]
        contribution_rate = fd["contribution"] / 100
        sector = fd["sector"]
        target_income = fd["target_income"]
        runs = 1000

        # --- MODIFIED: Realistic Investment Assumptions ---
        # Using a Balanced Portfolio as a more realistic baseline
        allocation = {
            "equity": 0.50,
            "bonds": 0.40,
            "cash": 0.10
        }
        returns = {
            "equity": (0.1, 0.15),
            "bonds": (0.05, 0.05),
            "cash": (0.02, 0.01)
        }
        
        inflation = 0.02
        state_pension = 13800
        state_pension_growth = 0.0433
        state_projected_pension = state_pension * ((1 + state_pension_growth) ** years)

        age_group = get_age_group(age)
        salary_data = salary_df[(salary_df["NACE Sector"] == sector) & (salary_df["Age Group"] == age_group)]

        avg_growth = 0.025
        if not salary_data.empty:
            values = salary_data.sort_values("Year")["Value"].values
            if len(values) > 1:
                growth_rates = np.diff(values) / values[:-1]
                avg_growth = np.mean(growth_rates)

        results_real = []
        yearly_balances = np.zeros((runs, years + 1))
        yearly_incomes = np.zeros((runs, years + 1))

        for run in range(runs):
            curr_income = income
            curr_balance = balance
            cumulative_inflation = 1.0
            
            yearly_balances[run, 0] = curr_balance
            yearly_incomes[run, 0] = 0
            
            for year in range(years):
                
                roi = sum([
                    np.random.normal(returns[asset][0], returns[asset][1]) * allocation[asset]
                    for asset in allocation
                ])
                
                curr_income *= (1 + avg_growth)
                contribution = contribution_rate * curr_income
                curr_balance = (curr_balance + contribution) * (1 + roi)
                cumulative_inflation *= (1 + inflation)
                yearly_balances[run, year + 1] = curr_balance / cumulative_inflation
                state_pension_age = 66
                if retirement_age >= state_pension_age:
                     yearly_incomes[run, year + 1] = (
                     (curr_balance / cumulative_inflation) * 0.04 +
                     (state_projected_pension / cumulative_inflation if year + 1 == years else 0)
                 )
                else:
                     yearly_incomes[run, year + 1] = (curr_balance / cumulative_inflation) * 0.04
            final_real = curr_balance / cumulative_inflation
            withdrawal_income = final_real * 0.04
            total_income = withdrawal_income + (state_projected_pension / cumulative_inflation)
            results_real.append(total_income)
                                                 
        mean_balances = yearly_balances.mean(axis=0)
        mean_incomes = yearly_incomes.mean(axis=0)
        years_axis = np.arange(age, retirement_age + 1)

        target_annual_income = target_income * 12
        success_rate = np.mean(np.array(results_real) >= target_annual_income)

        required_total = target_annual_income / 0.04
        months = years * 12
        required_monthly_saving = required_total / months
        expected_monthly_income = np.mean(results_real) / 12

        st.info(
            f"At Retirement (age {retirement_age}), your total retirement savings is: **€{mean_balances[-1]:,.0f}**"
            )

        # ----------- Year-on-Year Graph -----------
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years_axis,
            y=mean_balances,
            mode='lines+markers',
            name='Pension Pot (€)',
            line=dict(width=3)
        ))
        fig.add_trace(go.Scatter(
            x=years_axis,
            y=mean_incomes,
            mode='lines+markers',
            name='Annual Retirement Income (€)',
            line=dict(width=3)
        ))

        fig.update_layout(
            title='Year-on-Year Pension Projection',
            xaxis_title='Age',
            yaxis_title='Value (€)',
            legend=dict(yanchor="top",y=0.99, xanchor="left", x=0.01),
            margin=dict(l=30, r=30, t=50, b=30)
        )
        custom_info = """
        <div style='
        background-color: #e6f2ff;
        padding: 18px 16px;
        border-left: 6px solid #267ddb;
        border-radius: 10px;
        font-size: 15px;
        width: 260px;
        min-height: 120px;
        margin-bottom: 16px;
        '>
        <strong>Pension Pot:</strong><br>
        The pension pot is calculated each year by adding your annual contributions to the pot, growing the total by investment returns, and adjusting for inflation.
        </div>
        """  

        custom_info_income = """
        <div style='
        background-color: #e6f2ff;
        padding: 18px 16px;
        border-left: 6px solid #267ddb;
        border-radius: 10px;
        font-size: 15px;
        width: 260px;
        min-height: 100px;
        margin-bottom: 16px;
        '>
        <strong>Annual Retirement Income:</strong><br>
        This is estimated as 4% of your pension pot at retirement, plus your state pension. It’s how much you could withdraw each year to help your savings last throughout retirement.
        </div>
        """

        col1, col2 = st.columns([3, 1])
        with col1:
          st.plotly_chart(fig, use_container_width=True)

        with col2:
          st.markdown(custom_info, unsafe_allow_html=True)
          st.markdown(custom_info_income, unsafe_allow_html=True)

        st.button("← Start Over", on_click=lambda: run_reset())

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Discover how different equity allocations affect your chances of reaching your retirement goals"):
          st.session_state.page = "portfolio"
          st.rerun()

def run_reset():
    st.session_state.page = "landing"
    st.session_state.rp_step = 1
    st.session_state.form_data = {}