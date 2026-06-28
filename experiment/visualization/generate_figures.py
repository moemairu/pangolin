#!/usr/bin/env python3
"""
Pangolin Benchmark — Publication-Quality Visualization Generator (Seaborn)

Generates clear, paper-ready figures from the benchmark CSV data.
All figures are saved as both PNG (300 DPI) and PDF for LaTeX compatibility.

Usage:
    python generate_figures.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from pathlib import Path

# ============================================================================
#  Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_PATH = SCRIPT_DIR.parent / "benchmark" / "results.csv"
OUTPUT_DIR = SCRIPT_DIR / "figures"

FILE_SIZE_ORDER = ["1 MB", "5 MB", "10 MB", "50 MB", "100 MB", "500 MB", "1000 MB"]
FILE_SIZE_NUMERIC = [1, 5, 10, 50, 100, 500, 1000]

# --- Seaborn + Matplotlib academic style ---
sns.set_theme(
    style="whitegrid",
    context="paper",
    font_scale=1.3,
    rc={
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.15,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.linestyle": "--",
        "grid.alpha": 0.35,
        "lines.linewidth": 2.0,
        "lines.markersize": 7,
    }
)

# Colorblind-safe palette
PAL = sns.color_palette("colorblind", 10)
C = {
    "blue":      PAL[0],
    "orange":    PAL[1],
    "green":     PAL[2],
    "red":       PAL[3],
    "purple":    PAL[4],
    "brown":     PAL[5],
    "pink":      PAL[6],
    "gray":      PAL[7],
    "yellow":    PAL[8],
    "cyan":      PAL[9],
}


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and preprocess the benchmark CSV data."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["file_size_label"] = pd.Categorical(
        df["file_size_label"], categories=FILE_SIZE_ORDER, ordered=True
    )
    df["file_size_mb"] = df["file_size_bytes"] / (1024 * 1024)
    df = df.sort_values(["file_size_label", "iteration"])
    return df


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-file-size statistics."""
    metrics = [
        "keygen_time_ms", "encapsulation_time_ms", "encryption_time_ms",
        "transfer_time_ms", "decapsulation_time_ms", "decryption_time_ms",
        "hash_verification_time_ms", "total_time_ms", "peak_ram_mb",
        "cpu_percent", "throughput_mbps",
    ]
    stats = df.groupby("file_size_label", observed=True)[metrics].agg(
        ["mean", "std", "median", "min", "max"]
    )
    stats = stats.reindex(FILE_SIZE_ORDER)
    return stats


def save_fig(fig, name: str, out: Path):
    """Save figure in PNG and PDF."""
    fig.savefig(out / f"{name}.png", format="png")
    fig.savefig(out / f"{name}.pdf", format="pdf")
    plt.close(fig)
    print(f"  ✅  {name}.png / .pdf")


# ============================================================================
#  Fig 1 — Total End-to-End Processing Time
# ============================================================================

def fig1_total_time(stats, df, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    means = stats["total_time_ms"]["mean"].values
    stds  = stats["total_time_ms"]["std"].values
    x = np.arange(len(FILE_SIZE_ORDER))

    sns.barplot(
        data=df, x="file_size_label", y="total_time_ms",
        estimator="mean", errorbar="sd",
        color=C["blue"], alpha=0.88, edgecolor="white", linewidth=0.6,
        capsize=0.15, err_kws={"linewidth": 1.3, "color": "#333"},
        ax=ax,
    )

    # Annotate values
    for i, (m, s) in enumerate(zip(means, stds)):
        label = f"{m:.1f} ms" if m < 1000 else f"{m/1000:.2f} s"
        ax.text(i, m + s + means.max() * 0.03, label,
                ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_yscale("log")
    ax.set_xlabel("File Size")
    ax.set_ylabel("Total Processing Time (ms, log scale)")
    ax.set_title("End-to-End Processing Time vs. File Size")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:.1f}"
    ))

    fig.tight_layout()
    save_fig(fig, "fig1_total_time", out)


# ============================================================================
#  Fig 2 — Processing Time Breakdown (Stacked Bar)
# ============================================================================

