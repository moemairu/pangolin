# Pangolin — Experimental Evaluation Report

## Overview of the Experiment Scripts

This experimental evaluation was conducted using two primary scripts located in the `experiment/` directory:

1. **`generate_dataset.py`**: This script is responsible for generating the evaluation dataset. It creates 7 random binary files with sizes ranging from 1 MB to 1000 MB (1 GB). The files are populated using `os.urandom()` to ensure the data is cryptographically secure and non-compressible, accurately simulating real-world arbitrary data. The generated files are stored in the `dataset/` directory at the project root.

2. **`run_benchmark.py`**: This is the core benchmark execution script. It performs a true end-to-end simulation of the Pangolin cryptographic workflow. For every file generated in the dataset, the script runs 10 iterations. Each iteration involves:
   - Generating a Kyber768 keypair.
   - Encapsulating a shared secret (ML-KEM).
   - Deriving an AES-256 key and encrypting the file (AES-256-GCM).
   - Simulating network transfer by copying the files to the receiver's directory.
   - Decapsulating the shared secret and decrypting the file.
   - Verifying the SHA-256 integrity of the decrypted file against the original.
   - Completely cleaning up all artifacts (keys, encrypted files, decrypted files) to ensure a clean state for the next iteration.

   The script captures fine-grained timing metrics for each step, along with CPU and peak RAM usage, and outputs the raw data and statistics to the `experiment/benchmark/` directory (as JSON and CSV), as well as generating this Markdown report.

---

## 1. Experimental Environment

| Parameter | Value |
|---|---|
| **Operating System** | Linux-7.1.1-2-cachyos-x86_64-with-glibc2.43 |
| **Architecture** | x86_64 |
| **CPU** | AMD Ryzen 7 8845HS w/ Radeon 780M Graphics |
| **CPU Cores (Physical / Logical)** | 8 / 16 |
| **RAM Total** | 14.88 GB |
| **RAM Available (at start)** | 7.28 GB |
| **Python Version** | 3.14.6 |
| **Pangolin Version** | 0.1.0 |
| **cryptography** | 49.0.0 |
| **liboqs-python** | installed |
| **psutil** | 7.2.2 |
| **Date & Time (UTC)** | 2026-06-28T08:39:39.324820+00:00 |
| **Date & Time (Local)** | 2026-06-28 15:39:39  |

---

## 2. Dataset

All dataset files were generated using `os.urandom()` (cryptographically secure pseudo-random bytes).

| Filename | Size (Bytes) | Size (Human) | SHA-256 |
|---|---|---|---|
| `file_1MB.bin` | 1,048,576 | 1 MB | `29cbdbf9fc63d704...` |
| `file_5MB.bin` | 5,242,880 | 5 MB | `11e98f68fc1e019a...` |
| `file_10MB.bin` | 10,485,760 | 10 MB | `16ad0fd80793dc09...` |
| `file_50MB.bin` | 52,428,800 | 50 MB | `b743218a2e9c472a...` |
| `file_100MB.bin` | 104,857,600 | 100 MB | `f0e6fc1859610400...` |
| `file_500MB.bin` | 524,288,000 | 500 MB | `9525d0fe819f8146...` |
| `file_1000MB.bin` | 1,048,576,000 | 1000 MB | `22eb653f784a030f...` |

---

## 3. Experimental Procedure

### Methodology

- **Repetitions per file size:** 10
- **Total iterations:** 7 files × 10 iterations = 70

### Execution Workflow (per iteration)

Each iteration performs the complete Pangolin workflow as a real end-to-end simulation:

1. **Key Generation** — Receiver generates a Kyber768 keypair, writes `public.bin` and `secret.bin` to disk
2. **Public Key Distribution** — Public key is copied from `receiver/keys/` to `sender/public_keys/`
3. **ML-KEM Encapsulation** — Sender encapsulates a shared secret using the receiver's public key
4. **AES-256-GCM Encryption** — Sender encrypts the dataset file, writes `.enc`, `.kem`, `.meta.json` to disk
5. **Transfer Simulation** — All 3 encrypted artifacts are copied from `sender/data/encrypted/` to `receiver/data/received/`
6. **ML-KEM Decapsulation** — Receiver recovers the shared secret using their secret key
7. **AES-256-GCM Decryption** — Receiver decrypts the payload, writes the plaintext file to disk
8. **SHA-256 Integrity Verification** — Receiver computes the hash of the decrypted file and compares against the original hash
9. **Cleanup** — All artifacts (keys, encrypted files, received files, decrypted files) are deleted

### Measured Metrics

| Metric | Unit | Description |
|---|---|---|
| Keygen Time | ms | Kyber768 keypair generation + disk write |
| Encapsulation Time | ms | ML-KEM encapsulation |
| Encryption Time | ms | Hash computation + AES-256-GCM encryption + disk I/O |
| Transfer Time | ms | File copy simulation (3 files) |
| Decapsulation Time | ms | ML-KEM decapsulation |
| Decryption Time | ms | AES-256-GCM decryption + disk write |
| Hash Verification Time | ms | SHA-256 verification |
| Total Time | ms | End-to-end (keygen through verification) |
| Peak RAM | MB | Peak resident set size during iteration |
| CPU Usage | % | Process CPU utilization |
| Throughput | MB/s | file_size / total_time |
| SHA-256 Verification | PASS/FAIL | Integrity check result |

