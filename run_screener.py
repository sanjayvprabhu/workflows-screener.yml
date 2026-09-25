import sys
import requests
from bs4 import BeautifulSoup

URL = "https://chartink.com/screener/chartink-dry-up-setup-ready-screener-code-for-oneil-disiple"
PROCESS_URL = "https://chartink.com/screener/process"

def get_watchlist():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    print("Fetching screener page...")
    response = session.get(URL, headers=headers, timeout=20)
    
    if response.status_code != 200:
        print(f"Error: Initial request failed with HTTP status {response.status_code}")
        sys.exit(1)
        
    soup = BeautifulSoup(response.text, "html.parser")
    
    csrf_tag = soup.find("meta", {"name": "csrf-token"})
    clause_tag = soup.find("input", {"id": "scan_clause"})
    
    if not csrf_tag or not clause_tag:
        print("Error: Could not extract CSRF token or scan clause.")
        if "cf-browser-verification" in response.text or "Cloudflare" in response.text:
            print("Notice: Chartink displayed a Cloudflare bot check to the GitHub runner IP.")
        else:
            print("HTML Snippet returned:\n", response.text[:600])
        sys.exit(1)
        
    csrf_token = csrf_tag["content"]
    scan_clause = clause_tag["value"]
    
    post_headers = {
        **headers,
        "x-csrf-token": csrf_token,
        "Referer": URL,
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {"scan_clause": scan_clause}
    
    print("Posting query to process endpoint...")
    res = session.post(PROCESS_URL, data=payload, headers=post_headers, timeout=20)
    
    if res.status_code != 200:
        print(f"Error: Process request failed with HTTP status {res.status_code}")
        print("Response body:\n", res.text[:500])
        sys.exit(1)
        
    try:
        json_resp = res.json()
    except Exception as e:
        print(f"Error: Could not parse JSON response: {e}")
        print("Raw response:\n", res.text[:500])
        sys.exit(1)
        
    data = json_resp.get("data", [])
    
    tickers = [f"NSE:{item['nsecode']}" for item in data if "nsecode" in item]
    
    output_path = "tv_dryup_watchlist.txt"
    with open(output_path, "w") as f:
        f.write(",\n".join(tickers))
        
    print(f"Success: Exported {len(tickers)} symbols to {output_path}")
    if tickers:
        print(", ".join(tickers))
    else:
        print("Zero stocks matched the criteria at this scan time.")

if __name__ == "__main__":
    get_watchlist()
