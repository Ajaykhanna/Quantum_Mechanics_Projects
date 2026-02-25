#!/usr/bin/env python3
"""
Parse frozen-geometry NEXMD outputs into NumPy arrays.

Outputs:
  - acn_R.npy                       shape: (N, natoms, 3)
  - acn_Z.npy                       shape: (N, natoms)
  - acn_frzNACT{ij}.npy             shape: (N,) for requested state pairs

Behavior:
  - Frame order follows foldernames.txt exactly.
  - Missing fock_rho_trace_frzn_matrix_eV.out is logged as a warning.
  - Missing pair values are kept as NaN to preserve frame indexing.
  - A text log is written to output_dir/parse_frozen_outputs.log
"""

import argparse
import logging
import os
import re
from pathlib import Path
from multiprocessing import Pool, set_start_method

# ALWAYS import numpy, as workers rely on it to avoid GPU context locks
import numpy as np

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

ATOMIC_NUMBERS = {
    "H": 1, "HE": 2, "LI": 3, "BE": 4, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9,
    "NE": 10, "NA": 11, "MG": 12, "AL": 13, "SI": 14, "P": 15, "S": 16, "CL": 17,
    "AR": 18, "K": 19, "CA": 20,
}


def setup_logger(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "parse_frozen_outputs.log"

    logger = logging.getLogger("parse_frozen_outputs")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    fmt = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, mode="w")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, log_path


def read_foldernames(path):
    names = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            token = line.strip()
            if not token or token.startswith("#"):
                continue
            names.append(token)
    return names


def parse_pair_token(token):
    token = token.strip()
    if not token:
        raise ValueError("empty pair token")

    if "-" in token:
        parts = token.split("-")
        if len(parts) != 2:
            raise ValueError(f"invalid pair token: {token}")
        i = int(parts[0])
        j = int(parts[1])
    else:
        if not token.isdigit():
            raise ValueError(f"invalid pair token: {token}")
        if len(token) != 2:
            raise ValueError(f"pair token '{token}' is ambiguous; use i-j format for multi-digit states")
        i = int(token[0])
        j = int(token[1])

    if i == j:
        raise ValueError(f"pair token has equal states: {token}")
        
    # FIX: Array Bounds Check. Prevent Python negative indexing wrap-around.
    if i <= 0 or j <= 0:
        raise ValueError(f"pair tokens must be 1-indexed (e.g., state > 0). Got: {token}")

    i, j = sorted((i, j))
    code = f"{i}{j}"
    return i, j, code


def parse_pairs(pair_string):
    seen = set()
    parsed = []
    for tok in pair_string.split(","):
        i, j, code = parse_pair_token(tok)
        if code in seen:
            continue
        seen.add(code)
        parsed.append((i, j, code))
    return parsed


def resolve_frame_paths(frame_token, trace_filename):
    frame_path = Path(frame_token)
    frame_dir = frame_path.with_suffix("") if frame_path.suffix else frame_path
    stem = frame_path.stem if frame_path.suffix else frame_path.name

    xyz_candidates = [
        frame_dir / (stem + ".xyz"),
        frame_dir / (frame_path.name + ".xyz"),
    ]
    xyz_path = xyz_candidates[0]
    for cand in xyz_candidates:
        if cand.exists():
            xyz_path = cand
            break

    trace_path = frame_dir / trace_filename
    return frame_dir, xyz_path, trace_path


def atomic_number_from_token(tok):
    try:
        return int(tok)
    except ValueError:
        key = tok.strip().upper()
        if key not in ATOMIC_NUMBERS:
            raise ValueError(f"unknown element token '{tok}'")
        return ATOMIC_NUMBERS[key]


