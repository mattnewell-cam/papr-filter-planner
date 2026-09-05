#!/usr/bin/env python3
"""src.html -> index.html.

src.html is the canonical source and is also what gets published as an Artifact, so it
carries no <!doctype>/<html>/<head>/<body> - the Artifact runtime supplies those. This
wraps it for ordinary web hosting. Run after editing src.html, then commit and push.
"""
import io, os, sys

here = os.path.dirname(os.path.abspath(__file__))
src  = io.open(os.path.join(here, 'src.html'), encoding='utf-8').read()

anchor = src.index('<header class="top">')
cut    = src.rindex('</style>', 0, anchor) + len('</style>')
head, body = src[:cut], src[cut:]

out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Work out how to roll household blankets into an air filter: pick what you own, give your pressure and size budget, get a build spec that maximises protection factor.">
<meta name="color-scheme" content="light dark">
<style>img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""
io.open(os.path.join(here, 'index.html'), 'w', encoding='utf-8').write(out)
# Keep the original GitHub Pages entry point when this repo includes testing/theory.
io.open(os.path.join(here, '..', 'index.html'), 'w', encoding='utf-8').write(out)
print(f'index.html  {len(out)//1024} KB')
