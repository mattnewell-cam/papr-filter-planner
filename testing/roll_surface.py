"""Achievable log10PF over bundle shape, and where its maximum sits.

A cylindrical bundle has three geometric freedoms (r_i, r_o, H). Two of them are
parametrised here as face area A = 2*pi*rbar*H and radius ratio rho = r_o/r_i; the
third, wall thickness tau, is not free - it is set by whichever budget binds first,
tau = min(tau_pressure, tau_volume). That min() is what makes the achievable surface a
pair of faces meeting along a ridge, and what makes the cap contours kink at the ridge.

Usage
    python roll_surface.py out.png                  # surfaces + ridge, no size caps
    python roll_surface.py out.png --ro 15 --h 50   # + cap walls, allowed region, optimum

Needs plotly + kaleido. See ../THEORY.md section 7 for what the picture means.
"""
import argparse, json, math, os
import numpy as np
import plotly.graph_objects as go

ap = argparse.ArgumentParser()
ap.add_argument('out')
ap.add_argument('--ro', type=float, help='outer radius cap, cm')
ap.add_argument('--h', type=float, help='bundle length cap, cm')
ap.add_argument('--mat', default='grey fuzzy')
ap.add_argument('--q', type=float, default=180.0, help='L/min')
ap.add_argument('--dp', type=float, default=200.0, help='Pa')
ap.add_argument('--vol', type=float, default=20.0, help='litres of cloth')
ap.add_argument('--alpha', type=float, default=0.5, help='diffusion exponent')
args = ap.parse_args()
CAPPED = args.ro is not None and args.h is not None

m = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'coefficients.json')))[args.mat]
tl = m['t_layer']
a, c, k = m['D'] / tl, m['C'] / tl, m['k_layer'] / tl          # per cm of wall
al = args.alpha
Q, P, V = args.q * 1000 / 60, args.dp, args.vol * 1000
RO, HM = args.ro, args.h
AMIN, AMAX, ZB, ZT, RMAX = (1500., 6000., 2., 5.5, 4.) if CAPPED else (1000., 8000., 0., 5.5, 8.)
TAUC = 2 * math.pi

xOf = lambda r: 2 * (r - 1) / (r + 1)                                    # tau / rbar
Astar = lambda r: np.sqrt(V * k * Q * np.log(r) / (P * xOf(r)))          # ridge: both budgets tight
Alow = lambda r: RO * k * Q * np.log(r) / (P * (1 + xOf(r) / 2))         # r_o cap, pressure branch
Ahigh = lambda r: V * (1 + xOf(r) / 2) / (RO * xOf(r))                   # r_o cap, volume branch
AH = lambda r: np.sqrt(TAUC * V * HM / xOf(r))                           # H cap, volume branch
roR = lambda r: (1 + xOf(r) / 2) * np.sqrt(P * V / (xOf(r) * k * Q * np.log(r)))   # r_o on the ridge


def bis(f, lo, hi):
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def geom(A, r, tau):
    """log10PF, r_i, r_o and H for a wall of thickness tau at (A, rho)."""
    rb = tau / xOf(r)
    ri, ro = rb - tau / 2, rb + tau / 2
    z = a * (Q * rb / A) ** -al * (ro ** (1 + al) - ri ** (1 + al)) / (1 + al) + c * tau
    return z, ri, ro, A / (TAUC * rb)


zP = lambda A, r: geom(A, r, P * A * xOf(r) / (k * Q * np.log(r)))[0]     # pressure-limited face
zV = lambda A, r: geom(A, r, V / A)[0]                                    # volume-limited face


def band(rs, lo, hi, n, zf, lift=0.0):
    f = np.linspace(0, 1, n + 1)[None, :]
    A = np.asarray(lo)[:, None] + (np.asarray(hi) - np.asarray(lo))[:, None] * f
    R = np.repeat(np.asarray(rs)[:, None], n + 1, axis=1)
    return A, R, zf(A, R) + lift


rs = 1.02 + (RMAX - 1.02) * np.linspace(0, 1, 130) ** (1.4 if CAPPED else 1.5)
As = np.clip(Astar(rs), AMIN, AMAX)
surf = lambda g, c0, c1: go.Surface(x=g[0], y=g[1], z=g[2], colorscale=[[0, c0], [1, c1]],
                                    showscale=False, hoverinfo='skip')
data = [surf(band(rs, np.full_like(rs, AMIN), As, 70, zP), '#9dc6ef', '#185FA5'),
        surf(band(rs, As, np.full_like(rs, AMAX), 70, zV), '#f6c1a6', '#b8451c')]

