#!/usr/bin/env python3

import numpy as np
import math
import os
import argparse
from collections import deque

# --- ORCA Input Template ---
# Note the placeholder {{xyz_filename}} which will be replaced
ORCA_TEMPLATE = """# X-Ray Scan: Angle {{angle_deg}}
! CAM-B3LYP cc-pvtz TightSCF ZORA

% maxcore 5000 # 5.0 GB Per Processor 8*5.0 GB >= 40GB required

%pal
   nprocs 8 # Adjust as needed
end

%tddft
      Tda true
      orbwin[0] = 1,1,-1,-1 # Selecting the alpha set (orbwin[0]). Selecting donor orbital range : 1 to -1 to -1 (meaning all virtual orbitals)
      nroots 30 # Setting the number of roots (transitions) to be calculated.
      maxdim 10 # Setting the scaling of maximum dimension of the expansion space.
      DoDipoleLength true
      DoDipoleVelocity true
      DoHigherMoments true
      DecomposeFoscLength true
      DecomposeFoscVelocity true
      DoCD  true
      TPrint 1E-6
end

# Coordinates are read from the separate XYZ file
* xyzfile 0 1 {{xyz_filename}}
"""

# --- Gaussian Input Template Parts ---
GAUSSIAN_HEADER = "# tda=(nstates=2,root=1) cam-b3lyp/6-31g(d) nosymm geom=connectivity"
GAUSSIAN_TITLE_TEMPLATE = "TDA: SCAN + CNNC {} Deg"  # Angle inserted here
GAUSSIAN_CHARGE = 0
GAUSSIAN_MULTIPLICITY = 1

# --- Helper Functions ---


def parse_xyz_file(filepath):
    """Parses an XYZ file into elements and coordinates."""
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Input XYZ file not found at '{filepath}'")
    except IOError as e:
        raise IOError(f"Error reading XYZ file '{filepath}': {e}")

    if not lines:
        raise ValueError(f"Error: Input XYZ file '{filepath}' is empty.")

    try:
        num_atoms = int(lines[0].strip())
    except ValueError:
        raise ValueError(
            f"Error: First line of XYZ file '{filepath}' must be the number of atoms."
        )

    if len(lines) < num_atoms + 2:
        raise ValueError(
            f"XYZ file '{filepath}' seems incomplete. Expected {num_atoms} atoms + 2 header lines, got {len(lines)} lines."
        )

    elements = []
    coords = []
    atom_lines = lines[2 : num_atoms + 2]  # Read exactly num_atoms lines after header

    for i, line in enumerate(atom_lines):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(
                f"Error parsing line {i+3} in '{filepath}': '{line.strip()}'. Expected element and 3 coordinates."
            )
        elements.append(parts[0])
        try:
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            coords.append([x, y, z])
        except ValueError:
            raise ValueError(
                f"Error converting coordinates to float on line {i+3} in '{filepath}': '{line.strip()}'"
            )

    if len(elements) != num_atoms:
        print(
            f"Warning: Number of atoms read ({len(elements)}) does not match header ({num_atoms}) in '{filepath}'."
        )

    return elements, np.array(coords)


def parse_connectivity_file(filepath, num_atoms):
    """Parses a connectivity file into a 0-based adjacency list."""
    adj_list = {i: set() for i in range(num_atoms)}
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Error: Input connectivity file not found at '{filepath}'"
        )
    except IOError as e:
        raise IOError(f"Error reading connectivity file '{filepath}': {e}")

    for line_num, line in enumerate(lines):
        parts = line.split()
        if not parts:
            continue  # Skip empty lines
        try:
            atom_from_1based = int(parts[0])
            atom_from_0based = atom_from_1based - 1

            if atom_from_0based < 0 or atom_from_0based >= num_atoms:
                print(
                    f"Warning: Connectivity line {line_num+1} starts with invalid atom index {atom_from_1based}. Skipping line: '{line.strip()}'"
                )
                continue

            i = 1
            while i < len(parts):
                if i + 1 >= len(parts):
                    if i == 1 and len(parts) == 1:
                        break
                    else:
                        print(
                            f"Warning: Missing bond order or unexpected format for atom index {parts[i]} on line {line_num+1}. Skipping connection: '{line.strip()}'"
                        )
                        break
                atom_to_1based = int(parts[i])
                atom_to_0based = atom_to_1based - 1

                if atom_to_0based < 0 or atom_to_0based >= num_atoms:
                    print(
                        f"Warning: Connectivity line {line_num+1} contains invalid target atom index {atom_to_1based}. Skipping connection in line: '{line.strip()}'"
                    )
                elif atom_from_0based == atom_to_0based:
                    print(
                        f"Warning: Atom {atom_from_1based} connected to itself on line {line_num+1}. Skipping self-connection: '{line.strip()}'"
                    )
                else:
                    adj_list[atom_from_0based].add(atom_to_0based)
                    adj_list[atom_to_0based].add(atom_from_0based)
                i += 2
        except ValueError:
            print(
                f"Warning: Could not parse numbers on connectivity line {line_num+1}: '{line.strip()}'. Skipping."
            )
            continue
        except IndexError:
            print(
                f"Warning: Unexpected format on connectivity line {line_num+1}: '{line.strip()}'. Skipping."
            )
            continue
    return adj_list


