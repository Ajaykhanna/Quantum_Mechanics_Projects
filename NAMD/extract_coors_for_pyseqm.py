#!/usr/bin/env python
# coding: utf-8
"""
Extract Atomic Numbers (Z) and Coordinates (R) from XYZ Frames

This script extracts atomic numbers and Cartesian coordinates from
either a single concatenated XYZ trajectory file OR individual
XYZ files (frame_1.xyz through frame_N.xyz). It outputs `.npy` arrays
with optional sorting functionality.

Features:
- NEW: Parse single concatenated .xyz trajectory files
- Parallel processing for individual frame directory structures
- Expanded periodic table support (matches PySEQM)
- Progress tracking with TQDM
- Optional Z/R sorting (descending atomic number)
- Validation system
"""

import os
import argparse
import datetime
import numpy as np
import multiprocessing
from typing import Tuple, Optional
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

# Default Settings
BASE_PATH = "./"  # Base path to frame XYZ files (user-configurable)
DATE = datetime.datetime.now().strftime("%Y-%b-%d")

# Create output directory
if not os.path.exists(f"./{DATE}"):
    os.makedirs(f"./{DATE}")

# Generate default frame filenames (for directory-based extraction)
FILENAMES = [f"frame_{i}/frame_{i}.xyz" for i in range(1, 100001)]

# Comprehensive element dictionary compatible with PySEQM
ELEMENT_DICT = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
    "Na": 11,
    "Mg": 12,
    "Al": 13,
    "Si": 14,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "Ar": 18,
    "K": 19,
    "Ca": 20,
    "Sc": 21,
    "Ti": 22,
    "V": 23,
    "Cr": 24,
    "Mn": 25,
    "Fe": 26,
    "Co": 27,
    "Ni": 28,
    "Cu": 29,
    "Zn": 30,
    "Ga": 31,
    "Ge": 32,
    "As": 33,
    "Se": 34,
    "Br": 35,
    "Kr": 36,
    "Rb": 37,
    "Sr": 38,
    "Y": 39,
    "Zr": 40,
    "Nb": 41,
    "Mo": 42,
    "Tc": 43,
    "Ru": 44,
    "Rh": 45,
    "Pd": 46,
    "Ag": 47,
    "Cd": 48,
    "In": 49,
    "Sn": 50,
    "Sb": 51,
    "Te": 52,
    "I": 53,
    "Xe": 54,
}

# ============================================================================
# TRAJECTORY FILE PARSER (NEW)
# ============================================================================


def count_frames_in_trajectory(filepath: str) -> int:
    """
    Counts the total number of frames in a concatenated XYZ trajectory file.
    """
    logger.info(f"Scanning trajectory file to count frames: {filepath}")
    count = 0
    with open(filepath, "r", buffering=8 << 20) as f:
        while True:
            nline = f.readline()
            if not nline:
                break
            try:
                n = int(nline.strip())
                f.readline()  # Skip comment line
                for _ in range(n):
                    f.readline()  # Skip atom lines
                count += 1
            except ValueError:
                logger.error(
                    f"Malformed XYZ file at frame {count+1}. Expected integer for atom count."
                )
                break
    return count


