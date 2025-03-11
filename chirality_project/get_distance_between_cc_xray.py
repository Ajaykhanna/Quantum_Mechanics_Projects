##########################################################################
# Developer: Ajay Khanna
# Lab: Dr. Sergei Tretiak
# Date: Mar.11.2025
# Place: Los Alamos National Laboratory (LANL)
# Project: Multidimension X-ray Spectroscopy
# Program: Script To Get Distance Between Chiral Carbon and X-ray Chromophore
# How to Run?: python get_distance_between_cc_xray.py --base_path "path/to/base_folder" --folder_prefix "PG1" --xray_atom "Br"
##########################################################################


import re
import os
import glob
import argparse
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, squareform

# Display ASCII banner with LAB Name and Project Name


def banner():
    """
    Display a banner with project information.
    """
    print("##########################################################################")
    print("# Python Script To Get Distance Between Chiral Carbon and X-ray Chromophore")
    print("# Developer: Ajay Khanna")
    print("# Lab: Dr. Sergei Tretiak")
    print("##########################################################################")


def natural_sort_key(s):
    """
    Create key for natural sorting of strings containing numbers.

    Args:
        s (str): The string to be sorted.

    Returns:
        list: A list of integers and strings for sorting.
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


def get_connectivity_matrix(coordinates):
    """
    Generate connectivity matrix using specific bond length thresholds.

    Args:
        coordinates (np.ndarray): Array of atomic coordinates and types.

    Returns:
        np.ndarray: Connectivity matrix.
    """
    positions = coordinates[:, 1:].astype(float)
    distances = squareform(pdist(positions))

    # Define specific bond length thresholds
    bond_thresholds = {
        ("C", "C"): 1.6,  # C-C single/double bond
        ("C", "N"): 1.5,  # C-N bond
        ("C", "O"): 1.4,  # C-O bond
        ("C", "H"): 1.2,  # C-H bond
    }

    n_atoms = len(coordinates)
    connectivity = np.zeros((n_atoms, n_atoms), dtype=bool)

    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            atom1, atom2 = coordinates[i, 0], coordinates[j, 0]
            pair = tuple(sorted([atom1, atom2]))
            threshold = bond_thresholds.get(pair, 1.8)  # default threshold
            if distances[i, j] < threshold:
                connectivity[i, j] = connectivity[j, i] = True

    return connectivity


def find_carboxyl_group(coordinates, conn_matrix, carbon_idx):
    """
    Check if carbon has a COOH group by looking for bonded carbon with two oxygens.

    Args:
        coordinates (np.ndarray): Array of atomic coordinates and types.
        conn_matrix (np.ndarray): Connectivity matrix.
        carbon_idx (int): Index of the carbon atom.

    Returns:
        bool: True if COOH group is found, False otherwise.
    """
    bonded_indices = np.where(conn_matrix[carbon_idx])[0]

    for idx in bonded_indices:
        if coordinates[idx, 0] == "C":
            # Check if this carbon has two oxygens
            c_bonds = np.where(conn_matrix[idx])[0]
            oxygen_count = sum(1 for i in c_bonds if coordinates[i, 0] == "O")
            if oxygen_count == 2:
                return True
    return False


def identify_chiral_carbon(coordinates):
    """
    Identify chiral carbon with NH2-C-COOH pattern.

    Args:
        coordinates (np.ndarray): Array of atomic coordinates and types.

    Returns:
        int: Index of the chiral carbon atom, or None if not found.
    """
    conn_matrix = get_connectivity_matrix(coordinates)

    for i, atom in enumerate(coordinates[:, 0]):
        if atom != "C":
            continue

        bonded_indices = np.where(conn_matrix[i])[0]
        bonded_atoms = coordinates[bonded_indices, 0]

        # Check for NH2 group
        n_count = sum(1 for idx in bonded_indices if coordinates[idx, 0] == "N")

        # Check for benzene connection
        c_count = sum(1 for idx in bonded_indices if coordinates[idx, 0] == "C")

        # Check for COOH group
        has_carboxyl = find_carboxyl_group(coordinates, conn_matrix, i)

        if n_count == 1 and c_count >= 1 and has_carboxyl:
            return i

    return None


def get_x_ray_chromophore_index(coordinates, xray_atom="Br"):
    """
    Determines the x-ray chromophore index based on string query.

    Args:
        coordinates (np.ndarray): Array of atomic coordinates and types.
        xray_atom (str): Symbol of the x-ray chromophore atom.

    Returns:
        int: Index of the x-ray chromophore atom, or None if not found.
    """
    for idx, atom in enumerate(coordinates[:, 0]):
        if xray_atom in atom:
            return idx
    return None


def get_xyz_contents(xyz_file):
    """
    Reads XYZ file contents and returns numpy array of coordinates.

    Args:
        xyz_file (str): Path to the XYZ file.

    Returns:
        np.ndarray: Array of atomic coordinates and types.
    """
    try:
        coordinates = np.zeros((0, 4), dtype=object)
        with open(xyz_file, "r") as file:
            lines = file.readlines()[2:]
            for line in lines:
                atom, x, y, z = line.split()
                coordinates = np.vstack(
                    [coordinates, [atom, float(x), float(y), float(z)]]
                )
        return coordinates
    except FileNotFoundError:
        print(f"Error: File {xyz_file} not found.")
        return None
    except Exception as e:
        print(f"Error reading {xyz_file}: {e}")
        return None


def get_distance(coordinates, index_atom1, index_atom2):
    """
    Calculates distance between two atoms in 3D space.

    Args:
        coordinates (np.ndarray): Array of atomic coordinates and types.
        index_atom1 (int): Index of the first atom.
        index_atom2 (int): Index of the second atom.

    Returns:
        float: Distance between the two atoms.
    """
    atom1_coords = np.array(coordinates[index_atom1][1:], dtype=float)
    atom2_coords = np.array(coordinates[index_atom2][1:], dtype=float)
    return np.linalg.norm(atom1_coords - atom2_coords)


def process_folders(base_path, folder_prefix, xray_atom):
    """
    Process folders with detailed logging.

    Args:
        base_path (str): Base path containing the folders.
        folder_prefix (str): Prefix of the folders to process.
        xray_atom (str): Symbol of the x-ray chromophore atom.

    Returns:
        dict: Results of the distance calculations.
    """
    folder_pattern = os.path.join(base_path, f"{folder_prefix}_Br*_trans")
    folders = glob.glob(folder_pattern)
    results = {}

    print(f"\nProcessing {len(folders)} folders...")

    for folder in sorted(folders):
        folder_name = os.path.basename(folder)

        xyz_pattern = os.path.join(folder, f"{folder_name}_opt_gs.xyz")
        xyz_files = glob.glob(xyz_pattern)

        if not xyz_files:
            print(f"No XYZ file found in {folder_name}")
            continue

        xyz_file = xyz_files[0]

        coordinates = get_xyz_contents(xyz_file)
        if coordinates is None:
            print("Failed to read coordinates")
            continue

        chiral_carbon_idx = identify_chiral_carbon(coordinates)
        if chiral_carbon_idx is None:
            print("Could not identify chiral carbon")
            continue

        xray_idx = get_x_ray_chromophore_index(coordinates, xray_atom)
        if xray_idx is None:
            print(f"Could not find {xray_atom} atom")
            continue

        distance = get_distance(coordinates, chiral_carbon_idx, xray_idx)
        results[folder_name] = {
            "distance": distance,
            "chiral_idx": chiral_carbon_idx,
            "xray_idx": xray_idx,
        }

    return results


def main():
    """
    Main function to parse arguments and process folders.
    """
    parser = argparse.ArgumentParser(
        description="Calculate distances between chiral carbon and x-ray chromophore for multiple structures."
    )
    parser.add_argument(
        "--base_path", type=str, help="Base path containing the PG1_Br*_trans folders"
    )
    parser.add_argument(
        "--folder_prefix",
        type=str,
        default="PG1",
        help="Prefix of the folders to process",
    )
    parser.add_argument(
        "--xray_atom",
        type=str,
        default="Br",
        help="Symbol of the x-ray chromophore atom",
    )

    args = parser.parse_args()

    # Process all folders and get results
    results = process_folders(args.base_path, args.folder_prefix, args.xray_atom)

    # Print results in a formatted way
    print("\nDistance Results:")
    print("-" * 90)
    print(
        f"{'Structure':<30} {'Distance (Å)':<15} {'Chiral Index':<15} {'X-ray Index':<15}"
    )
    print("-" * 90)

    # Use natural sorting for output
    for folder_name, data in sorted(
        results.items(), key=lambda x: natural_sort_key(x[0])
    ):
        print(
            f"{folder_name:<30} {data['distance']:>15.5f} {data['chiral_idx']:>15} {data['xray_idx']:>15}"
        )

    # Save results to a log file
    log_file = "distance_measurements.log"
    # Use natural sorting for log file
    with open(log_file, "w") as f:
        f.write("Structure Distance Measurements\n")
        f.write("-" * 90 + "\n")
        f.write(
            f"{'Structure':<30} {'Distance (Å)':<15} {'Chiral Index':<15} {'X-ray Index':<15}\n"
        )
        f.write("-" * 90 + "\n")
        for folder_name, data in sorted(
            results.items(), key=lambda x: natural_sort_key(x[0])
        ):
            f.write(
                f"{folder_name:<30} {data['distance']:>15.5f} {data['chiral_idx']:>15} {data['xray_idx']:>15}\n"
            )

    print(f"\nResults have been saved to {log_file}")


if __name__ == "__main__":
    main()
