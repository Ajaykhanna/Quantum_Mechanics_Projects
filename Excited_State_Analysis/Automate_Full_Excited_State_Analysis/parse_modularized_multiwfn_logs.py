#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_multiwfn_log.py

Modular parser for Multiwfn excited-state analysis logs with CLI flags to
select which analyses to parse. By default it parses EVERYTHING; you can
limit the work via flags like --nto, --deltaR, --lambda, --ifct, --cts, --mo.

▶ Output behavior
- Writes a SINGLE file in the SAME FOLDER as the Multiwfn log.
- Default extension is .txt but the contents are Markdown-formatted.
- The filename reflects the chosen analyses and the log timestamp, e.g.:
  MultiWfn_Excited_States_NTOs_Analysis_20250813_144935.txt
- Change the extension to .md with --ext md.
- You can change the base name with --out (basename only); it will still be
  written to the log’s directory.

Examples
--------
# Parse everything (default) and write a single .txt (markdown) file
python parse_multiwfn_log.py /path/to/MultiWfn_Excited_States_Analysis_20250813_144935.log

# Parse only NTO (filename auto: ..._NTOs_Analysis_YYYYMMDD_HHMMSS.txt)
python parse_multiwfn_log.py /path/to/log.log --nto

# Parse NTO + IFCT + CTS (filename auto: ..._NTOs_IFCT_CTS_Analysis_YYYYMMDD_HHMMSS.txt)
python parse_multiwfn_log.py /path/to/log.log --nto --ifct --cts

# Parse only MO contributions, write .md
python parse_multiwfn_log.py /path/to/log.log --mo --ext md
"""
import argparse
import os
import re
from typing import Dict, List, Optional

import pandas as pd


# ----------------------------- Utilities ----------------------------- #


def _to_float(s: str) -> Optional[float]:
    """Safely convert string to float; return None if conversion fails."""
    try:
        return float(s)
    except Exception:
        return None


def _read_text(path: str) -> str:
    """Read text from path with basic validation and helpful errors."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Log file not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        raise ValueError("The provided log file is empty.")
    return text


def _find_current_state_backwards(text: str, pos: int) -> Optional[int]:
    """
    Look backwards from index `pos` to find the most recent excited-state marker.
    Prefers: 'Loading configuration coefficients of excited state   X'
    Fallback: 'Excited state   X:'
    """
    window_start = max(0, pos - 8000)
    window = text[window_start:pos]
    matches = list(
        re.finditer(
            r"Loading configuration coefficients of excited state\s+(\d+)", window
        )
    )
    if matches:
        return int(matches[-1].group(1))
    matches = list(re.finditer(r"Excited state\s+(\d+)\s*:", window))
    if matches:
        return int(matches[-1].group(1))
    return None


def _extract_log_timestamp(log_path: str) -> str:
    """
    Try to extract a timestamp like YYYYMMDD_HHMMSS from the log filename.
    If not found, fall back to current time.
    """
    fname = os.path.basename(log_path)
    m = re.search(r"(\d{8}_\d{6})", fname)
    if m:
        return m.group(1)
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _selected_labels(parse_all: bool, flags: Dict[str, bool]) -> List[str]:
    """
    Build human-readable labels for selected analyses, used in filename and report.
    Ordering is fixed for stability.
    """
    order = [
        ("nto", "NTOs"),
        ("deltaR", "DeltaR"),
        ("lambda", "Lambda"),
        ("ifct", "IFCT"),
        ("cts", "CTS"),
        ("mo", "MOs"),
    ]
    if parse_all:
        return ["ALL"]
    labels = [label for key, label in order if flags.get(key)]
    return labels if labels else ["ALL"]


# ----------------------------- Parsers ----------------------------- #


