#!/usr/bin/env python3
"""
Script to extract and plot IFCT (Interfragment Charge Transfer) analysis from MultiWfn output.
Reads CT% and LE% data and creates a stacked bar plot with annotations.

Author: Graduate Chemistry Tutorial
Date: October 2025
"""

import os
import sys
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def parse_ifct_data(file_path):
    """
    Parse the IFCT Summary section from MultiWfn output file.

    Parameters
    ----------
    file_path : str or Path
        Path to the MultiWfn analysis file

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: state, CT_percent, LE_percent
    """

    # Read the file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

    # Find the IFCT Summary section
    pattern = r"## IFCT: Summary \(CT% / LE%\)\s*\n\| state \| CT_percent \| LE_percent \|\s*\n\| --- \| --- \| --- \|\s*\n((?:\| \d+ \| [\d.]+ \| [\d.]+ \|\s*\n)+)"

    match = re.search(pattern, content)
    if not match:
        raise ValueError(
            "IFCT Summary section not found in the file. Please check the file format."
        )

    # Extract the data rows
    data_section = match.group(1)

    # Parse each data row
    data_rows = []
    row_pattern = r"\| (\d+) \| ([\d.]+) \| ([\d.]+) \|"

    for line in data_section.strip().split("\n"):
        row_match = re.match(row_pattern, line.strip())
        if row_match:
            state = int(row_match.group(1))
            ct_percent = float(row_match.group(2))
            le_percent = float(row_match.group(3))
            data_rows.append(
                {"state": state, "CT_percent": ct_percent, "LE_percent": le_percent}
            )

    if not data_rows:
        raise ValueError("No data rows found in IFCT Summary section.")

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Validation: CT% + LE% should be close to 100%
    df["total_percent"] = df["CT_percent"] + df["LE_percent"]

    # Check for reasonable totals (allowing some numerical precision issues)
    invalid_totals = df[abs(df["total_percent"] - 100.0) > 5.0]
    if not invalid_totals.empty:
        print(
            f"Warning: Found {len(invalid_totals)} states with CT% + LE% significantly different from 100%"
        )
        print(invalid_totals[["state", "CT_percent", "LE_percent", "total_percent"]])

    return df


