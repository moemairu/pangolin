#!/usr/bin/env python3
"""
Pangolin — Post-Quantum Cryptography Proof-of-Concept

Main entry point that orchestrates the full secure file transfer
workflow using CRYSTALS-Kyber768, AES-256-GCM, and SHA-256.

Usage:
    python main.py                         Run demo with a generated sample file
    python main.py --file path/to/file     Encrypt and transfer a specific file
    python main.py --benchmark             Run performance benchmarks
    python main.py --file path --benchmark Run both demo and benchmarks
"""

import argparse
import os
import sys
from pathlib import Path

from pangolin.aes import decrypt_file, derive_aes_key, encrypt_file
from pangolin.benchmark import print_summary, run_full_benchmark, save_results
from pangolin.integrity import compute_hash, compute_hash_bytes, verify_hash_bytes
from pangolin.kyber import decapsulate, encapsulate, generate_keypair
from pangolin.logger import setup_logger
from pangolin.metadata import create_metadata, load_metadata, save_metadata
from pangolin.transfer import send, send_multiple

# Directory layout
BASE_DIR = Path(__file__).parent
SENDER_DIR = BASE_DIR / "data" / "sender"
ENCRYPTED_DIR = BASE_DIR / "data" / "encrypted"
RECEIVER_DIR = BASE_DIR / "data" / "receiver"


def create_sample_file(size_bytes: int = 1024 * 100) -> Path:
    """
    Create a sample file for demonstration.

    Args:
        size_bytes: Size of the sample file (default: 100 KB).

    Returns:
        Path to the created sample file.
    """
    SENDER_DIR.mkdir(parents=True, exist_ok=True)
    sample_path = SENDER_DIR / "sample_document.bin"
    sample_path.write_bytes(os.urandom(size_bytes))
    return sample_path


def run_demo(filepath: Path, logger) -> bool:
    """
    Run the full Pangolin secure file transfer demonstration.

    Workflow:
        1. Generate Kyber768 key pair (receiver side)
        2. Compute SHA-256 hash of original file
        3. Encapsulate shared secret (sender side)
        4. Derive AES-256 key from shared secret
        5. Encrypt file with AES-256-GCM
        6. Save encrypted data and metadata
        7. Simulate transfer to receiver
        8. Decapsulate shared secret (receiver side)
        9. Decrypt file
        10. Verify integrity with SHA-256

    Args:
        filepath: Path to the file to encrypt and transfer.
        logger: Logger instance.

    Returns:
        True if the entire workflow succeeds, False otherwise.
    """
    print("\n" + "=" * 60)
    print("  PANGOLIN — Post-Quantum Secure File Transfer Demo")
    print("=" * 60)

    # Ensure directories exist
    ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
    RECEIVER_DIR.mkdir(parents=True, exist_ok=True)

    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return False

    file_size = filepath.stat().st_size
    logger.info(f"Input file: {filepath.name} ({file_size:,} bytes)")

    # ──────────────────────────────────────────────────────────
    # STEP 1: Generate Kyber768 key pair (Receiver)
    # ──────────────────────────────────────────────────────────
    print("\n[Step 1] Generating Kyber768 key pair (Receiver)...")
    public_key, secret_key = generate_keypair()

    # ──────────────────────────────────────────────────────────
    # STEP 2: Compute SHA-256 hash of original file
    # ──────────────────────────────────────────────────────────
    print("[Step 2] Computing SHA-256 hash of original file...")
    original_hash = compute_hash(filepath)
    print(f"         Hash: {original_hash[:32]}...")

    # ──────────────────────────────────────────────────────────
    # STEP 3: Encapsulate shared secret (Sender)
    # ──────────────────────────────────────────────────────────
    print("[Step 3] Encapsulating shared secret (Sender)...")
    kem_ciphertext, shared_secret_sender = encapsulate(public_key)

    # ──────────────────────────────────────────────────────────
    # STEP 4: Derive AES-256 key from shared secret
    # ──────────────────────────────────────────────────────────
    print("[Step 4] Deriving AES-256 key from shared secret...")
    aes_key_sender = derive_aes_key(shared_secret_sender)
    logger.info(f"AES-256 key derived ({len(aes_key_sender)} bytes)")

    # ──────────────────────────────────────────────────────────
    # STEP 5: Encrypt file with AES-256-GCM
    # ──────────────────────────────────────────────────────────
    print("[Step 5] Encrypting file with AES-256-GCM...")
    nonce, ciphertext, tag = encrypt_file(filepath, aes_key_sender)

    # ──────────────────────────────────────────────────────────
    # STEP 6: Save encrypted data and metadata
    # ──────────────────────────────────────────────────────────
    print("[Step 6] Saving encrypted data and metadata...")

    # Save encrypted file
    encrypted_filepath = ENCRYPTED_DIR / f"{filepath.name}.enc"
    encrypted_filepath.write_bytes(nonce + tag + ciphertext)
    logger.info(f"Encrypted file saved: {encrypted_filepath}")

    # Save KEM ciphertext (needed for decapsulation)
    kem_filepath = ENCRYPTED_DIR / f"{filepath.name}.kem"
    kem_filepath.write_bytes(kem_ciphertext)
    logger.info(f"KEM ciphertext saved: {kem_filepath}")

    # Save metadata
    metadata = create_metadata(
        filename=filepath.name,
        filesize=file_size,
        original_hash=original_hash,
        extra={
            "nonce_size": len(nonce),
            "tag_size": len(tag),
            "ciphertext_size": len(ciphertext),
            "kem_ciphertext_size": len(kem_ciphertext),
        },
    )
    metadata_filepath = ENCRYPTED_DIR / f"{filepath.name}.meta.json"
    save_metadata(metadata, metadata_filepath)

    # ──────────────────────────────────────────────────────────
    # STEP 7: Simulate transfer to receiver
    # ──────────────────────────────────────────────────────────
    print("[Step 7] Simulating file transfer to receiver...")
    send_multiple(
        [encrypted_filepath, kem_filepath, metadata_filepath],
        RECEIVER_DIR,
    )

    # ──────────────────────────────────────────────────────────
    # STEP 8: Decapsulate shared secret (Receiver)
    # ──────────────────────────────────────────────────────────
    print("[Step 8] Decapsulating shared secret (Receiver)...")

    # Load KEM ciphertext from received files
    received_kem = (RECEIVER_DIR / f"{filepath.name}.kem").read_bytes()
    shared_secret_receiver = decapsulate(secret_key, received_kem)

    # Verify shared secrets match
    assert shared_secret_sender == shared_secret_receiver, (
        "CRITICAL: Shared secrets do not match!"
    )
    logger.info("Shared secrets match ✓")

    # ──────────────────────────────────────────────────────────
    # STEP 9: Decrypt file
    # ──────────────────────────────────────────────────────────
    print("[Step 9] Decrypting file with AES-256-GCM...")

    # Read encrypted file from received files
    received_data = (RECEIVER_DIR / f"{filepath.name}.enc").read_bytes()
    recv_nonce = received_data[:12]
    recv_tag = received_data[12:28]
    recv_ciphertext = received_data[28:]

    aes_key_receiver = derive_aes_key(shared_secret_receiver)
    decrypted_data = decrypt_file(recv_nonce, recv_ciphertext, recv_tag, aes_key_receiver)

    # Save decrypted file
    decrypted_filepath = RECEIVER_DIR / f"decrypted_{filepath.name}"
    decrypted_filepath.write_bytes(decrypted_data)
    logger.info(f"Decrypted file saved: {decrypted_filepath}")

    # ──────────────────────────────────────────────────────────
    # STEP 10: Verify integrity with SHA-256
    # ──────────────────────────────────────────────────────────
    print("[Step 10] Verifying file integrity with SHA-256...")

    # Load expected hash from metadata
    received_metadata = load_metadata(RECEIVER_DIR / f"{filepath.name}.meta.json")
    expected_hash = received_metadata["original_hash"]

    integrity_ok = verify_hash_bytes(decrypted_data, expected_hash)

    # ──────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if integrity_ok:
        print("  ✅ DEMO COMPLETED SUCCESSFULLY")
        print("  All cryptographic operations verified.")
    else:
        print("  ❌ DEMO FAILED — Integrity check did not pass.")
    print("=" * 60)

    print(f"\n  Original file:   {filepath}")
    print(f"  Encrypted file:  {encrypted_filepath}")
    print(f"  Decrypted file:  {decrypted_filepath}")
    print(f"  Metadata:        {metadata_filepath}")
    print(f"  File size:       {file_size:,} bytes")
    print(f"  Algorithm:       Kyber768 + AES-256-GCM")
    print(f"  Integrity:       SHA-256 {'PASS ✓' if integrity_ok else 'FAIL ✗'}")
    print()

    return integrity_ok


