## Production Script For Publication
# __author__ = Ajay Khanna
# __place__ = LANL
#__date__ = Oct.24.2025
#__project__ = Covalent Control of Excitonic Interactions in Perylene Diimide Trimers: A Computational Study

import os
import sys
import argparse
import logging
import numpy as np
import pandas as pd
from datetime import date

## Solvent File Paths
solvent_files = [
    "./solvent_wb97xd/uPDI3_gs_optd.xyz",
    "./solvent_wb97xd/tPDI3_gs_optd.xyz",
    "./solvent_wb97xd/sPDI3_gs_optd.xyz",
]

# Vacuum File Paths
vacuum_files = [
    "./vacuum_wb97xd/uPDI3_gs_optd.xyz",
    "./vacuum_wb97xd/tPDI3_gs_optd.xyz",
    "./vacuum_wb97xd/sPDI3_gs_optd.xyz",
]


# Create Directory Using Month_Date_Year
today_str = date.today().strftime("%B_%d_%Y")
output_dir = f"./{today_str}"
os.makedirs(output_dir, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
# -------------------- Helpers --------------------


def parse_xyz(filename):
    """
    Parse a simple XYZ file into a list of (element, position) tuples.

    Parameters
    ----------
    filename : str
        Path to an XYZ format file. The function assumes the first two lines
        are header lines (atom count and comment) and that each subsequent line
        contains at least four whitespace-separated tokens: element x y z.

    Returns
    -------
    list of (str, ndarray)
        A list where each entry is a tuple (element_symbol, position_array).
        element_symbol is a string like 'C' or 'H', and position_array is a
        numpy.ndarray of shape (3,) with dtype float.

    Notes
    -----
    - Lines that have fewer than four tokens are skipped.
    - Coordinates are converted to float and packaged in a numpy array.

    Example
    -------
    >>> atoms = parse_xyz("molecule.xyz")
    >>> elem, pos = atoms[0]
    """
    atoms = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                elem = parts[0]
                xyz = np.array(
                    [float(parts[1]), float(parts[2]), float(parts[3])], dtype=float
                )
                atoms.append((elem, xyz))
    return atoms


masses = {"H": 1.00784, "C": 12.0107, "N": 14.0067, "O": 15.999}


def to_zero_based(spec):
    """
    Convert a human-readable 1-based index specification into a sorted set of
    0-based integer indices.

    Parameters
    ----------
    spec : str
        A comma-separated string with integers and ranges. Examples:
        "1-5,8,10-12" or "43-85,129". Whitespaces are ignored.

    Returns
    -------
    list of int
        Sorted list of unique 0-based indices corresponding to the input spec.

    Notes
    -----
    - Ranges are inclusive and converted from 1-based to 0-based indexing.
    - Empty tokens are ignored.
    """
    idx = []
    for token in spec.replace(" ", "").split(","):
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-")
            a, b = int(a), int(b)
            idx.extend(range(a - 1, b))  # 1-based -> 0-based inclusive
        else:
            idx.append(int(token) - 1)
    return sorted(set(idx))


def centroid(positions):
    """
    Compute the unweighted centroid (arithmetic mean) of a collection of 3D points.

    Parameters
    ----------
    positions : array-like, shape (N, 3)
        Cartesian coordinates of N points.

    Returns
    -------
    ndarray, shape (3,)
        The centroid (mean x, mean y, mean z).

    Notes
    -----
    - Uses numpy.mean across axis 0.
    """
    return positions.mean(axis=0)


def com(positions, elements):
    """
    Compute the center of mass for a set of atoms.

    Parameters
    ----------
    positions : array-like, shape (N, 3)
        Cartesian coordinates of N atoms.
    elements : sequence of str
        Sequence of element symbols (e.g. 'C', 'H') of length N. Symbols must
        exist in the module-level `masses` mapping.

    Returns
    -------
    ndarray, shape (3,)
        Mass-weighted center of mass coordinates.

    Raises
    ------
    KeyError
        If an element symbol is not present in the `masses` dictionary.
    """
    w = np.array([masses[e] for e in elements], dtype=float)
    return (w[:, None] * positions).sum(axis=0) / w.sum()


def fit_plane_pca(positions):
    """
    Fit a best-fit plane to a set of 3D points using PCA (SVD).

    Parameters
    ----------
    positions : array-like, shape (N, 3)
        Coordinates of points to be used to define the plane.

    Returns
    -------
    c : ndarray, shape (3,)
        Centroid of the input points (a point on the plane).
    n : ndarray, shape (3,)
        Unit normal vector to the fitted plane.
    a1 : ndarray, shape (3,)
        First in-plane unit axis (principal direction).
    a2 : ndarray, shape (3,)
        Second in-plane unit axis orthogonal to a1.

    Notes
    -----
    - The algorithm centers the points, performs SVD, and treats the first two
      right-singular vectors as in-plane directions and the third as the normal.
    - Ensures a consistent right-handed orientation for a1, a2, n.
    """
    c = centroid(positions)
    X = positions - c
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    a1, a2, n = Vt[0], Vt[1], Vt[2]
    if np.dot(np.cross(a1, a2), n) < 0:
        a2 = -a2
    a1 = a1 / np.linalg.norm(a1)
    a2 = a2 / np.linalg.norm(a2)
    n = n / np.linalg.norm(n)
    return c, n, a1, a2


def angle_between(u, v):
    """
    Return the unsigned angle in degrees between two vectors.

    Parameters
    ----------
    u, v : array-like, shape (3,)
        Input vectors.

    Returns
    -------
    float
        Angle in degrees in the range [0, 180].

    Notes
    -----
    - Vectors are normalized before computing the angle.
    - Uses numerical clipping to avoid domain errors in arccos.
    """
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    c = np.clip(np.dot(u, v), -1.0, 1.0)
    return np.degrees(np.arccos(c))


def signed_angle_in_plane(u, v, n_ref):
    """
    Compute the signed angle (degrees) from vector u to v within the plane
    orthogonal to n_ref, using right-hand-rule sign convention about n_ref.

    Parameters
    ----------
    u, v : array-like, shape (3,)
        Input vectors; they do not need to be already in-plane.
    n_ref : array-like, shape (3,)
        Reference normal vector defining the plane whose sign determines
        the positive rotation direction.

    Returns
    -------
    float
        Signed angle in degrees in range (-180, 180]. Returns 0.0 if either
        projected vector is (numerically) zero.

    Notes
    -----
    - Projects u and v into the plane orthogonal to n_ref, normalizes them,
      and computes atan2 of the sine and cosine components to get a stable
      signed result.
    """
    n_ref = n_ref / np.linalg.norm(n_ref)
    u = u - np.dot(u, n_ref) * n_ref
    v = v - np.dot(v, n_ref) * n_ref
    if np.linalg.norm(u) < 1e-12 or np.linalg.norm(v) < 1e-12:
        return 0.0
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    x = np.cross(u, v)
    s = np.clip(np.dot(x, n_ref), -1.0, 1.0)
    c = np.clip(np.dot(u, v), -1.0, 1.0)
    return np.degrees(np.arctan2(s, c))


def perp_and_slip(r_other, r_mid, n_mid, a1_mid, a2_mid):
    """
    Compute perpendicular distance and slip components between two reference points.

    Parameters
    ----------
    r_other : array-like, shape (3,)
        Position of the "other" fragment (top or bottom).
    r_mid : array-like, shape (3,)
        Position of the middle/reference fragment.
    n_mid : array-like, shape (3,)
        Unit normal vector of the middle plane.
    a1_mid, a2_mid : array-like, shape (3,)
        In-plane orthonormal axes for the middle plane.

    Returns
    -------
    d_perp_signed : float
        Signed perpendicular distance from r_mid to r_other along n_mid
        (positive if r_other is in the direction of n_mid).
    d_perp_abs : float
        Absolute value of the perpendicular distance.
    s_mag : float
        Magnitude of the slip vector projected into the middle plane.
    sx, sy : float
        Components of the slip vector along a1_mid and a2_mid respectively.

    Notes
    -----
    - Slip is defined by projecting the inter-centroid vector into the plane
      and decomposing onto the in-plane basis (a1_mid, a2_mid).
    """
    d = r_other - r_mid
    d_perp_signed = np.dot(d, n_mid)
    d_perp_abs = abs(d_perp_signed)
    s_vec = d - d_perp_signed * n_mid
    sx = np.dot(s_vec, a1_mid)
    sy = np.dot(s_vec, a2_mid)
    s_mag = np.sqrt(sx**2 + sy**2)
    return d_perp_signed, d_perp_abs, s_mag, sx, sy


def split_ep(struct):
    """
    Split a structure representation into element labels and position array.

    Parameters
    ----------
    struct : list of (str, ndarray)
        Output of parse_xyz: a list of (element, position) tuples.

    Returns
    -------
    E : ndarray of object dtype, shape (N,)
        Array of element symbols.
    P : ndarray, shape (N, 3)
        Stacked positions array.

    Example
    -------
    >>> E, P = split_ep(parsed_atoms)
    """
    E = np.array([e for e, _ in struct], dtype=object)
    P = np.vstack([p for _, p in struct])
    return E, P


# -------------------- Load files --------------------
# Add column lists required later when building DataFrames
plane_cols = [
    "d_perp_top",
    "d_perp_bottom",
    "slip_top",
    "slip_bottom",
    "slip_top_x",
    "slip_top_y",
    "slip_bottom_x",
    "slip_bottom_y",
    "tilt_top",
    "tilt_bottom",
    "twist_top",
    "twist_bottom",
]
com_cols = [
    "COMdist_top_middle",
    "COMdist_bottom_middle",
    "COMdist_top_bottom",
    "central_angle_COMs",
]

# Initialize unattached/sandwich/zigzag robustly to avoid NameError.
try:
    parser = argparse.ArgumentParser(
        description="Compare three PDI trimer geometries (top/middle/bottom). "
        "Provide three xyz files (unattached sandwich zigzag) as positional args to override defaults."
    )
    parser.add_argument(
        "files", nargs="*", help="three xyz files: unattached sandwich zigzag"
    )
    parser.add_argument(
        "-o", "--output-dir", help="override output directory", default=None
    )
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)

    if len(args.files) >= 3:
        unattached = parse_xyz(str(args.files[0]))
        sandwich = parse_xyz(str(args.files[1]))
        zigzag = parse_xyz(str(args.files[2]))
    else:
        # fall back to provided default file lists (prefer vacuum, then solvent)
        if len(vacuum_files) >= 3 and all(os.path.exists(p) for p in vacuum_files[:3]):
            unattached = parse_xyz(vacuum_files[0])
            sandwich = parse_xyz(vacuum_files[1])
            zigzag = parse_xyz(vacuum_files[2])
        elif len(solvent_files) >= 3 and all(
            os.path.exists(p) for p in solvent_files[:3]
        ):
            unattached = parse_xyz(solvent_files[0])
            sandwich = parse_xyz(solvent_files[1])
            zigzag = parse_xyz(solvent_files[2])
        else:
            raise FileNotFoundError(
                "No input files supplied and default file paths not found. "
                "Provide three xyz files as command-line arguments or ensure default paths exist."
            )
