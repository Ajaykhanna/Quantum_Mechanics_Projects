#!/usr/bin/env python3
"""
NEXMD Output Analyzer
---------------------
Parses a directory containing output files from a NEXMD single-point
electronic structure calculation (semi-empirical). It prints requested
information about shape, dimensions, rows, columns, and units, linking
them to the underlying total atoms and electronic states where possible.

Usage:
    python nexmd_analyzer.py --dir /path/to/outputs --output analysis.txt

Developer Information:
    __author__ = "Ajay Khanna"
    __place__ = "LANL"
    __date__ = "May.17.2026"
"""

import os
import sys
import argparse
import logging

# Configure logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_actual_shape(filepath):
    """
    Reads a file to determine the actual (rows, columns) shape.
    Skips comment lines (starting with # or !) and empty lines.

    Args:
        filepath (str): Path to the file.

    Returns:
        tuple: (rows, cols) as integers. Returns (0, 0) if empty.
    """
    try:
        with open(filepath, "r") as f:
            lines = [
                line.strip()
                for line in f
                if line.strip()
                and not line.startswith("#")
                and not line.startswith("!")
            ]

        if not lines:
            return 0, 0

        rows = len(lines)
        # We assume the file is a uniform matrix; probe the first valid line
        cols = len(lines[0].split())
        return rows, cols
    except Exception as e:
        logging.error(f"Error reading file {filepath}: {e}")
        return "Error", "Error"


def get_n_orbs(elements, theory):
    """
    Estimates the total number of atomic orbitals in the semi-empirical basis set.
    Standard sp basis is 4 orbitals per heavy atom (C, N, O). Hydrogen is 1.
    Some theories (PM6, AM1/d) use d-orbitals (9) for heavier elements (Si, P, S, Cl, Br, I).
    """
    theory = theory.upper()
    d_elements = {"SI", "P", "S", "CL", "BR", "I"}
    n_orbs = 0
    for el in elements:
        el = el.strip().upper()
        # Remove any digits attached to element names
        el = "".join([c for c in el if not c.isdigit()])
        if el == "H":
            n_orbs += 1
        elif el in d_elements and theory in ["PM6", "AM1/D", "MNDO/D", "PM7"]:
            n_orbs += 9
        else:
            n_orbs += 4
    return n_orbs


