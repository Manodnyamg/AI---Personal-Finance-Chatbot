import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
import os

# --- Data Loading and Helper Functions ---
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

def simulate_portfolio_with_deemed_disposal(
    monthly_contribution,
    years,
    asset_type,
    pension_balance
):
    """
    Simulates portfolio growth over time with an 8-year deemed disposal tax event.
    """
    if asset_type == "equities":
        annual_return = 0.10
        annual_fees = 0.002
        tax_rate = 0.41
    elif asset_type == "bonds":
        annual_return = 0.05
        annual_fees = 0.002
        tax_rate = 0.41
    elif asset_type == "cash":
        annual_return = 0.02
        annual_fees = 0.00
        tax_rate = 0.0
    else:
        raise ValueError("Invalid asset_type. Choose 'equities', 'bonds', or 'cash'.")

    months = years * 12
    monthly_return = (1 + annual_return) ** (1/12) - 1
    monthly_fees = (1 + annual_fees) ** (1/12) - 1
    
    portfolio_value = pension_balance
    total_contributions = 0
    total_fees = 0
    total_taxes = 0
    taxable_gains_since_last_disposal = 0
    
    portfolio_history = []
    
    for month in range(months):
        gains_this_month = portfolio_value * monthly_return
        fees_this_month = portfolio_value * monthly_fees
        
        portfolio_value += gains_this_month + monthly_contribution
        portfolio_value -= fees_this_month
        total_contributions += monthly_contribution
        total_fees += fees_this_month
        
        taxable_gains_since_last_disposal += gains_this_month - fees_this_month
        
        if (month + 1) % 96 == 0 and tax_rate > 0:
            taxes_paid_this_period = taxable_gains_since_last_disposal * tax_rate
            total_taxes += taxes_paid_this_period
            portfolio_value -= taxes_paid_this_period
            taxable_gains_since_last_disposal = 0
            
        portfolio_history.append(portfolio_value)
    
    final_value = portfolio_value
    total_gains_before_tax = final_value - total_contributions + total_taxes

    return {
        'history': portfolio_history,
        'final_value': final_value,
        'total_contributions': total_contributions,
        'total_gains_before_tax': total_gains_before_tax,
        'total_taxes': total_taxes,
        'total_fees': total_fees,
        'tax_rate': tax_rate
    }

