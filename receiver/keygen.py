#!/usr/bin/env python3
"""
Receiver Tool: Key Generation
Generates a Kyber768 key pair and saves the public and private keys.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path to import the pangolin core library
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.kyber import generate_keypair
from core.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(description="Receiver: Generate Kyber768 Keypair")
    parser.add_argument(
        "--out-dir",
        default="keys",
        help="Output directory for keys (default: keys/)",
    )
    args = parser.parse_args()

    logger = setup_logger("receiver", log_file="receiver.log")
    
    # Resolve relative to receiver/ directory
    out_dir = Path(__file__).resolve().parent / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  RECEIVER: Generating Kyber768 Key Pair")
    print("=" * 60)

    public_key, secret_key = generate_keypair()

    pub_path = out_dir / "public.bin"
    sec_path = out_dir / "secret.bin"

    pub_path.write_bytes(public_key)
    sec_path.write_bytes(secret_key)

    logger.info(f"Public key saved to: {pub_path}")
    logger.info(f"Secret key saved to: {sec_path}")
    
    print("\n[!] IMPORTANT: ")
    print(f"    Send '{pub_path.relative_to(Path.cwd())}' to the Sender.")
    print(f"    Keep '{sec_path.relative_to(Path.cwd())}' safe and secret.\n")


if __name__ == "__main__":
    main()