def parse_nto(text: str) -> pd.DataFrame:
    """
    Extract NTO top-10 eigenvalues + total sum for each excited state.

    Returns
    -------
    DataFrame columns:
      state, nto_sum, eig1..eig10
    """
    records = []
    # Two lines of floats then "Sum of all eigenvalues"
    for m in re.finditer(
        r"The highest 10 eigenvalues of NTO pairs:\s*\n(.*?)\n\s*Sum of all eigenvalues:\s*([0-9.]+)",
        text,
        flags=re.DOTALL,
    ):
        block_start = m.start()
        state = _find_current_state_backwards(text, block_start)
        lines_block = m.group(1).strip()
        eigvals = re.findall(r"[0-9]*\.[0-9]+", lines_block)
        eigvals = [float(x) for x in eigvals][:10]
        while len(eigvals) < 10:
            eigvals.append(None)
        nto_sum = _to_float(m.group(2))
        row = {"state": state, "nto_sum": nto_sum}
        for i, v in enumerate(eigvals, start=1):
            row[f"eig{i}"] = v
        records.append(row)
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.drop_duplicates(subset=["state"]).sort_values("state")
    return df


def parse_delta_r(text: str) -> pd.DataFrame:
    """
    Extract Δr (Bohr and Å) per excited state.

    Returns
    -------
    DataFrame columns:
      state, delta_r_bohr, delta_r_angstrom
    """
    matches = re.findall(
        r"Excited state\s+(\d+):\s+Delta_r\s*=\s*([0-9.]+)\s*Bohr,\s*([0-9.]+)\s*Angstrom",
        text,
    )
    df = pd.DataFrame(matches, columns=["state", "delta_r_bohr", "delta_r_angstrom"])
    if not df.empty:
        df["state"] = df["state"].astype(int)
        df["delta_r_bohr"] = pd.to_numeric(df["delta_r_bohr"], errors="coerce")
        df["delta_r_angstrom"] = pd.to_numeric(df["delta_r_angstrom"], errors="coerce")
        df = df.drop_duplicates(subset=["state"]).sort_values("state")
    return df


def parse_lambda(text: str) -> pd.DataFrame:
    """
    Extract lambda index per excited state.

    Returns
    -------
    DataFrame columns:
      state, lambda_index
    """
    matches = re.findall(r"Excited state\s+(\d+):\s+lambda\s*=\s*([0-9.]+)", text)
    df = pd.DataFrame(matches, columns=["state", "lambda_index"])
    if not df.empty:
        df["state"] = df["state"].astype(int)
        df["lambda_index"] = pd.to_numeric(df["lambda_index"], errors="coerce")
        df = df.drop_duplicates(subset=["state"]).sort_values("state")
    return df


