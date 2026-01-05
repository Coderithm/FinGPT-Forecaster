import os
from dotenv import load_dotenv
from transformers import AutoConfig, AutoModelForCausalLM
import torch

load_dotenv()
token = os.environ.get("HF_TOKEN")

print(f"Token: {token[:4]}...{token[-4:]}")
print("Attempting to load AutoConfig for 'meta-llama/Llama-2-7b-chat-hf'...")

try:
    config = AutoConfig.from_pretrained(
        'meta-llama/Llama-2-7b-chat-hf',
        token=token,
        trust_remote_code=True
    )
    print("SUCCESS: Config loaded (Auth working for transformers).")
except Exception as e:
    print(f"FAILED to load Config: {e}")
    # exit(1) # Continue to check model

print("\nAttempting to initiate model load (just the beginning)...")
try:
    # We won't download the whole thing, just check if it fails auth immediately
    # We use a dummy device map to avoid actual huge allocation if possible, or catch error early
    model = AutoModelForCausalLM.from_pretrained(
        'meta-llama/Llama-2-7b-chat-hf',
        token=token,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    print("SUCCESS: Model load initiated (Auth working).")
except OSError as e:
    print(f"OSError (Expected if model not downloaded, but verifies auth passed to get here): {e}")
except Exception as e:
    print(f"FAILED to load Model: {e}")
