"""
Performance benchmarking for cryptographic operations.

Measures timing, CPU usage, and memory consumption for
each step of the Pangolin workflow.
"""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

from pangolin.logger import get_logger

logger = get_logger()


@dataclass
class BenchmarkResult:
    """Result of a single benchmarked operation."""

    operation: str
    duration_ms: float
    cpu_percent: float
    ram_mb: float
    file_size_bytes: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


def _get_process_metrics() -> tuple:
    """
    Capture current process CPU and memory metrics.

    Returns:
        Tuple of (cpu_percent, ram_mb).
    """
    process = psutil.Process(os.getpid())
    cpu = process.cpu_percent(interval=None)
    ram = process.memory_info().rss / (1024 * 1024)  # bytes → MB
    return cpu, ram


def measure(
    operation_name: str,
    func: Callable,
    *args: Any,
    file_size: int = 0,
    **kwargs: Any,
) -> tuple:
    """
    Measure the performance of a function call.

    Wraps a function with timing and resource measurement.

    Args:
        operation_name: Human-readable name for the operation.
        func: The function to benchmark.
        *args: Positional arguments to pass to the function.
        file_size: Size of the file being processed (for reporting).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Tuple of (function_result, BenchmarkResult).
    """
    # Prime CPU measurement
    process = psutil.Process(os.getpid())
    process.cpu_percent(interval=None)

    # Execute and time the function
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Capture post-execution metrics
    cpu_percent = process.cpu_percent(interval=None)
    ram_mb = process.memory_info().rss / (1024 * 1024)

    benchmark = BenchmarkResult(
        operation=operation_name,
        duration_ms=round(elapsed_ms, 3),
        cpu_percent=round(cpu_percent, 1),
        ram_mb=round(ram_mb, 2),
        file_size_bytes=file_size,
    )

    logger.info(
        f"[BENCHMARK] {operation_name}: "
        f"{elapsed_ms:.3f} ms | "
        f"CPU: {cpu_percent:.1f}% | "
        f"RAM: {ram_mb:.2f} MB"
    )

    return result, benchmark


def run_full_benchmark(
    file_sizes: Optional[List[int]] = None,
    iterations: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run a complete benchmark across multiple file sizes.

    For each file size, runs the full encrypt/decrypt workflow
    multiple times and collects average metrics.

    Args:
        file_sizes: List of file sizes in bytes to test.
            Defaults to [1KB, 100KB, 1MB, 10MB].
        iterations: Number of iterations per file size.

    Returns:
        List of benchmark result dictionaries.
    """
    # Import here to avoid circular imports
    from pangolin.aes import derive_aes_key, decrypt_file, encrypt_file
    from pangolin.integrity import compute_hash_bytes
    from pangolin.kyber import decapsulate, encapsulate, generate_keypair

    if file_sizes is None:
        file_sizes = [
            1 * 1024,           # 1 KB
            100 * 1024,         # 100 KB
            1 * 1024 * 1024,    # 1 MB
            10 * 1024 * 1024,   # 10 MB
        ]

    all_results = []

    for size in file_sizes:
        size_label = _format_size(size)
        logger.info(f"\n{'='*60}")
        logger.info(f"Benchmarking file size: {size_label}")
        logger.info(f"{'='*60}")

        # Generate a synthetic test file
        test_data = os.urandom(size)
        tmp_file = Path(f"data/sender/_benchmark_{size}.bin")
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file.write_bytes(test_data)

        iteration_results = []

        for i in range(iterations):
            logger.info(f"\n--- Iteration {i + 1}/{iterations} ---")
            run_results = {}

            # 1. Key generation
            (public_key, secret_key), bench = measure(
                "key_generation", generate_keypair, file_size=size
            )
            run_results["key_generation"] = asdict(bench)

            # 2. Encapsulation
            (ciphertext, shared_secret), bench = measure(
                "encapsulation", encapsulate, public_key, file_size=size
            )
            run_results["encapsulation"] = asdict(bench)

            # 3. Key derivation
            aes_key = derive_aes_key(shared_secret)

            # 4. Encryption
            (nonce, ct, tag), bench = measure(
                "encryption", encrypt_file, tmp_file, aes_key, file_size=size
            )
            run_results["encryption"] = asdict(bench)

            # 5. Hash computation
            _, bench = measure(
                "hash_computation", compute_hash_bytes, test_data, file_size=size
            )
            run_results["hash_computation"] = asdict(bench)

            # 6. Decapsulation
            recovered_secret, bench = measure(
                "decapsulation", decapsulate, secret_key, ciphertext, file_size=size
            )
            run_results["decapsulation"] = asdict(bench)

            # 7. Decryption
            plaintext, bench = measure(
                "decryption", decrypt_file, nonce, ct, tag,
                derive_aes_key(recovered_secret),
                file_size=size,
            )
            run_results["decryption"] = asdict(bench)

            # Verify correctness
            assert plaintext == test_data, "Decryption produced incorrect output!"

            iteration_results.append(run_results)

        # Compute averages
        avg_result = _compute_averages(iteration_results, size, size_label, iterations)
        all_results.append(avg_result)

        # Clean up temp file
        tmp_file.unlink(missing_ok=True)

    return all_results


def _compute_averages(
    iteration_results: List[Dict],
    file_size: int,
    size_label: str,
    iterations: int,
) -> Dict[str, Any]:
    """Compute average metrics across iterations."""
    operations = iteration_results[0].keys()
    averages = {}

    for op in operations:
        durations = [r[op]["duration_ms"] for r in iteration_results]
        cpus = [r[op]["cpu_percent"] for r in iteration_results]
        rams = [r[op]["ram_mb"] for r in iteration_results]

        averages[op] = {
            "avg_duration_ms": round(sum(durations) / len(durations), 3),
            "min_duration_ms": round(min(durations), 3),
            "max_duration_ms": round(max(durations), 3),
            "avg_cpu_percent": round(sum(cpus) / len(cpus), 1),
            "avg_ram_mb": round(sum(rams) / len(rams), 2),
        }

    return {
        "file_size_bytes": file_size,
        "file_size_label": size_label,
        "iterations": iterations,
        "operations": averages,
    }


def save_results(results: List[Dict[str, Any]], filepath: str | Path) -> None:
    """
    Save benchmark results to a JSON file.

    Args:
        results: List of benchmark result dictionaries.
        filepath: Output JSON file path.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark results saved to: {filepath}")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """
    Print a formatted summary table of benchmark results.

    Args:
        results: List of benchmark result dictionaries.
    """
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    header = (
        f"{'File Size':<12} {'Operation':<20} "
        f"{'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10} "
        f"{'CPU %':>8} {'RAM MB':>8}"
    )
    print(header)
    print("-" * 80)

    for result in results:
        size_label = result["file_size_label"]
        for op_name, metrics in result["operations"].items():
            print(
                f"{size_label:<12} {op_name:<20} "
                f"{metrics['avg_duration_ms']:>10.3f} "
                f"{metrics['min_duration_ms']:>10.3f} "
                f"{metrics['max_duration_ms']:>10.3f} "
                f"{metrics['avg_cpu_percent']:>8.1f} "
                f"{metrics['avg_ram_mb']:>8.2f}"
            )
        print()

    print("=" * 80)


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.0f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    else:
        return f"{size_bytes} B"
