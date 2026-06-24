"""
AES-256-GCM authenticated encryption and decryption.

Uses the `cryptography` library for symmetric file encryption.
Provides confidentiality and integrity in a single operation.
"""

import os
import time
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pangolin.logger import get_logger

# AES-256 key size in bytes
KEY_SIZE = 32

# GCM nonce size in bytes (96 bits as recommended by NIST)
NONCE_SIZE = 12

logger = get_logger()


def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    Derive a 256-bit AES key from a Kyber shared secret.

    Uses the first 32 bytes of the shared secret directly.
    Kyber768 produces a 32-byte shared secret, which maps
    directly to an AES-256 key.

    Args:
        shared_secret: The shared secret from Kyber KEM.

    Returns:
        32-byte AES-256 key.

    Raises:
        ValueError: If the shared secret is too short.
    """
    if len(shared_secret) < KEY_SIZE:
        raise ValueError(
            f"Shared secret too short: {len(shared_secret)} bytes "
            f"(need at least {KEY_SIZE})"
        )
    return shared_secret[:KEY_SIZE]


def encrypt_file(filepath: str | Path, key: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt a file using AES-256-GCM.

    Reads the entire file into memory, encrypts it, and returns
    the nonce, ciphertext, and authentication tag.

    Args:
        filepath: Path to the plaintext file.
        key: 32-byte AES-256 key.

    Returns:
        Tuple of (nonce, ciphertext, tag).
        Note: The `cryptography` library appends the 16-byte tag
        to the ciphertext. We split them for clarity.
    """
    filepath = Path(filepath)
    logger.info(f"Encrypting file: {filepath.name} ({filepath.stat().st_size} bytes)")
    start = time.perf_counter()

    # Read plaintext
    plaintext = filepath.read_bytes()

    # Generate random nonce
    nonce = os.urandom(NONCE_SIZE)

    # Encrypt with AES-256-GCM
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)

    # Split ciphertext and tag (last 16 bytes are the GCM tag)
    ciphertext = ciphertext_with_tag[:-16]
    tag = ciphertext_with_tag[-16:]

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Encryption completed in {elapsed_ms:.2f} ms "
        f"(ciphertext: {len(ciphertext)} bytes, tag: {len(tag)} bytes)"
    )

    return nonce, ciphertext, tag


def decrypt_file(
    nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes
) -> bytes:
    """
    Decrypt a file using AES-256-GCM.

    Verifies the authentication tag and returns the plaintext.

    Args:
        nonce: The 12-byte nonce used during encryption.
        ciphertext: The encrypted data.
        tag: The 16-byte GCM authentication tag.
        key: 32-byte AES-256 key.

    Returns:
        The decrypted plaintext bytes.

    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails.
    """
    logger.info(f"Decrypting data ({len(ciphertext)} bytes)...")
    start = time.perf_counter()

    # Reassemble ciphertext + tag as expected by the library
    ciphertext_with_tag = ciphertext + tag

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Decryption completed in {elapsed_ms:.2f} ms "
        f"(plaintext: {len(plaintext)} bytes)"
    )

    return plaintext
