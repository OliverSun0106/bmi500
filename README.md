# Environment Setup

1. either do 
```
conda create -n bmi500 python=3.12.4
```

or 

```
python3 -m venv bmi500
```

2. activate environment
```
conda activate bmi500
```

or 

```
source bmi500/bin/activate
```

3. Install required packages
```
pip install -r requirements.txt
```

It may be required to install g++ and cmake in order to install python louvain


4. run scanpy_pbmc.py
```
python scanpy_pbmc.py --data-dir {data_dir} --data-set {data_set} --out-dir {output_dir} --num-threads {num_thread}
```

`data_dir` is the top level directory in which the data_set subdirectories resides.  defaults to `data`

`output_dir` is where the output file is placed. defaults to `data`

`data_set` is one of 'pbmc3k', 'pbmc6k', and 'pbmc10k'.

## Homework profiling artifacts

Actual successful OddJobs runs are stored in `results/pbmc3k-1289747`,
`results/pbmc6k-1289760`, and `results/pbmc10k-1289774`. Each includes console
output, GNU time statistics, section timings, cProfile data, metadata, installed
versions, and snapshots of the measured source. Large `.h5ad` files and Numba
caches remain on disk but are ignored by Git. Do not use failed jobs as timings.

The tested cluster environment used `module load bmi/python-3.12` (Python
3.12.13) and `/home/zsun264/bmi500-venv`. After installing the original
requirements, these compatibility adjustments resolved observed import errors:

```bash
python -m pip install "anndata==0.10.8" "zarr==2.18.7" "setuptools==80.9.0"
```

`requirements-oddjobs.txt` records the resulting environment with `pip freeze`.
It records installed versions, not a guarantee of compatibility on every OS.
Run Python and package installation on an allocated compute node, following
OddJobs rules. Load the module and activate the environment before submission:

```bash
export BMI500_PYTHON=/home/zsun264/bmi500-venv/bin/python
sbatch --partition=overflow --export=ALL slurm/scanpy_pbmc.sbatch pbmc3k
```

Replace the dataset argument with `pbmc6k` or `pbmc10k` as needed, after extracting
the matching archive under `data/`. The current script specifies CPU core binding
to avoid the observed inherited-binding launch failure. The original successful
3K run predates this change; its script snapshot preserves that distinction.

For local analysis only (no Scanpy rerun), with NumPy and Matplotlib installed:

```bash
python analyze_profiles.py
```

This validates the three fixed successful runs and generates `profiling_report/`
and `scanpy_profiling.ipynb`. SHA-256 hashes in `source_manifest.csv` identify the
input evidence. The PDF and notebook cover profiling only, and are not the final
complete homework submission. The 20K values are explicitly modeled scenarios.
No quiz answers or required partner / independent AI reviews are included.

