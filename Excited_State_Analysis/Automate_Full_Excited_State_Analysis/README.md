# 🧪 Multiwfn Excited-State Automation & Parser

Automate **Gaussian→Multiwfn** excited-state analyses from the command line, then parse the resulting log into a clean, human-readable report.

* 🧰 **Bash:** `excited_state_multiwfn.sh` — modular driver for Multiwfn
* 🐍 **Python:** `parse_multiwfn_log.py` — selective, Markdown-style report generator

---

## ✨ What you get

* **One-command automation** of Multiwfn’s excited-state menus for any subset of analyses:

  * NTO, Δr (Delta-R), IFCT, CTS, MO; **λ (Lambda) is deferred to the very end** by design.
* **Failure isolation** — each analysis runs in its own Multiwfn session; if one fails, others continue.
* **Fragment handling** for IFCT/CTS (ranges like `1-3,5,7-10`).
* **Single, pretty report** (Markdown-formatted `.txt` or `.md`) per run with per-state tables.

---

## 👩‍💻 Developer

**Ajay Khanna**
Lab: **Dr. Tretiak** · Los Alamos National Laboratory (LANL)
Project: *Mesoscale Materials for Energy Transport Applications*

---

## ⚙️ Requirements

* **Gaussian** output (`.log`) + **formatted checkpoint** (`.fch`/`.fchk`)

  > ⛔️ Plain `.chk` is not accepted.
* **Multiwfn** installed and accessible (e.g., in `PATH` or via `--multiwfn /path/to/Multiwfn`)
* **Python 3.8+** with `pandas` for the parser:

  ```bash
  pip install pandas
  ```

---

## 🚀 Bash: `excited_state_multiwfn.sh`

### What it does

Runs Multiwfn excited-state analyses in a **modular** fashion. You can run everything with `--full` or cherry-pick with flags (e.g., `--nto` only). **λ** is slow/expensive, so it’s always run **last** when `--full` is requested.

### Usage

```bash
./excited_state_multiwfn.sh INPUT.fch[k] INPUT.log [analysis flags] [options]
```

### Analysis flags

* `--full` → NTO, Δr, IFCT, CTS, MO for all states, then **λ** at the end
* `--nto` → NTO only
* `--deltaR` → Δr only
* `--ifct` → IFCT only (**requires fragments**)
* `--cts` → CTS only (**requires fragments**)
* `--mo` → excited-state MO contributions only
* `--lambda` → λ only

> 📌 **Fragments are required only for IFCT and CTS.** If neither is selected, any `--frag*` inputs are ignored.

### Options

* `--states A-B` → state range (default: **1** if omitted; i.e., single state)
* `--multiwfn PATH` → path to the Multiwfn binary
* `--nFrags N` and `--frag1 "RANGES"` … `--fragN "RANGES"` → fragment setup for IFCT/CTS

**Fragment syntax:** lists & ranges separated by commas (spaces optional)
Examples: `1,2` · `1-2` · `1-2,3` · `1-2,3-5,7`

**Defaults (if `--nFrags` omitted):**

```
Fragment_1: 25-27
Fragment_2: 6,12-13,16-19,22-24
Fragment_3: 1-5,7-11,14-15,20-21
```

(Override with `--frag1..3` as needed.)

### Examples

```bash
# Full analysis (λ runs last)
./excited_state_multiwfn.sh sample.fchk sample.log --full

# NTO + MO for states 1-3
./excited_state_multiwfn.sh sample.fchk sample.log --nto --mo --states 1-3

# IFCT with custom fragments
./excited_state_multiwfn.sh sample.fchk sample.log --ifct --nFrags 3 \
  --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"

# CTS only (runs over all excited states present in the Gaussian log)
./excited_state_multiwfn.sh sample.fchk sample.log --cts --nFrags 3 \
  --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"
```

### Exact Multiwfn menu flows used

* **NTO:** `18, 6, ${log}, ${state}, 3, S${state}.mwfn, 0, q`
* **Δr:** `18, 4, ${log}, ${state}, n, 0, q`
* **λ (updated):**

  ```
  18
  14
  ${log}
  ${state}
  n
  n
  0
  q
  ```

