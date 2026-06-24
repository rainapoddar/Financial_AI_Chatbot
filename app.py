import os
import re
import streamlit as st
from excel_parser import ExcelParser
from financial_engine import FinancialEngine
from llm import ask_llama
from intent_classifier import detect_intent, detect_member   # ← detect_member added

st.set_page_config(layout="wide", page_title="Financial AI Chatbot", page_icon="💼")

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2rem; font-weight: 700; color: #0E3A53;
        margin-bottom: 0.2rem;
    }
    .subtitle { color: #5B6B73; font-size: 1rem; margin-bottom: 1.2rem; }
    .stButton>button {
        border-radius: 8px; border: 1px solid #D6DEE3;
        background-color: #F6F9FB; color: #0E3A53; font-weight: 500;
        padding: 0.45rem 0.8rem; white-space: normal; text-align: left;
    }
    .stButton>button:hover {
        background-color: #0E3A53; color: white; border-color: #0E3A53;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">💼 Financial AI Chatbot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Upload your Family Portfolio report and ask anything about your investments.</div>',
    unsafe_allow_html=True,
)

file = st.file_uploader("Upload Family Portfolio (.xlsx)", type=["xlsx"])

if file:
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

    with st.expander("Detected Sheets (for verification)"):
        for sheet, df in tables.items():
            st.subheader(sheet)
            st.write("Columns:", df.columns.tolist())
            st.dataframe(df.head())

st.divider()
st.header("Ask the Financial Chatbot")

if "engine" not in st.session_state:
    st.info("Please upload your Family Portfolio Excel file above to start chatting.")
    st.stop()

engine = st.session_state["engine"]

# ── year extraction ───────────────────────────────────────────────────────────
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


def rupee(x):
    return f"₹ {x:,.2f}"


# ── answer engine ─────────────────────────────────────────────────────────────
def answer(question, engine):
    intent      = detect_intent(question)
    holder_name = detect_member(question)          # ← NEW: who is being asked about?

    # Label shown before every answer so the user knows which scope was used
    if holder_name:
        scope_label = f"🔍 Answering for **{holder_name}**\n\n"
    else:
        scope_label = "🔍 Answering for **the entire family**\n\n"

    # ── fund value ────────────────────────────────────────────────────────────
    if intent == "fund_value":
        v = engine.fund_value(holder_name)
        if v is None:
            return "warning", scope_label + "Current fund value is not available in this report."
        rate = engine.xirr(holder_name)
        msg = scope_label + f"Current fund value is **{rupee(v)}**."
        if rate is not None:
            msg += f"\n\n📈 Growing at an annualised rate (XIRR) of **{rate:.2f}% per year**."
        return "success", msg

    # ── investment ────────────────────────────────────────────────────────────
    if intent == "investment":
        v = engine.investment(holder_name)
        if v is None:
            return "warning", scope_label + "Total investment is not available in this report."
        rate = engine.xirr(holder_name)
        msg = scope_label + f"Total investment (cost) is **{rupee(v)}**."
        if rate is not None:
            msg += f"\n\n📈 Growing at XIRR of **{rate:.2f}% per year**."
        return "success", msg

    # ── returns ───────────────────────────────────────────────────────────────
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

    # ── holders ───────────────────────────────────────────────────────────────
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

    # ── projection ────────────────────────────────────────────────────────────
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

    # ── SIP ───────────────────────────────────────────────────────────────────
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

    # ── bank ──────────────────────────────────────────────────────────────────
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

    # ── tax ───────────────────────────────────────────────────────────────────
    if intent == "tax":
        return "warning", (
            "This valuation report does not include a capital-gains / tax statement. "
            "Please request a 'Capital Gains Statement' from your AMC/RTA."
        )

    # ── dividend ──────────────────────────────────────────────────────────────
    if intent == "dividend":
        monthly = engine.monthly_dividend(holder_name)
        if monthly is None:
            return "warning", scope_label + "No dividend transactions found in this report."
        df_out = monthly.reset_index()
        df_out.columns = ["Month", "Dividend Amount"]
        return "dataframe", df_out

    # ── SWP ───────────────────────────────────────────────────────────────────
    if intent == "swp":
        monthly = engine.monthly_swp(holder_name)
        if monthly is None:
            return "warning", scope_label + "No SWP transactions found in this report."
        df_out = monthly.reset_index()
        df_out.columns = ["Month", "SWP Amount"]
        return "dataframe", df_out

    # ── service requests ──────────────────────────────────────────────────────
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

    # ── raw tables ────────────────────────────────────────────────────────────
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


# ── FAQ buttons ───────────────────────────────────────────────────────────────
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
    "What will be Sonal's amount after 10 years",        # ← new member-specific examples
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

cols = st.columns(3)
for i, faq in enumerate(FAQ_QUESTIONS):
    with cols[i % 3]:
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