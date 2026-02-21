"""
Manual check for CD-30.4 shipping address encryption.

Run from backend directory:
    py scripts/test_order_encryption.py
"""

from app.core.security import decrypt_field, encrypt_field


def test_shipping_address_encryption() -> None:
    """Validate encrypt/decrypt behavior for a sample shipping address."""
    shipping_address = "No 12, Main Street, Colombo 05"

    encrypted = encrypt_field(shipping_address)
    if not encrypted:
        raise RuntimeError("Encryption failed: encrypt_field returned empty value")

    if encrypted == shipping_address:
        raise RuntimeError("Encryption failed: value is still plain text")

    decrypted = decrypt_field(encrypted)
    if decrypted != shipping_address:
        raise RuntimeError("Decryption failed: decrypted value does not match input")

    print("CD-30.4 encryption test passed")
    print(f"Plain:     {shipping_address}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")


if __name__ == "__main__":
    test_shipping_address_encryption()
