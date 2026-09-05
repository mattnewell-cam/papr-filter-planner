# Reproducing material fits

Live source: [DIY PAPR Testing — Prototype PF & Q](https://docs.google.com/spreadsheets/d/1vNnPBNcy6AXGmybD3XqS8CLbzuCFn33SeNJbljD8o0Y/edit?gid=1848070649#gid=1848070649).

`fit_materials.py` fits the recorded prototype data using the explicit row selections
and geometry in `fit_series.json`. Workbook and CSV exports stay in Google Drive;
download and export them as described in the [repository README](../README.md#measurement-data).
Run from `testing/`:

```text
python -m pip install numpy scipy
python fit_materials.py --output fitted_coefficients.json
python theory_examples.py
```

The script leaves `coefficients.json` unchanged and reports differences in resistance.
The grey core diameters are taken from the sheet formulas. Pink and towel are 2 ply.
Pink wrapped length is **125 cm per ply** (250 cm total stock).
With the recorded 42.5 cm outer circumference and 0.4688 cm
per-ply thickness, this gives a calculated core ID of **58.13 mm**, not a measured
diameter. Missing inputs are reported.

Towel geometry uses **2 × 85.5 cm** (171 cm total stock),
32.5 cm outer circumference and 40 cm effective axial length. Thickness comes from
the separate 4 × 130 cm solid roll with 42 cm circumference: 0.2699513 cm per ply.
These inputs give **69.46 mm ID and k_layer = 3.5894 Pa/(cm/s) per ply**.
Effective axial length excludes dead material and must not be equated to the full
folded dimension.

Inputs use cm, cm/s, cm³/s and Pa. Column B in the saved export is circumference.
Column F is L/min, G is log10PF, K is calculated
centre pressure, and Y is its manometer observation. A missing Y excludes that row
from the pressure fit even if K caches zero. A measured numeric zero stays zero.
After refreshing or restructuring the sheet, check the manifest's row map and the
column mapping in `observations`; material-name checks catch displaced series.

The fit integrates the velocity-dependent capture terms across the radial wall.
Geometry and thickness are inputs, not adjustable fit parameters. Residuals are
unweighted whole-bundle log10PF; alpha is constrained to (0, 2/3], beta to (0, 1],
and D/C/B are nonnegative. The endpoint upturn rule is applied within each geometry.
Pressure uses a least-squares line through zero. RMSE, row lists, input hashes and
geometry provenance accompany the output. Only current single-material runs above
`OLD / IGNORE` are selected. H is read from column C per row; all six duvet rows
record 42 cm.

The output distinguishes midpoint velocity ranges from the full local velocity
range across the measured annuli. Do not treat an old midpoint range as a measured
range at every radius. Parameter agreement alone is not independent validation;
review prediction residuals and geometry before replacing published coefficients.

Constructed multi-material builds often fall below single-material-based predictions:
measured PF can be about half the predicted PF. This is flow-dependent, not a universal correction; see `RESULTS.md`.

`theory_examples.py` independently recalculates the worked geometry and scaling
tables using the published coefficients; it does not fit or change them.

To regenerate plots of all seven materials (filtration and pressure) and the grey+pink
comparison, run:

```text
python -m pip install numpy scipy matplotlib
python plot_fits.py
```

PNG and SVG outputs go into `plots/`; use `--out PATH` to choose another folder.
The script reads the saved CSV, geometry manifest and published coefficients without
refitting. It plots only the measured flow range and records input hashes. Impaction
comparisons omit the term while retaining the other coefficients; they are not refits.
These are current-data plots, not reproductions of superseded fit variants.
For the 3D geometry surfaces, use `roll_surface.py` as described in `../THEORY.md` §7.

To refresh the prototype CSV after downloading the live sheet as XLSX, run
`python export_prototype.py fresh-download.xlsx`. The export preserves worksheet
row numbers and puts dashes in missing pressure fields without editing the XLSX.
`prototype_pf_q.source.json` records the source hash; its export timestamp must
not be mistaken for the last live-sheet download date. The archived workbook tabs
retain the superseded bench measurements; only the prototype has a standalone CSV.