---

## 4. Results

### 1 MB (`file_1MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.404 | 0.328 | 0.287 | 1.065 | 0.237 |
| Encapsulation (ms) | 0.207 | 0.182 | 0.153 | 0.375 | 0.072 |
| Encryption (ms) | 3.008 | 2.841 | 2.645 | 3.672 | 0.343 |
| Transfer (ms) | 3.785 | 3.188 | 0.964 | 10.673 | 2.672 |
| Decapsulation (ms) | 0.235 | 0.186 | 0.170 | 0.455 | 0.093 |
| Decryption (ms) | 1.785 | 1.709 | 1.332 | 3.035 | 0.499 |
| Hash Verify (ms) | 0.974 | 0.947 | 0.837 | 1.149 | 0.115 |
| **Total (ms)** | 14.654 | 13.591 | 11.505 | 25.251 | 3.922 |
| Peak RAM (MB) | 43.316 | 43.415 | 42.410 | 43.440 | 0.319 |
| CPU (%) | 66.740 | 73.100 | 0.000 | 143.200 | 41.643 |
| Throughput (MB/s) | 71.283 | 73.622 | 39.602 | 86.920 | 12.946 |

### 5 MB (`file_5MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.417 | 0.410 | 0.344 | 0.563 | 0.068 |
| Encapsulation (ms) | 0.206 | 0.200 | 0.151 | 0.310 | 0.046 |
| Encryption (ms) | 11.085 | 10.691 | 9.457 | 13.323 | 1.174 |
| Transfer (ms) | 10.813 | 10.477 | 8.678 | 13.484 | 1.688 |
| Decapsulation (ms) | 0.258 | 0.239 | 0.210 | 0.349 | 0.045 |
| Decryption (ms) | 5.289 | 5.025 | 4.440 | 6.725 | 0.758 |
| Hash Verify (ms) | 3.335 | 3.266 | 3.075 | 3.717 | 0.228 |
| **Total (ms)** | 42.294 | 42.101 | 38.743 | 47.403 | 2.716 |
| Peak RAM (MB) | 66.972 | 67.470 | 62.470 | 67.480 | 1.582 |
| CPU (%) | 63.710 | 64.550 | 45.300 | 94.200 | 15.377 |
| Throughput (MB/s) | 118.647 | 118.769 | 105.479 | 129.057 | 7.412 |

### 10 MB (`file_10MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.409 | 0.394 | 0.322 | 0.545 | 0.079 |
| Encapsulation (ms) | 0.220 | 0.214 | 0.169 | 0.304 | 0.040 |
| Encryption (ms) | 18.699 | 18.971 | 17.312 | 20.393 | 0.997 |
| Transfer (ms) | 22.734 | 22.685 | 19.093 | 26.308 | 2.300 |
| Decapsulation (ms) | 0.287 | 0.254 | 0.224 | 0.457 | 0.081 |
| Decryption (ms) | 9.543 | 9.360 | 8.553 | 11.099 | 0.842 |
| Hash Verify (ms) | 6.598 | 6.272 | 6.065 | 8.868 | 0.868 |
| **Total (ms)** | 76.720 | 76.632 | 71.127 | 81.921 | 3.129 |
| Peak RAM (MB) | 96.512 | 97.510 | 87.500 | 97.530 | 3.167 |
| CPU (%) | 58.640 | 54.900 | 49.800 | 78.400 | 9.165 |
| Throughput (MB/s) | 130.541 | 130.493 | 122.069 | 140.593 | 5.356 |

### 50 MB (`file_50MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.412 | 0.383 | 0.346 | 0.557 | 0.072 |
| Encapsulation (ms) | 0.271 | 0.199 | 0.150 | 0.584 | 0.164 |
| Encryption (ms) | 94.144 | 94.085 | 86.968 | 106.956 | 5.445 |
| Transfer (ms) | 146.331 | 121.162 | 106.059 | 246.480 | 51.231 |
| Decapsulation (ms) | 0.255 | 0.227 | 0.203 | 0.376 | 0.061 |
| Decryption (ms) | 48.984 | 49.646 | 40.083 | 57.228 | 5.992 |
| Hash Verify (ms) | 33.553 | 32.663 | 29.878 | 39.986 | 3.542 |
| **Total (ms)** | 397.079 | 374.707 | 348.446 | 499.242 | 51.355 |
| Peak RAM (MB) | 287.829 | 287.835 | 287.800 | 287.840 | 0.014 |
| CPU (%) | 57.030 | 59.700 | 42.100 | 65.500 | 8.040 |
| Throughput (MB/s) | 127.641 | 133.445 | 100.152 | 143.494 | 14.837 |