def parse_ifct(text: str) -> Dict[str, pd.DataFrame]:
    """
    Extract IFCT blocks:
      - Per-fragment hole/electron contributions
      - Variation of population per fragment
      - Intrafragment electron redistribution
      - Transferred electrons between fragments (forward/backward/net)
      - CT% / LE% summary

    Returns
    -------
    Dict of DataFrames:
      {
        "ifct_fragment_contrib": DataFrame[state, fragment, hole_pct, electron_pct],
        "ifct_population_variation": DataFrame[state, fragment, delta_population],
        "ifct_intrafragment_redistribution": DataFrame[state, fragment, redistribution],
        "ifct_transfers": DataFrame[state, donor, acceptor, forward, backward, net],
        "ifct_summary": DataFrame[state, CT_percent, LE_percent],
      }
    """
    lines = text.splitlines()
    current_state = None
    contrib, var_pop, redist, transfers, summary = [], [], [], [], []

    i = 0
    while i < len(lines):
        line = lines[i]

        m_state = re.search(
            r"Loading configuration coefficients of excited state\s+(\d+)", line
        )
        if m_state:
            try:
                current_state = int(m_state.group(1))
            except Exception:
                current_state = None

        if "Contribution of each fragment to hole and electron" in line:
            j = i + 1
            while j < len(lines):
                m_contrib = re.match(
                    r"\s*(\d+)\s+Hole:\s+([\-0-9.]+)\s*%\s+Electron:\s+([\-0-9.]+)\s*%",
                    lines[j],
                )
                if m_contrib:
                    frag = int(m_contrib.group(1))
                    hole = _to_float(m_contrib.group(2))
                    elec = _to_float(m_contrib.group(3))
                    contrib.append(
                        {
                            "state": current_state,
                            "fragment": frag,
                            "hole_pct": hole,
                            "electron_pct": elec,
                        }
                    )
                    j += 1
                else:
                    break
            i = j
            continue

        m_var = re.match(
            r"\s*Variation of population number of fragment\s+(\d+):\s+([\-0-9.]+)",
            line,
        )
        if m_var:
            frag = int(m_var.group(1))
            val = _to_float(m_var.group(2))
            var_pop.append(
                {"state": current_state, "fragment": frag, "delta_population": val}
            )
            i += 1
            continue

        m_red = re.match(
            r"\s*Intrafragment electron redistribution of fragment\s+(\d+):\s+([\-0-9.]+)",
            line,
        )
        if m_red:
            frag = int(m_red.group(1))
            val = _to_float(m_red.group(2))
            redist.append(
                {"state": current_state, "fragment": frag, "redistribution": val}
            )
            i += 1
            continue

        if "Transferred electrons between fragments" in line:
            j = i + 1
            while j < len(lines):
                m_tr = re.match(
                    r"\s*(\d+)\s*->\s*(\d+):\s*([\-0-9.]+)\s+"
                    r"\1\s*<-\s*\2:\s*([\-0-9.]+)\s+"
                    r"Net\s*\1\s*->\s*\2:\s*([\-0-9.]+)",
                    lines[j],
                )
                if m_tr:
                    donor = int(m_tr.group(1))
                    acceptor = int(m_tr.group(2))
                    forward = _to_float(m_tr.group(3))
                    backward = _to_float(m_tr.group(4))
                    net = _to_float(m_tr.group(5))
                    transfers.append(
                        {
                            "state": current_state,
                            "donor": donor,
                            "acceptor": acceptor,
                            "forward": forward,
                            "backward": backward,
                            "net": net,
                        }
                    )
                    j += 1
                else:
                    break
            i = j
            continue

        m_ct = re.match(
            r"\s*Intrinsic charge transfer percentage, CT\(%\):\s*([\-0-9.]+)\s*%", line
        )
        if m_ct:
            ct = _to_float(m_ct.group(1))
            le = None
            for k in range(1, 5):
                if i + k < len(lines):
                    m_le = re.match(
                        r"\s*Intrinsic local excitation percentage, LE\(%\):\s*([\-0-9.]+)\s*%",
                        lines[i + k],
                    )
                    if m_le:
                        le = _to_float(m_le.group(1))
                        break
            summary.append({"state": current_state, "CT_percent": ct, "LE_percent": le})

        i += 1

    def _df(cols):
        return pd.DataFrame(columns=cols)

    df_contrib = (
        pd.DataFrame(contrib)
        if contrib
        else _df(["state", "fragment", "hole_pct", "electron_pct"])
    )
    df_var_pop = (
        pd.DataFrame(var_pop)
        if var_pop
        else _df(["state", "fragment", "delta_population"])
    )
    df_redist = (
        pd.DataFrame(redist) if redist else _df(["state", "fragment", "redistribution"])
    )
    df_trans = (
        pd.DataFrame(transfers)
        if transfers
        else _df(["state", "donor", "acceptor", "forward", "backward", "net"])
    )
    df_summary = (
        pd.DataFrame(summary) if summary else _df(["state", "CT_percent", "LE_percent"])
    )

    if not df_contrib.empty:
        df_contrib = df_contrib.astype(
            {"state": "Int64", "fragment": "Int64"}
        ).sort_values(["state", "fragment"])
    if not df_var_pop.empty:
        df_var_pop = df_var_pop.astype(
            {"state": "Int64", "fragment": "Int64"}
        ).sort_values(["state", "fragment"])
    if not df_redist.empty:
        df_redist = df_redist.astype(
            {"state": "Int64", "fragment": "Int64"}
        ).sort_values(["state", "fragment"])
    if not df_trans.empty:
        df_trans = df_trans.astype(
            {"state": "Int64", "donor": "Int64", "acceptor": "Int64"}
        ).sort_values(["state", "donor", "acceptor"])
    if not df_summary.empty:
        df_summary = (
            df_summary.astype({"state": "Int64"})
            .drop_duplicates(subset=["state"])
            .sort_values("state")
        )

    return {
        "ifct_fragment_contrib": df_contrib,
        "ifct_population_variation": df_var_pop,
        "ifct_intrafragment_redistribution": df_redist,
        "ifct_transfers": df_trans,
        "ifct_summary": df_summary,
    }


