"""Crop the scan orthophoto in the metric site frame with a labelled grid, for tracing footprints and
measuring objects (cars, doors) by eye.

python grid_crop.py ortho.png ortho.json --u U0 U1 --v V0 V1 [--frame frame.json] [--grid 2] [--px 1400]
                    [--overlay layout.json] --out crop.png
Without --frame, U/V are scan-world X/Y (scan units) — use that before the scale is known.
--overlay draws rectangles from a JSON list of {u, v, w, d, rot, name} (site metres) to check a trace.
"""
import argparse, json, math
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
ap = argparse.ArgumentParser()
ap.add_argument('ortho'); ap.add_argument('ortho_json')
ap.add_argument('--u', type=float, nargs=2, required=True); ap.add_argument('--v', type=float, nargs=2, required=True)
ap.add_argument('--frame'); ap.add_argument('--grid', type=float, default=2.0); ap.add_argument('--px', type=int, default=1400)
ap.add_argument('--overlay'); ap.add_argument('--out', required=True)
a = ap.parse_args()

oj = json.load(open(a.ortho_json))
im = np.asarray(Image.open(a.ortho).convert('RGB')); H, W = im.shape[:2]
(U0, U1), (V0, V1) = a.u, a.v
w = a.px; h = int(w * (V1 - V0) / (U1 - U0))
uu = U0 + (np.arange(w) + .5) / w * (U1 - U0); vv = V1 - (np.arange(h) + .5) / h * (V1 - V0)
UU, VV = np.meshgrid(uu, vv)
if a.frame:
    f = json.load(open(a.frame)); S = f['scale']; ang = math.radians(f['angle']); ox, oy = f['origin']
    X = ox + (UU * math.cos(ang) - VV * math.sin(ang)) / S
    Y = oy + (UU * math.sin(ang) + VV * math.cos(ang)) / S
else:
    X, Y = UU, VV
px = np.clip((X - oj['x0']) / (oj['x1'] - oj['x0']) * W, 0, W - 1).astype(int)
py = np.clip((oj['y1'] - Y) / (oj['y1'] - oj['y0']) * H, 0, H - 1).astype(int)
out = Image.fromarray(im[py, px]); d = ImageDraw.Draw(out)
g = a.grid
for gu in np.arange(math.ceil(U0 / g) * g, U1, g):
    x = (gu - U0) / (U1 - U0) * w; d.line([(x, 0), (x, h)], fill=(255, 0, 0))
    d.text((x + 2, 2), f'{gu:g}', fill=(255, 255, 0)); d.text((x + 2, h - 12), f'{gu:g}', fill=(255, 255, 0))
for gv in np.arange(math.ceil(V0 / g) * g, V1, g):
    y = (V1 - gv) / (V1 - V0) * h; d.line([(0, y), (w, y)], fill=(255, 0, 0))
    d.text((2, y + 2), f'{gv:g}', fill=(255, 255, 0)); d.text((w - 40, y + 2), f'{gv:g}', fill=(255, 255, 0))
if a.overlay:
    for b in json.load(open(a.overlay)):
        c, s = math.cos(math.radians(b.get('rot', 0))), math.sin(math.radians(b.get('rot', 0)))
        pts = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x = b['u'] + sx * b['w'] / 2 * c - sy * b['d'] / 2 * s; y = b['v'] + sx * b['w'] / 2 * s + sy * b['d'] / 2 * c
            pts.append(((x - U0) / (U1 - U0) * w, (V1 - y) / (V1 - V0) * h))
        d.polygon(pts, outline=(0, 255, 255)); d.text(pts[3], b.get('name', ''), fill=(0, 255, 255))
out.save(a.out); print('wrote', a.out, out.size)
