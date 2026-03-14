"""AES-256-GCM encryption/decryption for statement files."""

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

IV_LENGTH = 12  # 96-bit IV recommended for GCM


def encrypt_bytes(key: bytes, plaintext: bytes) -> bytes:
    """Encrypt plaintext with AES-256-GCM. Returns iv + ciphertext + tag."""
    iv = os.urandom(IV_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)  # ciphertext includes 16-byte tag
    return iv + ciphertext


def decrypt_bytes(key: bytes, data: bytes) -> bytes:
    """Decrypt data produced by encrypt_bytes."""
    iv = data[:IV_LENGTH]
    ciphertext = data[IV_LENGTH:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext, None)