* **IFCT:** `18, 8, 2, ${log}, ${state}, ${IFCT_FRAG_BLOCK}, 0, 0, q`
* **CTS:** `18, 16, ${IFCT_FRAG_BLOCK}, ${log}, 2, 0, q`
  *(CTS always processes **all** excited states available in the Gaussian log.)*
* **MO:** `18, 1, ${log}, ${state}, 2, 0.2, 0, 0, q`

> `${IFCT_FRAG_BLOCK}` is fed as: first a line with **N** (number of fragments), then **N lines** with the atom ranges for each fragment.

### Output (from Bash)

* A timestamped run log like:
  `MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log`
* Per-state outputs produced by Multiwfn (e.g., `S1.mwfn` for NTO)

---

## 🐍 Python: `parse_multiwfn_log.py`

### What it does

Parses the Multiwfn run log and generates a **single Markdown-formatted** report file living in the **same folder** as the log. You can parse **everything** or **select** analyses via flags.

### Usage

```bash
python parse_multiwfn_log.py /path/to/MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log [flags]
```

### Selection flags

* `--nto` → parse **NTO** (top-10 eigenvalues + sum)
* `--deltaR` → parse **Δr** (Bohr/Å per state)
* `--lambda` → parse **λ** (per state)
* `--ifct` → parse **IFCT** (fragment contributions; Δpopulation; redistribution; transfers; CT/LE %)
* `--cts` → parse **CTS** *(per-state fragment hole/electron %; CTS runs over all excited states in the log)*
* `--mo` → parse **MO** contributions *(per-MO hole/electron %, plus per-state sums)*

> No flags → **parse everything**.

### Output behavior

* Writes **one file** in the log’s directory.
* Content is **Markdown**; default extension is **`.txt`** (change with `--ext md`).
* Filename reflects the chosen analyses and timestamp embedded in the log name.
  Examples:

  * `MultiWfn_Excited_States_ALL_Analysis_20250813_144935.txt`
  * `MultiWfn_Excited_States_NTOs_Analysis_20250813_144935.txt`
  * `MultiWfn_Excited_States_NTOs_IFCT_CTS_Analysis_20250813_144935.md`

Optional:

```bash
--ext {txt,md}     # default txt
--out BASENAME     # change base name; still saved next to the log
```

### Examples

```bash
# Everything → Markdown in .txt
python parse_multiwfn_log.py /runs/MultiWfn_Excited_States_Analysis_20250813_144935.log

# Only NTO
python parse_multiwfn_log.py /runs/..._144935.log --nto

# NTO + IFCT + CTS → .md
python parse_multiwfn_log.py /runs/..._144935.log --nto --ifct --cts --ext md

# MO only
python parse_multiwfn_log.py /runs/..._144935.log --mo
```

### What’s parsed (high level)

| Module   | Key outputs (per state unless noted)                                                             |
| -------- | ------------------------------------------------------------------------------------------------ |
| **NTO**  | top-10 NTO eigenvalues + sum                                                                     |
| **Δr**   | Delta-R in Bohr & Å                                                                              |
| **λ**    | Lambda index                                                                                     |
| **IFCT** | fragment hole/electron %; Δpopulation; intrafragment redistribution; pairwise transfers; CT/LE % |
| **CTS**  | per-state fragment hole/electron % *(CTS spans all states present in the Gaussian log)*          |
| **MO**   | per-MO hole/electron % + occupancy; **sum of hole/electron %** per state                         |

---

## 📄 Sample report structure

* **Summary by state** (condensed view with whatever was parsed)
* **NTO eigenvalues (wide)**
* **Δr (Bohr & Å)**
* **λ (lambda index)**
* **IFCT tables:** contributions, Δpopulation, redistribution, transfers, CT/LE%
* **CTS tables:** per-state wide and tidy (long) formats
* **MO tables:** per-MO long table; per-state sums

> Tip: Open the output `.txt` in a Markdown viewer for best readability.

---

## 🧭 Troubleshooting