def get_file_metadata():
    """
    Returns the metadata dictionary mapping filenames to their expected
    units, dimensions, symmetry, and relation to atoms/states.

    Returns:
        dict: Metainformation for parsing.
    """
    return {
        "input.ceon": {
            "desc": "NEXMD configuration parameters",
            "units": "N/A",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "User configuration",
        },
        "coords.xyz": {
            "desc": "Atomic coordinates (XYZ Format)",
            "units": "Angstrom",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (
                na + 2 if na else "N_atoms+2",
                4,
            ),
            "dependent_on": "N_atoms",
        },
        "velocity.out": {
            "desc": "Atomic velocities",
            "units": "Angstrom/fs",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (na if na else "N_atoms", 3),
            "dependent_on": "N_atoms",
        },
        "energy-ev.out": {
            "desc": "Energies (Kinetic, Potential, Total, etc)",
            "units": "eV",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (
                1,
                ns + 4 if ns else "N_states+4",
            ),
            "dependent_on": "N_states",
        },
        "pes.out": {
            "desc": "Potential Energy Surfaces",
            "units": "eV",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (
                1,
                ns + 1 if ns else "N_states+1",
            ),
            "dependent_on": "N_states",
        },
        "coefficient.out": {
            "desc": "Complex quantum amplitudes (C_i)",
            "units": "Unitless",
            "symmetry": "Hermitian (Density Matrix via C_i)",
            "expected_shape": lambda na, ns, no, ptdm: (
                1,
                2 * ns + 1 if ns else "2*N_states+1",
            ),
            "dependent_on": "N_states",
        },
        "coeff-n.out": {
            "desc": "Classical state populations",
            "units": "Unitless",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (
                1,
                ns + 1 if ns else "N_states+1",
            ),
            "dependent_on": "N_states",
        },
        "coeff-q.out": {
            "desc": "Quantum state populations",
            "units": "Unitless",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (
                1,
                ns + 1 if ns else "N_states+1",
            ),
            "dependent_on": "N_states",
        },
        "gradients.out": {
            "desc": "Energy gradients of the active state",
            "units": "eV/Angstrom",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (na if na else "N_atoms", 3),
            "dependent_on": "N_atoms",
        },
        "nact.out": {
            "desc": "Time-derivative non-adiabatic couplings",
            "units": "eV / hbar",
            "symmetry": "Anti-symmetric (d_ij = -d_ji)",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "N_states (Pairs)",
        },
        "nacr.out": {
            "desc": "Spatial non-adiabatic coupling vectors",
            "units": "1/Angstrom",
            "symmetry": "Anti-symmetric (d_ij = -d_ji)",
            "expected_shape": lambda na, ns, no, ptdm: (na if na else "N_atoms", 3),
            "dependent_on": "N_atoms",
        },
        "tdipole.out": {
            "desc": "Transition dipole moments",
            "units": "e*Bohr / Debye",
            "symmetry": "Symmetric (u_ij = u_ji)",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", 7),
            "dependent_on": "N_states (Pairs)",
        },
        "temperature.out": {
            "desc": "System temperature",
            "units": "K",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (1, 2),
            "dependent_on": "Time",
        },
        "cm.out": {
            "desc": "Connection Matrix / Decoherence tracking",
            "units": "Unitless",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "N_states",
        },
        "order.out": {
            "desc": "State ordering (Trivial crossing tracking)",
            "units": "State Index",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: (1, ns if ns else "N_states"),
            "dependent_on": "N_states",
        },
        "cross-steps.out": {
            "desc": "Records of trivial crossings",
            "units": "N/A",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "Trajectory Events",
        },
        "hops.out": {
            "desc": "Successful surface hops",
            "units": "N/A",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "Trajectory Events",
        },
        "hops-trial.out": {
            "desc": "Attempted (trial) surface hops",
            "units": "N/A",
            "symmetry": "None",
            "expected_shape": lambda na, ns, no, ptdm: ("varies", "varies"),
            "dependent_on": "Trajectory Events",
        },
        "transition-densities.out": {
            "desc": "Transition densities matrix",
            "units": "e",
            "symmetry": "Symmetric (P_ij = P_ji)",
            "expected_shape": lambda na, ns, no, ptdm: (
                "varies",
                no if ptdm == 0 else (no * no if no else "N_orbs^2"),
            ),
            "dependent_on": "Semi-Empirical Basis Set Orbs",
        },
    }


def print_and_save_table(data, headers, output_file=None):
    """
    Formats the parsed data into a neat table, prints to stdout,
    and optionally saves to a designated file.
    """
    if not data:
        logging.warning("No data provided to format.")
        return

    # Evaluate max width for each column to align perfectly
    col_widths = [len(h) for h in headers]
    for row in data:
        for i, item in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(item)))

    # Add a slight padding buffer
    col_widths = [w + 2 for w in col_widths]

    fmt = "|".join([f" {{:<{w}}} " for w in col_widths])
    separator = "+".join(["-" * (w + 2) for w in col_widths])

    table_lines = [fmt.format(*headers), separator]
    for row in data:
        table_lines.append(fmt.format(*[str(item) for item in row]))

    final_output = "\n".join(table_lines)
    print("\n" + final_output + "\n")

    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(final_output + "\n")
            logging.info(f"Table successfully saved to {output_file}")
        except Exception as e:
            logging.error(f"Failed to save output to {output_file}: {e}")


def parse_numerical_blocks(filepath):
    """Reads a file and yields continuous blocks of purely numerical data, skipping text."""
    blocks = []
    current_block = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                try:
                    vals = [float(p) for p in parts]
                    current_block.append(vals)
                except ValueError:
                    # Non-numerical line hit (e.g. headers, separators)
                    if current_block:
                        blocks.append(current_block)
                        current_block = []
        if current_block:
            blocks.append(current_block)
    except Exception as e:
        logging.error(f"Error parsing numerical blocks from {filepath}: {e}")
    return blocks


