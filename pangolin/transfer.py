"""
Simulated file transfer via folder-to-folder copying.

Mimics network file transfer by copying files between
directories using shutil. Logs transfer timing and file sizes.
"""

import shutil
import time
from pathlib import Path
from typing import List

from pangolin.logger import get_logger

logger = get_logger()


def send(source_path: str | Path, destination_dir: str | Path) -> Path:
    """
    Simulate sending a file by copying it to the destination directory.

    Args:
        source_path: Path to the file to "send".
        destination_dir: Destination directory to copy to.

    Returns:
        Path to the copied file in the destination directory.
    """
    source_path = Path(source_path)
    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    dest_path = destination_dir / source_path.name
    file_size = source_path.stat().st_size

    logger.info(
        f"Simulating transfer: {source_path.name} "
        f"({file_size:,} bytes) → {destination_dir}"
    )
    start = time.perf_counter()

    shutil.copy2(source_path, dest_path)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Transfer completed in {elapsed_ms:.2f} ms")

    return dest_path


def send_multiple(
    source_paths: List[str | Path], destination_dir: str | Path
) -> List[Path]:
    """
    Simulate sending multiple files to a destination directory.

    Args:
        source_paths: List of file paths to "send".
        destination_dir: Destination directory to copy to.

    Returns:
        List of paths to the copied files.
    """
    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Simulating batch transfer of {len(source_paths)} file(s)...")
    start = time.perf_counter()

    dest_paths = []
    total_size = 0

    for source_path in source_paths:
        source_path = Path(source_path)
        dest_path = destination_dir / source_path.name
        total_size += source_path.stat().st_size
        shutil.copy2(source_path, dest_path)
        dest_paths.append(dest_path)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"Batch transfer completed in {elapsed_ms:.2f} ms "
        f"({len(dest_paths)} file(s), {total_size:,} bytes total)"
    )

    return dest_paths
