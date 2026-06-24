#!/usr/bin/env python3
"""
Sender Tool: File Encryption
Encrypts a file using the Receiver's Kyber768 public key.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.aes import derive_aes_key, encrypt_file
from core.integrity import compute_hash
from core.kyber import encapsulate
from core.logger import setup_logger
from core.metadata import create_metadata, save_metadata


def main():
    parser = argparse.ArgumentParser(description="Sender: Encrypt file")
    parser.add_argument("--file", required=True, help="Path to file to encrypt")
    parser.add_argument("--pubkey", required=True, help="Path to receiver's public key")
    parser.add_argument("--out-dir", default="data/encrypted", help="Output directory")
    args = parser.parse_args()

    logger = setup_logger("sender", log_file="sender.log")
    
    filepath = Path(args.file).resolve()
    pubkey_path = Path(args.pubkey).resolve()
    
    # Resolve relative to sender/ directory
    out_dir = Path(__file__).resolve().parent / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  SENDER: Encrypting File")
    print("=" * 60)

    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)
    if not pubkey_path.exists():
        logger.error(f"Public key not found: {pubkey_path}")
        sys.exit(1)

    file_size = filepath.stat().st_size
    public_key = pubkey_path.read_bytes()

    original_hash = compute_hash(filepath)
    kem_ciphertext, shared_secret = encapsulate(public_key)
    aes_key = derive_aes_key(shared_secret)
    nonce, ciphertext, tag = encrypt_file(filepath, aes_key)

    enc_path = out_dir / f"{filepath.name}.enc"
    kem_path = out_dir / f"{filepath.name}.kem"
    meta_path = out_dir / f"{filepath.name}.meta.json"

    enc_path.write_bytes(nonce + tag + ciphertext)
    kem_path.write_bytes(kem_ciphertext)

    metadata = create_metadata(
        filename=filepath.name,
        filesize=file_size,
        original_hash=original_hash,
        extra={
            "nonce_size": len(nonce), 
            "tag_size": len(tag), 
            "ciphertext_size": len(ciphertext), 
            "kem_ciphertext_size": len(kem_ciphertext)
        }
    )
    save_metadata(metadata, meta_path)

    print("\n[!] TRANSFER REQUIRED: ")
    print(f"    Send the following files from '{out_dir.relative_to(Path.cwd())}' to the Receiver:")
    print(f"      1. {enc_path.name}")
    print(f"      2. {kem_path.name}")
    print(f"      3. {meta_path.name}\n")


if __name__ == "__main__":
    main()