def read_trajectory_file(
    filepath: str,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
    step_frame: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reads a single concatenated XYZ trajectory file with slicing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Trajectory file not found: {filepath}")

    total_available_frames = count_frames_in_trajectory(filepath)

    end_idx = (
        total_available_frames
        if end_frame is None
        else min(end_frame, total_available_frames)
    )

    target_frames = list(range(start_frame, end_idx, step_frame))
    target_set = set(target_frames)

    logger.info(
        f"Extracting {len(target_frames)} frames out of {total_available_frames} from trajectory file..."
    )

    Z_list = []
    R_list = []

    current_frame = 0

    with open(filepath, "r", buffering=64 << 20) as f:
        with tqdm(total=len(target_frames), desc="Parsing trajectory") as pbar:
            while True:
                nline = f.readline()
                if not nline:
                    break
                n_atoms = int(nline.strip())

                if current_frame >= end_idx:
                    break  # Stop parsing once we're past the end frame

                if current_frame in target_set:
                    f.readline()  # Skip comment

                    z_frame = np.zeros(n_atoms, dtype=int)
                    r_frame = np.zeros((n_atoms, 3), dtype=float)

                    for i in range(n_atoms):
                        parts = f.readline().split()
                        sym = parts[0]

                        # Check if it's already a numeric atomic number or needs symbol lookup
                        if sym.isdigit():
                            z_frame[i] = int(sym)
                        else:
                            # Capitalize nicely to match dictionary (e.g., 'c' -> 'C', 'he' -> 'He')
                            clean_sym = sym.capitalize()
                            if clean_sym not in ELEMENT_DICT:
                                raise ValueError(f"Unknown atomic symbol: {sym}")
                            z_frame[i] = ELEMENT_DICT[clean_sym]

                        r_frame[i, 0] = float(parts[1])
                        r_frame[i, 1] = float(parts[2])
                        r_frame[i, 2] = float(parts[3])

                    Z_list.append(z_frame)
                    R_list.append(r_frame)
                    pbar.update(1)
                else:
                    # Skip this frame entirely
                    f.readline()  # Skip comment
                    for _ in range(n_atoms):
                        f.readline()  # Skip atom lines

                current_frame += 1

    return np.array(Z_list), np.array(R_list)


# ============================================================================
# UTILITY FUNCTIONS (MULTI-FOLDER FALLBACK)
# ============================================================================


def get_atomic_number_and_coordinates(filename: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reads the atomic numbers and coordinates from an individual XYZ file.
    """
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Coordinates file not found: {filename}")

        data = np.loadtxt(filename, skiprows=2, dtype=str)

        # Extract atomic numbers
        atomic_numbers = []
        for row in data:
            symbol = row[0]
            if symbol.isdigit():
                atomic_numbers.append(int(symbol))
            else:
                clean_sym = symbol.capitalize()
                if clean_sym not in ELEMENT_DICT:
                    raise ValueError(f"Unknown atomic symbol: {symbol}")
                atomic_numbers.append(ELEMENT_DICT[clean_sym])

        # Extract coordinates
        atomic_coordinates = data[:, 1:].astype(float)

        return np.array(atomic_numbers), atomic_coordinates
    except Exception as e:
        logger.error(f"Error reading atomic data from {filename}: {e}")
        raise


def check_if_sorted_descending(Z: np.ndarray) -> bool:
    """
    Checks if atomic numbers array is sorted in descending order for all frames.
    """
    for frame_idx in range(Z.shape[0]):
        frame_Z = Z[frame_idx]
        if not np.all(frame_Z[:-1] >= frame_Z[1:]):
            return False
    return True


def sort_Z_and_R(
    Z: np.ndarray, R: np.ndarray, subdirectory: str = DATE
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Sorts atomic numbers in descending order and rearranges coordinates accordingly.
    """
    logger.info("Sorting Z and R data by descending atomic number...")

    desc_indices = np.argsort(-Z, axis=1)
    sorted_Z = np.take_along_axis(Z, desc_indices, axis=1)
    sorted_R = np.take_along_axis(R, desc_indices[:, :, None], axis=1)

    logger.info("Saving sorted data files...")
    save_data("sorted_Z.npy", sorted_Z, subdirectory)
    save_data("sorted_R.npy", sorted_R, subdirectory)
    save_data("sorted_Z_indices.npy", desc_indices, subdirectory)

    logger.info(f"Sorted data saved:")
    logger.info(f"  sorted_Z.npy: {sorted_Z.shape}")
    logger.info(f"  sorted_R.npy: {sorted_R.shape}")
    logger.info(f"  sorted_Z_indices.npy: {desc_indices.shape}")

    return sorted_Z, sorted_R, desc_indices


def process_frame(frame: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Processes a single frame folder (multiprocessing helper).
    """
    try:
        frame_path = os.path.join(BASE_PATH, frame)
        z, coords = get_atomic_number_and_coordinates(frame_path)
        return z, coords
    except Exception as e:
        logger.error(f"Error processing frame {frame}: {e}")
        raise


# ============================================================================
# DATA SAVING & VALIDATION
# ============================================================================


def save_data(filename: str, data: np.ndarray, subdirectory: str = DATE) -> None:
    try:
        filepath = f"{subdirectory}/{filename}"
        np.save(filepath, data)
        logger.info(f"Saved: {filepath} with shape {data.shape}")
    except IOError as e:
        logger.error(f"Error saving {filename}: {e}")
        raise


def validate_data(
    Z: np.ndarray, R: np.ndarray, filenames: list, num_samples: int = 5
) -> None:
    """
    Validates extracted Z and R data against source directory files.
    """
    logger.info(f"Validating data with {num_samples} random samples...")
    num_frames = len(filenames)
    sample_indices = np.random.choice(num_frames, size=num_samples, replace=False)

    all_valid = True
    for idx in sample_indices:
        frame = filenames[idx]
        frame_path = os.path.join(BASE_PATH, frame)

        try:
            z_file, r_file = get_atomic_number_and_coordinates(frame_path)

            if not np.array_equal(Z[idx], z_file):
                logger.error(f"Validation failed for {frame}: Z mismatch")
                all_valid = False
                continue

            if not np.allclose(R[idx], r_file, rtol=1e-10, atol=1e-10):
                logger.error(f"Validation failed for {frame}: R mismatch")
                all_valid = False
                continue

            logger.info(f"✓ Frame {idx} ({frame}): Validation passed")

        except Exception as e:
            logger.error(f"Validation error for {frame}: {e}")
            all_valid = False

    if all_valid:
        logger.info("✓ All validation checks passed!")
    else:
        logger.warning("⚠ Some validation checks failed!")


# ============================================================================
# MAIN EXTRACTION PIPELINE
# ============================================================================


def main(
    base_path: str = "./",
    traj_file: Optional[str] = None,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
    step_frame: int = 1,
    num_frames: Optional[int] = None,
    validate: bool = True,
    sort_data: bool = False,
) -> dict:

    global BASE_PATH
    BASE_PATH = base_path

    logger.info("=" * 70)
    logger.info("Z and R Extraction Pipeline")
    logger.info("=" * 70)
    logger.info(f"Output directory: {DATE}/")

    # Handle fallback for num_frames vs end_frame
    if end_frame is None and num_frames is not None:
        end_frame = start_frame + num_frames

    # ---- PARSE DATA ----
    if traj_file:
        logger.info(f"Mode: Single Trajectory File -> {traj_file}")
        atomic_number_data, coords_data = read_trajectory_file(
            traj_file, start_frame, end_frame, step_frame
        )

        if validate:
            logger.info(
                "Skipping cross-file validation (not required for single trajectory parse)."
            )

    else:
        logger.info(f"Mode: Directory Frames -> {BASE_PATH}")

        end_idx = end_frame if end_frame is not None else len(FILENAMES)
        frames_to_process = FILENAMES[start_frame:end_idx:step_frame]

        if not frames_to_process:
            raise ValueError(
                "No frames selected. Check start_frame, end_frame, and step_frame values."
            )

        first_frame_path = os.path.join(BASE_PATH, frames_to_process[0])
        if not os.path.exists(first_frame_path):
            raise FileNotFoundError(
                f"First frame not found: {first_frame_path}\n"
                f"Please check BASE_PATH and file naming convention."
            )

        logger.info(f"Processing {len(frames_to_process)} frames...")
        with multiprocessing.Pool() as pool:
            results = list(
                tqdm(
                    pool.imap(process_frame, frames_to_process),
                    total=len(frames_to_process),
                    desc="Extracting Z and R",
                )
            )

        z_array, coords_array = zip(*results)
        atomic_number_data = np.array(z_array)
        coords_data = np.array(coords_array)

        if validate:
            logger.info("Performing validation...")
            validate_data(
                atomic_number_data,
                coords_data,
                frames_to_process,
                num_samples=min(5, len(frames_to_process)),
            )

    logger.info("Extracted data shapes:")
    logger.info(f"  Atomic numbers (Z): {atomic_number_data.shape}")
    logger.info(f"  Coordinates (R): {coords_data.shape}")

    # ---- SAVE PARENT FILES ----
    logger.info("Saving parent data files...")
    save_data("acn_Z.npy", atomic_number_data)
    save_data("acn_R.npy", coords_data)

    result_dict = {
        "atomic_numbers": atomic_number_data,
        "coordinates": coords_data,
    }

    # ---- SORTING ----
    if sort_data:
        logger.info("Checking if Z data is already sorted...")
        if check_if_sorted_descending(atomic_number_data):
            logger.info("✓ Z data is already sorted in descending order!")
            logger.info("  Skipping sorting operation.")
        else:
            logger.info("Z data is not sorted. Starting sorting operation...")
            sorted_Z, sorted_R, sort_indices = sort_Z_and_R(
                atomic_number_data, coords_data
            )
            result_dict["sorted_atomic_numbers"] = sorted_Z
            result_dict["sorted_coordinates"] = sorted_R
            result_dict["sort_indices"] = sort_indices

    logger.info("=" * 70)
    logger.info(f"Processing complete! Data saved to {DATE}/")
    logger.info("=" * 70)

    return result_dict


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract atomic numbers (Z) and coordinates (R) from XYZ frames or trajectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from a single concatenated trajectory file
  python extract_frames_for_pyseqm.py --traj_file coords.xyz

  # Extract from a single file, sort, and process only first 500 frames
  python extract_frames_for_pyseqm.py --traj_file coords.xyz --sort_ZR --num_frames 500

  # Extract from individual frames in current directory (Old Behavior)
  python extract_frames_for_pyseqm.py --base_path ./frames/
        """,
    )

    parser.add_argument(
        "--traj_file",
        type=str,
        default=None,
        help="Path to a single concatenated .xyz trajectory file (Overrides --base_path if provided)",
    )

    parser.add_argument(
        "--base_path",
        type=str,
        default="./",
        help="Base directory containing frame_*.xyz files (default: current directory)",
    )

    parser.add_argument(
        "--start_frame",
        type=int,
        default=0,
        help="Starting frame index (0-based, default: 0)",
    )

    parser.add_argument(
        "--end_frame",
        type=int,
        default=None,
        help="Ending frame index (exclusive, default: all available)",
    )

    parser.add_argument(
        "--step_frame",
        type=int,
        default=1,
        help="Step size between extracted frames (default: 1)",
    )

    parser.add_argument(
        "--num_frames",
        type=int,
        default=None,
        help="Number of frames to process (Legacy option, overridden by end_frame)",
    )

    parser.add_argument(
        "--no_validate",
        action="store_true",
        help="Skip validation step (faster but less safe - auto-skipped for trajectories)",
    )

    parser.add_argument(
        "--sort_ZR",
        action="store_true",
        help="Sort Z by descending atomic number and rearrange R accordingly",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Z and R Extraction from XYZ Files")
    print("=" * 70)

    if args.traj_file:
        print(f"Target: Single Trajectory ({args.traj_file})")
    else:
        print(f"Target: Base path ({args.base_path})")

    print(f"Start frame: {args.start_frame}")
    if args.end_frame is not None:
        print(f"End frame: {args.end_frame}")
    elif args.num_frames is not None:
        print(f"End frame: {args.start_frame + args.num_frames} (via num_frames)")
    else:
        print("End frame: All available")
    print(f"Step frame: {args.step_frame}")
    print(f"Sort Z and R: {args.sort_ZR}")
    print("=" * 70)

    extracted_data = main(
        base_path=args.base_path,
        traj_file=args.traj_file,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        step_frame=args.step_frame,
        num_frames=args.num_frames,
        validate=not args.no_validate,
        sort_data=args.sort_ZR,
    )

    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)
    print(f"Output directory: {DATE}/")
    print(f"Data keys: {list(extracted_data.keys())}")
    print("=" * 70)
