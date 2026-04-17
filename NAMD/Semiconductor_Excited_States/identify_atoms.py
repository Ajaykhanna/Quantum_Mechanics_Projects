#!/usr/bin/env python3
"""
Identify atom indices and infer molecular connectivity from a structure file.

The script is designed to be transferable across molecules instead of relying on
one hard-coded distance cutoff. It:

1. Loads the structure from any ASE-readable file when ASE is available.
2. Falls back to a plain XYZ parser when ASE is not installed.
3. Infers bonds from covalent radii with light valence constraints.
4. Prints atom, bond, angle, and dihedral suggestions using 0-based indices.
5. Saves a labeled 3D figure with labels offset away from atom centers.

Usage:
    python3 identify_atoms.py coords.xyz
    python3 identify_atoms.py coords.xyz --show
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import os
from pathlib import Path
import tempfile
from typing import Iterable

# Use a writable Matplotlib config directory for shared or sandboxed environments.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib.pyplot as plt
import numpy as np

try:
    from ase.data import atomic_numbers, covalent_radii
    from ase.io import read as ase_read

    HAS_ASE = True
except Exception:
    atomic_numbers = None
    covalent_radii = None
    ase_read = None
    HAS_ASE = False


FALLBACK_COVALENT_RADII = {
    "H": 0.31,
    "B": 0.85,
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "F": 0.57,
    "Si": 1.11,
    "P": 1.07,
    "S": 1.05,
    "Cl": 1.02,
    "Br": 1.20,
    "I": 1.39,
}

DEFAULT_MAX_VALENCE = {
    "H": 1,
    "B": 3,
    "C": 4,
    "N": 3,
    "O": 2,
    "F": 1,
    "Si": 4,
    "P": 5,
    "S": 6,
    "Cl": 1,
    "Br": 1,
    "I": 1,
}

ELEMENT_COLORS = {
    "H": "#f4f4f4",
    "B": "#f5b041",
    "C": "#6e6e6e",
    "N": "#3776ff",
    "O": "#ff3b30",
    "F": "#7ed957",
    "Si": "#c49a6c",
    "P": "#ff8c00",
    "S": "#ffd60a",
    "Cl": "#34c759",
    "Br": "#8b4513",
    "I": "#6a0dad",
}

ELEMENT_SIZES = {
    "H": 110,
    "B": 170,
    "C": 220,
    "N": 210,
    "O": 210,
    "F": 190,
    "Si": 240,
    "P": 230,
    "S": 230,
    "Cl": 220,
    "Br": 230,
    "I": 250,
}


@dataclass(frozen=True)
class Structure:
    name: str
    symbols: list[str]
    positions: np.ndarray
    formula: str

    @property
    def n_atoms(self) -> int:
        return len(self.symbols)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Label atom indices, infer bonds from covalent radii, and print "
            "suggested bonds/angles/dihedrals for a molecular structure."
        )
    )
    parser.add_argument("structure_file", type=Path, help="Path to the structure file.")
    parser.add_argument(
        "--bond-scale",
        type=float,
        default=1.20,
        help="Scale factor applied to summed covalent radii when inferring bonds.",
    )
    parser.add_argument(
        "--bond-padding",
        type=float,
        default=0.10,
        help="Absolute padding in Angstrom added to the bond cutoff.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the plot interactively after saving it.",
    )
    return parser.parse_args()


def parse_xyz(path: Path) -> Structure:
    with path.open("r", encoding="utf-8") as handle:
        lines = [line.rstrip() for line in handle if line.strip()]

    if len(lines) < 2:
        raise ValueError(f"{path} is not a valid XYZ file.")

    try:
        n_atoms = int(lines[0].split()[0])
    except ValueError as exc:
        raise ValueError(f"First line of {path} must contain the atom count.") from exc

    atom_lines = lines[2 : 2 + n_atoms]
    if len(atom_lines) != n_atoms:
        raise ValueError(
            f"Expected {n_atoms} atom lines in {path}, found {len(atom_lines)}."
        )

    symbols: list[str] = []
    positions: list[list[float]] = []
    for idx, line in enumerate(atom_lines):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"Malformed XYZ atom line {idx + 3} in {path}: {line!r}")
        symbols.append(parts[0])
        positions.append([float(parts[1]), float(parts[2]), float(parts[3])])

    return Structure(
        name=path.stem,
        symbols=symbols,
        positions=np.asarray(positions, dtype=float),
        formula=hill_formula(symbols),
    )


def load_structure(path: Path) -> Structure:
    if not path.exists():
        raise FileNotFoundError(f"Structure file not found: {path}")

    if HAS_ASE:
        atoms = ase_read(path)
        return Structure(
            name=path.stem,
            symbols=list(atoms.get_chemical_symbols()),
            positions=np.asarray(atoms.get_positions(), dtype=float),
            formula=atoms.get_chemical_formula(),
        )

    if path.suffix.lower() != ".xyz":
        raise RuntimeError(
            "ASE is not installed, so only XYZ files can be read in this environment."
        )
    return parse_xyz(path)


def hill_formula(symbols: Iterable[str]) -> str:
    counts = Counter(symbols)
    order: list[str] = []
    if "C" in counts:
        order.append("C")
    if "H" in counts:
        order.append("H")
    order.extend(sorted(symbol for symbol in counts if symbol not in {"C", "H"}))

    parts = []
    for symbol in order:
        count = counts[symbol]
        parts.append(symbol if count == 1 else f"{symbol}{count}")
    return "".join(parts)


def covalent_radius(symbol: str) -> float:
    if HAS_ASE and symbol in atomic_numbers:
        radius = float(covalent_radii[atomic_numbers[symbol]])
        if radius > 0:
            return radius
    if symbol in FALLBACK_COVALENT_RADII:
        return FALLBACK_COVALENT_RADII[symbol]
    raise KeyError(
        f"No covalent radius available for element {symbol!r}. "
        "Install ASE or extend FALLBACK_COVALENT_RADII."
    )


def interatomic_distance(positions: np.ndarray, i: int, j: int) -> float:
    return float(np.linalg.norm(positions[i] - positions[j]))


def can_add_bond(symbols: list[str], degrees: list[int], i: int, j: int) -> bool:
    limit_i = DEFAULT_MAX_VALENCE.get(symbols[i])
    limit_j = DEFAULT_MAX_VALENCE.get(symbols[j])
    if limit_i is not None and degrees[i] >= limit_i:
        return False
    if limit_j is not None and degrees[j] >= limit_j:
        return False
    return True


def infer_bonds(
    structure: Structure,
    bond_scale: float,
    bond_padding: float,
) -> list[tuple[int, int, float]]:
    candidates: list[tuple[float, float, int, int]] = []
    symbols = structure.symbols
    positions = structure.positions

    for i in range(structure.n_atoms):
        for j in range(i + 1, structure.n_atoms):
            r_sum = covalent_radius(symbols[i]) + covalent_radius(symbols[j])
            cutoff = bond_scale * r_sum + bond_padding
            dist = interatomic_distance(positions, i, j)
            if dist <= cutoff:
                normalized = dist / max(r_sum, 1.0e-8)
                is_hh = int(symbols[i] == "H" and symbols[j] == "H")
                candidates.append((is_hh, normalized, i, j))

    degrees = [0] * structure.n_atoms
    bonds: list[tuple[int, int, float]] = []
    seen_pairs: set[tuple[int, int]] = set()

    def add_bond(i: int, j: int) -> None:
        pair = (min(i, j), max(i, j))
        if pair in seen_pairs:
            return
        seen_pairs.add(pair)
        degrees[i] += 1
        degrees[j] += 1
        bonds.append(
            (pair[0], pair[1], interatomic_distance(positions, pair[0], pair[1]))
        )

    hydrogen_indices = [idx for idx, symbol in enumerate(symbols) if symbol == "H"]
    for h_idx in hydrogen_indices:
        options: list[tuple[int, float, int, int]] = []
        for is_hh, normalized, i, j in candidates:
            if h_idx not in {i, j}:
                continue
            other = j if i == h_idx else i
            prefer_hydrogen_neighbor = int(symbols[other] == "H")
            options.append((prefer_hydrogen_neighbor, normalized, min(i, j), max(i, j)))

        for _, _, i, j in sorted(options):
            if can_add_bond(symbols, degrees, i, j):
                add_bond(i, j)
                break

    for _, _, i, j in sorted(candidates):
        if (i, j) in seen_pairs:
            continue
        if can_add_bond(symbols, degrees, i, j):
            add_bond(i, j)

    bonds.sort(key=lambda item: (item[0], item[1]))
    return bonds


def build_adjacency(
    n_atoms: int, bonds: list[tuple[int, int, float]]
) -> dict[int, list[int]]:
    adjacency: dict[int, list[int]] = {idx: [] for idx in range(n_atoms)}
    for i, j, _ in bonds:
        adjacency[i].append(j)
        adjacency[j].append(i)
    for idx in adjacency:
        adjacency[idx].sort()
    return adjacency


def bond_type_key(symbol_a: str, symbol_b: str) -> str:
    pair = tuple(sorted((symbol_a, symbol_b)))
    return f"{pair[0]}-{pair[1]}"


def compute_angle(positions: np.ndarray, i: int, j: int, k: int) -> float:
    vec1 = positions[i] - positions[j]
    vec2 = positions[k] - positions[j]
    denom = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if denom == 0:
        return float("nan")
    cos_theta = np.dot(vec1, vec2) / denom
    cos_theta = float(np.clip(cos_theta, -1.0, 1.0))
    return float(np.degrees(np.arccos(cos_theta)))


def compute_dihedral(positions: np.ndarray, i: int, j: int, k: int, l: int) -> float:
    b0 = positions[j] - positions[i]
    b1 = positions[k] - positions[j]
    b2 = positions[l] - positions[k]

    b1_norm = np.linalg.norm(b1)
    if b1_norm == 0:
        return float("nan")
    b1_unit = b1 / b1_norm

    v = b0 - np.dot(b0, b1_unit) * b1_unit
    w = b2 - np.dot(b2, b1_unit) * b1_unit

    x = np.dot(v, w)
    y = np.dot(np.cross(b1_unit, v), w)
    return float(np.degrees(np.arctan2(y, x)))


def enumerate_angles(
    structure: Structure, adjacency: dict[int, list[int]]
) -> list[tuple[int, int, int, float]]:
    angles: list[tuple[int, int, int, float]] = []
    for center, neighbors in adjacency.items():
        if len(neighbors) < 2:
            continue
        for left, right in combinations(neighbors, 2):
            angle = compute_angle(structure.positions, left, center, right)
            angles.append((left, center, right, angle))
    angles.sort(key=lambda item: item[:3])
    return angles


def enumerate_dihedrals(
    structure: Structure, adjacency: dict[int, list[int]]
) -> list[tuple[int, int, int, int, float]]:
    seen: set[tuple[int, int, int, int]] = set()
    dihedrals: list[tuple[int, int, int, int, float]] = []

    for j in range(structure.n_atoms):
        for k in adjacency[j]:
            if j >= k:
                continue
            left_neighbors = [i for i in adjacency[j] if i != k]
            right_neighbors = [l for l in adjacency[k] if l != j]
            for i in left_neighbors:
                for l in right_neighbors:
                    if len({i, j, k, l}) < 4:
                        continue
                    forward = (i, j, k, l)
                    reverse = (l, k, j, i)
                    key = min(forward, reverse)
                    if key in seen:
                        continue
                    seen.add(key)
                    torsion = compute_dihedral(structure.positions, *key)
                    dihedrals.append((*key, torsion))

    dihedrals.sort(key=lambda item: item[:4])
    return dihedrals


def select_important_angles(
    structure: Structure, angles: list[tuple[int, int, int, float]]
) -> list[tuple[int, int, int, float]]:
    heavy_only = [
        angle
        for angle in angles
        if all(structure.symbols[idx] != "H" for idx in angle[:3])
    ]
    if heavy_only:
        return heavy_only

    center_not_h = [angle for angle in angles if structure.symbols[angle[1]] != "H"]
    return center_not_h or angles


def select_important_dihedrals(
    structure: Structure, dihedrals: list[tuple[int, int, int, int, float]]
) -> list[tuple[int, int, int, int, float]]:
    heavy_only = [
        dihedral
        for dihedral in dihedrals
        if all(structure.symbols[idx] != "H" for idx in dihedral[:4])
    ]
    if heavy_only:
        return heavy_only

    central_heavy = [
        dihedral
        for dihedral in dihedrals
        if structure.symbols[dihedral[1]] != "H"
        and structure.symbols[dihedral[2]] != "H"
    ]
    return central_heavy or dihedrals


def print_structure_info(structure: Structure, adjacency: dict[int, list[int]]) -> None:
    print("\n" + "=" * 70)
    print(f"{structure.name} Structure Information")
    print("=" * 70)
    print(f"Formula: {structure.formula}")
    print(f"Number of atoms: {structure.n_atoms}")

    print("\nAtom Listing:")
    print("-" * 70)
    print(f"{'Index':<7} {'Element':<10} {'Position (Å)':<30}")
    print("-" * 70)
    for idx, (symbol, pos) in enumerate(zip(structure.symbols, structure.positions)):
        print(f"{idx:<7} {symbol:<10} ({pos[0]:7.3f}, {pos[1]:7.3f}, {pos[2]:7.3f})")

    print("\nInferred Connectivity:")
    print("-" * 70)
    print(f"{'Index':<7} {'Element':<10} {'Neighbors (0-indexed)':<30}")
    print("-" * 70)
    for idx, symbol in enumerate(structure.symbols):
        neighbors = ", ".join(str(neighbor) for neighbor in adjacency[idx]) or "-"
        print(f"{idx:<7} {symbol:<10} {neighbors:<30}")
    print("=" * 70)


def print_bond_report(
    structure: Structure, bonds: list[tuple[int, int, float]]
) -> None:
    print("\n" + "=" * 70)
    print("Suggested Important Bonds")
    print("=" * 70)

    grouped: dict[str, list[tuple[int, int, float]]] = defaultdict(list)
    for i, j, dist in bonds:
        grouped[bond_type_key(structure.symbols[i], structure.symbols[j])].append(
            (i, j, dist)
        )

    for bond_type in sorted(grouped):
        print(f"\n{bond_type} bonds:")
        for i, j, dist in grouped[bond_type]:
            print(
                f"  ({i}, {j}): {structure.symbols[i]}-{structure.symbols[j]} = {dist:.3f} Å"
            )
    print("=" * 70)


def print_angle_report(
    structure: Structure,
    important_angles: list[tuple[int, int, int, float]],
) -> None:
    print("\n" + "=" * 70)
    print("Suggested Important Angles")
    print("=" * 70)
    if not important_angles:
        print("\nNo angles were identified from the inferred bond graph.")
        print("=" * 70)
        return

    for i, j, k, angle in important_angles:
        print(
            f"  ({i}, {j}, {k}): "
            f"{structure.symbols[i]}-{structure.symbols[j]}-{structure.symbols[k]} = "
            f"{angle:.2f}°"
        )
    print("=" * 70)


def print_dihedral_report(
    structure: Structure,
    important_dihedrals: list[tuple[int, int, int, int, float]],
) -> None:
    print("\n" + "=" * 70)
    print("Suggested Important Dihedrals")
    print("=" * 70)
    if not important_dihedrals:
        print("\nNo dihedrals were identified from the inferred bond graph.")
        print("=" * 70)
        return

    for i, j, k, l, torsion in important_dihedrals:
        print(
            f"  ({i}, {j}, {k}, {l}): "
            f"{structure.symbols[i]}-{structure.symbols[j]}-"
            f"{structure.symbols[k]}-{structure.symbols[l]} = "
            f"{torsion:.2f}°"
        )
    print("=" * 70)


def generate_comparison_code(
    structure: Structure,
    bonds: list[tuple[int, int, float]],
    important_angles: list[tuple[int, int, int, float]],
    important_dihedrals: list[tuple[int, int, int, int, float]],
) -> None:
    print("\n" + "=" * 70)
    print("Generated Code for compare_nexmd_hippynn.py")
    print("=" * 70)
    print(
        """