def read_xyz(path, natoms):
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if len(lines) < natoms:
        raise ValueError("too few lines in xyz file")

    atom_lines = None
    first_parts = lines[0].split()
    if len(first_parts) > 0 and first_parts[0].isdigit():
        nfile = int(first_parts[0])
        if len(lines) >= nfile + 2:
            atom_lines = lines[2 : 2 + nfile]

    if atom_lines is None:
        atom_lines = lines

    if len(atom_lines) < natoms:
        raise ValueError(f"xyz has fewer than requested natoms={natoms}")

    atom_lines = atom_lines[:natoms]

    z = np.full((natoms,), -1, dtype=np.int32)
    r = np.full((natoms, 3), np.nan, dtype=np.float32)

    for i, line in enumerate(atom_lines):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"bad xyz atom line: '{line}'")
        z[i] = atomic_number_from_token(parts[0])
        r[i, 0] = float(parts[1])
        r[i, 1] = float(parts[2])
        r[i, 2] = float(parts[3])

    return z, r


def read_trace_matrix(path):
    nstates_header = None
    rows = []
    pat = re.compile(r"Nstates\s*=\s*(\d+)")

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                m = pat.search(line)
                if m:
                    nstates_header = int(m.group(1))
                continue

            vals = [float(x.replace("D", "E").replace("d", "e")) for x in line.split()]
            rows.append(vals)

    if not rows:
        raise ValueError("trace matrix file contains no numeric rows")

    ncol = len(rows[0])
    for row in rows:
        if len(row) != ncol:
            raise ValueError("inconsistent row length in matrix")

    mat = np.array(rows, dtype=np.float64)
    if mat.shape[0] != mat.shape[1]:
        raise ValueError(f"matrix is not square: {mat.shape}")

    if nstates_header is not None and mat.shape[0] != nstates_header:
        raise ValueError(f"matrix size mismatch with header: {mat.shape[0]} vs {nstates_header}")

    return mat


def process_frame(task_args):
    """Worker function to process a single frame."""
    idx, frame, args, pairs = task_args

    # Force standard numpy in workers to prevent multiprocessing GPU context conflicts
    np_or_cp = np 

    frame_dir, xyz_path, trace_path = resolve_frame_paths(frame, args.trace_filename)

    R_frame = np_or_cp.full((args.natoms, 3), np.nan, dtype=np.float32)
    Z_frame = np_or_cp.full((args.natoms,), -1, dtype=np.int32)
    pair_vals_frame = {code: np.nan for _, _, code in pairs}
    
    # Track individual frame stats to send back to main process
    f_stats = {
        "xyz_ok": 0, "missing_xyz": 0, "bad_xyz": 0,
        "trace_ok": 0, "missing_trace": 0, "bad_trace": 0
    }

    # Process XYZ file
    if xyz_path.exists():
        try:
            z, r = read_xyz(xyz_path, args.natoms)
            Z_frame = z
            R_frame = r
            f_stats["xyz_ok"] = 1
        except Exception as exc:
            logging.warning(f"Frame {frame}: failed to parse xyz ({xyz_path}): {exc}")
            f_stats["bad_xyz"] = 1
    else:
        f_stats["missing_xyz"] = 1

    # Process trace matrix
    if trace_path.exists():
        try:
            mat = read_trace_matrix(trace_path)
            nstates = mat.shape[0]
            for i, j, code in pairs:
                # Array bounds check: j must be within state dimensions
                if j <= nstates:
                    pair_vals_frame[code] = mat[i - 1, j - 1]
            f_stats["trace_ok"] = 1
        except Exception as exc:
            logging.warning(f"Frame {frame}: failed to parse trace matrix ({trace_path}): {exc}")
            f_stats["bad_trace"] = 1
    else:
        f_stats["missing_trace"] = 1

    return idx, R_frame, Z_frame, pair_vals_frame, f_stats


