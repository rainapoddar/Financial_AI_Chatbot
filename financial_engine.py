import pandas as pd


class FinancialEngine:

    def __init__(self, tables):
        self.tables = tables

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def get_sheet(self, name):
        for sheet, df in self.tables.items():
            if name.lower() in sheet.lower():
                return df
        return None

    def find_col(self, df, *keywords):
        if df is None:
            return None
        for col in df.columns:
            cl = str(col).lower()
            if all(k.lower() in cl for k in keywords):
                return col
        return None

    def numeric(self, df, col):
        if df is None or col is None or col not in df.columns:
            return pd.Series(dtype=float)
        return pd.to_numeric(df[col], errors="coerce").fillna(0)

    def is_empty(self, df):
        return df is None or df.empty

    # ------------------------------------------------------------------
    # MEMBER FILTER HELPER  ← NEW
    # ------------------------------------------------------------------
    def filter_by_holder(self, df, holder_name=None):
        """
        If holder_name is given, keep only rows where the Holder Name column
        contains that string (case-insensitive). Returns df unchanged if
        holder_name is None or no name column is found.
        """
        if holder_name is None or df is None:
            return df
        name_col = self.find_col(df, "holder", "name")
        if name_col is None:
            # try just "holder"
            name_col = self.find_col(df, "holder")
        if name_col is None:
            return df
        mask = df[name_col].astype(str).str.upper().str.contains(
            holder_name.upper(), na=False
        )
        return df[mask].copy()

    # ------------------------------------------------------------------
    # FUND VALUE / INVESTMENT / RETURNS
    # ------------------------------------------------------------------
    def fund_value(self, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("holder"), holder_name)
        col = self.find_col(df, "current value")
        if self.is_empty(df) or col is None:
            return None
        return float(self.numeric(df, col).sum())

    def investment(self, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("holder"), holder_name)
        col = self.find_col(df, "cost of investment")
        if self.is_empty(df) or col is None:
            return None
        return float(self.numeric(df, col).sum())

    def returns(self, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("holder"), holder_name)
        if self.is_empty(df):
            return None
        notional_col = self.find_col(df, "notional", "p/l")
        booked_col   = self.find_col(df, "booked",   "p/l")
        notional = self.numeric(df, notional_col).sum() if notional_col else 0
        booked   = self.numeric(df, booked_col).sum()   if booked_col   else 0
        if notional_col is None and booked_col is None:
            return None
        return float(notional + booked)

    # ------------------------------------------------------------------
    # XIRR  (weighted by current value per holder)
    # ------------------------------------------------------------------
    def xirr(self, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("holder"), holder_name)
        if self.is_empty(df):
            return None
        xirr_col  = self.find_col(df, "xirr")
        value_col = self.find_col(df, "current value")
        if xirr_col is None:
            return None
        xirr_vals = self.numeric(df, xirr_col)
        if value_col is None:
            vals = xirr_vals[xirr_vals != 0]
            return float(vals.mean()) if len(vals) else None
        weights      = self.numeric(df, value_col)
        total_weight = weights.sum()
        if total_weight == 0:
            vals = xirr_vals[xirr_vals != 0]
            return float(vals.mean()) if len(vals) else None
        return float((xirr_vals * weights).sum() / total_weight)

    # ------------------------------------------------------------------
    # HOLDER INFO
    # ------------------------------------------------------------------
    def holder_count(self):
        df = self.get_sheet("holder")
        name_col = self.find_col(df, "holder", "name")
        if self.is_empty(df) or name_col is None:
            return None
        names = df[name_col].astype(str).str.strip()
        names = names[(names != "") & (names.str.lower() != "nan")]
        return int(names.nunique())

    def holder_names(self):
        df = self.get_sheet("holder")
        name_col = self.find_col(df, "holder", "name")
        if self.is_empty(df) or name_col is None:
            return None
        names = df[name_col].astype(str).str.strip()
        names = names[(names != "") & (names.str.lower() != "nan")]
        return list(dict.fromkeys(names))

    def holder_breakdown(self, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("holder"), holder_name)
        if self.is_empty(df):
            return None
        name_col    = self.find_col(df, "holder", "name")
        cost_col    = self.find_col(df, "cost of investment")
        value_col   = self.find_col(df, "current value")
        notional_col= self.find_col(df, "notional", "p/l")
        booked_col  = self.find_col(df, "booked",   "p/l")
        xirr_col    = self.find_col(df, "xirr")
        sip_col     = self.find_col(df, "sip")
        if name_col is None:
            return None
        out = df[[name_col]].copy()
        out.columns = ["Holder Name"]
        if cost_col:  out["Investment"]     = self.numeric(df, cost_col)
        if value_col: out["Current Value"]  = self.numeric(df, value_col)
        if cost_col and value_col:
            out["Return"] = out["Current Value"] - out["Investment"]
        elif notional_col or booked_col:
            n = self.numeric(df, notional_col) if notional_col else 0
            b = self.numeric(df, booked_col)   if booked_col   else 0
            out["Return"] = n + b
        if xirr_col: out["XIRR (%)"]   = self.numeric(df, xirr_col)
        if sip_col:  out["SIP Amount"] = self.numeric(df, sip_col)
        out = out[out["Holder Name"].astype(str).str.strip() != ""]
        out = out[out["Holder Name"].astype(str).str.lower() != "nan"]
        return out.reset_index(drop=True) if not out.empty else None

    # ------------------------------------------------------------------
    # FUTURE VALUE PROJECTION
    # ------------------------------------------------------------------
    def project_future_value(self, years, holder_name=None, monthly_sip_topup=None):
        current_value = self.fund_value(holder_name)
        rate          = self.xirr(holder_name)
        if current_value is None or rate is None:
            return None
        r = rate / 100.0
        projected_lumpsum = current_value * ((1 + r) ** years)
        result = {
            "current_value":           current_value,
            "rate":                    rate,
            "years":                   years,
            "projected_lumpsum_only":  projected_lumpsum,
            "projected_with_sip":      None,
            "sip_amount":              None,
        }
        sip_amount = monthly_sip_topup
        if sip_amount is None:
            sip_amount = self.sip_amount_total(holder_name)
        if sip_amount:
            n_months     = years * 12
            monthly_rate = r / 12.0
            if monthly_rate > 0:
                sip_fv = sip_amount * (
                    (((1 + monthly_rate) ** n_months) - 1) / monthly_rate
                ) * (1 + monthly_rate)
            else:
                sip_fv = sip_amount * n_months
            result["sip_amount"]        = sip_amount
            result["projected_with_sip"]= projected_lumpsum + sip_fv
        return result

    # ------------------------------------------------------------------
    # SIP
    # ------------------------------------------------------------------
    def _clean_sip_df(self, holder_name=None):
        df = self.get_sheet("active sip")
        if df is None:
            df = self.get_sheet("sip")
        df = self.filter_by_holder(df, holder_name)
        if self.is_empty(df):
            return None
        amt_col = self.find_col(df, "amount")
        if amt_col is None:
            return None
        cleaned = df.copy()
        cleaned[amt_col] = pd.to_numeric(cleaned[amt_col], errors="coerce")
        cleaned = cleaned[cleaned[amt_col].notna() & (cleaned[amt_col] > 0)]
        return cleaned if not cleaned.empty else None

    def sip_details(self, holder_name=None):
        return self._clean_sip_df(holder_name)

    def sip_amount_total(self, holder_name=None):
        df = self._clean_sip_df(holder_name)
        if df is None:
            return None
        amt_col = self.find_col(df, "amount")
        return float(pd.to_numeric(df[amt_col], errors="coerce").sum())

    def sip_dates(self, holder_name=None):
        df = self._clean_sip_df(holder_name)
        if df is None:
            return None
        date_col = self.find_col(df, "sip", "date")
        if date_col is None:
            return None
        return sorted(set(df[date_col].astype(str).str.strip()) - {"", "nan"})

    # ------------------------------------------------------------------
    # BANK
    # ------------------------------------------------------------------
    def bank_details(self):
        for df in self.tables.values():
            if self.find_col(df, "bank"):
                return None
        return "NOT_AVAILABLE"

    # ------------------------------------------------------------------
    # TRANSACTIONS / FOLIOS
    # ------------------------------------------------------------------
    def transactions(self, holder_name=None):
        df = self.get_sheet("transaction")
        return self.filter_by_holder(df, holder_name)

    def folios(self, holder_name=None):
        df = self.get_sheet("folio")
        return self.filter_by_holder(df, holder_name)

    # ------------------------------------------------------------------
    # DIVIDEND / SWP
    # ------------------------------------------------------------------
    def _transactions_by_type(self, *type_keywords, holder_name=None):
        df = self.filter_by_holder(self.get_sheet("transaction"), holder_name)
        if self.is_empty(df):
            return None
        type_col = self.find_col(df, "transaction")
        date_col = self.find_col(df, "date")
        amt_col  = self.find_col(df, "amount")
        if not all([type_col, date_col, amt_col]):
            return None
        mask = df[type_col].astype(str).str.lower().apply(
            lambda v: any(k in v for k in type_keywords)
        )
        rows = df[mask].copy()
        if rows.empty:
            return None
        rows[amt_col]  = pd.to_numeric(rows[amt_col], errors="coerce").fillna(0)
        rows["_month"] = pd.to_datetime(
            rows[date_col], errors="coerce", dayfirst=True
        ).dt.to_period("M")
        return rows, date_col, amt_col

    def monthly_dividend(self, holder_name=None):
        result = self._transactions_by_type("div", holder_name=holder_name)
        if result is None:
            return None
        rows, _, amt_col = result
        return rows.groupby("_month")[amt_col].sum().sort_index()

    def monthly_swp(self, holder_name=None):
        result = self._transactions_by_type("swp", holder_name=holder_name)
        if result is None:
            return None
        rows, _, amt_col = result
        return rows.groupby("_month")[amt_col].sum().sort_index()

    # ------------------------------------------------------------------
    # TAX
    # ------------------------------------------------------------------
    def tax_statement(self):
        return None 
    def calculate_tax_liability(self, scheme_name: str, current_value: float) -> float:
        """
        Calculate tax on Long Term Capital Gain (LTCG) for MFs.
        - If equity (>65%) and held > 1 year: Tax only on gain above ₹1 lakh @ 10%.
        - All other cases: Tax is ₹0 (Debt, Hybrid, or Short Term).
        """
        # 1. Get Scheme Type (Equity / Debt / Hybrid)
        mf_type = self.get_scheme_type(scheme_name)
        if mf_type is None:
            return 0.0  # Can't calculate tax if we don't know the type

        # 2. Check Equity Threshold (>65% assets)
        is_equity_heavy = (mf_type.lower() == "equity")
        is_debt_or_hybrid = (mf_type.lower() in ["debt", "hybrid"])

        # 3. Check Holding Period
        # We need to know the purchase date to determine long-term vs short-term.
        # User query asks for "tax for 2026", implying we look at current holdings.
        # For this logic, we assume current holdings in equity funds are Long Term
        # unless specified otherwise, OR we check the 'type' column if it denotes LTCG.
        
        # Check if the fund is classified as Long Term Equity in the Excel
        is_ltcg_fund = False
        if is_equity_heavy:
            # Look for 'LTCG' status in the fund details
            df = self.get_sheet("fund details")
            if df is not None:
                col_name = self.find_col(df, "name")
                col_ltcg = self.find_col(df, "ltcg", "tax")
                if col_name and col_ltcg:
                    fund_row = df[df[col_name].astype(str).str.lower() == scheme_name.lower()]
                    if not fund_row.empty:
                        status = str(fund_row.iloc[0][col_ltcg]).lower()
                        if "ltcg" in status or "long term" in status:
                            is_ltcg_fund = True

        # 4. Calculate Tax
        tax_amount = 0.0
        
        # Condition for Tax: Equity + Long Term
        if is_ltcg_fund:
            # User asked for tax for 2026. 
            # If current_value is the value on Jan 1 2026 (start of year), tax applies on gains above 1L.
            # If current_value is today, we assume the user wants to know the tax on the gain *up to* this point.
            gain = current_value - self.get_investment_amount(scheme_name)
            
            if gain > 100000:
                taxable_gain = gain - 100000
                tax_amount = taxable_gain * 0.10  # 10% tax on LTCG
        
        # Debt/Hybrid or Short Term Equity: No tax
        else:
            tax_amount = 0.0
            
        return round(tax_amount, 2) 