from fastapi import FastAPI, Request
from utils.crypto_utils import *
from cryptography.hazmat.primitives import serialization
import base64

app = FastAPI()

# Cloud keypair
cloud_private, cloud_public = generate_keypair()

@app.get("/public-key")
def get_public_key():
    """Expose Cloud’s public key for Fog to use."""
    return {
        "cloud_public": base64.b64encode(
            cloud_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        ).decode()
    }

@app.post("/data")
async def receive_from_fog(request: Request):
    data = await request.json()

    # Decode fog’s public key and message
    fog_pub_bytes = base64.b64decode(data["fog_public"])
    encrypted_data = base64.b64decode(data["message"])

    # Derive shared key with Fog Node
    shared_key = derive_shared_key(cloud_private, fog_pub_bytes)
    decrypted = decrypt_message(shared_key, encrypted_data, aad=b"FN-CS")

    print(f"✅ Cloud decrypted data: {decrypted.decode()}")
    return {"status": "Cloud received and decrypted successfully"}

@app.get("/")
def root():
    return {"message": "Cloud Server running"}
