#!/usr/bin/env python3
"""
Pangolin Benchmark Runner — Full End-to-End Simulation.

Runs the complete Pangolin cryptographic workflow as a real simulation:
  Receiver keygen → copy pubkey → Sender encrypt → transfer → Receiver decrypt → verify

Each dataset file is processed 10 times with full cleanup between iterations.
Produces benchmark/results.csv, benchmark/results.json, and EXPERIMENT.md.
"""

import csv
import hashlib
import io
import json
import os
import platform
import shutil
import statistics
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pathlib import Path

import psutil

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
EXPERIMENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXPERIMENT_DIR.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
BENCHMARK_DIR = EXPERIMENT_DIR / "benchmark"

# Pangolin working directories
RECEIVER_DIR = PROJECT_ROOT / "receiver"
SENDER_DIR = PROJECT_ROOT / "sender"

RECEIVER_KEYS_DIR = RECEIVER_DIR / "keys"
SENDER_PUBKEYS_DIR = SENDER_DIR / "public_keys"
SENDER_ENCRYPTED_DIR = SENDER_DIR / "data" / "encrypted"
RECEIVER_RECEIVED_DIR = RECEIVER_DIR / "data" / "received"
RECEIVER_DECRYPTED_DIR = RECEIVER_DIR / "data" / "decrypted"

# Add both receiver and sender to path for core imports
sys.path.insert(0, str(RECEIVER_DIR))
sys.path.insert(0, str(SENDER_DIR))

from core.aes import derive_aes_key, decrypt_file, encrypt_file
from core.integrity import compute_hash, compute_hash_bytes, verify_hash_bytes
from core.kyber import decapsulate, encapsulate, generate_keypair
from core.metadata import create_metadata, save_metadata, load_metadata

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ITERATIONS = 10

DATASET_FILES = [
    "file_1MB.bin",
    "file_5MB.bin",
    "file_10MB.bin",
    "file_50MB.bin",
    "file_100MB.bin",
    "file_500MB.bin",
    "file_1000MB.bin",
]

# CSV column order
CSV_COLUMNS = [
    "file_name",
    "file_size_bytes",
    "file_size_label",
    "iteration",
    "status",
    "keygen_time_ms",
    "encapsulation_time_ms",
    "key_derivation_enc_time_ms",
    "encryption_time_ms",
    "transfer_time_ms",
    "decapsulation_time_ms",
    "key_derivation_dec_time_ms",
    "decryption_time_ms",
    "hash_verification_time_ms",
    "total_time_ms",
    "peak_ram_mb",
    "cpu_percent",
    "throughput_mbps",
    "sha256_verification",
    "error_message",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.0f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} B"


def ensure_dirs():
    """Create all required working directories."""
    for d in [
        RECEIVER_KEYS_DIR,
        SENDER_PUBKEYS_DIR,
        SENDER_ENCRYPTED_DIR,
        RECEIVER_RECEIVED_DIR,
        RECEIVER_DECRYPTED_DIR,
        BENCHMARK_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def cleanup_artifacts():
    """Delete all generated artifacts to ensure a clean state."""
    dirs_to_clean = [
        RECEIVER_KEYS_DIR,
        SENDER_PUBKEYS_DIR,
        SENDER_ENCRYPTED_DIR,
        RECEIVER_RECEIVED_DIR,
        RECEIVER_DECRYPTED_DIR,
    ]
    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
    # Recreate empty dirs
    ensure_dirs()


def get_peak_ram_mb() -> float:
    """Get current process RSS in MB."""
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / (1024 * 1024), 2)


def get_cpu_percent() -> float:
    """Get current process CPU percent."""
    process = psutil.Process(os.getpid())
    return process.cpu_percent(interval=None)