# --- Main Streamlit App Logic ---
def run(session):
    fd = session.form_data

    if session.rp_step < 8:
        st.warning("Please complete the Retirement tab before accessing Portfolio.")
        if st.button("Go to Retirement Planning"):
            session.page = "retirement"
            st.rerun()
        return

    # Inputs from the Retirement planning tab
    current_age = fd.get("age", 30)
    retirement_age = fd.get("retirement_age", 65)
    income = fd.get("income", 60000)
    contribution_rate = fd.get("contribution", 15) / 100
    pension_balance = fd.get("pension_pot", 0)
    monthly_goal = fd.get("target_income", 2000)

    years_to_retire = retirement_age - current_age
    months_to_retire = years_to_retire * 12

    st.subheader("Summary of Your Retirement Plan Inputs")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- **Current Age:** {current_age}")
        st.markdown(f"- **Annual Income:** €{income:,.0f}")
        st.markdown(f"- **Existing Pension Balance:** €{pension_balance:,.0f}")
    with col2:
        st.markdown(f"- **Retirement Age:** {retirement_age}")
        st.markdown(f"- **Contribution Rate:** {contribution_rate * 100:.0f}%")
        st.markdown(f"- **Target Monthly Retirement Income:** €{monthly_goal:,.0f}")

    st.divider()
    
    st.markdown("### Choose a Strategy")

    preset = st.radio(
        "",
        ["Conservative", "Balanced", "Aggressive"],
        index=0,
        horizontal=True
    )

    if "equity_slider" not in st.session_state:
        st.session_state.equity_slider = 20
    if "bond_slider" not in st.session_state:
        st.session_state.bond_slider = 70
    if "cash_slider" not in st.session_state:
        st.session_state.cash_slider = 10
    if "last_preset" not in st.session_state:
        st.session_state.last_preset = None

    if preset != st.session_state.last_preset:
        st.session_state.last_preset = preset
        if preset == "Conservative":
            st.session_state.equity_slider = 20
            st.session_state.bond_slider = 70
            st.session_state.cash_slider = 10
        elif preset == "Balanced":
            st.session_state.equity_slider = 50
            st.session_state.bond_slider = 40
            st.session_state.cash_slider = 10
        elif preset == "Aggressive":
            st.session_state.equity_slider = 80
            st.session_state.bond_slider = 15
            st.session_state.cash_slider = 5

    def update_allocation(changed_key):
        total = st.session_state.equity_slider + st.session_state.bond_slider + st.session_state.cash_slider
        if total != 100:
            keys = ["equity_slider", "bond_slider", "cash_slider"]
            keys.remove(changed_key)
            to_adjust = keys[0] if keys[0] != changed_key else keys[1]
            st.session_state[to_adjust] -= (total - 100)
            st.session_state[to_adjust] = max(0, min(100, st.session_state[to_adjust]))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.slider("Equities (%)", 0, 100, key="equity_slider", on_change=update_allocation, args=("equity_slider",))
    with col2:
        st.slider("Bonds (%)", 0, 100, key="bond_slider", on_change=update_allocation, args=("bond_slider",))
    with col3:
        st.slider("Cash (%)", 0, 100, key="cash_slider", on_change=update_allocation, args=("cash_slider",))

    total_allocation = st.session_state.equity_slider + st.session_state.bond_slider + st.session_state.cash_slider
    if total_allocation != 100:
        st.warning(f"Total allocation is {total_allocation}%. Adjusting...")

    allocation = {
        "equity": st.session_state.equity_slider / 100,
        "bonds": st.session_state.bond_slider / 100,
        "cash": st.session_state.cash_slider / 100
    }

    returns = {
        "equity": (0.1, 0.15),
        "bonds": (0.05, 0.05),
        "cash": (0.02, 0.01)
    }

    sector = fd.get("sector", "All sectors")
    age_group = get_age_group(current_age)
    salary_data = salary_df[(salary_df["NACE Sector"] == sector) & (salary_df["Age Group"] == age_group)]
    avg_growth = 0.025
    if not salary_data.empty:
        values = salary_data.sort_values("Year")["Value"].values
        if len(values) > 1:
            growth_rates = np.diff(values) / values[:-1]
            avg_growth = np.mean(growth_rates)

    runs = 1000
    final_values = []
    all_paths = []
    
    inflation_rate = 0.02
    inflation_monthly = (1 + inflation_rate) ** (1 / 12) - 1

    for _ in range(runs):
        balance = pension_balance
        curr_income = income
        monthly_balances = []
        for month in range(months_to_retire):
            yearly_return = sum([
                np.random.normal(returns[asset][0], returns[asset][1]) * allocation[asset]
                for asset in allocation
            ])
            monthly_return = (1 + yearly_return) ** (1 / 12) - 1
            
            if month % 12 == 0 and month > 0:
                curr_income *= (1 + avg_growth)
            
            monthly_contribution = (curr_income * contribution_rate) / 12
            
            balance = (balance + monthly_contribution) * (1 + monthly_return)
            balance /= (1 + inflation_monthly)
            monthly_balances.append(balance)
        final_values.append(balance)
        all_paths.append(monthly_balances)

    all_paths = np.array(all_paths)
    percentiles = [10, 50, 90]
    percentile_paths = {p: np.percentile(all_paths, p, axis=0) for p in percentiles}
    
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Projected Portfolio Growth Over Time")
        st.markdown(
            """
            <p style="color: #666; font-size: 15px; margin-top: -10px;">
                Simulated growth of your portfolio under different market scenarios (10th, 50th, and 90th percentiles),
                adjusted for inflation.
            </p>
            """,
            unsafe_allow_html=True,
        )

        chart_df = pd.DataFrame({
            "Month": range(1, months_to_retire + 1),
        })
        for p in percentiles:
            chart_df[f"{p}th Percentile (€)"] = percentile_paths[p]

        fig = go.Figure()
        colors = {
            10: "lightcoral",
            50: "royalblue",
            90: "darkgreen"
        }
        for p in percentiles:
            fig.add_trace(go.Scatter(
                x=chart_df["Month"],
                y=chart_df[f"{p}th Percentile (€)"],
                mode="lines",
                name=f"{p}th Percentile",
                line=dict(color=colors[p], dash="solid" if p == 50 else "dot")
            ))

        min_y = min(chart_df[[f"{p}th Percentile (€)" for p in percentiles]].min())
        max_y = max(chart_df[[f"{p}th Percentile (€)" for p in percentiles]].max())
        y_padding = (max_y - min_y) * 0.1

        fig.update_layout(
            yaxis=dict(range=[min_y - y_padding, max_y + y_padding]),
            xaxis_title="Months from Now",
            yaxis_title="Portfolio Value (€, inflation-adjusted)",
            template="plotly_white",
            hovermode="x unified",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )

        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("What This Means For You")     

        p10 = np.percentile(final_values, 10)
        p50 = np.percentile(final_values, 50)
        p90 = np.percentile(final_values, 90)

        cash_balance = pension_balance
        curr_income_cash = income
        for month in range(months_to_retire):
            if month % 12 == 0 and month > 0:
                curr_income_cash *= (1 + avg_growth)
            monthly_contribution = (curr_income_cash * contribution_rate) / 12
            cash_balance = (cash_balance + monthly_contribution) * (1 + ((1 + 0.01)**(1/12) - 1))
            cash_balance /= (1 + inflation_monthly)
        cash_final = cash_balance

        st.markdown(
            f"""
            <div class="large-text-container" style="background-color:#fffae6; padding:10px; border-left:5px solid #ffb400; 
                        margin-bottom:20px; min-height:100px;">
                <strong>
                    If you only save in Cash...<br>
                    At retirement, your pension could be around: 
                    <span style="color:#d35400; font-weight:bold;">€{cash_final:,.0f}</span>
                </strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        total_nominal_contributions = 0
        curr_income_total = income
        for year in range(years_to_retire):
            total_nominal_contributions += curr_income_total * contribution_rate * 12
            curr_income_total *= (1 + avg_growth)

        st.markdown(
            f"""
            <div class="large-text-container">
            <p style="font-size: 14px; color: #555; margin-top: -10px; margin-bottom: 25px;">
                Over {years_to_retire} years, your total contributions will grow to approximately 
                <span style="font-weight:bold;">€{total_nominal_contributions:,.0f}</span>. 
                The projected value of <span style="font-weight:bold;">€{cash_final:,.0f}</span> reflects the 
                <span style="color:#d35400;">impact of inflation</span> on your purchasing power.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="large-text-container" style="background-color:#d4edda; color:#155724; padding:15px; border-radius:6px; 
                        margin-bottom:30px;">
                Based on your chosen portfolio and contributions:<br><br>
                By age <strong>{retirement_age}</strong>, your pension fund is most likely to be around 
                <span style="font-weight:bold;">€{p50:,.0f}</span> (median outcome).<br>
                In tougher markets, it could be as low as <span style="font-weight:bold;">€{p10:,.0f}</span>.<br>
                In stronger markets, it might grow to <span style="font-weight:bold;">€{p90:,.0f}</span> or more.<br><br>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.divider()

    st.header("Deep Dive: How Different Assets Perform")
    st.markdown(
        """
        <p style="color: #666; font-size: 15px; margin-top: -10px;">
            This section shows the growth of a single-asset portfolio over 20 years, illustrating the impact
            of returns, fees, and the 8-year "Deemed Disposal" tax event on equities and bonds.
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    monthly_contribution = (income * contribution_rate) / 12

    cols = st.columns(3)
    
    # --- Equities Section ---
    with cols[0]:
        st.markdown("### <span style='color: #004d99;'>Equities</span>", unsafe_allow_html=True)
        equities_results = simulate_portfolio_with_deemed_disposal(monthly_contribution * allocation['equity'], years_to_retire, "equities", pension_balance * allocation['equity'])
        
        df = pd.DataFrame({
            'Month': range(1, len(equities_results['history']) + 1),
            'Portfolio Value': equities_results['history']
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Month'], y=df['Portfolio Value'], mode='lines', name='Equities', line=dict(color='#004d99')))
        if equities_results['tax_rate'] > 0:
            for tax_month in range(96, len(equities_results['history']) + 1, 96):
                fig.add_vline(x=tax_month, line_width=1, line_dash="dash", line_color="red")
        fig.update_layout(xaxis_title='Months', yaxis_title='Value (€)', height=350, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<h5>Key Metrics</h5>", unsafe_allow_html=True)
        
        container = st.container(border=True)
        with container:
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total value of your fund after all contributions, gains, and taxes have been applied.">
                    Final Value</span>
                    <br><span style='color:#004d99;font-weight:bold;'>€{equities_results['final_value']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total profit generated by your investments before any taxes were paid. It does not include your personal contributions.">
                    Total Gains Before Tax</span>
                    <br><span style='color:#004d99;font-weight:bold;'>€{equities_results['total_gains_before_tax']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
            with metric_cols[1]:
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of money you have personally contributed to the fund over the entire period.">
                    Total Contributions</span>
                    <br><span style='color:#004d99;font-weight:bold;'>€{equities_results['total_contributions']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of tax paid on your investment gains through the 8-year 'Deemed Disposal' events.">
                    Total Taxes Paid</span>
                    <br><span style='color:#004d99;font-weight:bold;'>€{equities_results['total_taxes']:,.2f}</span>
                    """, unsafe_allow_html=True
                )

    with cols[1]:
        st.markdown("### <span style='color: #006600;'>Bonds</span>", unsafe_allow_html=True)
        bonds_results = simulate_portfolio_with_deemed_disposal(monthly_contribution * allocation['bonds'], years_to_retire, "bonds", pension_balance * allocation['bonds'])

        df = pd.DataFrame({
            'Month': range(1, len(bonds_results['history']) + 1),
            'Portfolio Value': bonds_results['history']
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Month'], y=df['Portfolio Value'], mode='lines', name='Bonds', line=dict(color='#006600')))
        if bonds_results['tax_rate'] > 0:
            for tax_month in range(96, len(bonds_results['history']) + 1, 96):
                fig.add_vline(x=tax_month, line_width=1, line_dash="dash", line_color="red")
        fig.update_layout(xaxis_title='Months', yaxis_title='Value (€)', height=350, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h5>Key Metrics</h5>", unsafe_allow_html=True)
        
        container = st.container(border=True)
        with container:
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total value of your fund after all contributions, gains, and taxes have been applied.">
                    Final Value</span>
                    <br><span style='color:#006600;font-weight:bold;'>€{bonds_results['final_value']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total profit generated by your investments before any taxes were paid. It does not include your personal contributions.">
                    Total Gains Before Tax</span>
                    <br><span style='color:#006600;font-weight:bold;'>€{bonds_results['total_gains_before_tax']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
            with metric_cols[1]:
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of money you have personally contributed to the fund over the entire period.">
                    Total Contributions</span>
                    <br><span style='color:#006600;font-weight:bold;'>€{bonds_results['total_contributions']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of tax paid on your investment gains through the 8-year 'Deemed Disposal' events.">
                    Total Taxes Paid</span>
                    <br><span style='color:#006600;font-weight:bold;'>€{bonds_results['total_taxes']:,.2f}</span>
                    """, unsafe_allow_html=True
                )

    with cols[2]:
        st.markdown("### <span style='color: #ff8c00;'>Cash</span>", unsafe_allow_html=True)
        cash_results = simulate_portfolio_with_deemed_disposal(monthly_contribution * allocation['cash'], years_to_retire, "cash", pension_balance * allocation['cash'])

        df = pd.DataFrame({
            'Month': range(1, len(cash_results['history']) + 1),
            'Portfolio Value': cash_results['history']
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Month'], y=df['Portfolio Value'], mode='lines', name='Cash', line=dict(color='#ff8c00')))
        fig.update_layout(xaxis_title='Months', yaxis_title='Value (€)', height=350, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<h5>Key Metrics</h5>", unsafe_allow_html=True)
        
        container = st.container(border=True)
        with container:
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total value of your fund after all contributions, gains, and taxes have been applied.">
                    Final Value</span>
                    <br><span style='color:#ff8c00;font-weight:bold;'>€{cash_results['final_value']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="This is the total profit generated by your investments before any taxes were paid. It does not include your personal contributions.">
                    Total Gains Before Tax</span>
                    <br><span style='color:#ff8c00;font-weight:bold;'>€{cash_results['total_gains_before_tax']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
            with metric_cols[1]:
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of money you have personally contributed to the fund over the entire period.">
                    Total Contributions</span>
                    <br><span style='color:#ff8c00;font-weight:bold;'>€{cash_results['total_contributions']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <span data-tooltip="The total amount of tax paid on your investment gains through the 8-year 'Deemed Disposal' events.">
                    Total Taxes Paid</span>
                    <br><span style='color:#ff8c00;font-weight:bold;'>€{cash_results['total_taxes']:,.2f}</span>
                    """, unsafe_allow_html=True
                )
    st.divider()

    st.header("Retirement Goal Tracking")
    life_expectancy_ireland = 82
    retirement_years = max(life_expectancy_ireland + 5 - retirement_age, 1)

    target_fund = monthly_goal * 12 * retirement_years
    p50 = np.percentile(final_values, 50)
    gap = target_fund - p50
    st.markdown(f"""
    You plan to retire at age **{retirement_age}**.
    Based on an estimated life expectancy of **{life_expectancy_ireland}** years and a buffer of 5 years,
    your retirement fund needs to last approximately **{retirement_years} years**.
    To support your desired monthly retirement income of **€{monthly_goal:,.0f}**,
    you will need a fund of approximately **€{target_fund:,.0f}**.
    """)

    if gap > 0:
        st.warning(f"You may fall short by about **€{gap:,.0f}** with your current plan.")
        shortfall_percentage = (gap / target_fund) * 100
        st.markdown(f"This represents a shortfall of **{shortfall_percentage:.1f}%** of your target fund.")
        
        r = ((1 + 0.04) ** (1 / 12)) - 1
        pmt_fv_future = npf.fv(rate=r, nper=months_to_retire, pmt=0, pv=-pension_balance)
        required_contribution = abs(npf.pmt(rate=r, 
                                            nper=months_to_retire, 
                                            pv=0, 
                                            fv=target_fund - pmt_fv_future))

        st.markdown(f"""
        To reach your goal of **€{target_fund:,.0f}**, you would need to increase your current monthly contributions to approximately **€{required_contribution:,.0f}**
        (based on a conservative growth estimate of 4% annually above inflation, and assuming no further salary growth).
        """)
    else:
        surplus = abs(gap)
        st.success(f"Great! You're on track to meet your retirement goal, with a projected surplus of **€{surplus:,.0f}**.")
        surplus_percentage = (surplus / target_fund) * 100
        st.markdown(f"This represents a surplus of **{surplus_percentage:.1f}%** above your target fund.")
        
    st.divider()

    if st.button("← Back to Home"):
        session.page = "landing"
        st.rerun()

    # The CSS is updated to apply a larger font size to the entire container
    st.markdown("""
        <style>
            [data-tooltip] {
                position: relative;
                cursor: pointer;
                border-bottom: 1px dotted #888;
                font-weight: normal !important;
            }

            [data-tooltip]::before {
                content: attr(data-tooltip);
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                
                /* Tooltip Styling */
                background-color: #333;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 8px;
                z-index: 1000;
                width: 250px;
                white-space: normal;
                font-size: 14px;
                
                /* Hide by default */
                visibility: hidden;
                opacity: 0;
                transition: opacity 0.3s, visibility 0.3s;
            }

            [data-tooltip]::after {
                content: "";
                position: absolute;
                top: calc(100% - 5px);
                left: 50%;
                transform: translateX(-50%);
                border-width: 5px;
                border-style: solid;
                border-color: transparent transparent #333 transparent;
                z-index: 1000;
                
                /* Hide by default */
                visibility: hidden;
                opacity: 0;
                transition: opacity 0.3s, visibility 0.3s;
            }

            [data-tooltip]:hover::before,
            [data-tooltip]:hover::after {
                visibility: visible;
                opacity: 1;
            }
            
            /* Apply large font to the entire container class */
            .large-text-container {
                font-size: 1.15rem; /* This sets a large font size for the entire div */
            }
            
            /* Ensure the bolded values maintain their bold style */
            .large-text-container strong {
                font-weight: bold;
            }
            
            /* A crucial fix for the tooltip cutoff issue */
            .st-emotion-cache-16txte0 {
                overflow: visible !important;
            }

        </style>
        """, unsafe_allow_html=True)