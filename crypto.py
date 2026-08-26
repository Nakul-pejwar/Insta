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


def encrypt_password(password: str, key_id: int, pubkey_b64: str) -> str:
    try:
        timestamp = int(time.time())
        session_key = os.urandom(32)
        iv = os.urandom(12)

        pubkey_der = base64.b64decode(pubkey_b64)
        public_key = serialization.load_der_public_key(pubkey_der)

        rsa_encrypted = public_key.encrypt(
            session_key,
            asym_padding.PKCS1v15()
        )
        rsa_size = len(rsa_encrypted)

        aesgcm = AESGCM(session_key)
        aad = struct.pack(">I", timestamp)
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