except Exception as e:
    logger.error("Error initializing input structures: %s", e)
    sys.exit(1)

E_un, P_un = split_ep(unattached)
E_sa, P_sa = split_ep(sandwich)
E_zi, P_zi = split_ep(zigzag)

# -------------------- User-specified indices --------------------
# UA_top_spec = "86-127,130-131,133-135,154-183" % PDI Cores + Bulky Quaternary Ammonium
# UA_middle_spec = "43-85,129,136-153,184-201" % PDI Cores + Bulky Quaternary Ammonium
# UA_bottom_spec = "1-42,128,132,202-237" % PDI Cores + Bulky Quaternary Ammonium
UA_top_spec = "86-118,121-125"  # Top PDI Core only
UA_middle_spec = "43-75,78-82"  # Middle PDI Core only
UA_bottom_spec = "1-33,36-40"  # Bottom PDI Core only

# SA_top_spec = "86-129,133-146,153,222-236" % PDI Cores + Bulky Quaternary Ammonium
# SA_middle_spec = "43-85,131,147-149,260-292" % PDI Cores + Bulky Quaternary Ammonium
# SA_bottom_spec = "1-42,130,132,150-152,170-184,201-212" % PDI Cores + Bulky Quaternary Ammonium
SA_top_spec = "86-118,122-126"  # Top PDI Core only
SA_middle_spec = "43-75,78-82"  # Middle PDI Core only
SA_bottom_spec = "1-33,36-40"  # Bottom PDI Core only

