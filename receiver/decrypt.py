#!/usr/bin/env python3
"""
Receiver Tool: File Decryption
Decrypts a received package using the Receiver's Kyber768 secret key.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.aes import decrypt_file, derive_aes_key
from core.integrity import verify_hash_bytes
from core.kyber import decapsulate
from core.logger import setup_logger
from core.metadata import load_metadata


def main():
    parser = argparse.ArgumentParser(description="Receiver: Decrypt file")
    parser.add_argument("--enc-file", required=True, help="Path to encrypted file (.enc)")
    parser.add_argument("--seckey", required=True, help="Path to your secret key")
    parser.add_argument("--out-dir", default="data/decrypted", help="Output directory")
    args = parser.parse_args()

    logger = setup_logger("receiver", log_file="receiver.log")
    
    enc_path = Path(args.enc_file).resolve()
    seckey_path = Path(args.seckey).resolve()
    
    base_name = enc_path.name.replace(".enc", "")
    kem_path = enc_path.parent / f"{base_name}.kem"
    meta_path = enc_path.parent / f"{base_name}.meta.json"

    # Resolve relative to receiver/ directory
    out_dir = Path(__file__).resolve().parent / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  RECEIVER: Decrypting File")
    print("=" * 60)

    if not enc_path.exists() or not kem_path.exists() or not meta_path.exists():
        logger.error(f"Missing required files in {enc_path.parent} (need .enc, .kem, .meta.json)")
        sys.exit(1)
    if not seckey_path.exists():
        logger.error(f"Secret key not found: {seckey_path}")
        sys.exit(1)

    secret_key = seckey_path.read_bytes()
    kem_ciphertext = kem_path.read_bytes()
    
    shared_secret = decapsulate(secret_key, kem_ciphertext)
    aes_key = derive_aes_key(shared_secret)

    received_data = enc_path.read_bytes()
    nonce = received_data[:12]
    tag = received_data[12:28]
    ciphertext = received_data[28:]

    plaintext = decrypt_file(nonce, ciphertext, tag, aes_key)
    
    decrypted_path = out_dir / base_name
    decrypted_path.write_bytes(plaintext)
    logger.info(f"Decrypted file saved to: {decrypted_path}")

    metadata = load_metadata(meta_path)
    
    print("\n" + "-" * 60)
    if verify_hash_bytes(plaintext, metadata["original_hash"]):
        print("  ✅ Integrity Verification PASSED: File is authentic and untampered.")
    else:
        print("  ❌ Integrity Verification FAILED: File has been tampered with or corrupted.")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
