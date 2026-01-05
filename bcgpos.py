import yfinance as yf
import wikipediaapi
import pandas as pd
import numpy as np
from pytrends.request import TrendReq

# -----------------------------
# CONFIG
# -----------------------------
HIGH_GROWTH_THRESHOLD = 10.0
HIGH_MARKET_SHARE = 1.0

WIKI_USER_AGENT = "BCGMatrixEstimator/1.0 (contact: research@example.com)"

from yfinance import Search

# -----------------------------
# STEP 0: Resolve ticker + industry keyword automatically (FIXED)
# -----------------------------
def resolve_company_metadata(company_name):
    """
    Uses Yahoo Finance Search API to resolve:
    - ticker
    - industry keyword
    """
    try:
        search = Search(company_name, max_results=5)
        quotes = search.quotes

        if not quotes:
            return None, None

        # Pick first equity result
        for q in quotes:
            if q.get("quoteType") == "EQUITY":
                ticker = q.get("symbol")
                stock = yf.Ticker(ticker)
                info = stock.info

                industry = (
                    info.get("industry")
                    or info.get("sector")
                    or company_name
                )

                return ticker, industry

    except Exception:
        pass

    return None, None

# -----------------------------
# STEP 1: Get company revenue
# -----------------------------
def get_company_revenue(ticker):
    stock = yf.Ticker(ticker)
    fin = stock.financials

    if fin is None or fin.empty:
        return None, None

    try:
        revenue = fin.loc["Total Revenue"].iloc[0]
        prev_revenue = fin.loc["Total Revenue"].iloc[1]
        growth = ((revenue - prev_revenue) / prev_revenue) * 100
        return revenue, growth
    except Exception:
        return None, None


# -----------------------------
# STEP 2: Get competitors (Wikipedia heuristic)
# -----------------------------
def get_competitors(company_name):
    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent=WIKI_USER_AGENT
    )

    page = wiki.page(company_name)
    competitors = []

    if not page.exists():
        return competitors

    text = page.text.lower()
    keywords = ["competitor", "competition", "rival"]

    for line in text.split("\n"):
        if any(k in line for k in keywords):
            words = line.split()
            competitors.extend([w.capitalize() for w in words if w.istitle()])

    competitors = list(set(c for c in competitors if len(c) > 3))
    return competitors[:3]


# -----------------------------
# STEP 3: Industry growth (Google Trends)
# -----------------------------
def get_industry_growth(keyword):
    pytrends = TrendReq(hl="en-US", tz=330)

    try:
        pytrends.build_payload([keyword], timeframe="today 5-y")
        data = pytrends.interest_over_time()

        if data.empty:
            return 5.0

        first = data[keyword].iloc[0]
        last = data[keyword].iloc[-1]

        growth = ((last - first) / max(first, 1)) * 100
        return round(growth / 5, 2)

    except Exception:
        return 5.0


# -----------------------------
# STEP 4: Relative market share
# -----------------------------
def compute_relative_market_share(company_revenue, competitor_revenues):
    if not competitor_revenues:
        return 1.2

    return round(company_revenue / max(competitor_revenues), 2)


# -----------------------------
# STEP 5: BCG Classification
# -----------------------------
def classify_bcg(industry_growth, market_share, revenue_growth):
    """
    Enhanced BCG logic with stricter business performance gate
    """
    # Business severely declining → Dog
    if revenue_growth is not None and revenue_growth < -10:
        return "Dog"

    # Failing but not extremely → Question Mark
    if revenue_growth is not None and revenue_growth < -5:
        if industry_growth >= HIGH_GROWTH_THRESHOLD:
            return "Question Mark"
        else:
            return "Dog"

    # Standard BCG logic
    if industry_growth >= HIGH_GROWTH_THRESHOLD and market_share >= HIGH_MARKET_SHARE:
        return "Star"
    elif industry_growth < HIGH_GROWTH_THRESHOLD and market_share >= HIGH_MARKET_SHARE:
        return "Cash Cow"
    elif industry_growth >= HIGH_GROWTH_THRESHOLD and market_share < HIGH_MARKET_SHARE:
        return "Question Mark"
    else:
        return "Dog"


# -----------------------------
# STEP 6: Confidence score
# -----------------------------
def compute_confidence(growth, market_share):
    growth_conf = min(abs(growth) / 20, 1.0)
    share_conf = min(abs(market_share - 1), 1.0)
    return round((growth_conf + share_conf) / 2, 2)


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def bcg_pipeline(company_name):
    ticker, industry_keyword = resolve_company_metadata(company_name)

    if not ticker:
        return {"error": "Unable to resolve ticker"}

    revenue, rev_growth = get_company_revenue(ticker)
    if revenue is None:
        return {"error": "Financial data unavailable"}

    competitors = get_competitors(company_name)
    competitor_revenues = []

    for comp in competitors:
        try:
            comp_ticker, _ = resolve_company_metadata(comp)
            if not comp_ticker:
                continue

            comp_rev, _ = get_company_revenue(comp_ticker)
            if comp_rev:
                competitor_revenues.append(comp_rev)
        except Exception:
            pass

    relative_share = compute_relative_market_share(revenue, competitor_revenues)
    industry_growth = get_industry_growth(industry_keyword)

    return {
        "company": company_name,
        "ticker": ticker,
        "industry_keyword": industry_keyword,
        "industry_growth_%": industry_growth,
        "revenue_growth_%": round(rev_growth, 2) if rev_growth else None,
        "relative_market_share": relative_share,
        "bcg_position": classify_bcg(industry_growth, relative_share, rev_growth),
        "confidence": compute_confidence(industry_growth, relative_share),
        "assumptions": {
            "industry_growth_source": "Google Trends proxy",
            "market_share": "Revenue-based estimation",
            "competitors_source": "Wikipedia heuristic"
        }
    }


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    result = bcg_pipeline("Nokia")
    print("\nBCG MATRIX OUTPUT\n")
    for k, v in result.items():
        print(f"{k}: {v}")