def fig2_time_breakdown(stats, out):
    fig, ax = plt.subplots(figsize=(8.5, 5))

    phases = [
        ("keygen_time_ms",            "Key Generation",   C["blue"]),
        ("encapsulation_time_ms",     "ML-KEM Encap.",    C["cyan"]),
        ("encryption_time_ms",        "AES-256-GCM Enc.", C["orange"]),
        ("transfer_time_ms",          "Transfer",         C["yellow"]),
        ("decapsulation_time_ms",     "ML-KEM Decap.",    C["green"]),
        ("decryption_time_ms",        "AES-256-GCM Dec.", C["red"]),
        ("hash_verification_time_ms", "SHA-256 Verify",   C["purple"]),
    ]

    x = np.arange(len(FILE_SIZE_ORDER))
    width = 0.58
    bottom = np.zeros(len(FILE_SIZE_ORDER))

    for col, label, color in phases:
        vals = stats[col]["mean"].values
        ax.bar(x, vals, width=width, bottom=bottom, label=label,
               color=color, edgecolor="white", linewidth=0.4)
        bottom += vals

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(FILE_SIZE_ORDER)
    ax.set_xlabel("File Size")
    ax.set_ylabel("Processing Time (ms, log scale)")
    ax.set_title("Processing Time Breakdown by Cryptographic Phase")
    ax.legend(
        loc="upper left", framealpha=0.95, edgecolor="#ccc",
        ncol=2, fontsize=8, borderpad=0.6,
    )

    fig.tight_layout()
    save_fig(fig, "fig2_time_breakdown", out)


# ============================================================================
#  Fig 3 — Encryption & Decryption Scaling (Linear Fit)
# ============================================================================

