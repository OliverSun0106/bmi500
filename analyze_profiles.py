"""Generate figures and a profiling-only report from actual OddJobs artifacts.

Run locally: python analyze_profiles.py
Requires matplotlib and numpy. Does not run Scanpy or any cluster experiment.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import pstats
import re
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'profiling_report'
RUNS = ['pbmc3k-1289747', 'pbmc6k-1289760', 'pbmc10k-1289774']


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_run(name):
    path = ROOT / 'results' / name
    meta = json.loads((path / 'metadata.json').read_text())
    if (path / 'exit_code.txt').read_text().strip() != '0' or meta['status'] != 'complete':
        raise ValueError(f'Incomplete run: {name}')
    raw = (path / 'time.txt').read_text()
    def field(label):
        return re.search(r'^\s*' + re.escape(label) + r':\s*(.+)$', raw, re.M).group(1)
    if field('Exit status') != '0':
        raise ValueError(f'Failed timed process: {name}')
    elapsed = 0.0
    for part in field('Elapsed (wall clock) time (h:mm:ss or m:ss)').split(':'):
        elapsed = elapsed * 60 + float(part)
    with (path / 'sections.csv').open(newline='') as f:
        sections = {row['section']: float(row['seconds']) for row in csv.DictReader(f)}
    if len(sections) != 16 or any(not np.isfinite(t) or t < 0 for t in sections.values()):
        raise ValueError(f'Invalid section data: {name}')
    stat = pstats.Stats(str(path / 'rank_genes_groups.prof'))
    console = (path / 'console.txt').read_text()
    clusters = int(re.search(r'finished: found (\d+) clusters', console).group(1))
    return dict(name=name, path=path, meta=meta, sections=sections, stats=stat,
                wall=elapsed, user=float(field('User time (seconds)')),
                system=float(field('System time (seconds)')),
                cpu=field('Percent of CPU this job got'),
                rss=int(field('Maximum resident set size (kbytes)')), clusters=clusters)


def main():
    runs = [load_run(name) for name in RUNS]
    OUT.mkdir(exist_ok=True)
    sections = list(runs[0]['sections'])
    if any(list(r['sections']) != sections for r in runs):
        raise ValueError('Section order differs across runs')
    manifest = []
    for r in runs:
        for name in ['metadata.json', 'exit_code.txt', 'time.txt', 'console.txt',
                     'sections.csv', 'rank_genes_groups.prof', 'environment.txt',
                     'scanpy_pbmc.py', 'profile_sections.py', 'scanpy_pbmc.sbatch']:
            path = r['path'] / name
            manifest.append({'path': path.relative_to(ROOT).as_posix(),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    write_csv(OUT / 'source_manifest.csv', manifest)
    summary = [dict(run=r['name'], input_cells=r['meta']['input_cells'],
                    analyzed_cells=r['meta']['analyzed_cells'], clusters=r['clusters'],
                    host=r['meta']['hostname'], wall_seconds=r['wall'],
                    user_seconds=r['user'], system_seconds=r['system'],
                    cpu_percent=r['cpu'], max_rss_kib=r['rss'],
                    section_sum_seconds=sum(r['sections'].values())) for r in runs]
    write_csv(OUT / 'summary.csv', summary)
    # Define 20K as input cells; assume 10K's filtering fraction and gene composition.
    # Small setup sections stay at the 10K observation; data sections scale with N.
    fixed = {'imports', 'settings', 'arguments', 'report_placeholder', 'paga_placeholder'}
    factor = 20000 / runs[-1]['meta']['input_cells']
    predictions = []
    for section in sections:
        observed = runs[-1]['sections'][section]
        predictions.append(dict(section=section, observed_10k_seconds=observed,
                                assumed_model='constant' if section in fixed else 'linear in input cells',
                                estimate_20k_seconds=observed if section in fixed else observed * factor,
                                quadratic_sensitivity_seconds=observed if section in fixed else observed * factor**2))
    write_csv(OUT / 'estimate_20k.csv', predictions)
    predicted_total = sum(p['estimate_20k_seconds'] for p in predictions)
    sensitivity_total = sum(p['quadratic_sensitivity_seconds'] for p in predictions)
    prose = [
        'BMI 500: Scanpy PBMC profiling (partial homework report)',
        'Evidence and method',
        'All measurements come from successful OddJobs Slurm jobs 1289747, 1289760, '
        'and 1289774. No synthetic timing data are included. Each run requested one '
        'CPU, 16 GiB memory, and two hours. /usr/bin/time -v wrapped Python inside '
        'srun. SectionTimer used time.time() at all 16 starter section boundaries. '
        'Only the final rank_genes_groups call was instrumented with cProfile.',
        'Scanpy 1.10.2 and Python 3.12.13 were used. requirements-oddjobs.txt and '
        'per-run environment.txt record installed versions. AnnData 0.10.8, Zarr '
        '2.18.7, and setuptools 80.9.0 resolved observed import failures. Scanpy '
        'read caching was disabled; each run used a separate NUMBA_CACHE_DIR. OS '
        'filesystem caches and all library caches were not controlled.',
        'Observed process measurements',
    ]
    for r in runs:
        prose.append(f"{r['name']}: {r['meta']['input_cells']} input cells, "
                     f"{r['meta']['analyzed_cells']} analyzed cells, {r['clusters']} clusters; "
                     f"wall {r['wall']:.2f} s, user CPU {r['user']:.2f} s, system CPU "
                     f"{r['system']:.2f} s, CPU utilization {r['cpu']}, peak RSS "
                     f"{r['rss']} KiB ({r['rss']/1024:.1f} MiB). "
                     f"Host: {r['meta']['hostname']}.")
    prose += ['Bottlenecks and interpretation',
        'Settings is the largest measured 3K section (15.05 s); UMAP is the largest '
        '6K section (15.90 s); neighbors is the largest 10K section (33.04 s). '
        'The settings section includes print_header and figure setup; it was not '
        'profiled internally, so its specific cause cannot be established. '
        'Among biological analysis steps, UMAP dominates 3K and 6K. The 10K '
        'rank_genes_groups step takes 14.24 s and UMAP takes 14.37 s.',
        'UMAP is faster at 10K than at 6K, while neighbors jumps from 4.57 to '
        '33.04 s. These observations do not establish a smooth scaling law. '
        'Possible contributors include algorithm paths, JIT compilation, data '
        'structure, node performance and contention; these were not isolated.',
    ]
    for r in runs:
        ranks = [(key, value) for key, value in r['stats'].stats.items()
                 if key[2] == 'rank' and key[0].endswith('algorithms.py')]
        if ranks:
            self_time = sum(v[2] for _, v in ranks)
            prose.append(f"{r['meta']['dataset']} cProfile: pandas algorithms.rank self time "
                         f"is {self_time:.3f} s, {100*self_time/r['stats'].total_tt:.1f}% "
                         'of total profiled self time. This supports ranking as a major '
                         'cost within the Wilcoxon marker-gene calculation.')
    prose += [
        'The pipeline selects 2000 variable genes for dimensionality reduction, '
        'but adata.raw is captured before this selection and rank_genes_groups '
        'uses use_raw=True. Marker testing therefore includes the retained genes '
        'in raw, not only the 2000 selected genes. Group count also changes from '
        '4 to 7 to 16, so cell count alone cannot explain marker-test scaling.',
        '20K estimate: scenario, not a measured result',
        f'Define 20K as 20000 input cells. Use the actual 10K input size of 11769 '
        f'cells, giving a scale factor of {factor:.4f}. Hold imports, settings, '
        'argument handling and empty placeholders constant. Multiply all other '
        '10K section times by this factor. This assumes similar filtering fraction, '
        'gene count, sparsity, cluster structure, hardware and algorithm behavior.',
        f'The section-sum estimate is {predicted_total:.2f} s. It excludes recorder '
        'and process overhead and is not a prediction of exact /usr/bin/time wall '
        f'time. As an alternative assumption, quadratic scaling of data-dependent '
        f'sections gives {sensitivity_total:.2f} s. These are two sensitivity '
        'scenarios, not confidence bounds. estimate_20k.csv lists every section.',
        'Limits and submission status',
        'There is only one successful run per dataset, on two nodes. The 3K '
        'script used default CPU binding; 6K and 10K explicitly used --cpu-bind=cores '
        'after two failed launches. Thus this is an exploratory comparison, not '
        'a controlled benchmark. Repeats with matching node type and binding would '
        'be needed to quantify variability. Failed jobs 1289755 and 1289757 are '
        'excluded from all measurements.',
        'The total process time includes imports, profiling and output overhead. '
        'Section times omit timer printing and CSV writes. The final section '
        'includes cProfile setup and profile dumping. Cumulative cProfile times '
        'overlap across callers and callees and must not be summed. Self time '
        'excludes called functions. The profiler introduces overhead.',
        'The h5ad write stays in the starter location before marker testing, so '
        'that file does not contain the subsequent marker results. Peak RSS is '
        'process-wide; there are no per-section memory measurements. The sparse '
        'matrix is densified during scale, as noted in the console warnings.',
        'This report and notebook cover profiling only. They are not the final '
        'complete homework submission. The Python Quiz remains entirely the '
        "student's work. Class-partner manual review and a different assistant's "
        'AI review remain outstanding. No such reviews are generated here.',
    ]
    position = prose.index('Limits and submission status')
    prose[position:position] = ['20K per-section linear scenario (seconds)'] + [
        f"{p['section']}: {p['estimate_20k_seconds']:.6f} ({p['assumed_model']})."
        for p in predictions]
    (OUT / 'report.md').write_text('\n\n'.join(prose) + '\n', encoding='utf-8')
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    images = []
    with PdfPages(OUT / 'profiling_report.pdf') as pdf:
        lines = []
        for paragraph in prose:
            lines.extend(textwrap.wrap(paragraph, width=95))
            lines.append('')
        for i in range(0, len(lines), 49):
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.07, 0.95, '\n'.join(lines[i:i+49]), va='top', fontsize=10,
                     linespacing=1.45)
            pdf.savefig(fig)
            plt.close(fig)
        def save(fig, name):
            fig.savefig(OUT / f'{name}.png', dpi=170, bbox_inches='tight')
            pdf.savefig(fig, bbox_inches='tight')
            images.append(name)
            plt.close(fig)
        active = [s for s in sections if 'placeholder' not in s and s != 'arguments']
        fig, ax = plt.subplots(figsize=(11, 6))
        bottom = np.zeros(3)
        colors = plt.get_cmap('tab20')(np.linspace(0, 1, len(active)))
        for s, color in zip(active, colors):
            values = np.array([r['sections'][s] for r in runs])
            ax.bar(range(3), values, bottom=bottom, label=s, color=color)
            bottom += values
        ax.set_xticks(range(3), [f"{r['meta']['dataset']}\n{r['meta']['input_cells']:,} input cells" for r in runs])
        ax.set_ylabel('Section wall time (seconds)')
        ax.set_title('OddJobs measured section times (one run per dataset)')
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
        fig.tight_layout()
        save(fig, 'section_times')
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
        for ax, section in zip(axes, ['neighbors', 'umap', 'rank_genes_groups']):
            ax.plot([r['meta']['input_cells'] for r in runs],
                    [r['sections'][section] for r in runs], 'o-', label='Measured')
            prediction = next(p for p in predictions if p['section'] == section)
            ax.plot([11769, 20000], [runs[-1]['sections'][section], prediction['estimate_20k_seconds']],
                    '--', color='gray', label='Linear scenario')
            ax.scatter([20000], [prediction['estimate_20k_seconds']], marker='x', color='black')
            ax.set(title=section, xlabel='Input cells', ylabel='Seconds')
            ax.legend(fontsize=8)
        fig.tight_layout()
        save(fig, 'scaling_scenario')
        for r in runs:
            stats = r['stats']
            stream = io.StringIO()
            stats.stream = stream
            stats.sort_stats('cumulative').print_stats(40)
            (OUT / f"{r['meta']['dataset']}_cprofile.txt").write_text(stream.getvalue(), encoding='utf-8')
            rows = []
            for (file, line, function), (primitive, calls, self_time, cumulative, callers) in stats.stats.items():
                rows.append(dict(file=file, line=line, function=function, primitive_calls=primitive,
                                 total_calls=calls, self_seconds=self_time, cumulative_seconds=cumulative))
            write_csv(OUT / f"{r['meta']['dataset']}_functions.csv", sorted(rows, key=lambda x: -x['cumulative_seconds']))
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            for ax, key, title in zip(axes, ['self_seconds', 'cumulative_seconds'], ['Self time', 'Cumulative time (overlapping)']):
                top = sorted(rows, key=lambda x: x[key], reverse=True)[:10][::-1]
                labels = [f"{Path(x['file']).name}:{x['line']} {x['function']}" for x in top]
                ax.barh(range(len(top)), [x[key] for x in top], color='#397a9c')
                ax.set_yticks(range(len(top)), labels, fontsize=8)
                ax.set(xlabel='Seconds', title=title)
            fig.suptitle(f"{r['meta']['dataset']}: rank_genes_groups cProfile")
            fig.tight_layout()
            save(fig, f"{r['meta']['dataset']}_cprofile")
    # A separate profiling notebook, with existing measured figures embedded.
    # No quiz content or fabricated execution outputs are included.
    import base64
    cells = [{'cell_type': 'markdown', 'metadata': {}, 'source': '\n\n'.join(prose)}]
    for name in images:
        data = base64.b64encode((OUT / f'{name}.png').read_bytes()).decode('ascii')
        cells.append({'cell_type': 'markdown', 'metadata': {},
                      'source': f'![{name}](attachment:{name}.png)',
                      'attachments': {f'{name}.png': {'image/png': data}}})
    cells.append({'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
                  'source': '# Optional local regeneration from the repository root:\n'
                            'import subprocess, sys\nsubprocess.run([sys.executable, "analyze_profiles.py"], check=True)\n'})
    notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3',
                'language': 'python', 'name': 'python3'}}, 'nbformat': 4, 'nbformat_minor': 4}
    (ROOT / 'scanpy_profiling.ipynb').write_text(json.dumps(notebook, indent=1), encoding='utf-8')
    print('Validated 3 successful runs; generated report, 5 figures, tables and notebook.')
    print(f'20K section-sum scenario: {predicted_total:.2f} s; quadratic sensitivity: {sensitivity_total:.2f} s')


if __name__ == '__main__':
    main()
