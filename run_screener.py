import os
import requests
from bs4 import BeautifulSoup

URL = "https://chartink.com/screener/chartink-dry-up-setup-ready-screener-code-for-oneil-disiple"
PROCESS_URL = "https://chartink.com/screener/process"

def get_watchlist():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Fetch CSRF token and scan clause
    response = session.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]
    scan_clause = soup.find("input", {"id": "scan_clause"})["value"]

    # 2. Query screener process endpoint
    post_headers = {
        **headers,
        "x-csrf-token": csrf_token,
        "Referer": URL
    }
    payload = {"scan_clause": scan_clause}

    res = session.post(PROCESS_URL, data=payload, headers=post_headers)
    data = res.json().get("data", [])

    # 3. Format as TradingView watchlist (NSE:TICKER)
    tickers = [f"NSE:{item['nsecode']}" for item in data if "nsecode" in item]

    output_path = "tv_dryup_watchlist.txt"
    with open(output_path, "w") as f:
        f.write(",\n".join(tickers))

    print(f"Exported {len(tickers)} symbols to {output_path}")
    print(", ".join(tickers))

if __name__ == "__main__":
    get_watchlist()