def save_block(filepath, block, header):
    """Saves a 2D numerical block to a file safely for numpy loading."""
    try:
        with open(filepath, "w") as f:
            f.write(f"# {header}\n")
            f.write("# Format: Space-separated floats (NumPy compatible)\n")
            for row in block:
                f.write(" ".join(f"{val:16.8e}" for val in row) + "\n")
    except Exception as e:
        logging.error(f"Error writing to {filepath}: {e}")


def print_numpy_instructions(extract_dir, extracted_files):
    """Prints an auto-generated Python script for loading the extracted data."""
    if not extracted_files:
        return

    print("\n" + "=" * 70)
    print(" NUMPY EXTRACTION SUCCESS - LOADING INSTRUCTIONS")
    print("=" * 70)
    print(f"Data cleanly extracted to: {extract_dir}/\n")
    print("You can easily load these files in Python using NumPy:")
    print("----------------------------------------------------------------------")
    print("import numpy as np")
    print("import os\n")
    print(f"data_dir = '{extract_dir}'\n")

    for fname, dtype in extracted_files:
        var_name = fname.replace(".txt", "").replace("-", "_")
        print(f"# Load {dtype}")
        print(f"{var_name} = np.loadtxt(os.path.join(data_dir, '{fname}'))")

    print("\n# Note: Single-point calculations return single frames.")
    print(
        "# 'Stacked' tensors (like forces) are natively saved as (N_atoms, 3) 2D arrays."
    )
    print("======================================================================\n")


