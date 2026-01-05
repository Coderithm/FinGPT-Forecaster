import os
from dotenv import load_dotenv
from huggingface_hub import login
from transformers import AutoConfig

load_dotenv()
token = os.environ.get("HF_TOKEN")

print(f"Token present: {bool(token)}")

if token:
    print("Logging in via huggingface_hub...")
    login(token=token, add_to_git_credential=False)
    print("Login complete.")

print("Attempting to load AutoConfig for 'meta-llama/Llama-2-7b-chat-hf'...")
try:
    # Try WITHOUT passing token arg, relying on the login we just did
    config = AutoConfig.from_pretrained(
        'meta-llama/Llama-2-7b-chat-hf',
        trust_remote_code=True
    )
    print("SUCCESS: Config loaded (Global login working).")
except Exception as e:
    print(f"FAILED to load Config: {e}")
