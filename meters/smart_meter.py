# smart_meter.py
import base64
import json
import requests
from cryptography.hazmat.primitives import serialization

from utils.crypto_utils import *

FOG_URL = "http://127.0.0.1:8001"

# keys
meter_private, meter_public = generate_keypair()
sig_sk, sig_pk = gen_sign_keypair()

# fetch fog pubkey
fog_public_b64 = requests.get(f"{FOG_URL}/public-key").json()["fog_public"]
fog_public_bytes = base64.b64decode(fog_public_b64)

# derive link key
k = derive_shared_key(meter_private, fog_public_bytes)

# reading + envelope
payload = {
    "reading": "Meter#101: Power Usage = 5.2 kWh",
    "issued_at": now_ms()
}
plaintext = json.dumps(payload).encode()

ts = now_ms()
nonce = base64.b64encode(os.urandom(16)).decode()

# sign plaintext
signature = sign(sig_sk, plaintext)

# encrypt with AAD to bind channel
enc = encrypt_message(k, plaintext, aad=b"SM-FN")

body = {
    "meter_public": base64.b64encode(
        meter_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    ).decode(),
    "meter_sig_pub": base64.b64encode(
        sig_pk.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    ).decode(),
    "ts": ts,
    "nonce": nonce,
    "signature": base64.b64encode(signature).decode(),
    "encrypted_data": base64.b64encode(enc).decode()
}

r = requests.post(f"{FOG_URL}/exchange", json=body)
print(r.json())
