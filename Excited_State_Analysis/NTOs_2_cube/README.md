Great 🚀 Let’s update the `README.md` to reflect the fixes and improvements from the latest script.
This version makes it **super clear** about `.mfwn` vs `.mwfn`, shows the new **error-proof filename handling**, and updates the examples.

---

```markdown
# 🌀 Multiwfn Batch Orbital CUBE Generator

🚀 **Automate Multiwfn orbital wavefunction CUBE file generation** for multiple excited states in a single command — no more overwriting `orbital.cub` and no tedious manual inputs!  

This script:
- Runs Multiwfn in **fully non-interactive mode** using your exact menu sequence.
- Renames the generated `orbital.cub` for each state so they never overwrite each other.
- Supports **state ranges** (`1-4`) and **lists** (`1 3 5-7`).
- Organizes logs and outputs neatly into folders.
- ✅ Robust against weird input ranges (`10,12,15-18`), falling back to safe filenames.

---

## 📜 Features

✨ **What this script does:**
- 🔢 Loops over any number of states.
- 📂 Creates organized output directories (`cube_out/` for `.cub` files, `logs/` for run logs).
- 🛡 Prevents file overwrites by renaming each output to:

```

S<state>*orbs\<start\_padded6>*\<end\_padded3>.cub

````

Example:  
`S3_orbs000585_589.cub` → State 3, orbitals 585–589.

- 🧠 Automatically parses the `ORBITAL_RANGE` to determine the filename suffix.
- ⚡ Supports parallel execution to speed things up.
- 🪄 Falls back to safe names if `ORBITAL_RANGE` is complex (`10,12,15-18` → `S1_orbs10_12_15_18_X.cub`).

---

## 📦 Installation

Clone this repository:

```bash
git clone https://github.com/yourusername/multiwfn-cube-generator.git
cd multiwfn-cube-generator
````

Make the script executable:

```bash
chmod +x generate_orbital_cubes.sh
```

Ensure **Multiwfn** is installed and available in your `PATH`, or set the path via `MULTIWFN_BIN`.

---

## ⚙️ Configuration

You can control behavior via **environment variables**:

| Variable        | Default    | Description                                                         |
| --------------- | ---------- | ------------------------------------------------------------------- |
| `MULTIWFN_BIN`  | `multiwfn` | Path to Multiwfn executable                                         |
| `STATE_PREFIX`  | `S`        | Prefix for input files (`S<state>.mfwn` or `.mwfn`)                 |
| `INPUT_EXT`     | `.mfwn`    | Extension of Multiwfn input files (use `.mwfn` if that’s your case) |
| `ORBITAL_RANGE` | `584-589`  | Orbital(s) to process; single range or list                         |
| `OUTDIR`        | `cube_out` | Directory for `.cub` output files                                   |
| `LOGDIR`        | `logs`     | Directory for log files                                             |
| `JOBS`          | `1`        | Parallel jobs for multi-state processing                            |
| `DRY_RUN`       | `0`        | Set to `1` to preview without running                               |

---

## 🖥 Usage

### Basic

Generate cubes for **states 1 to 4** with the default orbital range (`584-589`):

```bash
./generate_orbital_cubes.sh 1-4
```

Output:

```
cube_out/S1_orbs000584_589.cub
cube_out/S2_orbs000584_589.cub
cube_out/S3_orbs000584_589.cub
cube_out/S4_orbs000584_589.cub
```

---

### Using `.mwfn` inputs

If your files are `S1.mwfn`, `S2.mwfn`, etc., set the extension:

```bash
INPUT_EXT=".mwfn" ./generate_orbital_cubes.sh 1
```

---

### Custom Orbital Range

Generate cubes for orbitals `600–605` for **states 2 and 5**:

```bash
ORBITAL_RANGE="600-605" ./generate_orbital_cubes.sh 2 5
```

---

### Parallel Execution

Run **4 states in parallel** (faster if you have CPU cores to spare):

```bash
JOBS=4 ./generate_orbital_cubes.sh 1-4
```

---

### Dry Run

Preview what will happen without actually running Multiwfn:

```bash
DRY_RUN=1 INPUT_EXT=".mwfn" ./generate_orbital_cubes.sh 1
```

---

## 🔍 How It Works

1. **Reads the state list/range** from your input arguments.
2. **Expands ranges** (e.g., `1-3` → `1 2 3`).
3. For each state:

   * Builds the **exact Multiwfn input sequence**:

     ```
     200
     3
     <ORBITAL_RANGE>
     3
     2
     0
     q
     ```
   * Runs Multiwfn on `S<state>.mfwn` (or `.mwfn`).
   * Renames `orbital.cub` → `S<state>_orbs<start6>_<end3>.cub`.
   * Saves logs in `logs/state_<state>.log`.
   * If parsing fails, safely falls back to filenames like `S1_orbs10_12_15_18_X.cub`.

---

## 📁 Example Directory Layout

```
cube_out/
├── S1_orbs000584_589.cub
├── S2_orbs000584_589.cub
├── S3_orbs000584_589.cub
└── S4_orbs000584_589.cub