def find_rotation_group(start_node, forbidden_node, adj_list):
    """Finds all nodes reachable from start_node without passing through forbidden_node using BFS."""
    if start_node not in adj_list:
        print(
            f"Error: Start node {start_node} for rotation group search not found in adjacency list."
        )
        return set()
    visited = set()
    queue = deque([start_node])
    while queue:
        current_node = queue.popleft()
        if current_node == forbidden_node:
            continue
        if current_node in visited:
            continue
        visited.add(current_node)
        for neighbor in adj_list.get(current_node, set()):
            if neighbor != forbidden_node and neighbor not in visited:
                queue.append(neighbor)
    return visited


def calculate_dihedral(coords, indices):
    """Calculates the dihedral angle between four points."""
    max_index = max(indices)
    num_coords = len(coords)
    if max_index >= num_coords:
        raise IndexError(
            f"Dihedral index {max_index} is out of bounds for coordinates array with size {num_coords}"
        )
    if any(idx < 0 for idx in indices):
        raise IndexError(f"Dihedral indices cannot be negative: {indices}")
    p0, p1, p2, p3 = (
        coords[indices[0]],
        coords[indices[1]],
        coords[indices[2]],
        coords[indices[3]],
    )
    b0 = -1.0 * (p1 - p0)
    b1 = p2 - p1
    b2 = p3 - p2
    if np.linalg.norm(b1) < 1e-7:
        # print(f"Warning: Central atoms {indices[1]} and {indices[2]} defining dihedral axis are nearly coincident (distance < 1e-7). Dihedral is ill-defined. Returning 0.0.")
        return 0.0  # Return 0 if central bond is too short
    n1 = np.cross(b0, b1)
    n2 = np.cross(b1, b2)
    n1_norm = np.linalg.norm(n1)
    n2_norm = np.linalg.norm(n2)
    if n1_norm < 1e-7 or n2_norm < 1e-7:
        # collinear_set = "0,1,2" if n1_norm < 1e-7 else "1,2,3"
        # print(f"Warning: Atoms {indices} involved in dihedral are nearly collinear (plane normal < 1e-7 for set {collinear_set}). Setting dihedral to 0.0.")
        return 0.0  # Return 0 if atoms are collinear
    b1_norm = np.linalg.norm(b1)
    b1_unit = b1 / b1_norm
    v = b0 - np.dot(b0, b1_unit) * b1_unit
    w = b2 - np.dot(b2, b1_unit) * b1_unit
    x = np.dot(v, w)
    y = np.dot(np.cross(b1_unit, v), w)
    if np.linalg.norm(v) < 1e-9 or np.linalg.norm(w) < 1e-9:
        # print(f"Warning: Projection vectors are near zero for dihedral {indices}. Setting angle to 0.0.")
        return 0.0  # Return 0 if projection vectors are zero
    return np.degrees(np.arctan2(y, x))


def rodrigues_rotation_matrix(axis, theta):
    """Returns the Rodrigues' rotation matrix for rotation by theta radians around axis."""
    axis_norm = np.linalg.norm(axis)
    if axis_norm < 1e-9:
        # print("Warning: Rotation axis has near-zero length. Returning identity matrix.")
        return np.identity(3)
    axis = axis / axis_norm
    ux, uy, uz = axis[0], axis[1], axis[2]
    K = np.array([[0, -uz, uy], [uz, 0, -ux], [-uy, ux, 0]])
    K2 = np.dot(K, K)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    R = np.identity(3) + sin_theta * K + (1 - cos_theta) * K2
    return R


