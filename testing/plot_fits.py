"""Plot current measurements against published fits: python plot_fits.py.

Requires numpy, scipy and matplotlib. Writes PNG/SVG files to plots/ by default.
Does not refit or modify measurements or coefficients.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter
import numpy as np

from fit_materials import observations, prediction

HERE = Path(__file__).resolve().parent


def logs(material, obs, diffusion_only=False, without_impaction=False):
    theta = [material['D'], 0 if diffusion_only else material['C'], material['alpha']]
    impaction = 'beta' in material and not (without_impaction or diffusion_only)
    if impaction:
        theta += [material['B'], material['beta']]
    return prediction(theta, obs, material['t_layer'], impaction)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'plots')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with (HERE / 'prototype_pf_q.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    specs = json.loads((HERE / 'fit_series.json').read_text())['materials']
    coefficients = json.loads((HERE / 'coefficients.json').read_text())
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.fonttype': 'none'})

    def save(fig, name):
        for ax in fig.axes:
            ax.grid(alpha=.2)
            if ax.get_xscale() == 'log':
                ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
                ax.xaxis.set_major_formatter(ScalarFormatter())
                ax.xaxis.set_minor_formatter(NullFormatter())
        fig.tight_layout()
        for extension in ('png', 'svg'):
            fig.savefig(args.out / f'{name}.{extension}', dpi=160)
        plt.close(fig)

    for name, spec in specs.items():
        material = coefficients[name]
        if not math.isclose(spec['t_layer'], material['t_layer'], rel_tol=1e-6):
            raise ValueError(f'{name}: manifest and coefficient thickness differ')
        obs = observations(rows, spec)
        fig, (pf, pressure) = plt.subplots(1, 2, figsize=(11, 4.3))
        fig.suptitle(f'{name.capitalize()}: measurements and published model')
        groups = {}
        for o in obs:
            # Keep separate curves if any recorded build geometry differs.
            groups.setdefault((o['ri'], o['ro'], float(rows[o['row']-1][2])), []).append(o)
        for (ri, ro, height), group in groups.items():
            q = np.array([float(rows[o['row']-1][5]) for o in group])
            flow = np.geomspace(min(q), max(q), 180)
            smooth = [dict(K=f*1000/60/(2*math.pi*height), ri=ri, ro=ro) for f in flow]
            pf.scatter(q, [o['y'] for o in group], color='black', label='Measured')
            pf.plot(flow, logs(material, smooth), label='Published model')
            if 'beta' in material:
                pf.plot(flow, logs(material, smooth, without_impaction=True), '--',
                        label='Same coefficients, impaction omitted')
            measured_p = [(f, o['p']) for f, o in zip(q, group) if o['p'] is not None]
            if measured_p:
                pressure.scatter(*zip(*measured_p), color='black', label='Measured')
            model_p = material['k_layer']/material['t_layer'] * np.array(
                [o['K'] for o in smooth]) * math.log(ro/ri)
            pressure.plot(flow, model_p, label='Published model')
        pf.set(xscale='log', xlabel='Airflow Q (L/min)', ylabel='log₁₀ PF at 0.3 µm')
        pressure.set(xlabel='Airflow Q (L/min)', ylabel='Centre pressure (Pa)')
        for ax in (pf, pressure):
            handles, labels = ax.get_legend_handles_labels()
            unique = dict(zip(labels, handles))
            ax.legend(unique.values(), unique.keys(), fontsize=8)
        save(fig, name.replace(' ', '_') + '_fit')

    # Grey+pink construction documented in MODEL_CHECKS.md; row data are read fresh.
    grey, pink = coefficients['grey fuzzy'], coefficients['pink']
    selected = rows[16:23]
    for row in selected:
        if not row[0].startswith('Grey fuzzy (2) then pink (3)'):
            raise ValueError('Grey+pink rows moved; update the row selection')
        if float(row[1]) != 60.5 or float(row[2]) != 43:
            raise ValueError('Grey+pink geometry changed; review wrapped lengths')
    ro = 60.5/(2*math.pi)
    ri = math.sqrt(ro**2-(2*125*grey['t_layer']+3*125*pink['t_layer'])/math.pi)
    boundary = math.sqrt(ri**2+2*125*grey['t_layer']/math.pi)
    q = np.array([float(r[5]) for r in selected])
    measured = np.array([float(r[7]) for r in selected])

    def combined(flow):
        total = np.zeros(len(flow))
        for material, inner, outer in ((grey, ri, boundary), (pink, boundary, ro)):
            obs = [dict(K=f*1000/60/(2*math.pi*43), ri=inner, ro=outer) for f in flow]
            total += logs(material, obs)
        return 10**total

    flow = np.geomspace(min(q), max(q), 180)
    fig, (pf, residual) = plt.subplots(1, 2, figsize=(11, 4.3))
    fig.suptitle('Grey fuzzy + pink: single-material prediction versus combined build')
    pf.scatter(q, measured, color='black', label='Measured')
    pf.plot(flow, combined(flow), label='Published model')
    pf.set(xscale='log', yscale='log', xlabel='Airflow Q (L/min)', ylabel='PF at 0.3 µm')
    pf.legend()
    residual.scatter(q, combined(q)/measured, color='black')
    residual.axhline(1, color='grey', linestyle='--')
    residual.set(xscale='log', xlabel='Airflow Q (L/min)', ylabel='Predicted PF / measured PF')
    save(fig, 'grey_pink_comparison')

    # Record exact inputs so later exports can be distinguished without altering sources.
    hashes = {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
              for name in ('prototype_pf_q.csv', 'coefficients.json', 'fit_series.json', 'plot_fits.py')}
    (args.out/'inputs.json').write_text(json.dumps(hashes, indent=2)+'\n')
    print(f'Wrote {len(specs)+1} plots as PNG and SVG to {args.out.resolve()}')
    print('Grey+pink predicted/measured:', np.round(combined(q)/measured, 3))


if __name__ == '__main__':
    main()
