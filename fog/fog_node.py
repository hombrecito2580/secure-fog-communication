import base64
import json
import threading

import requests
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI, Request, HTTPException

from utils.crypto_utils import *

app = FastAPI()

# === Fog keys ===
fog_private, fog_public = generate_keypair()

# === Cloud connection ===
CLOUD_URL = "http://127.0.0.1:8002"
cloud_public_b64 = requests.get(f"{CLOUD_URL}/public-key").json()["cloud_public"]
cloud_public_bytes = base64.b64decode(cloud_public_b64)

# === Meter tracking ===
readings_buffer = []       # temporary store for incoming meter readings
buffer_lock = threading.Lock()

# === Public key endpoint ===
@app.get("/public-key")
def get_public_key():
    return {
        "fog_public": base64.b64encode(
            fog_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        ).decode()
    }

# === Receive data from meters ===
@app.post("/exchange")
async def receive_from_meter(request: Request):
    data = await request.json()

    try:
        meter_pub_bytes = base64.b64decode(data["meter_public"])
        meter_sig_pub = base64.b64decode(data["meter_sig_pub"])
        encrypted_data = base64.b64decode(data["encrypted_data"])
        sig = base64.b64decode(data["signature"])
        ts = int(data["ts"])

        # Derive shared key and decrypt
        shared_key = derive_shared_key(fog_private, meter_pub_bytes)
        plaintext = decrypt_message(shared_key, encrypted_data, aad=b"SM-FN")

        # Verify signature
        if not verify_sig(meter_sig_pub, plaintext, sig):
            raise HTTPException(400, detail="Invalid signature")

        reading = json.loads(plaintext.decode())

        # Store reading
        with buffer_lock:
            readings_buffer.append(reading)

        print(f"📩 From {reading['meter_id']}: {reading['power_usage']} kWh ({reading['voltage']} V)")

        return {"status": "ok"}

    except Exception as e:
        print("❌ Error processing meter data:", e)
        raise HTTPException(400, detail=str(e))

# === Background task: aggregate and send to cloud ===
def aggregate_and_send():
    while True:
        time.sleep(10)  # aggregate every 10 seconds

        with buffer_lock:
            if not readings_buffer:
                continue

            # Compute aggregate stats
            total_power = sum(r["power_usage"] for r in readings_buffer)
            avg_power = total_power / len(readings_buffer)
            avg_voltage = sum(r["voltage"] for r in readings_buffer) / len(readings_buffer)

            payload = {
                "fog_id": "FN-01",
                "num_meters": len(readings_buffer),
                "avg_power": round(avg_power, 2),
                "avg_voltage": round(avg_voltage, 1),
                "timestamp": now_ms()
            }

            readings_buffer.clear()

        print(f"📦 Aggregated → Cloud: {payload}")

        # Encrypt and forward
        shared_key = derive_shared_key(fog_private, cloud_public_bytes)
        encrypted_data = encrypt_message(shared_key, json.dumps(payload).encode(), aad=b"FN-CS")

        fog_pub_b64 = base64.b64encode(
            fog_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        ).decode()

        resp = requests.post(f"{CLOUD_URL}/data", json={
            "fog_public": fog_pub_b64,
            "message": base64.b64encode(encrypted_data).decode()
        })

        if resp.status_code == 200:
            print("✅ Sent aggregated data to cloud")
        else:
            print("⚠️ Cloud response:", resp.status_code)


# Start the background thread
threading.Thread(target=aggregate_and_send, daemon=True).start()

@app.get("/")
def root():
    return {"message": "Fog Node running and aggregating data"}
