import os
import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from excel_parser import ExcelParser
from financial_engine import FinancialEngine
from llm import ask_llama
from intent_classifier import detect_intent, detect_member

st.set_page_config(layout="wide", page_title="Financial AI Chatbot & Dashboard", page_icon="💼")

# ── Styling / Aesthetics ───────────────────────────────────────────────────────
st.markdown(
    """
     <style>
    /* Professional Wealth Management Adaptive Theme */
    .main-title {
        font-size: 2.2rem; 
        font-weight: 800;
        margin-bottom: 0.1rem;
        text-align: left;
        color: #FFFFFF !important; /* Force title to be visible on dark background */
    }
    .subtitle { 
        color: #A3B899 !important; /* Made slightly lighter for visibility */
        font-size: 1.05rem; 
        margin-bottom: 1.5rem; 
        text-align: left; 
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 1.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E88E5;
        padding-left: 0.75rem;
        color: #FFFFFF !important; /* Force headers to be visible */
    }
    
    /* FAQ & Chat Buttons */
    .stButton>button {
        border-radius: 8px; border: 1px solid #D6DEE3;
        background-color: #F6F9FB; color: #0E3A53; font-weight: 500;
        padding: 0.45rem 0.8rem; white-space: normal; text-align: left;
    }
    .stButton>button:hover {
        background-color: #0E3A53; color: white; border-color: #0E3A53;
    }
    
    /* Info Cards & Containers */
    .insight-card {
        background-color: #FFFFFF !important; /* Force cards to stay pure white */
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        color: #1A202C !important; /* Kept dark text for readability inside white cards */
    }
    .insight-card strong {
        color: #0E3A53 !important; /* Professional dark blue contrast for bold items */
    }
    .insight-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1A202C !important; /* Force card subtitles/headers to be dark text */
    }
    .badge {
        display: inline-block; 
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
        margin-top: 0.3rem;
    }
    .badge-success { background-color: #C6F6D5; color: #22543D; }
    .badge-warning { background-color: #FEFCBF; color: #744210; }
    .badge-danger { background-color: #FED7D7; color: #742A2A; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Currency Format Helpers ──────────────────────────────────────────────────
def rupee(x):
    if x is None:
        return "N/A"
    return f"₹ {x:,.2f}"

def format_currency(x):
    if x is None:
        return "N/A"
    abs_x = abs(x)
    if abs_x >= 10000000: # 1 Crore
        return f"₹ {x/10000000:.2f} Cr"
    elif abs_x >= 100000: # 1 Lakh
        return f"₹ {x/100000:.2f} Lakhs"
    else:
        return f"₹ {x:,.2f}"

# ── Main Header ──────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">💼 Financial AI Advisor & Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Gain visual insights and ask intelligent questions about your family portfolio.</div>',
    unsafe_allow_html=True,
)

# ── File Upload Section ────────────────────────────────────────────────────────
file = st.file_uploader("Upload Family Portfolio (.xlsx)", type=["xlsx"])

if file:
    with st.spinner("Parsing portfolio Excel sheet and loading data models..."):
        os.makedirs("data", exist_ok=True)
        path = "data/uploaded.xlsx"
        with open(path, "wb") as f:
            f.write(file.read())

        parser = ExcelParser(path)
        tables = parser.parse()
        engine = FinancialEngine(tables)

        st.session_state["engine"] = engine
        st.session_state["tables"] = tables
    st.success("✅ Excel parsed successfully")

# ── Tab Definitions ───────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Portfolio Summary",
    "👥 Member & Allocation",
    "🏆 Fund Performance",
    "🧠 AI Insights",
    "🎯 Goal Simulator",
    "💬 Chatbot",
])

# ── Guard: no file uploaded yet ───────────────────────────────────────────────
if "engine" not in st.session_state:
    for _tab in [tab1, tab2, tab3, tab4, tab5]:
        with _tab:
            st.info("Please upload your Family Portfolio Excel file above to view this section.")
    with tab6:
        st.header("💬 Ask the Financial Chatbot")
        st.info("Please upload your Family Portfolio Excel file above to start chatting.")
    st.stop()

# ── Shared state ──────────────────────────────────────────────────────────────
engine = st.session_state["engine"]
tables = st.session_state["tables"]

# Pre-compute values shared across tabs
total_val = engine.fund_value()
total_inv = engine.investment()
total_gain = engine.returns()
total_xirr = engine.xirr()
total_ret_pct = (total_gain / total_inv * 100) if total_inv and total_inv > 0 else 0.0
top_df, bottom_df = engine.get_fund_performance()
alloc = engine.get_asset_allocation()
sip_total = engine.sip_amount_total()

# ------------------------------------------------------------------
# TAB 1: PORTFOLIO SUMMARY DASHBOARD (KPI Cards)
# ------------------------------------------------------------------
with tab1:
    st.markdown('<div class="section-header">📈 Portfolio Summary Dashboard</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Portfolio Value",
            value=format_currency(total_val),
            help="Current market valuation of all investments."
        )
    with col2:
        st.metric(
            label="Total Invested Cost",
            value=format_currency(total_inv),
            help="Initial principal investment amount."
        )
    with col3:
        st.metric(
            label="Total Gain / Loss",
            value=format_currency(total_gain),
            delta=f"{'+' if total_gain >= 0 else ''}{total_gain/total_inv*100:.2f}%" if total_inv else None,
            help="Net absolute capital gain/loss including realized and unrealized profit."
        )
    with col4:
        st.metric(
            label="Portfolio Returns %",
            value=f"{total_ret_pct:.2f}%",
            help="Absolute cumulative return rate of your investments."
        )
    with col5:
        st.metric(
            label="Portfolio XIRR %",
            value=f"{total_xirr:.2f}%" if total_xirr is not None else "N/A",
            help="Weighted internal rate of return reflecting annualized performance."
        )

# ------------------------------------------------------------------
# TAB 2: MEMBER COMPARISON & ASSET ALLOCATION
# ------------------------------------------------------------------
with tab2:
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown('<div class="section-header">👥 Family Member Allocation</div>', unsafe_allow_html=True)
        member_data = engine.get_member_comparison()

        if member_data:
            members = [m["Member"] for m in member_data]
            values = [m["Portfolio Value"] for m in member_data]
            investments = [m["Investment"] for m in member_data]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name='Portfolio Value',
                x=members,
                y=values,
                marker_color='#0E3A53',
                hovertemplate="Value: ₹%{y:,.2f}<extra></extra>"
            ))
            fig_bar.add_trace(go.Bar(
                name='Invested Cost',
                x=members,
                y=investments,
                marker_color='#A2B5CD',
                hovertemplate="Cost: ₹%{y:,.2f}<extra></extra>"
            ))
            fig_bar.update_layout(
                barmode='group',
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Amount (₹)'),
                xaxis=dict(title='')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Member info cards
            m_cols = st.columns(len(member_data))
            for idx, m in enumerate(member_data):
                with m_cols[idx]:
                    gain_color = "#2F855A" if m['Gain'] >= 0 else "#C53030"
                    st.markdown(
                        f"""
                        <div style="background-color: #F7FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; text-align: center; color: #1A202C !important;">
                            <strong style="color: #0E3A53; font-size: 0.9rem;">{m['Member']}</strong><br/>
                            <span style="font-size: 0.8rem; color: #4A5568;">Value: <strong style="color: #1A202C !important;">{format_currency(m['Portfolio Value'])}</strong></span><br/>
                            <span style="font-size: 0.8rem; color: #4A5568;">Cost: <strong style="color: #1A202C !important;">{format_currency(m['Investment'])}</strong></span><br/>
                            <span style="font-size: 0.8rem; color: #4A5568;">Return: <strong style="color: {gain_color};">{m['Return %']:.1f}%</strong></span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("No member details detected.")

    with c_right:
        st.markdown('<div class="section-header">📊 Asset Class Allocation</div>', unsafe_allow_html=True)

        # Filter non-zero classes
        labels = []
        vals = []
        colors_map = {
            "Equity": "#0E3A53",
            "Debt": "#2E7D32",
            "Hybrid": "#FF8F00",
            "Other": "#757575"
        }
        for k, v in alloc.items():
            if v > 0:
                labels.append(k)
                vals.append(v)

        if vals:
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=vals,
                hole=0.45,
                marker=dict(colors=[colors_map[l] for l in labels]),
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Value: ₹%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
            )])
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Allocation table breakdown
            alloc_df = pd.DataFrame({
                "Asset Class": labels,
                "Current Value": [rupee(v) for v in vals],
                "Weight %": [f"{v/sum(vals)*100:.2f}%" for v in vals]
            })
            st.dataframe(alloc_df, hide_index=True, use_container_width=True)
        else:
            st.info("No asset class breakdown available.")