### 100 MB (`file_100MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.392 | 0.379 | 0.315 | 0.611 | 0.085 |
| Encapsulation (ms) | 0.188 | 0.172 | 0.144 | 0.272 | 0.041 |
| Encryption (ms) | 231.772 | 195.690 | 180.169 | 431.715 | 81.707 |
| Transfer (ms) | 272.898 | 235.763 | 170.368 | 468.925 | 105.889 |
| Decapsulation (ms) | 0.279 | 0.221 | 0.210 | 0.461 | 0.091 |
| Decryption (ms) | 111.093 | 107.933 | 98.170 | 127.781 | 9.997 |
| Hash Verify (ms) | 104.624 | 70.576 | 61.840 | 394.734 | 102.904 |
| **Total (ms)** | 864.936 | 859.619 | 652.729 | 1180.909 | 171.798 |
| Peak RAM (MB) | 537.762 | 537.765 | 537.730 | 537.780 | 0.014 |
| CPU (%) | 54.370 | 53.850 | 45.000 | 65.300 | 7.338 |
| Throughput (MB/s) | 119.810 | 116.348 | 84.681 | 153.203 | 23.866 |

### 500 MB (`file_500MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.447 | 0.440 | 0.332 | 0.635 | 0.089 |
| Encapsulation (ms) | 0.198 | 0.185 | 0.140 | 0.260 | 0.037 |
| Encryption (ms) | 1898.692 | 1689.822 | 1467.657 | 2462.497 | 390.470 |
| Transfer (ms) | 514.194 | 428.138 | 287.918 | 1089.169 | 257.718 |
| Decapsulation (ms) | 0.295 | 0.283 | 0.204 | 0.413 | 0.082 |
| Decryption (ms) | 1515.870 | 1481.411 | 1113.109 | 2189.156 | 388.690 |
| Hash Verify (ms) | 506.083 | 523.691 | 405.583 | 730.011 | 102.845 |
| **Total (ms)** | 5227.290 | 5447.271 | 4058.007 | 6663.034 | 914.440 |
| Peak RAM (MB) | 2525.297 | 2524.120 | 2523.440 | 2537.780 | 4.397 |
| CPU (%) | 54.700 | 54.600 | 47.600 | 61.600 | 4.996 |
| Throughput (MB/s) | 98.424 | 91.794 | 75.041 | 123.213 | 17.739 |

### 1000 MB (`file_1000MB.bin`)

- **Total iterations:** 10
- **Successful:** 10
- **Failed:** 0
- **SHA-256 PASS:** 10 | **FAIL:** 0

| Metric | Mean | Median | Min | Max | Std Dev |
|---|---|---|---|---|---|
| Keygen (ms) | 0.940 | 0.377 | 0.342 | 5.912 | 1.748 |
| Encapsulation (ms) | 0.192 | 0.181 | 0.142 | 0.344 | 0.055 |
| Encryption (ms) | 5009.651 | 4796.828 | 3921.627 | 7008.426 | 1039.109 |
| Transfer (ms) | 579.014 | 466.514 | 288.439 | 1475.355 | 369.494 |
| Decapsulation (ms) | 0.334 | 0.330 | 0.211 | 0.469 | 0.092 |
| Decryption (ms) | 3649.486 | 3614.071 | 2656.412 | 5176.315 | 687.383 |
| Hash Verify (ms) | 871.420 | 861.353 | 783.577 | 957.224 | 53.423 |
| **Total (ms)** | 11601.994 | 11552.979 | 9296.342 | 13959.767 | 1247.056 |
| Peak RAM (MB) | 4900.756 | 4932.450 | 4713.570 | 5022.960 | 119.558 |
| CPU (%) | 49.790 | 49.050 | 39.200 | 58.500 | 6.392 |
| Throughput (MB/s) | 87.116 | 86.572 | 71.634 | 107.569 | 9.661 |

---

## 5. Raw Console Output

