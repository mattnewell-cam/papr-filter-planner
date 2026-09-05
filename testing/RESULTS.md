# Household material filtration — measured results

Source: `filter_testing.xlsx` ([DIY PAPR Testing](https://docs.google.com/spreadsheets/d/1vNnPBNcy6AXGmybD3XqS8CLbzuCFn33SeNJbljD8o0Y/edit?gid=1848070649#gid=1848070649)), refetched 2026-09-05,
plus `prototype_pf_q.csv` (formulas evaluated; missing pressure shown as dashes).
The older standalone CSVs were removed; their source tabs remain in the XLSX. Published coefficients predate this refresh and live in `coefficients.json`;
`roll_model.py` loads them and computes bundles. `../THEORY.md` works out what the fits
imply for how to build one.

Counts are count-based, at 0.3 µm. QF is in kPa⁻¹ throughout.

The 0.3 µm channel is the project's working worst-case proxy and has higher counts
for less noisy measurements. This count-based endpoint differs from the wider
project's RFP endpoint of inhaled PM10 mass reduction.

For an auditable fitting procedure and its remaining geometry gaps, see `FITTING.md`.

## Where the numbers come from

Ground truth is the **`Prototype PF & Q` tab**: single-material rolled bundles swept
across fan voltage, giving PF, Q and centre pressure at 4–6 flows each. The flat-sheet
bench rig on `V-PF relationship` is superseded (see the last section).

Fits are on log₁₀PF per layer against face velocity, with velocity varying radially
across the wall and integrated properly rather than evaluated at a mean.

## The model

    log10PF per layer = D*v^-alpha + C + B*v^beta        dp per layer = k_layer*v

Three capture mechanisms: **diffusion** (falls with velocity), **interception**
(velocity-independent), **impaction** (rises with velocity). Comparisons between
materials are best made per centimetre of wall — divide by `t_layer` — since that is
independent of how the fabric is folded: a(v) is logs per cm and k = k_layer/t_layer is
Pa per (cm/s) per cm, the symbols `../THEORY.md` uses throughout.

`coefficients.json` stores the per-layer fit under these same names: `D`, `C`, `B`, `alpha`,
`beta`, `k_layer`, `t_layer`.

## Materials

| material | t_layer (cm) | k (Pa/(cm/s)/cm) | logs/cm @0.64 | @1.2 | @2.4 | QF @0.64 | @1.2 | @2.4 |
|---|---|---|---|---|---|---|---|---|
| grey holey | 0.2015 | 4.4 | 0.231 | 0.210 | 0.188 | 188.0 | 90.8 | 40.7 |
| duvet | 1.9516 | 1.6 | 0.082 | 0.062 | 0.052 | 186.6 | 74.9 | 31.7 |
| grey fuzzy | 0.2830 | 23.1 | 0.760 | 0.634 | 0.533 | 118.2 | 52.6 | 22.1 |
| blue holey | 0.2903 | 9.8 | 0.282 | 0.240 | 0.211 | 103.5 | 46.9 | 20.6 |
| towel | 0.2700 | 13.3 | 0.375 | 0.294 | 0.251 | 101.4 | 42.5 | 18.1 |
| pink | 0.4688 | 14.9 | 0.283 | 0.255 | 0.228 | 68.2 | 32.7 | 14.7 |
| soft linen | 0.0514 | 122.4 | 1.013 | 0.938 | 0.884 | 29.8 | 14.7 | 6.9 |

### Products

| material | product |
|---|---|
| grey holey | [IKEA SANDBRODD throw, anthracite](https://www.ikea.com/gb/en/p/sandbrodd-throw-anthracite-00562038/) |
| grey fuzzy | [amazon.co.uk B073HC2G7Q](https://www.amazon.co.uk/dp/B073HC2G7Q) |
| blue holey | [amazon.co.uk B01C8XRV44](https://www.amazon.co.uk/dp/B01C8XRV44) |
| pink | [amazon.co.uk B082TPFNH7](https://www.amazon.co.uk/dp/B082TPFNH7) |
| soft linen | [ASDA George Home soft-touch reversible duvet set, king](https://www.asda.com/groceries/product/duvet-cover-sets/george-home-grey-striped-soft-touch-reversible-duvet-set-king/7727810) |
| blue fuzzy | [IKEA KLIPPOXEL throw, grey/turquoise](https://www.ikea.com/gb/en/p/klippoxel-throw-grey-turquoise-00584629/) — **not yet tested** |

Duvet (**13.5 tog, synthetic polyester fill**) and towel are household items with no
product link.

0.64–2.4 cm/s is the range a real bundle spans: an 80 mm core out to a 300 mm outer
diameter at 180 L/min over 50 cm gives 0.64 at the skin and 2.39 at the core. QF at a
single velocity ranks materials correctly — the integrated figure over that whole
annulus is ~13% below QF@1 for every material, a near-constant offset.

Per-layer coefficients, geometry and provenance are in `coefficients.json`. Notes:

- **brown**, named in the combined-material sheet runs, is assumed equivalent to
  **pink** based on visual inspection; it was not tested separately.
- **pink** has two batches that differ by up to 0.44 logs; see the aerosol section. The
  fit is batch 2, the incense series, matching every other material.
  Its dimensions are **125 × 190 cm** (owner correction, 2026-09-05; 150 cm was a typo).
  In the grey-fuzzy + pink test, pink's wrapped length is confirmed as **125 cm**;
  the 190 cm side is folded into three plies.
- **duvet** is 13.5 tog with a **synthetic polyester fill**. Both matter: tog is the spec
  that plausibly transfers to other duvets, since t_layer (1.95 cm) and loft follow from
  it — but **down and feather duvets should not be assumed to behave the same way**. The
  fibre geometry is entirely different, and nothing here has been measured on one.
  The published fit used rows 89–94 in the September 4 export. These are now
  rows 56–61; all six now record effective length 42 cm after Matt corrected
  C57 in the live sheet on 2026-09-05 and the saved export was refreshed.
  Published coefficients have not been refitted. Older partial-length runs are excluded.

## Choosing the functional form

**Diffusion exponent α is free but capped at 2/3.** Fixing 2/3 everywhere fits some
series well and others worse than a plain power law; freeing it always wins but the
fitted value scatters 0.16–0.67 with no material pattern, and a shared-α fit sits on a
very flat SSE profile. 2/3 is the physical ceiling for diffusive capture, so α floats
below it. The production catalogue has seven materials; four exponents are at or close to the cap.

**Impaction exponent β is capped at 1.0.** Single-fibre impaction efficiency scales with
Stokes number, which is linear in v; saturation at high St only pushes the effective
exponent below 1. Uncapped, β runs to 3.5–6 and produces a hockey stick fitted to the
single highest-velocity point, with B ≈ 10⁻⁵. Capped, B becomes a real contributor.

**When to add the impaction term:** *iff log₁₀PF at the highest measured velocity exceeds
the series minimum.* Note this is an endpoint-vs-minimum test, **not** monotonicity — a
mid-range dip is ignored, since impaction lives at the top end. In the historical nine-series comparison (including separate grey and pink batches),
the five negatives sat at exactly 0.0% excess
(their fastest point *was* their minimum) and the positives at 0.9%, 6.4%, 19.2%, 23.6%.
Those nine series are not nine distinct fitted materials; blue holey is borderline, as noted below.

Guard: require the fitted B > 0. If the upturn is noise the constrained fit returns
B ≈ 0 and you revert to two terms automatically.

The high-velocity endpoint supplies much of the information about B and β in these
sparse sweeps. This is a fit/extrapolation limitation, not an open question about
whether impaction exists. It matters especially above the tested velocity range;
normal design work generally stays within that range. Retain the impaction term,
while distinguishing the mechanism from how precisely its parameters are measured.

Two cautions on the rule. Blue holey passes by only 0.9%, inside the ±6% replicate
noise — kept because the 2-term model cannot produce an upturn at all, so it is
directional evidence, and because the fitted curve is visibly better across the whole
range rather than at one point. And pink batch 1 also triggers, at 6.4% — a batch
already distrusted for the aerosol reason, so the rule will pull in bad data as readily
as good.

**Why the single power law was dropped.** No mechanism, and its slope was not stable —
−0.16 to −0.30 across series. It survives only where the velocity range is too narrow to
resolve curvature.

**Why bypass terms were dropped.** Chiefly because a bypass path is not plausible in the
construction actually used — stuffed and clamped rolls with no route round the material
that would survive assembly. And because bypass combined with the multi-term form is too
flexible: between them they can be tuned to match almost any shape, so a good fit is not
evidence. Two variants also fail on their own terms: *correlated bypass* (fraction f past
the whole stack) goes to f = 0 when grey A and grey B are constrained to share one, and
there is no reason for f to persist across geometries; *in-layer holes* at flow fraction φ
give log₁₀PF = N·log₁₀PF₁ with no bundle-level saturation, so the effect is a near-constant
downward shift — **degenerate with D and C**, already inside the fitted coefficients and
not separable from this data. (φ is a *flow* fraction, not open area: holes are far less
resistive per unit area, ρ ≈ 0.003–0.01, so φ = 47% is only ~0.3–0.9% open area.)

## The aerosol effect

Pink batch 1 and batch 2 are the same material and build but differ by up to 0.44 logs,
far outside the ±6% replicate noise. The cause is the challenge aerosol: batch 1 used
natural background, batch 2 incense. It is visible in the counts — batch 1 has an
external 0.5/0.3 µm ratio of 0.58–0.62 against 0.32–0.36 for every other series, and
external 0.3 µm counts of ~20,000 against 70,000–270,000.

**Incense gives lower PF**, consistent with its size distribution sitting nearer the
MPPS. Every other series used incense, so batch 2 is the matched comparator.

## Rolled-bundle geometry

A strip of length L folded f times, rolled outward from core radius r_i:

    r_1 = sqrt(r_0^2 + L*tau/pi)        tau = f * t_layer
    N   = f*L / (pi*(r_o + r_i))        layers — independent of t_layer

N depends only on r_o + r_i, so **whichever material sits innermost gets more layers**.

**A part-turn is not worth its layers.** It leaves one sector of the circumference
thinner than the rest, and penetration is area-weighted, so the thin sector dominates —
three layers spread over 1.3 turns is worth far less than four over one turn. Where the
folded wrap is **≥ 1 cm thick**, count whole turns only and round down; a turn of an
f-ply fold lays down f layers and f·t of radial depth. Below 1 cm the sector is thin
enough that a part-turn is a fair approximation, and counting it beats discarding the
cloth.

`t_layer` is measured by rolling a known strip solid and measuring the circumference,
t = πr_o²/(f·L). That, plus the built roll's circumference, then pins the core:
r_i² = r_o² − (material area)/π. Both measurements are needed — one circumference alone
leaves t and ID degenerate.

The solid roll and the built roll may use different sides of the same piece — grey holey
(173 × 137 cm) was rolled solid along its 137 cm side and built along its 173 cm side.

**A correction to t is not just a rescale where the core was derived from t.** r_i comes
out of r_o² − (material area)/π, so changing t moves the geometry and hence the per-cm
coefficients; that series has to be refitted. Only where r_i is pinned independently — as
in both grey fuzzy series, where the sheet's own v_mid column fixes it — does a change in
t leave the per-cm values alone and simply re-split them per layer.

**Ordering rule for multi-material bundles.** Not cheapest-first. At each radius place
the material maximising a_j(v) − λ·k_j·v, where a is logs/cm, k is Pa/(cm/s)/cm and λ is
the pressure shadow price. For any pair this gives a crossover velocity

    v* = [ (delta_a) / (lambda * delta_k) ]^(1/(1+alpha))

with the better-but-costlier material on the **slow** side, i.e. outward. Tighter
pressure budget → larger λ → lower v*.

## What was superseded

The flat-sheet bench rig produced a 1-layer gross fit (slope −0.222), then a net-of-rig
per-layer analysis across 1/2/4/8 layers giving a near-flat 8-layer slope (−0.048) and a
claimed n^−0.187 decline in per-layer protection with stack depth. Both are wrong: the
roll series give −0.218 and −0.282, and going from grey A's 9.55 layers to grey B's 12.52
shows per-layer protection 2.8% *up*. The original 1-layer bench slope agreed with the
rolls; the layer-count correction broke it. The bench also under-predicts roll pressure
drop by 1.6×.

## Standing assumptions

- **Constructed-build shortfall.** Multi-material builds often underperform predictions
  assembled from single-material fits: measured PF can be **about half the predicted PF**.
  In the grey-fuzzy + pink
  run, with pink wrapped length 125 cm, the current model predicts PF 101 versus 51 measured at
  240 L/min. Across 154–522 L/min it overpredicts by 1.6–2.0×; see
  [the recalculated comparison](MODEL_CHECKS.md#grey-fuzzy--pink). The shortfall is flow-dependent: that run exceeds predictions at its lowest
  flow. Treat this as an observed discrepancy, not a universal correction or worst-case
  bound. A good single-material fit does not validate a combined build.
- **Layer-count independence** — every layer contributes the same regardless of depth, so
  QF is invariant to N. Coefficients were derived under it, so cross-series agreement is
  a consistency check, not a test.
- **Δp linear in Q** remains the model assumption. Current grey-fuzzy data are close
  to linear, but blue holey shows curvature and soft linen favours an offset;
  see [the pressure check](MODEL_CHECKS.md#pressure-linearity). No shared exponent or
  zero offset is established across materials.
- Folded plies are *registered* — same fabric, holes aligned — the worst case in
  `../../../filtration_modelling/fabric_analyse.py`. Rolled wraps are not.
- Fits cover roughly 0.3–5 cm/s (blue holey and towel to 11–13). Narrow cores push the
  inner face well past that.
