#!/usr/bin/env python3
"""
Dataset Generator for Pangolin Benchmark Experiments.

Generates cryptographically secure random binary files of various sizes
for use in the experimental evaluation.
"""

import hashlib
import os
import sys
import time
from pathlib import Path

# File sizes to generate (in bytes)
FILE_SIZES = {
    "file_1MB.bin": 1 * 1024 * 1024,
    "file_5MB.bin": 5 * 1024 * 1024,
    "file_10MB.bin": 10 * 1024 * 1024,
    "file_50MB.bin": 50 * 1024 * 1024,
    "file_100MB.bin": 100 * 1024 * 1024,
    "file_500MB.bin": 500 * 1024 * 1024,
    "file_1000MB.bin": 1000 * 1024 * 1024,
}

# Write in chunks to avoid memory issues for large files
CHUNK_SIZE = 64 * 1024  # 64 KB


def generate_file(filepath: Path, size_bytes: int) -> str:
    """
    Generate a random binary file of the specified size.

    Uses os.urandom() for cryptographically secure random bytes.
    Writes in chunks to handle large files without excessive memory usage.

    Args:
        filepath: Path to write the file to.
        size_bytes: Desired file size in bytes.

    Returns:
        SHA-256 hex digest of the generated file.
    """
    sha256 = hashlib.sha256()
    bytes_written = 0

    with open(filepath, "wb") as f:
        while bytes_written < size_bytes:
            remaining = size_bytes - bytes_written
            chunk_size = min(CHUNK_SIZE, remaining)
            chunk = os.urandom(chunk_size)
            f.write(chunk)
            sha256.update(chunk)
            bytes_written += chunk_size

    return sha256.hexdigest()


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.0f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} B"


def main():
    project_root = Path(__file__).resolve().parent.parent
    dataset_dir = project_root / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("  PANGOLIN BENCHMARK — Dataset Generator")
    print("=" * 70)
    print(f"\n  Output directory: {dataset_dir}")
    print(f"  Generation method: os.urandom() (cryptographically secure)")
    print(f"  Files to generate: {len(FILE_SIZES)}")

    total_size = sum(FILE_SIZES.values())
    print(f"  Total size: {format_size(total_size)}")
    print()

    results = []

    for filename, size_bytes in FILE_SIZES.items():
        filepath = dataset_dir / filename
        size_label = format_size(size_bytes)

        print(f"  Generating {filename} ({size_label})... ", end="", flush=True)
        start = time.perf_counter()

        try:
            sha256_hash = generate_file(filepath, size_bytes)
            elapsed = time.perf_counter() - start

            # Verify file size
            actual_size = filepath.stat().st_size
            if actual_size != size_bytes:
                print(f"ERROR (size mismatch: expected {size_bytes}, got {actual_size})")
                continue

            print(f"OK ({elapsed:.2f}s)")
            print(f"    SHA-256: {sha256_hash}")

            results.append({
                "filename": filename,
                "size_bytes": size_bytes,
                "size_label": size_label,
                "sha256": sha256_hash,
                "generation_time_s": round(elapsed, 3),
            })

        except Exception as e:
            print(f"FAILED ({e})")
            continue

    print("\n" + "-" * 70)
    print(f"  Generated {len(results)}/{len(FILE_SIZES)} files successfully.")
    print("-" * 70 + "\n")

    if len(results) != len(FILE_SIZES):
        print("  WARNING: Some files failed to generate!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
