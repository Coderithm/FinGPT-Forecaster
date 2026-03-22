from fyers_apiv3 import fyersModel

client_id = "E3M6LF8A03-100"
secret_key = "XK7FOW2CVD"
redirect_uri = "http://127.0.0.1:7861"

session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type="code",
    grant_type="authorization_code"
)

login_url = session.generate_authcode()
print("1. Please click the link below to login and get the authcode:")
print(login_url)
print("\n2. After logging in, you will be redirected to a URL like:")
print("   http://127.0.0.1:7861/?auth_code=YOUR_AUTH_CODE&state=None")
print("\n3. Copy the YOUR_AUTH_CODE part and paste it here.")

auth_code = input("\nEnter auth code: ").strip()

session.set_token(auth_code)

response = session.generate_token()

if "access_token" in response:
    print("\nSUCCESS! Your NEW ACCESS TOKEN is:")
    print("-" * 50)
    print(response["access_token"])
    print("-" * 50)
else:
    print("\nERROR generating token:")
    print(response)