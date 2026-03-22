from fyers_apiv3 import fyersModel

# 🔐 credentials
client_id = "E3M6LF8A03-100"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcHVra3hYMWpqbEYyTmZBQ2FQVjhoQ2JHZVE4aTN3UkZDbF9zVGlUOUtSeF95QmRJNnRfcTR1OTA3dlZQcUl2ME5sY3ZWRG9vcGRldTZpOWs4MHlNa1U5eFF5d2tCenhsejJDcDhBbURYb3pnV0FkYz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZTAxZmNmZThlZTQ1Y2EyNTFmOGJjNDk0OTI2MTNkMWM5NzY4YWZlNjZjZDRkMzRlNmRjZjRmYiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiRkFJOTIxMzUiLCJhcHBUeXBlIjoxMDAsImV4cCI6MTc3Mzg4MDIwMCwiaWF0IjoxNzczODE2MTEzLCJpc3MiOiJhcGkuZnllcnMuaW4iLCJuYmYiOjE3NzM4MTYxMTMsInN1YiI6ImFjY2Vzc190b2tlbiJ9.nsJLIPxA6aKjvHyIkEwfmtNjBnwFkoIijpoaelJhl8Q"

# connect to fyers
fyers = fyersModel.FyersModel(
    client_id=client_id,
    token=access_token
)

# 📊 STEP 2 → function here
import datetime

def get_stock_data(symbol):
    # Dynamic date range from 5 days ago to today to ensure we get some trading days
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=5)
    
    data = {
        "symbol": symbol,
        "resolution": "10",
        "date_format": "1",
        "range_from": start_date.strftime("%Y-%m-%d"),
        "range_to": end_date.strftime("%Y-%m-%d"),
        "cont_flag": "1"
    }

    try:
        response = fyers.history(data)
        return response
    except Exception as e:
        print(f"Fyers API Error: {e}")
        return {"s": "error", "message": str(e)}

def analyze_stock(symbol):
    
    # Simple heuristic to translate standard ticker (like AAPL or RELIANCE.NS) to Fyers format
    fyers_symbol = symbol
    if symbol.endswith(".NS"):
        fyers_symbol = f"NSE:{symbol.split('.')[0]}-EQ"
    elif symbol.endswith(".BO"):
         fyers_symbol = f"BSE:{symbol.split('.')[0]}-EQ"
    elif not ":" in symbol:
        fyers_symbol = f"NSE:{symbol}-EQ"

    data = get_stock_data(fyers_symbol)

    if not data or data.get("s") != "ok":
        return None

    candles = data.get("candles", [])

    if not candles:
        return None

    latest = candles[-1]
    prev = candles[-2] if len(candles) > 1 else latest

    open_price = latest[1]
    close_price = latest[4]

    change = close_price - prev[4]
    percent_change = (change / prev[4]) * 100 if prev[4] != 0 else 0

    trend = "Bullish \ud83d\udcc8" if change > 0 else "Bearish \ud83d\udcc9" if change < 0 else "Sideways \u27a1\ufe0f"

    # Format the timestamp
    latest_time = datetime.datetime.fromtimestamp(latest[0]).strftime('%Y-%m-%d %H:%M:%S')

    result = f"[Latest Intraday Data ({latest_time})]:\n"
    result += f"- Current Price: {close_price: .2f}\n"
    result += f"- 10m Trend: {trend} (Change: {change: .2f}, {percent_change: .2f}%)\n"
    result += f"- 10m Volume: {latest[5]}\n"
    
    return result

if __name__ == "__main__":
    print(analyze_stock("RELIANCE.NS"))