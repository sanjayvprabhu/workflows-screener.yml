import re
import sys
import requests
from bs4 import BeautifulSoup

SCREENER_URL = "https://chartink.com/screener/chartink-dry-up-setup-ready-screener-code-for-oneil-disiple"
PROCESS_URL = "https://chartink.com/screener/process"

# If dynamic parsing fails, paste your copied scan_clause between the quotes below:
FALLBACK_SCAN_CLAUSE = ""

def get_watchlist():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print("Connecting to Chartink...")
    # 1. Fetch CSRF token from chartink
    resp = session.get(SCREENER_URL, headers=headers, timeout=25)
    if resp.status_code != 200:
        print(f"Error: Failed to load screener page (HTTP {resp.status_code})")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_tag = soup.find("meta", {"name": "csrf-token"})
    if not csrf_tag or not csrf_tag.get("content"):
        print("Error: Could not locate CSRF token. Possible Cloudflare bot block.")
        sys.exit(1)
        
    csrf_token = csrf_tag["content"]

    # 2. Extract scan_clause
    clause = None
    input_tag = soup.find("input", {"id": "scan_clause"}) or soup.find("input", {"name": "scan_clause"})
    if input_tag and input_tag.get("value"):
        clause = input_tag["value"]
    else:
        # Search embedded JavaScript variables
        match = re.search(r'scan_clause["\']?\s*[:=]\s*["\'](.*?)["\']', resp.text)
        if match:
            clause = match.group(1)

    if not clause:
        if FALLBACK_SCAN_CLAUSE.strip():
            print("Using fallback scan clause.")
            clause = FALLBACK_SCAN_CLAUSE.strip()
        else:
            print("Error: Could not extract scan_clause from HTML.")
            print("Inspect Network -> 'process' request -> copy 'scan_clause' into FALLBACK_SCAN_CLAUSE.")
            sys.exit(1)

    # 3. Post to process endpoint
    post_headers = {
        **headers,
        "x-csrf-token": csrf_token,
        "Referer": SCREENER_URL,
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Executing scanner query...")
    api_resp = session.post(PROCESS_URL, data={"scan_clause": clause}, headers=post_headers, timeout=25)
    
    if api_resp.status_code != 200:
        print(f"Error: API returned status {api_resp.status_code}")
        sys.exit(1)

    results = api_resp.json().get("data", [])
    tickers = [f"NSE:{item['nsecode']}" for item in results if "nsecode" in item]

    output_file = "tv_dryup_watchlist.txt"
    with open(output_file, "w") as f:
        f.write(",\n".join(tickers))

    print(f"Success: Exported {len(tickers)} symbols to {output_file}")
    if tickers:
        print(", ".join(tickers))
    else:
        print("No stocks matched the criteria today.")

if __name__ == "__main__":
    get_watchlist()
