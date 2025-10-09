"""
Unified Electronic Coupling and Exciton Bandwidth Analysis Script

This script combines functionality from three separate scripts:
1. plot_coupling_disorder_lcwpbe_d3.py
2. plot_coupling_disorder_wB97xD2.py
3. compute_and_plot_exciton_bandwidth.py

Features:
- Parse electronic coupling, disorder, and monomer site energies
- Calculate exciton bandwidths using Hamiltonian diagonalization
- Generate comprehensive plots for both functionals (LC-wPBE and wB97xD2)
- Create coupling plots with bandwidth insets
- Generate dedicated bandwidth analysis plots
- Export summary data to CSV files

Author: Combined from original scripts
Date: October 2025
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import FormatStrFormatter

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Matplotlib settings for publication-quality plots
plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 14,
        "axes.labelsize": 18,
        "axes.titlesize": 18,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 14,
        "legend.title_fontsize": 14,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.linewidth": 1.2,
        "xtick.major.width": 1.2,
        "ytick.major.width": 1.2,
    }
)

# Figure settings
FIGURE_SIZE = (8, 6)
FIGSIZE_MULTI = (11, 4)  # for multi-panel plots
FIGSIZE_SINGLE = (10, 6)  # for single plots
SAVE_DPI = 300

# Color scheme for topologies
COLORS = {
    "TSM": "#1f77b4",  # Blue
    "TTA": "#ECE133",  # Yellow
    "TTL": "#029E73",  # Green
}

# Environment colors for bandwidth plots
ENV_COLORS = {"Vacuum": "blue", "Solvent (Water, IEFPCM)": "black"}

# Topology display names for legends
TOPOLOGY_LABELS = {
    "TSM": "PDI-Free",
    "TTA": "PDI-Sandwiched",
    "TTL": "PDI-Zigzagged",
}

# Dimer display names for x-axis
DIMER_LABELS = {
    "V12": r"V$_{TM}$",
    "V23": r"V$_{MB}$",
    "V13": r"V$_{TB}$",
}

# Directory paths
INPUT_DIR = Path("C:/Users/401770/Documents/data")
OUTPUT_DIR = Path(
    "C:/Users/401770/OneDrive - Los Alamos National Laboratory/PostDoc/LANL/"
    "UNM_Project/publication_data/Oct_04_2025"
)

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATA PARSING FUNCTIONS
# ============================================================================


def parse_file_basic(topology, path):
    """
    Basic parser for electronic coupling and disorder data only.
    Used for coupling/disorder plots.
    """
    data = []
    env = None
    dimer = None

    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if s.startswith("# Vacuum"):
                env = "Vacuum"
            elif "Solvent" in s or "Water" in s:
                if s.startswith("#"):
                    env = "Solvent (Water, IEFPCM)"
            elif s.startswith("## Dimer"):
                m = re.search(r"V(\d{2})", s)
                if m:
                    dimer = f"V{m.group(1)}"
            elif "Electronic Coupling (eV):" in s:
                val = float(s.split(":")[-1].strip())
                data.append(
                    dict(
                        Topology=topology,
                        Environment=env,
                        Dimer=dimer,
                        Metric="Electronic Coupling (eV)",
                        Value=val,
                    )
                )
            elif "Disorder (eV):" in s:
                val = float(s.split(":")[-1].strip())
                data.append(
                    dict(
                        Topology=topology,
                        Environment=env,
                        Dimer=dimer,
                        Metric="Disorder (eV)",
                        Value=val,
                    )
                )

    return pd.DataFrame(data)


def parse_with_monomers(topology, path):
    """
    Enhanced parser that extracts coupling, disorder, AND monomer site energies.
    Used for bandwidth calculations.
    """
    env = None
    dimer = None
    rows = []
    monomer_rows = []

    with open(path, "r") as f:
        for raw in f:
            s = raw.strip()
            if s.startswith("# Vacuum"):
                env = "Vacuum"
            elif s.startswith("#") and ("Solvent" in s or "Water" in s):
                env = "Solvent (Water, IEFPCM)"

            # Parse dimer sections
            m_dimer = re.match(r"##\s*Dimer\s*V(\d{2})", s)
            if m_dimer:
                dimer = f"V{m_dimer.group(1)}"

            # Parse monomer site energies
            m_mono = re.match(r"###\s*Monomer_(\d+)\s*-\s*S1:\s*([0-9]*\.?[0-9]+)", s)
            if m_mono and env is not None:
                idx = int(m_mono.group(1))
                val = float(m_mono.group(2))
                monomer_rows.append(
                    dict(Topology=topology, Environment=env, Monomer=idx, S1_eV=val)
                )

            # Parse electronic coupling
            if "Electronic Coupling (eV):" in s and env and dimer:
                val = float(s.split(":")[-1].strip())
                rows.append(
                    dict(
                        Topology=topology,
                        Environment=env,
                        Dimer=dimer,
                        Metric="J (eV)",
                        Value=val,
                    )
                )

            # Parse disorder
            if "Disorder (eV):" in s and env and dimer:
                val = float(s.split(":")[-1].strip())
                rows.append(
                    dict(
                        Topology=topology,
                        Environment=env,
                        Dimer=dimer,
                        Metric="Disorder (eV)",
                        Value=val,
                    )
                )

    df = pd.DataFrame(rows)
    monomers = pd.DataFrame(monomer_rows)

    if not monomers.empty:
        monomers = monomers.sort_values(
            ["Topology", "Environment", "Monomer"]
        ).drop_duplicates(["Topology", "Environment", "Monomer"], keep="last")

    return df, monomers


def load_functional_data(functional_tag):
    """
    Load all data for a specific functional (lcwpbe or wb97xd2).
    Returns both basic and enhanced datasets.
    """
    # Define input files
    files = {
        "TSM": INPUT_DIR
        / f"TSM/{functional_tag}/Trimer_Starting_Materials_electronic_coupling_{functional_tag}.txt",
        "TTA": INPUT_DIR
        / f"TTA/{functional_tag}/Trimer_Tethered_Alternate_electronic_coupling_{functional_tag}.txt",
        "TTL": INPUT_DIR
        / f"TTL/{functional_tag}/Trimer_Tethered_Linear_electronic_coupling_{functional_tag}.txt",
    }

    # Parse with both methods
    basic_frames = []
    enhanced_frames = []
    monomer_frames = []

    for topo, path in files.items():
        # Basic parsing
        basic_df = parse_file_basic(topo, str(path))
        basic_df["Functional"] = functional_tag.upper()
        basic_frames.append(basic_df)

        # Enhanced parsing with monomers
        enhanced_df, mons = parse_with_monomers(topo, str(path))
        enhanced_df["Functional"] = functional_tag.upper()
        mons["Functional"] = functional_tag.upper()
        enhanced_frames.append(enhanced_df)
        monomer_frames.append(mons)

    basic_data = pd.concat(basic_frames, ignore_index=True)
    enhanced_data = pd.concat(enhanced_frames, ignore_index=True)
    monomer_data = pd.concat(monomer_frames, ignore_index=True)

    return basic_data, enhanced_data, monomer_data


# ============================================================================
# BANDWIDTH CALCULATION FUNCTIONS
# ============================================================================


def bandwidth_full(eps, j12, j23, j13):
    """
    Calculate exciton bandwidth using Hamiltonian diagonalization.

    Parameters:
    - eps: Site energies [E1, E2, E3]
    - j12, j23, j13: Electronic couplings between sites

    Returns:
    - Bandwidth (max eigenvalue - min eigenvalue)
    """
    e = np.array(eps, float)
    e = e - e.mean()  # Center energies around mean

    # Build 3x3 Hamiltonian matrix
    H = np.array([[e[0], j12, j13], [j12, e[1], j23], [j13, j23, e[2]]], dtype=float)

    # Diagonalize to get eigenvalues
    w = np.linalg.eigvalsh(H)

    return float(w.max() - w.min())


def build_full_tables(metrics_df, monomers_df):
    """
    Build comprehensive tables with coupling and monomer data.
    """
    # Pivot coupling data
    coup = (
        metrics_df[metrics_df["Metric"] == "J (eV)"]
        .pivot_table(
            index=["Functional", "Topology", "Environment"],
            columns="Dimer",
            values="Value",
        )
        .reset_index()
    )

    # Pivot monomer data
    mons = (
        monomers_df.pivot_table(
            index=["Functional", "Topology", "Environment"],
            columns="Monomer",
            values="S1_eV",
        )
        .reset_index()
        .rename(columns={1: "E1 (eV)", 2: "E2 (eV)", 3: "E3 (eV)"})
    )

    # Merge coupling and monomer data
    full = coup.merge(mons, on=["Functional", "Topology", "Environment"], how="left")

    return full


def compute_bandwidths(full_df):
    """
    Compute bandwidths for all systems using both equal-sites and actual site energies.
    """
    rows = []

    for _, r in full_df.iterrows():
        F = r["Functional"]
        topo = r["Topology"]
        env = r["Environment"]
        j12, j23, j13 = float(r["V12"]), float(r["V23"]), float(r["V13"])
        e1, e2, e3 = float(r["E1 (eV)"]), float(r["E2 (eV)"]), float(r["E3 (eV)"])

        # Calculate bandwidths
        W_equal = bandwidth_full((0.0, 0.0, 0.0), j12, j23, j13)  # Equal site energies
        W_eps = bandwidth_full((e1, e2, e3), j12, j23, j13)  # Actual site energies

        rows.append([F, topo, env, j12, j23, j13, e1, e2, e3, W_equal, W_eps])

    out = pd.DataFrame(
        rows,
        columns=[
            "Functional",
            "Topology",
            "Environment",
            "V12",
            "V23",
            "V13",
            "E1",
            "E2",
            "E3",
            "Bandwidth (Equal-sites) (eV)",
            "Bandwidth (With site energies) (eV)",
        ],
    )

    return out


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================


def save_figure(fig, filename):
    """Save figure in both PNG and PDF formats."""
    png_path = OUTPUT_DIR / (filename + ".png")
    pdf_path = OUTPUT_DIR / (filename + ".pdf")

    fig.savefig(png_path, dpi=SAVE_DPI, bbox_inches="tight", format="png")
    fig.savefig(pdf_path, dpi=SAVE_DPI, bbox_inches="tight", format="pdf")

    return png_path, pdf_path


def create_coupling_plot_with_bandwidth_inset(
    coupling_data, bandwidth_data, functional, environment, env_label
):
    """
    Create electronic coupling plot with bandwidth inset.
    Replicates functionality from the original coupling/disorder scripts.
    """
    # Filter data for specific functional and environment
    env_key = "Vacuum" if environment == "vacuum" else "Solvent (Water, IEFPCM)"
    env_data = coupling_data[
        (coupling_data["Environment"] == env_key)
        & (coupling_data["Functional"] == functional.upper())
    ]

    # Create pivot table for plotting
    coupling_subset = env_data[env_data["Metric"] == "Electronic Coupling (eV)"]
    pivot_data = coupling_subset.pivot(
        index="Dimer", columns="Topology", values="Value"
    ).loc[["V12", "V23", "V13"]]

    # Rename for display
    pivot_data = pivot_data.rename(columns=TOPOLOGY_LABELS)
    pivot_data = pivot_data.rename(index=DIMER_LABELS)

    # Create main plot
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    pivot_data.plot(
        kind="bar",
        rot=0,
        ax=ax,
        color=[COLORS[col] for col in ["TSM", "TTA", "TTL"]],
        legend=False,
    )

    ax.set_ylabel("Electronic Coupling [eV]", fontweight="bold")
    ax.set_xlabel("Dimer", fontweight="bold")

    # Set y-axis limits based on functional
    if functional.lower() == "lcwpbe":
        ax.set_ylim(0.0, 0.45)
        ax.set_yticks(np.linspace(0.0, 0.45, 5))
    else:  # wb97xd2
        ax.set_ylim(0.0, 0.45)
        ax.set_yticks(np.linspace(0.0, 0.45, 5))

    ax.yaxis.set_major_formatter("{x:.2f}")

    # Place legend at the top
    ax.legend(
        ["PDI-Free", "PDI-Sandwiched", "PDI-Zigzagged"],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.095),
        ncol=3,
        frameon=False,
    )

    # Annotate bars with values
    for p in ax.patches:
        height = p.get_height()  # type: ignore
        ax.annotate(
            f"{height:.2f}",
            xy=(p.get_x() + p.get_width() / 2, height),  # type: ignore
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    # Add bandwidth inset
    ax_inset = fig.add_axes((0.665, 0.632, 0.30, 0.25))  # type: ignore

    # Get bandwidth values
    bandwidth_subset = bandwidth_data[
        (bandwidth_data["Functional"] == functional.upper())
        & (bandwidth_data["Environment"] == env_key)
    ]

    bandwidth_labels = ["PDI-Free", "PDI-Sandwiched", "PDI-Zigzagged"]
    topology_map = {"PDI-Free": "TSM", "PDI-Sandwiched": "TTA", "PDI-Zigzagged": "TTL"}

    bandwidth_values = []
    for label in bandwidth_labels:
        topo = topology_map[label]
        value = bandwidth_subset[bandwidth_subset["Topology"] == topo][
            "Bandwidth (With site energies) (eV)"
        ]
        if len(value) > 0:
            bandwidth_values.append(float(value.values[0]) * 1000)  # Convert to meV
        else:
            bandwidth_values.append(0.0)

    x_pos = np.arange(len(bandwidth_labels))
    bars = ax_inset.bar(
        x_pos, bandwidth_values, color=[COLORS["TSM"], COLORS["TTA"], COLORS["TTL"]]
    )

    ax_inset.set_ylabel("Bandwidth [meV]", fontsize=12, fontweight="bold")
    ax_inset.set_xticks(x_pos)
    ax_inset.set_xticklabels(
        bandwidth_labels, fontsize=10, rotation=45, ha="right", fontweight="bold"
    )
    ax_inset.set_ylim(0, 800)
    ax_inset.set_yticks(np.linspace(0, 800, 5))
    ax_inset.tick_params(labelsize=10)
    ax_inset.yaxis.set_major_formatter("{x:.0f}")

    # Annotate inset bars
    for i, (bar, val) in enumerate(zip(bars, bandwidth_values)):
        ax_inset.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{val:.1f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()

    # Generate filename
    filename = f"electronic_coupling_{environment}_{functional.lower()}"
    return fig, filename


def plot_bandwidth_by_environment(
    bw_df, funcs, topo_order, metric_key, metric_label, env, env_label
):
    """
    Create multi-panel bandwidth plot for specific environment.
    """
    fig, axes = plt.subplots(1, len(funcs), figsize=FIGSIZE_MULTI, sharey=True)
    if len(funcs) == 1:
        axes = [axes]

    x = np.arange(len(topo_order))
    width = 0.5

    for ax, func in zip(axes, funcs):
        subset = bw_df[(bw_df["Functional"] == func) & (bw_df["Environment"] == env)]
        heights = []

        for topo in topo_order:
            sel = subset[subset["Topology"] == topo][metric_key]
            heights.append(
                float(sel.values[0]) * 1000 if len(sel) else np.nan
            )  # Convert to meV

        bars = ax.bar(x, heights, width, color=ENV_COLORS[env])

        # Annotate bars
        for rect, h in zip(bars, heights):
            if not np.isnan(h):
                ax.text(
                    rect.get_x() + rect.get_width() / 2,
                    h + 20,
                    f"{h:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=16,
                )

        ax.set_xticks(x)
        ax.set_xticklabels(
            ["PDI-Free", "PDI-Sandwiched", "PDI-Zigzagged"], fontweight="bold"
        )
        ax.set_xlabel("Topology", fontweight="bold")
        if ax is axes[0]:
            ax.set_ylabel("Bandwidth [meV]", fontweight="bold")

        # Y-axis formatting
        ax.set_ylim(0.0, 1100.0)
        y_ticks = np.arange(0, 1100, 200)
        ax.set_yticks(y_ticks)
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))

    fig.suptitle(f"{metric_label} — {env_label}", fontsize=20)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))  # type: ignore
    return fig


def plot_bandwidth_single(
    subset, func, topo_order, metric_key, metric_label, env, env_label
):
    """
    Create single bandwidth plot for one functional and environment.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
    x = np.arange(len(topo_order))
    width = 0.5

    heights = []
    for topo in topo_order:
        sel = subset[(subset["Topology"] == topo) & (subset["Environment"] == env)][
            metric_key
        ]
        heights.append(
            float(sel.values[0]) * 1000 if len(sel) else np.nan
        )  # Convert to meV

    bars = ax.bar(x, heights, width, color=ENV_COLORS[env])

    # Annotate bars
    for rect, h in zip(bars, heights):
        if not np.isnan(h):
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                h + 20,
                f"{h:.1f}",
                ha="center",
                va="bottom",
                fontsize=16,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(
        ["PDI-Free", "PDI-Sandwiched", "PDI-Zigzagged"], fontweight="bold"
    )
    ax.set_xlabel("Topology", fontweight="bold")
    ax.set_ylabel("Bandwidth [meV]", fontweight="bold")

    # Y-axis formatting
    ax.set_ylim(0.0, 800.0)
    y_ticks = np.linspace(0, 800, 5)
    ax.set_yticks(y_ticks)
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))

    fig.tight_layout()
    return fig


