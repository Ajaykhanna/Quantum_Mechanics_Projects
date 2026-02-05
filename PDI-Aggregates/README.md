# PDI Trimer Structural Analysis Script

This repository contains the Python script `structural_comparison_3D_PDIs_production.py`, designed to perform a rigorous structural analysis of PDI (perylene diimide) trimer aggregates. It compares geometrical parameters across three distinct assembly types:

1. **u-PDI3** (`unattached`): Non-covalent, free assembly (Reference: `Trimer_Starting_Materials`).
2. **s-PDI3** (`sandwich`): Folded "foldamer" assembly (Reference: `Trimer_Tethered`).
3. **t-PDI3** (`zigzag`/`stapled`): Linear/Tethered assembly (Reference: `Trimer_Tethered_Linear`).

## 1. Rationale: Why Plane-Based Metrics?

Standard Center-of-Mass (COM) distance metrics treats molecules as 0D points ($r_{COM}$). While useful for coarse approximations, simple COM metrics fail to capture the nuances of $\pi$-$\pi$ interactions critical for determining optoelectronic properties in PDI aggregates.

**Limitations of Simple COM Metrics:**

* **Ambiguity**: A COM distance of $3.5 \AA$ could represent a perfect face-to-face stack (strong coupling) or a T-shaped perpendicular arrangement (zero coupling).
* **Lack of Orientation**: It ignores the "Slip" (offset in the conjugation plane) vs. "Rise" (interplanar distance) distinction.
* **Rotational Blindness**: It cannot quantify **Twist** (rotation around the stacking axis) or **Tilt** (non-parallelism of planes), which severely impact electronic orbital overlap integral ($J$).

**Solution employed by this script:**
This procedure treats each PDI core as a **finite plane**. By defining a local coordinate system for the central PDI unit, we can decompose the position of the neighboring units (Top and Bottom) into chemically meaningful components:

* **Perpendicular Distance ($d_{\perp}$)**: The true $\pi$-stacking distance.
* **Slip ($s$)**: The displacement along the molecular plane (long/short axis offset).
* **Twist ($\phi$)**: The rotational angle determining the "helical" nature of the stack.
* **Tilt ($\theta$)**: The deviation from perfect parallelism.

---

## 2. Script Overview

### Functionality

The script processes XYZ coordinate files for the three assemblies in distinct environments (e.g., Vacuum and Solvent). It extracts the Top, Middle, and Bottom PDI cores using specific atom indices, fits a plane to each core, and calculates geometries relative to the **Middle Core** (fixed frame of reference).

### Inputs

The script requires XYZ files for the following structures. It defaults to hardcoded paths but accepts command-line arguments.

* `unattached` XYZ (u-PDI3)
* `sandwich` XYZ (s-PDI3)
* `zigzag` XYZ (t-PDI3)

### Outputs

The script generates CSV files in a date-stamped folder (e.g., `./February_05_2026/`) containing:

* `_plane_metrics.csv`: Detailed slip, tilt, and twist data.
* `_com_summary.csv`: Mass-weighted COM distances.
* `_deltas_vs_unattached.csv`: Differences between the tethered structures and the free assembly.

---

## 3. Methodology & Equations

The script follows a linear pipeline: **Parse** $\rightarrow$ **Split Cores** $\rightarrow$ **Fit Planes** $\rightarrow$ **Project Vectors** $\rightarrow$ **Compute Metrics**.

### Step 1: Plane Fitting (Principal Component Analysis)

For each PDI core (Top, Middle, Bottom), we define a best-fit plane using the positions of its atoms ($\mathbf{r}_i$). This is done via Singular Value Decomposition (SVD) of the centered coordinates.

**Centroid ($\mathbf{c}$):**
$$ \mathbf{c} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{r}_i $$

**SVD:**
We construct the centered matrix $\mathbf{X} = \mathbf{r}_i - \mathbf{c}$. We perform SVD such that $\mathbf{X} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T$.
The rows of $\mathbf{V}^T$ define the intrinsic molecular axes:

* $\mathbf{a}_1$: Major axis (longest dimension of the PDI core).
* $\mathbf{a}_2$: Minor axis (width of the PDI core).
* $\mathbf{n}$: Normal vector (perpendicular to the $\pi$-system).