* **“Multiwfn binary not found”**
  Use `--multiwfn /path/to/Multiwfn` or set `MULTIWFN_BIN` / `MULTIWFN` / `multiwfn` env var.

* **IFCT/CTS complain about fragments**
  Provide fragments with `--nFrags N` and `--frag1..N`. Syntax like `1-3,5,7-10`.

* **Parsing found nothing**
  Ensure you’re passing the correct log generated by the Bash script. Try running the parser with no flags to parse everything.

* **Input conversion errors (Fortran / stdin misalignment)**
  Usually means a menu stream mismatch. The modular runner isolates each analysis and follows the exact menu order shown above.

---

## 📈 Performance tips

* Use `--full` to let the script handle **λ last** (cheaper analyses first).
* CTS runs over **all** excited states in the Gaussian log (by design in Multiwfn). If you only need CTS, run `--cts` alone.

---

## 🏷️ Citation

* **Multiwfn:**
  * Tian Lu, Feiwu Chen, Multiwfn: A Multifunctional Wavefunction Analyzer, J. Comput. Chem. 33, **580-592** (2012) DOI: 10.1002/jcc.22885
  * Tian Lu, A comprehensive electron wavefunction analysis toolbox for chemists, Multiwfn, J. Chem. Phys., **161**, 082503 (2024) DOI: 10.1063/5.0216272

* **Hole-electron analysis:**
  * Zeyu Liu, Tian Lu, Qinxue Chen, An sp-hybridized all-carboatomic ring, cyclo[18]carbon: Electronic structure, electronic spectrum, and optical nonlinearity, Carbon, **165**, 461-467 (2020) DOI: 10.1016/j.carbon.2020.05.023
* **Charge-Transfer Spectrum (CTS) method:**
  * Zeyu Liu, Xia Wang, Tian Lu, et al., Potential optical molecular switch: Lithium@cyclo[18]carbon complex transforming between two stable configurations, Carbon, **187**, 78-85 (2022) DOI: 10.1016/j.carbon.2021.11.005
  
* **Intra-Fragment Charge Transfer (IFCT) method:**
  * Bioconjugate Chem. DOI: <https://doi.org/10.1021/acs.bioconjchem.0c00020>
  * Solar Energy 201 (2020) 872–883. DOI: <https://doi.org/10.1016/j.solener.2020.03.053>
  * ChemistrySelect*, **5**, 3971 (2020)
  * Eur. J. Inorg. Chem., 2019, 4350
  * Org. Elect., 71, 212 (2020)
  * J. Mater. Chem. C, 2019,7, 2604-2614

* **NTOs .mwfn Format:**
  * Tian Lu, Qinxue Chen, mwfn: A Strict, Concise and Extensible Format for Electronic Wavefunction Storage and Exchange, ChemRxiv (2020) DOI: <https://doi.org/10.26434/chemrxiv.11872524>

---

## 🤝 Contributing

PRs welcome! Please:

1. Keep the Multiwfn menu flows explicit in comments.
2. Favor small, isolated functions (both Bash & Python).
3. Add a quick example and update this README for new features.

---

## 🪪 License

[MIT](https://opensource.org/license/mit)

---

## ✅ Quick checklist

* [ ] Gaussian `.log` and `.fch`/`.fchk` ready
* [ ] Multiwfn path known or in `PATH`
* [ ] Run Bash automation with the analyses you need
* [ ] Parse the run log with the Python script
* [ ] Share or archive the Markdown report 🎉

---

### 🧷 Handy one-liners

```bash
# Run everything on state 1 (default)
./excited_state_multiwfn.sh sys.fchk sys.log --full

# IFCT + CTS with custom fragments, states 1-5
./excited_state_multiwfn.sh sys.fchk sys.log --ifct --cts --states 1-5 --nFrags 3 \
  --frag1 "1-10" --frag2 "11-20" --frag3 "21-30"

# Parse only CTS and write an .md report next to the log
python parse_multiwfn_log.py /runs/MultiWfn_Excited_States_Analysis_20250813_144935.log --cts --ext md
```

Happy computing! 🧫⚡️
