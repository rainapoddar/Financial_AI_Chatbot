import re


def detect_member(question: str, holder_names: list = None):
    """
    Dynamically detects which family member is being referred to in a question.

    Args:
        question:     The raw user question string.
        holder_names: List of holder name strings extracted from the uploaded
                      Excel (e.g. engine.holder_names()). If None or empty,
                      returns None (family-wide scope).

    Returns:
        The full holder name string (as it appears in the Excel) if a member
        is mentioned, or None for a family-wide question.

    Strategy:
        1. Check each word / token in the question against every holder name.
           A match is found when ANY token from the question appears as a
           contiguous sub-word of a holder name (case-insensitive).
        2. Among all matches, return the one with the longest matching token
           to prefer "Harshesh Patel" over "Patel" when both holders share
           the surname.
    """
    if not holder_names:
        return None

    q_lower = question.lower()

    # Tokenise the question into meaningful words (≥3 chars, alpha only)
    q_tokens = [t for t in re.findall(r"[a-z]+", q_lower) if len(t) >= 3]

    best_match = None
    best_len = 0

    for full_name in holder_names:
        name_lower = full_name.lower()
        # Split holder name into individual word tokens
        name_parts = name_lower.split()

        for q_tok in q_tokens:
            for part in name_parts:
                # Match if the question token is fully contained in a name part
                if q_tok in part and len(q_tok) > best_len:
                    best_match = full_name
                    best_len = len(q_tok)

    return best_match


def detect_intent(question: str) -> str:
    """
    Order matters: more specific phrases must be checked BEFORE the generic
    single-keyword ones.
    """
    q = question.lower().strip()

    # ── holders / family members ──────────────────────────────────────────────
    if ("how many" in q and ("holder" in q or "member" in q or "people" in q)):
        return "holder_count"

    if (
        ("each" in q or "every" in q or "wise" in q or "breakdown" in q or "individual" in q)
        and ("holder" in q or "member" in q or "portfolio" in q)
    ):
        return "holder_breakdown"

    if "holder" in q or "family member" in q or "members" in q:
        return "holder_breakdown"

    # ── future value / projection ─────────────────────────────────────────────
    if any(
        phrase in q
        for phrase in [
            "after", "future value", "fv of", "projected", "projection",
            "grow to", "become after", "worth after",
        ]
    ) and ("year" in q or "yr" in q):
        return "projection"

    # ── service requests ──────────────────────────────────────────────────────
    if "increase" in q and "sip" in q:
        return "increase_sip"

    if "change" in q and "bank" in q:
        return "change_bank"

    if ("one time" in q or "lumpsum" in q or "lump sum" in q) and (
        "invest" in q or "amount" in q
    ):
        return "lumpsum"

    if "increase" in q and "return" in q:
        return "advice_returns"

    # ── SIP ───────────────────────────────────────────────────────────────────
    if "sip" in q and ("date" in q or "dates" in q):
        return "sip_dates"

    if "sip" in q and "bank" in q:
        return "sip_banks"

    if "sip" in q and ("amount" in q or "amt" in q):
        return "sip_amount"

    if "sip" in q:
        return "sip_details"

    # ── bank / tax / dividend / swp ───────────────────────────────────────────
    if "bank" in q:
        return "bank"

    if "tax" in q:
        return "tax"

    if "dividend" in q:
        return "dividend"

    if "swp" in q:
        return "swp"

    # ── financials ────────────────────────────────────────────────────────────
    if "return" in q:
        return "returns"

    if "fund value" in q or ("fund" in q and "value" in q):
        return "fund_value"

    if "investment" in q or "invested" in q:
        return "investment"

    if "xirr" in q:
        return "xirr"

    # ── raw report lookups ────────────────────────────────────────────────────
    if "transaction" in q:
        return "transactions"

    if "folio" in q:
        return "folios"

    return "search"