<div align="center">

# 🦔 Pangolin 
*(assume this is a pangolin)*

**A Python proof-of-concept for quantum-resistant secure file transfer.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![NIST PQC](https://img.shields.io/badge/NIST-FIPS%20203%20%28ML--KEM%29-brightgreen.svg?style=flat)](https://csrc.nist.gov/pubs/fips/203/final)
[![liboqs](https://img.shields.io/badge/liboqs-Open%20Quantum%20Safe-yellow.svg?style=flat)](https://openquantumsafe.org/)
[![AES-256-GCM](https://img.shields.io/badge/Encryption-AES--256--GCM-blueviolet.svg?style=flat)]()
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=flat)](https://www.gnu.org/licenses/gpl-3.0)

[Overview](#-overview) • [Installation](#%EF%B8%8F-installation) • [Quick Start](#-quick-start) • [Documentation](DOCS.md)
</div>

---

## ✨ Overview

Pangolin simulates a real-world two-party file transfer where sender and receiver operate in **isolated workspaces**. The sender encrypts a file using the receiver's public key; the receiver decrypts it using their private key. No shared filesystem is assumed beyond the explicit transfer of three artifacts.

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Key Encapsulation** | **CRYSTALS-Kyber768 (FIPS 203)** | Quantum-resistant key exchange |
| **Symmetric Encryption** | **AES-256-GCM** | Authenticated file encryption |
| **Integrity** | **SHA-256** | Pre/post transfer hash verification |
| **Transfer** | **File copy (simulated)** | Mimics an out-of-band channel |

*For full technical details — cryptographic parameters, architecture diagrams, module reference, benchmarking, and security analysis — see [**DOCS.md**](DOCS.md).*

---

## 🛠️ Installation

### Prerequisites
- **Python 3.11+**
- **CMake**, **Ninja**, **GCC/Clang**, **OpenSSL headers** (for building `liboqs`)

### 1. Build liboqs (Native C Library)

**🐧 Ubuntu / Debian:**
```bash
sudo apt install -y cmake gcc ninja-build libssl-dev
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja .. && ninja && sudo ninja install && sudo ldconfig
```

**🍎 macOS:**
```bash
brew install cmake ninja openssl
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja -DOPENSSL_ROOT_DIR=$(brew --prefix openssl) ..
ninja && sudo ninja install
```

### 2. Install Python Dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Quick Start

Follow these steps to perform a complete quantum-secure file transfer simulation:

```bash
# 1. Receiver generates a Kyber768 keypair
python receiver/keygen.py
# → receiver/keys/public.bin  (share this)
# → receiver/keys/secret.bin  (keep this secret)

# 2. Share the public key with the sender
cp receiver/keys/public.bin sender/public_keys/public.bin

# 3. Sender encrypts a file
python sender/encrypt.py     --file "sender/data/document.pdf"     --pubkey "sender/public_keys/public.bin"
# → document.pdf.enc  (encrypted payload)
# → document.pdf.kem  (KEM ciphertext)
# → document.pdf.meta.json  (metadata + integrity hash)

# 4. Transfer all 3 files to the receiver
cp sender/data/encrypted/document.pdf.* receiver/data/received/

# 5. Receiver decrypts and verifies
python receiver/decrypt.py     --enc-file "receiver/data/received/document.pdf.enc"     --seckey "receiver/keys/secret.bin"
# → ✅ Integrity Verification PASSED: File is authentic and untampered.
```

---

## 🏗️ Project Structure

```text
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
├── README.md              # You are here! 👋
└── DOCS.md                # 📖 Full technical documentation
```

---

<div align="center">

  **🦔 Pangolin** — *Because even your files deserve quantum armor.*

</div>

---

<div align="center">
  <i>Licensed under the GNU GPLv3. See <a href="DOCS.md#security-notes">DOCS.md § Security Notes</a> for important caveats before any production use.</i>
</div>
