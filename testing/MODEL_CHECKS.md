# Pressure linearity and grey+pink prediction checks

Rechecked on 5 September 2026 against the saved `Prototype PF & Q` export. Reproduce
with `python check_pressure_and_mixing.py` (numpy and scipy). The script reads the
data and published coefficients without changing them.

Inputs for the numbers below:

- `prototype_pf_q.csv` SHA256: `0b5d4b8426df5f421d5cf7bd90948e4e731ac2f7389f9e094a09a351ef4474b6`.
- `coefficients.json` SHA256: `1a16d0a8c7862b4e592ac28f724401cead79759930ffafc0605f8e0d0dbd5e94`.
- [Live source](https://docs.google.com/spreadsheets/d/1vNnPBNcy6AXGmybD3XqS8CLbzuCFn33SeNJbljD8o0Y/edit?gid=1848070649#gid=1848070649);
  geometry and row provenance in [FITTING.md](FITTING.md).

## Grey fuzzy + pink

Rows 17–23: grey inside at 2 ply, pink outside at 3 ply, 125 cm wrapped length each,
60.5 cm outer circumference and 43 cm axial length. The published thicknesses imply
a 3.772945 cm core radius. Predictions integrate the published single-material fits
through these radial bands.

| Q (L/min) | Measured PF | Predicted PF | Predicted / measured |
|---:|---:|---:|---:|
| 521.74 | 34.45 | 55.90 | 1.62 |
| 342.86 | 39.55 | 75.18 | 1.90 |
| 240.00 | 50.55 | 100.84 | 2.00 |
| 153.85 | 89.40 | 155.06 | 1.73 |
| 75.00 | 269.99 | 375.44 | 1.39 |
| 35.29 | 2267.00 | 1326.71 | 0.59 |
| 35.29 | 1764.55 | 1326.71 | 0.75 |

The model overpredicts PF by roughly 1.6–2.0× over the measured 154–522 L/min range.
That description does not cover the whole sweep: the lowest-flow readings exceed
the prediction. The old claim of agreement near 180 L/min and the old residual range
should not be carried forward. Neither a constant correction factor nor a universal
claim that the combined build performs better is supported.

There are no recorded centre-pressure measurements for these rows. The old claim of
1.7× lower resistance was inferred by treating fan-voltage-derived stall pressure as
the operating pressure. It does not establish measured mixed-material resistance.
The PF shortfall also does not establish improved QF: pressure was not measured.

## Pressure linearity

Use current single-material rows from `fit_series.json`, grouped by recorded
circumference and axial length. Include column K pressure only where column Y contains
a manometer observation. Q is column F. Fits minimise squared residuals in **Pa** with
equal weight per observation; they are not log-space regressions.

Compare `p = kQ`, `p = kQ + c`, and `p = a(Q/100)^n`. For each model, also leave out
each observation in turn, refit the others and predict the omitted pressure. This
checks whether the extra parameter improves predictions of withheld points. With only
4–6 points per series, these are descriptive comparisons, not precise exponent estimates.

| Material (rows) | Q range (L/min) | Power exponent n | Offset c (Pa) | Fit RMSE: linear / offset / power (Pa) | Withheld-point RMSE: linear / offset / power (Pa) |
|---|---:|---:|---:|---:|---:|
| Grey fuzzy (5–9) | 26–300 | 0.979 | +6.60 | 9.50 / 8.63 / 9.39 | 13.75 / 18.73 / 24.94 |
| Grey holey (25–28) | 111–444 | 0.971 | +0.82 | 0.49 / 0.36 / 0.38 | 0.70 / 0.63 / 0.68 |
| Soft linen (36–40) | 32–267 | 0.955 | +11.81 | 7.05 / 2.84 / 4.02 | 8.10 / 5.18 / 10.49 |
| Blue holey (49–54) | 59–706 | 1.204 | −19.58 | 13.82 / 8.63 / 3.74 | 19.12 / 14.48 / 6.61 |
| Duvet (56–61) | 103–750 | 1.272 | −8.53 | 6.56 / 5.01 / 3.50 | 10.39 / 9.64 / 8.46 |
| Pink (11–15) | 33–632 | 1.114 | −9.63 | 11.07 / 9.26 / 7.48 | 15.20 / 14.73 / 23.85 |
| Towel (42–47) | 67–857 | 0.984 | +7.08 | 8.12 / 7.00 / 8.05 | 9.59 / 12.46 / 15.98 |

**The old universal 0.889 exponent is not reproduced by these current fits.** Grey
fuzzy is close to linear; allowing a +6.6 Pa offset slightly improves its in-sample
fit but worsens withheld-point predictions. Its current sweep already reaches
26 L/min, so the old request for one point below 30 L/min is stale.

Blue holey gives the clearest evidence against a straight line through zero over its
tested range: the power curve improves both fit and withheld-point errors. Duvet shows
weaker evidence in the same direction. Soft linen instead favours a positive offset.
There is no common offset or exponent across all materials.

These fits cannot distinguish material behaviour from construction or measurement
effects. Flow uncertainty is not modelled, and a fitted intercept is not a measured
zero. A single replicate pair does not justify dismissing all series' curvature as
noise. Keep the published linear model for now; the useful follow-up is fan-off zero
checks and repeated pressure/flow sweeps, particularly for blue holey and soft linen,
before deciding whether a model change is warranted.
