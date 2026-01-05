"""
BCG Matrix Classifier (Free, Market-Data Driven)

- Industry Growth: Sector ETF CAGR (5Y)
- Market Share: Revenue vs peer average
- No Google Trends, No Wikipedia heuristics
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List


# ---------------------------
# CONFIGURATION
# ---------------------------

SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Consumer Electronics": "XLY",
    "Consumer Discretionary": "XLY",
    "Software - Infrastructure": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI"
}

INDUSTRY_GROWTH_THRESHOLD = 10.0      # % CAGR
MARKET_SHARE_THRESHOLD = 1.0          # Relative share


# ---------------------------
# DATA FETCHING UTILITIES
# ---------------------------

def get_etf_cagr(etf: str, years: int = 5) -> float:
    """Calculate CAGR for sector ETF"""
    hist = yf.Ticker(etf).history(period=f"{years}y")
    if hist.empty:
        return 0.0

    start = hist["Close"].iloc[0]
    end = hist["Close"].iloc[-1]

    cagr = ((end / start) ** (1 / years) - 1) * 100
    return round(cagr, 2)


def get_company_revenue(ticker: str) -> float:
    """Get latest annual revenue"""
    try:
        financials = yf.Ticker(ticker).financials
        return float(financials.loc["Total Revenue"].iloc[0])
    except Exception:
        return 0.0


def get_peer_revenues(ticker: str) -> List[float]:
    """Fetch revenues of peer companies"""
    peers = yf.Ticker(ticker).info.get("peers", [])
    revenues = []

    for peer in peers:
        try:
            rev = get_company_revenue(peer)
            if rev > 0:
                revenues.append(rev)
        except Exception:
            continue

    return revenues


# ---------------------------
# CORE BCG LOGIC
# ---------------------------

def classify_bcg(industry_growth: float, relative_market_share: float) -> str:
    if industry_growth >= INDUSTRY_GROWTH_THRESHOLD and relative_market_share >= MARKET_SHARE_THRESHOLD:
        return "Star"
    if industry_growth < INDUSTRY_GROWTH_THRESHOLD and relative_market_share >= MARKET_SHARE_THRESHOLD:
        return "Cash Cow"
    if industry_growth >= INDUSTRY_GROWTH_THRESHOLD and relative_market_share < MARKET_SHARE_THRESHOLD:
        return "Question Mark"
    return "Dog"


def calculate_confidence(industry_growth: float, peer_count: int) -> float:
    score = 0.0
    if industry_growth > 0:
        score += 0.3
    if peer_count >= 3:
        score += 0.4
    if peer_count >= 5:
        score += 0.3
    return round(min(score, 1.0), 2)


# ---------------------------
# MAIN PIPELINE
# ---------------------------

def bcg_matrix_classifier(
    company: str,
    ticker: str,
    industry_keyword: str
) -> Dict:

    # Industry growth
    etf = SECTOR_ETF_MAP.get(industry_keyword, "SPY")
    industry_growth = get_etf_cagr(etf)

    # Market share
    company_revenue = get_company_revenue(ticker)
    peer_revenues = get_peer_revenues(ticker)

    avg_peer_revenue = np.mean(peer_revenues) if peer_revenues else 0
    relative_market_share = (
        round(company_revenue / avg_peer_revenue, 2)
        if avg_peer_revenue > 0 else 0
    )

    # BCG position
    bcg_position = classify_bcg(industry_growth, relative_market_share)

    # Confidence
    confidence = calculate_confidence(industry_growth, len(peer_revenues))

    return {
        "company": company,
        "ticker": ticker,
        "industry_keyword": industry_keyword,
        "industry_growth_%": industry_growth,
        "relative_market_share": relative_market_share,
        "bcg_position": bcg_position,
        "confidence": confidence,
        "assumptions": {
            "industry_growth_source": f"{etf} 5Y CAGR via yfinance",
            "market_share": "Revenue vs peer average",
            "peers_source": "Yahoo Finance peers list"
        }
    }


# ---------------------------
# EXAMPLE USAGE
# ---------------------------

if __name__ == "__main__":
    result = bcg_matrix_classifier(
        company="BlackBerry",
        ticker="BB",
        industry_keyword="Software - Infrastructure"
    )

    print("\nBCG MATRIX OUTPUT\n")
    for k, v in result.items():
        print(f"{k}: {v}")