*Python Implementation (`fit_plane_pca`):*

```python
c = centroid(positions)
X = positions - c
U, S, Vt = np.linalg.svd(X)
a1, a2, n = Vt[0], Vt[1], Vt[2] # Principal axes and normal
```

### Step 2: Defining the Reference Frame

All metrics are calculated relative to the **Middle Core**. Meaning, we define the Middle Core's plane as the $xy$-plane ($z = \mathbf{n}_{mid}$).

* Origin: $\mathbf{c}_{mid}$
* Z-axis: $\mathbf{n}_{mid}$
* X-axis: $\mathbf{a}_{1, mid}$ (Long axis)
* Y-axis: $\mathbf{a}_{2, mid}$ (Short axis)

### Step 3: Calculation of Structural Parameters

#### A. Perpendicular Distance ($d_{\perp}$) and Slip ($s$)

The vector connecting the Middle centroid to the Top centroid is $\mathbf{d} = \mathbf{c}_{top} - \mathbf{c}_{mid}$.

**Perpendicular Distance:**
The projection of $\mathbf{d}$ onto the normal vector $\mathbf{n}_{mid}$:
$$ d_{\perp} = \mathbf{d} \cdot \mathbf{n}_{mid} $$

**Slip Vector ($\mathbf{s}$):**
The remaining component of the vector after removing the vertical rise:
$$ \mathbf{s}_{vec} = \mathbf{d} - d_{\perp} \mathbf{n}_{mid} $$
The magnitude is the total slip:
$$ s = \| \mathbf{s}_{vec} \| $$
The slip is further decomposed into X (long-axis) and Y (short-axis) displacements:
$$ s_x = \mathbf{s}_{vec} \cdot \mathbf{a}_{1, mid} $$
$$ s_y = \mathbf{s}_{vec} \cdot \mathbf{a}_{2, mid} $$

*Python Implementation (`perp_and_slip`):*

```python
d = r_other - r_mid
d_perp_signed = np.dot(d, n_mid)   # Vertical Rise
s_vec = d - d_perp_signed * n_mid  # Vector in the plane
s_mag = np.sqrt(sx**2 + sy**2)     # Total Slip
```

#### B. Tilt Angle ($\theta$)

The angle between the normal vectors of the Top and Middle planes. A tilt of $0^\circ$ implies perfectly parallel plates.
$$ \theta = \arccos( \mathbf{n}_{top} \cdot \mathbf{n}_{mid} ) $$

*Python Implementation (`angle_between`):*

```python
c = np.clip(np.dot(u, v), -1.0, 1.0) # Numerical stability
angle = np.degrees(np.arccos(c))
```

#### C. Twist Angle ($\phi$)

The rotation of the neighbor molecule relative to the reference, specifically around the stacking axis. This is calculated as the signed angle between the major axis of the Middle ($\mathbf{a}_{1, mid}$) and the Top ($\mathbf{a}_{1, top}$), projected onto the reference plane.

$$ \phi = \text{atan2}( (\mathbf{a}_{1, mid} \times \mathbf{a}_{1, top}) \cdot \mathbf{n}_{mid} , \mathbf{a}_{1, mid} \cdot \mathbf{a}_{1, top} ) $$

*Python Implementation (`signed_angle_in_plane`):*

```python
x = np.cross(u, v)
s = np.dot(x, n_ref) # Sine component
c = np.dot(u, v)     # Cosine component
angle = np.degrees(np.arctan2(s, c))
```

---

## 4. Usage

### Prerequisites

* Python 3.x
* `numpy`, `pandas`

### Running the Script

Run the script directly. It will attempt to look for default file paths hardcoded in the script, or you can provide paths via command line arguments.

**Using default paths:**

```bash
python structural_comparison_3D_PDIs_production.py
```

**Using custom files:**

```bash
python structural_comparison_3D_PDIs_production.py path/to/u-PDI3.xyz path/to/s-PDI3.xyz path/to/t-PDI3.xyz
```

### Interpretation of Results

