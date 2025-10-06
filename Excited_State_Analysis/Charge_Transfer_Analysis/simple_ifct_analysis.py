#!/usr/bin/env python3
"""
Simple script to extract and plot IFCT analysis from MultiWfn output.
Uses only standard library modules (no pandas/matplotlib dependencies).

Author: Graduate Chemistry Tutorial
Date: October 2025
"""

import os
import sys
import re
import argparse
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
    list of dict
        List of dictionaries with keys: state, CT_percent, LE_percent
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

    # Validation: CT% + LE% should be close to 100%
    for row in data_rows:
        total = row["CT_percent"] + row["LE_percent"]
        if abs(total - 100.0) > 5.0:
            print(
                f"Warning: State {row['state']} has CT% + LE% = {total:.1f}% (expected ~100%)"
            )

    return data_rows


def create_matplotlib_plot(data, num_states=3, output_path=None):
    """
    Create a bar plot using matplotlib (if available).
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Select the requested number of states
        plot_data = data[:num_states]

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))

        # Set up the bar positions
        states = [str(row["state"]) for row in plot_data]
        x_pos = np.arange(len(states))
        width = 0.4

        # Extract data
        ct_values = [row["CT_percent"] for row in plot_data]
        le_values = [row["LE_percent"] for row in plot_data]

        # Create stacked bars
        ct_bars = ax.bar(
            x_pos,
            ct_values,
            width,
            label="Charge Transfer (CT)",
            color="#D55E00",
            alpha=0.8,
        )
        le_bars = ax.bar(
            x_pos,
            le_values,
            width,
            bottom=ct_values,
            label="Local Excitation (LE)",
            color="#009E73",
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
        ax.set_ylim(0, 110)
        ax.tick_params(axis="y", labelsize=12)

        # Add grid
        # ax.grid(True, alpha=0.3, axis="y")
        # ax.set_axisbelow(True)

        # Add percentage annotations with smart positioning
        for i, (ct_val, le_val) in enumerate(zip(ct_values, le_values)):
            # CT annotation - smart positioning
            ct_center = ct_val / 2
            if ct_val < 15:  # Small CT bar - place text outside or adjust
                if ct_val < 8:  # Very small - place above the bar
                    ax.annotate(
                        f"{ct_val:.1f}%",
                        xy=(i, ct_val + 2),
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        fontweight="bold",
                        color="black",
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="white", alpha=0.8
                        ),
                    )
                else:  # Small but visible - use smaller font inside
                    ax.annotate(
                        f"{ct_val:.1f}%",
                        xy=(i, ct_center),
                        ha="center",
                        va="center",
                        fontsize=9,
                        fontweight="bold",
                        color="white",
                    )
            else:  # Normal size - center placement
                ax.annotate(
                    f"{ct_val:.1f}%",
                    xy=(i, ct_center),
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white",
                )

            # LE annotation - smart positioning
            le_center = ct_val + (le_val / 2)
            if le_val < 15:  # Small LE bar - place text outside or adjust
                if le_val < 8:  # Very small - place above the bar
                    ax.annotate(
                        f"{le_val:.1f}%",
                        xy=(i, ct_val + le_val + 2),
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        fontweight="bold",
                        color="black",
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="white", alpha=0.8
                        ),
                    )
                else:  # Small but visible - use smaller font inside
                    ax.annotate(
                        f"{le_val:.1f}%",
                        xy=(i, le_center),
                        ha="center",
                        va="center",
                        fontsize=9,
                        fontweight="bold",
                        color="white",
                    )
            else:  # Normal size - center placement
                ax.annotate(
                    f"{le_val:.1f}%",
                    xy=(i, le_center),
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white",
                )

        # Add 50% reference line for easy comparison
        ax.axhline(
            y=50,
            color="black",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label="50% Reference",
        )

        # Add legend
        ax.legend(loc="upper right", fontsize=12, framealpha=0.9)

        # Improve layout
        plt.tight_layout()

        # Save the plot
        if output_path is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"IFCT_analysis_{num_states}states_{timestamp}.png"

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save with high quality
        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )

        print(f"Plot saved as: {output_path}")

        # Show the plot
        plt.show()

        return True

    except ImportError:
        print("Matplotlib not available. Plot cannot be created.")
        return False


def create_ascii_plot(data, num_states=3):
    """
    Create a simple ASCII bar chart.
    """
    plot_data = data[:num_states]

    print("\n" + "=" * 60)
    print("ASCII BAR CHART - IFCT Analysis")
    print("=" * 60)

    max_width = 50  # Maximum width of bars in characters

    for row in plot_data:
        state = row["state"]
        ct_percent = row["CT_percent"]
        le_percent = row["LE_percent"]

        # Calculate bar lengths
        ct_width = int((ct_percent / 100.0) * max_width)
        le_width = int((le_percent / 100.0) * max_width)

        # Create bars
        ct_bar = "█" * ct_width
        le_bar = "▓" * le_width

        print(f"\nS{state:2d} CT: |{ct_bar:<{max_width}}| {ct_percent:5.1f}%")
        print(f"     LE: |{le_bar:<{max_width}}| {le_percent:5.1f}%")
        print(f"     Sum: {ct_percent + le_percent:5.1f}%")

    print("\nLegend: █ = Charge Transfer (CT), ▓ = Local Excitation (LE)")
    print("=" * 60)


def print_summary_statistics(data):
    """Print summary statistics of the IFCT data."""

    print("\n" + "=" * 60)
    print("IFCT ANALYSIS SUMMARY")
    print("=" * 60)

    ct_values = [row["CT_percent"] for row in data]
    le_values = [row["LE_percent"] for row in data]

    ct_mean = sum(ct_values) / len(ct_values)
    le_mean = sum(le_values) / len(le_values)

    # Calculate standard deviation
    ct_var = sum((x - ct_mean) ** 2 for x in ct_values) / len(ct_values)
    le_var = sum((x - le_mean) ** 2 for x in le_values) / len(le_values)
    ct_std = ct_var**0.5
    le_std = le_var**0.5

    print(f"Total number of states analyzed: {len(data)}")
    print(f"Average CT character: {ct_mean:.1f}% ± {ct_std:.1f}%")
    print(f"Average LE character: {le_mean:.1f}% ± {le_std:.1f}%")

    # Find predominantly CT and LE states
    ct_threshold = 70.0
    le_threshold = 70.0

    ct_states = [row for row in data if row["CT_percent"] > ct_threshold]
    le_states = [row for row in data if row["LE_percent"] > le_threshold]

    print(f"\nStates with >70% CT character: {len(ct_states)}")
    if ct_states:
        ct_state_names = [f"S{row['state']}" for row in ct_states]
        print(f"  States: {', '.join(ct_state_names)}")

    print(f"States with >70% LE character: {len(le_states)}")
    if le_states:
        le_state_names = [f"S{row['state']}" for row in le_states]
        print(f"  States: {', '.join(le_state_names)}")

    # Show top 5 states by CT character
    print(f"\nTop 5 states by CT character:")
    sorted_by_ct = sorted(data, key=lambda x: x["CT_percent"], reverse=True)
    for row in sorted_by_ct[:5]:
        print(
            f"  S{row['state']}: {row['CT_percent']:.1f}% CT, {row['LE_percent']:.1f}% LE"
        )

    print("=" * 60)


def print_data_table(data, num_states=None):
    """Print the data in a formatted table."""

    if num_states is None:
        display_data = data
        title = "All States"
    else:
        display_data = data[:num_states]
        title = f"First {num_states} States"

    print(f"\n{title} - IFCT Summary Data:")
    print("-" * 50)
    print(f"{'State':<8} {'CT %':<10} {'LE %':<10} {'Total %':<10}")
    print("-" * 50)

    for row in display_data:
        total = row["CT_percent"] + row["LE_percent"]
        print(
            f"S{row['state']:<7} {row['CT_percent']:<10.1f} {row['LE_percent']:<10.1f} {total:<10.1f}"
        )

    print("-" * 50)


def main():
    """Main function with command line interface."""

    parser = argparse.ArgumentParser(
        description="Extract and plot IFCT analysis from MultiWfn output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_ifct_analysis.py input.txt
  python simple_ifct_analysis.py input.txt --states 5
  python simple_ifct_analysis.py input.txt --states 3 --output my_plot.png
        """,
    )

    parser.add_argument("input_file", help="Path to MultiWfn analysis file")
    parser.add_argument(
        "--states",
        "-n",
        type=int,
        default=3,
        help="Number of states to analyze (default: 3)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file path for plot (default: auto-generated)"
    )
    parser.add_argument(
        "--no-summary", action="store_true", help="Skip printing summary statistics"
    )
    parser.add_argument(
        "--ascii-only",
        action="store_true",
        help="Only create ASCII plot (skip matplotlib)",
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
        data = parse_ifct_data(args.input_file)
        print(f"Successfully parsed data for {len(data)} states")

        # Check if we have enough states
        if args.states > len(data):
            print(
                f"Warning: Requested {args.states} states, but only {len(data)} available. Using all {len(data)} states."
            )
            args.states = len(data)

        # Print data table
        print_data_table(data, args.states)

        # Print summary statistics
        if not args.no_summary:
            print_summary_statistics(data)

        # Create plots
        if args.ascii_only:
            create_ascii_plot(data, args.states)
        else:
            # Try matplotlib first, fall back to ASCII
            plot_created = create_matplotlib_plot(data, args.states, args.output)
            if not plot_created:
                print("\nFalling back to ASCII plot...")
                create_ascii_plot(data, args.states)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