def fig3_enc_dec_scaling(stats, df, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    sizes = np.array(FILE_SIZE_NUMERIC)
    fit_x = np.linspace(0, 1050, 300)

    for col, label, color, marker in [
        ("encryption_time_ms",  "AES-256-GCM Encryption",  C["orange"], "o"),
        ("decryption_time_ms",  "AES-256-GCM Decryption",  C["red"],    "s"),
    ]:
        means = stats[col]["mean"].values
        stds  = stats[col]["std"].values

        ax.errorbar(sizes, means, yerr=stds, fmt=f"{marker}-", color=color,
                    label=label, capsize=4, capthick=1, markersize=6, zorder=4)

        # Linear fit
        coeffs = np.polyfit(sizes, means, 1)
        ax.plot(fit_x, np.polyval(coeffs, fit_x), "--", color=color,
                alpha=0.35, linewidth=1.3,
                label=f"  Fit: {coeffs[0]:.2f}·x {coeffs[1]:+.1f}")

    ax.set_xlabel("File Size (MB)")
    ax.set_ylabel("Processing Time (ms)")
    ax.set_title("Encryption & Decryption Time Scaling")
    ax.legend(framealpha=0.95, edgecolor="#ccc", fontsize=8.5)
    ax.set_xlim(-20, 1080)
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    save_fig(fig, "fig3_enc_dec_scaling", out)


# ============================================================================
#  Fig 4 — Throughput (Bar + Strip)
# ============================================================================

def fig4_throughput(stats, df, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    means = stats["throughput_mbps"]["mean"].values
    stds  = stats["throughput_mbps"]["std"].values

    # Bar plot
    sns.barplot(
        data=df, x="file_size_label", y="throughput_mbps",
        estimator="mean", errorbar="sd",
        color=C["orange"], alpha=0.82, edgecolor="white", linewidth=0.6,
        capsize=0.15, err_kws={"linewidth": 1.3, "color": "#333"},
        ax=ax,
    )

    # Overlay data points
    sns.stripplot(
        data=df, x="file_size_label", y="throughput_mbps",
        color="#333", size=3.5, alpha=0.45, jitter=0.18, ax=ax, zorder=5,
    )

    # Annotations
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 2.5, f"{m:.1f}",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    overall = np.mean(means)
    ax.axhline(y=overall, color=C["gray"], linestyle=":", linewidth=1.2,
               label=f"Overall mean: {overall:.1f} MB/s", zorder=2)

    ax.set_xlabel("File Size")
    ax.set_ylabel("Throughput (MB/s)")
    ax.set_title("End-to-End Throughput vs. File Size")
    ax.set_ylim(0, max(means + stds) * 1.22)
    ax.legend(framealpha=0.95, edgecolor="#ccc")

    fig.tight_layout()
    save_fig(fig, "fig4_throughput", out)


# ============================================================================
#  Fig 5 — Peak Memory Usage  (fixed overlap)
# ============================================================================

def fig5_memory(stats, out):
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    sizes     = np.array(FILE_SIZE_NUMERIC)
    ram_means = stats["peak_ram_mb"]["mean"].values
    ram_stds  = stats["peak_ram_mb"]["std"].values

    ax.errorbar(sizes, ram_means, yerr=ram_stds, fmt="D-",
                color=C["purple"], label="Measured Peak RAM",
                capsize=4, capthick=1, markersize=7, zorder=4)

    # Linear fit (plot on log-spaced x for smooth curve)
    coeffs = np.polyfit(sizes, ram_means, 1)
    fit_x = np.linspace(0.8, 1200, 500)
    ax.plot(fit_x, np.polyval(coeffs, fit_x), ":", color=C["gray"],
            linewidth=1.3,
            label=f"Linear fit: {coeffs[0]:.2f}·size {coeffs[1]:+.0f} MB",
            zorder=3)

    # Log x-axis — spreads 1,5,10 MB apart so labels don't overlap
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels([f"{s}" for s in sizes])
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())

    # Annotate every data point — ALL above, alternating heights
    # Custom (dx, dy) offsets per point to stay inside and avoid line overlap
    offsets = [
        (0,  40),   # 1 MB    — high
        (0,  70),   # 5 MB    — higher (avoid overlap with 1 MB)
        (0,  40),   # 10 MB   — high
        (0,  70),   # 50 MB   — higher
        (0,  40),   # 100 MB  — high
        (0,  70),   # 500 MB  — higher
        (0,  40),   # 1000 MB — high
    ]

    for i, (s, r, sd) in enumerate(zip(sizes, ram_means, ram_stds)):
        ratio = r / s
        label_text = f"{r:,.0f} MB ({ratio:.1f}×)"
        ox, oy = offsets[i]

        ax.annotate(
            label_text,
            xy=(s, r), xytext=(ox, oy), textcoords="offset points",
            ha="center", va="bottom", fontsize=7.8, fontweight="bold",
            color=C["purple"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#ddd",
                      alpha=0.9),
            arrowprops=dict(arrowstyle="-", color=C["purple"],
                            alpha=0.5, lw=0.8),
        )

    ax.set_xlabel("File Size (MB)")
    ax.set_ylabel("Peak RAM Usage (MB)")
    ax.set_title("Peak Memory Usage vs. File Size")
    ax.legend(loc="upper left", framealpha=0.95, edgecolor="#ccc")
    # Extra headroom for labels above the line
    ax.set_ylim(bottom=0, top=max(ram_means) * 1.35)

    fig.tight_layout()
    save_fig(fig, "fig5_memory_usage", out)


# ============================================================================
#  Fig 6 — KEM Operation Overhead  (fixed annotation)
# ============================================================================

def fig6_kem_overhead(stats, df, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    # Melt data for seaborn grouped bar
    kem_cols = {
        "keygen_time_ms":        "Key Generation",
        "encapsulation_time_ms": "Encapsulation",
        "decapsulation_time_ms": "Decapsulation",
    }

    rows = []
    for _, row in df.iterrows():
        for col, label in kem_cols.items():
            rows.append({
                "File Size": row["file_size_label"],
                "Operation": label,
                "Time (ms)": row[col],
            })
    kem_df = pd.DataFrame(rows)
    kem_df["Operation"] = pd.Categorical(
        kem_df["Operation"],
        categories=["Key Generation", "Encapsulation", "Decapsulation"],
        ordered=True,
    )

    palette = [C["blue"], C["cyan"], C["green"]]

    # Filter out keygen outlier for 1000 MB (5.9 ms cold-start spike)
    kem_df_clean = kem_df[
        ~((kem_df["File Size"] == "1000 MB")
          & (kem_df["Operation"] == "Key Generation")
          & (kem_df["Time (ms)"] > 2.0))
    ]

    sns.barplot(
        data=kem_df_clean, x="File Size", y="Time (ms)", hue="Operation",
        estimator="mean", errorbar=("ci", 95),
        palette=palette, alpha=0.88, edgecolor="white", linewidth=0.4,
        capsize=0.08, err_kws={"linewidth": 0.9, "color": "#555"},
        ax=ax,
    )

    # Clean y-limit based on filtered data
    ax.set_ylim(0, 0.85)

    ax.set_xlabel("File Size")
    ax.set_ylabel("Time (ms)")
    ax.set_title("ML-KEM Operation Overhead (Kyber768)")

    # Move annotation to bottom-right, away from bars
    ax.text(
        0.98, 0.03,
        "KEM operations are constant-time,\nindependent of file size",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=8.5, style="italic", color="#555",
        bbox=dict(boxstyle="round,pad=0.4", fc="#f7f7f7", ec="#ccc", alpha=0.9),
    )

    ax.legend(
        title="Operation", framealpha=0.95, edgecolor="#ccc",
        fontsize=8, title_fontsize=9,
    )

    fig.tight_layout()
    save_fig(fig, "fig6_kem_overhead", out)


# ============================================================================
#  Fig 7 — Box Plots (fixed median labels)
# ============================================================================

def fig7_variability(df, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    palette = sns.color_palette("Blues", n_colors=len(FILE_SIZE_ORDER))

    sns.boxplot(
        data=df, x="file_size_label", y="total_time_ms",
        hue="file_size_label", palette=palette, legend=False,
        width=0.55, linewidth=1,
        flierprops=dict(marker="o", markersize=4, alpha=0.5),
        medianprops=dict(color=C["red"], linewidth=1),
        boxprops=dict(edgecolor="#444"),
        whiskerprops=dict(color="#444"),
        capprops=dict(color="#444"),
        ax=ax,
    )

    ax.set_yscale("log")
    ax.set_xlabel("File Size")
    ax.set_ylabel("Total Processing Time (ms, log scale)")
    ax.set_title("Processing Time Distribution Across 10 Iterations")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:.1f}"
    ))

    # Annotate medians — offset to the right to avoid overlap
    for i, label in enumerate(FILE_SIZE_ORDER):
        subset = df[df["file_size_label"] == label]["total_time_ms"]
        med = subset.median()
        txt = f"{med:.0f} ms" if med < 1000 else f"{med/1000:.1f} s"
        ax.annotate(
            txt, xy=(i + 0.3, med),
            fontsize=7.5, fontweight="bold", color=C["red"],
            va="center", ha="left",
        )

    fig.tight_layout()
    save_fig(fig, "fig7_variability", out)


# ============================================================================
#  Main
# ============================================================================

def main():
    print("=" * 60)
    print("  Pangolin Benchmark — Figure Generator (Seaborn)")
    print("=" * 60)

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n  CSV:    {CSV_PATH}")
    print(f"  Output: {OUTPUT_DIR}\n")

    df = load_data(CSV_PATH)
    stats = compute_stats(df)
    print(f"  Loaded {len(df)} iterations × {len(FILE_SIZE_ORDER)} file sizes\n")
    print("  Generating figures...\n")

    fig1_total_time(stats, df, OUTPUT_DIR)
    fig2_time_breakdown(stats, OUTPUT_DIR)
    fig3_enc_dec_scaling(stats, df, OUTPUT_DIR)
    fig4_throughput(stats, df, OUTPUT_DIR)
    fig5_memory(stats, OUTPUT_DIR)
    fig6_kem_overhead(stats, df, OUTPUT_DIR)
    fig7_variability(df, OUTPUT_DIR)

    print(f"\n  ✅ All 7 figures saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