# Copy the following into your compare_nexmd_hippynn.py script
# and adjust further if you want a smaller, chemistry-specific subset.

# Important bonds (0-indexed)
# Format: (atom_i, atom_j)
important_bonds = ["""
    )
    for i, j, dist in bonds:
        print(
            f"    ({i}, {j}),  # {structure.symbols[i]}-{structure.symbols[j]} ({dist:.3f} Å)"
        )
    print("]")

    print("\n# Important angles (0-indexed)")
    print("# Format: (atom_i, atom_j, atom_k) - angle at atom_j")
    print("important_angles = [")
    for i, j, k, angle in important_angles:
        print(
            f"    ({i}, {j}, {k}),  # "
            f"{structure.symbols[i]}-{structure.symbols[j]}-{structure.symbols[k]} "
            f"({angle:.2f} deg)"
        )
    print("]")

    print("\n# Important dihedrals (0-indexed)")
    print("# Format: (atom_i, atom_j, atom_k, atom_l)")
    print("important_dihedrals = [")
    for i, j, k, l, torsion in important_dihedrals:
        print(
            f"    ({i}, {j}, {k}, {l}),  # "
            f"{structure.symbols[i]}-{structure.symbols[j]}-"
            f"{structure.symbols[k]}-{structure.symbols[l]} "
            f"({torsion:.2f} deg)"
        )
    print("]")
    print("=" * 70)


def set_equal_axes(ax, positions: np.ndarray) -> None:
    mins = positions.min(axis=0)
    maxs = positions.max(axis=0)
    centers = 0.5 * (mins + maxs)
    radius = 0.5 * max(maxs - mins)
    radius = max(radius, 1.0)

    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)
    if hasattr(ax, "set_box_aspect"):
        ax.set_box_aspect((1.0, 1.0, 1.0))


def plot_structure_with_labels(
    structure: Structure, bonds: list[tuple[int, int, float]]
) -> plt.Figure:
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="3d")

    positions = structure.positions
    center = positions.mean(axis=0)
    spread = np.ptp(positions, axis=0)
    label_offset = max(float(spread.max()) * 0.04, 0.12)

    for i, j, _ in bonds:
        ax.plot(
            [positions[i, 0], positions[j, 0]],
            [positions[i, 1], positions[j, 1]],
            [positions[i, 2], positions[j, 2]],
            color="#7f7f7f",
            alpha=0.45,
            linewidth=1.5,
        )

    for idx, (symbol, pos) in enumerate(zip(structure.symbols, positions)):
        ax.scatter(
            pos[0],
            pos[1],
            pos[2],
            c=ELEMENT_COLORS.get(symbol, "#b565d9"),
            s=ELEMENT_SIZES.get(symbol, 150),
            edgecolors="black",
            linewidths=1.2,
            alpha=0.9,
        )

        direction = pos - center
        norm = np.linalg.norm(direction)
        if norm < 1.0e-8:
            direction = np.array([1.0, 1.0, 1.0])
            norm = np.linalg.norm(direction)
        label_pos = pos + (direction / norm) * label_offset
        ax.text(
            label_pos[0],
            label_pos[1],
            label_pos[2],
            str(idx),
            fontsize=11,
            fontweight="bold",
            color="black",
        )

    ax.set_xlabel("X (Å)")
    ax.set_ylabel("Y (Å)")
    ax.set_zlabel("Z (Å)")
    ax.set_title(
        f"{structure.name} Structure (with atom indices)",
        fontsize=14,
        fontweight="bold",
    )
    ax.view_init(elev=22, azim=-58)
    set_equal_axes(ax, positions)

    legend_elements = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=ELEMENT_COLORS.get(symbol, "#b565d9"),
            markeredgecolor="black",
            markersize=9,
            label=symbol,
        )
        for symbol in sorted(set(structure.symbols))
    ]
    ax.legend(handles=legend_elements, loc="upper right")
    plt.tight_layout()
    return fig


def main() -> None:
    args = parse_args()
    structure = load_structure(args.structure_file)

    bonds = infer_bonds(
        structure=structure,
        bond_scale=float(args.bond_scale),
        bond_padding=float(args.bond_padding),
    )
    adjacency = build_adjacency(structure.n_atoms, bonds)
    all_angles = enumerate_angles(structure, adjacency)
    all_dihedrals = enumerate_dihedrals(structure, adjacency)
    important_angles = select_important_angles(structure, all_angles)
    important_dihedrals = select_important_dihedrals(structure, all_dihedrals)

    print_structure_info(structure, adjacency)
    print_bond_report(structure, bonds)
    print_angle_report(structure, important_angles)
    print_dihedral_report(structure, important_dihedrals)
    generate_comparison_code(structure, bonds, important_angles, important_dihedrals)

    fig = plot_structure_with_labels(structure, bonds)
    output_file = args.structure_file.with_name(
        f"{args.structure_file.stem}_labeled.png"
    )
    plt.savefig(output_file, dpi=180, bbox_inches="tight")
    print(f"\n✓ Structure visualization saved to: {output_file}")

    if args.show:
        plt.show()
    else:
        plt.close(fig)

    print(
        "\n✓ Done! Use the labeled structure plus inferred connectivity to choose indices."
    )


if __name__ == "__main__":
    main()