# ============================================================================
# DATA ANALYSIS FUNCTIONS
# ============================================================================


def compute_summary_statistics(coupling_df, disorder_df):
    """
    Compute summary statistics including nearest-neighbor averages,
    long-range coupling averages, and percent changes.
    """
    # 1) Nearest-neighbor (V12 & V23) average per topology & environment
    nn_avg = (
        coupling_df[coupling_df["Dimer"].isin(["V12", "V23"])]
        .groupby(["Topology", "Environment", "Functional"])["Electronic Coupling (eV)"]
        .mean()
        .reset_index()
        .rename(columns={"Electronic Coupling (eV)": "NN Avg Coupling (eV)"})
    )

    # 2) Long-range (V13) mean per topology & environment
    lr_avg = (
        coupling_df[coupling_df["Dimer"] == "V13"]
        .groupby(["Topology", "Environment", "Functional"])["Electronic Coupling (eV)"]
        .mean()
        .reset_index()
        .rename(columns={"Electronic Coupling (eV)": "Long-Range (V13) Coupling (eV)"})
    )

    # 3) Disorder averages per topology & environment
    disorder_avg = (
        disorder_df.groupby(["Topology", "Environment", "Functional"])["Disorder (eV)"]
        .mean()
        .reset_index()
        .rename(columns={"Disorder (eV)": "Avg Disorder (eV)"})
    )

    return nn_avg, lr_avg, disorder_avg


