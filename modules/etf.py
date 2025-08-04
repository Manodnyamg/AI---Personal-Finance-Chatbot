import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

def run(session):
    st.markdown("""
    <div style='font-size:30px; font-weight:700; margin-bottom:20px;color:#0068c9;font-family: Times New Roman;'>
    ETF Explorer
    </div>""", unsafe_allow_html=True)

    # --- ETF Metadata ---
    low_risk_etfs = {
    "Vanguard Total Bond Market ETF": {"ticker": "BND"},
    "iShares 1-3 Year Treasury Bond ETF": {"ticker": "SHY"},
    "Vanguard Dividend Appreciation ETF": {"ticker": "VIG"},
    }

    high_risk_etfs = {
    "Invesco QQQ Trust": {"ticker": "QQQ"},
    "ARK Innovation ETF": {"ticker": "ARKK"},
    "SPDR S&P 500 ETF Trust": {"ticker": "SPY"},
    }

    # This price_data is only used for the "Since Inception" months calculation
    np.random.seed(42)
    days = 252 * 3  # 3 years trading days approx
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    price_data = pd.DataFrame({
    "Close": 100 * np.cumprod(1 + np.random.normal(0, 0.001, days))
    }, index=dates)

    # Define your projection periods dictionary for the Monte Carlo simulation
    # These are the periods for which we will run MC and display results in the bar chart
    mc_bar_chart_projection_periods = {
        "1 Month": 1,
        "3 Months": 3,
        "1 Year": 12,
        "3 Years": 36,
        "5 Years": 60,
    }

    def fetch_etf_data(ticker, period):
        etf = yf.Ticker(ticker)
        data = etf.history(period=period)
        if data.empty:
            return data, {}
        data["MA_30"] = data["Close"].rolling(window=30).mean()
        data["MA_90"] = data["Close"].rolling(window=90).mean()
        return data, etf.info

    def calculate_risk_metrics(data):
        returns = data["Close"].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        max_drawdown = (data["Close"] / data["Close"].cummax() - 1).min()
        return volatility, sharpe_ratio, max_drawdown

    def monte_carlo_simulation(data, months, sims=1000):
        if data.empty or "Close" not in data.columns or len(data) < 2:
            return None, None
        returns = data["Close"].pct_change().dropna()
        if returns.empty: # Handle case where pct_change results in empty Series
             return None, None
        last_price = data["Close"].iloc[-1]
        
        # Ensure that mean and std are not NaN before proceeding
        if returns.mean() is None or np.isnan(returns.mean()) or returns.std() is None or np.isnan(returns.std()):
            return None, None

        mu = returns.mean() * 252  # annual drift
        sigma = returns.std() * np.sqrt(252)  # annual volatility

        dt = 1/252
        steps = int(months * 21)  # approx trading days in months

        if steps == 0: # Handle cases where months is very small and steps becomes 0
            return None, None

        price_paths = np.zeros((steps + 1, sims))
        price_paths[0] = last_price

        for t in range(1, steps + 1):
            rand = np.random.standard_normal(sims)
            price_paths[t] = price_paths[t-1] * np.exp((mu - 0.5 * sigma**2)*dt + sigma * np.sqrt(dt) * rand)

        # Calculate projected returns as % change from last price to last simulated price
        projected_returns = (price_paths[-1] / last_price) - 1
        return price_paths, projected_returns

    # --- Main UI ---

    # --- Risk Category Dropdown ---
    risk_category = st.selectbox("Select Risk Category:", ["Low Risk", "High Risk"])

    # --- Dynamic ETF Dropdown based on Risk Category ---
    if risk_category == "Low Risk":
        selected_etf = st.selectbox("Choose an ETF:", list(low_risk_etfs.keys()))
        ticker = low_risk_etfs[selected_etf]["ticker"]
    else:
        selected_etf = st.selectbox("Choose an ETF:", list(high_risk_etfs.keys()))
        ticker = high_risk_etfs[selected_etf]["ticker"]

    # Fetch data up to max period for initial info and risk metrics
    default_data, info = fetch_etf_data(ticker, "max")

    # --- Header and styled metric boxes with tooltips ---
    quote = info.get('regularMarketPrice', 'N/A')
    expense = info.get('expenseRatio', 'N/A')
    aum = info.get('totalAssets', 'N/A')
    st.markdown(f"""
        <style>
        .metric-container {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 20px;
            font-family: 'Times New Roman';
            width: 100%;
        }}
        .metric-box {{
            background-color: #f9f9f9;
            border-left: 4px solid #0068c9;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            min-width: 200px;
            flex-grow: 1;
            flex-basis: 0;
            position: relative;
        }}
        .metric-box .info-icon {{
            position: absolute;
            top: 8px;
            left: 8px;
            font-size: 14px;
            color: #0068c9;
            cursor: help;
        }}
        .metric-label {{
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin-left: 20px;
        }}
        .metric-value {{
            font-size: 16px;
            font-weight: 600;
            color: #111;
            margin-left: 20px;
        }}
        </style>

        <div class="metric-container">
            <div class="metric-box">
                <span class="info-icon" title="The most recent market price for this ETF.">ⓘ</span>
                <div class="metric-label">Quote</div>
                <div class="metric-value">€{quote:.2f}</div>
            </div>
            <div class="metric-box">
                <span class="info-icon" title="Annual operating expenses as a percentage of assets.">ⓘ</span>
                <div class="metric-label">Expense Ratio</div>
                <div class="metric-value">{expense if expense != 'N/A' else 'N/A'}</div>
            </div>
            <div class="metric-box">
                <span class="info-icon" title="Total value of assets managed by the fund.">ⓘ</span>
                <div class="metric-label">Assets Under Management</div>
                <div class="metric-value">€{aum:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


    # --- First Row: Price Chart (Left) and ETF Description/Risk Metrics (Right) ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Price Chart")
        period_map = {
        "1 Month": "1mo", "3 Months": "3mo", "1 Year": "1y",
        "3 Years": "3y", "5 Years": "5y", "Since Inception": "max"
        }
        selected_period_label = st.radio("Select Time Range", list(period_map.keys()), horizontal=True)
        selected_period = period_map[selected_period_label]
        data_for_chart, _ = fetch_etf_data(ticker, selected_period) # Use different variable name for clarity

        if data_for_chart.empty:
            st.warning("No data found for this period.")
        else:
            start_price = data_for_chart["Close"].iloc[0]
            end_price = data_for_chart["Close"].iloc[-1]
            color = "green" if end_price >= start_price else "red"

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(data_for_chart.index, data_for_chart["Close"], label="Close Price", color=color, linewidth=2)
            ax.plot(data_for_chart.index, data_for_chart["MA_30"], label="30-day MA", linestyle="--", alpha=0.7)
            ax.plot(data_for_chart.index, data_for_chart["MA_90"], label="90-day MA", linestyle=":", alpha=0.7)
            ax.set_ylabel("Price (€)")
            ax.set_title(f"{ticker} - Price Over {selected_period_label}")
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            ax.set_facecolor("white")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(False)
            st.pyplot(fig)
            st.caption(f"Data from Yahoo Finance | Range: {selected_period_label}")

    with col2:
        st.subheader("ETF Description")
        st.write(info.get("longBusinessSummary", "No detailed description available."))

        st.subheader("Risk Metrics")
        volatility, sharpe_ratio, max_drawdown = calculate_risk_metrics(default_data)

        st.markdown(f"""
        <ul style="list-style-type:none; padding-left:0;">
        <li>
            <strong>Volatility (Annualized):</strong>
            <span style="color:green; font-size:18px; font-weight:bold;">{volatility:.2%}</span><br>
            <span style="font-size:16px; color:#000;">Shows how much the ETF’s price fluctuates over a year. Higher volatility indicates more risk.</span>
        </li><br>
        <li>
            <strong>Sharpe Ratio:</strong>
            <span style="color:green; font-size:18px; font-weight:bold;">{sharpe_ratio:.2f}</span><br>
            <span style="font-size:16px; color:#000;">Measures return per unit of risk. Higher values indicate better risk-adjusted performance.</span>
        </li><br>
        <li>
            <strong>Max Drawdown:</strong>
            <span style="color:green; font-size:18px; font-weight:bold;">{max_drawdown:.2%}</span><br>
            <span style="font-size:16px; color:#000;">The largest observed loss from peak to trough. Indicates potential downside risk.</span>
        </li>
        </ul>
        """, unsafe_allow_html=True)

    # --- Full Width Section for Monte Carlo Simulation Inputs ---
    st.markdown("---") # Optional: A horizontal rule for visual separation
    st.subheader("Projected Returns via Monte Carlo Simulation Inputs")

    # Investment type and input
    investment_type = st.radio("Select investment type:", ["Monthly Installment", "One-time Investment"], horizontal=True, key="investment_type_mc_input")
    if investment_type == "Monthly Installment":
        invest_amt = st.number_input("Monthly investment amount (€):", 1.0, value=50.0, step=1.0, format="%.2f", key="monthly_invest_amt_mc_input")
    else:
        invest_amt = st.number_input("One-time investment amount (€):", 1.0, value=250.0, step=1.0, format="%.2f", key="one_time_invest_amt_mc_input")

    # The main slider for the Monte Carlo simulation duration
    months = st.slider("Select duration for projection (months):", 1, 120, 12, key="mc_duration_slider_input")

    # --- Second Row: Monte Carlo Projection Chart (Left) and Summary (Right) ---
    st.markdown("---") # Optional: Another horizontal rule
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <h3 style="margin: 0; margin-right: 8px;">Monte Carlo Simulation Results</h3>
        <span style="font-size: 14px; color: #0068c9; cursor: help;" title="Runs thousands of scenarios to show possible future outcomes based on historical patterns.">ⓘ</span>
    </div>
    """, unsafe_allow_html=True)

    mc_chart_col, mc_summary_col = st.columns(2)
    # Run Monte Carlo for the selected duration
    price_paths, projected_returns = monte_carlo_simulation(default_data, months)

    if projected_returns is None:
        mc_summary_col.warning("Insufficient or invalid data for Monte Carlo simulation. Please select a valid ETF and period.")
        with mc_chart_col:
             st.info("No data to plot Monte Carlo projections.")
    else:
        median_return = np.median(projected_returns)
        lower_pct = np.percentile(projected_returns, 5)
        upper_pct = np.percentile(projected_returns, 95)

        with mc_summary_col: # Place summary content in the right column
            st.markdown("### Projected Portfolio Summary")
            st.write(f"**Investment Type:** {investment_type}")
            if investment_type == "Monthly Installment":
                 st.write(f"**Monthly Investment:** €{invest_amt:.2f}")
            else:
                 st.write(f"**One-time Investment:** €{invest_amt:.2f}")
            st.write(f"**Duration:** {months} months")

            st.success(f"""
                        - Most likely outcome:
                          _(Median projected return: {median_return:.2%})_

                        - Pessimistic case (5% worst outcomes):
                          Return could be as low as **{lower_pct:.2%}**

                        - Optimistic case (top 5%):
                          Return could be as high as **{upper_pct:.2%}**
                        """)
    #st.subheader("Monte Carlo Simulation Results") # New subheader for the results section
    
        
                  # Calculate FV based on investment type and median return
            if investment_type == "Monthly Installment":
                # Assuming the median_return is the total return for the 'months' period
                # We need an effective monthly rate for compounding monthly investments
                if (1 + median_return) <= 0: # Avoid issues with power of negative numbers
                    r_monthly = -1 # Effective monthly loss of 100%
                else:
                    r_monthly = (1 + median_return)**(1/months) - 1

                if r_monthly == 0:
                    fv = invest_amt * months # Simple sum if no growth/decay
                else:
                    fv = invest_amt * (((1 + r_monthly) ** months - 1) / r_monthly)
                st.markdown(f"""
                    - Projected portfolio value after **{months} months** with **€{invest_amt:.2f}/month**:
                    **€{fv:,.2f}**
                    """)
            else: # One-time Investment
                fv = invest_amt * (1 + median_return)
                st.markdown(f"""
                    - Projected portfolio value after **{months} months** with a **€{invest_amt:.2f} one-time investment**:
                    **€{fv:,.2f}**
                    """)

        with mc_chart_col: # Place chart content in the left column
            # Calculate median returns for the specific bar chart periods using MC simulation
            actual_median_returns = {}
            for label, period_months in mc_bar_chart_projection_periods.items():
                # We need to ensure we use default_data for historical volatility/return calculation
                _, period_projected_returns = monte_carlo_simulation(default_data, period_months)
                if period_projected_returns is not None:
                    actual_median_returns[label] = np.median(period_projected_returns)
                else:
                    actual_median_returns[label] = 0 # Fallback for no data or error

            labels = list(actual_median_returns.keys())
            values = list(actual_median_returns.values())

            fig, ax = plt.subplots(figsize=(8, 4))
            # Plot raw return values, which are decimals (e.g., 0.15 for 15%)
            bars = ax.bar(labels, values, color='#0068c9')

            # Set title and y-axis label to reflect percentages if that's the desired display
            ax.set_title("Median Projected Returns (%)", fontsize=14)
            ax.set_ylabel("Return (%)")

            # Adjust y-axis limits to show percentage range, potentially from negative to positive
            # Find min and max values to set dynamic limits
            min_val = min(0, min(values))
            max_val = max(0, max(values))
            ax.set_ylim(min_val * 1.2, max_val * 1.2) # Add some padding

            ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Labels on bars: Display as percentages (multiply by 100 and format)
            for bar, ret in zip(bars, values):
                height = bar.get_height()
                # Check if the return is negative to adjust label position
                if height >= 0:
                    va = 'bottom'
                    offset = 0.005 * (max_val - min_val) # Dynamic offset based on range
                else:
                    va = 'top'
                    offset = -0.005 * (max_val - min_val) # Dynamic offset for negative bars

                ax.text(bar.get_x() + bar.get_width() / 2, height + offset, f"{ret * 100:.1f}%", ha='center', va=va, fontsize=10)

            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            st.caption(f"These returns are simulated values and are subject to market changes.")
    