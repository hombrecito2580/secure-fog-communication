import base64
import json
import requests
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI, Request, HTTPException

from utils.crypto_utils import *

app = FastAPI()

# keys
fog_private, fog_public = generate_keypair()
meter_seen_nonces: set[str] = set()     # simple in-memory replay cache
METER_NONCE_TTL_MS = 10_000             # 10s window
METER_MAX_SKEW_MS = 10_000

CLOUD_URL = "http://127.0.0.1:8002"

# get cloud public key once
cloud_public_b64 = requests.get(f"{CLOUD_URL}/public-key").json()["cloud_public"]
cloud_public_bytes = base64.b64decode(cloud_public_b64)

@app.get("/public-key")
def get_public_key():
    return {
        "fog_public": base64.b64encode(
            fog_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        ).decode()
    }

def _purge_nonce_cache():
    # for demo simplicity we don’t store timestamps per nonce; reset when grows
    if len(meter_seen_nonces) > 5000:
        meter_seen_nonces.clear()

@app.post("/exchange")
async def receive_from_meter(request: Request):
    data = await request.json()

    # parse envelope
    meter_pub_bytes = base64.b64decode(data["meter_public"])
    meter_sig_pub = base64.b64decode(data["meter_sig_pub"])
    ts = int(data["ts"])
    nonce_b64 = data["nonce"]
    sig = base64.b64decode(data["signature"])
    enc = base64.b64decode(data["encrypted_data"])

    # derive link key with meter
    k_m = derive_shared_key(fog_private, meter_pub_bytes)

    # anti-replay: skew + nonce uniqueness
    now = now_ms()
    if abs(now - ts) > METER_MAX_SKEW_MS:
        raise HTTPException(400, detail="stale or future timestamp")
    if nonce_b64 in meter_seen_nonces:
        raise HTTPException(400, detail="replay detected")
    meter_seen_nonces.add(nonce_b64); _purge_nonce_cache()

    # decrypt (bind channel via AAD)
    aad = b"SM-FN"
    plaintext = decrypt_message(k_m, enc, aad=aad)

    # verify signature over plaintext
    if not verify_sig(meter_sig_pub, plaintext, sig):
        raise HTTPException(400, detail="bad signature")

    msg = json.loads(plaintext.decode())
    print(f"📩 From Meter: {msg['reading']}")

    # forward to cloud with fresh FN↔CS key + envelope (optional signature skipped here)
    k_c = derive_shared_key(fog_private, cloud_public_bytes)
    to_cloud = encrypt_message(k_c, plaintext, aad=b"FN-CS")

    fog_pub_b64 = base64.b64encode(
        fog_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    ).decode()

    payload = {
        "fog_public": fog_pub_b64,
        "message": base64.b64encode(to_cloud).decode()
    }
    requests.post(f"{CLOUD_URL}/data", json=payload)
    return {"status": "Fog received and forwarded securely"}

@app.get("/")
def root():
    return {"message": "Fog Node running"}
