"""Fit radial integrals to prototype PF/pressure with explicit geometry.

python fit_materials.py --output fitted_coefficients.json
Output is a new fit, never an automatic replacement of coefficients.json.
Requires numpy and scipy. See FITTING.md for assumptions and unresolved inputs.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent


def numeric(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def observations(rows, spec):
    out = []
    t = spec['t_layer']
    for series in spec['series']:
        if series.get('r_i') is None and series.get('stock_cm') is None:
            raise ValueError('test-roll core radius or cloth stock is not documented')
        for number in range(series['rows'][0], series['rows'][1]+1):
            row = rows[number-1]
            if not row[0].startswith(series['description_prefix']):
                raise ValueError(f'row {number} no longer matches its material; update the row map')
            ro = float(row[1])/(2*math.pi)  # stored circumference, despite old "Diam" label
            H = float(row[2])
            if series.get('r_i') is not None:
                ri = series['r_i']
            else:
                area = ro*ro-series['stock_cm']*t/math.pi
                if area <= 0:
                    raise ValueError(f'row {number}: cloth stock exceeds outer roll area')
                ri = math.sqrt(area)
            if not (0 < ri < ro and H > 0 and t > 0):
                raise ValueError(f'row {number}: invalid geometry')
            q, y = numeric(row[5]), numeric(row[6])
            if q is None or q <= 0 or y is None:
                raise ValueError(f'row {number}: missing flow or log10PF')
            # A pressure derived from an absent manometer observation is missing,
            # even when spreadsheet arithmetic has cached a zero.
            pressure = numeric(row[10]) if numeric(row[24]) is not None else None
            K = q*1000/60/(2*math.pi*H)
            out.append(dict(row=number, K=K, ri=ri, ro=ro, y=y, p=pressure,
                            midpoint_velocity=K/((ro+ri)/2)))
    return out


def prediction(theta, obs, t, impaction):
    D, C, alpha = theta[:3]
    K = np.array([o['K'] for o in obs])
    ri = np.array([o['ri'] for o in obs]); ro = np.array([o['ro'] for o in obs])
    pred = (D*K**-alpha*(ro**(1+alpha)-ri**(1+alpha))/(1+alpha)+C*(ro-ri))/t
    if impaction:
        B, beta = theta[3:]
        integ = np.log(ro/ri) if abs(beta-1)<1e-8 else (ro**(1-beta)-ri**(1-beta))/(1-beta)
        pred += B*K**beta*integ/t
    return pred


def fit(obs, t):
    y = np.array([o['y'] for o in obs])
    # Apply the endpoint rule within each geometry, comparing per-layer logs.
    groups = {}
    for o in obs:
        groups.setdefault((o['ri'],o['ro']), []).append(o)
    impaction = any(max(g,key=lambda o:o['midpoint_velocity'])['y'] > min(o['y'] for o in g)+1e-12
                    for g in groups.values())
    candidates = []
    for alpha in (.1,.35,2/3-1e-6):
        for beta in ((.3,.7,1-1e-6) if impaction else (None,)):
            x0 = [.05,.02,alpha] + ([.001,beta] if impaction else [])
            lower = [0,0,.001]+([0,.001] if impaction else [])
            upper = [np.inf,np.inf,2/3]+([np.inf,1] if impaction else [])
            result = least_squares(lambda x:prediction(x,obs,t,impaction)-y,
                                   x0,bounds=(lower,upper),max_nfev=10000,
                                   ftol=1e-12,xtol=1e-12,gtol=1e-12)
            if result.success:
                candidates.append(result)
    if not candidates:
        raise ValueError('fit did not converge')
    best = min(candidates,key=lambda x:np.sum(x.fun*x.fun))
    D,C,alpha=best.x[:3]
    pressure_obs=[o for o in obs if o['p'] is not None]
    if not pressure_obs:
        raise ValueError('no measured pressure available')
    basis=np.array([o['K']*math.log(o['ro']/o['ri'])/t for o in pressure_obs])
    pressure=np.array([o['p'] for o in pressure_obs])
    k_layer=float(basis@pressure/(basis@basis))
    if k_layer <= 0:
        raise ValueError('nonpositive resistance fit')
    sse=float(best.fun@best.fun);sst=float(np.sum((y-y.mean())**2))
    output=dict(D=float(D),C=float(C),alpha=float(alpha),k_layer=k_layer,t_layer=t,
                log_rmse=math.sqrt(sse/len(obs)),r2=1-sse/sst if sst else None,
                pressure_rmse=float(np.sqrt(np.mean((k_layer*basis-pressure)**2))),
                rows=[o['row'] for o in obs],impaction_selected=impaction,
                midpoint_v_lo=min(o['midpoint_velocity'] for o in obs),
                midpoint_v_hi=max(o['midpoint_velocity'] for o in obs),
                v_lo=min(o['K']/o['ro'] for o in obs),v_hi=max(o['K']/o['ri'] for o in obs))
    if impaction:
        output.update(B=float(best.x[3]),beta=float(best.x[4]))
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=HERE/'prototype_pf_q.csv')
    parser.add_argument('--manifest',type=Path,default=HERE/'fit_series.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve()==(HERE/'coefficients.json').resolve():
        parser.error('write a separate candidate file; do not overwrite the published coefficients')
    rows=list(csv.reader(args.csv.open(encoding='utf-8-sig',newline='')))
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    result={'_provenance':{'input_sha256':hashlib.sha256(args.csv.read_bytes()).hexdigest(),
             'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
             'method':'unweighted whole-bundle log10PF residuals; radial integrals; nonnegative D/C/B; alpha<=2/3, beta<=1; pressure OLS through zero'},
             '_unresolved':{}}
    published=json.loads((HERE/'coefficients.json').read_text(encoding='utf-8'))
    for name,spec in manifest['materials'].items():
        try:
            result[name]=fit(observations(rows,spec),spec['t_layer'])
            result[name]['geometry_provenance']=spec['provenance']
            print(f"{name}: k_layer={result[name]['k_layer']:.5f} (published {published[name]['k_layer']:.5f}), log RMSE={result[name]['log_rmse']:.4f}")
        except ValueError as error:
            result['_unresolved'][name]=str(error)
            print(f'{name}: UNRESOLVED: {error}')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f"Wrote {args.output}; {len(result['_unresolved'])} unresolved materials. Published coefficients unchanged.")


if __name__=='__main__':
    main()