def parse_cts(text: str) -> Dict[str, pd.DataFrame]:
    """
    Extract CTS (Charge-Transfer Spectrum) per-state fragment Hole/Electron (%) contributions.

    The CTS printout includes lines like:
      Calculating excited state     1  of    10
      Fragment   1    Hole:  17.92 %     Electron:   5.40 %
      Fragment   2    Hole:  51.06 %     Electron:  47.77 %
      Fragment   3    Hole:  31.02 %     Electron:  46.83 %

    This parser collects those into:
      - cts_long: state, fragment, hole_pct, electron_pct
      - cts_wide: state, Frag 1 Hole/Electron (%), Frag 2 Hole/Electron (%), ...

    Notes
    -----
    • CTS in Multiwfn processes ALL excited states available in the Gaussian log.
      We only summarize the printed results; we do not control which states it ran.
    """
    # Try to confine to a CTS-specific window to avoid accidental matches
    start_candidates = [
        "Select the method for calculating fragment contributions to hole and electron",
        "NOTE: The charge-transfer spectrum was first proposed",
        "There are",  # e.g., "There are   10 excited states, loading basic information..."
    ]
    start_idx = -1
    for key in start_candidates:
        idx = text.find(key)
        if idx != -1:
            start_idx = idx
            break

    end_key = "The following files have been generated"
    end_idx = text.find(end_key, start_idx) if start_idx != -1 else -1
    cts_text = (
        text
        if start_idx == -1
        else (text[start_idx:] if end_idx == -1 else text[start_idx:end_idx])
    )

    state_pattern = re.compile(
        r"Calculating excited state\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE
    )
    frag_pattern = re.compile(
        r"^\s*Fragment\s+(\d+)\s+Hole:\s+([\-0-9.]+)\s*%\s+Electron:\s+([\-0-9.]+)\s*%",
        re.IGNORECASE | re.MULTILINE,
    )

    states_data = []
    current_state = None
    fragments = []

    for line in cts_text.splitlines():
        m_state = state_pattern.search(line)
        if m_state:
            # Flush previous state
            if current_state is not None and fragments:
                for frag_idx, hole, electron in fragments:
                    states_data.append(
                        {
                            "state": int(current_state),
                            "fragment": int(frag_idx),
                            "hole_pct": float(hole),
                            "electron_pct": float(electron),
                        }
                    )
            current_state = int(m_state.group(1))
            fragments = []
            continue

        m_frag = frag_pattern.match(line)
        if m_frag and current_state is not None:
            frag_idx, hole, electron = m_frag.groups()
            fragments.append((int(frag_idx), float(hole), float(electron)))

    # Flush last
    if current_state is not None and fragments:
        for frag_idx, hole, electron in fragments:
            states_data.append(
                {
                    "state": int(current_state),
                    "fragment": int(frag_idx),
                    "hole_pct": float(hole),
                    "electron_pct": float(electron),
                }
            )

    cts_long = pd.DataFrame(
        states_data, columns=["state", "fragment", "hole_pct", "electron_pct"]
    )
    if not cts_long.empty:
        cts_long = cts_long.astype({"state": "Int64", "fragment": "Int64"}).sort_values(
            ["state", "fragment"]
        )

    # Build wide
    if cts_long.empty:
        cts_wide = pd.DataFrame(columns=["state"])
    else:
        frag_ids = sorted(cts_long["fragment"].unique().tolist())
        rows: List[Dict] = []
        for state, group in cts_long.groupby("state"):
            row: Dict = {"state": int(state)}
            for _, r in group.iterrows():
                fid = int(r["fragment"])
                row[f"Frag {fid} Hole (%)"] = float(r["hole_pct"])
                row[f"Frag {fid} Electron (%)"] = float(r["electron_pct"])
            rows.append(row)
        ordered_cols = ["state"]
        for fid in frag_ids:
            ordered_cols += [f"Frag {fid} Hole (%)", f"Frag {fid} Electron (%)"]
        cts_wide = pd.DataFrame(rows)
        if not cts_wide.empty:
            ordered_cols = [c for c in ordered_cols if c in cts_wide.columns]
            cts_wide = (
                cts_wide[ordered_cols].sort_values("state").astype({"state": "Int64"})
            )

    return {"cts_long": cts_long, "cts_wide": cts_wide}