def compute_percent_changes(nn_avg, lr_avg, disorder_avg):
    """
    Compute percent changes from vacuum to solvent for all functionals.
    """

    def percent_change(vac, solv):
        return (solv - vac) / vac * 100.0

    rows = []

    for functional in ["LCWPBE", "WB97XD2"]:
        for topo in ["TSM", "TTA", "TTL"]:
            # Get values for this functional and topology
            nn_vac = nn_avg[
                (nn_avg.Topology == topo)
                & (nn_avg.Environment == "Vacuum")
                & (nn_avg.Functional == functional)
            ]["NN Avg Coupling (eV)"]

            nn_sol = nn_avg[
                (nn_avg.Topology == topo)
                & (nn_avg.Environment == "Solvent (Water, IEFPCM)")
                & (nn_avg.Functional == functional)
            ]["NN Avg Coupling (eV)"]

            lr_vac = lr_avg[
                (lr_avg.Topology == topo)
                & (lr_avg.Environment == "Vacuum")
                & (lr_avg.Functional == functional)
            ]["Long-Range (V13) Coupling (eV)"]

            lr_sol = lr_avg[
                (lr_avg.Topology == topo)
                & (lr_avg.Environment == "Solvent (Water, IEFPCM)")
                & (lr_avg.Functional == functional)
            ]["Long-Range (V13) Coupling (eV)"]

            d_vac = disorder_avg[
                (disorder_avg.Topology == topo)
                & (disorder_avg.Environment == "Vacuum")
                & (disorder_avg.Functional == functional)
            ]["Avg Disorder (eV)"]

            d_sol = disorder_avg[
                (disorder_avg.Topology == topo)
                & (disorder_avg.Environment == "Solvent (Water, IEFPCM)")
                & (disorder_avg.Functional == functional)
            ]["Avg Disorder (eV)"]

            # Only compute if all values exist
            if (
                len(nn_vac) > 0
                and len(nn_sol) > 0
                and len(lr_vac) > 0
                and len(lr_sol) > 0
                and len(d_vac) > 0
                and len(d_sol) > 0
            ):

                rows.append(
                    {
                        "Functional": functional,
                        "Topology": topo,
                        "ΔNN Coupling % (Solvent vs Vacuum)": percent_change(
                            nn_vac.values[0], nn_sol.values[0]
                        ),
                        "ΔLong-Range (V13) Coupling %": percent_change(
                            lr_vac.values[0], lr_sol.values[0]
                        ),
                        "ΔAvg Disorder %": percent_change(
                            d_vac.values[0], d_sol.values[0]
                        ),
                    }
                )

    return pd.DataFrame(rows)


