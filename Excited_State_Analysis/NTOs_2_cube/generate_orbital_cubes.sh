#!/usr/bin/env bash
#===============================================================================
# Developer: Ajay Khanna
# Lab: Dr. Tretiak
# Date: Aug.13.2025
# Place: Los Alamos National Laboratory (LANL)
# Project: Mesoscale Materials for Energy Transport Applications
# Name: excited_state_multiwfn.sh
#
# Purpose:
#   Streamlined: run Multiwfn once per state and rename the produced "orbital.cub"
#   to "S<state>_orbs000584_589.cub" (e.g., S3_orbs000585_589.cub)
#

set -euo pipefail # Strict mode: exit on error, undefined vars, and pipe failures

# -------- Configuration --------
MULTIWFN_BIN="${MULTIWFN_BIN:-multiwfn}"   # Path/name of Multiwfn binary
STATE_PREFIX="${STATE_PREFIX:-S}"          # Input files look like S<state>.mwfn
INPUT_EXT="${INPUT_EXT:-.mwfn}"            # Extension of Multiwfn input files
ORBITAL_RANGE="${ORBITAL_RANGE:-584-589}"  # e.g. "584-589" (can be "10,12,15-18" too)
OUTDIR="${OUTDIR:-cube_out}"               # Where to put renamed .cub files
LOGDIR="${LOGDIR:-logs}"                   # Logs per state
JOBS="${JOBS:-1}"                          # Parallel jobs
DRY_RUN="${DRY_RUN:-0}"                    # 1 = print actions, 0 = run

# Multiwfn menu sequence (your exact inputs)
SEQ_PRE="200"$'\n'"3"$'\n'
SEQ_POST=$'\n''3'$'\n''2'$'\n''0'$'\n''q'$'\n'

usage() {
  cat <<EOF
Usage: $0 STATE_LIST...

STATE_LIST can be:
  - Space-separated states ("1 2 3")
  - A range like "1-5"
  - A mix, e.g. "1 3 5-7"

Env vars:
  MULTIWFN_BIN   Path to multiwfn (default: "multiwfn" in PATH)
  STATE_PREFIX   Prefix for input files (default: "S")
  INPUT_EXT      Input extension (default: ".mwfn")
  ORBITAL_RANGE  Orbital list/range (default: "584-589")
  OUTDIR         Output dir for renamed .cub (default: "cube_out")
  LOGDIR         Log dir (default: "logs")
  JOBS           Parallel jobs (default: 1)
  DRY_RUN        1=print plan only

Example:
  ORBITAL_RANGE="585-589" ./generate_orbital_cubes.sh 1-4
EOF
}

expand_ranges() {
  # Expand tokens like "1 3 5-7" -> "1 3 5 6 7"
  local out=() tok start end
  for tok in "$@"; do
    if [[ "$tok" =~ ^[0-9]+-[0-9]+$ ]]; then
      start="${tok%-*}"; end="${tok#*-}"
      (( start<=end )) || { echo "Invalid range: $tok" >&2; exit 1; }
      for ((i=start;i<=end;i++)); do out+=("$i"); done
    elif [[ "$tok" =~ ^[0-9]+$ ]]; then
      out+=("$tok")
    else
      echo "Bad state token: $tok" >&2; exit 1
    fi
  done
  printf "%s\n" "${out[@]}"
}

# Parse ORBITAL_RANGE to (start,end) for filename.
# - If it's "a-b", use a and b.
# - If it's lists/ranges, we take global min and max numbers found.
derive_orb_bounds() {
  local rng="$1" n min="" max=""
  # Extract all integers in order
  while read -r n; do
    [[ -z "$min" || "$n" -lt "$min" ]] && min="$n"
    [[ -z "$max" || "$n" -gt "$max" ]] && max="$n"
  done < <(grep -oE '[0-9]+' <<<"$rng")
  [[ -n "$min" && -n "$max" ]] || { echo "Could not parse ORBITAL_RANGE: $rng" >&2; return 1; }
  printf "%s %s\n" "$min" "$max"
}

run_one_state() {
  local state="$1"
  local infile="${STATE_PREFIX}${state}${INPUT_EXT}"
  local log="${LOGDIR}/state_${state}.log"

  if [[ ! -f "$infile" ]]; then
    echo "[state $state] Missing input file: $infile" >&2
    return 2
  fi

  mkdir -p "$OUTDIR" "$LOGDIR"

  # Build Multiwfn input payload
  local payload="${SEQ_PRE}${ORBITAL_RANGE}${SEQ_POST}"

  # Determine filename based on ORBITAL_RANGE
  local start end start6 end3 newname
  read -r start end < <(derive_orb_bounds "$ORBITAL_RANGE")
  start6=$(printf "%06d" "$start")
  end3=$(printf "%03d" "$end")
  newname="${STATE_PREFIX}${state}_orbs${start6}_${end3}.cub"

  echo "[state $state] Running Multiwfn on ${infile} -> ${newname}"
  if [[ "$DRY_RUN" == "1" ]]; then
    printf "-----BEGIN MULTIWFN INPUT (state %s)-----\n%s-----END MULTIWFN INPUT-----\n" "$state" "$payload"
    echo "[state $state] Would move ./orbital.cub -> ${OUTDIR}/${newname}"
    return 0
  fi

  # Remove any stale orbital.cub before run to avoid confusion
  [[ -f orbital.cub ]] && rm -f orbital.cub

  # Run Multiwfn non-interactively
  if ! { printf "%s" "$payload" | "$MULTIWFN_BIN" "$infile"; } >"$log" 2>&1; then
    echo "[state $state] Multiwfn failed; see $log" >&2
    return 1
  fi

  # Immediately rename/move the generated file
  if [[ -f "orbital.cub" ]]; then
    mv -f "orbital.cub" "${OUTDIR}/${newname}"
    echo "[state $state] Saved: ${OUTDIR}/${newname} (log: ${log})"
  else
    echo "[state $state] Expected orbital.cub not found; check ${log}" >&2
    return 3
  fi
}

main() {
  if (( $# == 0 )) || [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage; exit 0
  fi

  # Expand user-provided state list/ranges
  mapfile -t STATES < <(expand_ranges "$@")

  # Ensure Multiwfn is available
  if ! command -v "$MULTIWFN_BIN" >/dev/null 2>&1; then
    echo "Error: Multiwfn not found at '${MULTIWFN_BIN}'. Set MULTIWFN_BIN or add to PATH." >&2
    exit 1
  fi

  export -f run_one_state derive_orb_bounds
  export MULTIWFN_BIN STATE_PREFIX INPUT_EXT ORBITAL_RANGE OUTDIR LOGDIR DRY_RUN SEQ_PRE SEQ_POST

  # Sequential or parallel
  if (( JOBS > 1 )); then
    printf "%s\n" "${STATES[@]}" | xargs -I{} -P "$JOBS" bash -c 'run_one_state "$@"' _ {}
  else
    for s in "${STATES[@]}"; do
      run_one_state "$s"
    done
  fi

  echo "Done. Renamed CUBE files are in: ${OUTDIR}/"
}

main "$@"