def write_xyz_file(filepath, elements, coords, comment=""):
    """Writes coordinates to an XYZ file."""
    num_atoms = len(elements)
    try:
        with open(filepath, "w") as f:
            f.write(f"{num_atoms}\n")
            f.write(f"{comment}\n")
            for i in range(num_atoms):
                f.write(
                    f" {elements[i]:<3s} {coords[i, 0]:>16.8f} {coords[i, 1]:>16.8f} {coords[i, 2]:>16.8f}\n"
                )
    except IOError as e:
        print(f"Error writing XYZ file '{filepath}': {e}")


def write_gaussian_file(filepath, elements, coords, angle_deg):
    """Writes a Gaussian input file."""
    num_atoms = len(elements)
    try:
        with open(filepath, "w") as f:
            f.write(f"{GAUSSIAN_HEADER}\n")
            f.write("\n")
            f.write(f"{GAUSSIAN_TITLE_TEMPLATE.format(f'{angle_deg:.2f}')}\n")
            f.write("\n")
            f.write(f"{GAUSSIAN_CHARGE} {GAUSSIAN_MULTIPLICITY}\n")
            for i in range(num_atoms):
                f.write(
                    f" {elements[i]:<3s} {coords[i, 0]:>16.8f} {coords[i, 1]:>16.8f} {coords[i, 2]:>16.8f}\n"
                )
            f.write("\n")
    except IOError as e:
        print(f"Error writing Gaussian file '{filepath}': {e}")


def write_orca_file(filepath, xyz_filename_rel, angle_deg):
    """Writes an ORCA input file using the template."""
    # Replace placeholders in the template
    content = ORCA_TEMPLATE.replace("{{xyz_filename}}", xyz_filename_rel)
    content = content.replace("{{angle_deg}}", f"{angle_deg:.2f}")
    try:
        with open(filepath, "w") as f:
            f.write(content)
    except IOError as e:
        print(f"Error writing ORCA file '{filepath}': {e}")


# --- Main Execution ---