# ZI_top_spec = "85-127,130,198-200,202,215-225,257-259,263,276-289" % PDI Cores + Bulky Quaternary Ammonium
# ZI_middle_spec = "43-84,129,131,148-162,195-197,201,203-205,249-256" % PDI Cores + Bulky Quaternary Ammonium
# ZI_bottom_spec = "1-42,128,132-147,260-262,264-275,290-292" % PDI Cores + Bulky Quaternary Ammonium
ZI_top_spec = "85-117,120-124"  # Top PDI Core only
ZI_middle_spec = "43-75,78-82"  # Middle PDI Core only
ZI_bottom_spec = "1-33,36-40"  # Bottom PDI Core only

IDX = {
    "unattached": {
        "E": E_un,
        "P": P_un,
        "top": to_zero_based(UA_top_spec),
        "middle": to_zero_based(UA_middle_spec),
        "bottom": to_zero_based(UA_bottom_spec),
    },
    "sandwich": {
        "E": E_sa,
        "P": P_sa,
        "top": to_zero_based(SA_top_spec),
        "middle": to_zero_based(SA_middle_spec),
        "bottom": to_zero_based(SA_bottom_spec),
    },
    "zigzag": {
        "E": E_zi,
        "P": P_zi,
        "top": to_zero_based(ZI_top_spec),
        "middle": to_zero_based(ZI_middle_spec),
        "bottom": to_zero_based(ZI_bottom_spec),
    },
}