if CAPPED:
    RC = bis(lambda r: roR(r) - RO, 1.05, 9.0)          # ridge meets the r_o cap
    RH = math.exp(TAUC * P * HM / (k * Q))              # ridge meets the H cap (closed form)
    RS = bis(lambda r: Alow(r) - AMIN, 1.001, 9.0)
    pocket = Ahigh(RH) < AH(RH)
    RM = bis(lambda r: Ahigh(r) - AH(r), 1.02, RH) if pocket else RH

    rp = np.linspace(RS, RH, 90)
    okP = band(rp, np.full_like(rp, AMIN), np.minimum(Alow(rp), Astar(rp)), 50, zP, .012)
    rv = np.linspace(1.02, RH, 90)
    lo_v, hi_v = np.maximum(Astar(rv), Ahigh(rv)), np.minimum(AMAX, AH(rv))
    keep = hi_v > lo_v + 1e-9

    if pocket:
        yel = ([(x, RH) for x in np.linspace(AMIN, Astar(RH), 40)]
               + [(AH(r), r) for r in np.linspace(RH, RM, 50)])
        pnk = ([(Ahigh(r), r) for r in np.linspace(RM, RC, 40)]
               + [(Alow(r), r) for r in np.linspace(RC, RS, 50)])
    else:
        yel = [(x, RH) for x in np.linspace(AMIN, Alow(RH), 40)]
        pnk = [(Alow(r), r) for r in np.linspace(RH, RS, 60)]
    for pts, col in ((yel, '#eda100'), (pnk, '#e87ba4')):
        W = np.asarray(pts)
        data.append(go.Surface(x=np.repeat(W[:, 0:1], 2, 1), y=np.repeat(W[:, 1:2], 2, 1),
                               z=np.tile([ZB, ZT], (len(W), 1)),
                               colorscale=[[0, col], [1, col]],
                               showscale=False, opacity=.34, hoverinfo='skip'))
    data.append(surf(okP, '#5dcaa5', '#0f6e56'))
    if keep.any():
        data.append(surf(band(rv[keep], lo_v[keep], hi_v[keep], 40, zV, .012), '#5dcaa5', '#0f6e56'))

    # The optimum sits at rho* = min(RC, RH): on the ridge when the r_o cap bites first,
    # otherwise pinched off it, onto the r_o boundary at the ratio where H runs out.
    bR = min(RC, RH)
    bA = min(Alow(bR), Astar(bR))
    tau = min(P * bA * xOf(bR) / (k * Q * math.log(bR)), V / bA)
    bz, ri, ro, H = geom(bA, bR, tau)
    data.append(go.Scatter3d(x=[bA], y=[bR], z=[bz + .03], mode='markers',
                             marker=dict(color='#6250d6', size=7), hoverinfo='skip'))
    print('optimum %.3f logs | A=%.0f cm2  r_o/r_i=%.3f  r_i=%.2f  r_o=%.2f  H=%.1f  tau=%.2f'
          % (bz, bA, bR, ri, ro, H, tau))
    print('  cloth used %.1f of %.1f L | %s'
          % (bA * tau / 1000, V / 1000, 'on the ridge' if RC <= RH else 'PINCHED off the ridge'))
    print('  ridge meets r_o cap at rho=%.4f, H cap at rho=%.4f' % (RC, RH))
    cam, dims = dict(x=-1.29, y=-1.51, z=1.00), (1250, 900)
else:
    rZ = zV(As, rs) + .02
    data += [go.Scatter3d(x=As, y=rs, z=rZ, mode='lines',
                          line=dict(color='#1baf7a', width=7), hoverinfo='skip'),
             go.Scatter3d(x=[As[0]], y=[rs[0]], z=[rZ[0]], mode='markers',
                          marker=dict(color='#1baf7a', size=9), hoverinfo='skip')]
    print('ridge peak %.3f logs at A=%.0f cm2 | falls to %.3f at r_o/r_i=%.0f'
          % (rZ[0] - .02, As[0], rZ[-1] - .02, rs[-1]))
    cam, dims = dict(x=1.62, y=-2.40, z=.60), (1300, 1030)

ink, gridc = '#52514e', '#e1e0d9'
ax = lambda t, rng: dict(title=dict(text=t, font=dict(size=14, color=ink)),
                         tickfont=dict(size=11, color=ink), range=rng,
                         gridcolor=gridc, zerolinecolor=gridc,
                         backgroundcolor='white', showbackground=True)
xa = ax('face area A (cm²)', [AMIN, AMAX])
if not CAPPED:
    xa['tickvals'] = list(range(2000, int(AMAX) + 1, 1000))
go.Figure(data=data, layout=dict(
    margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='white', showlegend=False,
    font=dict(family='Arial, Helvetica, sans-serif'),
    scene=dict(xaxis=xa, yaxis=ax('r<sub>o</sub> / r<sub>i</sub>', [1, RMAX]),
               zaxis=ax('log₁₀ PF', [ZB, ZT]), camera=dict(eye=cam)))
).write_image(args.out, width=dims[0], height=dims[1], scale=2)

from PIL import Image, ImageChops                                 # trim the white margin
im = Image.open(args.out).convert('RGB')
bb = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
if bb:
    p = 30
    im.crop((max(0, bb[0] - p), max(0, bb[1] - p),
             min(im.width, bb[2] + p), min(im.height, bb[3] + p))).save(args.out)
