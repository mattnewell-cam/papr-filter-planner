# PAPR Filter Planner

Pick the blankets and towels you actually own, give a pressure budget, an airflow target
and the space you have, and it returns a rolled-filter build spec that maximises
protection factor — which material goes at which radius, how to fold each piece, how many
turns, and what Δp and PF to expect.

The filtration model is fitted from whole-bundle prototype sweeps, not bench coupons:
per layer, `log10PF = A·v^-α + C + B·v^β`, with `Δp = k·v`. Flow through a roll is radial,
so face velocity falls as `v(r) = Q/(2πrH)` and both quantities are integrated over radius.

Everything runs in the browser. No backend, no data leaves the page.

## Editing

`src.html` is the source. `index.html` is generated — don't edit it directly.

```
python build.py && git commit -am "..." && git push
```

GitHub Pages redeploys on push.