# ------------------------------------------------------------------
# TAB 3: FUND PERFORMANCE & HISTORICAL GROWTH
# ------------------------------------------------------------------
with tab3:
    c_perf, c_growth = st.columns(2)

    with c_perf:
        st.markdown('<div class="section-header">🏆 Top & Bottom Performing Funds</div>', unsafe_allow_html=True)

        if not top_df.empty:
            tab_top, tab_bottom = st.tabs(["🟢 Top 5 Performing Funds", "🔴 Bottom 5 Performing Funds"])

            with tab_top:
                fig_top = px.bar(
                    top_df,
                    x='Return %',
                    y='Fund Name',
                    orientation='h',
                    color_discrete_sequence=['#2E7D32'],
                    text='Return %'
                )
                fig_top.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='inside',
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Valuation: ₹%{customdata[0]:,.2f}<extra></extra>",
                    customdata=top_df[['Current Value']].values
                )
                fig_top.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, title='Cumulative Return %'),
                    yaxis=dict(autorange="reversed", title='')
                )
                st.plotly_chart(fig_top, use_container_width=True)

            with tab_bottom:
                fig_bot = px.bar(
                    bottom_df,
                    x='Return %',
                    y='Fund Name',
                    orientation='h',
                    color_discrete_sequence=['#C62828'],
                    text='Return %'
                )
                fig_bot.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='inside',
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Valuation: ₹%{customdata[0]:,.2f}<extra></extra>",
                    customdata=bottom_df[['Current Value']].values
                )
                fig_bot.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, title='Cumulative Return %'),
                    yaxis=dict(autorange="reversed", title='')
                )
                st.plotly_chart(fig_bot, use_container_width=True)

            # Full metrics details table
            perf_combined = pd.concat([top_df, bottom_df.sort_values(by="Return %", ascending=False)]).drop_duplicates().reset_index(drop=True)
            perf_combined["Current Value"] = perf_combined["Current Value"].apply(rupee)
            perf_combined["Invested Amount"] = perf_combined["Invested Amount"].apply(rupee)
            perf_combined["Return %"] = perf_combined["Return %"].apply(lambda r: f"{r:.2f}%")
            perf_combined["XIRR"] = perf_combined["XIRR"].apply(lambda x: f"{x:.2f}%")

            with st.expander("🔎 View Performance Details Table"):
                st.dataframe(perf_combined, hide_index=True, use_container_width=True)
        else:
            st.info("No mutual scheme data found to calculate performance.")

    with c_growth:
        st.markdown('<div class="section-header">📈 Portfolio Value Growth Over Time</div>', unsafe_allow_html=True)
        growth_df = engine.get_portfolio_growth_series()

        if not growth_df.empty:
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Scatter(
                x=growth_df['Month'],
                y=growth_df['Current Value'],
                mode='lines',
                name='Market Value',
                line=dict(color='#0E3A53', width=3),
                hovertemplate="Market Value: ₹%{y:,.2f}<extra></extra>"
            ))
            fig_growth.add_trace(go.Scatter(
                x=growth_df['Month'],
                y=growth_df['Invested Amount'],
                mode='lines',
                name='Invested Cost',
                line=dict(color='#A2B5CD', width=2, dash='dash'),
                hovertemplate="Invested Cost: ₹%{y:,.2f}<extra></extra>"
            ))
            fig_growth.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor='rgba(0,0,0,0.05)', title=''),
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Amount (₹)')
            )
            st.plotly_chart(fig_growth, use_container_width=True)
            st.caption("ℹ️ Portfolio value history estimated based on chronological transaction records and historical transaction nav rates.")
        else:
            st.info("No transaction history available to generate portfolio growth charts.")

