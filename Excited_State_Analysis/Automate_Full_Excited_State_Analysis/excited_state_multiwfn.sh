#!/usr/bin/env bash
#===============================================================================
# Developer: Ajay Khanna
# Lab: Dr. Tretiak
# Date: Aug.12.2025
# Place: Los Alamos National Laboratory (LANL)
# Project: Mesoscale Materials for Energy Transport Applications
# Name: excited_state_multiwfn.sh
# Purpose: Automate excited-state analyses (NTO, MO, Lambda Index, Delta_R, Inter Fragment Charge Transfer) in Multiwfn for Gaussian results.
#
# Usage:
#   ./excited_state_multiwfn.sh INPUT.fch[k] INPUT.log \
#       [--states A-B] \
#       [--multiwfn /path/to/Multiwfn] \
#       [--nFrags N] [--frag1 "RANGES"] ... [--fragN "RANGES"]
#
# Examples:
#   ./excited_state_multiwfn.sh sample.fchk sample.log
#   ./excited_state_multiwfn.sh sample.fch sample.log --states 1-5 --multiwfn /opt/Multiwfn/Multiwfn
#   ./excited_state_multiwfn.sh sample.fchk sample.log --nFrags 2 --frag1 "1-3, 4, 5-7" --frag2 "4,6,11-15"
#   ./excited_state_multiwfn.sh sample.fchk sample.log --nFrags 4 \
#       --frag1 "1-3,4,5-7" --frag2 "4,6,11-15" --frag3 "16-20,3,2" --frag4 "21-25,29"
#
# Inputs (required):
#   1) Formatted checkpoint: .fch or .fchk   (no .chk accepted)
#   2) Gaussian output log: .log
#
# Fragment syntax:
#   Lists and ranges separated by commas (spaces optional):
#     1,2   | 1-2   | 1-2, 3   | 1-2,3-5, 7
#
# Output:
#   - Per-state Multiwfn outputs (e.g., ${state}.mwfn, etc.)
#   - Log file: MultiWfn_Excited_States_Analysis_YYYYMMDD_HHMMSS.log
#===============================================================================

set -Eeuo pipefail

STATE_RANGE="1-5"
MULTIWFN_BIN="${MULTIWFN_BIN:-${MULTIWFN:-${multiwfn:-Multiwfn}}}"  # env override or PATH

# Default fragments (used when --nFrags is omitted; user may override any of these three)
FRAG_DEFAULTS=( \
  "25-27" \
  "6,12-13,16-19,22-24" \
  "1-5,7-11,14-15,20-21" \
)

print_usage() {
  sed -n '1,80p' "$0" | sed -n '2,80p' | sed -n '2,80p' >/dev/null 2>&1 || true
  cat <<'USAGE'
Usage:
  excited_state_multiwfn.sh INPUT.fch[k] INPUT.log [--states A-B] [--multiwfn PATH]
                            [--nFrags N] [--frag1 "RANGES"] ... [--fragN "RANGES"]

Examples:
  ./excited_state_multiwfn.sh SP_ExSt_TDA_push_pull_system.fchk SP_ExSt_TDA_push_pull_system.log
  ./excited_state_multiwfn.sh SP_ExSt_TDA_push_pull_system.fch  SP_ExSt_TDA_push_pull_system.log --states 1-5 --multiwfn /opt/Multiwfn/Multiwfn
  ./excited_state_multiwfn.sh SP_ExSt_TDA_push_pull_system.fchk SP_ExSt_TDA_push_pull_system.log --nFrags 3 --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"

Fragments syntax:
  Accepts lists and ranges separated by commas (spaces optional):
    1,2  | 1-2  | 1-2, 3  | 1-2,3-5, 7
USAGE
}

normalize_fragment() {
  # Trim whitespace; validate pattern like: 1,2 or 1-3,4,7-9
  local raw="${1:-}"
  local cleaned
  cleaned="$(echo "$raw" | sed -E 's/[[:space:]]+//g')"
  if [[ -z "$cleaned" ]]; then
    echo "ERROR: Empty fragment specification." >&2
    return 1
  fi
  if [[ ! "$cleaned" =~ ^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$ ]]; then
    echo "ERROR: Invalid fragment spec '$raw'. Use forms like '1,2' or '1-2,3-5,7'." >&2
    return 1
  fi
  echo "$cleaned"
}