logs/
├── state_1.log
├── state_2.log
├── state_3.log
└── state_4.log

S1.mwfn
S2.mwfn
S3.mwfn
S4.mwfn
generate_orbital_cubes.sh
```

---

## 🖼 Process Overview

Below are **two ways** to visualize how this script works:

---

### 📊 Mermaid Flowchart (renders on GitHub)

```mermaid
flowchart LR
    A[📂 Input: S*.mwfn or S*.mfwn] --> B{📝 State list/range}
    B --> C[🔄 Expand ranges]
    C --> D[🛠 Build Multiwfn menu payload]
    D --> E[⚙️ Run Multiwfn\n200 → 3 → <ORBITAL_RANGE> → 3 → 2 → 0 → q]
    E --> F[📄 orbital.cub]
    F --> G[✏️ Rename file\nS<state>_orbs<start6>_<end3>.cub]
    G --> H[📂 cube_out/]
    E --> L[🗒 logs/state_<state>.log]

    %% Parallel processing branch
    subgraph P[⚡ Parallel Execution (JOBS > 1)]
        direction LR
        P1[Worker #1: state 1]
        P2[Worker #2: state 2]
        P3[Worker #3: state 3]
        P4[Worker #4: state 4]
    end
    C --> P
    P1 --> E
    P2 --> E
    P3 --> E
    P4 --> E
```

---

### 🖥 ASCII Diagram (works everywhere)

```text
                                🌀 Multiwfn Batch Orbital CUBE Generator

Inputs                                Orchestration                         Processing                          Outputs
======                                =============                         ==========                          =======
                                                                                                                 
  S1.mwfn                                                                                                         cube_out/
  S2.mwfn            +------------------------------+                        +-----------------------+            ├─ S1_orbs000584_589.cub
  S3.mwfn   ───────▶ | generate_orbital_cubes.sh    |   for each state s ──▶ | Multiwfn (non-interactive) | ─┐    ├─ S2_orbs000584_589.cub
  S4.mwfn            |   • expands ranges           |                        |  using exact menu input:   |  │    └─ S3_orbs000584_589.cub
                     |   • builds menu payload      |                        |                             |  │
State list/range     |   • runs sequential/parallel |                        |   200                       |  │    logs/
( e.g., "1 3 5-7" )  +------------------------------+                        |   3                         |  │    ├─ state_1.log
                                                                            |   <ORBITAL_RANGE>           |  │    ├─ state_2.log
                                                                            |   3                         |  │    ├─ state_3.log
                                                                            |   2                         |  │    └─ state_4.log
                                                                            |   0                         |  │
                                                                            |   q                         |  │
                                                                            +-----------------------------+  │
                                                                                                              │
                                                                                                              ▼
                                                                                                    Generated file:
                                                                                                         ./orbital.cub
                                                                                                              │
                                                                                                              │  rename + move
                                                                                                              ▼
                                                                                                   +--------------------------+
                                                                                                   |  "${OUTDIR}/S${s}_orbs  |
                                                                                                   |   ${start6}_${end3}.cub"|
                                                                                                   +--------------------------+
```

---

## 🏆 License

This script is released under the [MIT License](LICENSE).

---

## 🧪 Example Run

```bash
$ DRY_RUN=1 INPUT_EXT=".mwfn" ./generate_orbital_cubes.sh 1
[state 1] Running Multiwfn on S1.mwfn -> S1_orbs000584_589.cub
-----BEGIN MULTIWFN INPUT (state 1)-----
200
3
584-589
3
2
0
q
-----END MULTIWFN INPUT-----
[state 1] Would move ./orbital.cub -> cube_out/S1_orbs000584_589.cub
```
Perfect 🙌 — let’s add a **Troubleshooting** section to the `README.md`.
This helps users debug common issues like missing files, wrong extensions, Multiwfn path, etc.

Here’s the updated **tail end of the README** with the new section:

---

````markdown
---

## 🏆 License
This script is released under the [MIT License](LICENSE).

---

## 🧪 Example Run
```bash
$ DRY_RUN=1 INPUT_EXT=".mwfn" ./generate_orbital_cubes.sh 1
[state 1] Running Multiwfn on S1.mwfn -> S1_orbs000584_589.cub
-----BEGIN MULTIWFN INPUT (state 1)-----
200
3
584-589
3
2
0
q
-----END MULTIWFN INPUT-----
[state 1] Would move ./orbital.cub -> cube_out/S1_orbs000584_589.cub
````

---

## 🛠 Troubleshooting

### ❌ `Missing input file: S1.mfwn`

* By default the script expects `.mwfn` files.
* If your files are `.mfwn`, run with:

  ```bash
  INPUT_EXT=".mfwn" ./generate_orbital_cubes.sh 1
  ```

---

### ❌ `Error: Multiwfn not found`

* Ensure Multiwfn is installed and in your `PATH`.
* Or provide the full path:

  ```bash
  MULTIWFN_BIN="/path/to/Multiwfn" ./generate_orbital_cubes.sh 1
  ```

---

### ❌ `Expected orbital.cub not found`

* This means Multiwfn didn’t produce `orbital.cub`.
* Check the log for that state under `logs/state_<state>.log`.
* Common causes:

  * Wrong menu inputs (verify `ORBITAL_RANGE` is valid).
  * Missing/invalid wavefunction in the `.mfwn`/`.mwfn` file.

---

### ❌ Script fails with `invalid option` in `printf`

* This was a common issue when payloads or filenames began with `-`.
* ✅ Already fixed: the script now uses `printf --` to prevent option parsing.
* If you still see it, please report with your `ORBITAL_RANGE` value.

---

### ⚡ Multiwfn runs but outputs are overwritten

* Not possible with this script anymore: each state is renamed immediately.
* Files follow the pattern:

  ```
  S<state>_orbs<start6>_<end3>.cub
  ```

  Example: `S3_orbs000584_589.cub`.

---

### 📂 My output filenames look weird (e.g. `S1_orbs10_12_15_18_X.cub`)

* This happens when `ORBITAL_RANGE` is **not a simple range** (e.g., `10,12,15-18`).
* The script falls back to a safe filename that includes all values separated by underscores.
* ✅ CUBE data is still correct.

---

### 💡 General tips

* Always check logs under `logs/state_<state>.log` if something fails.
* Use `DRY_RUN=1` to preview what the script *would* do without touching files.
* Run with `JOBS=N` to speed up large state lists (if CPU allows).
* Make sure you have write permissions in the working directory (the script renames/moves files).

---

🌟 **With this script + troubleshooting guide, you’ll never lose an orbital CUBE file again!**

```

---

Would you like me to also add a **badge-style quick start** at the very top of the README (like “✅ Works with `.mwfn` and `.mfwn` | ⚡ Parallel | 🛡 No overwrites”), to make it pop for GitHub visitors?
```
