# %%

from profile_sections import SectionTimer
section_timer = SectionTimer()

from typing_extensions import ParamSpecArgs
import numpy as np
import pandas as pd
import scanpy as sc

import time
import sys
import argparse
import cProfile
import json
import platform
from pathlib import Path

section_timer.finish('imports')

# %%
sc.settings.verbosity = 3             # verbosity: errors (0), warnings (1), info (2), hints (3)
sc.logging.print_header()
sc.settings.set_figure_params(dpi=80, facecolor='white')
# sc.settings.n_jobs = int(sys.argv[4])
sc.settings.n_jobs = 1

# Actual thread count is applied after argument parsing.

section_timer.finish('settings')

# %%
parser = argparse.ArgumentParser(description='Process arguments.')
parser.add_argument('--data-dir', type=str, help='Directory containing the dataset subdirectories', default='data')
parser.add_argument('--data-set', choices=['pbmc3k', 'pbmc6k', 'pbmc10k'], help='Dataset name, which is the subdirectory name', default='pbmc3k')
parser.add_argument('--out-dir', type=str, help='Output directory', required=False, default='data')
parser.add_argument('--num-threads', type=int, help='Number of threads', default=1, required=False)

args = parser.parse_args()

datadir = args.data_dir if args.data_dir.endswith('/') else args.data_dir + '/'
dataset = args.data_set 
outdir = args.out_dir if args.out_dir.endswith('/') else args.out_dir + '/'
nthreads = args.num_threads
if nthreads < 1:
    parser.error('--num-threads must be positive')
sc.settings.n_jobs = nthreads
print(f"using {sc.settings.n_jobs} threads")
Path(outdir).mkdir(parents=True, exist_ok=True)
section_timer.path = Path(outdir) / 'sections.csv'
metadata = {'dataset': dataset, 'threads': nthreads, 'scanpy_version': sc.__version__,
            'python_version': platform.python_version(), 'hostname': platform.node(),
            'scanpy_read_cache': False, 'status': 'running'}
metadata_path = Path(outdir) / 'metadata.json'
metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

section_timer.finish('arguments')

#%%

# I/O
results_file = "/".join([outdir, dataset + '.scanpy.h5ad'])  # the file that will store the analysis results

adata = sc.read_10x_mtx(
    #'/nethome/tpan7/scgc/data/' + dataset + '/filtered_gene_bc_matrices/hg19',  # the directory with the `.mtx` file
    "/".join([datadir, dataset, 'filtered_gene_bc_matrices']),  # the directory with the `.mtx` file
    var_names='gene_symbols',                # use gene symbols for the variable names (variables-axis index)
    cache=False)                              # disable Scanpy read cache for consistent profiling policy

metadata.update(input_cells=adata.n_obs, input_genes=adata.n_vars)
metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

adata.var_names_make_unique()  # this is unnecessary if using `var_names='gene_ids'` in `sc.read_10x_mtx`

section_timer.finish('read_data')

# %%
# preprocessing

# basic filtering
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)

section_timer.finish('filter')

#%%
# metric
#adata.var['mt'] = adata.var_names.str.startswith('MT-')  # annotate the group of mitochondrial genes as 'mt'
#sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

# filtering by slicing the AnnData object
#adata = adata[adata.obs.n_genes_by_counts < 2500, :]
#adata = adata[adata.obs.pct_counts_mt < 5, :]


# and normalize to 10K reads per cell
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

section_timer.finish('normalize_log')

# %%
# highly variable genes

#sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
sc.pp.highly_variable_genes(adata, flavor="seurat", n_top_genes=2000)

# freeze data.
adata.raw = adata

# filtering by highly variable genes.
adata = adata[:, adata.var.highly_variable]

section_timer.finish('highly_variable_genes')

#%%
# regres out effects of total counts per cell an d% mitochondrial genes
#sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt'])
sc.pp.scale(adata)

section_timer.finish('scale')

# %%
# report adata - so we can check ot see if we are comparable to Seurat
# adata.write(results_file)
# adata

section_timer.finish('report_placeholder')

# %%
# pca.  parallel via OMP_NUM_THREADS
sc.tl.pca(adata, svd_solver='arpack', n_comps=30)

# adata.write(results_file)
# adata

section_timer.finish('pca')

# %%
# neighborhood graph
sc.pp.neighbors(adata, n_pcs=30)

section_timer.finish('neighbors')

# %% 
# for fixing disconnected clusters or connectivity issues:
#sc.tl.paga(adata)
#sc.pl.paga(adata, plot=False)  # remove `plot=False` if you want to see the coarse-grained graph
#cs.tl.umap(adata, init_pos='paga')


# adata.write(results_file)
# adata

section_timer.finish('paga_placeholder')

# %%
# clustering  (currently uses leiden,  previously using louvain (like Seurat).)
#sc.tl.leiden(adata)
sc.tl.louvain(adata, resolution = 0.5)

section_timer.finish('louvain')

#%%
# umap
sc.tl.umap(adata, n_components=30)

section_timer.finish('umap')

#%%
adata.write(results_file)
adata

section_timer.finish('write_h5ad')

# %%
# support t-test, wilcoxon, logistic regression
# find marker genes
profiler = cProfile.Profile()
profiler.enable()
try:
    sc.tl.rank_genes_groups(adata, 'louvain', method='wilcoxon', use_raw=True)
finally:
    profiler.disable()
    profiler.dump_stats(str(Path(outdir) / 'rank_genes_groups.prof'))

section_timer.finish('rank_genes_groups')

metadata.update(status='complete', analyzed_cells=adata.n_obs, analyzed_genes=adata.n_vars)
metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