# ----------------------------- Parse CLI --------------------------------------
if (( $# < 2 )); then
  print_usage; exit 1
fi

INPUT_FCHK="$1"; shift
INPUT_LOG="$1"; shift

NFRAGS=""
declare -A FRAG_MAP=()  # key: index (1..N), value: normalized string

while (( $# > 0 )); do
  case "${1:-}" in
    -h|--help) print_usage; exit 0 ;;
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
      # Extract index and normalize the value
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

# ----------------------------- Validation -------------------------------------
# 1) Formatted checkpoint only (.fch/.fchk)
ext_fchk="${INPUT_FCHK##*.}"
case "${ext_fchk,,}" in
  fch|fchk) : ;;
  *) echo "ERROR: First argument must be .fch or .fchk (no .chk allowed): $INPUT_FCHK"; exit 1;;
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

# 4) State range expand
IFS='-' read -r STATE_START STATE_END <<<"$STATE_RANGE"
if (( STATE_START <= 0 || STATE_END < STATE_START )); then
  echo "ERROR: Invalid state range: $STATE_RANGE"; exit 1
fi
STATE_LIST=(); for (( s=STATE_START; s<=STATE_END; s++ )); do STATE_LIST+=("$s"); done

# 5) Determine fragments:
declare -a FRAG_LIST=()

if [[ -z "$NFRAGS" ]]; then
  # Default mode: 3 fragments. Fill with defaults; allow overriding frag1..frag3 if provided.
  NFRAGS=3
  for i in 1 2 3; do
    if [[ -n "${FRAG_MAP[$i]:-}" ]]; then
      FRAG_LIST+=("${FRAG_MAP[$i]}")
    else
      FRAG_LIST+=("${FRAG_DEFAULTS[$((i-1))]}")
    fi
  done
  # If user tried to supply frag>3 without --nFrags, warn/error
  for k in "${!FRAG_MAP[@]}"; do
    if (( k > 3 )); then
      echo "ERROR: You specified --frag$k but did not set --nFrags $k+. Provide --nFrags or remove extra fragments."
      exit 1
    fi
  done
else
  # User specified NFRAGS: require frag1..fragN provided
  for (( i=1; i<=NFRAGS; i++ )); do
    if [[ -z "${FRAG_MAP[$i]:-}" ]]; then
      echo "ERROR: --nFrags $NFRAGS requires --frag$i to be specified."
      exit 1
    fi
    FRAG_LIST+=("${FRAG_MAP[$i]}")
  done
fi

# Build newline-delimited fragment inputs for Multiwfn
FRAG_INPUTS="$(printf '%s\n' "${FRAG_LIST[@]}")"

# ----------------------------- Logging ----------------------------------------
multiwfn_logfile="MultiWfn_Excited_States_Analysis_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$multiwfn_logfile") 2>&1

echo "=== Starting Excited-State Analysis @ $(date) ==="
echo "Multiwfn binary : $MULTIWFN_BIN"
echo "Formatted chk   : $INPUT_FCHK"
echo "Gaussian log    : $INPUT_LOG"
echo "States          : ${STATE_START}-${STATE_END}"
echo "Fragments (N)   : $NFRAGS"
for (( i=1; i<=NFRAGS; i++ )); do
  echo "  Fragment_$i    : ${FRAG_LIST[$((i-1))]}"
done
echo "Output log      : $multiwfn_logfile"
echo "Required files  :"
echo "  - $INPUT_FCHK"
echo "  - $INPUT_LOG"
echo

# ----------------------------- Runner -----------------------------------------
run_multiwfn_for_state() {
  local fchk="$1" log="$2" state="$3"

  echo "--- Running Multiwfn for State $state ---"

  # Compose IFCT fragments block: first the number of fragments, then each line
  IFCT_FRAG_BLOCK="$(printf '%s\n%s' "$NFRAGS" "$FRAG_INPUTS")"
  # CTS uses the same fragments block (without the leading number in our old script,
  # but in your menu flow the number precedes the lists; keep consistent with IFCT)
  CTS_FRAG_BLOCK="$IFCT_FRAG_BLOCK"

  # Build blocks exactly as sent to Multiwfn
  IFCT_FRAG_BLOCK="$(printf '%s\n' "$NFRAGS" "${FRAG_LIST[@]}")"
  CTS_FRAG_BLOCK="$IFCT_FRAG_BLOCK"   # or: CTS_FRAG_BLOCK="$(printf '%s\n' "${FRAG_LIST[@]}")" if CTS doesn’t need the count

  echo "IFCT fragments → stdin (State $state):"
  printf '%s\n' "$IFCT_FRAG_BLOCK" | sed 's/^/  > /'

  echo "CTS fragments → stdin (State $state):"
  printf '%s\n' "$CTS_FRAG_BLOCK" | sed 's/^/  > /'

  # Feed Multiwfn (numbers only; no shell echoes in the stream)
  "$MULTIWFN_BIN" "$fchk" <<EOF
18
6
${log}
${state}
3
S${state}.mwfn
4
${log}
${state}
n
14
${state}
n
n
8
2
${state}
${IFCT_FRAG_BLOCK}
0
1
${state}
2
0.2
0
0
q
EOF

  echo "--- Completed State $state ---"
  echo
}

for state in "${STATE_LIST[@]}"; do
  run_multiwfn_for_state "$INPUT_FCHK" "$INPUT_LOG" "$state"
done

echo "=== All tasks completed @ $(date) ==="