def main():
    parser = argparse.ArgumentParser(
        description="Parse frozen trace outputs into acn_* numpy files."
    )
    parser.add_argument("--foldernames", default="foldernames.txt")
    parser.add_argument("--output_dir", default="parsed_npys")
    parser.add_argument("--pairs", default="12,13,23")
    parser.add_argument("--natoms", type=int, default=15)
    parser.add_argument("--trace_filename", default="fock_rho_trace_frzn_matrix_eV.out")
    parser.add_argument(
        "--use_gpus", action="store_true",
        help="Enable GPU usage if CuPy is available. Defaults to CPU only.",
    )
    args = parser.parse_args()

    # Determine whether to use GPUs based on argparse and CuPy availability
    global GPU_AVAILABLE 
    GPU_AVAILABLE = GPU_AVAILABLE and args.use_gpus

    output_dir = Path(args.output_dir)
    logger, log_path = setup_logger(output_dir)

    frames = read_foldernames(args.foldernames)
    nframes = len(frames)
    if nframes == 0:
        logger.error(f"No frames found in {args.foldernames}")
        return

    pairs = parse_pairs(args.pairs)
    logger.info(f"Total frames listed: {nframes}")
    logger.info(f"Requested state pairs: {', '.join([p[2] for p in pairs])}")

    # Use CuPy in the main process if available and enabled
    np_or_cp = cp if GPU_AVAILABLE else np

    # Ensure bounds and types are mapped safely whether using CuPy or NumPy
    R = np_or_cp.full((nframes, args.natoms, 3), np_or_cp.nan, dtype=np_or_cp.float32)
    Z = np_or_cp.full((nframes, args.natoms), -1, dtype=np_or_cp.int32)
    pair_vals = {
        code: np_or_cp.full((nframes,), np_or_cp.nan, dtype=np_or_cp.float64)
        for _, _, code in pairs
    }

    stats = {
        "xyz_ok": 0, "missing_xyz": 0, "bad_xyz": 0,
        "trace_ok": 0, "missing_trace": 0, "bad_trace": 0
    }

    with Pool(processes=16) as pool:
        tasks = [(idx, frame, args, pairs) for idx, frame in enumerate(frames)]
        
        # Use imap_unordered for dynamic streaming of results as they finish
        result_iterator = pool.imap_unordered(process_frame, tasks)
        
        if HAS_TQDM:
            result_iterator = tqdm(result_iterator, total=len(tasks), desc="Parsing Frames", unit="frame")

        # Aggregate results as they stream in (memory efficient)
        for idx, R_frame, Z_frame, pair_vals_frame, f_stats in result_iterator:
            if GPU_AVAILABLE:
                R[idx, :, :] = cp.asarray(R_frame)
                Z[idx, :] = cp.asarray(Z_frame)
            else:
                R[idx, :, :] = R_frame
                Z[idx, :] = Z_frame
                
            for code in pair_vals_frame:
                pair_vals[code][idx] = pair_vals_frame[code]
                
            # Accumulate run stats safely
            for k in stats:
                stats[k] += f_stats[k]

    # Safely retrieve array based on global definition, avoiding NameError
    def get_final_array(arr):
        return cp.asnumpy(arr) if GPU_AVAILABLE else arr

    # Save results
    np.save(output_dir / "acn_R.npy", get_final_array(R))
    np.save(output_dir / "acn_Z.npy", get_final_array(Z))
    for _, _, code in pairs:
        np.save(output_dir / f"acn_frzNACT{code}.npy", get_final_array(pair_vals[code]))

    logger.info(f"Saved: {output_dir / 'acn_R.npy'}")
    logger.info(f"Saved: {output_dir / 'acn_Z.npy'}")
    for _, _, code in pairs:
        logger.info(f"Saved: {output_dir / f'acn_frzNACT{code}.npy'}")

    logger.info(
        "XYZ summary: ok=%d missing=%d bad=%d",
        stats["xyz_ok"], stats["missing_xyz"], stats["bad_xyz"]
    )
    logger.info(
        "Trace summary: ok=%d missing=%d bad=%d",
        stats["trace_ok"], stats["missing_trace"], stats["bad_trace"]
    )
    logger.info(f"Log saved to: {log_path}")


if __name__ == "__main__":
    # Protect set_start_method inside the main execution block
    # This prevents the "RuntimeError: context has already been set" 
    # when spawn method recursively re-imports the file
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass
        
    main()