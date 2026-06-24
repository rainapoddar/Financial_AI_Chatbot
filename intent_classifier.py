import re

# ── known holders (add more aliases here as needed) ──────────────────────────
HOLDER_ALIASES = {
    "HARSHESH JAYANTIBHAI PATEL": [
        "harshesh", "harsheshbhai", "mr. harshesh", "mr harshesh",
        "husband", "my account",
    ],
    "SONALBEN HARSESH PATEL": [
        "sonal", "sonalben", "mrs. sonal", "mrs sonal",
        "wife", "sonal account",
    ],
}


def detect_member(question: str):
    """
    Returns the full holder name if a family member is mentioned,
    or None for a family-wide question.
    """
    q = question.lower()
    for full_name, aliases in HOLDER_ALIASES.items():
        if any(alias in q for alias in aliases):
            return full_name
    return None


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