import re
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Developer Info
__author__ = "Ajay Khanna"
__email__ = "akhanna2@lanl.gov"
__version__ = "1.0.0"


# ============================================================================
# PRODUCTION PLOT CONFIGURATION
# ============================================================================

# Figure settings
FIGURE_WIDTH = 10  # inches
FIGURE_HEIGHT = 6  # inches
FIGURE_DPI = 300  # high resolution for publications

# Font settings
FONT_SIZE = 18
FONT_FAMILY = "serif"
FONT_WEIGHT = "normal"

# Line and marker settings
LINE_WIDTH = 2.5
MARKER_EDGE_WIDTH = 1.5
MARKER_ALPHA = 0.85
LINE_ALPHA = 0.6

# Color scheme (colorblind-friendly palette)
COLORBLIND_COLORS = [
    "#0173B2",  # Blue
    "#DE8F05",  # Orange
    "#029E73",  # Green
    "#CC78BC",  # Purple
    "#CA9161",  # Brown
    "#ECE133",  # Yellow
]

# Marker styles
MARKER_STYLES = ["o", "s", "^", "D", "v", "P"]

# Output settings
OUTPUT_FORMATS = ["png", "pdf"]  # Add "svg" if needed
OUTPUT_DIR = Path("output_plots")

# Plot appearance
GRID_STYLE = "--"
GRID_ALPHA = 0.3
LEGEND_FRAMEALPHA = 0.9
LEGEND_SHADOW = True

# Apply global matplotlib settings
plt.rcParams.update(
    {
        "font.size": FONT_SIZE,
        "font.family": FONT_FAMILY,
        "font.weight": FONT_WEIGHT,
        "figure.dpi": FIGURE_DPI,
        "figure.figsize": (FIGURE_WIDTH, FIGURE_HEIGHT),
        "axes.linewidth": 1.5,
        "axes.labelsize": FONT_SIZE + 2,
        "axes.titlesize": FONT_SIZE + 4,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "xtick.major.width": 1.5,
        "ytick.major.width": 1.5,
        "xtick.major.size": 6,
        "ytick.major.size": 6,
        "legend.fontsize": FONT_SIZE - 1,
        "legend.framealpha": LEGEND_FRAMEALPHA,
        "savefig.dpi": FIGURE_DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    }
)

# ============================================================================
# FILE PATHS
# ============================================================================

