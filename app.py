import os
import re
import json
import base64
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime, timedelta
from excel_parser import ExcelParser
from financial_engine import FinancialEngine
from llm import ask_llama
from intent_classifier import detect_intent, detect_member

st.set_page_config(layout="wide", page_title="Wealth AI Dashboard", page_icon="💼")

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
        color: #FFFFFF !important;
    }
    .subtitle { 
        color: #A3B899 !important;
        font-size: 1.05rem; 
        margin-bottom: 1.5rem; 
        text-align: left; 
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 1.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E88E5;
        padding-left: 0.75rem;
        color: #FFFFFF !important;
    }
    .stButton>button {
        border-radius: 8px; border: 1px solid #D6DEE3;
        background-color: #F6F9FB; color: #0E3A53; font-weight: 500;
        padding: 0.45rem 0.8rem; white-space: normal; text-align: left;
    }
    .stButton>button:hover {
        background-color: #0E3A53; color: white; border-color: #0E3A53;
    }
    .insight-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        color: #1A202C !important;
    }
    .insight-card strong { color: #0E3A53 !important; }
    .insight-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #1A202C !important;
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

    /* ── NEW: Alert Cards (Feature 5) ─────────────────────────────────── */
    .alert-card-green {
        background: linear-gradient(135deg, #F0FFF4, #C6F6D5);
        border-left: 5px solid #38A169;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #22543D;
        font-size: 0.9rem;
    }
    .alert-card-orange {
        background: linear-gradient(135deg, #FFFAF0, #FEEBC8);
        border-left: 5px solid #DD6B20;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #7B341E;
        font-size: 0.9rem;
    }
    .alert-card-red {
        background: linear-gradient(135deg, #FFF5F5, #FED7D7);
        border-left: 5px solid #E53E3E;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #742A2A;
        font-size: 0.9rem;
    }

    /* ── Health Score bar (Feature 1) ─────────────────────────────────── */
    .health-score-circle {
        width: 120px; height: 120px;
        border-radius: 50%;
        background: conic-gradient(#0E3A53 var(--pct), #E2E8F0 0);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 12px auto;
        position: relative;
    }
    .health-score-inner {
        width: 88px; height: 88px;
        border-radius: 50%;
        background: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem; font-weight: 800; color: #0E3A53;
    }

    /* ── Fund Search Cards (Feature 7) ────────────────────────────────── */
    .fund-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .fund-card:hover { border-color: #0E3A53; }

    /* ── Chat Bubbles (Feature 6) ─────────────────────────────────────── */
    .chat-user {
        background: #EBF4FF; border-radius: 12px 12px 2px 12px;
        padding: 10px 14px; margin: 6px 0; margin-left: 30%;
        color: #1A202C; font-size: 0.92rem;
    }
    .chat-bot {
        background: #F7FAFC; border: 1px solid #E2E8F0;
        border-radius: 12px 12px 12px 2px;
        padding: 10px 14px; margin: 6px 0; margin-right: 30%;
        color: #1A202C; font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Currency Format Helpers (UNCHANGED) ──────────────────────────────────────
def rupee(x):
    if x is None:
        return "N/A"
    return f"₹ {x:,.2f}"

def format_currency(x):
    if x is None:
        return "N/A"
    abs_x = abs(x)
    if abs_x >= 10000000:
        return f"₹ {x/10000000:.2f} Cr"
    elif abs_x >= 100000:
        return f"₹ {x/100000:.2f} Lakhs"
    else:
        return f"₹ {x:,.2f}"


# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">💼 Wealth AI — Family Portfolio Dashboard</div>', unsafe_allow_html=True)
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
        # Reset chat memory on new upload
        st.session_state["chat_history"] = []
        st.session_state["chat_context"] = {}
    st.success("✅ Excel parsed successfully")

# ── NEW Tab Definitions (expanded from 6 to 8 tabs) ──────────────────────────
tab1, tab2, tab3, tab4, tab5, tab_health, tab_review, tab_funds, tab_alerts, tab_reports, tab6 = st.tabs([
    "📊 Dashboard",
    "👥 Family",
    "📈 Performance",
    "🧠 AI Insights",
    "🎯 Goal Simulator",
    "❤️ Health Score",      # Feature 1
    "📋 AI Review",          # Feature 2
    "🔍 Fund Search",        # Feature 7
    "🔔 Alerts",             # Feature 5
    "📄 Reports",            # Feature 4
    "💬 Chatbot",
])

# ── Guard: no file uploaded yet ───────────────────────────────────────────────
if "engine" not in st.session_state:
    for _tab in [tab1, tab2, tab3, tab4, tab5, tab_health, tab_review, tab_funds, tab_alerts, tab_reports]:
        with _tab:
            st.info("Please upload your Family Portfolio Excel file above to view this section.")
    with tab6:
        st.header("💬 Ask the Financial Chatbot")
        st.info("Please upload your Family Portfolio Excel file above to start chatting.")
    st.stop()

# ── Shared state ──────────────────────────────────────────────────────────────
engine = st.session_state["engine"]
tables = st.session_state["tables"]

# Initialise chat memory if not present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "chat_context" not in st.session_state:
    st.session_state["chat_context"] = {}

# Pre-compute shared values (UNCHANGED)
total_val = engine.fund_value()
total_inv = engine.investment()
total_gain = engine.returns()
total_xirr = engine.xirr()
total_ret_pct = (total_gain / total_inv * 100) if total_inv and total_inv > 0 else 0.0
top_df, bottom_df = engine.get_fund_performance()
alloc = engine.get_asset_allocation()
sip_total = engine.sip_amount_total()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: PORTFOLIO HEALTH SCORE  (Feature 1)
# ═══════════════════════════════════════════════════════════════════════════════
def compute_health_score(engine, alloc, total_val, total_inv, top_df, bottom_df, sip_total):
    """
    Dynamically computes a 0-100 Portfolio Health Score from 5 sub-metrics.
    Returns dict with score, sub_scores, explanation.
    """
    scores = {}

    # 1. Diversification (0-20): penalise if 1 fund > 30% or < 4 funds
    df_scheme = engine.get_sheet("scheme")
    num_funds = 0
    max_fund_pct = 0.0
    if df_scheme is not None and not df_scheme.empty:
        val_col = engine.find_col(df_scheme, "current value")
        if val_col:
            fund_vals = pd.to_numeric(df_scheme[val_col], errors="coerce").fillna(0)
            fund_vals = fund_vals[fund_vals > 5]
            num_funds = len(fund_vals)
            if total_val and total_val > 0:
                max_fund_pct = float(fund_vals.max() / total_val * 100) if not fund_vals.empty else 0.0

    if num_funds >= 10 and max_fund_pct < 20:
        div_score = 20
    elif num_funds >= 6 and max_fund_pct < 30:
        div_score = 15
    elif num_funds >= 3:
        div_score = 10
    else:
        div_score = 5
    scores["Diversification"] = (div_score, 20)

    # 2. Risk Balance (0-20): ideal = 60-75% equity, adequate debt
    eq_pct = alloc.get("Equity", 0) / total_val * 100 if total_val else 0
    db_pct = alloc.get("Debt", 0) / total_val * 100 if total_val else 0
    if 50 <= eq_pct <= 80 and db_pct >= 10:
        risk_score = 20
    elif 40 <= eq_pct <= 85 and db_pct >= 5:
        risk_score = 15
    elif eq_pct > 90:
        risk_score = 8
    else:
        risk_score = 12
    scores["Risk Balance"] = (risk_score, 20)

    # 3. Returns (0-20): scored on XIRR relative to 12% benchmark
    xirr = engine.xirr() or 0
    if xirr >= 15:
        ret_score = 20
    elif xirr >= 12:
        ret_score = 17
    elif xirr >= 8:
        ret_score = 13
    elif xirr >= 5:
        ret_score = 8
    else:
        ret_score = 4
    scores["Returns"] = (ret_score, 20)

    # 4. Tax Efficiency (0-20): equity-heavy portfolio = tax efficient
    if eq_pct >= 65:
        tax_score = 18
    elif eq_pct >= 50:
        tax_score = 14
    else:
        tax_score = 10
    scores["Tax Efficiency"] = (tax_score, 20)

    # 5. Liquidity (0-20): SIP active + no over-concentration in illiquid
    liq_score = 10
    if sip_total and sip_total > 0:
        liq_score += 5
    if db_pct >= 10:
        liq_score += 5
    scores["Liquidity"] = (min(liq_score, 20), 20)

    total_score = sum(v[0] for v in scores.values())

    explanation_parts = []
    if div_score < 15:
        explanation_parts.append(f"Spread investments across more funds to reduce single-fund risk ({num_funds} funds detected).")
    if risk_score < 15:
        explanation_parts.append(f"Your equity allocation ({eq_pct:.0f}%) is {'very high' if eq_pct > 85 else 'lower than ideal'}; consider rebalancing.")
    if ret_score < 13:
        explanation_parts.append(f"XIRR of {xirr:.1f}% is below the 12% benchmark — review underperforming funds.")
    if not explanation_parts:
        explanation_parts.append("Portfolio is well-diversified, returns are healthy, and risk balance is appropriate.")

    return {
        "total": total_score,
        "sub_scores": scores,
        "explanation": " ".join(explanation_parts)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: GENERATE SMART ALERTS  (Feature 5)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_alerts(engine, alloc, total_val, total_inv, top_df, bottom_df, sip_total):
    """Returns list of (level, icon, title, message) alert tuples."""
    alerts = []

    # Upcoming SIP (green)
    if sip_total and sip_total > 0:
        sip_dates = engine.sip_dates()
        date_str = ", ".join(sip_dates) if sip_dates else "scheduled dates"
        alerts.append(("green", "📅", "Upcoming SIP Instalment",
                        f"Your monthly SIP of {rupee(sip_total)} is active. Ensure sufficient bank balance by {date_str}."))

    # Negative returns (red)
    if not bottom_df.empty:
        neg_funds = bottom_df[bottom_df["Return %"] < 0]
        if not neg_funds.empty:
            worst = neg_funds.iloc[0]
            alerts.append(("red", "📉", "Negative Return Detected",
                            f"{worst['Fund Name']} has a negative return of {worst['Return %']:.1f}%. Consider reviewing this holding."))

    # High concentration (orange)
    df_scheme = engine.get_sheet("scheme")
    if df_scheme is not None and total_val and total_val > 0:
        val_col = engine.find_col(df_scheme, "current value")
        scheme_col = engine.find_col(df_scheme, "scheme", "name") or engine.find_col(df_scheme, "scheme")
        if val_col and scheme_col:
            fund_vals = pd.to_numeric(df_scheme[val_col], errors="coerce").fillna(0)
            idx_max = fund_vals.idxmax()
            max_pct = fund_vals[idx_max] / total_val * 100
            if max_pct > 30:
                fname = df_scheme.loc[idx_max, scheme_col] if idx_max in df_scheme.index else "Unknown"
                alerts.append(("orange", "⚠️", "Concentration Risk",
                                f"{fname} accounts for {max_pct:.1f}% of your portfolio — above the 30% safe limit."))

    # High equity exposure (orange)
    eq_pct = alloc.get("Equity", 0) / total_val * 100 if total_val else 0
    if eq_pct > 85:
        alerts.append(("orange", "📊", "High Equity Exposure",
                        f"Equity allocation stands at {eq_pct:.1f}%. High returns potential but significant volatility risk."))

    # Inactive / low-value funds (orange)
    if df_scheme is not None:
        val_col = engine.find_col(df_scheme, "current value")
        scheme_col = engine.find_col(df_scheme, "scheme", "name") or engine.find_col(df_scheme, "scheme")
        if val_col and scheme_col:
            inactive = df_scheme[pd.to_numeric(df_scheme[val_col], errors="coerce").fillna(0) < 5]
            if not inactive.empty:
                n = len(inactive)
                alerts.append(("orange", "💤", f"{n} Inactive / Redeemed Fund(s)",
                                "Some fund entries have negligible balance (< ₹5). Consider removing from tracking."))

    # SWP alert (green)
    monthly_swp = engine.monthly_swp()
    if monthly_swp is not None and not monthly_swp.empty:
        swp_total = monthly_swp.iloc[-1] if len(monthly_swp) > 0 else 0
        alerts.append(("green", "💸", "Active SWP Detected",
                        f"SWP withdrawal of approx. {rupee(swp_total)} detected. Ensure corpus is sufficient."))

    # Tax saving reminder (green) — Q4 reminder after October
    month_now = datetime.now().month
    if month_now >= 10 or month_now <= 3:
        alerts.append(("green", "🧾", "Tax Saving Window",
                        "Q4 is approaching — consider reviewing ELSS investments to maximise Section 80C benefits before March 31."))

    # Low diversification (red)
    if not top_df.empty:
        num_active = len(top_df) + len(bottom_df)
        if num_active < 4:
            alerts.append(("red", "🗂️", "Under-Diversified Portfolio",
                            f"Only {num_active} active funds detected. Broaden exposure to reduce concentration risk."))

    return alerts


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: DETECT CHART INTENT FOR CHATBOT  (Feature 3)
# ═══════════════════════════════════════════════════════════════════════════════
def detect_chart_intent(question: str) -> str | None:
    """Returns chart type key or None."""
    q = question.lower()
    if any(k in q for k in ["allocation", "asset mix", "equity", "debt", "hybrid"]):
        return "allocation_pie"
    if any(k in q for k in ["compare", "family", "member", "each member", "all member"]):
        return "member_comparison"
    if any(k in q for k in ["best fund", "top fund", "best performing", "worst fund", "bottom fund"]):
        return "fund_performance"
    if any(k in q for k in ["growth", "portfolio growth", "history", "historical"]):
        return "portfolio_growth"
    return None


def render_chart_for_question(chart_key, engine, alloc, total_val, top_df, bottom_df):
    """Renders the appropriate Plotly chart for the chat context."""
    if chart_key == "allocation_pie":
        labels, vals, colors_map = [], [], {"Equity": "#0E3A53","Debt": "#2E7D32","Hybrid": "#FF8F00","Other": "#757575"}
        for k, v in alloc.items():
            if v > 0:
                labels.append(k); vals.append(v)
        if vals:
            fig = go.Figure(data=[go.Pie(labels=labels, values=vals, hole=0.45,
                marker=dict(colors=[colors_map[l] for l in labels]), textinfo='percent+label')])
            fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    elif chart_key == "member_comparison":
        member_data = engine.get_member_comparison()
        if member_data:
            members = [m["Member"] for m in member_data]
            values = [m["Portfolio Value"] for m in member_data]
            investments = [m["Investment"] for m in member_data]
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Portfolio Value', x=members, y=values, marker_color='#0E3A53'))
            fig.add_trace(go.Bar(name='Invested Cost', x=members, y=investments, marker_color='#A2B5CD'))
            fig.update_layout(barmode='group', height=320, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    elif chart_key == "fund_performance":
        if not top_df.empty:
            fig = px.bar(top_df, x='Return %', y='Fund Name', orientation='h',
                color_discrete_sequence=['#2E7D32'], text='Return %')
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    elif chart_key == "portfolio_growth":
        growth_df = engine.get_portfolio_growth_series()
        if not growth_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=growth_df['Month'], y=growth_df['Current Value'],
                mode='lines', name='Market Value', line=dict(color='#0E3A53', width=3)))
            fig.add_trace(go.Scatter(x=growth_df['Month'], y=growth_df['Invested Amount'],
                mode='lines', name='Invested Cost', line=dict(color='#A2B5CD', width=2, dash='dash')))
            fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: BUILD PDF REPORT HTML  (Feature 4)
# ═══════════════════════════════════════════════════════════════════════════════
def build_report_html(engine, total_val, total_inv, total_gain, total_ret_pct, total_xirr,
                       alloc, top_df, bottom_df, sip_total, member_data, health):
    """Returns styled HTML string for PDF/print report."""
    now = datetime.now().strftime("%d %B %Y")

    alloc_rows = ""
    total_alloc = sum(alloc.values())
    for k, v in alloc.items():
        if v > 0:
            pct = v / total_alloc * 100 if total_alloc else 0
            alloc_rows += f"<tr><td>{k}</td><td>{format_currency(v)}</td><td>{pct:.1f}%</td></tr>"

    top_fund_rows = ""
    if not top_df.empty:
        for _, r in top_df.head(5).iterrows():
            top_fund_rows += f"<tr><td>{r['Fund Name']}</td><td>{format_currency(r['Current Value'])}</td><td>{r['Return %']:.2f}%</td><td>{r['XIRR']:.2f}%</td></tr>"

    member_rows = ""
    for m in member_data:
        member_rows += f"<tr><td>{m['Member']}</td><td>{format_currency(m['Portfolio Value'])}</td><td>{format_currency(m['Investment'])}</td><td>{m['Return %']:.1f}%</td><td>{m['XIRR %']:.1f}%</td></tr>"

    health_rows = ""
    for metric, (score, out_of) in health["sub_scores"].items():
        pct = int(score / out_of * 100)
        health_rows += f"<tr><td>{metric}</td><td>{score}/{out_of}</td><td><div style='background:#E2E8F0;border-radius:4px;height:10px;width:100%'><div style='background:#0E3A53;width:{pct}%;height:10px;border-radius:4px'></div></div></td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset='utf-8'>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1A202C; margin: 40px; font-size: 13px; }}
        h1 {{ color: #0E3A53; border-bottom: 3px solid #0E3A53; padding-bottom: 8px; }}
        h2 {{ color: #0E3A53; margin-top: 32px; border-left: 4px solid #1E88E5; padding-left: 10px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 16px 0; }}
        .kpi-card {{ background: #F7FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; text-align: center; }}
        .kpi-value {{ font-size: 1.4rem; font-weight: 800; color: #0E3A53; }}
        .kpi-label {{ font-size: 0.8rem; color: #718096; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th {{ background: #0E3A53; color: white; padding: 8px 12px; text-align: left; font-size: 12px; }}
        td {{ padding: 7px 12px; border-bottom: 1px solid #E2E8F0; font-size: 12px; }}
        tr:nth-child(even) {{ background: #F7FAFC; }}
        .score-big {{ font-size: 3rem; font-weight: 800; color: #0E3A53; text-align: center; }}
        .footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid #E2E8F0; color: #718096; font-size: 11px; text-align: center; }}
        .insight-box {{ background: #EBF8FF; border-left: 4px solid #3182CE; padding: 12px 16px; border-radius: 4px; margin: 12px 0; font-size: 12px; }}
    </style>
    </head>
    <body>
    <h1>💼 Family Portfolio Report</h1>
    <p style="color:#718096">Generated on {now} | Wealth AI Dashboard</p>

    <h2>Portfolio Health Score</h2>
    <div class="score-big">{health['total']} / 100</div>
    <table>{health_rows}</table>
    <div class="insight-box">{health['explanation']}</div>

    <h2>Key Financial Metrics</h2>
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-value">{format_currency(total_val)}</div><div class="kpi-label">Portfolio Value</div></div>
        <div class="kpi-card"><div class="kpi-value">{format_currency(total_inv)}</div><div class="kpi-label">Total Invested</div></div>
        <div class="kpi-card"><div class="kpi-value">{format_currency(total_gain)}</div><div class="kpi-label">Total Gain</div></div>
        <div class="kpi-card"><div class="kpi-value">{total_ret_pct:.2f}%</div><div class="kpi-label">Returns</div></div>
        <div class="kpi-card"><div class="kpi-value">{total_xirr:.2f}%</div><div class="kpi-label">XIRR</div></div>
        <div class="kpi-card"><div class="kpi-value">{rupee(sip_total) if sip_total else 'N/A'}</div><div class="kpi-label">Monthly SIP</div></div>
    </div>

    <h2>Family Member Summary</h2>
    <table>
        <tr><th>Member</th><th>Portfolio Value</th><th>Invested</th><th>Return %</th><th>XIRR %</th></tr>
        {member_rows}
    </table>

    <h2>Asset Allocation</h2>
    <table>
        <tr><th>Asset Class</th><th>Value</th><th>Weight</th></tr>
        {alloc_rows}
    </table>

    <h2>Top 5 Performing Funds</h2>
    <table>
        <tr><th>Fund Name</th><th>Current Value</th><th>Return %</th><th>XIRR %</th></tr>
        {top_fund_rows}
    </table>

    <div class="footer">
        This report is for informational purposes only and does not constitute financial advice.<br/>
        Generated by Wealth AI Dashboard · {now}
    </div>
    </body>
    </html>
    """
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Pre-compute new feature data
# ─────────────────────────────────────────────────────────────────────────────
health = compute_health_score(engine, alloc, total_val, total_inv, top_df, bottom_df, sip_total)
alerts = generate_alerts(engine, alloc, total_val, total_inv, top_df, bottom_df, sip_total)
member_data = engine.get_member_comparison()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: DASHBOARD (unchanged Portfolio Summary)
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">📊 Portfolio Summary Dashboard</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Total Portfolio Value", value=format_currency(total_val),
                  help="Current market valuation of all investments.")
    with col2:
        st.metric(label="Total Invested Cost", value=format_currency(total_inv),
                  help="Initial principal investment amount.")
    with col3:
        st.metric(label="Total Gain / Loss", value=format_currency(total_gain),
                  delta=f"{'+' if total_gain >= 0 else ''}{total_gain/total_inv*100:.2f}%" if total_inv else None,
                  help="Net absolute capital gain/loss.")
    with col4:
        st.metric(label="Portfolio Returns %", value=f"{total_ret_pct:.2f}%",
                  help="Absolute cumulative return rate.")
    with col5:
        st.metric(label="Portfolio XIRR %",
                  value=f"{total_xirr:.2f}%" if total_xirr is not None else "N/A",
                  help="Weighted internal rate of return reflecting annualized performance.")

    # Quick summary mini-cards row
    st.markdown("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"""<div class="insight-card"><strong>❤️ Health Score</strong><br/>
        <span style="font-size:1.6rem;font-weight:800;color:#0E3A53">{health['total']}/100</span><br/>
        <span style="font-size:0.8rem;color:#718096">{health['explanation'][:90]}...</span></div>""",
        unsafe_allow_html=True)
    with d2:
        active_alerts = len(alerts)
        red_count = sum(1 for a in alerts if a[0] == "red")
        color = "#C53030" if red_count > 0 else "#DD6B20" if active_alerts > 2 else "#22543D"
        st.markdown(f"""<div class="insight-card"><strong>🔔 Active Alerts</strong><br/>
        <span style="font-size:1.6rem;font-weight:800;color:{color}">{active_alerts}</span><br/>
        <span style="font-size:0.8rem;color:#718096">{red_count} critical · {active_alerts-red_count} advisory</span></div>""",
        unsafe_allow_html=True)
    with d3:
        sip_str = rupee(sip_total) if sip_total else "Not detected"
        st.markdown(f"""<div class="insight-card"><strong>💳 Monthly SIP</strong><br/>
        <span style="font-size:1.6rem;font-weight:800;color:#0E3A53">{sip_str}</span><br/>
        <span style="font-size:0.8rem;color:#718096">Active monthly commitment</span></div>""",
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: FAMILY (unchanged Member & Allocation)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown('<div class="section-header">👥 Family Member Allocation</div>', unsafe_allow_html=True)
        if member_data:
            members = [m["Member"] for m in member_data]
            values = [m["Portfolio Value"] for m in member_data]
            investments = [m["Investment"] for m in member_data]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name='Portfolio Value', x=members, y=values,
                marker_color='#0E3A53', hovertemplate="Value: ₹%{y:,.2f}<extra></extra>"))
            fig_bar.add_trace(go.Bar(name='Invested Cost', x=members, y=investments,
                marker_color='#A2B5CD', hovertemplate="Cost: ₹%{y:,.2f}<extra></extra>"))
            fig_bar.update_layout(barmode='group', height=320,
                margin=dict(l=10,r=10,t=10,b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Amount (₹)'))
            st.plotly_chart(fig_bar, use_container_width=True)

            m_cols = st.columns(len(member_data))
            for idx, m in enumerate(member_data):
                with m_cols[idx]:
                    gain_color = "#2F855A" if m['Gain'] >= 0 else "#C53030"
                    st.markdown(
                        f"""<div style="background-color:#F7FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px;text-align:center;color:#1A202C;">
                            <strong style="color:#0E3A53;font-size:0.9rem;">{m['Member']}</strong><br/>
                            <span style="font-size:0.8rem;color:#4A5568;">Value: <strong>{format_currency(m['Portfolio Value'])}</strong></span><br/>
                            <span style="font-size:0.8rem;color:#4A5568;">Cost: <strong>{format_currency(m['Investment'])}</strong></span><br/>
                            <span style="font-size:0.8rem;color:#4A5568;">Return: <strong style="color:{gain_color};">{m['Return %']:.1f}%</strong></span>
                        </div>""", unsafe_allow_html=True)
        else:
            st.info("No member details detected.")

    with c_right:
        st.markdown('<div class="section-header">📊 Asset Class Allocation</div>', unsafe_allow_html=True)
        labels, vals, colors_map = [], [], {"Equity":"#0E3A53","Debt":"#2E7D32","Hybrid":"#FF8F00","Other":"#757575"}
        for k, v in alloc.items():
            if v > 0:
                labels.append(k); vals.append(v)
        if vals:
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, values=vals, hole=0.45,
                marker=dict(colors=[colors_map[l] for l in labels]),
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Value: ₹%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
            )])
            fig_pie.update_layout(showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=10,r=10,t=10,b=10), height=320,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
            alloc_df = pd.DataFrame({"Asset Class": labels, "Current Value": [rupee(v) for v in vals],
                "Weight %": [f"{v/sum(vals)*100:.2f}%" for v in vals]})
            st.dataframe(alloc_df, hide_index=True, use_container_width=True)
        else:
            st.info("No asset class breakdown available.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: PERFORMANCE (unchanged Fund Performance)
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    c_perf, c_growth = st.columns(2)

    with c_perf:
        st.markdown('<div class="section-header">🏆 Top & Bottom Performing Funds</div>', unsafe_allow_html=True)
        if not top_df.empty:
            tab_top, tab_bottom = st.tabs(["🟢 Top 5 Performing Funds", "🔴 Bottom 5 Performing Funds"])
            with tab_top:
                fig_top = px.bar(top_df, x='Return %', y='Fund Name', orientation='h',
                    color_discrete_sequence=['#2E7D32'], text='Return %')
                fig_top.update_traces(texttemplate='%{text:.1f}%', textposition='inside',
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<extra></extra>")
                fig_top.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False), yaxis=dict(autorange="reversed", title=''))
                st.plotly_chart(fig_top, use_container_width=True)
            with tab_bottom:
                fig_bot = px.bar(bottom_df, x='Return %', y='Fund Name', orientation='h',
                    color_discrete_sequence=['#C62828'], text='Return %')
                fig_bot.update_traces(texttemplate='%{text:.1f}%', textposition='inside',
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<extra></extra>")
                fig_bot.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False), yaxis=dict(autorange="reversed", title=''))
                st.plotly_chart(fig_bot, use_container_width=True)

            perf_combined = pd.concat([top_df, bottom_df.sort_values(by="Return %", ascending=False)]).drop_duplicates().reset_index(drop=True)
            perf_combined_disp = perf_combined.copy()
            perf_combined_disp["Current Value"] = perf_combined_disp["Current Value"].apply(rupee)
            perf_combined_disp["Invested Amount"] = perf_combined_disp["Invested Amount"].apply(rupee)
            perf_combined_disp["Return %"] = perf_combined_disp["Return %"].apply(lambda r: f"{r:.2f}%")
            perf_combined_disp["XIRR"] = perf_combined_disp["XIRR"].apply(lambda x: f"{x:.2f}%")
            with st.expander("🔎 View Performance Details Table"):
                st.dataframe(perf_combined_disp, hide_index=True, use_container_width=True)
        else:
            st.info("No mutual scheme data found to calculate performance.")

    with c_growth:
        st.markdown('<div class="section-header">📈 Portfolio Value Growth Over Time</div>', unsafe_allow_html=True)
        growth_df = engine.get_portfolio_growth_series()
        if not growth_df.empty:
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Scatter(x=growth_df['Month'], y=growth_df['Current Value'],
                mode='lines', name='Market Value', line=dict(color='#0E3A53', width=3),
                hovertemplate="Market Value: ₹%{y:,.2f}<extra></extra>"))
            fig_growth.add_trace(go.Scatter(x=growth_df['Month'], y=growth_df['Invested Amount'],
                mode='lines', name='Invested Cost', line=dict(color='#A2B5CD', width=2, dash='dash'),
                hovertemplate="Invested Cost: ₹%{y:,.2f}<extra></extra>"))
            fig_growth.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Amount (₹)'))
            st.plotly_chart(fig_growth, use_container_width=True)
            st.caption("ℹ️ Portfolio value history estimated based on chronological transaction records.")
        else:
            st.info("No transaction history available to generate portfolio growth charts.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: AI INSIGHTS (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">🧠 AI Insights & Warnings</div>', unsafe_allow_html=True)

    insights = []
    warnings_list = []

    if not top_df.empty:
        best_fund = top_df.iloc[0]
        insights.append(f"🌟 <strong>Best Performing Fund</strong>: <strong>{best_fund['Fund Name']}</strong> yielding a cumulative return of <strong>{best_fund['Return %']:.2f}%</strong>.")
    if not bottom_df.empty:
        worst_fund = bottom_df.iloc[0]
        insights.append(f"⚠️ <strong>Worst Performing Fund</strong>: <strong>{worst_fund['Fund Name']}</strong> with a return of <strong>{worst_fund['Return %']:.2f}%</strong>.")

    df_scheme = engine.get_sheet("scheme")
    if df_scheme is not None and not df_scheme.empty:
        scheme_col = engine.find_col(df_scheme, "scheme","name") or engine.find_col(df_scheme, "scheme")
        val_col = engine.find_col(df_scheme, "current value")
        if scheme_col and val_col:
            df_sc = df_scheme.copy()
            df_sc["ValNum"] = pd.to_numeric(df_sc[val_col], errors="coerce").fillna(0)
            df_sc = df_sc.sort_values(by="ValNum", ascending=False).reset_index(drop=True)
            if not df_sc.empty and df_sc.loc[0,"ValNum"] > 0:
                highest_fund = df_sc.loc[0, scheme_col]
                highest_val = df_sc.loc[0, "ValNum"]
                insights.append(f"🏆 <strong>Highest Value Holding</strong>: <strong>{highest_fund}</strong> representing <strong>{format_currency(highest_val)}</strong>.")
                pct_share = (highest_val / total_val * 100) if total_val else 0.0
                if pct_share > 30.0:
                    warnings_list.append(f"⚠️ <strong>Concentration Risk Warning</strong>: <strong>{highest_fund}</strong> constitutes <strong>{pct_share:.1f}%</strong> of your total portfolio value.")

    if sip_total:
        insights.append(f"💵 <strong>Savings Rate</strong>: You have an active monthly SIP of <strong>{rupee(sip_total)}</strong>.")
    insights.append(f"📈 <strong>Family Return Summary</strong>: Overall return: <strong>{total_ret_pct:.2f}%</strong> | XIRR: <strong>{total_xirr:.2f}%</strong>.")

    if total_val and total_val > 0:
        eq_pct = alloc.get("Equity", 0) / total_val * 100
        db_pct = alloc.get("Debt", 0) / total_val * 100
        hb_pct = alloc.get("Hybrid", 0) / total_val * 100
        insights.append(f"💼 <strong>Asset Allocation Mix</strong>: Equity {eq_pct:.1f}% | Debt {db_pct:.1f}% | Hybrid {hb_pct:.1f}%.")
        if eq_pct > 80.0:
            warnings_list.append(f"📈 <strong>Aggressive Equity Bias</strong>: <strong>{eq_pct:.1f}%</strong> equity allocation.")
        elif db_pct < 10.0:
            warnings_list.append(f"🛡️ <strong>Low Debt Cushion</strong>: Debt allocation is only <strong>{db_pct:.1f}%</strong>.")

    i_left, i_right = st.columns(2)
    with i_left:
        st.markdown('<div class="insight-header">💡 Key Portfolio Insights</div>', unsafe_allow_html=True)
        for ins in insights:
            st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)
    with i_right:
        st.markdown('<div class="insight-header">⚠️ Risk & Diversification Warnings</div>', unsafe_allow_html=True)
        if warnings_list:
            for warn in warnings_list:
                st.markdown(f"""<div style="background-color:#FFF5F5;border-left:4px solid #E53E3E;padding:12px;margin-bottom:12px;border-radius:0 8px 8px 0;font-size:0.9rem;color:#9B2C2C;">{warn}</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background-color:#F0FFF4;border-left:4px solid #38A169;padding:15px;border-radius:0 8px 8px 0;font-size:0.9rem;color:#22543D;">✅ <strong>Healthy Diversification</strong>: No high concentration warnings detected.</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: GOAL SIMULATOR (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">🎯 Interactive Goal Projection Simulator</div>', unsafe_allow_html=True)
    st.caption("Plan your financial goals using Monte Carlo simulation.")

    default_rate = float(f"{total_xirr:.1f}") if total_xirr and total_xirr > 0 else 12.0
    default_sip = float(sip_total) if sip_total else 20000.0

    sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
    with sim_col1:
        target_amt = st.number_input("Target Goal Amount (₹)", min_value=50000.0, step=100000.0, value=10000000.0, format="%f")
        st.caption(f"Target: **{format_currency(target_amt)}**")
    with sim_col2:
        expected_rate = st.slider("Expected Annual Return %", min_value=2.0, max_value=30.0, value=default_rate, step=0.5)
    with sim_col3:
        monthly_sip_sim = st.number_input("Monthly SIP Contribution (₹)", min_value=0.0, step=1000.0, value=default_sip, format="%f")
        st.caption(f"Monthly: **{rupee(monthly_sip_sim)}**")
    with sim_col4:
        horizon_years = st.slider("Investment Horizon (Years)", min_value=1, max_value=40, value=10, step=1)

    include_curr_portfolio = st.checkbox(
        f"Include current portfolio valuation ({format_currency(total_val)}) as starting lump sum", value=True)

    with st.spinner("Calculating probability distributions..."):
        proj_df, expected_fv, prob_success, yrs_req = engine.simulate_goal_probability(
            target_amount=target_amt, expected_return_pct=expected_rate,
            monthly_sip=monthly_sip_sim, years=horizon_years, include_current=include_curr_portfolio)

    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric(label="Future Expected Value (Median)", value=format_currency(expected_fv))
    with res_col2:
        if yrs_req is not None:
            delta_str = "Exceeds Horizon" if yrs_req > horizon_years else None
            st.metric(label="Years to Reach Target", value=f"{yrs_req} Years",
                      delta=delta_str, delta_color="inverse" if delta_str else "normal")
        else:
            st.metric(label="Years to Reach Target", value="Unreachable")
    with res_col3:
        badge_class = "badge-success" if prob_success >= 70 else "badge-warning" if prob_success >= 40 else "badge-danger"
        badge_label = "🟢 High" if prob_success >= 70 else "🟡 Moderate" if prob_success >= 40 else "🔴 Low"
        st.metric(label="Goal Success Probability", value=f"{prob_success:.1f}%")
        st.markdown(f'<span class="badge {badge_class}">{badge_label} Success Probability</span>', unsafe_allow_html=True)

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=proj_df['Date'], y=proj_df['Conservative (25th)'],
        mode='lines', line=dict(width=0.5, color='rgba(239,68,68,0.5)'), showlegend=False))
    fig_proj.add_trace(go.Scatter(x=proj_df['Date'], y=proj_df['Optimistic (75th)'],
        mode='lines', line=dict(width=0.5, color='rgba(16,185,129,0.5)'),
        fill='tonexty', fillcolor='rgba(14,58,83,0.05)', name='Market Variance Range (25th–75th %ile)'))
    fig_proj.add_trace(go.Scatter(x=proj_df['Date'], y=proj_df['Median (50th)'],
        mode='lines', name='Expected Value (Median)', line=dict(color='#0E3A53', width=3)))
    fig_proj.add_trace(go.Scatter(x=[proj_df['Date'].min(), proj_df['Date'].max()],
        y=[target_amt, target_amt], mode='lines', name='Target Goal',
        line=dict(color='#EF4444', width=2, dash='dash')))
    fig_proj.update_layout(title='Wealth Projection Path Chart', height=350,
        margin=dict(l=10,r=10,t=40,b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', title='Valuation (₹)'))
    st.plotly_chart(fig_proj, use_container_width=True)

    with st.expander("Detected Sheets (for verification)"):
        for sheet, df in tables.items():
            st.subheader(sheet)
            st.write("Columns:", df.columns.tolist())
            st.dataframe(df.head())


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: HEALTH SCORE  (Feature 1 — NEW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_health:
    st.markdown('<div class="section-header">❤️ Portfolio Health Score</div>', unsafe_allow_html=True)

    h_left, h_right = st.columns([1, 2])

    with h_left:
        score = health["total"]
        score_pct = score / 100 * 360
        # Colour: green ≥75, orange ≥50, red <50
        color = "#38A169" if score >= 75 else "#DD6B20" if score >= 50 else "#E53E3E"
        grade = "Excellent" if score >= 85 else "Good" if score >= 70 else "Fair" if score >= 50 else "Needs Attention"

        # SVG dial
        angle = score / 100 * 283  # circumference of circle r=45 ≈ 283
        st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <svg width="160" height="160" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="60" fill="none" stroke="#E2E8F0" stroke-width="14"/>
                <circle cx="80" cy="80" r="60" fill="none" stroke="{color}" stroke-width="14"
                    stroke-dasharray="{angle} 283" stroke-dashoffset="70.75"
                    stroke-linecap="round" transform="rotate(-90 80 80)"/>
                <text x="80" y="76" text-anchor="middle" font-size="26" font-weight="800" fill="{color}">{score}</text>
                <text x="80" y="96" text-anchor="middle" font-size="11" fill="#718096">out of 100</text>
            </svg>
            <div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:4px">{grade}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""<div class="insight-card" style="margin-top:12px">
            <strong>Advisor Note</strong><br/>
            <span style="font-size:0.88rem;color:#4A5568">{health['explanation']}</span>
        </div>""", unsafe_allow_html=True)

    with h_right:
        st.markdown("#### Sub-metric Breakdown")
        metric_icons = {
            "Diversification": "🗂️",
            "Risk Balance": "⚖️",
            "Returns": "📈",
            "Tax Efficiency": "🧾",
            "Liquidity": "💧"
        }
        for metric, (score_val, max_val) in health["sub_scores"].items():
            pct = score_val / max_val
            bar_color = "#38A169" if pct >= 0.75 else "#DD6B20" if pct >= 0.5 else "#E53E3E"
            icon = metric_icons.get(metric, "•")
            st.markdown(f"""
            <div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-weight:600;font-size:0.9rem">{icon} {metric}</span>
                    <span style="font-size:0.85rem;color:#718096">{score_val} / {max_val}</span>
                </div>
                <div style="background:#E2E8F0;border-radius:6px;height:10px">
                    <div style="background:{bar_color};width:{int(pct*100)}%;height:10px;border-radius:6px;transition:width 0.4s"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("#### What Does Each Metric Mean?")
        with st.expander("Learn more"):
            st.markdown("""
- **Diversification** — How spread out your investments are across different funds and sectors.
- **Risk Balance** — Equity/Debt ratio versus your ideal age-based allocation.
- **Returns** — XIRR compared to the 12% long-term benchmark.
- **Tax Efficiency** — Proportion of equity investments benefiting from LTCG tax rates.
- **Liquidity** — Presence of active SIP, short-duration holdings, and debt buffer.
            """)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: AI REVIEW  (Feature 2 — NEW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_review:
    st.markdown('<div class="section-header">📋 AI Portfolio Review</div>', unsafe_allow_html=True)
    st.caption("An automated professional summary of your family portfolio — generated fresh each session.")

    # Build dynamic review points
    review_items = []

    # Portfolio Value
    review_items.append(("✅ Portfolio Value",
        f"Your family's combined portfolio stands at **{format_currency(total_val)}**, representing the current market value of all mutual fund holdings."))

    # Overall Return
    xirr_str = f"{total_xirr:.1f}%" if total_xirr else "N/A"
    ret_quality = "strong" if total_ret_pct > 20 else "moderate" if total_ret_pct > 10 else "below benchmark"
    review_items.append(("✅ Overall Return",
        f"Cumulative return since inception: **{total_ret_pct:.2f}%** ({ret_quality}). Annualized XIRR: **{xirr_str}**."))

    # Best Fund
    if not top_df.empty:
        bf = top_df.iloc[0]
        review_items.append(("✅ Best Performing Fund",
            f"**{bf['Fund Name']}** leads with a return of **{bf['Return %']:.2f}%** (XIRR: {bf['XIRR']:.1f}%), current value {format_currency(bf['Current Value'])}."))

    # Worst Fund
    if not bottom_df.empty:
        wf = bottom_df.iloc[0]
        action = "Consider reviewing or exiting this position." if wf['Return %'] < 0 else "Returns are positive but lag the portfolio average."
        review_items.append(("✅ Worst Performing Fund",
            f"**{wf['Fund Name']}** trails with **{wf['Return %']:.2f}%** return. {action}"))

    # Largest Holding
    df_sc = engine.get_sheet("scheme")
    if df_sc is not None and not df_sc.empty:
        vc = engine.find_col(df_sc, "current value")
        snc = engine.find_col(df_sc, "scheme", "name") or engine.find_col(df_sc, "scheme")
        if vc and snc:
            num_vals = pd.to_numeric(df_sc[vc], errors="coerce").fillna(0)
            if not num_vals.empty:
                idx_m = num_vals.idxmax()
                lg_name = df_sc.loc[idx_m, snc]
                lg_val = num_vals[idx_m]
                lg_pct = lg_val / total_val * 100 if total_val else 0
                review_items.append(("✅ Largest Holding",
                    f"**{lg_name}** is the largest position at {format_currency(lg_val)} ({lg_pct:.1f}% of portfolio)."))

    # Monthly SIP
    if sip_total:
        annual_sip = sip_total * 12
        review_items.append(("✅ Monthly SIP",
            f"Active SIP contributions total **{rupee(sip_total)}/month** ({format_currency(annual_sip)}/year), steadily compounding your wealth."))
    else:
        review_items.append(("✅ Monthly SIP",
            "No active SIP detected. Consider starting a monthly SIP to benefit from rupee cost averaging."))

    # Equity Allocation
    eq_pct = alloc.get("Equity", 0) / total_val * 100 if total_val else 0
    eq_comment = "aggressively growth-oriented" if eq_pct > 80 else "well-balanced for long-term growth" if eq_pct > 60 else "conservative"
    review_items.append(("✅ Equity Allocation",
        f"Equity exposure stands at **{eq_pct:.1f}%** of the portfolio — {eq_comment}."))

    # Diversification Status
    num_funds_active = (len(top_df) + len(bottom_df))
    div_status = "well-diversified" if num_funds_active >= 8 else "moderately diversified" if num_funds_active >= 5 else "under-diversified"
    review_items.append(("✅ Diversification Status",
        f"Portfolio holds **{num_funds_active}+ active funds** — {div_status}. A broader spread reduces single-fund risk."))

    # Concentration Risk
    if lg_pct > 30:
        review_items.append(("⚠️ Concentration Risk",
            f"**{lg_name}** represents **{lg_pct:.1f}%** of the portfolio — above the recommended 30% threshold. Rebalancing is advisable."))
    else:
        review_items.append(("✅ Concentration Risk",
            f"No single fund exceeds 30% of the portfolio. Concentration risk is within acceptable limits."))

    # Suggested Improvement
    suggestions = []
    if total_xirr and total_xirr < 10:
        suggestions.append("Consider switching underperforming funds to better-rated alternatives.")
    if eq_pct > 85:
        suggestions.append("Add a Debt/Hybrid component to reduce volatility.")
    if not sip_total:
        suggestions.append("Start an SIP to benefit from long-term compounding.")
    if not suggestions:
        suggestions.append("Continue current strategy, review annually, and step up SIPs by 10% each year.")
    review_items.append(("💡 Suggested Improvement", " ".join(suggestions)))

    # Render review cards in 2 columns
    col_r1, col_r2 = st.columns(2)
    for i, (label, text) in enumerate(review_items):
        col = col_r1 if i % 2 == 0 else col_r2
        icon_color = "#22543D" if label.startswith("✅") else "#744210" if label.startswith("⚠️") else "#1A365D"
        bg = "#F0FFF4" if label.startswith("✅") else "#FFFAF0" if label.startswith("⚠️") else "#EBF4FF"
        border = "#38A169" if label.startswith("✅") else "#DD6B20" if label.startswith("⚠️") else "#3182CE"
        with col:
            st.markdown(f"""
            <div style="background:{bg};border-left:4px solid {border};border-radius:6px;padding:14px 16px;margin-bottom:12px">
                <div style="font-weight:700;color:{icon_color};font-size:0.9rem;margin-bottom:6px">{label}</div>
                <div style="color:#1A202C;font-size:0.88rem">{text}</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: FUND SEARCH  (Feature 7 — NEW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_funds:
    st.markdown('<div class="section-header">🔍 Fund Explorer</div>', unsafe_allow_html=True)

    # Build a comprehensive fund dataframe from scheme sheet
    df_sc = engine.get_sheet("scheme")
    if df_sc is not None and not df_sc.empty:
        scheme_col = engine.find_col(df_sc, "scheme", "name") or engine.find_col(df_sc, "scheme")
        val_col = engine.find_col(df_sc, "current value")
        cost_col = engine.find_col(df_sc, "cost of investment") or engine.find_col(df_sc, "investment")
        xirr_col = engine.find_col(df_sc, "xirr")
        cat_col = engine.find_col(df_sc, "category")
        amc_col = engine.find_col(df_sc, "amc")

        fund_df = df_sc.copy()
        fund_df["_val"] = pd.to_numeric(fund_df[val_col], errors="coerce").fillna(0) if val_col else 0
        fund_df["_cost"] = pd.to_numeric(fund_df[cost_col], errors="coerce").fillna(0) if cost_col else 0
        fund_df["_xirr"] = pd.to_numeric(fund_df[xirr_col], errors="coerce").fillna(0) if xirr_col else 0
        fund_df["_ret"] = np.where(fund_df["_cost"] > 0,
            (fund_df["_val"] - fund_df["_cost"]) / fund_df["_cost"] * 100, 0)
        fund_df = fund_df[fund_df["_val"] > 5].reset_index(drop=True)

        # Search & Filter controls
        fs_col1, fs_col2, fs_col3 = st.columns([3, 2, 2])
        with fs_col1:
            search_q = st.text_input("🔎 Search funds", placeholder="Type fund name, AMC, or category...")
        with fs_col2:
            sort_by = st.selectbox("Sort by", ["Current Value (High→Low)", "Return % (High→Low)", "XIRR (High→Low)", "Fund Name (A→Z)"])
        with fs_col3:
            min_ret = st.slider("Min Return %", min_value=-50, max_value=200, value=-50)

        # Apply filters
        filtered_df = fund_df.copy()
        if search_q:
            q_lower = search_q.lower()
            mask = filtered_df[scheme_col].astype(str).str.lower().str.contains(q_lower, na=False)
            if amc_col:
                mask |= filtered_df[amc_col].astype(str).str.lower().str.contains(q_lower, na=False)
            if cat_col:
                mask |= filtered_df[cat_col].astype(str).str.lower().str.contains(q_lower, na=False)
            filtered_df = filtered_df[mask]

        filtered_df = filtered_df[filtered_df["_ret"] >= min_ret]

        sort_map = {
            "Current Value (High→Low)": ("_val", False),
            "Return % (High→Low)": ("_ret", False),
            "XIRR (High→Low)": ("_xirr", False),
            "Fund Name (A→Z)": (scheme_col, True)
        }
        sc, asc = sort_map[sort_by]
        filtered_df = filtered_df.sort_values(by=sc, ascending=asc).reset_index(drop=True)

        st.caption(f"Showing **{len(filtered_df)}** of {len(fund_df)} active funds")

        # Render fund cards
        if filtered_df.empty:
            st.info("No funds match your search. Try a different keyword.")
        else:
            for i, row in filtered_df.iterrows():
                fname = row[scheme_col]
                fval = row["_val"]
                fcost = row["_cost"]
                fret = row["_ret"]
                fxirr = row["_xirr"]
                ret_color = "#22543D" if fret >= 0 else "#742A2A"
                fcat = row[cat_col] if cat_col else "N/A"
                famc = row[amc_col] if amc_col else ""

                with st.expander(f"{fname}  —  {format_currency(fval)}  |  {fret:+.1f}%"):
                    dc1, dc2, dc3, dc4 = st.columns(4)
                    dc1.metric("Current Value", format_currency(fval))
                    dc2.metric("Invested", format_currency(fcost))
                    dc3.metric("Return %", f"{fret:.2f}%")
                    dc4.metric("XIRR %", f"{fxirr:.2f}%")

                    # Mini allocation bar
                    if total_val and total_val > 0:
                        alloc_pct = fval / total_val * 100
                        st.markdown(f"""
                        <div style="margin-top:10px">
                            <div style="font-size:0.8rem;color:#718096;margin-bottom:4px">Portfolio Allocation: {alloc_pct:.1f}%</div>
                            <div style="background:#E2E8F0;border-radius:4px;height:8px">
                                <div style="background:#0E3A53;width:{min(alloc_pct,100):.1f}%;height:8px;border-radius:4px"></div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    if famc:
                        st.caption(f"AMC: {famc}  |  Category: {fcat}")
    else:
        st.info("No scheme-wise data found. Please upload a portfolio with a Scheme Wise sheet.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: ALERTS  (Feature 5 — NEW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    st.markdown('<div class="section-header">🔔 Smart Alerts & Notifications</div>', unsafe_allow_html=True)
    st.caption("Automatically generated alerts based on your portfolio data.")

    if not alerts:
        st.success("✅ No alerts at this time. Your portfolio appears to be in good health.")
    else:
        green_alerts = [a for a in alerts if a[0] == "green"]
        orange_alerts = [a for a in alerts if a[0] == "orange"]
        red_alerts = [a for a in alerts if a[0] == "red"]

        if red_alerts:
            st.markdown("#### 🔴 Critical Alerts")
            for _, icon, title, msg in red_alerts:
                st.markdown(f'<div class="alert-card-red"><strong>{icon} {title}</strong><br/>{msg}</div>', unsafe_allow_html=True)

        if orange_alerts:
            st.markdown("#### 🟠 Advisory Alerts")
            for _, icon, title, msg in orange_alerts:
                st.markdown(f'<div class="alert-card-orange"><strong>{icon} {title}</strong><br/>{msg}</div>', unsafe_allow_html=True)

        if green_alerts:
            st.markdown("#### 🟢 Informational")
            for _, icon, title, msg in green_alerts:
                st.markdown(f'<div class="alert-card-green"><strong>{icon} {title}</strong><br/>{msg}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"Alerts generated at {datetime.now().strftime('%d %b %Y %H:%M')} based on uploaded portfolio data.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: REPORTS  (Feature 4 — NEW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_reports:
    st.markdown('<div class="section-header">📄 Portfolio Reports</div>', unsafe_allow_html=True)
    st.caption("Download or print professional reports of your portfolio.")

    rpt_col1, rpt_col2 = st.columns(2)

    # Build the HTML report once
    report_html = build_report_html(
        engine, total_val, total_inv, total_gain, total_ret_pct, total_xirr,
        alloc, top_df, bottom_df, sip_total, member_data, health
    )

    with rpt_col1:
        st.markdown("#### 📊 Complete Portfolio Report")
        st.markdown("Includes: Portfolio Summary, Health Score, Member Breakdown, Asset Allocation, Top Funds, Insights, and Recommendations.")

        # Download HTML as file
        html_bytes = report_html.encode("utf-8")
        b64 = base64.b64encode(html_bytes).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="portfolio_report_{datetime.now().strftime("%Y%m%d")}.html" style="display:inline-block;background:#0E3A53;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-right:8px">⬇️ Download Report (HTML)</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.markdown("&nbsp;")
        # Print button using JS
        print_js = f"""
        <script>
        function printReport() {{
            var w = window.open('', '_blank');
            w.document.write(`{report_html.replace('`', '\\`')}`);
            w.document.close();
            w.focus();
            w.print();
        }}
        </script>
        <button onclick="printReport()" style="background:#1E88E5;color:white;padding:10px 20px;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:14px">🖨️ Print Report</button>
        """
        st.components.v1.html(print_js, height=60)

    with rpt_col2:
        st.markdown("#### 📋 Report Preview")
        st.markdown(f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:20px;color:#1A202C;font-size:0.85rem">
            <h3 style="color:#0E3A53;border-bottom:2px solid #0E3A53;padding-bottom:6px">Portfolio Summary</h3>
            <p>📊 <strong>Portfolio Value:</strong> {format_currency(total_val)}</p>
            <p>💰 <strong>Total Invested:</strong> {format_currency(total_inv)}</p>
            <p>📈 <strong>Total Gain:</strong> {format_currency(total_gain)}</p>
            <p>🔄 <strong>XIRR:</strong> {total_xirr:.2f}%</p>
            <p>❤️ <strong>Health Score:</strong> {health['total']} / 100</p>
            <p>🔔 <strong>Alerts:</strong> {len(alerts)} active</p>
            <p style="color:#718096;font-size:0.75rem;margin-top:12px">Download the full report for complete charts, tables, and fund-level analysis.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📑 Quick Data Export")
    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        if not top_df.empty:
            csv_funds = top_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Top Funds CSV", csv_funds, "top_funds.csv", "text/csv", use_container_width=True)

    with exp2:
        if member_data:
            member_df_exp = pd.DataFrame(member_data)
            csv_members = member_df_exp.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Member Summary CSV", csv_members, "members.csv", "text/csv", use_container_width=True)

    with exp3:
        alloc_df_exp = pd.DataFrame([{"Asset Class": k, "Value": v, "Weight %": v/total_val*100 if total_val else 0} for k, v in alloc.items() if v > 0])
        csv_alloc = alloc_df_exp.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Allocation CSV", csv_alloc, "allocation.csv", "text/csv", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB: CHATBOT  (Feature 3 + Feature 6 — enhanced with smart charts & memory)
# ═══════════════════════════════════════════════════════════════════════════════
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

    # ── Feature 6: Context-aware question resolution ──────────────────────────
    def resolve_question_with_context(question: str) -> str:
        """
        Replaces pronouns (her/his/she/he/their) using chat context.
        Returns enriched question string.
        """
        ctx = st.session_state.get("chat_context", {})
        q = question.lower()
        last_member = ctx.get("last_member")

        # Resolve pronouns to last mentioned member
        pronoun_map = {
            " her ": f" {last_member} ",
            " his ": f" {last_member} ",
            " she ": f" {last_member} ",
            " he ": f" {last_member} ",
            " their ": f" {last_member} ",
            "'s ": f" {last_member} ",
        }
        if last_member:
            for pronoun, replacement in pronoun_map.items():
                if pronoun in f" {q} ":
                    question = re.sub(re.escape(pronoun.strip()), last_member, question, flags=re.IGNORECASE)

        return question

    def update_context(question: str, holder_name):
        """Updates chat context with latest member reference."""
        if holder_name:
            st.session_state["chat_context"]["last_member"] = holder_name

    # ── answer engine (UNCHANGED logic, context-aware wrapper added) ──────────
    def answer(question, engine):
        # Resolve context before detecting intent
        question = resolve_question_with_context(question)

        intent = detect_intent(question)
        # Pass live holder names from the uploaded Excel so detection is
        # fully dynamic — no client-specific aliases are hardcoded.
        _known_holders = engine.holder_names() or []
        holder_name = detect_member(question, _known_holders)

        # Update memory
        update_context(question, holder_name)

        if holder_name:
            scope_label = f"🔍 Answering for **{holder_name}**\n\n"
        else:
            scope_label = "🔍 Answering for **the entire portfolio**\n\n"

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

        if intent == "investment":
            v = engine.investment(holder_name)
            if v is None:
                return "warning", scope_label + "Total investment is not available in this report."
            rate = engine.xirr(holder_name)
            msg = scope_label + f"Total investment (cost) is **{rupee(v)}**."
            if rate is not None:
                msg += f"\n\n📈 Growing at XIRR of **{rate:.2f}% per year**."
            return "success", msg

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

        if intent == "projection":
            years = extract_years(question)
            note = ""
            if years is None:
                years = 5
                note = " (default 5-year horizon — no period was specified)"
            proj = engine.project_future_value(years, holder_name=holder_name)
            if proj is None:
                return "warning", scope_label + "Cannot project — fund value or XIRR is missing."
            msg = scope_label + (
                f"**Estimated value after {years} year(s){note}:**\n\n"
                f"- Current fund value: {rupee(proj['current_value'])}\n"
                f"- Growth rate (past XIRR): {proj['rate']:.2f}% per year\n"
                f"- **Projected value (existing investment only): {rupee(proj['projected_lumpsum_only'])}**\n"
            )
            if proj["projected_with_sip"] is not None:
                msg += (f"- With active SIP of {rupee(proj['sip_amount'])}/month: "
                        f"**{rupee(proj['projected_with_sip'])}**\n")
            msg += "\n_Past performance is not a guarantee of future returns._"
            return "success", msg

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
            return "warning", "This report does not contain bank details for SIPs."

        if intent == "sip_details":
            df = engine.sip_details(holder_name)
            if df is None:
                return "warning_df", scope_label + "No active SIPs found in this report."
            return "dataframe", df

        if intent == "bank":
            result = engine.bank_details()
            if result is None or result == "NOT_AVAILABLE":
                return "warning", "Bank details are not present in this Excel report."
            return "info", result

        if intent == "change_bank":
            return "info", ("Changing a registered bank account requires a signed mandate submitted "
                "to the AMC or RTA (CAMS/KFintech) along with a cancelled cheque.")

        if intent == "tax":
            df_scheme = engine.get_sheet("scheme")
            if df_scheme is not None and not df_scheme.empty:
                scheme_col = engine.find_col(df_scheme, "scheme","name") or engine.find_col(df_scheme, "scheme")
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
                        msg = scope_label + f"Estimated 2026 LTCG tax liability is **{rupee(total_tax)}**:\n\n" + "\n".join(tax_lines)
                        return "success", msg
            return "warning", "Tax statement not available in this report."

        if intent == "dividend":
            monthly = engine.monthly_dividend(holder_name)
            if monthly is None:
                return "warning", scope_label + "No dividend transactions found."
            df_out = monthly.reset_index()
            df_out.columns = ["Month", "Dividend Amount"]
            return "dataframe", df_out

        if intent == "swp":
            monthly = engine.monthly_swp(holder_name)
            if monthly is None:
                return "warning", scope_label + "No SWP transactions found."
            df_out = monthly.reset_index()
            df_out.columns = ["Month", "SWP Amount"]
            return "dataframe", df_out

        if intent == "increase_sip":
            return "info", ("To increase your SIP amount, submit a SIP modification request to your AMC/advisor.")

        if intent == "lumpsum":
            return "info", ("For a one-time (lumpsum) investment, let me know the scheme/fund and amount.")

        if intent == "advice_returns":
            return "info", ("Returns improve through staying invested long-term, increasing SIP amounts "
                "periodically (step-up SIP), reviewing underperforming funds, and maintaining the right equity-debt mix.")

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

    # ── render_answer with smart chart support (Feature 3) ───────────────────
    def render_answer(question):
        kind, payload = answer(question, engine)

        # Feature 6: Display in chat bubble style in history
        st.session_state["chat_history"].append({"role": "user", "content": question})

        st.markdown(f"**You asked:** {question}")

        if kind == "success":
            st.success(payload)
            bot_response = payload
            try:
                nice = ask_llama(question, payload)
                if nice and nice.strip() != payload.strip():
                    st.write(nice)
                    bot_response = nice
            except Exception:
                pass
        elif kind == "info":
            st.info(payload)
            bot_response = payload
        elif kind in ("warning", "warning_df"):
            st.warning(payload)
            bot_response = payload
        elif kind == "dataframe":
            st.dataframe(payload)
            bot_response = "Data table shown above."

        st.session_state["chat_history"].append({"role": "assistant", "content": bot_response})

        # ── Feature 3: Smart chart rendering ─────────────────────────────────
        chart_key = detect_chart_intent(question)
        if chart_key:
            st.markdown("📊 **Visual Summary:**")
            render_chart_for_question(chart_key, engine, alloc, total_val, top_df, bottom_df)

    # ── Feature 6: Show conversation history ─────────────────────────────────
    history = st.session_state.get("chat_history", [])
    if history:
        with st.expander(f"💬 Conversation History ({len(history)//2} exchanges)", expanded=False):
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">🙋 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    short = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                    st.markdown(f'<div class="chat-bot">🤖 {short}</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear History", key="clear_history"):
                st.session_state["chat_history"] = []
                st.session_state["chat_context"] = {}
                st.rerun()

    # ── FAQ buttons (UNCHANGED) ───────────────────────────────────────────────
    # Build FAQ list dynamically using actual holder names from the Excel
    _faq_holders = engine.holder_names() or []
    _member_faqs = []
    for _h in _faq_holders[:3]:  # show up to 3 member-specific projection FAQs
        _first = _h.split()[0].title()  # use first name for readability
        _years = 10 if _faq_holders.index(_h) == 0 else 5
        _member_faqs.append(f"What will be {_first}'s amount after {_years} years")

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
    ] + _member_faqs + [
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