def perform_extraction(target_dir, args):
    """Handles parsing and saving of requested files into NumPy-ready text files."""
    extract_map = {
        "E": "pes.out",
        "energies": "pes.out",
        "f": "gradients.out",
        "forces": "gradients.out",
        "nacrs": "nacr.out",
        "nacts": "nact.out",
        "tdipoles": "tdipole.out",
        "transition-densities": "transition-densities.out",
        "transition-densities.out": "transition-densities.out",
    }

    targets = set()
    for ex in args.extract:
        # Strip potential user dash-prefixes like --energies
        ex_clean = ex.lstrip("-").lower()
        if ex_clean == "all":
            targets = set(extract_map.values())
            break
        elif ex_clean in extract_map:
            targets.add(extract_map[ex_clean])
        else:
            logging.warning(f"Unknown extract option ignored: {ex}")

    if not targets:
        logging.info("No valid files to extract.")
        return

    os.makedirs(args.extract_dir, exist_ok=True)
    logging.info(f"Extracting numerical data to directory: {args.extract_dir}")

    extracted_files = []

    for filename in targets:
        filepath = os.path.join(target_dir, filename)
        if not os.path.exists(filepath):
            logging.warning(f"Cannot extract {filename}, file not found.")
            continue

        blocks = parse_numerical_blocks(filepath)
        if not blocks:
            logging.warning(f"No numerical data found in {filename}.")
            continue

        base_name = filename.replace(".out", "")

        # Handle Transition Density matrices pairwise separation if requested
        if filename == "transition-densities.out" and args.extract_pair_tdmats:
            # Flatten blocks since single point outputs are continuous rows
            all_rows = []
            for b in blocks:
                all_rows.extend(b)

            # Each row represents a state transition from Ground (S0) to Excited State S(i+1)
            for i, row in enumerate(all_rows):
                out_name = f"TDMat_00_{i+1:02d}.txt"
                out_path = os.path.join(args.extract_dir, out_name)
                # save_block expects a 2D array, so we wrap the row in a list
                save_block(
                    out_path,
                    [row],
                    f"Extracted from {filename}, Transition S0 -> S{i+1}",
                )
                extracted_files.append((out_name, "TDM Vector/Flattened Matrix"))
        else:
            # Flatten/Stack blocks for unified 2D numpy format (Option B)
            stacked_data = []
            for b in blocks:
                stacked_data.extend(b)

            out_name = f"extracted_{base_name}.txt"
            out_path = os.path.join(args.extract_dir, out_name)
            save_block(
                out_path, stacked_data, f"Extracted stacked data from {filename}"
            )

            shape_type = (
                "Matrix / Stacked Tensor"
                if len(stacked_data) > 1
                else "Vector / Scalar"
            )
            extracted_files.append((out_name, shape_type))

    print_numpy_instructions(args.extract_dir, extracted_files)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze NEXMD single point outputs, correlating shapes/units to atoms and states."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=".",
        help="Directory containing the output files (default: current dir)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional: filepath to save the tabulated output.",
    )
    parser.add_argument(
        "--theory",
        type=str,
        default="AM1",
        help="Level of theory used (e.g., AM1, PM3, PM6). Determines atomic orbitals. (default: AM1)",
    )
    parser.add_argument(
        "--printTDM",
        type=int,
        choices=[0, 1],
        default=0,
        help="printTDM flag used in simulation. 0 = diagonals only, 1 = full matrix. (default: 0)",
    )
    parser.add_argument(
        "--extract",
        nargs="+",
        default=[],
        help="Quantities to extract into NumPy ready text files. Options: all, E, energies, f, forces, nacrs, nacts, tdipoles, transition-densities",
    )
    parser.add_argument(
        "--extract_dir",
        type=str,
        default="extracted_data",
        help="Directory to save extracted text files. (default: extracted_data)",
    )
    parser.add_argument(
        "--extract_pair_tdmats",
        action="store_true",
        help="Extract each transition density matrix pair to a separate file (e.g. TDMat_00_01.txt)",
    )
    args = parser.parse_args()

    target_dir = args.dir
    if not os.path.isdir(target_dir):
        logging.error(f"Provided directory '{target_dir}' does not exist.")
        sys.exit(1)

    logging.info(f"Scanning directory: {target_dir}")
    logging.info(f"Using Theory: {args.theory.upper()} | printTDM: {args.printTDM}")

    # Step 1: Attempt to dynamically identify N_atoms and N_states to link dimensions
    n_atoms = None
    n_states = None
    n_orbs = None
    elements = []

    coords_path = os.path.join(target_dir, "coords.xyz")
    if os.path.exists(coords_path):
        try:
            with open(coords_path, "r") as f:
                first_line = f.readline().strip()
                n_atoms = int(first_line)
                logging.info(
                    f"Deduced Total Atoms (N_atoms) = {n_atoms} from coords.xyz"
                )
                # Skip comment line
                f.readline()
                # Read elements
                for _ in range(n_atoms):
                    parts = f.readline().split()
                    if parts:
                        elements.append(parts[0])
            n_orbs = get_n_orbs(elements, args.theory)
            logging.info(
                f"Deduced Total Basis Orbitals (N_orbs) = {n_orbs} based on {args.theory.upper()}"
            )
        except Exception as e:
            logging.warning(
                f"Found coords.xyz but failed to extract N_atoms or elements: {e}"
            )

    pes_path = os.path.join(target_dir, "pes.out")
    if os.path.exists(pes_path):
        try:
            with open(pes_path, "r") as f:
                # Find the first data line (non comment)
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        # Column 1 is Time, rest are Electronic States
                        n_states = len(line.split()) - 1
                        logging.info(
                            f"Deduced Total States (N_states) = {n_states} from pes.out"
                        )
                        break
        except Exception as e:
            logging.warning(f"Found pes.out but failed to extract N_states: {e}")

    # Step 2: Iterate over tracked files and build the table
    file_meta = get_file_metadata()
    table_headers = [
        "Filename",
        "Status",
        "Actual Shape",
        "Expected Shape",
        "Symmetry",
        "Dependent Variables",
        "Units",
        "Description",
    ]
    table_data = []

    for filename, meta in file_meta.items():
        filepath = os.path.join(target_dir, filename)

        status = "Found" if os.path.exists(filepath) else "Missing"

        if status == "Found":
            act_r, act_c = get_actual_shape(filepath)
            actual_shape_str = f"({act_r}, {act_c})"
        else:
            actual_shape_str = "(N/A)"

        exp_r, exp_c = meta["expected_shape"](n_atoms, n_states, n_orbs, args.printTDM)
        expected_shape_str = f"({exp_r}, {exp_c})"

        table_data.append(
            [
                filename,
                status,
                actual_shape_str,
                expected_shape_str,
                meta["symmetry"],
                meta["dependent_on"],
                meta["units"],
                meta["desc"],
            ]
        )

    # Step 3: Print and Save
    print_and_save_table(table_data, table_headers, args.output)

    # Step 4: Perform Extractions if requested
    if args.extract:
        perform_extraction(target_dir, args)


if __name__ == "__main__":
    main()
