# -*- coding: utf-8 -*-

import os
import re
from typing import Dict, List, Optional
import pandas as pd

# ------------------ (Re)use the parser code from previous cell ------------------


def _to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except Exception:
        return None


def _find_current_state_backwards(text: str, pos: int) -> Optional[int]:
    window_start = max(0, pos - 5000)
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


def parse_multiwfn_log(log_path: str) -> Dict[str, pd.DataFrame]:
    if not os.path.isfile(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        raise ValueError("The provided log file is empty.")

    nto_records = []
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
        nto_entry = {"state": state, "nto_sum": nto_sum}
        for i, v in enumerate(eigvals, start=1):
            nto_entry[f"eig{i}"] = v
        nto_records.append(nto_entry)
    nto_df = (
        pd.DataFrame(nto_records).drop_duplicates(subset=["state"]).sort_values("state")
    )

    deltar_matches = re.findall(
        r"Excited state\s+(\d+):\s+Delta_r\s*=\s*([0-9.]+)\s*Bohr,\s*([0-9.]+)\s*Angstrom",
        text,
    )
    deltar_df = pd.DataFrame(
        deltar_matches, columns=["state", "delta_r_bohr", "delta_r_angstrom"]
    )
    if not deltar_df.empty:
        for c in ["state", "delta_r_bohr", "delta_r_angstrom"]:
            deltar_df[c] = deltar_df[c].astype(float)
        deltar_df["state"] = deltar_df["state"].astype(int)
        deltar_df = deltar_df.drop_duplicates(subset=["state"]).sort_values("state")

    lambda_matches = re.findall(
        r"Excited state\s+(\d+):\s+lambda\s*=\s*([0-9.]+)", text
    )
    lambda_df = pd.DataFrame(lambda_matches, columns=["state", "lambda_index"])
    if not lambda_df.empty:
        lambda_df["state"] = lambda_df["state"].astype(int)
        lambda_df["lambda_index"] = lambda_df["lambda_index"].astype(float)
        lambda_df = lambda_df.drop_duplicates(subset=["state"]).sort_values("state")

    lines = text.splitlines()
    current_state = None
    ifct_fragment_contrib = []
    ifct_population_variation = []
    ifct_intrafragment_redistribution = []
    ifct_transfers = []
    ifct_summary = []

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
                    ifct_fragment_contrib.append(
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
            ifct_population_variation.append(
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
            ifct_intrafragment_redistribution.append(
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
                    ifct_transfers.append(
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
            ifct_summary.append(
                {"state": current_state, "CT_percent": ct, "LE_percent": le}
            )

        i += 1

    def df_or_empty(cols):
        return pd.DataFrame(columns=cols)

    nto_df = (
        nto_df
        if not nto_df.empty
        else df_or_empty(
            [
                "state",
                "nto_sum",
                "eig1",
                "eig2",
                "eig3",
                "eig4",
                "eig5",
                "eig6",
                "eig7",
                "eig8",
                "eig9",
                "eig10",
            ]
        )
    )
    deltar_df = (
        deltar_df
        if not deltar_df.empty
        else df_or_empty(["state", "delta_r_bohr", "delta_r_angstrom"])
    )
    lambda_df = (
        lambda_df if not lambda_df.empty else df_or_empty(["state", "lambda_index"])
    )
    ifct_fragment_contrib_df = (
        pd.DataFrame(ifct_fragment_contrib)
        if ifct_fragment_contrib
        else df_or_empty(["state", "fragment", "hole_pct", "electron_pct"])
    )
    ifct_population_variation_df = (
        pd.DataFrame(ifct_population_variation)
        if ifct_population_variation
        else df_or_empty(["state", "fragment", "delta_population"])
    )
    ifct_intrafragment_redistribution_df = (
        pd.DataFrame(ifct_intrafragment_redistribution)
        if ifct_intrafragment_redistribution
        else df_or_empty(["state", "fragment", "redistribution"])
    )
    ifct_transfers_df = (
        pd.DataFrame(ifct_transfers)
        if ifct_transfers
        else df_or_empty(["state", "donor", "acceptor", "forward", "backward", "net"])
    )
    ifct_summary_df = (
        pd.DataFrame(ifct_summary)
        if ifct_summary
        else df_or_empty(["state", "CT_percent", "LE_percent"])
    )

    for df in [
        ifct_fragment_contrib_df,
        ifct_population_variation_df,
        ifct_intrafragment_redistribution_df,
        ifct_transfers_df,
    ]:
        if not df.empty:
            for col in df.columns:
                if col == "state" or col in ("fragment", "donor", "acceptor"):
                    continue
                if df[col].dtype == object:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

    if not ifct_fragment_contrib_df.empty:
        ifct_fragment_contrib_df = ifct_fragment_contrib_df.astype(
            {"state": "Int64", "fragment": "Int64"}
        ).sort_values(["state", "fragment"])
    if not ifct_population_variation_df.empty:
        ifct_population_variation_df = ifct_population_variation_df.astype(
            {"state": "Int64", "fragment": "Int64"}
        ).sort_values(["state", "fragment"])
    if not ifct_intrafragment_redistribution_df.empty:
        ifct_intrafragment_redistribution_df = (
            ifct_intrafragment_redistribution_df.astype(
                {"state": "Int64", "fragment": "Int64"}
            ).sort_values(["state", "fragment"])
        )
    if not ifct_transfers_df.empty:
        ifct_transfers_df = ifct_transfers_df.astype(
            {"state": "Int64", "donor": "Int64", "acceptor": "Int64"}
        ).sort_values(["state", "donor", "acceptor"])
    if not ifct_summary_df.empty:
        ifct_summary_df = (
            ifct_summary_df.astype({"state": "Int64"})
            .drop_duplicates(subset=["state"])
            .sort_values("state")
        )

    # Build summary
    states = set()
    for df in [nto_df, deltar_df, lambda_df, ifct_summary_df]:
        if not df.empty and "state" in df.columns:
            states.update(
                pd.to_numeric(df["state"], errors="coerce")
                .dropna()
                .astype(int)
                .tolist()
            )
    states = sorted(states)
    summary_rows = []
    for s in states:
        row = {"state": s}
        sub = deltar_df[deltar_df.get("state", pd.Series(dtype=int)) == s]
        if not sub.empty:
            row["delta_r_bohr"] = float(sub["delta_r_bohr"].iloc[0])
            row["delta_r_angstrom"] = float(sub["delta_r_angstrom"].iloc[0])
        sub = lambda_df[lambda_df.get("state", pd.Series(dtype=int)) == s]
        if not sub.empty:
            row["lambda_index"] = float(sub["lambda_index"].iloc[0])
        sub = nto_df[nto_df.get("state", pd.Series(dtype=int)) == s]
        if not sub.empty:
            row["nto_sum"] = (
                float(sub["nto_sum"].iloc[0])
                if "nto_sum" in sub.columns and pd.notna(sub["nto_sum"].iloc[0])
                else None
            )
            for i_e in range(1, 11):
                key = f"eig{i_e}"
                if key in sub.columns:
                    val = sub[key].iloc[0]
                    row[key] = float(val) if pd.notna(val) else None
        sub = ifct_summary_df[ifct_summary_df.get("state", pd.Series(dtype=int)) == s]
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
        summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows).sort_values("state")

    return {
        "summary_by_state": summary_df,
        "nto_eigs": nto_df,
        "delta_r": deltar_df,
        "lambda": lambda_df,
        "ifct_fragment_contrib": ifct_fragment_contrib_df,
        "ifct_population_variation": ifct_population_variation_df,
        "ifct_intrafragment_redistribution": ifct_intrafragment_redistribution_df,
        "ifct_transfers": ifct_transfers_df,
        "ifct_summary": ifct_summary_df,
    }


# ------------------ Markdown rendering helpers ------------------


def df_to_markdown_table(
    df: pd.DataFrame, float_fmt="{:.6f}", max_rows: Optional[int] = None
) -> str:
    """
    Render a pandas DataFrame as a Markdown table without external deps.
    - Numeric columns get formatted using float_fmt.
    - Truncates to max_rows if provided.
    """
    if df is None or df.empty:
        return "_No data found._\n"
    if max_rows is not None:
        df = df.head(max_rows).copy()

    # Prepare rows with formatted floats
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
    body_lines = []
    for _, row in df.iterrows():
        body_lines.append("| " + " | ".join(fmt_val(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + body_lines) + "\n"


def build_markdown_report(log_path: str, results: Dict[str, pd.DataFrame]) -> str:
    from datetime import datetime

    title = "# Multiwfn Excited-State Analysis (Markdown Report)\n"
    meta = f"- **Source log:** `{os.path.basename(log_path)}`\n- **Generated:** {datetime.now().isoformat(timespec='seconds')}\n\n"

    md = [title, meta]

    # Summary across states
    md.append("## Summary by state (NTO, Δr, λ, CT/LE)\n")
    md.append(df_to_markdown_table(results["summary_by_state"]))

    # NTO wide (optional detailed table)
    if not results["nto_eigs"].empty:
        md.append("\n## NTO eigenvalues (wide table)\n")
        md.append(df_to_markdown_table(results["nto_eigs"]))

    # IFCT blocks
    sections = [
        (
            "## IFCT: Fragment contributions (hole/electron %)\n",
            "ifct_fragment_contrib",
        ),
        ("## IFCT: Population variation (Δpopulation)\n", "ifct_population_variation"),
        (
            "## IFCT: Intrafragment electron redistribution\n",
            "ifct_intrafragment_redistribution",
        ),
        ("## IFCT: Transferred electrons between fragments\n", "ifct_transfers"),
        ("## IFCT: Summary (CT% / LE%)\n", "ifct_summary"),
    ]
    for title, key in sections:
        md.append("\n" + title)
        md.append(df_to_markdown_table(results[key]))

    return "".join(md)


# ------------------ Run and write files ------------------

log_path = "MultiWfn_Excited_States_Analysis_20250812_162411.log"
parsed = parse_multiwfn_log(log_path)

markdown_content = build_markdown_report(log_path, parsed)
md_path = "MultiWfn_Excited_States_Analysis_20250812_162411.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write(markdown_content)

# Also emit a plain text version (just strip the pipes to make it readable)
txt_path = "MultiWfn_Excited_States_Analysis_20250812_162411.txt"
txt_content = markdown_content.replace("|", "")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(txt_content)

print(f"Markdown report written to: {md_path}")
print(f"Plain text report written to: {txt_path}")
