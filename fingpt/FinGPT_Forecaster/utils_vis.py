import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import re
from datetime import datetime, timedelta

def parse_prediction(answer, last_price):
    """
    Attempts to parse prediction direction and price targets from the LLM answer.
    Returns a dictionary with 'direction', 'target_price', 'percentage'.
    """
    prediction = {
        'direction': None,
        'target_price': None
    }
    
    # Convert to lower case for keyword matching
    lower_ans = answer.lower()
    
    # 1. Determine Direction
    if any(x in lower_ans for x in ['rise', 'increase', 'bullish', 'upward', 'gain']):
        prediction['direction'] = 'Up'
    elif any(x in lower_ans for x in ['fall', 'decrease', 'bearish', 'downward', 'loss', 'drop']):
        prediction['direction'] = 'Down'
    
    # 2. Scope the search for numbers to the "Prediction" section if possible
    # This avoids picking up numbers from "Recent News" or "Financials" (like "EPS $3.00")
    prediction_text = lower_ans
    if 'prediction' in lower_ans:
        parts = lower_ans.split('prediction')
        # Take the part after the last occurrence of 'prediction' likely
        prediction_text = parts[-1]
    
    # 3. Look for Percentage Change (e.g., "increase by 2-3%", "gain of 5%")
    # Matches: "2%", "2.5%", "2-3%"
    pct_pattern = r'(\d+\.?\d*)\s?%|(\d+)\s?-\s?(\d+)\s?%'
    pct_matches = re.findall(pct_pattern, prediction_text)
    
    percentage = None
    if pct_matches:
        # Take the first match in the prediction text
        m = pct_matches[0]
        # m is a tuple like ('2', '', '') or ('', '2', '3')
        if m[0]: # Single percentage
            percentage = float(m[0])
        elif m[1] and m[2]: # Range "2-3%"
            percentage = (float(m[1]) + float(m[2])) / 2
            
    if percentage:
        # Apply percentage
        if prediction['direction'] == 'Down':
            prediction['target_price'] = last_price * (1 - percentage / 100)
        else:
            # Default to Up if generic or specified Up
            prediction['target_price'] = last_price * (1 + percentage / 100)
            if not prediction['direction']:
                 prediction['direction'] = 'Up'
                
    # 4. If no percentage, look for explicit Price Target (e.g., "reach $150")
    if prediction['target_price'] is None:
        price_pattern = r'\$\s?(\d+\.?\d*)'
        prices = re.findall(price_pattern, prediction_text)
        
        valid_prices = []
        for p in prices:
            try:
                val = float(p)
                # Sanity check: Price shouldn't be drastically different (e.g. < 10% of current price is likely a dividend or EPS)
                # unless the text explicitly says "crash"
                if val > last_price * 0.2 and val < last_price * 5.0:
                    valid_prices.append(val)
            except ValueError:
                pass
        
        if valid_prices:
            # Use the last valid price found in the prediction section
            prediction['target_price'] = valid_prices[-1]

    # 5. Final Fallback if we have Direction but no Price
    if prediction['target_price'] is None and prediction['direction']:
        if prediction['direction'] == 'Up':
            prediction['target_price'] = last_price * 1.02 # Default 2% up
        elif prediction['direction'] == 'Down':
            prediction['target_price'] = last_price * 0.98 # Default 2% down

    return prediction

def create_chart(ticker, history_df, answer):
    """
    Creates a matplotlib figure showing historical data and a visual indicator of the prediction.
    """
    
    # Ensure Date is datetime
    if 'Date' not in history_df.columns and isinstance(history_df.index, pd.DatetimeIndex):
         history_df = history_df.reset_index()
         if 'Date' not in history_df.columns:
             history_df.rename(columns={'index': 'Date'}, inplace=True)
    
    # Make sure we have proper columns
    if 'Date' not in history_df.columns or 'Close' not in history_df.columns:
        return None

    # Sort by date
    history_df['Date'] = pd.to_datetime(history_df['Date'])
    history_df = history_df.sort_values('Date')
    
    if history_df.empty:
        return None

    last_date = history_df['Date'].iloc[-1]
    last_price = history_df['Close'].iloc[-1]
    
    # Parse prediction
    pred_data = parse_prediction(answer, last_price)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot historical data
    ax.plot(history_df['Date'], history_df['Close'], label='Historical Close', color='blue', linewidth=2)
    
    # Visualizing Prediction
    next_week_date = last_date + timedelta(days=7)
    target_price = pred_data['target_price'] 
        
    if prev_direction := pred_data.get('direction'):
        if prev_direction == 'Up':
            color = 'green'
            marker = '^'
            if target_price is None: target_price = last_price
        elif prev_direction == 'Down':
            color = 'red'
            marker = 'v'
            if target_price is None: target_price = last_price
        else:
            color = 'gray'
            marker = 'o'
            if target_price is None: target_price = last_price
    else:
        # No direction found
        color = 'gray'
        marker = 'o'
        if target_price is None: target_price = last_price

    # Plot the prediction line (dotted)
    ax.plot([last_date, next_week_date], [last_price, target_price], color=color, linestyle='--', linewidth=2, label='Prediction')
    ax.scatter([next_week_date], [target_price], color=color, marker=marker, s=100, zorder=5)
    
    # Annotate price
    ax.annotate(f"${target_price:.2f}", 
                (next_week_date, target_price), 
                textcoords="offset points", 
                xytext=(10,0), 
                ha='left', 
                color=color,
                fontsize=10,
                fontweight='bold')
    
    # Formatting
    ax.set_title(f"{ticker} Stock Price & Prediction", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price (USD)", fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    
    # Format Date Axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    return fig
