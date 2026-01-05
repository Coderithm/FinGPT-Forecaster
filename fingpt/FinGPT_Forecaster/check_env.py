import os
import sys
from dotenv import load_dotenv

try:
    load_dotenv()
    print("DOTENV: Loaded variables from .env (if present)")
except Exception as e:
    print(f"DOTENV: Error loading .env: {e}")

required_vars = ["GROQ_API_KEY", "FINNHUB_API_KEY", "HF_TOKEN"]
missing = []
found = []

for var in required_vars:
    val = os.environ.get(var)
    if val:
        found.append(var)
        print(f"ENV: {var} is set (Length: {len(val)})")
    else:
        missing.append(var)
        print(f"ENV: {var} is NOT set")

print("-" * 20)

try:
    import gradio as gr
    print("IMPORT: gradio imported successfully")
except ImportError:
    print("IMPORT: Failed to import gradio")

try:
    import groq
    print("IMPORT: groq imported successfully")
except ImportError:
    print("IMPORT: Failed to import groq")

try:
    import finnhub
    print("IMPORT: finnhub imported successfully")
except ImportError:
    print("IMPORT: Failed to import finnhub")

if missing:
    print(f"MISSING VARIABLES: {', '.join(missing)}")
else:
    print("ALL REQUIRED VARIABLES FOUND.")
