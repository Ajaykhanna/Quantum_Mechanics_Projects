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
#   Modular Multiwfn automation for Gaussian excited-state analyses.
#   Run any subset of analyses or everything (--full) with λ run LAST.
#
# Analyses supported (flags):
#   --full      : run NTO, Δr, IFCT, CTS, MO for all states, then run λ at the end
#   --nto       : NTO only
#   --deltaR    : Δr only
#   --ifct      : IFCT only (requires fragments)
#   --cts       : CTS only  (requires fragments)
#   --mo        : Excited-state MO plots only
#   --lambda    : λ (lambda index) only
#
# Inputs (required):
#   1) Formatted checkpoint: .fch or .fchk   (no .chk accepted)
#   2) Gaussian output log: .log
#
# Fragment syntax (ONLY for IFCT/CTS, otherwise ignored):
#   --nFrags N
#   --frag1 "1-3, 5, 7-10"   --frag2 "..." ... --fragN "..."
#
# Output:
#   - Per-state outputs (e.g., S${state}.mwfn for NTO)
#   - Unified log: MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log
#===============================================================================

set -Eeuo pipefail

# ----------------------------- Defaults ---------------------------------------
# Default to a single state if --states is not provided
STATE_RANGE="1-1"
MULTIWFN_BIN="${MULTIWFN_BIN:-${MULTIWFN:-${multiwfn:-Multiwfn}}}"  # env override or PATH

# Defaults for fragments (used only if IFCT/CTS is requested and --nFrags omitted)
FRAG_DEFAULTS=(
  "25-27"
  "6,12-13,16-19,22-24"
  "1-5,7-11,14-15,20-21"
)

# ----------------------------- Usage ------------------------------------------
print_usage() {
  cat <<'USAGE'
Usage:
  excited_state_multiwfn.sh INPUT.fch[k] INPUT.log [analysis flags] [options]

Analysis flags (choose any; if none given -> --full):
  --full            Run NTO, Δr, IFCT, CTS, MO for all states; then run λ at the end
  --nto             Run NTO only
  --deltaR          Run Δr only
  --ifct            Run IFCT only (requires fragments)
  --cts             Run CTS only  (requires fragments)
  --mo              Run excited-state MO plots only
  --lambda          Run λ only

Options:
  --states A-B      State range (default: 1)
  --multiwfn PATH   Path to Multiwfn binary (default: env or PATH)
  --nFrags N        Number of fragments (IFCT/CTS only; default 3)
  --frag1 "RANGES"  e.g., "1-3,5,7-10" (IFCT/CTS only)
  --frag2 "RANGES"  ...
  --fragN "RANGES"  ...

Examples:
  ./excited_state_multiwfn.sh sample.fchk sample.log --full
  ./excited_state_multiwfn.sh sample.fchk sample.log --nto --mo --states 1-3
  ./excited_state_multiwfn.sh sample.fchk sample.log --ifct --nFrags 3 \
      --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"
  ./excited_state_multiwfn.sh sample.fchk sample.log --cts --nFrags 3 \
      --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"
USAGE
}

# ----------------------------- Helpers ----------------------------------------
normalize_fragment() {
  local raw="${1:-}"
  local cleaned
  cleaned="$(echo "$raw" | sed -E 's/[[:space:]]+//g')"
  if [[ -z "$cleaned" ]]; then
    echo "ERROR: Empty fragment specification." >&2
    return 1
  fi
  if [[ ! "$cleaned" =~ ^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$ ]]; then
    echo "ERROR: Invalid fragment spec '$raw'. Use '1,2' or '1-2,3-5,7'." >&2
    return 1
  fi
  echo "$cleaned"
}

make_state_list() {
  local range="$1"
  IFS='-' read -r STATE_START STATE_END <<<"$range"
  if (( STATE_START <= 0 || STATE_END < STATE_START )); then
    echo "ERROR: Invalid state range: $range" >&2
    return 1
  fi
  local out=()
  for (( s=STATE_START; s<=STATE_END; s++ )); do out+=("$s"); done
  printf '%s\n' "${out[@]}"
}