def parse_mo(text: str) -> Dict[str, pd.DataFrame]:
    """
    Extract Molecular Orbital (MO) contributions per excited state.

    We look for contiguous blocks of lines like:
      MO   55, Occ:   2.00000    Hole:    1.436 %    Electron:    0.000 %
      ...
      Sum of hole:   99.998 %    Sum of electron:   99.998 %

    For each block we:
      • Associate the block to the nearest excited-state marker above it.
      • Return a long table of (state, mo, occ, hole_pct, electron_pct).
      • Return a per-state sums table (sum_hole_pct, sum_electron_pct).
    """
    # Regex to capture a whole MO block (many MO lines) followed by the sums line
    block_regex = re.compile(
        r"((?:^\s*MO\s+\d+.*\n)+)\s*^\s*Sum of hole:\s*([\-0-9.]+)\s*%\s*Sum of electron:\s*([\-0-9.]+)\s*%.*?$",
        flags=re.MULTILINE,
    )
    line_regex = re.compile(
        r"^\s*MO\s+(\d+),\s*Occ:\s*([\-0-9.]+)\s*Hole:\s*([\-0-9.]+)\s*%\s*Electron:\s*([\-0-9.]+)\s*%",
        flags=re.MULTILINE,
    )

    mo_rows: List[Dict] = []
    sum_rows: List[Dict] = []

    for m in block_regex.finditer(text):
        block_text = m.group(1)
        sum_hole = _to_float(m.group(2))
        sum_elec = _to_float(m.group(3))
        # Find the state by looking backwards from the start of this block
        state = _find_current_state_backwards(text, m.start(1))

        for mo_line in line_regex.finditer(block_text):
            mo_idx = int(mo_line.group(1))
            occ = _to_float(mo_line.group(2))
            hole_pct = _to_float(mo_line.group(3))
            elec_pct = _to_float(mo_line.group(4))
            mo_rows.append(
                {
                    "state": state,
                    "mo": mo_idx,
                    "occ": occ,
                    "hole_pct": hole_pct,
                    "electron_pct": elec_pct,
                }
            )

        sum_rows.append(
            {"state": state, "sum_hole_pct": sum_hole, "sum_electron_pct": sum_elec}
        )

    mo_long = pd.DataFrame(
        mo_rows, columns=["state", "mo", "occ", "hole_pct", "electron_pct"]
    )
    mo_sums = pd.DataFrame(
        sum_rows, columns=["state", "sum_hole_pct", "sum_electron_pct"]
    )

    if not mo_long.empty:
        mo_long = mo_long.astype({"state": "Int64", "mo": "Int64"}).sort_values(
            ["state", "mo"]
        )
    if not mo_sums.empty:
        mo_sums = (
            mo_sums.astype({"state": "Int64"})
            .drop_duplicates(subset=["state"])
            .sort_values("state")
        )

    return {"mo_long": mo_long, "mo_sums": mo_sums}


# ----------------------------- Reporting ----------------------------- #


