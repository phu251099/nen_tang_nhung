import os
import base64
import hashlib
import binascii
import nacl.signing
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "static" / "firmwares"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

PRIV_KEY_FILE = BASE_DIR / "ed25519_private.key"
PUB_KEY_FILE = BASE_DIR / "ed25519_public.key"

def ensure_keys():
    if not PRIV_KEY_FILE.exists():
        sk = nacl.signing.SigningKey.generate()
        PRIV_KEY_FILE.write_bytes(sk.encode())
        PUB_KEY_FILE.write_bytes(sk.verify_key.encode())
    sk = nacl.signing.SigningKey(PRIV_KEY_FILE.read_bytes())
    vk = nacl.signing.VerifyKey(PUB_KEY_FILE.read_bytes())
    return sk, vk

SIGNING_KEY, VERIFY_KEY = ensure_keys()

def sha256_of_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def sign_bytes_ed25519(data: bytes) -> str:
    sig = SIGNING_KEY.sign(data).signature
    return base64.b64encode(sig).decode()

def build_full_url(request, path: str, public_base_url=None):
    if public_base_url:
        base = public_base_url.rstrip("/")
    else:
        if request is None:
            raise RuntimeError("Request is required to build full URL when PUBLIC_BASE_URL is not set")
        base = str(request.base_url).rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"