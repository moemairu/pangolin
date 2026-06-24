"""
CRYSTALS-Kyber768 Key Encapsulation Mechanism (KEM) wrapper.

Uses liboqs-python to provide post-quantum key exchange.
All operations are logged with timing information.
"""

import time
from typing import Tuple

import oqs

from pangolin.logger import get_logger

# NIST-standardized Kyber variant
ALGORITHM = "Kyber768"

logger = get_logger()


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate a Kyber768 key pair.

    Returns:
        Tuple of (public_key, secret_key) as raw bytes.
    """
    logger.info(f"Generating {ALGORITHM} key pair...")
    start = time.perf_counter()

    kem = oqs.KeyEncapsulation(ALGORITHM)
    public_key = kem.generate_keypair()
    secret_key = kem.export_secret_key()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Key pair generated in {elapsed_ms:.2f} ms "
        f"(public key: {len(public_key)} bytes, "
        f"secret key: {len(secret_key)} bytes)"
    )

    return public_key, secret_key


def encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
    """
    Encapsulate a shared secret using the recipient's public key.

    Args:
        public_key: Recipient's Kyber768 public key.

    Returns:
        Tuple of (ciphertext, shared_secret).
    """
    logger.info(f"Encapsulating shared secret with {ALGORITHM}...")
    start = time.perf_counter()

    kem = oqs.KeyEncapsulation(ALGORITHM)
    ciphertext, shared_secret = kem.encap_secret(public_key)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Encapsulation completed in {elapsed_ms:.2f} ms "
        f"(ciphertext: {len(ciphertext)} bytes, "
        f"shared secret: {len(shared_secret)} bytes)"
    )

    return ciphertext, shared_secret


def decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """
    Decapsulate a shared secret using the recipient's secret key.

    Args:
        secret_key: Recipient's Kyber768 secret key.
        ciphertext: Ciphertext from the encapsulation step.

    Returns:
        The recovered shared secret.
    """
    logger.info(f"Decapsulating shared secret with {ALGORITHM}...")
    start = time.perf_counter()

    kem = oqs.KeyEncapsulation(ALGORITHM, secret_key=secret_key)
    shared_secret = kem.decap_secret(ciphertext)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Decapsulation completed in {elapsed_ms:.2f} ms "
        f"(shared secret: {len(shared_secret)} bytes)"
    )

    return shared_secret
