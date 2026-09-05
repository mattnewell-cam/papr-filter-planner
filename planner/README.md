# PAPR Filter Planner

Pick the blankets and towels you actually own, give a pressure budget, an airflow target
and the space you have, and it returns a rolled-filter build spec that maximises
protection factor — which material goes at which radius, how to fold each piece, how many
turns, and what Δp and PF to expect.

The filtration model is fitted from whole-bundle prototype sweeps, not bench coupons:
per layer, `log10PF = A·v^-α + C + B·v^β`, with `Δp = k·v`. Flow through a roll is radial,
so face velocity falls as `v(r) = Q/(2πrH)` and both quantities are integrated over radius.

Measurements and fitting notes live in `../testing/`. Constructed multi-material
builds often underperform single-material-based predictions: measured PF can be
about half the predicted PF.
This is an observed, flow-dependent discrepancy, not a universal correction or bound.

Everything runs in the browser. No backend, no data leaves the page.

`materials/` holds the original material photographs. The planner embeds its display
images directly in `src.html`; it does not load these files at runtime.

The optimiser searches material order, folds, quantities and geometry together with
deterministic differential-evolution populations, followed by local refinement.
For up to three materials, populations explore every material order explicitly;
larger selections use four populations that evolve the order as well.
It includes every allowed fold orientation, permits unused materials, and searches
one contiguous band per material. Thick folded wraps use whole turns; thin wraps
allow fractional turns. Scores and budgets come directly from the returned bands.
Previous feasible plans are retained and rechecked after input changes.

This is a bounded heuristic, not a proof of a global optimum. Run `node test-solver.cjs`
for feasibility, repeatability, relaxed-budget and runtime regressions. The 20 quality
cases must come within 0.006 log10 PF (about 1.4% PF) of longer-search references and
each finish in under one second on the testing machine. The varied reference inputs
in `solver-reference.json` were generated with random seed 123 and evaluated with
eight populations of 1,000 generations; the seven standard cases used ten populations
of 900 generations. Default and pressure-sensitivity references were strengthened
using all six material orders and 1,200 generations per population after a pressure
sensitivity miss revealed that longer runs alone could still converge to one order.
These references are best-known feasible scores, not upper bounds.
`node test-solver.cjs --legacy` also compares the previous solver's scores and times;
its reported scores can include bands it subsequently removed.

## Editing

`src.html` is the source. `index.html` is generated — don't edit it directly.
The planner is published at https://mattnewell-cam.github.io/papr-filter/planner/.
Run these commands from `planner/`:

```
python build.py && git commit -am "..." && git push
```

GitHub Pages redeploys on push.