# ----------------------------- Parse CLI --------------------------------------
if (( $# < 2 )); then
  print_usage; exit 1
fi

INPUT_FCHK="$1"; shift
INPUT_LOG="$1"; shift

RUN_FULL=false
RUN_NTO=false
RUN_DELTAR=false
RUN_IFCT=false
RUN_CTS=false
RUN_MO=false
RUN_LAMBDA=false

NFRAGS=""
declare -A FRAG_MAP=()  # key: index (1..N), value: normalized string

while (( $# > 0 )); do
  case "${1:-}" in
    -h|--help) print_usage; exit 0 ;;
    --full)    RUN_FULL=true; shift; continue ;;
    --nto)     RUN_NTO=true; shift; continue ;;
    --deltaR)  RUN_DELTAR=true; shift; continue ;;
    --ifct)    RUN_IFCT=true; shift; continue ;;
    --cts)     RUN_CTS=true; shift; continue ;;
    --mo)      RUN_MO=true; shift; continue ;;
    --lambda)  RUN_LAMBDA=true; shift; continue ;;
    --states)
      shift
      [[ "${1:-}" =~ ^[0-9]+-[0-9]+$ ]] || { echo "ERROR: --states must be like 1-10"; exit 1; }
      STATE_RANGE="$1"; shift; continue;;
    --multiwfn)
      shift
      [[ -n "${1:-}" ]] || { echo "ERROR: --multiwfn requires a path"; exit 1; }
      MULTIWFN_BIN="$1"; shift; continue;;
    --nFrags)
      shift
      [[ "${1:-}" =~ ^[0-9]+$ && "${1:-}" -ge 1 ]] || { echo "ERROR: --nFrags must be a positive integer"; exit 1; }
      NFRAGS="$1"; shift; continue;;
    --frag[0-9]*)
      localopt="$1"; shift
      idx="${localopt#--frag}"
      [[ "$idx" =~ ^[0-9]+$ && "$idx" -ge 1 ]] || { echo "ERROR: Bad fragment option '$localopt'"; exit 1; }
      val="$(normalize_fragment "${1:-}")" || exit 1
      FRAG_MAP["$idx"]="$val"
      shift; continue;;
    -*)
      echo "ERROR: Unknown option: $1"; print_usage; exit 1;;
    *)
      echo "ERROR: Unexpected positional argument: $1"; print_usage; exit 1;;
  esac
done

# If no analysis flags given, default to full
if ! $RUN_FULL && ! $RUN_NTO && ! $RUN_DELTAR && ! $RUN_IFCT && ! $RUN_CTS && ! $RUN_MO && ! $RUN_LAMBDA; then
  RUN_FULL=true
fi

# If full, run all (λ to be scheduled last)
if $RUN_FULL; then
  RUN_NTO=true
  RUN_DELTAR=true
  RUN_IFCT=true
  RUN_CTS=true
  RUN_MO=true
  RUN_LAMBDA=true
fi

# ----------------------------- Validation -------------------------------------
# 1) Formatted checkpoint only (.fch/.fchk)
ext_fchk="${INPUT_FCHK##*.}"
case "${ext_fchk,,}" in
  fch|fchk) : ;;
  *) echo "ERROR: First argument must be .fch or .fchk (no .chk): $INPUT_FCHK"; exit 1;;
esac
[[ -f "$INPUT_FCHK" ]] || { echo "ERROR: File not found: $INPUT_FCHK"; exit 1; }

# 2) Gaussian .log
ext_log="${INPUT_LOG##*.}"
[[ "${ext_log,,}" == "log" ]] || { echo "ERROR: Second argument must be a .log file: $INPUT_LOG"; exit 1; }
[[ -f "$INPUT_LOG" ]] || { echo "ERROR: File not found: $INPUT_LOG"; exit 1; }

