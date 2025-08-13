#!/usr/bin/env bash
#
# ----------  SLURM DIRECTIVES  ------------------------------------------------
#SBATCH --job-name   Multiwfn            # Job name appears in squeue
#SBATCH --partition  general             # Partition / queue
#SBATCH --time       10:00:00            # HH:MM:SS
#SBATCH --nodes      1
#SBATCH --ntasks     32                  # Total CPU cores (not MPI ranks)
#SBATCH --mem        110G                # 110 GB for the whole node
#SBATCH --output     Multiwfn_%j.log     # Stdout  (%j = job-id)
#SBATCH --error      Multiwfn_%j.err     # Stderr  (keep separate if you like)

# ----------  BASH SAFETY / DEBUG OPTIONS  ------------------------------------
set -euo pipefail                          # “Strict” mode
umask 002                                  # Group-writeable files (optional)

# ----------  ENVIRONMENT / MODULES  ------------------------------------------
# Uncomment/modify to suit your cluster:
# module purge
# module load multiwfn
# or: source activate multiwfn-env

# ----------  LOGGING HEADER  --------------------------------------------------
echo "------------------------------------------------------------"
echo "Job started : $(date)"
echo "Job ID      : $SLURM_JOB_ID"
echo "Node list   : $SLURM_NODELIST"
echo "Cores       : $SLURM_NTASKS"
echo "Memory/node : ${SLURM_MEM_PER_NODE:-unknown}"
echo "Work dir    : $SLURM_SUBMIT_DIR"
echo "------------------------------------------------------------"

# Lift any soft-stack limits (some quantum-chemistry codes need this)
ulimit -s unlimited

# Optional wall-clock timer
t_start=$(date +%s)

# ----------  ACTUAL WORK  -----------------------------------------------------
# `srun` lets SLURM bind the 32 cores for you; remove it if the script
# internally launches its own MPI/OMP processes.
bash modularized_exst_analysis_multiwfn.sh ./examples/SP_ExSt_TDA_push_pull_system.fchk ./examples/SP_ExSt_TDA_push_pull_system.fchk --full --states 1-5 --frag1 "25-27" --frag2 "6,12-13,16-19,22-24" --frag3 "1-5,7-11,14-15,20-21"

# ----------  FINISH / FOOTER  -------------------------------------------------
t_end=$(date +%s)
runtime=$((t_end - t_start))

echo "------------------------------------------------------------"
echo "Job finished: $(date)"
echo "Total run   : $((runtime/3600))h $(((runtime%3600)/60))m $((runtime%60))s"
echo "------------------------------------------------------------"