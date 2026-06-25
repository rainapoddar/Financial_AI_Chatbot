# 💼 Financial AI Chatbot — Family Portfolio Assistant

A smart, conversational AI chatbot built with **Streamlit** and **LLaMA 3** that reads your family's mutual fund portfolio Excel report and answers any financial question in plain English — instantly.

---

## 🧠 What This Project Does

This chatbot turns a complex Excel portfolio report into a simple chat interface. Instead of manually opening spreadsheets and doing calculations, your client can just **ask questions** and get accurate, data-driven answers in seconds.

---

## 👨‍👩‍👧 Family Member Awareness

The chatbot understands **who** you are asking about:

- Asking about **"Harshesh"**, **"husband"**, or **"my account"** → answers only for **HARSHESH JAYANTIBHAI PATEL**
- Asking about **"Sonal"**, **"Sonalben"**, or **"wife"** → answers only for **SONALBEN HARSESH PATEL**
- No name mentioned → returns **family-level totals**

This means every answer is filtered to the right person automatically — no manual lookups needed.

---

## 💬 What You Can Ask

### Portfolio Summary
- *"What is my fund value?"*
- *"How much have I invested in total?"*
- *"What are my overall returns since investment?"*
- *"What is my portfolio's XIRR?"*
- *"Show each member's portfolio breakdown"*
- *"How many holders are in my family portfolio?"*

### Member-Specific Queries
- *"What is Sonal's current value and returns?"*
- *"What is Harshesh's XIRR?"*
- *"Show Sonalben's portfolio summary"*

### SIP (Systematic Investment Plan)
- *"What is my total SIP amount?"*
- *"What are my SIP dates?"*
- *"Show all my active SIPs"*
- *"What is Harshesh's SIP amount?"*
- *"What is Sonal's SIP amount?"*

### Future Value Projections
- *"What will my portfolio be worth after 10 years?"*
- *"What will Harshesh's amount be after 5 years?"*
- *"What will Sonal's portfolio grow to in 20 years?"*

  The chatbot uses your portfolio's own **XIRR** as the growth rate and projects:
  - Lumpsum (existing investment) future value
  - Combined future value including ongoing SIP contributions

### Transactions & Folios
- *"Show my transactions"*
- *"Show Harshesh's transactions"*
- *"Show my folio-wise data"*

### Dividend & SWP
- *"Show my monthly dividend amount"*
- *"Show my monthly SWP amount"*

### Service Requests & Guidance
- *"I want to increase my SIP amount"*
- *"I want to invest a one-time lumpsum amount"*
- *"How can I increase my investment returns?"*
- *"I want to change my bank"*

### Honest "Not Available" Responses
For data this report type does not contain, the chatbot clearly explains what is missing and where to get it:
- Bank account details → suggests CAS / bank-mandate report
- Income tax / capital gains statement → suggests requesting from AMC/RTA
- SIP bank mandate details → suggests checking NACH registration

---

## 📊 How It Works

```
User uploads Excel (.xlsx)
        ↓
ExcelParser detects header rows and cleans all sheets
        ↓
FinancialEngine reads Holder Wise, Active SIP,
Transaction Wise, Folio Wise, Category Wise, AMC Wise sheets
        ↓
User types or clicks a question
        ↓
detect_member() identifies which family member is being asked about
detect_intent() classifies what type of financial question it is
        ↓
FinancialEngine runs the correct calculation — filtered to that member
        ↓
LLaMA 3 (via Ollama) wraps the computed answer in a natural sentence
        ↓
Answer displayed in Streamlit with success / info / warning styling
```

---

## 📁 Supported Excel Sheets

| Sheet | What It Contains |
|---|---|
| **Holder Wise** | Per-member investment, current value, returns, XIRR, SIP |
| **Active SIP** | All active SIPs with scheme, amount, dates, folio |
| **Folio Wise** | Scheme-level holdings per folio |
| **Category Wise** | Equity / Debt / Balance split |
| **AMC Wise** | Fund house-wise allocation |
| **Scheme Wise** | Individual scheme performance |
| **Transaction Wise** | Full transaction history (purchases, redemptions, SWP, dividends) |

---

## ⚡ Key Features

| Feature | Details |
|---|---|
| **No manual filtering** | Just ask naturally — member detection is automatic |
| **Accurate calculations** | All numbers come directly from your Excel — nothing is guessed or hallucinated |
| **Future projections** | Uses your real XIRR to project lumpsum + SIP value |
| **LLM-powered replies** | LLaMA 3 converts computed facts into friendly, readable sentences |
| **Fallback safety** | If Ollama/LLaMA is not running, the raw computed answer is shown instead — the app never crashes |
| **One-click FAQ buttons** | 19 pre-built questions covering the most common queries |
| **Honest about gaps** | Clearly tells you when data is not in the report instead of making up an answer |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| UI / Web app | Streamlit |
| Excel parsing | Pandas + OpenPyXL |
| Financial calculations | Custom FinancialEngine (Python) |
| AI / Natural language | LLaMA 3 via Ollama (local, free, private) |
| Intent detection | Custom rule-based classifier |
| Member detection | Alias-based name resolver |

---

## 🚀 How to Run

```bash
# 1. Install dependencies
pip install streamlit pandas numpy openpyxl sentence-transformers ollama faiss-cpu python-dotenv

# 2. Pull the LLaMA 3 model (one-time setup)
ollama pull llama3

# 3. Start the app
streamlit run app.py
```

Then open your browser at `http://localhost:8501`, upload your Family Portfolio `.xlsx` file, and start chatting.

---

## 📌 Notes

- The Excel file must be a **Family Portfolio Valuation Report** in the standard format (as exported by CAMS, KFintech, or your advisor's portfolio management software).
- Bank details and capital gains / tax statements are **not part of this report type** — upload a separate CAS or Capital Gains Statement for those queries.
- All data stays **on your machine** — nothing is sent to any external server (LLaMA 3 runs locally via Ollama).

---

*Built by the Financial AI Chatbot team. For support or feature requests, please contact the developer.*               *RAINA PODDAR 2025-2026*   *https://github.com/rainapoddar/Financial_AI_Chatbot.git*  