# 3) Multiwfn binary present
if ! command -v "$MULTIWFN_BIN" >/dev/null 2>&1; then
  echo "ERROR: Multiwfn binary not found/executable: $MULTIWFN_BIN"
  exit 1
fi

# 4) States (defaults to 1 if --states not provided)
mapfile -t STATE_LIST < <(make_state_list "$STATE_RANGE")

# 5) IFCT/CTS fragments — only if IFCT or CTS requested
declare -a FRAG_LIST=()
IFCT_FRAG_BLOCK=""
if $RUN_IFCT || $RUN_CTS; then
  if [[ -z "$NFRAGS" ]]; then
    # default: 3 fragments, allow overrides of frag1..frag3
    NFRAGS=3
    for i in 1 2 3; do
      if [[ -n "${FRAG_MAP[$i]:-}" ]]; then
        FRAG_LIST+=("${FRAG_MAP[$i]}")
      else
        FRAG_LIST+=("${FRAG_DEFAULTS[$((i-1))]}")
      fi
    done
    # error if user tried to pass frag>3 without --nFrags
    for k in "${!FRAG_MAP[@]}"; do
      if (( k > 3 )); then
        echo "ERROR: You specified --frag$k but did not set --nFrags $k+. Use --nFrags first."
        exit 1
      fi
    done
  else
    # require frag1..fragN
    for (( i=1; i<=NFRAGS; i++ )); do
      if [[ -z "${FRAG_MAP[$i]:-}" ]]; then
        echo "ERROR: --nFrags $NFRAGS requires --frag$i to be specified."
        exit 1
      fi
      FRAG_LIST+=("${FRAG_MAP[$i]}")
    done
  fi
  IFCT_FRAG_BLOCK="$(printf '%s\n' "$NFRAGS" "${FRAG_LIST[@]}")"