def df_to_markdown_table(
    df: pd.DataFrame, float_fmt="{:.6f}", max_rows: Optional[int] = None
) -> str:
    """Render a DataFrame as a clean Markdown table."""
    if df is None or df.empty:
        return "_No data found._\n"
    if max_rows is not None:
        df = df.head(max_rows).copy()

    def fmt_val(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            try:
                return float_fmt.format(v)
            except Exception:
                return str(v)
        return str(v)

    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = [
        "| " + " | ".join(fmt_val(row[c]) for c in cols) + " |"
        for _, row in df.iterrows()
    ]
    return "\n".join([header, sep] + body) + "\n"


def build_summary_table(
    nto_df: pd.DataFrame,
    deltar_df: pd.DataFrame,
    lambda_df: pd.DataFrame,
    ifct_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    """Create a compact cross-state summary with available columns only."""
    states = set()
    for df in (nto_df, deltar_df, lambda_df, ifct_summary_df):
        if df is not None and not df.empty:
            states.update(
                pd.to_numeric(df["state"], errors="coerce")
                .dropna()
                .astype(int)
                .tolist()
            )
    states = sorted(states)

    rows: List[Dict] = []
    for s in states:
        row = {"state": s}
        if deltar_df is not None and not deltar_df.empty:
            sub = deltar_df[deltar_df["state"] == s]
            if not sub.empty:
                row["delta_r_bohr"] = float(sub["delta_r_bohr"].iloc[0])
                row["delta_r_angstrom"] = float(sub["delta_r_angstrom"].iloc[0])
        if lambda_df is not None and not lambda_df.empty:
            sub = lambda_df[lambda_df["state"] == s]
            if not sub.empty:
                row["lambda_index"] = float(sub["lambda_index"].iloc[0])
        if nto_df is not None and not nto_df.empty:
            sub = nto_df[nto_df["state"] == s]
            if not sub.empty:
                row["nto_sum"] = (
                    float(sub["nto_sum"].iloc[0])
                    if pd.notna(sub["nto_sum"].iloc[0])
                    else None
                )
                for i_e in range(1, 11):
                    key = f"eig{i_e}"
                    if key in sub.columns:
                        val = sub[key].iloc[0]
                        row[key] = float(val) if pd.notna(val) else None
        if ifct_summary_df is not None and not ifct_summary_df.empty:
            sub = ifct_summary_df[ifct_summary_df["state"] == s]
            if not sub.empty:
                row["CT_percent"] = (
                    float(sub["CT_percent"].iloc[0])
                    if pd.notna(sub["CT_percent"].iloc[0])
                    else None
                )
                row["LE_percent"] = (
                    float(sub["LE_percent"].iloc[0])
                    if pd.notna(sub["LE_percent"].iloc[0])
                    else None
                )
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("state")


def build_markdown_report(title: str, sections: Dict[str, pd.DataFrame]) -> str:
    """Assemble a Markdown report from selected sections."""
    from datetime import datetime

    md = [
        f"# {title}\n",
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}\n\n",
    ]

    # Summary first if present
    if "summary_by_state" in sections:
        md.append("## Summary by state\n")
        md.append(df_to_markdown_table(sections["summary_by_state"]))
        md.append("\n")

    # Then each available section in a user-friendly order
    order = [
        ("NTO eigenvalues (wide)", "nto_eigs"),
        ("Δr (Bohr & Å)", "delta_r"),
        ("λ (lambda index)", "lambda"),
        ("IFCT: Fragment contributions (hole/electron %)", "ifct_fragment_contrib"),
        ("IFCT: Population variation (Δpopulation)", "ifct_population_variation"),
        (
            "IFCT: Intrafragment electron redistribution",
            "ifct_intrafragment_redistribution",
        ),
        ("IFCT: Transferred electrons between fragments", "ifct_transfers"),
        ("IFCT: Summary (CT% / LE%)", "ifct_summary"),
        ("CTS: Per-state summary (wide)", "cts_wide"),
        ("CTS: Fragment contributions per state (long)", "cts_long"),
        ("MO: Contributions per MO (long)", "mo_long"),
        ("MO: Sum of hole/electron per state", "mo_sums"),
    ]
    for sec_title, key in order:
        df = sections.get(key)
        if isinstance(df, pd.DataFrame):
            md.append(f"## {sec_title}\n")
            md.append(df_to_markdown_table(df))
            md.append("\n")

    return "".join(md)


# ----------------------------- CLI ----------------------------- #


def main():
    parser = argparse.ArgumentParser(
        description="Parse Multiwfn excited-state analysis logs and write a single Markdown-formatted output file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("log", help="Path to Multiwfn log file.")

    # Selection flags: if none are provided, we parse everything.
    parser.add_argument("--nto", action="store_true", help="Parse NTO blocks.")
    parser.add_argument("--deltaR", action="store_true", help="Parse Δr blocks.")
    parser.add_argument(
        "--lambda",
        dest="lambda_idx",
        action="store_true",
        help="Parse λ (lambda index) blocks.",
    )
    parser.add_argument("--ifct", action="store_true", help="Parse IFCT blocks.")
    parser.add_argument(
        "--cts",
        action="store_true",
        help="Parse CTS (Charge-Transfer Spectrum) blocks.",
    )
    parser.add_argument(
        "--mo", action="store_true", help="Parse MO contribution blocks."
    )

    # Output naming controls
    parser.add_argument(
        "--ext",
        choices=["txt", "md"],
        default="txt",
        help="File extension for the output. Contents are Markdown either way.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional BASENAME for the output file (directory is forced to the log folder).",
    )

    args = parser.parse_args()

    # Read log
    log_path = os.path.abspath(args.log)
    log_dir = os.path.dirname(log_path)
    text = _read_text(log_path)

    # If user provided no flags, parse everything.
    flags = {
        "nto": args.nto,
        "deltaR": args.deltaR,
        "lambda": args.lambda_idx,
        "ifct": args.ifct,
        "cts": args.cts,
        "mo": args.mo,
    }
    parse_all = not any(flags.values())

    # Run selected parsers
    nto_df = parse_nto(text) if (parse_all or args.nto) else pd.DataFrame()
    deltar_df = parse_delta_r(text) if (parse_all or args.deltaR) else pd.DataFrame()
    lambda_df = parse_lambda(text) if (parse_all or args.lambda_idx) else pd.DataFrame()
    ifct_dict = parse_ifct(text) if (parse_all or args.ifct) else {}
    cts_dict = parse_cts(text) if (parse_all or args.cts) else {}
    mo_dict = parse_mo(text) if (parse_all or args.mo) else {}

    # Build sections for report
    sections: Dict[str, pd.DataFrame] = {}

    # Summary depends on what was parsed (IFCT summary contributes CT/LE columns)
    summary_df = build_summary_table(
        nto_df if not nto_df.empty else pd.DataFrame(),
        deltar_df if not deltar_df.empty else pd.DataFrame(),
        lambda_df if not lambda_df.empty else pd.DataFrame(),
        ifct_dict.get("ifct_summary", pd.DataFrame()) if ifct_dict else pd.DataFrame(),
    )
    if not summary_df.empty:
        sections["summary_by_state"] = summary_df

    # Attach selected raw sections
    if not nto_df.empty:
        sections["nto_eigs"] = nto_df
    if not deltar_df.empty:
        sections["delta_r"] = deltar_df
    if not lambda_df.empty:
        sections["lambda"] = lambda_df
    if ifct_dict:
        for k, df in ifct_dict.items():
            if not df.empty:
                sections[k] = df
    if cts_dict:
        for k in ["cts_long", "cts_wide"]:
            df = cts_dict.get(k, pd.DataFrame())
            if not df.empty:
                sections[k] = df
    if mo_dict:
        for k in ["mo_long", "mo_sums"]:
            df = mo_dict.get(k, pd.DataFrame())
            if not df.empty:
                sections[k] = df

    # Build markdown content
    labels = _selected_labels(parse_all, flags)
    title = f"Multiwfn Excited-State Analysis ({' + '.join(labels)})"
    md_content = build_markdown_report(title, sections)

    # Determine output filename + path
    timestamp = _extract_log_timestamp(log_path)
    if args.out:
        # Use provided BASENAME (strip directories), then force extension
        base = os.path.basename(args.out)
        name, _old_ext = os.path.splitext(base)
        out_name = f"{name}.{args.ext}"
    else:
        # Auto-name using selected labels
        tag = "_".join(labels)
        out_name = f"MultiWfn_Excited_States_{tag}_Analysis_{timestamp}.{args.ext}"

    out_path = os.path.join(log_dir, out_name)

    # Write a SINGLE file (markdown content)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("Report written:")
    print(f" - {out_path}")

    if not sections:
        print(
            "NOTE: No matching sections were found with the chosen flags. "
            "Try running without flags to parse everything."
        )


if __name__ == "__main__":
    main()
