# PAPR filter bank

Models, measurements analysis, and design tools for rolled filters made from
household blankets and towels.

| Resource | Contents |
|---|---|
| [Live planner](https://mattnewell-cam.github.io/papr-filter/) | Choose materials, airflow, pressure and size limits to calculate a proposed rolled-filter build. |
| [Planner source](planner/README.md) | Browser app, build script, solver tests, reference cases and material photographs. |
| [Filter theory](THEORY.md) | Pressure-budget allocation, material mixing and bundle geometry. |
| [Measured results](testing/RESULTS.md) | Published material fits, test conditions and model limitations. |
| [Fitting procedure](testing/FITTING.md) | Data preparation, geometry inputs, fitting and plot reproduction. |
| [Model checks](testing/MODEL_CHECKS.md) | Pressure linearity and measured versus predicted multi-material performance. |
| [Fit coefficients](testing/coefficients.json) | Published per-layer coefficients and measured velocity ranges. |
| [Fit plots](testing/plots/) | Filtration, pressure and combined-material comparisons. |

The models use count-based PF at 0.3 µm. Reported quality factors are in kPa⁻¹.
Constructed multi-material builds can perform below predictions from the individual
material fits; see the measured results and model checks.

## Measurement data

The source workbook lives in [DIY PAPR Testing on Google Sheets](https://docs.google.com/spreadsheets/d/1vNnPBNcy6AXGmybD3XqS8CLbzuCFn33SeNJbljD8o0Y/edit).
Workbook and CSV exports are excluded from Git. To run the analyses that use raw
measurements, download the workbook as `testing/filter_testing.xlsx`, then run:

```sh
python -m pip install -r testing/requirements.txt
python testing/export_prototype.py
```

Check the row mapping in `testing/fit_series.json` after changes to the source sheet.
The manifest and committed plots describe the September 5, 2026 data snapshot.
The published coefficients predate that refresh; refitting does not automatically
replace them. The bundle model and theory examples use the published coefficients
and do not require the workbook export.

## Planner development

```sh
python planner/build.py
node planner/test-solver.cjs
```

Edit `planner/src.html`. The build generates both `planner/index.html` and the root
`index.html`, preserving the existing GitHub Pages URL. GitHub Pages serves the
repository root on `main`.

`testing/fill_sheet.gs` is a historical Apps Script for the superseded flat-sheet
bench analysis, retained for provenance. Current fits use the whole-bundle prototype
measurements described in `testing/FITTING.md`.
