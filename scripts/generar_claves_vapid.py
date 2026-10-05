"""Generate a VAPID key pair (ECDSA P-256) in the base64url format expected by the .env file.

Usage (inside the app container):
    docker compose run --rm --no-deps amber python scripts/generar_claves_vapid.py
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


private_key = ec.generate_private_key(ec.SECP256R1())
public_bytes = private_key.public_key().public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
)
private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")

print(f"VAPID_PUBLIC_KEY={b64url(public_bytes)}")
print(f"VAPID_PRIVATE_KEY={b64url(private_bytes)}")
