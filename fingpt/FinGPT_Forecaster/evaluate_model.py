import os
import re
import json
import time
import finnhub
import yfinance as yf
import pandas as pd
import torch
from datetime import datetime, timedelta, date
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
from peft import PeftModel
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

# Setup Clients
finnhub_client = finnhub.Client(api_key=os.environ.get("FINNHUB_API_KEY"))
groq_api_key = os.environ.get("GROQ_API_KEY")

# ---------------------------------------------------------------------------- #
#                               Model Setup                                    #
# ---------------------------------------------------------------------------- #

def setup_model():
    if groq_api_key:
        print(f"Using Groq API for inference (Key found: {groq_api_key[:4]}...).")
        return None, None, groq.Groq(api_key=groq_api_key)
    
    print("Initializing Local Model...")
    access_token = os.environ.get("HF_TOKEN")
    
    base_model = AutoModelForCausalLM.from_pretrained(
        'meta-llama/Llama-2-7b-chat-hf',
        token=access_token,
        trust_remote_code=True, 
        device_map="auto",
        torch_dtype=torch.float16,
        offload_folder="offload/"
    )
    model = PeftModel.from_pretrained(
        base_model,
        'FinGPT/fingpt-forecaster_dow30_llama2-7b_lora',
        offload_folder="offload/"
    )
    model = model.eval()

    tokenizer = AutoTokenizer.from_pretrained(
        'meta-llama/Llama-2-7b-chat-hf',
        token=access_token
    )
    return model, tokenizer, None

# ---------------------------------------------------------------------------- #
#                               Data Fetching                                  #
# ---------------------------------------------------------------------------- #

def n_weeks_before(date_string, n):
    date_obj = datetime.strptime(date_string, "%Y-%m-%d") - timedelta(days=7*n)
    return date_obj.strftime("%Y-%m-%d")

def get_stock_data(stock_symbol, steps):
    # Fetch a bit more buffer to ensure we cover the range
    stock_data = yf.download(stock_symbol, steps[0], steps[-1])
    if len(stock_data) == 0:
        return None
    
    # Handle yfinance structure
    close_prices = stock_data['Close']
    if hasattr(close_prices, 'columns'):
        close_prices = close_prices.iloc[:, 0]

    dates, prices = [], []
    available_dates = stock_data.index.format()
    
    # Map steps to available trading days
    for date_step in steps[:-1]:
        for i in range(len(stock_data)):
            if available_dates[i] >= date_step:
                prices.append(close_prices.iloc[i])
                dates.append(datetime.strptime(available_dates[i], "%Y-%m-%d"))
                break

    # Add last step
    dates.append(datetime.strptime(available_dates[-1], "%Y-%m-%d"))
    prices.append(close_prices.iloc[-1])
    
    return pd.DataFrame({
        "Start Date": dates[:-1], "End Date": dates[1:],
        "Start Price": prices[:-1], "End Price": prices[1:]
    })

def get_news(symbol, data):
    news_list = []
    for _, row in data.iterrows():
        start_date = row['Start Date'].strftime('%Y-%m-%d')
        end_date = row['End Date'].strftime('%Y-%m-%d')
        time.sleep(0.5) # Rate limit protection
        try:
            weekly_news = finnhub_client.company_news(symbol, _from=start_date, to=end_date)
            formatted_news = [
                {
                    "date": datetime.fromtimestamp(n['datetime']).strftime('%Y%m%d%H%M%S'),
                    "headline": n['headline'],
                    "summary": n['summary'],
                } for n in weekly_news
            ]
            formatted_news.sort(key=lambda x: x['date'])
            news_list.append(json.dumps(formatted_news))
        except Exception as e:
            print(f"Warning: Failed to fetch news for {symbol}: {e}")
            news_list.append(json.dumps([]))
    
    data['News'] = news_list
    return data

def get_actual_return(symbol, prediction_date):
    """
    Get the actual stock return for the week FOLLOWING the prediction date.
    """
    start_date = prediction_date
    end_date = n_weeks_before(prediction_date, -1) # 1 week AFTER
    
    # We need a small buffer to find the nearest trading day
    buffer_end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")
    
    data = yf.download(symbol, start=start_date, end=buffer_end)
    if len(data) < 2:
        return None
        
    close_prices = data['Close']
    if hasattr(close_prices, 'columns'):
        close_prices = close_prices.iloc[:, 0]
        
    start_price = close_prices.iloc[0]
    end_price = close_prices.iloc[-1] # Approximation of 1 week later
    
    actual_return_pct = ((end_price - start_price) / start_price) * 100
    
    return actual_return_pct

# ---------------------------------------------------------------------------- #
#                               Prompt Building                                #
# ---------------------------------------------------------------------------- #

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
SYSTEM_PROMPT = "You are a seasoned stock market analyst. Your task is to list the positive developments and potential concerns for companies based on relevant news and basic financials from the past weeks, then provide an analysis and prediction for the companies' stock price movement for the upcoming week. Your answer format should be as follows:\n\n[Positive Developments]:\n1. ...\n\n[Potential Concerns]:\n1. ...\n\n[Prediction & Analysis]\nPrediction: ...\nAnalysis: ..."

