import yfinance as yf
import finnhub
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])

def n_weeks_before(date_string, n):
    date = datetime.strptime(date_string, "%Y-%m-%d") - timedelta(days=7*n)
    return date.strftime("%Y-%m-%d")

SYMBOL = "AAPL"
DATE = "2025-12-17" # User's input
N_WEEKS = 1

print(f"--- Debugging Data for {SYMBOL} ending {DATE} ---")

# 1. Test Dates
try:
    steps = [n_weeks_before(DATE, n) for n in range(N_WEEKS + 1)][::-1]
    print(f"Date Steps: {steps}")
except Exception as e:
    print(f"Date Error: {e}")
    exit(1)

# 2. Test yfinance
print("\n[yfinance] Downloading...")
try:
    stock_data = yf.download(SYMBOL, start=steps[0], end=steps[-1])
    print(stock_data)
    if len(stock_data) == 0:
        print("FAIL: yfinance returned empty data.")
    else:
        print(f"SUCCESS: Got {len(stock_data)} rows.")
except Exception as e:
    print(f"FAIL: yfinance exception: {e}")

# 3. Test Finnhub News
print("\n[Finnhub] Fetching News...")
try:
    start_date = steps[0]
    end_date = steps[-1]
    print(f"Querying news from {start_date} to {end_date}")
    weekly_news = finnhub_client.company_news(SYMBOL, _from=start_date, to=end_date)
    if len(weekly_news) == 0:
        print("FAIL: Finnhub returned no news.")
    else:
        print(f"SUCCESS: Got {len(weekly_news)} news items.")
        print(f"Sample: {weekly_news[0]['headline']}")
except Exception as e:
    print(f"FAIL: Finnhub exception: {e}")

# 4. Test Finnhub Profile
print("\n[Finnhub] Fetching Profile...")
try:
    profile = finnhub_client.company_profile2(symbol=SYMBOL)
    if not profile:
        print("FAIL: No profile found.")
    else:
        print("SUCCESS: Profile found.")
except Exception as e:
    print(f"FAIL: Finnhub profile exception: {e}")
