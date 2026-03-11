import requests
import json

OPENROUTER_API_KEY = ""
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

def bcg_product_pipeline(company_name):
    prompt = f"""
You are a top-tier management consultant.

Perform a BCG Matrix analysis at the PRODUCT / BUSINESS UNIT level for the company "{company_name}".

Steps:
1. Identify the major products or business units
2. For EACH product:
   - Define the target market
   - Classify market growth as High or Low
   - Classify relative market share as High or Low
   - Assign ONE BCG quadrant:
     Star, Cash Cow, Question Mark, or Dog
3. Provide a confidence score per product
4. List assumptions clearly

Return STRICT JSON ONLY.
No markdown, no explanations.

Format:

{{
  "company": "...",
  "products": [
    {{
      "product": "...",
      "market": "...",
      "market_growth": "High/Low",
      "relative_market_share": "High/Low",
      "bcg_position": "...",
      "confidence": 0.xx,
      "assumptions": ["...", "..."]
    }}
  ]
}}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a strategy consulting expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Product-Level BCG Matrix"
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)

from bcg_visualize import plot_bcg_matrix

if __name__ == "__main__":
    company = input("Enter company name: ")
    result = bcg_product_pipeline(company)

    print("\nPRODUCT-LEVEL BCG MATRIX\n")
    for p in result["products"]:
        print(f"\nProduct: {p['product']}")
        print(f"Market: {p['market']}")
        print(f"Growth: {p['market_growth']}")
        print(f"Market Share: {p['relative_market_share']}")
        print(f"BCG Position: {p['bcg_position']}")
        print(f"Confidence: {p['confidence']}")

    plot_bcg_matrix(result)
