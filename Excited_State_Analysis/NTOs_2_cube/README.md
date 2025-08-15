# 🌀 Multiwfn Batch Orbital CUBE Generator

🚀 **Automate Multiwfn orbital wavefunction CUBE file generation** for multiple excited states in a single command — no more overwriting `orbital.cub` and no tedious manual inputs!  

This script:

- Runs Multiwfn in **fully non-interactive mode** using your exact menu sequence.
- Renames the generated `orbital.cub` for each state so they never overwrite each other.
- Supports **state ranges** (`1-4`) and **lists** (`1 3 5-7`).
- Organizes logs and outputs neatly into folders.

---

## 📜 Features

✨ **What this script does:**

- 🔢 Loops over any number of states.
- 📂 Creates organized output directories (`cube_out/` for `.cub` files, `logs/` for run logs).
- 🛡 Prevents file overwrites by renaming each output to:

Example:  
`S3_orbs000585_589.cub` → State 3, orbitals 585–589.

- 🧠 Automatically parses the `ORBITAL_RANGE` to determine the filename suffix.
- ⚡ Supports parallel execution to speed things up.

---

## 📦 Installation

Clone this repository:

```bash
git clone https://github.com/Ajaykhanna/Quantum_Mechanics_Projects.git
cd Quantum_Mechanics_Projects/Excited_State_Analysis/NTOs_2_cube
````

Make the script executable:

```bash
chmod +x generate_orbital_cubes.sh
```

Ensure **Multiwfn** is installed and available in your `PATH`, or set the path via `MULTIWFN_BIN`.

---

## ⚙️ Configuration

You can control behavior via **environment variables**:

```bash
export MULTIWFN_BIN="/path/to/multiwfn" # Path to Multiwfn executable
export STATE_PREFIX="S" # Prefix for input files (e.g., "S" for S1.mfwn)
export INPUT_EXT=".mfwn" # Extension of Multiwfn input files
export ORBITAL_RANGE="584-589" # Orbital range to process (e.g., "584-589" or "600-605")
export OUTDIR="cube_out" # Directory for output .cub files
export LOGDIR="logs" # Directory for logs
export JOBS=4 # Number of parallel jobs (default: 1)
export DRY_RUN=1 # Set to 1 to preview without running
```
| Variable        | Default    | Description                                 |
| --------------- | ---------- | ------------------------------------------- |
| `MULTIWFN_BIN`  | `multiwfn` | Path to Multiwfn executable                 |
| `STATE_PREFIX`  | `S`        | Prefix for input files (`S<state>.mfwn`)    |
| `INPUT_EXT`     | `.mfwn`    | Extension of Multiwfn input files           |
| `ORBITAL_RANGE` | `584-589`  | Orbital(s) to process; single range or list |
| `OUTDIR`        | `cube_out` | Directory for `.cub` output files           |
| `LOGDIR`        | `logs`     | Directory for log files                     |
| `JOBS`          | `1`        | Parallel jobs for multi-state processing    |
| `DRY_RUN`       | `0`        | Set to `1` to preview without running       |

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
DRY_RUN=1 ./generate_orbital_cubes.sh 1
```

---

## 🔍 How It Works

1. **Reads the state list/range** from your input arguments.
2. **Expands ranges** (e.g., `1-3` → `1 2 3`).
3. For each state:

   - Builds the **exact Multiwfn input sequence**:

     ```
     200
     3
     <ORBITAL_RANGE>
     3
     2
     0
     q
     ```

   - Runs Multiwfn on `S<state>.mfwn`.
   - Renames `orbital.cub` → `S<state>_orbs<start6>_<end3>.cub`.
   - Saves logs in `logs/state_<state>.log`.

---

## 📁 Example Directory Layout

```tree
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

S1.mfwn
S2.mfwn
S3.mfwn
S4.mfwn
generate_orbital_cubes.sh
```

---

## 💡 Tips & Notes

- If `ORBITAL_RANGE` contains multiple comma-separated values, the filename uses the **minimum and maximum** numbers found.
- Always remove or move old `orbital.cub` files before running manually — the script already does this automatically.
- If Multiwfn fails, check the log file for that state in `logs/`.

---

## 🏆 License

[MIT License](https://opensource.org/license/mit).

---

## 🧪 Example Run

```bash
$ ./generate_orbital_cubes.sh 1 3
[state 1] Running Multiwfn on S1.mfwn -> S1_orbs000584_589.cub
[state 1] Saved: cube_out/S1_orbs000584_589.cub (log: logs/state_1.log)
[state 3] Running Multiwfn on S3.mfwn -> S3_orbs000584_589.cub
[state 3] Saved: cube_out/S3_orbs000584_589.cub (log: logs/state_3.log)
Done. Renamed CUBE files are in: cube_out/
```

## 🙏 Acknowledgments

Thanks to the authors/maintainers of **Multiwfn**. This toolkit simply orchestrates and organizes their outputs into a streamlined, reproducible workflow.

Happy computing! 🧫⚡️
