"""Read-only checks of saved prototype pressure and grey+pink predictions.

Run: python check_pressure_and_mixing.py (requires numpy and scipy).
Fits pressure residuals in Pa with equal weight per observation, separately by
recorded geometry. No measurement, geometry or published coefficient is changed.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from roll_model import Bundle, Section, GREY_FUZZY, PINK

HERE = Path(__file__).resolve().parent
source = HERE / 'prototype_pf_q.csv'
rows = list(csv.reader(source.open(encoding='utf-8-sig', newline='')))
specs = json.loads((HERE / 'fit_series.json').read_text())['materials']
print('CSV SHA256:', hashlib.sha256(source.read_bytes()).hexdigest())
print('Coefficients SHA256:', hashlib.sha256((HERE / 'coefficients.json').read_bytes()).hexdigest())


def fit(q, p, kind):
    if kind == 'linear':
        theta = np.array([q @ p / (q @ q)])
        predict = lambda x: theta[0] * x
    elif kind == 'offset':
        theta = np.linalg.lstsq(np.column_stack([q, np.ones(len(q))]), p, rcond=None)[0]
        predict = lambda x: theta[0] * x + theta[1]
    else:
        result = least_squares(lambda t: t[0]*(q/100)**t[1]-p,
                               [np.median(p), 1.0], bounds=([0, .1], [np.inf, 3]))
        theta = result.x
        predict = lambda x: theta[0] * (x/100)**theta[1]
    return theta, predict


print('\nPressure: material | rows | Q range | model parameters | RMSE Pa | leave-one-out RMSE Pa')
for name, spec in specs.items():
    groups = {}
    for series in spec['series']:
        for number in range(series['rows'][0], series['rows'][1]+1):
            row = rows[number-1]
            assert row[0].startswith(series['description_prefix'])
            try:
                float(row[24])  # require a real manometer observation
                q, p = float(row[5]), float(row[10])
            except ValueError:
                continue
            groups.setdefault((row[1], row[2]), []).append((number, q, p))
    for geometry, data in groups.items():
        q = np.array([r[1] for r in data]); p = np.array([r[2] for r in data])
        assert len(q) >= 4 and np.all(q > 0)
        for kind in ('linear', 'offset', 'power'):
            theta, predict = fit(q, p, kind)
            errors = []
            for i in range(len(q)):
                keep = np.arange(len(q)) != i
                _, heldout = fit(q[keep], p[keep], kind)
                errors.append(float(heldout(q[i])-p[i]))
            print(name, [r[0] for r in data], f'{min(q):.1f}-{max(q):.1f}', kind,
                  np.round(theta, 4), f'{np.sqrt(np.mean((predict(q)-p)**2)):.2f}',
                  f'{np.sqrt(np.mean(np.array(errors)**2)):.2f}')

print('\nGrey+pink: row | Q L/min | measured PF | predicted PF | predicted/measured')
# Recorded outer circumference 60.5 cm and H=43 cm; grey 2 ply, pink 3 ply.
# Wrapped length 125 cm each. Infer core from total cloth cross-section.
ro = 60.5/(2*math.pi)
ri = math.sqrt(ro**2-(2*125*GREY_FUZZY.t_layer+3*125*PINK.t_layer)/math.pi)
bundle = Bundle([Section([(GREY_FUZZY.refold(2), 125)]),
                 Section([(PINK.refold(3), 125)])], r_i=ri, H=43)
print(f'Geometry: core radius {ri:.6f} cm, outer radius {bundle.r_o:.6f} cm, H=43 cm')
for number in range(17, 24):
    row = rows[number-1]
    assert row[0].startswith('Grey fuzzy (2) then pink (3)')
    assert float(row[1]) == 60.5 and float(row[2]) == 43
    q, measured = float(row[5]), float(row[7])
    predicted = 10**bundle.log_pf(q*1000/60)
    print(number, f'{q:.2f}', f'{measured:.2f}', f'{predicted:.2f}', f'{predicted/measured:.3f}')