```

======================================================================
  PANGOLIN BENCHMARK — Full End-to-End Simulation
======================================================================
  Started at: 2026-06-28 15:39:39
  Iterations per file: 10
  Dataset files: 7
  Total planned iterations: 70

  OS: Linux-7.1.1-2-cachyos-x86_64-with-glibc2.43
  CPU: AMD Ryzen 7 8845HS w/ Radeon 780M Graphics
  RAM: 14.88 GB total, 7.28 GB available
  Python: 3.14.6

  Verifying dataset files...
    ✅ file_1MB.bin (1 MB) — 29cbdbf9fc63d704...
    ✅ file_5MB.bin (5 MB) — 11e98f68fc1e019a...
    ✅ file_10MB.bin (10 MB) — 16ad0fd80793dc09...
    ✅ file_50MB.bin (50 MB) — b743218a2e9c472a...
    ✅ file_100MB.bin (100 MB) — f0e6fc1859610400...
    ✅ file_500MB.bin (500 MB) — 9525d0fe819f8146...
    ✅ file_1000MB.bin (1000 MB) — 22eb653f784a030f...


======================================================================
  FILE 1/7: file_1MB.bin (1 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (1.065 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.375 ms)
    [4/7] AES-256-GCM encryption...
          Done (3.672 ms)
    [5/7] Transfer simulation...
          Done (10.673 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.455 ms
          Decryption:    3.035 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (1.116 ms)

    Summary: Total=25.251 ms | RAM=42.41 MB | Throughput=39.602 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.353 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.199 ms)
    [4/7] AES-256-GCM encryption...
          Done (3.151 ms)
    [5/7] Transfer simulation...
          Done (2.315 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.189 ms
          Decryption:    2.007 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (1.034 ms)

    Summary: Total=16.175 ms | RAM=43.40 MB | Throughput=61.826 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.297 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.154 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.645 ms)
    [5/7] Transfer simulation...
          Done (4.594 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.287 ms
          Decryption:    1.856 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (1.086 ms)

    Summary: Total=13.909 ms | RAM=43.40 MB | Throughput=71.895 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.331 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.170 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.815 ms)
    [5/7] Transfer simulation...
          Done (4.021 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.217 ms
          Decryption:    1.457 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.851 ms)

    Summary: Total=12.938 ms | RAM=43.41 MB | Throughput=77.292 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.325 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.173 ms)
    [4/7] AES-256-GCM encryption...
          Done (3.047 ms)
    [5/7] Transfer simulation...
          Done (2.423 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.180 ms
          Decryption:    1.825 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.883 ms)

    Summary: Total=14.004 ms | RAM=43.41 MB | Throughput=71.408 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.330 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.207 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.793 ms)
    [5/7] Transfer simulation...
          Done (3.935 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.183 ms
          Decryption:    1.413 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.923 ms)

    Summary: Total=12.417 ms | RAM=43.42 MB | Throughput=80.537 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.299 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.153 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.785 ms)
    [5/7] Transfer simulation...
          Done (2.314 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.170 ms
          Decryption:    1.432 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.970 ms)

    Summary: Total=12.997 ms | RAM=43.42 MB | Throughput=76.939 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.454 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.293 ms)
    [4/7] AES-256-GCM encryption...
          Done (3.519 ms)
    [5/7] Transfer simulation...
          Done (0.964 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.179 ms
          Decryption:    1.898 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.886 ms)

    Summary: Total=14.072 ms | RAM=43.42 MB | Throughput=71.064 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.297 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.153 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.785 ms)
    [5/7] Transfer simulation...
          Done (2.441 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.173 ms
          Decryption:    1.593 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (0.837 ms)

    Summary: Total=11.505 ms | RAM=43.43 MB | Throughput=86.920 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.287 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.192 ms)
    [4/7] AES-256-GCM encryption...
          Done (2.866 ms)
    [5/7] Transfer simulation...
          Done (4.170 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.321 ms
          Decryption:    1.332 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (1.149 ms)

    Summary: Total=13.272 ms | RAM=43.44 MB | Throughput=75.349 MB/s | SHA-256=PASS

======================================================================
  FILE 2/7: file_5MB.bin (5 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.364 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.201 ms)
    [4/7] AES-256-GCM encryption...
          Done (13.323 ms)
    [5/7] Transfer simulation...
          Done (12.559 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.210 ms
          Decryption:    4.923 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.664 ms)

    Summary: Total=47.403 ms | RAM=62.47 MB | Throughput=105.479 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.413 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.199 ms)
    [4/7] AES-256-GCM encryption...
          Done (12.486 ms)
    [5/7] Transfer simulation...
          Done (8.765 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.249 ms
          Decryption:    5.179 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.717 ms)

    Summary: Total=41.768 ms | RAM=67.46 MB | Throughput=119.709 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.431 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.221 ms)
    [4/7] AES-256-GCM encryption...
          Done (11.191 ms)
    [5/7] Transfer simulation...
          Done (9.504 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.349 ms
          Decryption:    4.440 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.075 ms)

    Summary: Total=39.837 ms | RAM=67.46 MB | Throughput=125.511 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.344 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.163 ms)
    [4/7] AES-256-GCM encryption...
          Done (10.499 ms)
    [5/7] Transfer simulation...
          Done (10.671 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.229 ms
          Decryption:    5.097 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.542 ms)

    Summary: Total=42.434 ms | RAM=67.47 MB | Throughput=117.830 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.484 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.226 ms)
    [4/7] AES-256-GCM encryption...
          Done (10.827 ms)
    [5/7] Transfer simulation...
          Done (10.283 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.226 ms
          Decryption:    6.128 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.216 ms)

    Summary: Total=42.496 ms | RAM=67.47 MB | Throughput=117.659 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.407 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.192 ms)
    [4/7] AES-256-GCM encryption...
          Done (10.150 ms)
    [5/7] Transfer simulation...
          Done (11.513 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.308 ms
          Decryption:    6.725 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.332 ms)

    Summary: Total=44.131 ms | RAM=67.47 MB | Throughput=113.300 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.367 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.161 ms)
    [4/7] AES-256-GCM encryption...
          Done (10.414 ms)
    [5/7] Transfer simulation...
          Done (8.678 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.229 ms
          Decryption:    4.590 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.130 ms)

    Summary: Total=38.743 ms | RAM=67.48 MB | Throughput=129.057 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.446 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.235 ms)
    [4/7] AES-256-GCM encryption...
          Done (10.554 ms)
    [5/7] Transfer simulation...
          Done (9.985 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.235 ms
          Decryption:    4.767 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.275 ms)

    Summary: Total=39.924 ms | RAM=67.48 MB | Throughput=125.238 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.563 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.310 ms)
    [4/7] AES-256-GCM encryption...
          Done (11.948 ms)
    [5/7] Transfer simulation...
          Done (13.484 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.243 ms
          Decryption:    6.084 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.139 ms)

    Summary: Total=45.448 ms | RAM=67.48 MB | Throughput=110.015 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.351 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.151 ms)
    [4/7] AES-256-GCM encryption...
          Done (9.457 ms)
    [5/7] Transfer simulation...
          Done (12.685 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.298 ms
          Decryption:    4.953 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (3.258 ms)

    Summary: Total=40.759 ms | RAM=67.48 MB | Throughput=122.673 MB/s | SHA-256=PASS

======================================================================
  FILE 3/7: file_10MB.bin (10 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.412 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.215 ms)
    [4/7] AES-256-GCM encryption...
          Done (17.633 ms)
    [5/7] Transfer simulation...
          Done (23.020 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.236 ms
          Decryption:    8.662 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.067 ms)

    Summary: Total=74.530 ms | RAM=87.50 MB | Throughput=134.174 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.425 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.242 ms)
    [4/7] AES-256-GCM encryption...
          Done (18.918 ms)
    [5/7] Transfer simulation...
          Done (24.614 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.457 ms
          Decryption:    10.346 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.291 ms)

    Summary: Total=78.486 ms | RAM=97.49 MB | Throughput=127.411 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.545 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.304 ms)
    [4/7] AES-256-GCM encryption...
          Done (19.292 ms)
    [5/7] Transfer simulation...
          Done (23.131 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.230 ms
          Decryption:    9.204 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.100 ms)

    Summary: Total=77.845 ms | RAM=97.50 MB | Throughput=128.461 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.394 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.169 ms)
    [4/7] AES-256-GCM encryption...
          Done (17.312 ms)
    [5/7] Transfer simulation...
          Done (22.350 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.271 ms
          Decryption:    11.099 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.519 ms)

    Summary: Total=75.893 ms | RAM=97.50 MB | Throughput=131.764 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.392 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.199 ms)
    [4/7] AES-256-GCM encryption...
          Done (20.393 ms)
    [5/7] Transfer simulation...
          Done (26.308 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.287 ms
          Decryption:    8.665 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.094 ms)

    Summary: Total=80.196 ms | RAM=97.51 MB | Throughput=124.695 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.336 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.191 ms)
    [4/7] AES-256-GCM encryption...
          Done (19.645 ms)
    [5/7] Transfer simulation...
          Done (22.206 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.287 ms
          Decryption:    9.410 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.065 ms)

    Summary: Total=76.825 ms | RAM=97.51 MB | Throughput=130.166 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.541 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.253 ms)
    [4/7] AES-256-GCM encryption...
          Done (19.023 ms)
    [5/7] Transfer simulation...
          Done (21.608 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.224 ms
          Decryption:    9.310 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (7.176 ms)

    Summary: Total=76.440 ms | RAM=97.52 MB | Throughput=130.821 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.322 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.214 ms)
    [4/7] AES-256-GCM encryption...
          Done (17.882 ms)
    [5/7] Transfer simulation...
          Done (19.676 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.237 ms
          Decryption:    8.553 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.253 ms)

    Summary: Total=71.127 ms | RAM=97.53 MB | Throughput=140.593 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.393 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.239 ms)
    [4/7] AES-256-GCM encryption...
          Done (17.807 ms)
    [5/7] Transfer simulation...
          Done (25.331 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.406 ms
          Decryption:    10.155 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (8.868 ms)

    Summary: Total=81.921 ms | RAM=97.53 MB | Throughput=122.069 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.331 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.178 ms)
    [4/7] AES-256-GCM encryption...
          Done (19.086 ms)
    [5/7] Transfer simulation...
          Done (19.093 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.234 ms
          Decryption:    10.022 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (6.550 ms)

    Summary: Total=73.936 ms | RAM=97.53 MB | Throughput=135.251 MB/s | SHA-256=PASS

======================================================================
  FILE 4/7: file_50MB.bin (50 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.367 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.194 ms)
    [4/7] AES-256-GCM encryption...
          Done (106.956 ms)
    [5/7] Transfer simulation...
          Done (106.059 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.221 ms
          Decryption:    53.679 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (39.986 ms)

    Summary: Total=377.488 ms | RAM=287.80 MB | Throughput=132.454 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.346 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.154 ms)
    [4/7] AES-256-GCM encryption...
          Done (91.232 ms)
    [5/7] Transfer simulation...
          Done (129.778 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.331 ms
          Decryption:    48.698 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (33.378 ms)

    Summary: Total=378.770 ms | RAM=287.81 MB | Throughput=132.006 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.474 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.253 ms)
    [4/7] AES-256-GCM encryption...
          Done (94.709 ms)
    [5/7] Transfer simulation...
          Done (109.744 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.214 ms
          Decryption:    50.594 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (31.090 ms)

    Summary: Total=355.963 ms | RAM=287.82 MB | Throughput=140.464 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.418 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.584 ms)
    [4/7] AES-256-GCM encryption...
          Done (94.646 ms)
    [5/7] Transfer simulation...
          Done (106.448 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.233 ms
          Decryption:    41.510 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (30.982 ms)

    Summary: Total=348.446 ms | RAM=287.83 MB | Throughput=143.494 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.398 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.280 ms)
    [4/7] AES-256-GCM encryption...
          Done (97.736 ms)
    [5/7] Transfer simulation...
          Done (112.052 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.308 ms
          Decryption:    52.155 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (33.774 ms)

    Summary: Total=366.361 ms | RAM=287.83 MB | Throughput=136.477 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.557 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.560 ms)
    [4/7] AES-256-GCM encryption...
          Done (86.968 ms)
    [5/7] Transfer simulation...
          Done (246.480 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.241 ms
          Decryption:    44.850 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (33.996 ms)

    Summary: Total=499.242 ms | RAM=287.84 MB | Throughput=100.152 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.359 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.150 ms)
    [4/7] AES-256-GCM encryption...
          Done (94.807 ms)
    [5/7] Transfer simulation...
          Done (112.547 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.203 ms
          Decryption:    57.228 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (31.947 ms)

    Summary: Total=369.245 ms | RAM=287.84 MB | Throughput=135.412 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.356 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.204 ms)
    [4/7] AES-256-GCM encryption...
          Done (93.524 ms)
    [5/7] Transfer simulation...
          Done (203.673 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.209 ms
          Decryption:    40.083 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (30.963 ms)

    Summary: Total=441.380 ms | RAM=287.84 MB | Throughput=113.281 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.488 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.165 ms)
    [4/7] AES-256-GCM encryption...
          Done (89.795 ms)
    [5/7] Transfer simulation...
          Done (135.101 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.376 ms
          Decryption:    44.886 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (29.878 ms)

    Summary: Total=371.925 ms | RAM=287.84 MB | Throughput=134.436 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.357 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.167 ms)
    [4/7] AES-256-GCM encryption...
          Done (91.063 ms)
    [5/7] Transfer simulation...
          Done (201.428 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.214 ms
          Decryption:    56.158 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (39.536 ms)

    Summary: Total=461.965 ms | RAM=287.84 MB | Throughput=108.233 MB/s | SHA-256=PASS

======================================================================
  FILE 5/7: file_100MB.bin (100 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.611 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.169 ms)
    [4/7] AES-256-GCM encryption...
          Done (206.525 ms)
    [5/7] Transfer simulation...
          Done (266.690 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.216 ms
          Decryption:    107.013 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (75.006 ms)

    Summary: Total=830.418 ms | RAM=537.73 MB | Throughput=120.421 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.323 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.148 ms)
    [4/7] AES-256-GCM encryption...
          Done (317.351 ms)
    [5/7] Transfer simulation...
          Done (184.186 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.327 ms
          Decryption:    126.419 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (394.734 ms)

    Summary: Total=1180.909 ms | RAM=537.75 MB | Throughput=84.681 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.381 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.183 ms)
    [4/7] AES-256-GCM encryption...
          Done (219.136 ms)
    [5/7] Transfer simulation...
          Done (358.976 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.226 ms
          Decryption:    127.781 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (110.237 ms)

    Summary: Total=969.265 ms | RAM=537.76 MB | Throughput=103.171 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.315 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.167 ms)
    [4/7] AES-256-GCM encryption...
          Done (431.715 ms)
    [5/7] Transfer simulation...
          Done (204.837 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.213 ms
          Decryption:    105.908 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (61.840 ms)

    Summary: Total=939.176 ms | RAM=537.76 MB | Throughput=106.476 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.376 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.232 ms)
    [4/7] AES-256-GCM encryption...
          Done (180.169 ms)
    [5/7] Transfer simulation...
          Done (189.339 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.214 ms
          Decryption:    108.274 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (63.445 ms)

    Summary: Total=676.248 ms | RAM=537.76 MB | Throughput=147.875 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.432 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.272 ms)
    [4/7] AES-256-GCM encryption...
          Done (183.114 ms)
    [5/7] Transfer simulation...
          Done (170.368 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.461 ms
          Decryption:    101.318 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (71.310 ms)

    Summary: Total=658.872 ms | RAM=537.77 MB | Throughput=151.775 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.366 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.226 ms)
    [4/7] AES-256-GCM encryption...
          Done (184.856 ms)
    [5/7] Transfer simulation...
          Done (334.373 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.210 ms
          Decryption:    109.742 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (72.335 ms)

    Summary: Total=849.047 ms | RAM=537.77 MB | Throughput=117.779 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.393 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.165 ms)
    [4/7] AES-256-GCM encryption...
          Done (228.733 ms)
    [5/7] Transfer simulation...
          Done (468.925 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.394 ms
          Decryption:    118.710 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (69.841 ms)

    Summary: Total=1022.502 ms | RAM=537.77 MB | Throughput=97.799 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.393 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.176 ms)
    [4/7] AES-256-GCM encryption...
          Done (183.509 ms)
    [5/7] Transfer simulation...
          Done (378.713 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.213 ms
          Decryption:    107.591 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (64.141 ms)

    Summary: Total=870.190 ms | RAM=537.77 MB | Throughput=114.917 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.330 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.144 ms)
    [4/7] AES-256-GCM encryption...
          Done (182.613 ms)
    [5/7] Transfer simulation...
          Done (172.570 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.316 ms
          Decryption:    98.170 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (63.348 ms)

    Summary: Total=652.729 ms | RAM=537.78 MB | Throughput=153.203 MB/s | SHA-256=PASS

======================================================================
  FILE 6/7: file_500MB.bin (500 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.457 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.218 ms)
    [4/7] AES-256-GCM encryption...
          Done (2462.497 ms)
    [5/7] Transfer simulation...
          Done (287.918 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.205 ms
          Decryption:    1203.236 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (730.011 ms)

    Summary: Total=5487.044 ms | RAM=2537.78 MB | Throughput=91.124 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.404 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.189 ms)
    [4/7] AES-256-GCM encryption...
          Done (2287.642 ms)
    [5/7] Transfer simulation...
          Done (343.941 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.221 ms
          Decryption:    1707.495 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (549.032 ms)

    Summary: Total=5822.288 ms | RAM=2524.08 MB | Throughput=85.877 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.635 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.182 ms)
    [4/7] AES-256-GCM encryption...
          Done (2389.906 ms)
    [5/7] Transfer simulation...
          Done (668.455 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.316 ms
          Decryption:    2189.156 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (540.500 ms)

    Summary: Total=6663.034 ms | RAM=2524.11 MB | Throughput=75.041 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.332 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.140 ms)
    [4/7] AES-256-GCM encryption...
          Done (2221.930 ms)
    [5/7] Transfer simulation...
          Done (512.335 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.413 ms
          Decryption:    1879.360 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (558.333 ms)

    Summary: Total=5978.159 ms | RAM=2524.13 MB | Throughput=83.638 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.357 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.182 ms)
    [4/7] AES-256-GCM encryption...
          Done (1583.654 ms)
    [5/7] Transfer simulation...
          Done (717.000 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.251 ms
          Decryption:    1807.877 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (506.882 ms)

    Summary: Total=5407.499 ms | RAM=2524.14 MB | Throughput=92.464 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.389 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.239 ms)
    [4/7] AES-256-GCM encryption...
          Done (1558.876 ms)
    [5/7] Transfer simulation...
          Done (323.993 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.204 ms
          Decryption:    1113.109 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (407.896 ms)

    Summary: Total=4082.926 ms | RAM=2524.14 MB | Throughput=122.461 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.537 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.159 ms)
    [4/7] AES-256-GCM encryption...
          Done (1635.111 ms)
    [5/7] Transfer simulation...
          Done (575.478 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.361 ms
          Decryption:    1158.142 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (410.203 ms)

    Summary: Total=4525.248 ms | RAM=2524.16 MB | Throughput=110.491 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.437 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.182 ms)
    [4/7] AES-256-GCM encryption...
          Done (1693.653 ms)
    [5/7] Transfer simulation...
          Done (301.455 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.355 ms
          Decryption:    1255.328 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (410.736 ms)

    Summary: Total=4331.943 ms | RAM=2523.54 MB | Throughput=115.422 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.443 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.229 ms)
    [4/7] AES-256-GCM encryption...
          Done (1685.991 ms)
    [5/7] Transfer simulation...
          Done (1089.169 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.392 ms
          Decryption:    1721.701 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (541.653 ms)

    Summary: Total=5916.754 ms | RAM=2523.44 MB | Throughput=84.506 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.480 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.260 ms)
    [4/7] AES-256-GCM encryption...
          Done (1467.657 ms)
    [5/7] Transfer simulation...
          Done (322.194 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.229 ms
          Decryption:    1123.292 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (405.583 ms)

    Summary: Total=4058.007 ms | RAM=2523.45 MB | Throughput=123.213 MB/s | SHA-256=PASS

======================================================================
  FILE 7/7: file_1000MB.bin (1000 MB)
======================================================================

  ── Iteration 1/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.353 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.163 ms)
    [4/7] AES-256-GCM encryption...
          Done (4346.881 ms)
    [5/7] Transfer simulation...
          Done (288.439 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.229 ms
          Decryption:    4142.813 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (783.577 ms)

    Summary: Total=11266.743 ms | RAM=5022.96 MB | Throughput=88.757 MB/s | SHA-256=PASS

  ── Iteration 2/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.515 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.189 ms)
    [4/7] AES-256-GCM encryption...
          Done (4532.059 ms)
    [5/7] Transfer simulation...
          Done (353.204 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.366 ms
          Decryption:    3714.407 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (957.224 ms)

    Summary: Total=11191.546 ms | RAM=4760.49 MB | Throughput=89.353 MB/s | SHA-256=PASS

  ── Iteration 3/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.392 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.173 ms)
    [4/7] AES-256-GCM encryption...
          Done (3921.627 ms)
    [5/7] Transfer simulation...
          Done (322.950 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.234 ms
          Decryption:    5176.315 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (873.772 ms)

    Summary: Total=11698.398 ms | RAM=4790.52 MB | Throughput=85.482 MB/s | SHA-256=PASS

  ── Iteration 4/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.343 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.185 ms)
    [4/7] AES-256-GCM encryption...
          Done (4026.897 ms)
    [5/7] Transfer simulation...
          Done (308.983 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.211 ms
          Decryption:    3705.823 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (835.601 ms)

    Summary: Total=10451.839 ms | RAM=4816.54 MB | Throughput=95.677 MB/s | SHA-256=PASS

  ── Iteration 5/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.362 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.183 ms)
    [4/7] AES-256-GCM encryption...
          Done (5061.598 ms)
    [5/7] Transfer simulation...
          Done (812.083 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.469 ms
          Decryption:    3862.990 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (847.085 ms)

    Summary: Total=12039.701 ms | RAM=4713.57 MB | Throughput=83.059 MB/s | SHA-256=PASS

  ── Iteration 6/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.424 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.183 ms)
    [4/7] AES-256-GCM encryption...
          Done (4065.940 ms)
    [5/7] Transfer simulation...
          Done (307.248 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.332 ms
          Decryption:    2656.412 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (833.743 ms)

    Summary: Total=9296.342 ms | RAM=5012.70 MB | Throughput=107.569 MB/s | SHA-256=PASS

  ── Iteration 7/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.343 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.142 ms)
    [4/7] AES-256-GCM encryption...
          Done (5570.002 ms)
    [5/7] Transfer simulation...
          Done (727.089 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.386 ms
          Decryption:    3512.865 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (866.437 ms)

    Summary: Total=12082.249 ms | RAM=4927.72 MB | Throughput=82.766 MB/s | SHA-256=PASS

  ── Iteration 8/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (5.912 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.344 ms)
    [4/7] AES-256-GCM encryption...
          Done (5278.178 ms)
    [5/7] Transfer simulation...
          Done (614.967 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.327 ms
          Decryption:    3122.947 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (922.126 ms)

    Summary: Total=11407.561 ms | RAM=5012.72 MB | Throughput=87.661 MB/s | SHA-256=PASS

  ── Iteration 9/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.342 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.179 ms)
    [4/7] AES-256-GCM encryption...
          Done (6284.904 ms)
    [5/7] Transfer simulation...
          Done (579.824 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.313 ms
          Decryption:    3522.319 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (856.270 ms)

    Summary: Total=12625.798 ms | RAM=4937.18 MB | Throughput=79.203 MB/s | SHA-256=PASS

  ── Iteration 10/10 ──
    [1/7] Generating Kyber768 keypair...
          Done (0.412 ms)
    [2/7] Copying public key to sender...
          /home/mole/Documents/Penelitian/CE/pangolin/receiver/keys/public.bin → /home/mole/Documents/Penelitian/CE/pangolin/sender/public_keys/public.bin
    [3/7] ML-KEM encapsulation...
          Done (0.176 ms)
    [4/7] AES-256-GCM encryption...
          Done (7008.426 ms)
    [5/7] Transfer simulation...
          Done (1475.355 ms)
    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...
          Decapsulation: 0.469 ms
          Decryption:    3077.969 ms
    [7/7] SHA-256 integrity verification...
          ✅ PASS (938.368 ms)

    Summary: Total=13959.767 ms | RAM=5013.16 MB | Throughput=71.634 MB/s | SHA-256=PASS

======================================================================
  BENCHMARK COMPLETE
======================================================================

  Total iterations: 70
  Successful: 70
  Failed: 0

  Computing statistics...

======================================================================
  SUMMARY TABLE
======================================================================

  File                   Enc (ms)     Dec (ms)   Total (ms)   RAM (MB)       MB/s  SHA-256
  ------------------------------------------------------------------------
  1 MB                      3.008        1.785       14.654      43.32     71.283    10/10
  5 MB                     11.085        5.289       42.294      66.97    118.647    10/10
  10 MB                    18.699        9.543       76.720      96.51    130.541    10/10
  50 MB                    94.144       48.984      397.079     287.83    127.641    10/10
  100 MB                  231.772      111.093      864.936     537.76    119.810    10/10
  500 MB                 1898.692     1515.870     5227.290    2525.30     98.424    10/10
  1000 MB                5009.651     3649.486    11601.994    4900.76     87.116    10/10

  Exporting results...

  CSV exported: /home/mole/Documents/Penelitian/CE/pangolin/benchmark/results.csv
  JSON exported: /home/mole/Documents/Penelitian/CE/pangolin/benchmark/results.json

```

---

## 6. Observations

No anomalies, failures, or unexpected behavior were observed during the experiment.
