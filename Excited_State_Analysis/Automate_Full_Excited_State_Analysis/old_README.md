# ⚗️ Multiwfn Excited-State Pipeline — *Automate → Analyze → Report* ✨

> Bash + Python toolkit to batch-run excited-state analyses with **Multiwfn** (from Gaussian results) and generate a clean **Markdown/TXT** report of key properties across excited states.

---

## 📦 What’s inside

* `excited_state_multiwfn.sh` — **Bash** automation that drives Multiwfn to compute:

  * Natural Transition Orbital (**NTO**) eigenvalues (top-10)
  * **Δr** (charge-transfer distance) in **Bohr** and **Å**
  * **λ** (lambda index)
  * **IFCT** (Inter-Fragment Charge Transfer):

    * Per-fragment **hole/electron %**
    * **Population variation** per fragment
    * **Intrafragment redistribution**
    * **Transferred electrons** between fragments (forward/backward/net)
    * **CT/LE %** summary

* `parse_multiwfn_log.py` — **Python** parser that:

  * Reads the Multiwfn run log
  * Extracts NTO, Δr, λ, and IFCT across all excited states
  * Writes a polished **`multiwfn_excited_state_summary.md`** and **`.txt`** report with tidy tables

> 📝 **Note:** The CTS analysis step was removed in the current Bash flow due to input timing/compat issues in some Multiwfn builds. IFCT is fully supported.

---

## 🚀 Quickstart

### 1) Prereqs

* Linux / macOS with Bash
* **Multiwfn** installed and accessible (either in `PATH` or via `--multiwfn /path/to/Multiwfn`)
* Gaussian **formatted checkpoint** (`.fch`/`.fchk`) and **log** (`.log`)
* Python **3.9+** and `pandas` for the parser:

  ```bash
  pip install pandas
  ```

### 2) Run the Bash automation

```bash
./excited_state_multiwfn.sh ./examples/SP_ExSt_TDA_push_pull_system.fchk ./examples/SP_ExSt_TDA_push_pull_system.log \
  --states 1-5 \
  --multiwfn /opt/Multiwfn/Multiwfn \
  --nFrags 3 \
  --frag1 "25-27" \
  --frag2 "6,12-13,16-19,22-24" \
  --frag3 "1-5,7-11,14-15,20-21"
```

This produces a timestamped log (e.g., `./examples/MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log`).

### 3) Parse the log → Markdown/TXT

```bash
python parse_multiwfn_log.py ./examples/MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log
```

Outputs:

* `./examples/multiwfn_excited_state_summary.md`
* `./examples/multiwfn_excited_state_summary.txt`

---

## 🧠 Features & Design

* **Robust parsing**: Regexes tolerant to whitespace and slight layout changes.
* **State-aware**: NTO blocks are associated with the correct excited state by scanning the nearest “Loading configuration coefficients of excited state X…” marker.
* **Fragment-aware IFCT**: Accepts flexible fragment specs (`1,2`, `1-3,5`, `1-2, 7-9, 11`, …).
* **Clean reporting**: Tidy cross-state summary with optional per-section detail tables.
* **Fail-safe UX**: Helpful error messages; missing sections simply omit from the report.

---

## 🛠️ Bash Script — Key CLI Options

```text
./excited_state_multiwfn.sh INPUT.fch[k] INPUT.log [options]

Required:
  INPUT.fch[k]             Formatted checkpoint (.fch/.fchk). (.chk is rejected)
  INPUT.log                Gaussian output file (.log)

General:
  --states A-B             Inclusive excited-state range (default: 1-5)
  --multiwfn PATH          Multiwfn binary (default: env MULTIWFN_BIN/MULTIWFN/multiwfn or PATH)

Fragments:
  --nFrags N               Number of fragments used for IFCT (if omitted, defaults to 3)
  --frag1 "RANGES"         e.g., "1-3, 5, 7-10"
  --frag2 "RANGES"
  ...
  --fragN "RANGES"

Examples:
  --nFrags 2 --frag1 "1-3, 4, 5-7" --frag2 "4,6,11-15"
  --nFrags 4 --frag1 "1-3,4,5-7" --frag2 "4,6,11-15" --frag3 "16-20,3,2" --frag4 "21-25,29"
```

> ℹ️ The script prints the fragment block it feeds into Multiwfn (debug lines), so you can verify exactly what’s sent.

---

## 🐍 Python Script — Output Structure

The **Markdown/TXT** report contains:

* **Summary by state**: `state, Δr (Bohr/Å), λ, NTO sum, eig1..eig10, CT/LE %`
* **IFCT tables**:

  * Fragment **hole/electron %**
  * **Population variation** per fragment
  * **Intrafragment redistribution** per fragment
  * **Transferred electrons**: `donor → acceptor (forward/backward/net)`
  * **CT/LE %** summary

> The parser tolerates missing blocks (e.g., if a specific state lacks IFCT), and just omits that section.

---

## 🧩 Tips & Troubleshooting

* **Fortran I/O error (unit -4)** in Multiwfn
  If you ever re-enable CTS and hit `forrtl: severe (64): input conversion error, unit -4`: it usually means a **filename** was piped where Multiwfn expected a **numeric menu choice**. Keep the order of inputs exactly as your Multiwfn build expects, or disable CTS (current repo default).

* **Fragments syntax**
  Spaces are ok; we normalize. Valid forms include:
  `1,2` | `1-2` | `1-2, 3` | `1-2,3-5, 7`

* **Multiwfn not found**
  Use `--multiwfn /path/to/Multiwfn` or set `MULTIWFN_BIN`/`MULTIWFN` env vars.

---

## 📁 Repo Layout

```
.
├── excited_state_multiwfn.sh        # Bash automation (Multiwfn driver)
├── parse_multiwfn_log.py            # Python parser → Markdown/TXT report
├── README.md                        # You are here
└── examples/                        # (optional) sample FCHK, logs & reports
```

---

## 👩‍💻 Developer & Project Info

* **Developer:** Ajay Khanna
* **Lab:** Dr. Tretiak, Los Alamos National Laboratory (LANL)
* **Date:** Aug 12, 2025
* **Project:** Mesoscale Materials for Energy Transport Applications

Contributions, suggestions, and PRs are very welcome! 🧑‍🔬💡

---

## 🤝 Contributing

* Fork the repo, create a feature branch, submit a PR.
* For parser updates, please include a short sample of the relevant log section and a unit test if possible.
* Style: keep Bash POSIX-friendly; Python with docstrings and helpful exceptions.

---

## 📜 License

MIT.

---

## 🙏 Acknowledgments

Thanks to the authors/maintainers of **Multiwfn** and the Gaussian ecosystem. This toolkit simply orchestrates and organizes their outputs into a streamlined, reproducible workflow.