def create_ifct_plot(df, num_states=3, output_path=None, figsize=(10, 6), dpi=300):
    """
    Create a stacked bar plot showing CT and LE contributions.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with IFCT data
    num_states : int, default=3
        Number of states to plot
    output_path : str or None
        Path to save the plot. If None, uses default naming
    figsize : tuple, default=(10, 6)
        Figure size in inches
    dpi : int, default=300
        Resolution for saved figure

    Returns
    -------
    tuple
        (fig, ax) matplotlib figure and axes objects
    """

    # Select the requested number of states
    plot_data = df.head(num_states).copy()

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Set up the bar positions
    states = plot_data["state"].astype(str)
    x_pos = np.arange(len(states))
    width = 0.4

    # Create stacked bars
    ct_bars = ax.bar(
        x_pos,
        plot_data["CT_percent"],
        width,
        label="Charge Transfer (CT)",
        # color="#D55E00",
        alpha=0.8,
    )
    le_bars = ax.bar(
        x_pos,
        plot_data["LE_percent"],
        width,
        bottom=plot_data["CT_percent"],
        label="Local Excitation (LE)",
        # color="#009E73",
        alpha=0.8,
    )

    # Customize the plot
    ax.set_xlabel("Excited State", fontsize=14, fontweight="bold")
    ax.set_ylabel("Character % Contribution", fontsize=14, fontweight="bold")
    ax.set_title(
        f"Charge Transfer vs Local Excitation Character\nFirst {num_states} Excited States",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    # Set x-axis
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"S{state}" for state in states], fontsize=12)

    # Set y-axis
    ax.set_ylim(0, 120)
    ax.set_ylabel("Character % Contribution", fontsize=14, fontweight="bold")
    ax.tick_params(axis="y", labelsize=12)

    # Add grid
    # ax.grid(False, alpha=0.3, axis="y")
    # ax.set_axisbelow(True)

    # Add percentage annotations with smart positioning
    for i, (ct_val, le_val) in enumerate(
        zip(plot_data["CT_percent"], plot_data["LE_percent"])
    ):
        # CT annotation - smart positioning
        ct_center = ct_val / 2
        if ct_val < 15:  # Small CT bar - place text outside or adjust
            if ct_val < 8:  # Very small - place above the bar
                ax.annotate(
                    f"{ct_val:.0f}%",
                    xy=(i, ct_val + 2),
                    ha="center",
                    va="bottom",
                    fontsize=14,
                    fontweight="bold",
                    color="black",
                    # bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                )
            else:  # Small but visible - use smaller font inside
                ax.annotate(
                    f"{ct_val:.0f}%",
                    xy=(i, ct_center),
                    ha="center",
                    va="center",
                    fontsize=14,
                    fontweight="bold",
                    color="white",
                )
        else:  # Normal size - center placement
            ax.annotate(
                f"{ct_val:.0f}%",
                xy=(i, ct_center),
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white",
            )

        # LE annotation - smart positioning
        le_center = ct_val + (le_val / 2)
        if le_val < 15:  # Small LE bar - place text outside or adjust
            if le_val < 8:  # Very small - place above the bar
                ax.annotate(
                    f"{le_val:.0f}%",
                    xy=(i, ct_val + le_val + 2),
                    ha="center",
                    va="bottom",
                    fontsize=14,
                    fontweight="bold",
                    color="black",
                    # bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                )
            else:  # Small but visible - use smaller font inside
                ax.annotate(
                    f"{le_val:.0f}%",
                    xy=(i, le_center),
                    ha="center",
                    va="center",
                    fontsize=14,
                    fontweight="bold",
                    color="white",
                )
        else:  # Normal size - center placement
            ax.annotate(
                f"{le_val:.0f}%",
                xy=(i, le_center),
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white",
            )

    # Add 50% reference line for easy comparison
    # ax.axhline(
    #    y=50,
    #    color="grey",
    #    linestyle="--",
    #    linewidth=1,
    #    alpha=0.5,
    # )

    # Add legend
    ax.legend(loc="upper right", fontsize=12, framealpha=0.9)

    # Improve layout
    plt.tight_layout()

    # Save the plot
    if output_path is None:
        # Create default filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"IFCT_analysis_{num_states}states_{timestamp}.png"

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save with high quality
    plt.savefig(
        output_path, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none"
    )

    print(f"Plot saved as: {output_path}")
    print(f'Plot dimensions: {figsize[0]}" x {figsize[1]}" at {dpi} DPI')

    return fig, ax


def print_summary_statistics(df):
    """Print summary statistics of the IFCT data."""

    print("\n" + "=" * 60)
    print("IFCT ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"Total number of states analyzed: {len(df)}")
    print(
        f"Average CT character: {df['CT_percent'].mean():.1f}% ± {df['CT_percent'].std():.1f}%"
    )
    print(
        f"Average LE character: {df['LE_percent'].mean():.1f}% ± {df['LE_percent'].std():.1f}%"
    )

    # Find predominantly CT and LE states
    ct_threshold = 70.0
    le_threshold = 70.0

    ct_states = df[df["CT_percent"] > ct_threshold]
    le_states = df[df["LE_percent"] > le_threshold]

    print(f"\nStates with >70% CT character: {len(ct_states)}")
    if not ct_states.empty:
        print(f"  States: {', '.join(f'S{s}' for s in ct_states['state'])}")

    print(f"States with >70% LE character: {len(le_states)}")
    if not le_states.empty:
        print(f"  States: {', '.join(f'S{s}' for s in le_states['state'])}")

    # Show top 5 states
    print(f"\nTop 5 states by CT character:")
    top_ct = df.nlargest(5, "CT_percent")
    for _, row in top_ct.iterrows():
        print(
            f"  S{int(row['state'])}: {row['CT_percent']:.1f}% CT, {row['LE_percent']:.1f}% LE"
        )

    print("=" * 60)


def main():
    """Main function with command line interface."""

    parser = argparse.ArgumentParser(
        description="Extract and plot IFCT analysis from MultiWfn output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plot_ifct_analysis.py input.txt
  python plot_ifct_analysis.py input.txt --states 5
  python plot_ifct_analysis.py input.txt --states 3 --output my_plot.png
  python plot_ifct_analysis.py input.txt --figsize 12 8 --dpi 600
        """,
    )

    parser.add_argument("input_file", help="Path to MultiWfn analysis file")
    parser.add_argument(
        "--states",
        "-n",
        type=int,
        default=3,
        help="Number of states to plot (default: 3)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file path (default: auto-generated)"
    )
    parser.add_argument(
        "--figsize",
        nargs=2,
        type=float,
        default=[10, 6],
        help="Figure size in inches (width height, default: 10 6)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for saved figure (default: 300)",
    )
    parser.add_argument(
        "--no-summary", action="store_true", help="Skip printing summary statistics"
    )

    args = parser.parse_args()

    # Validate inputs
    if args.states <= 0:
        raise ValueError("Number of states must be positive")

    if not Path(args.input_file).exists():
        raise FileNotFoundError(f"Input file not found: {args.input_file}")

    try:
        # Parse the data
        print(f"Reading IFCT data from: {args.input_file}")
        df = parse_ifct_data(args.input_file)
        print(f"Successfully parsed data for {len(df)} states")

        # Check if we have enough states
        if args.states > len(df):
            print(
                f"Warning: Requested {args.states} states, but only {len(df)} available. Plotting all {len(df)} states."
            )
            args.states = len(df)

        # Print summary statistics
        if not args.no_summary:
            print_summary_statistics(df)

        # Create the plot
        print(f"\nCreating plot for first {args.states} states...")
        fig, ax = create_ifct_plot(
            df,
            num_states=args.states,
            output_path=args.output,
            figsize=tuple(args.figsize),
            dpi=args.dpi,
        )

        # Show the plot
        plt.show()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