# ------------------------------------------------------------------
# TAB 4: AI INSIGHTS PANEL
# ------------------------------------------------------------------
with tab4:
    st.markdown('<div class="section-header">🧠 AI Insights & Warnings</div>', unsafe_allow_html=True)

    # Gather dynamic insights
    insights = []
    warnings = []

    if not top_df.empty:
        best_fund = top_df.iloc[0]
        insights.append(f"🌟 <strong>Best Performing Fund</strong>: <strong>{best_fund['Fund Name']}</strong> yielding a cumulative return of <strong>{best_fund['Return %']:.2f}%</strong>.")

    if not bottom_df.empty:
        worst_fund = bottom_df.iloc[0]
        insights.append(f"⚠️ <strong>Worst Performing Fund</strong>: <strong>{worst_fund['Fund Name']}</strong> with a return of <strong>{worst_fund['Return %']:.2f}%</strong>.")

    # Highest value holding
    df_scheme = engine.get_sheet("scheme")
    if df_scheme is not None and not df_scheme.empty:
        scheme_col = engine.find_col(df_scheme, "scheme", "name") or engine.find_col(df_scheme, "scheme")
        val_col = engine.find_col(df_scheme, "current value")
        if scheme_col and val_col:
            df_scheme_clean = df_scheme.copy()
            df_scheme_clean["ValNum"] = pd.to_numeric(df_scheme_clean[val_col], errors="coerce").fillna(0)
            df_scheme_sorted = df_scheme_clean.sort_values(by="ValNum", ascending=False).reset_index(drop=True)
            if not df_scheme_sorted.empty and df_scheme_sorted.loc[0, "ValNum"] > 0:
                highest_fund = df_scheme_sorted.loc[0, scheme_col]
                highest_val = df_scheme_sorted.loc[0, "ValNum"]
                insights.append(f"🏆 <strong>Highest Value Holding</strong>: <strong>{highest_fund}</strong> representing <strong>{format_currency(highest_val)}</strong>.")

                # Check Concentration Risk
                pct_share = (highest_val / total_val * 100) if total_val else 0.0
                if pct_share > 30.0:
                    warnings.append(f"⚠️ <strong>Concentration Risk Warning</strong>: <strong>{highest_fund}</strong> constitutes <strong>{pct_share:.1f}%</strong> of your total portfolio value. Financial planners generally recommend limiting single-fund exposure to 20-25% to manage downside risk.")

    # SIP amount
    if sip_total:
        insights.append(f"💵 <strong>Savings Rate</strong>: You have an active monthly SIP of <strong>{rupee(sip_total)}</strong> fueling your portfolio's compounding.")

    # Family returns
    insights.append(f"📈 <strong>Family Return Summary</strong>: The overall portfolio return stands at <strong>{total_ret_pct:.2f}%</strong> with an annualized growth (XIRR) of <strong>{total_xirr:.2f}%</strong>.")

    # Asset allocation observations
    if total_val and total_val > 0:
        eq_pct = alloc.get("Equity", 0) / total_val * 100
        db_pct = alloc.get("Debt", 0) / total_val * 100
        hb_pct = alloc.get("Hybrid", 0) / total_val * 100

        insights.append(f"💼 <strong>Asset Allocation Mix</strong>: Your assets are distributed as: <strong>Equity {eq_pct:.1f}%</strong> | <strong>Debt {db_pct:.1f}%</strong> | <strong>Hybrid {hb_pct:.1f}%</strong>.")

        if eq_pct > 80.0:
            warnings.append(f"📈 <strong>Aggressive Equity Bias</strong>: Your portfolio has an aggressive <strong>{eq_pct:.1f}%</strong> allocation to Equity. While beneficial for long-term wealth, prepare for higher short-term volatility during market corrections.")
        elif db_pct < 10.0:
            warnings.append(f"🛡️ <strong>Low Debt Cushion</strong>: A debt allocation of under 10% (<strong>{db_pct:.1f}%</strong> detected) leaves you with little hedge during market downturns. Adding a debt buffer offers safety and cash for opportunistic rebalancing.")

    # Display Insights in layout columns
    i_left, i_right = st.columns(2)
    with i_left:
        st.markdown('<div class="insight-header">💡 Key Portfolio Insights</div>', unsafe_allow_html=True)
        for ins in insights:
            st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

    with i_right:
        st.markdown('<div class="insight-header">⚠️ Risk & Diversification Warnings</div>', unsafe_allow_html=True)
        if warnings:
            for warn in warnings:
                st.markdown(
                    f"""
                    <div style="background-color: #FFF5F5; border-left: 4px solid #E53E3E; padding: 12px; margin-bottom: 12px; border-radius: 0 8px 8px 0; font-size: 0.9rem; color: #9B2C2C;">
                        {warn}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div style="background-color: #F0FFF4; border-left: 4px solid #38A169; padding: 15px; border-radius: 0 8px 8px 0; font-size: 0.9rem; color: #22543D;">
                    ✅ <strong>Healthy Diversification</strong>: No high concentration warnings or serious asset imbalances detected.
                </div>
                """,
                unsafe_allow_html=True
            )

