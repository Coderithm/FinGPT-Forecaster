import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, skipping .env load")

print("--- Diagnostic Report ---")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

print("\n--- Environment Variables ---")
hf_token = os.environ.get("HF_TOKEN")
finnhub_key = os.environ.get("FINNHUB_API_KEY")
groq_key = os.environ.get("GROQ_API_KEY")

print(f"HF_TOKEN: {'[SET]' if hf_token else '[MISSING]'}")
print(f"FINNHUB_API_KEY: {'[SET]' if finnhub_key else '[MISSING]'} {f'(Len: {len(finnhub_key)})' if finnhub_key else ''}")
print(f"GROQ_API_KEY: {'[SET]' if groq_key else '[MISSING]'} {f'(Len: {len(groq_key)})' if groq_key else ''}")

print("\n--- Dependencies ---")
try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
    else:
        print("WARNING: CUDA not available. Inference will be slow on CPU.")
except ImportError as e:
    print(f"Torch Error: {e}")

try:
    import yfinance as yf
    print(f"yfinance Version: {yf.__version__}")
except ImportError as e:
    print(f"yfinance Error: {e}")

try:
    import finnhub
    print(f"finnhub-python: Installed")
except ImportError:
    print("finnhub-python: MISSING")

try:
    import transformers
    print(f"transformers Version: {transformers.__version__}")
except ImportError:
    print("transformers: MISSING")

try:
    import groq
    print(f"groq: Installed (Version: {getattr(groq, '__version__', 'Unknown')})")
    # Try initializing client to see if it works with the key
    if groq_key:
        try:
            client = groq.Groq(api_key=groq_key)
            print("Groq Client initialized successfully.")
        except Exception as e:
            print(f"Groq Client Init Error: {e}")
except ImportError:
    print("groq: MISSING (This is likely the cause of slow performance!)")
