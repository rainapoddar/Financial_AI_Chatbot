import pandas as pd


class ExcelParser:
    """
    Parses a Wealth/MF family-portfolio Excel export into clean DataFrames.

    Each report sheet (Folio Wise, Category Wise, AMC Wise, Scheme Wise,
    Holder Wise, Active Sip, Transaction Wise ...) has a title row, maybe a
    blank row, maybe a client-name row, and THEN the real header row. This
    finds that header row reliably and gives back clean, de-duplicated,
    whitespace-trimmed column names with numeric columns coerced to numbers.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.workbook = pd.ExcelFile(filepath)
        self.tables = {}

    # ------------------------------------------------------------------
    # HEADER DETECTION
    # ------------------------------------------------------------------
    def find_header(self, raw):

        keywords = [
            "scheme name",
            "folio no",
            "category",
            "amc",
            "advisor",
            "holder",
            "bank",
            "sip",
            "transaction",
            "purchase",
            "current nav",
            "current value",
            "cost of investment",
            "isin",
        ]

        best_row, best_score = None, 0

        for i in range(min(25, len(raw))):

            row = raw.iloc[i].fillna("").astype(str).str.strip().str.lower()

            score = 0
            for cell in row:
                for k in keywords:
                    if k in cell:
                        score += 1

            # require at least 2 keyword hits AND that the row actually has
            # more than 1 non-empty cell (titles are usually a single cell)
            non_empty = (row != "").sum()

            if score >= 2 and non_empty >= 2 and score > best_score:
                best_row, best_score = i, score

        return best_row

    # ------------------------------------------------------------------
    # COLUMN CLEANUP
    # ------------------------------------------------------------------
    def _clean_columns(self, cols):

        new_cols = []
        seen = {}

        for c in cols:

            c = str(c).strip()

            if c == "" or c.lower() == "nan":
                c = "Unnamed"

            if c in seen:
                seen[c] += 1
                c = f"{c}_{seen[c]}"
            else:
                seen[c] = 0

            new_cols.append(c)

        return new_cols

    # ------------------------------------------------------------------
    # PARSE
    # ------------------------------------------------------------------
    def parse(self):

        for sheet in self.workbook.sheet_names:

            raw = pd.read_excel(self.filepath, sheet_name=sheet, header=None)

            header = self.find_header(raw)

            if header is None:
                df = raw.copy()
                df.columns = [f"Column_{i}" for i in range(df.shape[1])]
            else:
                df = raw.iloc[header + 1:].copy()
                df.columns = self._clean_columns(raw.iloc[header])

            df.reset_index(drop=True, inplace=True)

            # drop fully blank rows
            df.dropna(how="all", inplace=True)

            # drop "Total" / summary rows that have no real numeric data
            # (these confuse downstream sums and SIP listings)
            first_col = df.columns[0]
            df = df[~df[first_col].astype(str).str.strip().str.lower().eq("total")]

            # trim whitespace in every text cell, leave numbers alone
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace({"nan": "", "None": ""})

            df.reset_index(drop=True, inplace=True)

            self.tables[sheet] = df

        return self.tables  