# -------------------- Analysis --------------------


def analyze(name, data):
    """
    Analyze three fragment groups (top, middle, bottom) for relative geometry.

    Parameters
    ----------
    name : str
        Label for the structure (e.g., 'unattached', 'sandwich', 'zigzag').
    data : dict
        Dictionary with keys:
            - "E": ndarray of element symbols for all atoms
            - "P": ndarray of positions for all atoms
            - "top", "middle", "bottom": lists/arrays of integer indices selecting
              atoms that belong to each fragment.

    Returns
    -------
    dict
        Dictionary containing computed metrics:
            - d_perp_top, d_perp_bottom : perpendicular distances (float)
            - slip_top, slip_bottom : in-plane slip magnitudes (float)
            - slip_top_x/y, slip_bottom_x/y : in-plane slip components (float)
            - tilt_top/bottom : angles between normals in degrees (float)
            - twist_top/bottom : signed twist angles in degrees (float)
            - COMdist_* : mass-weighted COM distances (float)
            - central_angle_COMs : angle between COM vectors (degrees)

    Notes
    -----
    - Uses centroid-based plane fits for each fragment to define planes and
      in-plane axes, then uses the middle fragment as the reference.
    - Mass-weighted COMs are computed using the global `masses` map.
    """
    E, P = data["E"], data["P"]
    it, im, ib = data["top"], data["middle"], data["bottom"]
    Pt, Et = P[it], E[it]
    Pm, Em = P[im], E[im]
    Pb, Eb = P[ib], E[ib]

    # Plane fit on centroids of core atoms (unweighted)
    ct, nt, a1t, a2t = fit_plane_pca(Pt)
    cm, nm, a1m, a2m = fit_plane_pca(Pm)
    cb, nb, a1b, a2b = fit_plane_pca(Pb)

    # Normal orientation consistency
    if np.dot(nt, nm) < 0:
        nt = -nt
    if np.dot(nb, nm) < 0:
        nb = -nb

    # Tilts and twists
    tilt_top = angle_between(nt, nm)
    tilt_bottom = angle_between(nb, nm)
    twist_top = signed_angle_in_plane(a1m, a1t, nm)
    twist_bottom = signed_angle_in_plane(a1m, a1b, nm)

    # Perpendicular distances + slip (use centroids)
    dtop_s, dtop, stop, sxt, syt = perp_and_slip(ct, cm, nm, a1m, a2m)
    dbot_s, dbot, sbot, sxb, syb = perp_and_slip(cb, cm, nm, a1m, a2m)

    # COM–COM summary (mass-weighted)
    cmt = com(Pt, Et)
    cmm = com(Pm, Em)
    cmb = com(Pb, Eb)
    d_tm = np.linalg.norm(cmt - cmm)
    d_bm = np.linalg.norm(cmb - cmm)
    d_tb = np.linalg.norm(cmt - cmb)
    v_tm = cmt - cmm
    v_bm = cmb - cmm
    central_angle = np.degrees(
        np.arccos(
            np.clip(
                np.dot(v_tm, v_bm) / (np.linalg.norm(v_tm) * np.linalg.norm(v_bm)),
                -1.0,
                1.0,
            )
        )
    )

    return {
        "d_perp_top": dtop,
        "d_perp_bottom": dbot,
        "slip_top": stop,
        "slip_top_x": sxt,
        "slip_top_y": syt,
        "slip_bottom": sbot,
        "slip_bottom_x": sxb,
        "slip_bottom_y": syb,
        "tilt_top": tilt_top,
        "tilt_bottom": tilt_bottom,
        "twist_top": twist_top,
        "twist_bottom": twist_bottom,
        "COMdist_top_middle": d_tm,
        "COMdist_bottom_middle": d_bm,
        "COMdist_top_bottom": d_tb,
        "central_angle_COMs": central_angle,
    }


