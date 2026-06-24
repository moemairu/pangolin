# 🦔 Pangolin *(this is a pangolin)*

A Python proof-of-concept for **quantum-resistant secure file transfer**, combining CRYSTALS-Kyber768 (post-quantum KEM) with AES-256-GCM (authenticated symmetric encryption).

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![NIST FIPS 203](https://img.shields.io/badge/NIST-FIPS%20203%20ML--KEM-5c6bc0?style=flat-square)](https://csrc.nist.gov/pubs/fips/203/final)
[![liboqs](https://img.shields.io/badge/liboqs-Open%20Quantum%20Safe-7b5ea7?style=flat-square)](https://openquantumsafe.org/)
[![AES-256-GCM](https://img.shields.io/badge/cipher-AES--256--GCM-2e7d32?style=flat-square)]()
[![License](https://img.shields.io/badge/license-Research%20%26%20Education-e65100?style=flat-square)]()

---

## Overview

Pangolin simulates a real-world two-party file transfer where sender and receiver operate in **isolated workspaces**. The sender encrypts a file using the receiver's public key; the receiver decrypts it using their private key. No shared filesystem is assumed beyond the explicit transfer of three artifacts.

| Component | Technology | Role |
|---|---|---|
| Key Encapsulation | CRYSTALS-Kyber768 (FIPS 203) | Quantum-resistant key exchange |
| Symmetric Encryption | AES-256-GCM | Authenticated file encryption |
| Integrity | SHA-256 | Pre/post transfer hash verification |
| Transfer | File copy (simulated) | Mimics an out-of-band channel |

For full technical details — cryptographic parameters, architecture diagrams, module reference, benchmarking, and security analysis — see **[DOCS.md](DOCS.md)**.

---

## Requirements

- Python 3.11+
- `liboqs` native C library ([build instructions in DOCS.md](DOCS.md#installation))

---

## Installation

### 1 — Build liboqs (native library)

**Ubuntu / Debian:**
```bash
sudo apt install -y cmake gcc ninja-build libssl-dev
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja .. && ninja && sudo ninja install && sudo ldconfig
```

**macOS:**
```bash
brew install cmake ninja openssl
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja -DOPENSSL_ROOT_DIR=$(brew --prefix openssl) ..
ninja && sudo ninja install
```

### 2 — Install Python dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Start

```bash
# 1. Receiver generates a Kyber768 keypair
python receiver/keygen.py
# → receiver/keys/public.bin  (share this)
# → receiver/keys/secret.bin  (keep this secret)

# 2. Share the public key with the sender
cp receiver/keys/public.bin sender/public_keys/public.bin

# 3. Sender encrypts a file
python sender/encrypt.py \
    --file "sender/data/document.pdf" \
    --pubkey "sender/public_keys/public.bin"
# → document.pdf.enc  (encrypted payload)
# → document.pdf.kem  (KEM ciphertext)
# → document.pdf.meta.json  (metadata + integrity hash)

# 4. Transfer all 3 files to the receiver
cp sender/data/encrypted/document.pdf.* receiver/data/received/

# 5. Receiver decrypts and verifies
python receiver/decrypt.py \
    --enc-file "receiver/data/received/document.pdf.enc" \
    --seckey "receiver/keys/secret.bin"
# → ✅ Integrity Verification PASSED: File is authentic and untampered.
```

---

## Project Structure

```
pangolin/
├── receiver/
│   ├── keygen.py          # CLI: generate Kyber768 keypair
│   ├── decrypt.py         # CLI: decrypt received package
│   └── core/              # cryptographic library
│       ├── kyber.py       # Kyber768 KEM wrapper
│       ├── aes.py         # AES-256-GCM encrypt/decrypt
│       ├── integrity.py   # SHA-256 hashing & verification
│       ├── metadata.py    # JSON metadata management
│       ├── logger.py      # dual-output logging
│       └── benchmark.py   # performance benchmarking suite
├── sender/
│   ├── encrypt.py         # CLI: encrypt file for receiver
│   └── core/              # cryptographic library (mirror)
├── requirements.txt
├── README.md
└── DOCS.md                # full technical documentation
```

---

## License

Research and educational use only. See [DOCS.md § Security Notes](DOCS.md#security-notes) for important caveats before any production use.
