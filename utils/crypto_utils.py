# utils/crypto_utils.py
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os, time

# --- X25519 ---
def generate_keypair():
    priv = x25519.X25519PrivateKey.generate()
    return priv, priv.public_key()

def derive_shared_key(private_key, peer_public_bytes):
    peer_pub = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
    secret = private_key.exchange(peer_pub)
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'secure-fog-comm').derive(secret)

# --- AEAD w/ optional AAD ---
def encrypt_message(key, plaintext: bytes, aad: bytes | None = None):
    nonce = os.urandom(12)
    c = ChaCha20Poly1305(key)
    ct = c.encrypt(nonce, plaintext, aad)
    return nonce + ct  # [12B nonce || ciphertext+tag]

def decrypt_message(key, blob: bytes, aad: bytes | None = None):
    nonce, ct = blob[:12], blob[12:]
    c = ChaCha20Poly1305(key)
    return c.decrypt(nonce, ct, aad)

# --- Ed25519 ---
def gen_sign_keypair():
    sk = ed25519.Ed25519PrivateKey.generate()
    return sk, sk.public_key()

def sign(sk: ed25519.Ed25519PrivateKey, data: bytes) -> bytes:
    return sk.sign(data)

def verify_sig(pk_bytes: bytes, data: bytes, sig: bytes) -> bool:
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(pk_bytes).verify(sig, data)
        return True
    except Exception:
        return False

# --- anti-replay helpers ---
def now_ms() -> int:
    return int(time.time() * 1000)
