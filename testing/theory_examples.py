"""Recalculate the worked examples from coefficients.json; prints Markdown tables.

Uses the current grey-fuzzy fit. Sections 2/4/5 use 125 x 90 cm of cloth.
Section 7 uses 20 L and its explicitly illustrative alpha=0.5 override.
No fit parameters or project files are changed.
"""
import hashlib
import math
from pathlib import Path
from roll_model import GREY_FUZZY as M, PINK, Bundle, Section


def uniform(volume, pressure, flow=3000, m=M):
    n = math.sqrt(volume * pressure / (m.t_layer * m.k_layer * flow))
    area = volume / (m.t_layer * n)
    v = flow / area
    logs = n * m.logpf_layer(v)
    return n, v, logs, 10 ** logs, 1000 * math.log(10) * logs / pressure


def bisect(fn, lo, hi):
    assert fn(lo) * fn(hi) <= 0
    for _ in range(100):
        mid = (lo + hi) / 2
        if fn(lo) * fn(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def fold_rows():
    rows = []
    for f in (1, 2, 4, 8):
        h = 90 / f
        tau = M.t_layer * f
        c = 3000 / (2 * math.pi * h)
        ratio = math.exp(202 * M.t_layer / (M.k_layer * c))
        ri = math.sqrt(125 * tau / (math.pi * (ratio * ratio - 1)))
        b = Bundle([Section([(M.refold(f), 125)])], ri, h)
        r = b.report(3000)
        rows.append([f, ri * 20, b.r_o / ri, (b.r_o-ri)/M.t_layer,
                     r['v_outer'], r['v_inner'], r['PF'], r['QF_kPa'], r['log10PF']])
    return rows


def capped(radius, length):
    # Section 7: per-cm coefficients, alpha explicitly set to 0.5.
    pressure, q, volume, alpha = 200, 3000, 20000, .5
    k, a, c = M.k_layer/M.t_layer, M.D/M.t_layer, M.C/M.t_layer
    rho_h = math.exp(2*math.pi*pressure*length/(k*q))
    def ridge_ro(rho):
        x = 2*(rho-1)/(rho+1)
        return (1+x/2)*math.sqrt(pressure*volume/(x*k*q*math.log(rho)))
    rho_c = bisect(lambda rho: ridge_ro(rho)-radius, 1+1e-8, 1e5)
    rho = min(rho_c, rho_h)
    ro, ri = radius, radius/rho
    h = k*q*math.log(rho)/(2*math.pi*pressure)
    K = q/(2*math.pi*h)
    logs = a*K**-alpha*(ro**(1+alpha)-ri**(1+alpha))/(1+alpha)+c*(ro-ri)
    return logs, math.pi*(ro*ro-ri*ri)*h/1000, h


def main():
    digest = hashlib.sha256(Path(__file__).with_name('coefficients.json').read_bytes()).hexdigest()
    print('coefficients.json SHA256:', digest)
    print('folds | ID mm | ro/ri | layers | v out | v in | PF | QF | logs')
    for row in fold_rows():
        print(' | '.join(f'{x:.5f}' for x in row))
    volume = 125*90*M.t_layer
    print('uniform:', uniform(volume,202))
    print('material multiplier | layers | v | logs | PF | QF')
    for mult in (.5,1,2,4,8):
        print(mult, *uniform(volume*mult,202))
    print('pressure | layers | v | logs | PF | QF')
    for pressure in (50,100,202,400,800,1600):
        print(pressure, *uniform(volume,pressure))
    print('equal-volume grey + pink:')
    area = math.sqrt(3000*volume*(M.k_layer/M.t_layer+PINK.k_layer/PINK.t_layer)/202)
    v = 3000/area
    logs = volume/area*(M.logpf_cm(v)+PINK.logpf_cm(v))
    print('v, logs, PF, QF:',v,logs,10**logs,1000*math.log(10)*logs/202)
    print('Section 7: radius, length, logs, cloth litres, actual H')
    for ro,h in ((15,50),(15,40),(12,50),(12,40)):
        print(ro,h,*capped(ro,h))


if __name__ == '__main__':
    main()