# ---------------------------------------------------------------------------
# Single iteration of the full Pangolin simulation
# ---------------------------------------------------------------------------
def run_single_iteration(
    dataset_file: Path, file_name: str, file_size: int, iteration: int
) -> dict:
    """
    Execute one complete Pangolin workflow cycle.

    Returns a dictionary with all metrics for this iteration.
    """
    size_label = format_size(file_size)
    result = {
        "file_name": file_name,
        "file_size_bytes": file_size,
        "file_size_label": size_label,
        "iteration": iteration,
        "status": "OK",
        "error_message": "",
    }

    # Prime CPU measurement
    process = psutil.Process(os.getpid())
    process.cpu_percent(interval=None)

    total_start = time.perf_counter()
    peak_ram = get_peak_ram_mb()

    def track_ram():
        nonlocal peak_ram
        current = get_peak_ram_mb()
        if current > peak_ram:
            peak_ram = current

    # ── Step 1: Receiver generates Kyber768 keypair ──────────────────
    print(f"    [1/7] Generating Kyber768 keypair...")
    t0 = time.perf_counter()

    public_key, secret_key = generate_keypair()

    # Write keys to disk
    pub_path = RECEIVER_KEYS_DIR / "public.bin"
    sec_path = RECEIVER_KEYS_DIR / "secret.bin"
    pub_path.write_bytes(public_key)
    sec_path.write_bytes(secret_key)

    result["keygen_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    track_ram()
    print(f"          Done ({result['keygen_time_ms']:.3f} ms)")

    # ── Step 2: Copy public key to sender ────────────────────────────
    print(f"    [2/7] Copying public key to sender...")
    sender_pubkey = SENDER_PUBKEYS_DIR / "public.bin"
    shutil.copy2(pub_path, sender_pubkey)
    print(f"          {pub_path} → {sender_pubkey}")

    # ── Step 3: Sender encrypts the file ─────────────────────────────
    print(f"    [3/7] ML-KEM encapsulation...")
    t0 = time.perf_counter()

    sender_public_key = sender_pubkey.read_bytes()
    kem_ciphertext, shared_secret = encapsulate(sender_public_key)

    result["encapsulation_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    track_ram()
    print(f"          Done ({result['encapsulation_time_ms']:.3f} ms)")

    print(f"    [4/7] AES-256-GCM encryption...")
    t0 = time.perf_counter()

    aes_key = derive_aes_key(shared_secret)
    key_deriv_enc_time = time.perf_counter() - t0

    t_enc = time.perf_counter()
    original_hash = compute_hash(dataset_file)
    nonce, ciphertext, tag = encrypt_file(dataset_file, aes_key)

    # Write encrypted artifacts to disk
    enc_path = SENDER_ENCRYPTED_DIR / f"{file_name}.enc"
    kem_path = SENDER_ENCRYPTED_DIR / f"{file_name}.kem"
    meta_path = SENDER_ENCRYPTED_DIR / f"{file_name}.meta.json"

    enc_path.write_bytes(nonce + tag + ciphertext)
    kem_path.write_bytes(kem_ciphertext)

    metadata = create_metadata(
        filename=file_name,
        filesize=file_size,
        original_hash=original_hash,
        extra={
            "nonce_size": len(nonce),
            "tag_size": len(tag),
            "ciphertext_size": len(ciphertext),
            "kem_ciphertext_size": len(kem_ciphertext),
        },
    )
    save_metadata(metadata, meta_path)

    result["key_derivation_enc_time_ms"] = round(key_deriv_enc_time * 1000, 3)
    result["encryption_time_ms"] = round((time.perf_counter() - t_enc) * 1000, 3)
    track_ram()
    print(f"          Done ({result['encryption_time_ms']:.3f} ms)")

    # ── Step 4: Transfer (copy files to receiver) ────────────────────
    print(f"    [5/7] Transfer simulation...")
    t0 = time.perf_counter()

    recv_enc = RECEIVER_RECEIVED_DIR / enc_path.name
    recv_kem = RECEIVER_RECEIVED_DIR / kem_path.name
    recv_meta = RECEIVER_RECEIVED_DIR / meta_path.name

    shutil.copy2(enc_path, recv_enc)
    shutil.copy2(kem_path, recv_kem)
    shutil.copy2(meta_path, recv_meta)

    result["transfer_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    track_ram()
    print(f"          Done ({result['transfer_time_ms']:.3f} ms)")

    # ── Step 5: Receiver decapsulates + decrypts ─────────────────────
    print(f"    [6/7] ML-KEM decapsulation + AES-256-GCM decryption...")

    # Read files from received directory (as receiver would)
    recv_secret_key = sec_path.read_bytes()
    recv_kem_ciphertext = recv_kem.read_bytes()

    t0 = time.perf_counter()
    recovered_secret = decapsulate(recv_secret_key, recv_kem_ciphertext)
    result["decapsulation_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    track_ram()

    t0 = time.perf_counter()
    recv_aes_key = derive_aes_key(recovered_secret)
    result["key_derivation_dec_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)

    # Read encrypted payload
    received_data = recv_enc.read_bytes()
    recv_nonce = received_data[:12]
    recv_tag = received_data[12:28]
    recv_ciphertext = received_data[28:]

    t0 = time.perf_counter()
    plaintext = decrypt_file(recv_nonce, recv_ciphertext, recv_tag, recv_aes_key)

    # Write decrypted file
    decrypted_path = RECEIVER_DECRYPTED_DIR / file_name
    decrypted_path.write_bytes(plaintext)

    result["decryption_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    track_ram()
    print(f"          Decapsulation: {result['decapsulation_time_ms']:.3f} ms")
    print(f"          Decryption:    {result['decryption_time_ms']:.3f} ms")

    # ── Step 6: SHA-256 integrity verification ───────────────────────
    print(f"    [7/7] SHA-256 integrity verification...")
    t0 = time.perf_counter()

    recv_metadata = load_metadata(recv_meta)
    decrypted_data = decrypted_path.read_bytes()
    hash_ok = verify_hash_bytes(decrypted_data, recv_metadata["original_hash"])

    result["hash_verification_time_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    result["sha256_verification"] = "PASS" if hash_ok else "FAIL"
    track_ram()

    if hash_ok:
        print(f"          ✅ PASS ({result['hash_verification_time_ms']:.3f} ms)")
    else:
        print(f"          ❌ FAIL ({result['hash_verification_time_ms']:.3f} ms)")

    # ── Total metrics ────────────────────────────────────────────────
    total_ms = (time.perf_counter() - total_start) * 1000
    result["total_time_ms"] = round(total_ms, 3)
    result["peak_ram_mb"] = peak_ram
    result["cpu_percent"] = round(process.cpu_percent(interval=None), 1)

    # Throughput: file_size_MB / total_time_seconds
    total_seconds = total_ms / 1000
    file_size_mb = file_size / (1024 * 1024)
    result["throughput_mbps"] = round(file_size_mb / total_seconds, 3) if total_seconds > 0 else 0

    return result


# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------
def compute_statistics(all_results: list) -> dict:
    """
    Compute mean, median, min, max, stddev for each metric grouped by file size.
    """
    from collections import defaultdict

    grouped = defaultdict(list)
    for r in all_results:
        grouped[r["file_name"]].append(r)

    stats = {}
    numeric_metrics = [
        "keygen_time_ms",
        "encapsulation_time_ms",
        "key_derivation_enc_time_ms",
        "encryption_time_ms",
        "transfer_time_ms",
        "decapsulation_time_ms",
        "key_derivation_dec_time_ms",
        "decryption_time_ms",
        "hash_verification_time_ms",
        "total_time_ms",
        "peak_ram_mb",
        "cpu_percent",
        "throughput_mbps",
    ]

    for file_name, results in grouped.items():
        # Only use successful iterations for stats
        ok_results = [r for r in results if r["status"] == "OK"]
        file_stats = {
            "file_name": file_name,
            "file_size_bytes": results[0]["file_size_bytes"],
            "file_size_label": results[0]["file_size_label"],
            "total_iterations": len(results),
            "successful_iterations": len(ok_results),
            "failed_iterations": len(results) - len(ok_results),
            "sha256_pass_count": sum(1 for r in ok_results if r.get("sha256_verification") == "PASS"),
            "sha256_fail_count": sum(1 for r in ok_results if r.get("sha256_verification") == "FAIL"),
            "metrics": {},
        }

        if ok_results:
            for metric in numeric_metrics:
                values = [r[metric] for r in ok_results if metric in r and r[metric] is not None]
                if values:
                    file_stats["metrics"][metric] = {
                        "mean": round(statistics.mean(values), 3),
                        "median": round(statistics.median(values), 3),
                        "min": round(min(values), 3),
                        "max": round(max(values), 3),
                        "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
                    }

        stats[file_name] = file_stats

    return stats


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------
def export_csv(all_results: list, filepath: Path):
    """Export all results as CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"\n  CSV exported: {filepath}")


def export_json(all_results: list, stats: dict, filepath: Path):
    """Export all results and statistics as JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_iterations": len(all_results),
            "pangolin_version": "0.1.0",
        },
        "raw_results": all_results,
        "statistics": stats,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  JSON exported: {filepath}")


# ---------------------------------------------------------------------------
# Environment info
# ---------------------------------------------------------------------------
def collect_environment_info() -> dict:
    """Collect system and environment information."""
    info = {
        "os": platform.platform(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_model": "Unknown",
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "pangolin_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
    }

    # Try to get CPU model on Linux
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.strip().startswith("model name"):
                    info["cpu_model"] = line.split(":")[1].strip()
                    break
    except (FileNotFoundError, PermissionError):
        pass

    # Library versions
    try:
        import cryptography
        info["cryptography_version"] = cryptography.__version__
    except Exception:
        info["cryptography_version"] = "unknown"

    try:
        import oqs
        info["liboqs_python_version"] = getattr(oqs, "__version__", "installed")
    except Exception:
        info["liboqs_python_version"] = "unknown"

    info["psutil_version"] = psutil.__version__

    return info


# ---------------------------------------------------------------------------
# EXPERIMENT.md generation
# ---------------------------------------------------------------------------
def generate_experiment_md(
    env_info: dict,
    dataset_info: list,
    all_results: list,
    stats: dict,
    console_output: str,
    observations: list,
    filepath: Path,
):
    """Generate the comprehensive EXPERIMENT.md report."""
    lines = []

    def w(text=""):
        lines.append(text)

    # ── Section 1: Experimental Environment ──────────────────────────
    w("# Pangolin — Experimental Evaluation Report")
    w()
    w("---")
    w()
    w("## 1. Experimental Environment")
    w()
    w(f"| Parameter | Value |")
    w(f"|---|---|")
    w(f"| **Operating System** | {env_info['os']} |")
    w(f"| **Architecture** | {env_info['architecture']} |")
    w(f"| **CPU** | {env_info['cpu_model']} |")
    w(f"| **CPU Cores (Physical / Logical)** | {env_info['cpu_cores_physical']} / {env_info['cpu_cores_logical']} |")
    w(f"| **RAM Total** | {env_info['ram_total_gb']} GB |")
    w(f"| **RAM Available (at start)** | {env_info['ram_available_gb']} GB |")
    w(f"| **Python Version** | {env_info['python_version']} |")
    w(f"| **Pangolin Version** | {env_info['pangolin_version']} |")
    w(f"| **cryptography** | {env_info['cryptography_version']} |")
    w(f"| **liboqs-python** | {env_info['liboqs_python_version']} |")
    w(f"| **psutil** | {env_info['psutil_version']} |")
    w(f"| **Date & Time (UTC)** | {env_info['timestamp']} |")
    w(f"| **Date & Time (Local)** | {env_info['timestamp_local']} |")
    w()

    # ── Section 2: Dataset ───────────────────────────────────────────
    w("---")
    w()
    w("## 2. Dataset")
    w()
    w("All dataset files were generated using `os.urandom()` (cryptographically secure pseudo-random bytes).")
    w()
    w("| Filename | Size (Bytes) | Size (Human) | SHA-256 |")
    w("|---|---|---|---|")
    for d in dataset_info:
        w(f"| `{d['filename']}` | {d['size_bytes']:,} | {d['size_label']} | `{d['sha256'][:16]}...` |")
    w()

    # ── Section 3: Experimental Procedure ────────────────────────────
    w("---")
    w()
    w("## 3. Experimental Procedure")
    w()
    w("### Methodology")
    w()
    w(f"- **Repetitions per file size:** {ITERATIONS}")
    w(f"- **Total iterations:** {len(DATASET_FILES)} files × {ITERATIONS} iterations = {len(DATASET_FILES) * ITERATIONS}")
    w()
    w("### Execution Workflow (per iteration)")
    w()
    w("Each iteration performs the complete Pangolin workflow as a real end-to-end simulation:")
    w()
    w("1. **Key Generation** — Receiver generates a Kyber768 keypair, writes `public.bin` and `secret.bin` to disk")
    w("2. **Public Key Distribution** — Public key is copied from `receiver/keys/` to `sender/public_keys/`")
    w("3. **ML-KEM Encapsulation** — Sender encapsulates a shared secret using the receiver's public key")
    w("4. **AES-256-GCM Encryption** — Sender encrypts the dataset file, writes `.enc`, `.kem`, `.meta.json` to disk")
    w("5. **Transfer Simulation** — All 3 encrypted artifacts are copied from `sender/data/encrypted/` to `receiver/data/received/`")
    w("6. **ML-KEM Decapsulation** — Receiver recovers the shared secret using their secret key")
    w("7. **AES-256-GCM Decryption** — Receiver decrypts the payload, writes the plaintext file to disk")
    w("8. **SHA-256 Integrity Verification** — Receiver computes the hash of the decrypted file and compares against the original hash")
    w("9. **Cleanup** — All artifacts (keys, encrypted files, received files, decrypted files) are deleted")
    w()
    w("### Measured Metrics")
    w()
    w("| Metric | Unit | Description |")
    w("|---|---|---|")
    w("| Keygen Time | ms | Kyber768 keypair generation + disk write |")
    w("| Encapsulation Time | ms | ML-KEM encapsulation |")
    w("| Encryption Time | ms | Hash computation + AES-256-GCM encryption + disk I/O |")
    w("| Transfer Time | ms | File copy simulation (3 files) |")
    w("| Decapsulation Time | ms | ML-KEM decapsulation |")
    w("| Decryption Time | ms | AES-256-GCM decryption + disk write |")
    w("| Hash Verification Time | ms | SHA-256 verification |")
    w("| Total Time | ms | End-to-end (keygen through verification) |")
    w("| Peak RAM | MB | Peak resident set size during iteration |")
    w("| CPU Usage | % | Process CPU utilization |")
    w("| Throughput | MB/s | file_size / total_time |")
    w("| SHA-256 Verification | PASS/FAIL | Integrity check result |")
    w()

    # ── Section 4: Results ───────────────────────────────────────────
    w("---")
    w()
    w("## 4. Results")
    w()

    for file_name in DATASET_FILES:
        if file_name not in stats:
            continue

        s = stats[file_name]
        w(f"### {s['file_size_label']} (`{file_name}`)")
        w()
        w(f"- **Total iterations:** {s['total_iterations']}")
        w(f"- **Successful:** {s['successful_iterations']}")
        w(f"- **Failed:** {s['failed_iterations']}")
        w(f"- **SHA-256 PASS:** {s['sha256_pass_count']} | **FAIL:** {s['sha256_fail_count']}")
        w()

        if s["metrics"]:
            w("| Metric | Mean | Median | Min | Max | Std Dev |")
            w("|---|---|---|---|---|---|")

            metric_labels = {
                "keygen_time_ms": "Keygen (ms)",
                "encapsulation_time_ms": "Encapsulation (ms)",
                "encryption_time_ms": "Encryption (ms)",
                "transfer_time_ms": "Transfer (ms)",
                "decapsulation_time_ms": "Decapsulation (ms)",
                "decryption_time_ms": "Decryption (ms)",
                "hash_verification_time_ms": "Hash Verify (ms)",
                "total_time_ms": "**Total (ms)**",
                "peak_ram_mb": "Peak RAM (MB)",
                "cpu_percent": "CPU (%)",
                "throughput_mbps": "Throughput (MB/s)",
            }

            for metric_key, label in metric_labels.items():
                if metric_key in s["metrics"]:
                    m = s["metrics"][metric_key]
                    w(f"| {label} | {m['mean']:.3f} | {m['median']:.3f} | {m['min']:.3f} | {m['max']:.3f} | {m['stdev']:.3f} |")

            w()
        else:
            w("*No successful iterations — no statistics available.*")
            w()

    # ── Section 5: Raw Console Output ────────────────────────────────
    w("---")
    w()
    w("## 5. Raw Console Output")
    w()
    w("```")
    w(console_output)
    w("```")
    w()

    # ── Section 6: Observations ──────────────────────────────────────
    w("---")
    w()
    w("## 6. Observations")
    w()
    if observations:
        for obs in observations:
            w(f"- {obs}")
    else:
        w("No anomalies, failures, or unexpected behavior were observed during the experiment.")
    w()

    # Write file
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  EXPERIMENT.md generated: {filepath}")


# ---------------------------------------------------------------------------
# Main benchmark runner
# ---------------------------------------------------------------------------
def main():
    # Capture all console output
    console_buffer = io.StringIO()

    class TeeWriter:
        """Write to both console and buffer simultaneously."""
        def __init__(self, *writers):
            self.writers = writers
        def write(self, text):
            for w in self.writers:
                w.write(text)
                w.flush()
        def flush(self):
            for w in self.writers:
                w.flush()

    tee_stdout = TeeWriter(sys.stdout, console_buffer)
    tee_stderr = TeeWriter(sys.stderr, console_buffer)

    # Save originals
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    sys.stdout = tee_stdout
    sys.stderr = tee_stderr

    try:
        _run_benchmark()
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr

    return console_buffer.getvalue()


def _run_benchmark():
    """Core benchmark logic."""
    print("\n" + "=" * 70)
    print("  PANGOLIN BENCHMARK — Full End-to-End Simulation")
    print("=" * 70)
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Iterations per file: {ITERATIONS}")
    print(f"  Dataset files: {len(DATASET_FILES)}")
    print(f"  Total planned iterations: {len(DATASET_FILES) * ITERATIONS}")
    print()

    # Collect environment info
    env_info = collect_environment_info()
    print(f"  OS: {env_info['os']}")
    print(f"  CPU: {env_info['cpu_model']}")
    print(f"  RAM: {env_info['ram_total_gb']} GB total, {env_info['ram_available_gb']} GB available")
    print(f"  Python: {env_info['python_version']}")
    print()

    # Verify dataset files exist
    dataset_info = []
    print("  Verifying dataset files...")
    all_present = True
    for fname in DATASET_FILES:
        fpath = DATASET_DIR / fname
        if fpath.exists():
            fsize = fpath.stat().st_size
            # Compute SHA-256
            sha256 = hashlib.sha256()
            with open(fpath, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            fhash = sha256.hexdigest()
            dataset_info.append({
                "filename": fname,
                "size_bytes": fsize,
                "size_label": format_size(fsize),
                "sha256": fhash,
            })
            print(f"    ✅ {fname} ({format_size(fsize)}) — {fhash[:16]}...")
        else:
            print(f"    ❌ {fname} — NOT FOUND")
            all_present = False

    if not all_present:
        print("\n  ERROR: Some dataset files are missing. Run generate_dataset.py first.")
        return

    print()

    # Ensure working directories exist
    ensure_dirs()

    # Run benchmark
    all_results = []
    observations = []

    for file_idx, file_name in enumerate(DATASET_FILES):
        dataset_file = DATASET_DIR / file_name
        file_size = dataset_file.stat().st_size
        size_label = format_size(file_size)

        print("\n" + "=" * 70)
        print(f"  FILE {file_idx + 1}/{len(DATASET_FILES)}: {file_name} ({size_label})")
        print("=" * 70)

        for iteration in range(1, ITERATIONS + 1):
            print(f"\n  ── Iteration {iteration}/{ITERATIONS} ──")

            # Cleanup before iteration
            cleanup_artifacts()

            try:
                result = run_single_iteration(dataset_file, file_name, file_size, iteration)
                all_results.append(result)

                print(f"\n    Summary: Total={result['total_time_ms']:.3f} ms | "
                      f"RAM={result['peak_ram_mb']:.2f} MB | "
                      f"Throughput={result['throughput_mbps']:.3f} MB/s | "
                      f"SHA-256={result['sha256_verification']}")

                if result["sha256_verification"] == "FAIL":
                    msg = f"SHA-256 verification FAILED for {file_name}, iteration {iteration}"
                    observations.append(msg)
                    print(f"    ⚠️  {msg}")

            except MemoryError as e:
                error_msg = f"MemoryError on {file_name}, iteration {iteration}: {e}"
                print(f"\n    ❌ {error_msg}")
                observations.append(error_msg)
                all_results.append({
                    "file_name": file_name,
                    "file_size_bytes": file_size,
                    "file_size_label": size_label,
                    "iteration": iteration,
                    "status": "ERROR",
                    "error_message": str(e),
                    "sha256_verification": "N/A",
                    **{k: None for k in CSV_COLUMNS if k not in [
                        "file_name", "file_size_bytes", "file_size_label",
                        "iteration", "status", "error_message", "sha256_verification"
                    ]},
                })

            except Exception as e:
                error_msg = f"Error on {file_name}, iteration {iteration}: {type(e).__name__}: {e}"
                print(f"\n    ❌ {error_msg}")
                traceback.print_exc()
                observations.append(error_msg)
                all_results.append({
                    "file_name": file_name,
                    "file_size_bytes": file_size,
                    "file_size_label": size_label,
                    "iteration": iteration,
                    "status": "ERROR",
                    "error_message": str(e),
                    "sha256_verification": "N/A",
                    **{k: None for k in CSV_COLUMNS if k not in [
                        "file_name", "file_size_bytes", "file_size_label",
                        "iteration", "status", "error_message", "sha256_verification"
                    ]},
                })

            finally:
                # Always cleanup after iteration
                cleanup_artifacts()

    # ── Final cleanup ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  BENCHMARK COMPLETE")
    print("=" * 70)

    total_ok = sum(1 for r in all_results if r["status"] == "OK")
    total_err = sum(1 for r in all_results if r["status"] == "ERROR")
    print(f"\n  Total iterations: {len(all_results)}")
    print(f"  Successful: {total_ok}")
    print(f"  Failed: {total_err}")

    # Compute statistics
    print("\n  Computing statistics...")
    stats = compute_statistics(all_results)

    # Print summary table
    print("\n" + "=" * 70)
    print("  SUMMARY TABLE")
    print("=" * 70)
    print(f"\n  {'File':<18} {'Enc (ms)':>12} {'Dec (ms)':>12} {'Total (ms)':>12} {'RAM (MB)':>10} {'MB/s':>10} {'SHA-256':>8}")
    print("  " + "-" * 72)

    for file_name in DATASET_FILES:
        if file_name in stats and stats[file_name]["metrics"]:
            s = stats[file_name]
            m = s["metrics"]
            enc = m.get("encryption_time_ms", {}).get("mean", 0)
            dec = m.get("decryption_time_ms", {}).get("mean", 0)
            total = m.get("total_time_ms", {}).get("mean", 0)
            ram = m.get("peak_ram_mb", {}).get("mean", 0)
            tp = m.get("throughput_mbps", {}).get("mean", 0)
            sha_status = f"{s['sha256_pass_count']}/{s['successful_iterations']}"
            print(f"  {s['file_size_label']:<18} {enc:>12.3f} {dec:>12.3f} {total:>12.3f} {ram:>10.2f} {tp:>10.3f} {sha_status:>8}")

    print()

    # Export results
    print("  Exporting results...")
    csv_path = BENCHMARK_DIR / "results.csv"
    json_path = BENCHMARK_DIR / "results.json"
    export_csv(all_results, csv_path)
    export_json(all_results, stats, json_path)

    # Generate EXPERIMENT.md (console output will be captured by caller)
    # We store the placeholder here; the actual console output is injected by main()
    return env_info, dataset_info, all_results, stats, observations


def run_and_generate_report():
    """Run the benchmark and generate the final EXPERIMENT.md with captured output."""
    # Capture all console output
    console_buffer = io.StringIO()

    class TeeWriter:
        """Write to both real stdout/stderr and capture buffer."""
        def __init__(self, real_stream, buffer):
            self.real_stream = real_stream
            self.buffer = buffer
        def write(self, text):
            self.real_stream.write(text)
            self.buffer.write(text)
            self.real_stream.flush()
        def flush(self):
            self.real_stream.flush()

    real_stdout = sys.stdout
    real_stderr = sys.stderr
    tee_stdout = TeeWriter(real_stdout, console_buffer)
    tee_stderr = TeeWriter(real_stderr, console_buffer)

    sys.stdout = tee_stdout
    sys.stderr = tee_stderr

    try:
        result = _run_benchmark()
    finally:
        sys.stdout = real_stdout
        sys.stderr = real_stderr

    if result is None:
        print("Benchmark did not complete. Cannot generate EXPERIMENT.md.")
        return

    env_info, dataset_info, all_results, stats, observations = result
    console_output = console_buffer.getvalue()

    # Generate EXPERIMENT.md
    print("\n  Generating EXPERIMENT.md...")
    generate_experiment_md(
        env_info=env_info,
        dataset_info=dataset_info,
        all_results=all_results,
        stats=stats,
        console_output=console_output,
        observations=observations,
        filepath=EXPERIMENT_DIR / "EXPERIMENT.md",
    )

    print("\n  ✅ All done!")
    print(f"  Output files:")
    print(f"    - benchmark/results.csv")
    print(f"    - benchmark/results.json")
    print(f"    - EXPERIMENT.md")
    print()


if __name__ == "__main__":
    run_and_generate_report()
