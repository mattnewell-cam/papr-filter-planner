"""Radial-flow model for a rolled fabric filter bundle.

Geometry: a cylinder of axial length H, hollow core of radius r_i, wrapped outward
with one or more fabric strips. Air flows radially, so the face velocity is not
constant: v(r) = Q / (2*pi*r*H). Both pressure drop and log PF must be integrated
over radius.

For material j occupying [r0, r1] at n_j layers per cm of radial depth:

    dp    = k_layer_j * n_j * Q/(2*pi*H) * ln(r1/r0)
    logPF = n_j * integral_{r0}^{r1} f_j(v(r)) dr

where k_layer_j is Pa per cm/s per layer and f_j(v) is per-layer log10 PF from the
velocity-scaling fits in RESULTS.md. dp is exactly linear in Q, so inverting
dp -> Q is one division; logPF is not, and is integrated numerically.

Per-layer coefficients live in `coefficients.json` and are loaded at import; nothing
is hardcoded here. `t_layer` is the fabric's own per-layer thickness and `plies` the
fold count, so tau = t_layer*plies is the radial depth per wrap; re-fold a material
with `.refold(n)`. Layer count follows from geometry alone:
N = plies*L/(pi*(r_o+r_i)), independent of t_layer. The model assumes layer-count
independence — every layer contributes f(v) regardless of depth — so QF is
invariant to N.

Radii chain outward from the core by material cross-section:
    pi*(r1^2 - r0^2) = L * tau        so   r1 = sqrt(r0^2 + L*tau/pi)
with L the wrapped strip length and tau the strip's thickness per wrap.

Units throughout: cm, cm/s, cm^3/s, Pa. QF is reported in kPa^-1 per the project
convention. See RESULTS.md for the fits and their measured velocity ranges.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, replace
from typing import Sequence

LN10 = math.log(10.0)


@dataclass
class Material:
    """One fabric, with per-layer coefficients loaded from coefficients.json.

        log10PF per layer = D*v**-alpha + C + B*v**beta
        dp      per layer = k_layer*v

    The three terms are diffusion, interception and impaction. B/beta are absent for
    materials whose highest-velocity point is also their lowest PF (see RESULTS.md for
    the selection rule). alpha is capped at 2/3, beta at 1.0.
    """

    name: str
    k_layer: float                # Pa per (cm/s) per layer
    t_layer: float                # cm per single layer
    plies: int                    # layers per wrap of the folded strip
    v_lo: float                   # measured velocity range, cm/s
    v_hi: float
    D: float
    C: float
    alpha: float
    B: float = 0.0
    beta: float | None = None

    @property
    def tau(self) -> float:
        """cm of radial depth per wrap."""
        return self.t_layer * self.plies

    def refold(self, plies: int) -> "Material":
        """Same fabric, folded a different number of times."""
        return replace(self, plies=plies)

    def logpf_layer(self, v: float) -> float:
        y = self.D * v ** -self.alpha + self.C
        if self.beta is not None:
            y += self.B * v ** self.beta
        return y

    # per centimetre of wall - the geometry-independent comparison
    def logpf_cm(self, v: float) -> float:
        return self.logpf_layer(v) / self.t_layer

    def dp_cm(self, v: float) -> float:
        return self.k_layer * v / self.t_layer

    def qf(self, v: float) -> float:
        """Quality factor, kPa^-1."""
        return LN10 * self.logpf_layer(v) / (self.k_layer * v / 1000.0)


def _load(path: str = "coefficients.json") -> dict[str, Material]:
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    with open(here, encoding="utf-8") as fh:
        raw = json.load(fh)
    out = {}
    for name, m in raw.items():
        if name.startswith("_"):
            continue
        out[name] = Material(
            name=name, k_layer=m["k_layer"], t_layer=m["t_layer"], plies=2,
            v_lo=m.get("v_lo", 0.0), v_hi=m.get("v_hi", 99.0),
            D=m.get("D", 0.0), C=m.get("C", 0.0), alpha=m["alpha"],
            B=m.get("B", 0.0), beta=m.get("beta"),
        )
    return out


MATERIALS = _load()

GREY_HOLEY = MATERIALS["grey holey"]
DUVET      = MATERIALS["duvet"]
GREY_FUZZY = MATERIALS["grey fuzzy"]
BLUE_HOLEY = MATERIALS["blue holey"]
TOWEL      = MATERIALS["towel"]
PINK       = MATERIALS["pink"]
SOFT_LINEN = MATERIALS["soft linen"]


@dataclass
class Section:
    """One radial band. Several materials listed together are plied — wrapped as one
    strip, so each wrap lays down every material's plies at once and the band ends
    when the shortest strip runs out."""
    entries: Sequence[tuple[Material, float]]   # (material, available length cm)

    r0: float = field(default=0.0, init=False)
    r1: float = field(default=0.0, init=False)

    @property
    def tau(self) -> float:
        return sum(m.tau for m, _ in self.entries)

    @property
    def length(self) -> float:
        return min(L for _, L in self.entries)

    def layers_per_cm(self, m: Material) -> float:
        return m.plies / self.tau


@dataclass
class Bundle:
    sections: list[Section]
    r_i: float          # core radius, cm
    H: float            # axial length, cm

    def __post_init__(self) -> None:
        r = self.r_i
        for s in self.sections:
            s.r0 = r
            r = math.sqrt(r * r + s.length * s.tau / math.pi)
            s.r1 = r
        self.r_o = r

    # --- flow ---------------------------------------------------------------
    def velocity(self, r: float, Q: float) -> float:
        return Q / (2.0 * math.pi * r * self.H)

    def dp(self, Q: float) -> float:
        """Pa. Exactly linear in Q."""
        c = Q / (2.0 * math.pi * self.H)
        return sum(
            m.k_layer * s.layers_per_cm(m) * c * math.log(s.r1 / s.r0)
            for s in self.sections
            for m, _ in s.entries
        )

    def log_pf(self, Q: float, n: int = 4000) -> float:
        """Total log10 PF, Simpson quadrature in ln(r)."""
        total = 0.0
        for s in self.sections:
            lo, hi = math.log(s.r0), math.log(s.r1)
            h = (hi - lo) / n
            for m, _ in s.entries:
                npl = s.layers_per_cm(m)

                def g(u: float, m=m) -> float:      # dr = r du
                    r = math.exp(u)
                    return m.logpf_layer(self.velocity(r, Q)) * r

                acc = g(lo) + g(hi)
                for i in range(1, n):
                    acc += g(lo + i * h) * (4 if i % 2 else 2)
                total += npl * acc * h / 3.0
        return total

    def solve_Q(self, dp_target: float) -> float:
        return dp_target * 1.0 / self.dp(1.0)

    # --- reporting ----------------------------------------------------------
    def layers(self, m: Material) -> float:
        return sum(s.layers_per_cm(m) * (s.r1 - s.r0)
                   for s in self.sections for mm, _ in s.entries if mm is m)

    def report(self, Q: float) -> dict:
        dp = self.dp(Q)
        lpf = self.log_pf(Q)
        return dict(
            Q_cm3s=Q, Q_lmin=Q * 60 / 1000.0,
            r_i=self.r_i, r_o=self.r_o, H=self.H,
            v_inner=self.velocity(self.r_i, Q), v_outer=self.velocity(self.r_o, Q),
            dp_Pa=dp, log10PF=lpf, PF=10.0 ** lpf,
            QF_kPa=LN10 * lpf / (dp / 1000.0),
        )

    def extrapolation(self, Q: float) -> list[str]:
        out = []
        for s in self.sections:
            v1 = self.velocity(s.r0, Q)   # fastest, innermost
            v0 = self.velocity(s.r1, Q)
            for m, _ in s.entries:
                if v1 > m.v_hi or v0 < m.v_lo:
                    out.append(
                        f"{m.name}: sees {v0:.2f}-{v1:.2f} cm/s, "
                        f"fitted over {m.v_lo:.2f}-{m.v_hi:.2f}"
                    )
        return out


def fmt(r: dict) -> str:
    return (f"  r {r['r_i']:.2f}->{r['r_o']:.2f} cm   v {r['v_outer']:.2f}-{r['v_inner']:.2f} cm/s\n"
            f"  Q {r['Q_lmin']:.0f} L/min   dp {r['dp_Pa']:.1f} Pa   "
            f"log10PF {r['log10PF']:.3f}   PF {r['PF']:.1f}   QF {r['QF_kPa']:.1f} kPa^-1")


if __name__ == "__main__":
    print(f'{"material":<12}{"t_lyr":>7}{"Pa/cm":>8}'
          f'{"logs/cm @0.64":>15}{"@1.2":>7}{"@2.4":>7}'
          f'{"QF @0.64":>10}{"@1.2":>8}{"@2.4":>8}')
    for m in sorted(MATERIALS.values(), key=lambda x: -x.qf(1.2)):
        print(f"{m.name:<12}{m.t_layer:7.3f}{m.k_layer / m.t_layer:8.1f}"
              f"{m.logpf_cm(0.64):15.3f}{m.logpf_cm(1.2):7.3f}{m.logpf_cm(2.4):7.3f}"
              f"{m.qf(0.64):10.1f}{m.qf(1.2):8.1f}{m.qf(2.4):8.1f}")

    # worked bundle: grey holey inside, grey fuzzy outside, 125 cm of each
    L, H, r_i, Q = 125.0, 42.0, 2.5, 180 * 1000 / 60
    b = Bundle([Section([(GREY_HOLEY.refold(3), L)]),
                Section([(GREY_FUZZY.refold(3), L)])], r_i=r_i, H=H)
    print()
    print(f"125 cm each, folded 3x, ID {20 * r_i:.0f} mm, H {H:.0f} cm, "
          f"Q {Q * 60 / 1000:.0f} L/min")
    print(f"  r {r_i:.2f} -> {b.r_o:.2f} cm, dp {b.dp(Q):.0f} Pa, "
          f"log10PF {b.log_pf(Q):.3f}, PF {10 ** b.log_pf(Q):.0f}")
    for w in b.extrapolation(Q):
        print(f"  ! {w}")
