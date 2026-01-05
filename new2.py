import yfinance as yf
from yfinance import Search
import wikipediaapi
import requests
import numpy as np
import json


# =============================
# CONFIG
# =============================
# =============================
# OPENROUTER CONFIG (NEW)
# =============================
OPENROUTER_API_KEY = "***"
OPENROUTER_MODEL = "openai/gpt-4o-mini"

OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://academic-bcg-matrix.local",
    "X-Title": "BCG Matrix Validator"
}

ALPHA_VANTAGE_API_KEY = "T0PLWO2O4GKI4TAQ"

HIGH_GROWTH_THRESHOLD = 10.0   # % CAGR
HIGH_MARKET_SHARE = 1.0

WIKI_USER_AGENT = "BCGMatrixEstimator/1.0 (academic-use)"

# Sector → ETF proxy (free & realistic)
SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Consumer Electronics": "XLK",
    "Consumer Defensive": "XLP",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Communication Services": "XLC",
    "Utilities": "XLU"
}

# =============================
# STEP 0: Resolve ticker + sector
# =============================
def resolve_company_metadata(company_name):
    try:
        search = Search(company_name, max_results=5)
        for q in search.quotes:
            if q.get("quoteType") == "EQUITY":
                ticker = q["symbol"]
                info = yf.Ticker(ticker).info
                sector = info.get("sector") or "Technology"
                industry = info.get("industry") or sector
                return ticker, sector, industry
    except Exception:
        pass
    return None, None, None


# =============================
# STEP 1: Revenue growth (Alpha Vantage)
# =============================
def get_revenue_growth_alpha(ticker):
    url = (
        "https://www.alphavantage.co/query"
        f"?function=INCOME_STATEMENT&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    )
    data = requests.get(url).json()

    try:
        reports = data["annualReports"]
        latest = int(reports[0]["totalRevenue"])
        previous = int(reports[1]["totalRevenue"])
        growth = ((latest - previous) / previous) * 100
        return latest, round(growth, 2)
    except Exception:
        return None, None


# =============================
# STEP 2: Sector growth via ETF CAGR
# =============================
def get_sector_growth_alpha(sector):
    etf = SECTOR_ETF_MAP.get(sector, "XLK")

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={etf}&apikey={ALPHA_VANTAGE_API_KEY}"
    )
    data = requests.get(url).json()
    ts = data.get("Monthly Adjusted Time Series", {})

    try:
        dates = sorted(ts.keys())
        start_price = float(ts[dates[0]]["4. close"])
        end_price = float(ts[dates[-1]]["4. close"])
        years = len(dates) / 12
        cagr = ((end_price / start_price) ** (1 / years) - 1) * 100
        return round(cagr, 2)
    except Exception:
        return 5.0


# =============================
# STEP 3: Competitors (Wikipedia heuristic)
# =============================
def get_competitors(company_name):
    wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent=WIKI_USER_AGENT
)

    page = wiki.page(company_name)
    if not page.exists():
        return []

    competitors = []
    for line in page.text.split("\n"):
        if "competitor" in line.lower() or "rival" in line.lower():
            competitors.extend(
                [w for w in line.split() if w.istitle() and len(w) > 3]
            )

    return list(set(competitors))[:3]


# =============================
# STEP 4: Relative market share
# =============================
def compute_relative_market_share(company_revenue, competitors):
    peer_revenues = []

    for comp in competitors:
        ticker, _, _ = resolve_company_metadata(comp)
        if not ticker:
            continue
        rev, _ = get_revenue_growth_alpha(ticker)
        if rev:
            peer_revenues.append(rev)

    if not peer_revenues:
        return 1.2  # conservative default

    return round(company_revenue / max(peer_revenues), 2)


# =============================
# STEP 5: BCG classification
# =============================
def classify_bcg(industry_growth, market_share, revenue_growth):

    # Severe decline override
    if revenue_growth is not None and revenue_growth < -15:
        return "Dog"

    if industry_growth >= HIGH_GROWTH_THRESHOLD and market_share >= HIGH_MARKET_SHARE:
        return "Star"
    elif industry_growth < HIGH_GROWTH_THRESHOLD and market_share >= HIGH_MARKET_SHARE:
        return "Cash Cow"
    elif industry_growth >= HIGH_GROWTH_THRESHOLD and market_share < HIGH_MARKET_SHARE:
        return "Question Mark"
    else:
        return "Dog"


# =============================
# STEP 6: Confidence score
# =============================
def compute_confidence(industry_growth, market_share):
    growth_conf = min(abs(industry_growth) / 20, 1)
    share_conf = min(abs(market_share - 1), 1)
    return round((growth_conf + share_conf) / 2, 2)

# =============================
# STEP 6.5: OpenRouter Validation Layer (NEW)
# =============================
def validate_with_openrouter(bcg_result):
    """
    Uses LLM to validate logical consistency of BCG classification
    """

    prompt = f"""
You are a strategy consultant validating a BCG Matrix classification.

Check for:
- Logical correctness
- Growth vs market share alignment
- Obvious contradictions

Return JSON ONLY:
{{
  "approved": true/false,
  "confidence_adjustment": -0.2 to +0.2,
  "notes": "short explanation"
}}

DATA:
{bcg_result}
"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You validate business strategy outputs."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=20
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return json.loads(content)
  # trusted academic use
    except Exception as e:
        return {
            "approved": False,
            "confidence_adjustment": 0.0,
            "notes": f"Validation skipped: {e}"
        }


# =============================
# MAIN PIPELINE
# =============================
def bcg_pipeline(company_name):
    ticker, sector, industry = resolve_company_metadata(company_name)
    if not ticker:
        return {"error": "Unable to resolve ticker"}

    revenue, revenue_growth = get_revenue_growth_alpha(ticker)
    if revenue is None:
        return {"error": "Revenue data unavailable"}

    industry_growth = get_sector_growth_alpha(sector)
    competitors = get_competitors(company_name)
    relative_share = compute_relative_market_share(revenue, competitors)

    base_result = {
        "company": company_name,
        "ticker": ticker,
        "sector": sector,
        "industry": industry,
        "industry_growth_%": industry_growth,
        "revenue_growth_%": revenue_growth,
        "relative_market_share": relative_share,
        "bcg_position": classify_bcg(
            industry_growth, relative_share, revenue_growth
        ),
        "confidence": compute_confidence(industry_growth, relative_share),
        "assumptions": {
            "industry_growth": "Sector ETF CAGR (Alpha Vantage)",
            "revenue": "Company income statements (Alpha Vantage)",
            "market_share": "Revenue vs largest peer",
            "competitors": "Wikipedia heuristic"
        }
    }

    # 🔍 LLM VALIDATION LAYER
    validation = validate_with_openrouter(base_result)

    if validation.get("approved"):
        base_result["confidence"] = round(
            max(0, min(1, base_result["confidence"] + validation["confidence_adjustment"])),
            2
        )
        base_result["validation"] = {
            "status": "approved",
            "notes": validation["notes"]
        }
    else:
        base_result["validation"] = {
            "status": "warning",
            "notes": validation["notes"]
        }

    return base_result

# =============================
# RUN
# =============================
if __name__ == "__main__":
    result = bcg_pipeline("Blackberry")
    print("\nBCG MATRIX OUTPUT\n")
    for k, v in result.items():
        print(f"{k}: {v}")
