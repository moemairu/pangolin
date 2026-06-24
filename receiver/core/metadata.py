"""
JSON metadata management for encrypted file packages.

Stores and retrieves metadata about encrypted files including
algorithm information, file details, and timestamps.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import get_logger

logger = get_logger()


def create_metadata(
    filename: str,
    filesize: int,
    algorithm: str = "Kyber768 + AES-256-GCM",
    original_hash: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a metadata dictionary for an encrypted file.

    Args:
        filename: Original filename.
        filesize: Original file size in bytes.
        algorithm: Cryptographic algorithm description.
        original_hash: SHA-256 hash of the original plaintext file.
        extra: Additional metadata fields.

    Returns:
        Metadata dictionary.
    """
    metadata = {
        "filename": filename,
        "filesize": filesize,
        "algorithm": algorithm,
        "original_hash": original_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
    }

    if extra:
        metadata.update(extra)

    logger.info(f"Metadata created for: {filename}")
    return metadata


def save_metadata(metadata: Dict[str, Any], filepath: str | Path) -> None:
    """
    Save metadata dictionary as a JSON file.

    Args:
        metadata: The metadata dictionary to save.
        filepath: Output JSON file path.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Metadata saved to: {filepath}")


def load_metadata(filepath: str | Path) -> Dict[str, Any]:
    """
    Load metadata from a JSON file.

    Args:
        filepath: Path to the JSON metadata file.

    Returns:
        Metadata dictionary.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    filepath = Path(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    logger.info(f"Metadata loaded from: {filepath}")
    return metadata