# -------------------- Process datasets (vacuum + solvent) --------------------
labels = ["unattached", "sandwich", "zigzag"]
datasets = [("vacuum", vacuum_files), ("solvent", solvent_files)]

for tag, files in datasets:
    if len(files) != 3:
        print(f"Skipping {tag}: expected 3 files, got {len(files)}")
        continue

    # parse the three files in fixed order (PDI-Free, PDI-Sandwich, PDI-Zigzag)
    structs = [parse_xyz(fp) for fp in files]
    E_list = []
    P_list = []
    for s in structs:
        E, P = split_ep(s)
        E_list.append(E)
        P_list.append(P)

    # build IDX using the already-defined index specification strings
    IDX = {
        labels[0]: {
            "E": E_list[0],
            "P": P_list[0],
            "top": to_zero_based(UA_top_spec),
            "middle": to_zero_based(UA_middle_spec),
            "bottom": to_zero_based(UA_bottom_spec),
        },
        labels[1]: {
            "E": E_list[1],
            "P": P_list[1],
            "top": to_zero_based(SA_top_spec),
            "middle": to_zero_based(SA_middle_spec),
            "bottom": to_zero_based(SA_bottom_spec),
        },
        labels[2]: {
            "E": E_list[2],
            "P": P_list[2],
            "top": to_zero_based(ZI_top_spec),
            "middle": to_zero_based(ZI_middle_spec),
            "bottom": to_zero_based(ZI_bottom_spec),
        },
    }

    # run analysis and build DataFrames (same columns/rounding as before)
    results = {name: analyze(name, data) for name, data in IDX.items()}

    plane_df = pd.DataFrame(results).T[plane_cols]
    com_df = pd.DataFrame(results).T[com_cols]
    delta_df = plane_df.subtract(plane_df.loc["unattached"], axis="columns").loc[
        ["sandwich", "zigzag"]
    ]  # type: ignore

    plane_df_r = plane_df.copy().round(
        {
            "d_perp_top": 3,
            "d_perp_bottom": 3,
            "slip_top": 3,
            "slip_bottom": 3,
            "slip_top_x": 3,
            "slip_top_y": 3,
            "slip_bottom_x": 3,
            "slip_bottom_y": 3,
            "tilt_top": 1,
            "tilt_bottom": 1,
            "twist_top": 1,
            "twist_bottom": 1,
        }
    )
    com_df_r = com_df.copy().round(
        {
            "COMdist_top_middle": 3,
            "COMdist_bottom_middle": 3,
            "COMdist_top_bottom": 3,
            "central_angle_COMs": 1,
        }
    )
    delta_df_r = delta_df.copy().round(
        {
            "d_perp_top": 3,
            "d_perp_bottom": 3,
            "slip_top": 3,
            "slip_bottom": 3,
            "slip_top_x": 3,
            "slip_top_y": 3,
            "slip_bottom_x": 3,
            "slip_bottom_y": 3,
            "tilt_top": 1,
            "tilt_bottom": 1,
            "twist_top": 1,
            "twist_bottom": 1,
        }
    )

    # Print concise summaries
    print(
        f"\n[{tag.upper()}] Plane-based metrics (centroid planes; middle as reference)\n"
    )
    print(plane_df_r.to_string())
    print(f"\n[{tag.upper()}] COM–COM summary (mass-weighted)\n")
    print(com_df_r.to_string())
    print(
        f"\n[{tag.upper()}] Δ (Sandwich/Zigzag) relative to Unattached — Plane metrics\n"
    )
    print(delta_df_r.to_string())

    # Save CSVs with tag in filename
    plane_csv = os.path.join(output_dir, f"{tag}_plane_metrics.csv")
    com_csv = os.path.join(output_dir, f"{tag}_com_summary.csv")
    delta_csv = os.path.join(output_dir, f"{tag}_deltas_vs_unattached.csv")
    all_csv = os.path.join(output_dir, f"{tag}_all_metrics.csv")

    plane_df.to_csv(plane_csv, index=True)
    com_df.to_csv(com_csv, index=True)
    delta_df.to_csv(delta_csv, index=True)
    pd.concat([plane_df, com_df], axis=1).to_csv(all_csv, index=True)

    print(f"CSV files written for {tag}:", plane_csv, com_csv, delta_csv, all_csv)