file_path = [
    "C:/Users/401770/Documents/data/single_material/electronic_properties.md",
    "C:/Users/401770/Documents/data/TSM/electronic_properties.md",
    "C:/Users/401770/Documents/data/TTA/electronic_properties.md",
    "C:/Users/401770/Documents/data/TTL/electronic_properties.md",
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def setup_output_directory(output_dir: Path = OUTPUT_DIR) -> Path:
    """
    Create output directory if it doesn't exist.

    Parameters
    ----------
    output_dir : Path
        Directory path for saving plots.

    Returns
    -------
    Path
        The created/existing output directory path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def parse_excited_states(filename: str) -> dict:
    """
    Parse excited state data from a Markdown file containing DFT functional sections.

    The function extracts transitions (state index, excitation energy in eV,
    and oscillator strength) and organizes them in a nested dictionary structured as:

    {
        "<Functional Name>": {
            "Vacuum": [
                {"state": int, "energy": float, "osc_strength": float},
                ...
            ],
            "Solvent": [
                {"state": int, "energy": float, "osc_strength": float},
                ...
            ]
        },
        ...
    }

    Parameters
    ----------
    filename : str
        Path to the Markdown file containing excited state data.

    Returns
    -------
    dict
        Nested dictionary with parsed excited state data.
    """

    results = {}
    current_functional = None
    current_env = None

    # Regex patterns
    functional_pattern = re.compile(r"# .*DFT Functional:\s*(.*)")
    vacuum_pattern = re.compile(r"##\s*🌫️ Vacuum")
    solvent_pattern = re.compile(r"##\s*💧 Solvent:.*")
    state_pattern = re.compile(
        r"Excited State\s*(\d+)[\s:|]*([0-9.]+)\s*\|\s*([0-9.]+)"
    )

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Match functional
            func_match = functional_pattern.match(line)
            if func_match:
                current_functional = func_match.group(1).strip()
                results[current_functional] = {"Vacuum": [], "Solvent": []}
                continue

            # Match environment (Vacuum or Solvent)
            if vacuum_pattern.match(line):
                current_env = "Vacuum"
                continue
            if solvent_pattern.match(line):
                current_env = "Solvent"
                continue

            # Match excited state lines
            state_match = state_pattern.search(line)
            if state_match and current_functional and current_env:
                state = int(state_match.group(1))
                energy = float(state_match.group(2))
                osc = float(state_match.group(3))
                results[current_functional][current_env].append(
                    {"state": state, "energy": energy, "osc_strength": osc}
                )

    return results


# Get states, energy and oscillator strength: PDI Monomer
pdi_monomer_data = parse_excited_states(file_path[0])
pdi_mon_wb97xd2_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in pdi_monomer_data["wB97xD2/cc-pVDZ"]["Vacuum"]
    ],
    dtype=float,
)

pdi_mon_wb97xd2_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in pdi_monomer_data["wB97xD2/cc-pVDZ"]["Solvent"]
    ],
    dtype=float,
)

pdi_mon_lc_wpbed3_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in pdi_monomer_data["LC-wPBE/cc-pVDZ@D3"]["Vacuum"]
    ],
    dtype=float,
)

pdi_mon_lc_wpbed3_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in pdi_monomer_data["LC-wPBE/cc-pVDZ@D3"]["Solvent"]
    ],
    dtype=float,
)

# Get states, energy and oscillator strength: TSM: Unattached Trimer
tsm_data = parse_excited_states(file_path[1])
tsm_wb97xd2_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tsm_data["wB97xD2/cc-pVDZ"]["Vacuum"]
    ],
    dtype=float,
)

tsm_wb97xd2_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tsm_data["wB97xD2/cc-pVDZ"]["Solvent"]
    ],
    dtype=float,
)

tsm_lc_wpbed3_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tsm_data["LC-wPBE/cc-pVDZ@D3"]["Vacuum"]
    ],
    dtype=float,
)

tsm_lc_wpbed3_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tsm_data["LC-wPBE/cc-pVDZ@D3"]["Solvent"]
    ],
    dtype=float,
)


# Get states, energy and oscillator strength: TTA: Sandwiched Trimer
tta_data = parse_excited_states(file_path[2])
tta_wb97xd2_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tta_data["wB97xD2/cc-pVDZ"]["Vacuum"]
    ],
    dtype=float,
)

tta_wb97xd2_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tta_data["wB97xD2/cc-pVDZ"]["Solvent"]
    ],
    dtype=float,
)

tta_lc_wpbed3_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tta_data["LC-wPBE/cc-pVDZ@D3"]["Vacuum"]
    ],
    dtype=float,
)

tta_lc_wpbed3_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in tta_data["LC-wPBE/cc-pVDZ@D3"]["Solvent"]
    ],
    dtype=float,
)

# Get states, energy and oscillator strength: TTL: Zigzaged Trimer
ttl_data = parse_excited_states(file_path[3])
ttl_wb97xd2_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in ttl_data["wB97xD2/cc-pVDZ"]["Vacuum"]
    ],
    dtype=float,
)

ttl_wb97xd2_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in ttl_data["wB97xD2/cc-pVDZ"]["Solvent"]
    ],
    dtype=float,
)

ttl_lc_wpbed3_vacuum_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in ttl_data["LC-wPBE/cc-pVDZ@D3"]["Vacuum"]
    ],
    dtype=float,
)

ttl_lc_wpbed3_solvent_exst_data = np.array(
    [
        [entry["state"], entry["energy"], entry["osc_strength"]]
        for entry in ttl_data["LC-wPBE/cc-pVDZ@D3"]["Solvent"]
    ],
    dtype=float,
)

legends_title = [
    "PDI-Free",
    "PDI-Sandwiched",
    "PDI-Zigzaged",
]  # monomer removed

wb97xd2_all_vacuum_data = [
    # pdi_mon_wb97xd2_vacuum_exst_data,
    tsm_wb97xd2_vacuum_exst_data,
    tta_wb97xd2_vacuum_exst_data,
    ttl_wb97xd2_vacuum_exst_data,
]
wb97xd2_all_solvent_data = [
    # pdi_mon_wb97xd2_solvent_exst_data,
    tsm_wb97xd2_solvent_exst_data,
    tta_wb97xd2_solvent_exst_data,
    ttl_wb97xd2_solvent_exst_data,
]


lcwpbe_all_vacuum_data = [
    # pdi_mon_lc_wpbed3_vacuum_exst_data,
    tsm_lc_wpbed3_vacuum_exst_data,
    tta_lc_wpbed3_vacuum_exst_data,
    ttl_lc_wpbed3_vacuum_exst_data,
]

lcwpbe_all_solvent_data = [
    # pdi_mon_lc_wpbed3_solvent_exst_data,
    tsm_lc_wpbed3_solvent_exst_data,
    tta_lc_wpbed3_solvent_exst_data,
    ttl_lc_wpbed3_solvent_exst_data,
]


def _plot_dataset_list(
    dataset_list: List[np.ndarray],
    title_suffix: str,
    legends: List[str],
    out_filename: str,
    output_dir: Path = OUTPUT_DIR,
    x_range: Tuple[float, float] = (0.5, 5.5),
    y_range: Tuple[float, float] = (2.2, 4.0),
    show_grid: bool = False,
) -> None:
    """
    Plot a list of datasets with production-ready styling.

    Each dataset is an (N,3) array: [state, energy, osc_strength].
    Marker size is scaled by oscillator strength. Apply small horizontal jitter
    per dataset to avoid marker overlap when energies are close between datasets.

    Only the first five excited states (state indices 1..5) are plotted; datasets are
    filtered accordingly and empty results are skipped.

    Parameters
    ----------
    dataset_list : List[np.ndarray]
        List of datasets to plot.
    title_suffix : str
        Suffix for plot title (e.g., "Vacuum" or "Solvent").
    legends : List[str]
        Legend labels for each dataset.
    out_filename : str
        Base filename for output (without extension).
    output_dir : Path
        Directory to save output files.
    x_range : Tuple[float, float]
        X-axis range (min, max).
    y_range : Tuple[float, float]
        Y-axis range (min, max).
    show_grid : bool
        Whether to show grid lines.
    """
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    plotted_any = False

    n_sets = len(dataset_list)
    base_jitter = 0.12
    mid = (n_sets - 1) / 2.0

    for idx, data in enumerate(dataset_list):
        if data is None or data.size == 0:
            continue

        x = data[:, 0]
        y = data[:, 1]
        osc = data[:, 2]

        # Filter to first five excited states (1..5)
        mask = (x >= 1) & (x <= 5)
        if not np.any(mask):
            continue
        x = x[mask]
        y = y[mask]
        osc = osc[mask]

        # Scale marker size from oscillator strength
        sizes = np.clip(osc * 100.0, 10, 300)

        # Horizontal jitter to separate overlapping points
        jitter = (idx - mid) * base_jitter
        x_jittered = x + jitter

        color = COLORBLIND_COLORS[idx % len(COLORBLIND_COLORS)]
        marker = MARKER_STYLES[idx % len(MARKER_STYLES)]
        label = legends[idx] if idx < len(legends) else f"Dataset {idx+1}"
        z = 3 + idx

        # Plot markers
        ax.scatter(
            x_jittered,
            y,
            s=sizes,
            label=label,
            color=color,
            marker=marker,
            alpha=MARKER_ALPHA,
            edgecolors="k",
            linewidths=MARKER_EDGE_WIDTH,
            zorder=z,
        )

        # Connect points with lines
        ax.plot(
            x_jittered,
            y,
            color=color,
            alpha=LINE_ALPHA,
            linewidth=LINE_WIDTH,
            zorder=z - 1,
        )
        plotted_any = True

    if not plotted_any:
        ax.text(
            0.5,
            0.5,
            "No data to plot",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=FONT_SIZE + 4,
            color="gray",
        )

    # Configure axes
    ax.set_xlim(*x_range)
    ax.set_xticks(np.arange(1, 6))
    ax.set_ylim(*y_range)
    ax.set_yticks(np.linspace(y_range[0], y_range[1], 5))

    # Labels
    ax.set_xlabel(r"$n^{\mathrm{th}}$ Excited State", fontweight="bold")
    ax.set_ylabel("Excitation Energy [eV]", fontweight="bold")

    # Grid
    if show_grid:
        ax.grid(True, linestyle=GRID_STYLE, alpha=GRID_ALPHA, zorder=0)

    # Legend
    if plotted_any:
        ax.legend(
            loc="best",
            frameon=True,
            shadow=LEGEND_SHADOW,
            fancybox=True,
        )

    # Tight layout
    fig.tight_layout()

    # Save in multiple formats
    output_dir.mkdir(parents=True, exist_ok=True)
    for fmt in OUTPUT_FORMATS:
        output_path = output_dir / f"{out_filename}.{fmt}"
        fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight", format=fmt)
        print(f"Saved: {output_path}")

    plt.close(fig)


def format_data_table(
    dataset_list: List[np.ndarray],
    legends: List[str],
    max_states: int = 5,
) -> List[Dict]:
    """
    Format datasets into a list of dictionaries for table generation.

    Parameters
    ----------
    dataset_list : List[np.ndarray]
        List of datasets, each (N,3) array: [state, energy, osc_strength].
    legends : List[str]
        Labels for each dataset.
    max_states : int
        Maximum number of excited states to include.

    Returns
    -------
    List[Dict]
        List of dictionaries with formatted data for each dataset.
    """
    formatted_data = []

    for idx, data in enumerate(dataset_list):
        if data is None or data.size == 0:
            continue

        label = legends[idx] if idx < len(legends) else f"Dataset {idx+1}"

        # Filter to first N excited states
        mask = (data[:, 0] >= 1) & (data[:, 0] <= max_states)
        filtered = data[mask]

        if filtered.size == 0:
            continue

        formatted_data.append(
            {
                "label": label,
                "data": filtered,
            }
        )

    return formatted_data


def write_latex_table(
    formatted_data: List[Dict],
    output_path: Path,
    caption: str,
    label: str,
) -> None:
    """
    Write excited state data to a LaTeX table file.

    Parameters
    ----------
    formatted_data : List[Dict]
        Formatted data from format_data_table().
    output_path : Path
        Output file path for LaTeX table.
    caption : str
        Table caption.
    label : str
        LaTeX label for referencing.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write(f"\\caption{{{caption}}}\n")
        f.write(f"\\label{{{label}}}\n")

        # Determine column format
        n_datasets = len(formatted_data)
        col_format = "c|" + "ccc|" * n_datasets
        f.write(f"\\begin{{tabular}}{{{col_format[:-1]}}}\n")
        f.write("\\hline\n")

        # Header row
        header = "State"
        for item in formatted_data:
            header += f" & \\multicolumn{{3}}{{c|}}{{{item['label']}}}"
        f.write(header + " \\\\\n")

        # Subheader row
        subheader = ""
        for _ in formatted_data:
            subheader += " & $E$ (eV) & $f$ & "
        f.write(subheader[:-2] + " \\\\\n")
        f.write("\\hline\n")

        # Data rows
        max_states = max(len(item["data"]) for item in formatted_data)
        for state_idx in range(max_states):
            row = f"{state_idx + 1}"
            for item in formatted_data:
                if state_idx < len(item["data"]):
                    energy = item["data"][state_idx, 1]
                    osc = item["data"][state_idx, 2]
                    row += f" & {energy:.2f} & {osc:.2f} &"
                else:
                    row += " & -- & -- &"
            f.write(row[:-1] + " \\\\\n")

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"Saved LaTeX table: {output_path}")


