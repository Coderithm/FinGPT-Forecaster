from dotenv import load_dotenv
import os
from huggingface_hub import HfApi, login
from requests.exceptions import HTTPError

load_dotenv()
token = os.environ.get("HF_TOKEN")

print(f"Testing token: {token[:4]}...{token[-4:]}")

api = HfApi(token=token)

# 1. Test "whoami" (Basic validity)
try:
    user_info = api.whoami()
    print(f"[OK] Token format is valid. User: {user_info['name']}")
    print(f"     Org memberships: {user_info.get('orgs', [])}")
except HTTPError as e:
    print(f"[FAIL] Token invalid: {e}")
    exit(1)

# 2. Test access to public repo
print("\nTesting access to public repo (gpt2)...")
try:
    api.model_info("gpt2")
    print("[OK] Can access public repo.")
except Exception as e:
    print(f"[FAIL] Cannot access public repo: {e}")

# 3. Test access to gated repo (Llama-2)
print("\nTesting access to gated repo (meta-llama/Llama-2-7b-chat-hf)...")
try:
    api.model_info("meta-llama/Llama-2-7b-chat-hf")
    print("[OK] Can access gated Llama-2 repo.")
except Exception as e:
    print(f"[FAIL] Cannot access Llama-2 repo.")
    print(f"       Error details: {e}")
    print("\nPOSSIBLE CAUSES:")
    print("  1. You have not accepted the license on the model card page.")
    print("  2. Your token does not have the 'Read' permission.")
    print("  3. Your request is still pending approval.")