def display_table(title, df):
    """Print a title and a pandas DataFrame using pandas' to_string formatting."""
    print("\n" + title)
    print("=" * len(title))
    try:
        print(df.to_string(index=False))
    except Exception:
        print(df)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """
    Main execution function that combines all analysis steps.
    """
    print("=" * 80)
    print("UNIFIED ELECTRONIC COUPLING AND EXCITON BANDWIDTH ANALYSIS")
    print("=" * 80)

    # Load data for both functionals
    print("\n📁 Loading data for both functionals...")

    # LC-wPBE data
    lcwpbe_basic, lcwpbe_enhanced, lcwpbe_monomers = load_functional_data("lcwpbe")

    # wB97xD2 data
    wb97xd2_basic, wb97xd2_enhanced, wb97xd2_monomers = load_functional_data("wb97xd2")

    # Combine all data
    all_basic = pd.concat([lcwpbe_basic, wb97xd2_basic], ignore_index=True)
    all_enhanced = pd.concat([lcwpbe_enhanced, wb97xd2_enhanced], ignore_index=True)
    all_monomers = pd.concat([lcwpbe_monomers, wb97xd2_monomers], ignore_index=True)

    print(f"✅ Loaded data for {len(all_basic)} coupling/disorder measurements")
    print(f"✅ Loaded data for {len(all_monomers)} monomer site energies")

    # ========================================================================
    # BANDWIDTH CALCULATIONS
    # ========================================================================

    print("\n⚙️ Computing exciton bandwidths...")

    # Build full tables and compute bandwidths
    lcwpbe_full = build_full_tables(lcwpbe_enhanced, lcwpbe_monomers)
    wb97xd2_full = build_full_tables(wb97xd2_enhanced, wb97xd2_monomers)

    bw_lcwpbe = compute_bandwidths(lcwpbe_full)
    bw_wb97xd2 = compute_bandwidths(wb97xd2_full)

    # Combine bandwidth results
    bw_all = pd.concat([bw_lcwpbe, bw_wb97xd2], ignore_index=True)

    print(f"✅ Computed bandwidths for {len(bw_all)} systems")

    # ========================================================================
    # DATA SUMMARIES
    # ========================================================================

    print("\n📊 Computing summary statistics...")

    # Split basic data into coupling and disorder
    coupling_df = (
        all_basic[all_basic["Metric"] == "Electronic Coupling (eV)"]
        .drop(columns=["Metric"])
        .rename(columns={"Value": "Electronic Coupling (eV)"})
    )
    disorder_df = (
        all_basic[all_basic["Metric"] == "Disorder (eV)"]
        .drop(columns=["Metric"])
        .rename(columns={"Value": "Disorder (eV)"})
    )

    # Compute summaries
    nn_avg, lr_avg, disorder_avg = compute_summary_statistics(coupling_df, disorder_df)

    # Compute percent changes
    delta_df = compute_percent_changes(nn_avg, lr_avg, disorder_avg)

    # Display key results
    display_table(
        "Monomer Site Energies — LC-wPBE",
        lcwpbe_monomers.sort_values(["Topology", "Environment", "Monomer"]),
    )

    display_table(
        "Monomer Site Energies — wB97xD2",
        wb97xd2_monomers.sort_values(["Topology", "Environment", "Monomer"]),
    )

    display_table(
        "Exciton Bandwidths — LC-wPBE",
        bw_lcwpbe.sort_values(["Environment", "Topology"]),
    )

    display_table(
        "Exciton Bandwidths — wB97xD2",
        bw_wb97xd2.sort_values(["Environment", "Topology"]),
    )

    display_table(
        "Electronic Coupling Summary",
        coupling_df.sort_values(["Functional", "Environment", "Dimer", "Topology"]),
    )

    display_table(
        "Nearest-Neighbor Coupling Averages",
        nn_avg.sort_values(["Functional", "Environment", "Topology"]),
    )

    display_table(
        "Long-Range Coupling Averages",
        lr_avg.sort_values(["Functional", "Environment", "Topology"]),
    )

    display_table(
        "Average Disorder",
        disorder_avg.sort_values(["Functional", "Environment", "Topology"]),
    )

    display_table(
        "Solvent vs Vacuum Changes (%)",
        delta_df.sort_values(["Functional", "Topology"]),
    )

    # ========================================================================
    # PLOTTING
    # ========================================================================

    print("\n📈 Generating plots...")

    functionals = ["LCWPBE", "WB97XD2"]
    environments = [("vacuum", "Vacuum"), ("wat", "Solvent")]

    generated_files = []

    # 1. Electronic coupling plots with bandwidth insets
    print("\n  📊 Creating coupling plots with bandwidth insets...")
    for functional in ["lcwpbe", "wb97xd2"]:
        for env_code, env_label in environments:
            try:
                fig, filename = create_coupling_plot_with_bandwidth_inset(
                    all_basic, bw_all, functional, env_code, env_label
                )
                png_path, pdf_path = save_figure(fig, filename)
                generated_files.extend([png_path, pdf_path])
                plt.close(fig)
                print(f"    ✅ {filename}")
            except Exception as e:
                print(f"    ❌ Error creating {functional} {env_code} plot: {e}")

    # 2. Dedicated bandwidth analysis plots
    print("\n  📊 Creating dedicated bandwidth plots...")

    topo_order = ["TSM", "TTA", "TTL"]
    env_order = ["Vacuum", "Solvent (Water, IEFPCM)"]
    env_labels = {"Vacuum": "Vacuum", "Solvent (Water, IEFPCM)": "Solvent"}

    # Bandwidth metrics to plot
    metrics = [
        (
            "Bandwidth (Equal-sites) (eV)",
            "Exciton Bandwidth (Equal-sites)",
            "equal_sites",
        ),
        (
            "Bandwidth (With site energies) (eV)",
            "Exciton Bandwidth (With Site Energies)",
            "with_site_energies",
        ),
    ]

    for metric_key, metric_label, metric_slug in metrics:
        for env in env_order:
            env_slug = env_labels[env].lower()

            # Multi-panel plot (all functionals, one environment)
            try:
                fig = plot_bandwidth_by_environment(
                    bw_all,
                    functionals,
                    topo_order,
                    metric_key,
                    metric_label,
                    env,
                    env_labels[env],
                )
                png_path, pdf_path = save_figure(
                    fig, f"bandwidth_{metric_slug}_{env_slug}_multi"
                )
                generated_files.extend([png_path, pdf_path])
                plt.close(fig)
                print(f"    ✅ bandwidth_{metric_slug}_{env_slug}_multi")
            except Exception as e:
                print(f"    ❌ Error creating {metric_slug} {env_slug} multi plot: {e}")

            # Single plots (one functional, one environment)
            for func in functionals:
                try:
                    subset = bw_all[bw_all["Functional"] == func]
                    fig = plot_bandwidth_single(
                        subset,
                        func,
                        topo_order,
                        metric_key,
                        metric_label,
                        env,
                        env_labels[env],
                    )
                    filename = f"bandwidth_{metric_slug}_{env_slug}_{func.lower()}"
                    png_path, pdf_path = save_figure(fig, filename)
                    generated_files.extend([png_path, pdf_path])
                    plt.close(fig)
                    print(f"    ✅ {filename}")
                except Exception as e:
                    print(
                        f"    ❌ Error creating {func} {env_slug} {metric_slug} plot: {e}"
                    )

    # ========================================================================
    # EXPORT DATA
    # ========================================================================

    print("\n💾 Exporting summary data...")

    # Export comprehensive summary
    summary_export = coupling_df.merge(
        disorder_df, on=["Topology", "Environment", "Dimer", "Functional"]
    ).sort_values(["Functional", "Environment", "Dimer", "Topology"])

    csv_path = OUTPUT_DIR / "unified_coupling_disorder_summary.csv"
    summary_export.to_csv(csv_path, index=False)
    generated_files.append(csv_path)

    # Export bandwidth results
    bandwidth_csv = OUTPUT_DIR / "unified_exciton_bandwidths.csv"
    bw_all.to_csv(bandwidth_csv, index=False)
    generated_files.append(bandwidth_csv)

    # Export monomer site energies
    monomers_csv = OUTPUT_DIR / "unified_monomer_site_energies.csv"
    all_monomers.to_csv(monomers_csv, index=False)
    generated_files.append(monomers_csv)

    # Export summary statistics
    nn_avg_csv = OUTPUT_DIR / "unified_nearest_neighbor_averages.csv"
    nn_avg.to_csv(nn_avg_csv, index=False)
    generated_files.append(nn_avg_csv)

    lr_avg_csv = OUTPUT_DIR / "unified_long_range_averages.csv"
    lr_avg.to_csv(lr_avg_csv, index=False)
    generated_files.append(lr_avg_csv)

    disorder_avg_csv = OUTPUT_DIR / "unified_disorder_averages.csv"
    disorder_avg.to_csv(disorder_avg_csv, index=False)
    generated_files.append(disorder_avg_csv)

    # Export percent changes
    delta_csv = OUTPUT_DIR / "unified_percent_changes.csv"
    delta_df.to_csv(delta_csv, index=False)
    generated_files.append(delta_csv)

    print(f"✅ Exported coupling/disorder summary: {csv_path}")
    print(f"✅ Exported bandwidth results: {bandwidth_csv}")
    print(f"✅ Exported monomer energies: {monomers_csv}")
    print(f"✅ Exported nearest-neighbor averages: {nn_avg_csv}")
    print(f"✅ Exported long-range averages: {lr_avg_csv}")
    print(f"✅ Exported disorder averages: {disorder_avg_csv}")
    print(f"✅ Exported percent changes: {delta_csv}")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"📁 Total files generated: {len(generated_files)}")
    print(
        f"📊 Plots created: {len([f for f in generated_files if f.suffix in ['.png', '.pdf']])}"
    )
    print(
        f"💾 Data files exported: {len([f for f in generated_files if f.suffix == '.csv'])}"
    )
    print(f"📍 Output directory: {OUTPUT_DIR}")

    return generated_files


if __name__ == "__main__":
    generated_files = main()
