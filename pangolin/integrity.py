"""
SHA-256 file integrity verification.

Provides hash computation and comparison for ensuring
files are not tampered with during transfer.
"""

import hashlib
import time
from pathlib import Path

from pangolin.logger import get_logger

# Buffer size for streaming hash computation (64 KB)
CHUNK_SIZE = 65536

logger = get_logger()


def compute_hash(filepath: str | Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Uses streaming (chunk-based) reading to handle large files
    without loading the entire file into memory.

    Args:
        filepath: Path to the file to hash.

    Returns:
        Hexadecimal digest string (64 characters).
    """
    filepath = Path(filepath)
    logger.info(f"Computing SHA-256 hash for: {filepath.name}")
    start = time.perf_counter()

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)

    digest = sha256.hexdigest()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"SHA-256 hash computed in {elapsed_ms:.2f} ms: {digest[:16]}...")

    return digest


def compute_hash_bytes(data: bytes) -> str:
    """
    Compute the SHA-256 hash of raw bytes.

    Args:
        data: The bytes to hash.

    Returns:
        Hexadecimal digest string (64 characters).
    """
    logger.info(f"Computing SHA-256 hash for {len(data)} bytes of data")
    start = time.perf_counter()

    digest = hashlib.sha256(data).hexdigest()

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"SHA-256 hash computed in {elapsed_ms:.2f} ms: {digest[:16]}...")

    return digest


def verify_hash(filepath: str | Path, expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 hash against an expected value.

    Args:
        filepath: Path to the file to verify.
        expected_hash: Expected hexadecimal SHA-256 digest.

    Returns:
        True if the hash matches, False otherwise.
    """
    filepath = Path(filepath)
    logger.info(f"Verifying integrity of: {filepath.name}")

    actual_hash = compute_hash(filepath)
    match = actual_hash == expected_hash

    if match:
        logger.info(f"Integrity verification PASSED for {filepath.name}")
    else:
        logger.warning(
            f"Integrity verification FAILED for {filepath.name}\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual_hash}"
        )

    return match


def verify_hash_bytes(data: bytes, expected_hash: str) -> bool:
    """
    Verify the SHA-256 hash of raw bytes against an expected value.

    Args:
        data: The bytes to verify.
        expected_hash: Expected hexadecimal SHA-256 digest.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_hash_bytes(data)
    match = actual_hash == expected_hash

    if match:
        logger.info("Integrity verification PASSED for decrypted data")
    else:
        logger.warning(
            f"Integrity verification FAILED for decrypted data\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual_hash}"
        )

    return match