# ------------------------------------------------------------------
# TAB 5: GOAL PROJECTION SIMULATOR
# ------------------------------------------------------------------
with tab5:
    st.markdown('<div class="section-header">🎯 Interactive Goal Projection Simulator</div>', unsafe_allow_html=True)
    st.caption("Plan your financial goals using Monte Carlo simulation. Volatility is automatically estimated using your portfolio's asset allocation.")

    # Prefill defaults from engine facts
    default_rate = float(f"{total_xirr:.1f}") if total_xirr and total_xirr > 0 else 12.0
    default_sip = float(sip_total) if sip_total else 20000.0

    sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
    with sim_col1:
        target_amt = st.number_input(
            "Target Goal Amount (₹)",
            min_value=50000.0,
            step=100000.0,
            value=10000000.0,
            format="%f",
            help="The target wealth corpus you want to achieve."
        )
        st.caption(f"Target: **{format_currency(target_amt)}**")
    with sim_col2:
        expected_rate = st.slider(
            "Expected Annual Return %",
            min_value=2.0,
            max_value=30.0,
            value=default_rate,
            step=0.5,
            help="Expected annual compound growth rate."
        )
    with sim_col3:
        monthly_sip_sim = st.number_input(
            "Monthly SIP Contribution (₹)",
            min_value=0.0,
            step=1000.0,
            value=default_sip,
            format="%f",
            help="New or active monthly savings contribution."
        )
        st.caption(f"Monthly: **{rupee(monthly_sip_sim)}**")
    with sim_col4:
        horizon_years = st.slider(
            "Investment Horizon (Years)",
            min_value=1,
            max_value=40,
            value=10,
            step=1,
            help="Number of years you plan to invest."
        )

    include_curr_portfolio = st.checkbox(
        f"Include current portfolio valuation ({format_currency(total_val)}) as starting lump sum",
        value=True
    )

    # Run simulation
    with st.spinner("Calculating probability distributions and project path curves..."):
        proj_df, expected_fv, prob_success, yrs_req = engine.simulate_goal_probability(
            target_amount=target_amt,
            expected_return_pct=expected_rate,
            monthly_sip=monthly_sip_sim,
            years=horizon_years,
            include_current=include_curr_portfolio
        )

    # Render simulator results
    res_col1, res_col2, res_col3 = st.columns(3)

    with res_col1:
        st.metric(
            label="Future Expected Value (Median)",
            value=format_currency(expected_fv),
            help="Median wealth projection (50% probability of being higher or lower)."
        )
    with res_col2:
        if yrs_req is not None:
            if yrs_req <= horizon_years:
                st.metric(
                    label="Years to Reach Target",
                    value=f"{yrs_req} Years",
                    help="Estimated years to cross target amount based on median path."
                )
            else:
                st.metric(
                    label="Years to Reach Target",
                    value=f"{yrs_req} Years",
                    delta="Exceeds Horizon",
                    delta_color="inverse",
                    help="Target requires longer than your planned investment horizon."
                )
        else:
            st.metric(
                label="Years to Reach Target",
                value="Unreachable",
                help="Goal cannot be reached with the current rate and SIP contribution."
            )

    with res_col3:
        # Determine status color for progress bar and metrics
        if prob_success >= 70.0:
            badge_class = "badge-success"
            badge_label = "🟢 High Success Probability"
        elif prob_success >= 40.0:
            badge_class = "badge-warning"
            badge_label = "🟡 Moderate Success Probability"
        else:
            badge_class = "badge-danger"
            badge_label = "🔴 Low Success Probability"

        st.metric(
            label="Goal Success Probability",
            value=f"{prob_success:.1f}%",
            help="Percentage of Monte Carlo runs that successfully cross target amount."
        )
        st.markdown(f'<span class="badge {badge_class}">{badge_label}</span>', unsafe_allow_html=True)

    # Plot projection
    fig_proj = go.Figure()

    # 25th percentile line (no fill)
    fig_proj.add_trace(go.Scatter(
        x=proj_df['Date'],
        y=proj_df['Conservative (25th)'],
        mode='lines',
        line=dict(width=0.5, color='rgba(239, 68, 68, 0.5)'),
        showlegend=False,
        hovertemplate="Conservative Market (25th %ile): ₹%{y:,.2f}<extra></extra>"
    ))
    # 75th percentile line (filled to 25th)
    fig_proj.add_trace(go.Scatter(
        x=proj_df['Date'],
        y=proj_df['Optimistic (75th)'],
        mode='lines',
        line=dict(width=0.5, color='rgba(16, 185, 129, 0.5)'),
        fill='tonexty',
        fillcolor='rgba(14, 58, 83, 0.05)', # semi-transparent navy
        name='Market Variance Range (25th - 75th %ile)',
        hovertemplate="Optimistic Market (75th %ile): ₹%{y:,.2f}<extra></extra>"
    ))
    # Median path (dark bold line)
    fig_proj.add_trace(go.Scatter(
        x=proj_df['Date'],
        y=proj_df['Median (50th)'],
        mode='lines',
        name='Expected Value (Median Projection)',
        line=dict(color='#0E3A53', width=3),
        hovertemplate="Expected Value: ₹%{y:,.2f}<extra></extra>"
    ))
    # Target line (horizontal line at target amount)
    fig_proj.add_trace(go.Scatter(
        x=[proj_df['Date'].min(), proj_df['Date'].max()],
        y=[target_amt, target_amt],
        mode='lines',
        name='Target Goal Threshold',
        line=dict(color='#EF4444', width=2, dash='dash'),
        hovertemplate="Target Goal: ₹%{y:,.2f}<extra></extra>"
    ))
    fig_proj.update_layout(
        title='Wealth Projection Path Chart',
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Valuation (₹)')
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    with st.expander("Detected Sheets (for verification)"):
        for sheet, df in tables.items():
            st.subheader(sheet)
            st.write("Columns:", df.columns.tolist())
            st.dataframe(df.head())

# ------------------------------------------------------------------
# TAB 6: CHATBOT INTERFACE
# ------------------------------------------------------------------
with tab6:
    st.header("💬 Ask the Financial Chatbot")

    # ── year extraction ───────────────────────────────────────────────────────
    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "fifteen": 15, "twenty": 20, "twenty-five": 25, "thirty": 30,
    }

    def extract_years(question):
        q = question.lower()
        match = re.search(r"(\d+)\s*(?:years?|yrs?)", q)
        if match:
            return int(match.group(1))
        for word, num in NUMBER_WORDS.items():
            if word in q:
                return num
        return None

    # ── answer engine ─────────────────────────────────────────────────────────
    def answer(question, engine):
        intent = detect_intent(question)
        holder_name = detect_member(question)

        # Label shown before every answer so the user knows which scope was used
        if holder_name:
            scope_label = f"🔍 Answering for **{holder_name}**\n\n"
        else:
            scope_label = "🔍 Answering for **the entire family**\n\n"

        # ── fund value ────────────────────────────────────────────────────────
        if intent == "fund_value":
            v = engine.fund_value(holder_name)
            if v is None:
                return "warning", scope_label + "Current fund value is not available in this report."
            rate = engine.xirr(holder_name)
            msg = scope_label + f"Current fund value is **{rupee(v)}**."
            if rate is not None:
                msg += f"\n\n📈 Growing at an annualised rate (XIRR) of **{rate:.2f}% per year**."
            return "success", msg

        # ── investment ────────────────────────────────────────────────────────
        if intent == "investment":
            v = engine.investment(holder_name)
            if v is None:
                return "warning", scope_label + "Total investment is not available in this report."
            rate = engine.xirr(holder_name)
            msg = scope_label + f"Total investment (cost) is **{rupee(v)}**."
            if rate is not None:
                msg += f"\n\n📈 Growing at XIRR of **{rate:.2f}% per year**."
            return "success", msg

        # ── returns ───────────────────────────────────────────────────────────
        if intent == "returns":
            v = engine.returns(holder_name)
            if v is None:
                return "warning", scope_label + "Return figures are not available in this report."
            x = engine.xirr(holder_name)
            msg = scope_label + f"Overall return since investment: **{rupee(v)}**."
            if x is not None:
                msg += f" (XIRR: **{x:.2f}%**)"
            return "success", msg

        if intent == "xirr":
            x = engine.xirr(holder_name)
            if x is None:
                return "warning", scope_label + "XIRR is not available in this report."
            return "success", scope_label + f"Annualised growth rate (XIRR): **{x:.2f}%**."

        # ── holders ───────────────────────────────────────────────────────────
        if intent == "holder_count":
            n = engine.holder_count()
            if n is None:
                return "warning", "Holder information is not available in this report."
            names = engine.holder_names()
            msg = f"There are **{n} holder(s)** in this family portfolio."
            if names:
                msg += "\n\n" + "\n".join(f"- {name}" for name in names)
            return "success", msg

        if intent == "holder_breakdown":
            df = engine.holder_breakdown(holder_name)
            if df is None:
                return "warning_df", scope_label + "Holder-wise breakdown is not available."
            return "dataframe", df

        # ── projection ────────────────────────────────────────────────────────
        if intent == "projection":
            years = extract_years(question)
            note = ""
            if years is None:
                years = 5
                note = " (default 5-year horizon — no period was specified)"

            proj = engine.project_future_value(years, holder_name=holder_name)
            if proj is None:
                return "warning", scope_label + (
                    "Cannot project — current fund value or XIRR is missing from this report."
                )

            msg = scope_label + (
                f"**Estimated value after {years} year(s){note}:**\n\n"
                f"- Current fund value: {rupee(proj['current_value'])}\n"
                f"- Growth rate (past XIRR): {proj['rate']:.2f}% per year\n"
                f"- **Projected value (existing investment only): {rupee(proj['projected_lumpsum_only'])}**\n"
            )
            if proj["projected_with_sip"] is not None:
                msg += (
                    f"- With active SIP of {rupee(proj['sip_amount'])}/month: "
                    f"**{rupee(proj['projected_with_sip'])}**\n"
                )
            msg += "\n_Past performance is not a guarantee of future returns._"
            return "success", msg

        # ── SIP ───────────────────────────────────────────────────────────────
        if intent == "sip_amount":
            v = engine.sip_amount_total(holder_name)
            if v is None:
                return "warning", scope_label + "No active SIPs found in this report."
            return "success", scope_label + f"Total active SIP amount: **{rupee(v)}** per installment."

        if intent == "sip_dates":
            dates = engine.sip_dates(holder_name)
            if not dates:
                return "warning", scope_label + "No SIP dates found in this report."
            return "success", scope_label + "SIP date(s): " + ", ".join(dates)

        if intent == "sip_banks":
            return "warning", (
                "This report does not contain bank details for SIPs. "
                "Please check your bank mandate / NACH registration with your AMC."
            )

        if intent == "sip_details":
            df = engine.sip_details(holder_name)
            if df is None:
                return "warning_df", scope_label + "No active SIPs found in this report."
            return "dataframe", df

        # ── bank ──────────────────────────────────────────────────────────────
        if intent == "bank":
            result = engine.bank_details()
            if result is None or result == "NOT_AVAILABLE":
                return "warning", (
                    "Bank details are not present in this Excel report. "
                    "Please upload your CAS or a bank-mandate report."
                )
            return "info", result

        if intent == "change_bank":
            return "info", (
                "Changing a registered bank account requires a signed mandate submitted "
                "to the AMC or RTA (CAMS/KFintech) along with a cancelled cheque. "
                "I can help you draft the request — would you like me to?"
            )

        # ── tax ───────────────────────────────────────────────────────────────
        if intent == "tax":
            df_scheme = engine.get_sheet("scheme")
            if df_scheme is not None and not df_scheme.empty:
                scheme_col = engine.find_col(df_scheme, "scheme", "name") or engine.find_col(df_scheme, "scheme")
                val_col = engine.find_col(df_scheme, "current value")
                if scheme_col and val_col:
                    tax_lines = []
                    total_tax = 0.0
                    for _, row in df_scheme.iterrows():
                        name = row[scheme_col]
                        val = float(pd.to_numeric(row[val_col], errors="coerce") or 0.0)
                        if val > 5:
                            tax = engine.calculate_tax_liability(name, val)
                            if tax > 0:
                                tax_lines.append(f"- **{name}**: {rupee(tax)} ltcg tax estimate.")
                                total_tax += tax
                    if total_tax > 0:
                        msg = scope_label + f"Estimated 2026 LTCG tax liability on current holdings is **{rupee(total_tax)}**:\n\n" + "\n".join(tax_lines)
                        return "success", msg

            return "warning", (
                "This valuation report does not include a full capital-gains / tax statement. "
                "Please request a 'Capital Gains Statement' from your AMC/RTA for accurate returns computation."
            )

        # ── dividend ──────────────────────────────────────────────────────────
        if intent == "dividend":
            monthly = engine.monthly_dividend(holder_name)
            if monthly is None:
                return "warning", scope_label + "No dividend transactions found in this report."
            df_out = monthly.reset_index()
            df_out.columns = ["Month", "Dividend Amount"]
            return "dataframe", df_out

        # ── SWP ───────────────────────────────────────────────────────────────
        if intent == "swp":
            monthly = engine.monthly_swp(holder_name)
            if monthly is None:
                return "warning", scope_label + "No SWP transactions found in this report."
            df_out = monthly.reset_index()
            df_out.columns = ["Month", "SWP Amount"]
            return "dataframe", df_out

        # ── service requests ──────────────────────────────────────────────────
        if intent == "increase_sip":
            return "info", (
                "To increase your SIP amount, submit a SIP modification request to your AMC/advisor. "
                "Tell me the scheme and new amount and I'll draft the request for you."
            )

        if intent == "lumpsum":
            return "info", (
                "For a one-time (lumpsum) investment, let me know the scheme/fund and amount, "
                "and I can help you draft the purchase instruction."
            )

        if intent == "advice_returns":
            return "info", (
                "Returns improve over time through: staying invested long-term, increasing SIP amounts "
                "periodically (step-up SIP), reviewing underperforming funds, and maintaining the right "
                "equity-debt mix. For a personalised plan, consult your financial advisor."
            )

        # ── raw tables ────────────────────────────────────────────────────────
        if intent == "transactions":
            df = engine.transactions(holder_name)
            if df is None or df.empty:
                return "warning_df", "No transaction data found."
            return "dataframe", df

        if intent == "folios":
            df = engine.folios(holder_name)
            if df is None or df.empty:
                return "warning_df", "No folio-wise data found."
            return "dataframe", df

        return "warning", "Sorry, I don't have data to answer that question yet."


    def render_answer(question):
        kind, payload = answer(question, engine)
        st.markdown(f"**You asked:** {question}")

        if kind == "success":
            st.success(payload)
            try:
                nice = ask_llama(question, payload)
                if nice and nice.strip() != payload.strip():
                    st.write(nice)
            except Exception:
                pass
        elif kind == "info":
            st.info(payload)
        elif kind in ("warning", "warning_df"):
            st.warning(payload)
        elif kind == "dataframe":
            st.dataframe(payload)


    # ── FAQ buttons ───────────────────────────────────────────────────────────
    FAQ_QUESTIONS = [
        "How many holders are in my family portfolio",
        "Show each member's portfolio breakdown",
        "My SIP amount",
        "My SIP dates",
        "My fund value",
        "My total investment",
        "My family overall returns since investment",
        "What is my portfolio's XIRR",
        "What will be my amount after 5 years",
        "What will be Sonal's amount after 10 years",
        "What will be Harshesh's amount after 5 years",
        "My monthly total dividend amount",
        "My monthly SWP amount",
        "My banks in each SIP",
        "Want to increase SIP amount",
        "Want to invest one time amount",
        "How to increase investment return",
        "Want to change bank",
        "My family income tax statement for last financial year",
    ]

    st.markdown("##### 💬 Frequently Asked Questions")
    st.caption("Click a question below for an instant answer, or type your own below.")

    cols_faq = st.columns(3)
    for i, faq in enumerate(FAQ_QUESTIONS):
        with cols_faq[i % 3]:
            if st.button(faq, key=f"faq_{i}", use_container_width=True):
                st.session_state["pending_question"] = faq

    st.markdown("")

    question = st.text_input(
        "Or type your own question",
        value=st.session_state.get("pending_question", ""),
        key="question_input",
    )

    ask_clicked = st.button("Ask", type="primary")

    if ask_clicked and question:
        render_answer(question)
        st.session_state["pending_question"] = ""
    elif st.session_state.get("pending_question"):
        render_answer(st.session_state["pending_question"])
        st.session_state["pending_question"] = "" 