def write_markdown_table(
    formatted_data: List[Dict],
    output_path: Path,
    title: str,
) -> None:
    """
    Write excited state data to a Markdown table file.

    Parameters
    ----------
    formatted_data : List[Dict]
        Formatted data from format_data_table().
    output_path : Path
        Output file path for Markdown table.
    title : str
        Table title.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")

        # Header row
        header = "| State |"
        separator = "|-------|"
        for item in formatted_data:
            header += f" {item['label']} E (eV) | {item['label']} f |"
            separator += "---------------:|-------------:|"
        f.write(header + "\n")
        f.write(separator + "\n")

        # Data rows
        max_states = max(len(item["data"]) for item in formatted_data)
        for state_idx in range(max_states):
            row = f"| {state_idx + 1} |"
            for item in formatted_data:
                if state_idx < len(item["data"]):
                    energy = item["data"][state_idx, 1]
                    osc = item["data"][state_idx, 2]
                    row += f" {energy:.2f} | {osc:.2f} |"
                else:
                    row += " -- | -- |"
            f.write(row + "\n")

    print(f"Saved Markdown table: {output_path}")


if __name__ == "__main__":
    # Setup output directory
    output_dir = setup_output_directory()
    print(f"Output directory: {output_dir.absolute()}\n")

    # Create and save plots for the wB97xD2 datasets
    print("Generating wB97xD2 plots...")
    _plot_dataset_list(
        wb97xd2_all_vacuum_data[0:5],
        "Vacuum",
        legends_title,
        "wb97xd2_vacuum",
        output_dir=output_dir,
    )
    _plot_dataset_list(
        wb97xd2_all_solvent_data[0:5],
        "Solvent",
        legends_title,
        "wb97xd2_solvent",
        output_dir=output_dir,
    )

    # Create and save plots for the LC-wPBE@D3 datasets
    print("\nGenerating LC-wPBE@D3 plots...")
    _plot_dataset_list(
        lcwpbe_all_vacuum_data[0:5],
        "Vacuum",
        legends_title,
        "lcwpbe_vacuum",
        output_dir=output_dir,
    )
    _plot_dataset_list(
        lcwpbe_all_solvent_data[0:5],
        "Solvent",
        legends_title,
        "lcwpbe_solvent",
        output_dir=output_dir,
    )

    # Generate tables
    print("\nGenerating data tables...")

    # wB97xD2 vacuum tables
    formatted = format_data_table(wb97xd2_all_vacuum_data, legends_title)
    write_latex_table(
        formatted,
        output_dir / "wb97xd2_vacuum_table.tex",
        "Excited state data for wB97xD2/cc-pVDZ in vacuum",
        "tab:wb97xd2_vacuum",
    )
    write_markdown_table(
        formatted,
        output_dir / "wb97xd2_vacuum_table.md",
        "wB97xD2/cc-pVDZ Vacuum - Excited State Data",
    )

    # wB97xD2 solvent tables
    formatted = format_data_table(wb97xd2_all_solvent_data, legends_title)
    write_latex_table(
        formatted,
        output_dir / "wb97xd2_solvent_table.tex",
        "Excited state data for wB97xD2/cc-pVDZ in solvent",
        "tab:wb97xd2_solvent",
    )
    write_markdown_table(
        formatted,
        output_dir / "wb97xd2_solvent_table.md",
        "wB97xD2/cc-pVDZ Solvent - Excited State Data",
    )

    # LC-wPBE vacuum tables
    formatted = format_data_table(lcwpbe_all_vacuum_data, legends_title)
    write_latex_table(
        formatted,
        output_dir / "lcwpbe_vacuum_table.tex",
        "Excited state data for LC-wPBE/cc-pVDZ@D3 in vacuum",
        "tab:lcwpbe_vacuum",
    )
    write_markdown_table(
        formatted,
        output_dir / "lcwpbe_vacuum_table.md",
        "LC-wPBE/cc-pVDZ@D3 Vacuum - Excited State Data",
    )

    # LC-wPBE solvent tables
    formatted = format_data_table(lcwpbe_all_solvent_data, legends_title)
    write_latex_table(
        formatted,
        output_dir / "lcwpbe_solvent_table.tex",
        "Excited state data for LC-wPBE/cc-pVDZ@D3 in solvent",
        "tab:lcwpbe_solvent",
    )
    write_markdown_table(
        formatted,
        output_dir / "lcwpbe_solvent_table.md",
        "LC-wPBE/cc-pVDZ@D3 Solvent - Excited State Data",
    )

    print(f"\n✓ All plots and tables saved to: {output_dir.absolute()}")
