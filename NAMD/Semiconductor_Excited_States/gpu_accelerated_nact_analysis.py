import numpy as np
import matplotlib.pyplot as plt
import argparse
import logging
import os
import csv
from tqdm import tqdm
from multiprocessing import Pool

# GPU Acceleration Check
try:
    import cupy as cp
    from cupyx.scipy.ndimage import gaussian_filter1d as gpu_gaussian

    HAS_CUDA = cp.cuda.runtime.getDeviceCount() > 0
except:
    HAS_CUDA = False
    from scipy.ndimage import gaussian_filter1d as cpu_gaussian


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def apply_smoothing(data, sigma):
    if HAS_CUDA:
        gpu_data = cp.array(data, dtype=cp.float32)
        return cp.asnumpy(gpu_gaussian(gpu_data, sigma=sigma))
    return cpu_gaussian(data, sigma=sigma)


def worker(args_tuple):
    indices, base_dir, pairs, states = args_tuple
    batch = []
    for idx in indices:
        n_p, p_p = os.path.join(base_dir, f"frame_{idx}", "nact.out"), os.path.join(
            base_dir, f"frame_{idx}", "pes.out"
        )
        if not (os.path.exists(n_p) and os.path.exists(p_p)):
            continue
        try:
            n_d, p_d = np.loadtxt(n_p, ndmin=2), np.loadtxt(p_p, ndmin=2)
            n_s = int(np.sqrt(n_d.size - 1))
            n_mat = n_d[0, 1:].reshape(n_s, n_s)
            # Row: [idx, PES_S0...S_n, NACT_pair1...pair_n]
            row = (
                [idx]
                + [p_d[0, s + 1] for s in states]
                + [n_mat[p1, p2] for p1, p2 in pairs]
            )
            batch.append(row)
        except:
            continue
    return np.array(batch) if batch else None


def run_analysis(args):
    setup_logging()
    logging.info(f"CUDA: {HAS_CUDA} | Cores: {args.cores} | Target: {args.end} frames")

    # 1-indexed Logic (S1 = index 1 in matrix, col 2 in PES)
    tracked_pairs = []
    if args.ref_state > 1:
        tracked_pairs.append(tuple(sorted((args.ref_state, args.ref_state - 1))))
    curr = args.ref_state + 1
    while len(tracked_pairs) < args.total_pairs:
        tracked_pairs.append(tuple(sorted((args.ref_state, curr))))
        curr += 1
    tracked_pairs = sorted(tracked_pairs)
    tracked_states = sorted(list(set([s for p in tracked_pairs for s in p])))

    # Parallel Loading
    all_indices = list(range(args.start, args.end + 1, args.step))
    indices_split = np.array_split(all_indices, args.cores * 4)
    worker_args = [
        (c.tolist(), args.dir, tracked_pairs, tracked_states) for c in indices_split
    ]

    all_data = []
    with Pool(processes=args.cores) as pool:
        for result in tqdm(
            pool.imap(worker, worker_args), total=len(worker_args), desc="Loading"
        ):
            if result is not None:
                all_data.append(result)

    if not all_data:
        return
    full_data = np.vstack(all_data)
    full_data = full_data[full_data[:, 0].argsort()]

    frames = full_data[:, 0]
    n_pes = len(tracked_states)
    pes_dict = {s: full_data[:, i + 1] for i, s in enumerate(tracked_states)}
    nact_dict = {p: full_data[:, i + 1 + n_pes] for i, p in enumerate(tracked_pairs)}

    # Signal Processing
    phase_mat, prox_mat = [], []
    for p in tracked_pairs:
        # Phase Polarization
        phase_mat.append(apply_smoothing(np.sign(nact_dict[p]), args.sigma))

        # CI Proximity: 1.0 at gap=0, 0.0 at gap=threshold
        gap = np.abs(pes_dict[p[0]] - pes_dict[p[1]])
        prox = np.clip(1.0 - (gap / args.gap_threshold), 0, 1)
        prox_mat.append(prox)

    # Export CI Log
    ci_file = args.out.replace(".png", "_ci_log.csv")
    with open(ci_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Frame", "Pair", "Gap_eV"])
        for s1, s2 in tracked_pairs:
            gap = np.abs(pes_dict[s1] - pes_dict[s2])
            ci_idxs = np.where(gap < args.gap_threshold)[0]
            for idx in ci_idxs:
                writer.writerow([int(frames[idx]), f"S{s1}-S{s2}", f"{gap[idx]:.4f}"])

    # Visualizing with restored Legends and Colorbars
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1.5, 1.2], hspace=0.15)

    ax_pes = fig.add_subplot(gs[0])
    ax_phase = fig.add_subplot(gs[1], sharex=ax_pes)
    ax_ci = fig.add_subplot(gs[2], sharex=ax_pes)

    # 1. PES Line Plot
    cmap = plt.colormaps.get_cmap("tab10")
    for i, s in enumerate(tracked_states):
        ax_pes.plot(
            frames, pes_dict[s], label=f"S{s}", lw=0.8, alpha=0.6, color=cmap(i % 10)
        )
    ax_pes.legend(loc="upper right", ncol=len(tracked_states), frameon=True)
    ax_pes.set_ylabel("Energy (eV)", fontweight="bold")
    ax_pes.set_title(
        f"High-Density Trajectory Analysis (Ref: S{args.ref_state})",
        fontsize=15,
        fontweight="bold",
    )

    # 2. Phase Heatmap
    im_p = ax_phase.imshow(
        phase_mat,
        aspect="auto",
        cmap="RdBu",
        vmin=-1,
        vmax=1,
        extent=[min(frames), max(frames), len(tracked_pairs) - 0.5, -0.5],
    )
    ax_phase.set_yticks(range(len(tracked_pairs)))
    ax_phase.set_yticklabels(
        [f"S{p[0]}-S{p[1]}" for p in tracked_pairs], fontweight="bold"
    )
    ax_phase.set_ylabel("Phase Pol.", fontweight="bold")
    plt.colorbar(im_p, ax=ax_phase, pad=0.01, label="Sign Consistency")

    # 3. CI Proximity Heatmap
    im_c = ax_ci.imshow(
        prox_mat,
        aspect="auto",
        cmap="magma",
        vmin=0,
        vmax=1,
        extent=[min(frames), max(frames), len(tracked_pairs) - 0.5, -0.5],
    )
    ax_ci.set_ylabel("CI Prox.", fontweight="bold")
    ax_ci.set_yticks(range(len(tracked_pairs)))
    ax_ci.set_yticklabels([f"S{p[0]}-S{p[1]}" for p in tracked_pairs], fontsize=8)
    plt.colorbar(
        im_c, ax=ax_ci, pad=0.01, label=f"Near-Crossing (<{args.gap_threshold}eV)"
    )

    ax_ci.set_xlabel("Frame Number (Configuration Index)", fontweight="bold")

    plt.savefig(args.out, dpi=300, bbox_inches="tight")
    logging.info(f"Done. Output: {args.out} | Log: {ci_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100000)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--ref_state", type=int, default=1)
    parser.add_argument("--total_pairs", type=int, default=3)
    parser.add_argument("--cores", type=int, default=16)
    parser.add_argument("--sigma", type=float, default=250.0)
    parser.add_argument("--gap_threshold", type=float, default=0.1)
    parser.add_argument("--out", type=str, default="trajectory_analysis.png")
    run_analysis(parser.parse_args())
