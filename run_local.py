import os
import subprocess
import sys

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, skipping .env load")

def main():
    print("--- FinGPT Forecaster Local Launcher ---")
    
    # Check for keys
    hf_token = os.environ.get("HF_TOKEN")
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    
    if not hf_token:
        print("\n[!] HF_TOKEN not found.")
        print("Please enter your Hugging Face Token (Read access):")
        hf_token = input("> ").strip()
        os.environ["HF_TOKEN"] = hf_token
        
    if not finnhub_key:
        print("\n[!] FINNHUB_API_KEY not found.")
        print("Please enter your Finnhub API Key:")
        finnhub_key = input("> ").strip()
        os.environ["FINNHUB_API_KEY"] = finnhub_key

    # Check for Groq API Key
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("\n[?] GROQ_API_KEY not found in .env")
        print("To enable FAST cloud inference (Recommended), enter your Groq API Key.")
        print("Press Enter to skip and run SLOW local mode.")
        groq_key = input("> ").strip()
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
        
    print("\nStarting App... (This may take time to download the model on the first run)")
    
    # Path to app.py
    app_path = os.path.join("fingpt", "FinGPT_Forecaster", "app.py")
    
    if not os.path.exists(app_path):
        print(f"Error: Could not find {app_path}")
        return

    # Run the app
    # We use the current python executable
    try:
        subprocess.run([sys.executable, app_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"App crashed with error: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
