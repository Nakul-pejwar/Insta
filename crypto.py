import os
import time
import base64
import struct

from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_jazoest(phone_id: str) -> str:
    amount = sum(ord(c) for c in phone_id)
    return f"2{amount}"


def _load_public_key(pubkey_b64: str):
    raw = base64.b64decode(pubkey_b64)
    if raw.startswith(b"-----"):
        return serialization.load_pem_public_key(raw)
    if raw[:2] == b"\x30\x82":
        return serialization.load_der_public_key(raw)
    pem_text = raw.decode("ascii", errors="ignore")
    if "-----BEGIN" in pem_text:
        return serialization.load_pem_public_key(pem_text.encode())
    return serialization.load_der_public_key(raw)


def encrypt_password(password: str, key_id: int, pubkey_b64: str) -> str:
    try:
        timestamp = int(time.time())
        timestamp_str = str(timestamp)
        session_key = os.urandom(32)
        iv = os.urandom(12)

        public_key = _load_public_key(pubkey_b64)

        rsa_encrypted = public_key.encrypt(
            session_key,
            asym_padding.PKCS1v15()
        )
        rsa_size = len(rsa_encrypted)

        aesgcm = AESGCM(session_key)
        aad = timestamp_str.encode("utf-8")
        aes_ciphertext = aesgcm.encrypt(iv, password.encode("utf-8"), aad)
        aes_tag = aes_ciphertext[-16:]
        aes_body = aes_ciphertext[:-16]

        payload = b"\x01"
        payload += struct.pack("B", key_id)
        payload += iv
        payload += struct.pack("<H", rsa_size)
        payload += rsa_encrypted
        payload += aes_tag
        payload += aes_body

        encoded = base64.b64encode(payload).decode("ascii")
        return f"#PWD_INSTAGRAM:4:{timestamp}:{encoded}"

    except Exception:
        return password
