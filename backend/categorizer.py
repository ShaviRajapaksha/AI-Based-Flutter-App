import re

# keyword-based categorizer
KEYWORDS = {
    "EXPENSES": [
        r"grocery|supermarket|food|restaurant|dining|coffee|fuel|petrol|diesel|bus|train|uber|lyft|electric|water|internet|rent|insurance|medical|pharmacy|clothes|education|tuition|subscription|netflix|spotify",
    ],
    "SAVINGS": [
        r"savings|deposit|fd|fixed\s*deposit|recurring\s*deposit|transfer\s*to\s*savings|piggy|emergency\s*fund",
    ],
    "INVESTMENTS": [
        r"stock|share|mutual\s*fund|mf|etf|bond|treasury|crypto|bitcoin|property|real\s*estate|broker|ipo",
    ],
    "DEBT": [
        r"loan|emi|mortgage|debt|credit\s*card|card\s*payment|overdraft|lease",
    ],
}

DEFAULT_TYPE = "EXPENSES"

def guess_type(vendor: str | None, notes: str | None, category: str | None):
    haystack = " ".join([s for s in [vendor, notes, category] if s]).lower()
    for t, patterns in KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, haystack):
                return t
    return DEFAULT_TYPE