def main():
    parser = argparse.ArgumentParser(
        description="Generate rotated geometries and input files (Gaussian or ORCA) for a dihedral scan."
    )

    parser.add_argument(
        "--input_xyz", required=True, help="Path to the input XYZ file."
    )
    parser.add_argument(
        "--input_conn", required=True, help="Path to the input connectivity file."
    )
    parser.add_argument(
        "--dihedral_indices",
        required=True,
        type=int,
        nargs=4,
        metavar=("A1", "A2", "A3", "A4"),
        help="Four 0-based atom indices defining the dihedral angle (e.g., 1 0 2 5).",
    )
    parser.add_argument(
        "--start_angle",
        required=True,
        type=float,
        help="Starting angle shift relative to the reference dihedral (degrees).",
    )
    parser.add_argument(
        "--end_angle",
        required=True,
        type=float,
        help="Ending angle shift relative to the reference dihedral (degrees).",
    )
    parser.add_argument(
        "--step_angle",
        type=float,
        default=1.0,
        help="Angle step for the scan (degrees, default: 1.0).",
    )
    parser.add_argument(
        "--output_type",
        required=True,
        choices=["gaussian", "orca"],
        help="Type of computational chemistry input file to generate ('gaussian' or 'orca').",
    )
    parser.add_argument(
        "--output_dir",
        default="scan_files",
        help="Directory to save generated files (default: scan_files).",
    )
    parser.add_argument(
        "--basename", default="scan", help="Base name for output files (default: scan)."
    )

    args = parser.parse_args()

    # --- Input Processing ---
    try:
        elements, initial_coords = parse_xyz_file(args.input_xyz)
        n_atoms = len(elements)
        print(f"Successfully parsed {n_atoms} atoms from '{args.input_xyz}'.")

        adjacency_list = parse_connectivity_file(args.input_conn, n_atoms)
        print(f"Successfully parsed connectivity from '{args.input_conn}'.")

    except (FileNotFoundError, ValueError, IOError, IndexError) as e:
        print(f"Error during input processing: {e}")
        return 1  # Exit with error code

    # --- Determine Rotation Group ---
    n0_index = args.dihedral_indices[1]  # Fixed part anchor
    n2_index = args.dihedral_indices[2]  # Rotating part anchor

    try:
        atoms_to_rotate_set = find_rotation_group(
            start_node=n2_index, forbidden_node=n0_index, adj_list=adjacency_list
        )
        if not atoms_to_rotate_set:
            raise ValueError("Rotation group is empty.")
        if n0_index in atoms_to_rotate_set:
            raise ValueError("Forbidden node in rotation group.")
        if n2_index not in atoms_to_rotate_set:
            raise ValueError("Start node not in rotation group.")

        atoms_to_rotate_indices = sorted(list(atoms_to_rotate_set))
        print(f"Determined {len(atoms_to_rotate_indices)} atoms to rotate.")
        # print(f"Rotating indices (0-based): {atoms_to_rotate_indices}") # Uncomment for debugging

    except ValueError as e:
        print(f"Error determining rotation group: {e}. Check connectivity and indices.")
        return 1

    # --- Calculate Reference Angle and Axis ---
    try:
        if any(idx >= n_atoms or idx < 0 for idx in args.dihedral_indices):
            raise IndexError(
                f"Dihedral indices {args.dihedral_indices} out of bounds for {n_atoms} atoms."
            )

        reference_dihedral = calculate_dihedral(initial_coords, args.dihedral_indices)
        print(
            f"Reference dihedral ({args.dihedral_indices}): {reference_dihedral:.2f} degrees"
        )

        pivot_index = n0_index
        axis_start_index = n0_index
        axis_end_index = n2_index
        if (
            axis_start_index >= n_atoms
            or axis_end_index >= n_atoms
            or pivot_index >= n_atoms
        ):
            raise IndexError("Indices for rotation axis/pivot out of bounds.")

        rotation_axis = (
            initial_coords[axis_end_index] - initial_coords[axis_start_index]
        )
        if np.linalg.norm(rotation_axis) < 1e-7:
            raise ValueError(
                "Rotation axis vector has near-zero length. Cannot rotate."
            )
        pivot_point = initial_coords[pivot_index]

    except (IndexError, ValueError) as e:
        print(f"Error setting up rotation: {e}")
        return 1

    # --- Generate Target Angles ---
    # Use np.arange for robust step handling, include endpoint approximately
    start_shift = args.start_angle
    end_shift = args.end_angle
    step = args.step_angle
    # Ensure the range includes the end_angle if possible within the step
    num_steps = int(abs(end_shift - start_shift) / abs(step)) + 1
    angle_shifts = np.linspace(start_shift, end_shift, num_steps)

    target_angles = reference_dihedral + angle_shifts
    # Add reference angle if not already included (due to float precision)
    if not np.isclose(reference_dihedral, target_angles).any():
        target_angles = np.append(target_angles, reference_dihedral)

    target_angles = sorted(
        list(np.unique(np.round(target_angles, 8)))
    )  # Round to avoid float noise duplicates

    print(
        f"Generating {len(target_angles)} files for target angles from {min(target_angles):.2f} to {max(target_angles):.2f} deg..."
    )

    # --- Create Output Directory ---
    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Output directory: '{args.output_dir}'")

    # --- Loop, Rotate, and Write Files ---
    files_generated_count = 0
    for target_angle in target_angles:
        delta_angle_deg = target_angle - reference_dihedral
        delta_angle_rad = math.radians(delta_angle_deg)
        rotation_matrix = rodrigues_rotation_matrix(rotation_axis, delta_angle_rad)

        # Apply rotation
        new_coords = initial_coords.copy()
        for atom_idx in atoms_to_rotate_indices:
            vec = initial_coords[atom_idx] - pivot_point
            rotated_vec = np.dot(rotation_matrix, vec)
            new_coords[atom_idx] = rotated_vec + pivot_point

        # --- Determine Filenames ---
        if abs(target_angle) < 1e-9:
            angle_tag = "0.00"
        elif target_angle < 0:
            angle_tag = f"minus{abs(target_angle):.2f}"
        else:
            angle_tag = f"{target_angle:.2f}"

        base_filename = f"{args.basename}_cnnc_{angle_tag}"
        xyz_filepath = os.path.join(args.output_dir, f"{base_filename}.xyz")

        # --- Write Files ---
        # 1. Write XYZ file
        xyz_comment = f"Rotated structure: Target Dihedral = {target_angle:.2f} deg"
        write_xyz_file(xyz_filepath, elements, new_coords, xyz_comment)

        # 2. Write Gaussian or ORCA file
        if args.output_type == "gaussian":
            com_filepath = os.path.join(args.output_dir, f"{base_filename}.com")
            write_gaussian_file(com_filepath, elements, new_coords, target_angle)
        elif args.output_type == "orca":
            inp_filepath = os.path.join(args.output_dir, f"{base_filename}.inp")
            # ORCA needs relative path or just filename if in same dir
            xyz_filename_relative = os.path.basename(xyz_filepath)
            write_orca_file(inp_filepath, xyz_filename_relative, target_angle)

        files_generated_count += 1

    print(f"\nGenerated {files_generated_count} sets of files in '{args.output_dir}'")

    return 0  # Success


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
