#!/bin/bash
#SBATCH --job-name=bmi500-pbmc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%j.out

set -euo pipefail
: "${SLURM_JOB_ID:?Submit this script with sbatch}"
: "${SLURM_SUBMIT_DIR:?Missing Slurm working directory}"
cd "$SLURM_SUBMIT_DIR"
dataset="${1:-pbmc3k}"
case "$dataset" in pbmc3k|pbmc6k|pbmc10k) ;; *) echo 'Invalid dataset' >&2; exit 2 ;; esac
# Activate the README environment before sbatch; use its absolute Python path.
python_bin="${BMI500_PYTHON:-$(command -v python)}"
test -x "$python_bin"
test -x /usr/bin/time
test -f "data/$dataset/filtered_gene_bc_matrices/matrix.mtx"
run_dir="$PWD/results/${dataset}-${SLURM_JOB_ID}"
mkdir -p "$run_dir"
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export MKL_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export NUMEXPR_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export NUMBA_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export MPLBACKEND=Agg
export LC_ALL=C
# Separate JIT cache for each run; OS filesystem caches are not controlled.
export NUMBA_CACHE_DIR="$run_dir/numba-cache"
{
    date -u
    hostname
    printf 'job=%s dataset=%s cpus=%s python=%s\n' "$SLURM_JOB_ID" "$dataset" "$SLURM_CPUS_PER_TASK" "$python_bin"
    git rev-parse HEAD
    git status --short
    "$python_bin" --version
    "$python_bin" -m pip freeze
} > "$run_dir/environment.txt" 2>&1
# Record the exact measured sources, including uncommitted modifications.
cp scanpy_pbmc.py profile_sections.py "$run_dir/"
cp slurm/scanpy_pbmc.sbatch "$run_dir/"
set +e
srun /usr/bin/time -v -o "$run_dir/time.txt" \
    "$python_bin" -u scanpy_pbmc.py --data-dir data --data-set "$dataset" \
    --out-dir "$run_dir" --num-threads "$SLURM_CPUS_PER_TASK" \
    > "$run_dir/console.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$run_dir/exit_code.txt"
exit "$status"