def run_benchmarks(logger) -> None:
    """
    Run performance benchmarks and save results.

    Args:
        logger: Logger instance.
    """
    print("\n" + "=" * 60)
    print("  PANGOLIN — Performance Benchmarks")
    print("=" * 60)

    results = run_full_benchmark(
        file_sizes=[
            1 * 1024,           # 1 KB
            100 * 1024,         # 100 KB
            1 * 1024 * 1024,    # 1 MB
            10 * 1024 * 1024,   # 10 MB
        ],
        iterations=5,
    )

    # Print summary table
    print_summary(results)

    # Save results to JSON
    results_path = BASE_DIR / "data" / "benchmark_results.json"
    save_results(results, results_path)
    print(f"\nResults saved to: {results_path}")


def main():
    """Parse arguments and run the appropriate workflow."""
    parser = argparse.ArgumentParser(
        description="Pangolin — Post-Quantum Cryptography Proof-of-Concept",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                         Run demo with generated sample file
  python main.py --file document.pdf     Encrypt a specific file
  python main.py --benchmark             Run performance benchmarks
  python main.py --file doc.pdf --bench  Both demo and benchmarks
        """,
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to the file to encrypt and transfer",
    )
    parser.add_argument(
        "--benchmark", "--bench", "-b",
        action="store_true",
        help="Run performance benchmarks",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100 * 1024,
        help="Size of the generated sample file in bytes (default: 100KB)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Initialize logging
    import logging
    log_level = getattr(logging, args.log_level.upper())
    logger = setup_logger(level=log_level)

    logger.info("Pangolin PoC starting...")

    # Determine what to run
    run_demo_flag = True
    if args.benchmark and not args.file:
        run_demo_flag = False

    if run_demo_flag:
        # Determine input file
        if args.file:
            filepath = Path(args.file)
            if not filepath.exists():
                logger.error(f"File not found: {filepath}")
                sys.exit(1)
        else:
            logger.info(f"Generating sample file ({args.sample_size:,} bytes)...")
            filepath = create_sample_file(args.sample_size)
            logger.info(f"Sample file created: {filepath}")

        success = run_demo(filepath, logger)
        if not success:
            sys.exit(1)

    if args.benchmark:
        run_benchmarks(logger)

    logger.info("Pangolin PoC finished.")


if __name__ == "__main__":
    main()
