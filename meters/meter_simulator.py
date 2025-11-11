import base64
import json
import random
import threading

import requests
from cryptography.hazmat.primitives import serialization

from utils.crypto_utils import *

FOG_URL = "http://127.0.0.1:8001"   # Change to your fog node IP later
NUM_METERS = 10                     # simulate 10 smart meters
SEND_INTERVAL = 5                   # seconds between readings

# === Fetch fog node public key once ===
fog_public_b64 = requests.get(f"{FOG_URL}/public-key").json()["fog_public"]
fog_public_bytes = base64.b64decode(fog_public_b64)


def run_meter(meter_id: int):
    """Simulate one smart meter sending readings periodically."""
    # Generate crypto keys for this meter
    priv, pub = generate_keypair()
    sig_sk, sig_pk = gen_sign_keypair()
    shared_key = derive_shared_key(priv, fog_public_bytes)

    while True:
        reading = {
            "meter_id": f"M-{meter_id:03d}",
            "power_usage": round(random.uniform(4.5, 6.5), 2),
            "voltage": round(random.uniform(210, 250), 1),
            "timestamp": now_ms()
        }
        plaintext = json.dumps(reading).encode()

        # Sign + Encrypt
        signature = sign(sig_sk, plaintext)
        encrypted_data = encrypt_message(shared_key, plaintext, aad=b"SM-FN")

        payload = {
            "meter_public": base64.b64encode(
                pub.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            ).decode(),
            "meter_sig_pub": base64.b64encode(
                sig_pk.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            ).decode(),
            "ts": now_ms(),
            "nonce": base64.b64encode(os.urandom(16)).decode(),
            "signature": base64.b64encode(signature).decode(),
            "encrypted_data": base64.b64encode(encrypted_data).decode()
        }

        try:
            resp = requests.post(f"{FOG_URL}/exchange", json=payload)
            print(f"[Meter-{meter_id:03d}] sent → {resp.status_code}")
        except Exception as e:
            print(f"[Meter-{meter_id:03d}] ❌ Error: {e}")

        time.sleep(SEND_INTERVAL)


# === Launch all meters as threads ===
threads = []
for i in range(1, NUM_METERS + 1):
    t = threading.Thread(target=run_meter, args=(i,), daemon=True)
    t.start()
    time.sleep(0.5)  # small stagger so they don’t all send at once

print(f"🚀 Started {NUM_METERS} simulated smart meters.")
print("Press Ctrl+C to stop.")

while True:
    time.sleep(1)