else
  # IFCT/CTS not requested: ignore fragments if any were provided
  if (( ${#FRAG_MAP[@]} > 0 || ${#NFRAGS} > 0 )); then
    echo "Note: --frag* / --nFrags provided but neither --ifct nor --cts requested; ignoring fragment inputs."
  fi
fi

# ----------------------------- Logging header ---------------------------------
multiwfn_logfile="MultiWfn_Excited_States_Analysis_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$multiwfn_logfile") 2>&1

echo "=== Starting Excited-State Analysis @ $(date) ==="
echo "Multiwfn binary : $MULTIWFN_BIN"
echo "Formatted chk   : $INPUT_FCHK"
echo "Gaussian log    : $INPUT_LOG"
echo "States          : $STATE_RANGE (default is 1 if not provided)"
echo "Analyses        : $(
  printf '%s' "$( $RUN_FULL && echo full || echo selective)"
)"
echo "  - NTO     : $RUN_NTO"
echo "  - Delta_r : $RUN_DELTAR"
echo "  - IFCT    : $RUN_IFCT"
echo "  - CTS     : $RUN_CTS"
echo "  - MO      : $RUN_MO"
echo "  - Lambda  : $RUN_LAMBDA (runs last only if --full)"
if $RUN_IFCT || $RUN_CTS; then
  echo "Fragments (N)   : $NFRAGS"
  for (( i=1; i<=NFRAGS; i++ )); do
    echo "  Fragment_$i    : ${FRAG_LIST[$((i-1))]}"
  done
fi
echo "Output log      : $multiwfn_logfile"
echo

# ----------------------------- Analysis funcs ---------------------------------
run_nto_for_state() {
  local fchk="$1" log="$2" state="$3"
  echo "[NTO] State $state"
  if ! "$MULTIWFN_BIN" "$fchk" <<EOF
18
6
${log}
${state}
3
S${state}.mwfn
0
q
EOF
  then
    echo "WARN: NTO failed for state $state"
    return 1
  fi
}

run_deltaR_for_state() {
  local fchk="$1" log="$2" state="$3"
  echo "[Delta_r] State $state"
  if ! "$MULTIWFN_BIN" "$fchk" <<EOF
18
4
${log}
${state}
n
0
q
EOF
  then
    echo "WARN: Delta_r failed for state $state"
    return 1
  fi
}

run_lambda_for_state() {
  local fchk="$1" log="$2" state="$3"
  echo "[Lambda] State $state"
  if ! "$MULTIWFN_BIN" "$fchk" <<EOF
18
14
${log}
${state}
n
n
0
q
EOF
  then
    echo "WARN: Lambda failed for state $state"
    return 1
  fi
}

run_ifct_for_state() {
  local fchk="$1" log="$2" state="$3"
  echo "[IFCT] State $state"

  # Show exactly what we feed (debug)
  echo "[DEBUG] IFCT fragments → stdin (State $state):"
  printf '%s\n' "$IFCT_FRAG_BLOCK" | sed 's/^/  > /'

  if ! "$MULTIWFN_BIN" "$fchk" <<EOF
18
8
2
${log}
${state}
${IFCT_FRAG_BLOCK}
0
0
q
EOF
  then
    echo "WARN: IFCT failed for state $state"
    return 1
  fi
}

run_cts() {
  local fchk="$1" log="$2"
  echo "[CTS] Running once for all excited states present in: $log"

  echo "[DEBUG] CTS fragments → stdin:"
  printf '%s\n' "$IFCT_FRAG_BLOCK" | sed 's/^/  > /'

  "$MULTIWFN_BIN" "$fchk" <<EOF
18
16
${IFCT_FRAG_BLOCK}
${log}
2
0
q
EOF
}

run_mo_for_state() {
  local fchk="$1" log="$2" state="$3"
  echo "[MO] State $state"
  if ! "$MULTIWFN_BIN" "$fchk" <<EOF
18
1
${log}
${state}
2
0.2
0
0
q
EOF
  then
    echo "WARN: MO plotting failed for state $state"
    return 1
  fi
}

# ----------------------------- Orchestration ----------------------------------
# 1) Run the "fast" / non-lambda analyses per state (λ deferred if --full)
for state in "${STATE_LIST[@]}"; do
  echo "--- State $state ---"

  $RUN_NTO     && run_nto_for_state    "$INPUT_FCHK" "$INPUT_LOG" "$state" || true
  $RUN_DELTAR  && run_deltaR_for_state "$INPUT_FCHK" "$INPUT_LOG" "$state" || true
  $RUN_IFCT    && run_ifct_for_state   "$INPUT_FCHK" "$INPUT_LOG" "$state" || true
  $RUN_MO      && run_mo_for_state     "$INPUT_FCHK" "$INPUT_LOG" "$state" || true

  echo "--- Completed (non-lambda) for State $state ---"
  echo
done

# 2) Run CTS ONCE (Multiwfn internally iterates over all states in the .log)
if $RUN_CTS; then
  echo ">>> Running CTS once (Multiwfn processes all excited states found in ${INPUT_LOG})..."
  # You can pass any placeholder state; the function won’t use it.
  run_cts "$INPUT_FCHK" "$INPUT_LOG" || true
fi

# 3) If lambda was requested:
#    - If --full: run lambda AFTER all other analyses finish (globally last)
#    - If only --lambda (or selective incl. lambda), we still run it here
if $RUN_LAMBDA; then
  if $RUN_FULL; then
    echo ">>> Running Lambda (deferred) for all states..."
  else
    echo ">>> Running Lambda for requested states..."
  fi
  for state in "${STATE_LIST[@]}"; do
    run_lambda_for_state "$INPUT_FCHK" "$INPUT_LOG" "$state" || true
  done
fi

echo "=== All requested analyses completed @ $(date) ==="