def build_prompt(symbol, curday, n_weeks=3):
    steps = [n_weeks_before(curday, n) for n in range(n_weeks + 1)][::-1]
    
    data = get_stock_data(symbol, steps)
    if data is None:
        raise ValueError("No stock data found")
        
    data = get_news(symbol, data)
    
    # Construct prompt text (Simplified version of app.py logic)
    main_prompt = ""
    for _, row in data.iterrows():
        s_date = row['Start Date'].strftime('%Y-%m-%d')
        e_date = row['End Date'].strftime('%Y-%m-%d')
        term = 'increased' if row['End Price'] > row['Start Price'] else 'decreased'
        main_prompt += f"\nFrom {s_date} to {e_date}, {symbol}'s stock price {term} from {row['Start Price']:.2f} to {row['End Price']:.2f}. Company news:\n\n"
        
        news_items = json.loads(row["News"])
        # Take top 3 for brevity in test
        for n in news_items[:3]:
            main_prompt += f"[Headline]: {n['headline']}\n[Summary]: {n['summary']}\n"
    
    # Add company profile
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        company_intro = f"[Company Introduction]:\n{profile.get('name', symbol)} is in {profile.get('finnhubIndustry', 'N/A')}. "
    except:
        company_intro = f"[Company Introduction]:\n{symbol}."

    final_prompt = f"{company_intro}\n{main_prompt}\n\n[Basic Financials]:\nNo basic financial reported.\n\nBased on all information before {curday}, predict {symbol} stock price movement for next week."
    
    full_llama_prompt = B_INST + B_SYS + SYSTEM_PROMPT + E_SYS + final_prompt + E_INST
    return full_llama_prompt, final_prompt

# ---------------------------------------------------------------------------- #
#                               Evaluation                                     #
# ---------------------------------------------------------------------------- #

def parse_prediction(response):
    # Try to find "Prediction: ..."
    # Look for "Up" or "Down" and a percentage
    # Regex changed to avoid matching '[Prediction & Analysis]' header
    # Looks for 'Prediction:' at start of line
    pred_section = re.search(r"(?:^|\n)Prediction:\s*(.*?)(?:\n|$)", response, re.IGNORECASE)
    if not pred_section:
        # Fallback: search whole response
        text = response
    else:
        text = pred_section.group(1)
        
    print(f"DEBUG PARSED TEXT: {text}")

    direction = "Unknown"
    text_lower = text.lower()
    
    up_keywords = ["up", "increase", "positive", "rise", "rising", "growth", "bull", "high"]
    down_keywords = ["down", "decrease", "negative", "decline", "fall", "falling", "drop", "bear", "low"]
    
    if any(k in text_lower for k in up_keywords):
        direction = "Up"
    elif any(k in text_lower for k in down_keywords):
        direction = "Down"
        
    # Extract percentage if possible
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    pct = float(pct_match.group(1)) if pct_match else None
    
    return direction, pct

def main():
    print("Starting Model Evaluation...")
    model, tokenizer, groq_client = setup_model()
    
    # Define Test Cases
    # Use dates from a few months ago to ensure we have 'future' data to verify against
    test_cases = [
        {"symbol": "AAPL", "date": "2023-10-01"},
        {"symbol": "MSFT", "date": "2023-11-15"},
        {"symbol": "NVDA", "date": "2023-09-01"},
        # {"symbol": "JPM", "date": "2023-12-01"},
    ]
    
    results = []
    
    for case in test_cases:
        symbol = case['symbol']
        date_str = case['date']
        print(f"\n--- Testing {symbol} for date {date_str} ---")
        
        try:
            full_prompt, raw_prompt = build_prompt(symbol, date_str)
            
            # Inference
            start_time = time.time()
            if groq_client:
                print("Processing with Groq...")
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": raw_prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1
                )
                response = chat_completion.choices[0].message.content
            else:
                print("Processing with Local Model...")
                inputs = tokenizer(full_prompt, return_tensors='pt').to(model.device)
                res = model.generate(**inputs, max_new_tokens=512, do_sample=False)
                output = tokenizer.decode(res[0], skip_special_tokens=True)
                response = re.sub(r'.*\[/INST\]\s*', '', output, flags=re.DOTALL)
            
            print(f"DEBUG RAW RESPONSE:\n{response}\n-------------------")

            duration = time.time() - start_time
            print(f"Inference took {duration:.2f}s")
            
            # Get Ground Truth
            actual_return = get_actual_return(symbol, date_str)
            actual_dir = "Up" if actual_return > 0 else "Down"
            
            # Parse Prediction
            pred_dir, pred_pct = parse_prediction(response)
            
            # Compare
            match = (pred_dir == actual_dir)
            
            result = {
                "Symbol": symbol,
                "Date": date_str,
                "Pred_Dir": pred_dir,
                "Actual_Dir": actual_dir,
                "Pred_Pct": pred_pct,
                "Actual_Pct": f"{actual_return:.2f}%",
                "Correct": "YES" if match else "NO"
            }
            results.append(result)
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            
    # Summary
    print("\n\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        print(df_res.to_string(index=False))
        accuracy = (df_res["Correct"] == "YES").mean() * 100
        print(f"\nOverall Directional Accuracy: {accuracy:.2f}%")
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