* **`d_perp`**: Distance between planes. Typical $\pi$-stack is $\approx 3.4 \AA$.
* **`slip`**: Lateral geometric offset. Large slip indicates offset stacking (J-aggregate like structural features). Small slip indicate H-aggregate like features.
* **`twist`**: Rotational offset. Values near $0^\circ$ or $180^\circ$ indicate co-facial alignment.

## 5. Example Output

Below is an indicative output from terminal execution, showing metrics for both Vacuum and Solvent environments.

```text
[VACUUM] Plane-based metrics (centroid planes; middle as reference)

            d_perp_top  d_perp_bottom  slip_top  slip_bottom  slip_top_x  slip_top_y  slip_bottom_x  slip_bottom_y  tilt_top  tilt_bottom  twist_top  twist_bottom
unattached       3.434          3.502     0.661        1.691       0.531       0.394         -1.615          0.502       0.8          3.3     -144.7         -34.4
sandwich         3.308          3.314     0.862        1.067       0.814       0.284          0.740         -0.769       0.9          7.3     -151.4         -43.7
zigzag           3.427          3.413     0.577        1.659       0.504      -0.280          1.587          0.486       1.6          1.3      -33.9        -146.0

[VACUUM] COM–COM summary (mass-weighted)

            COMdist_top_middle  COMdist_bottom_middle  COMdist_top_bottom  central_angle_COMs
unattached               3.496                  3.905               7.277               159.0
sandwich                 3.422                  3.461               6.687               152.6
zigzag                   3.484                  3.783               6.963               146.7

[VACUUM] Δ (Sandwich/Zigzag) relative to Unattached — Plane metrics

          d_perp_top  d_perp_bottom  slip_top  slip_bottom  slip_top_x  slip_top_y  slip_bottom_x  slip_bottom_y  tilt_top  tilt_bottom  twist_top  twist_bottom
sandwich      -0.126         -0.188     0.201       -0.623       0.283      -0.111          2.355         -1.271       0.1          4.0       -6.6          -9.3
zigzag        -0.007         -0.089    -0.084       -0.031      -0.026      -0.675          3.201         -0.016       0.8         -2.0      110.8        -111.6
CSV files written for vacuum: ./February_05_2026\vacuum_plane_metrics.csv ./February_05_2026\vacuum_com_summary.csv ./February_05_2026\vacuum_deltas_vs_unattached.csv ./February_05_2026\vacuum_all_metrics.csv

[SOLVENT] Plane-based metrics (centroid planes; middle as reference)

            d_perp_top  d_perp_bottom  slip_top  slip_bottom  slip_top_x  slip_top_y  slip_bottom_x  slip_bottom_y  tilt_top  tilt_bottom  twist_top  twist_bottom
unattached       3.239          3.323     1.216        0.278       1.006      -0.683          0.276          0.026       2.4          0.7      140.0          36.8
sandwich         3.256          3.259     0.261        0.324       0.041      -0.258         -0.308         -0.101       1.4          2.9      -32.6          33.0
zigzag           3.328          3.245     0.785        0.160      -0.683      -0.387          0.148         -0.061       3.1          0.9     -142.6         -31.7

[SOLVENT] COM–COM summary (mass-weighted)

            COMdist_top_middle  COMdist_bottom_middle  COMdist_top_bottom  central_angle_COMs
unattached               3.423                  3.329               6.595               155.3
sandwich                 3.240                  3.264               6.488               172.1
zigzag                   3.411                  3.220               6.597               168.2

[SOLVENT] Δ (Sandwich/Zigzag) relative to Unattached — Plane metrics

          d_perp_top  d_perp_bottom  slip_top  slip_bottom  slip_top_x  slip_top_y  slip_bottom_x  slip_bottom_y  tilt_top  tilt_bottom  twist_top  twist_bottom
sandwich       0.017         -0.064    -0.955        0.046      -0.965       0.425         -0.584         -0.127      -1.0          2.2     -172.7          -3.8
zigzag         0.089         -0.078    -0.431       -0.117      -1.689       0.296         -0.128         -0.087       0.7          0.1     -282.7         -68.5
CSV files written for solvent: ./February_05_2026\solvent_plane_metrics.csv ./February_05_2026\solvent_com_summary.csv ./February_05_2026\solvent_deltas_vs_unattached.csv ./February_05_2026\solvent_all_metrics.csv
```
