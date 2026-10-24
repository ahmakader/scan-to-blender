"""Level a scan and derive heightmaps in a metric local site frame.

Subcommands
  fit    points.npy  [--color water|green|grey|any] [--bbox x0 x1 y0 y1] [--out plane.json]
         Robust (IRLS) plane fit z = a*x + b*y + c to surfaces that must be horizontal. Prints the tilt.
  angle  ortho.png ortho.json
         Dominant building/street angle (deg, mod 90) from Hough lines on the orthophoto.
  frame  --plane plane.json --scale M_PER_UNIT --origin X Y --angle DEG [--datum 0] --out frame.json
         Writes the scan->site transform (4x4, includes levelling shear) used by every later step and by
         Blender to place the scan as a reference layer: x,y metres in the site grid, z metres above datum.
  dsm    points.npy --frame frame.json --extent U0 U1 V0 V1 [--res 0.3] [--ground-size 40] --out DIR
         DSM (max z, skirts removed), bare ground (8th-percentile filter over --ground-size metres), relative heights, local
         colour ortho, footprint candidates and tree blobs. PNG previews are written next to the arrays.
All arrays: row 0 = V1 (north / far edge), column 0 = U0.
"""
import argparse, json, math, os, sys
import numpy as np
from scipy import ndimage


def colour_mask(rgb, kind):
    import cv2
    hsv = cv2.cvtColor(rgb.astype(np.uint8).reshape(-1, 1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3).astype(float)
    h, s, v = hsv.T
    if kind == 'water':
        return (h > 85) & (h < 120) & (s > 30)
    if kind == 'green':
        return (h > 30) & (h < 85) & (s > 40)
    if kind == 'grey':
        return (s < 35) & (v > 60)
    return np.ones(len(rgb), bool)


def irls_plane(x, y, z, iters=12):
    A = np.stack([x, y, np.ones_like(x)], 1); w = np.ones_like(z)
    for _ in range(iters):
        c, *_ = np.linalg.lstsq(A * w[:, None], z * w, rcond=None)
        r = z - A @ c; s = np.median(np.abs(r)) * 1.5 + 1e-9
        w = 1 / (1 + (r / s) ** 2)
    return c, float(np.median(np.abs(r)))


def cmd_fit(a):
    P = np.load(a.points)
    m = colour_mask(P[:, 3:6], a.color)
    if a.bbox:
        x0, x1, y0, y1 = a.bbox
        m &= (P[:, 0] > x0) & (P[:, 0] < x1) & (P[:, 1] > y0) & (P[:, 1] < y1)
    if m.sum() < 100:
        sys.exit(f'only {m.sum()} points selected — widen --bbox or change --color')
    c, mad = irls_plane(P[m, 0].astype(float), P[m, 1].astype(float), P[m, 2].astype(float))
    tilt = math.degrees(math.atan(math.hypot(c[0], c[1])))
    print(f'plane z = {c[0]:.6f} x + {c[1]:.6f} y + {c[2]:.6f}   tilt {tilt:.2f} deg   residual MAD {mad:.4f}   n={m.sum()}')
    json.dump({'a': c[0], 'b': c[1], 'c': c[2], 'tilt_deg': tilt, 'n': int(m.sum())}, open(a.out, 'w'), indent=1)


def cmd_angle(a):
    import cv2
    im = cv2.imread(a.ortho, cv2.IMREAD_GRAYSCALE)
    im = cv2.resize(im, (2048, 2048))
    e = cv2.Canny(cv2.GaussianBlur(im, (5, 5), 0), 60, 160)
    lines = cv2.HoughLinesP(e, 1, np.pi / 720, 80, minLineLength=40, maxLineGap=4)
    if lines is None:
        sys.exit('no lines found')
    ang, wts = [], []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        ang.append(math.degrees(math.atan2(-(y2 - y1), x2 - x1)) % 90); wts.append(math.hypot(x2 - x1, y2 - y1))
    hist, edges = np.histogram(ang, 180, (0, 90), weights=wts)
    hist = ndimage.gaussian_filter1d(hist, 2, mode='wrap')
    best = (edges[np.argmax(hist)] + 0.25)
    if best > 45:
        best -= 90
    print(f'dominant angle {best:.1f} deg (rotate the site frame by this; lines counted: {len(ang)})')


def frame_matrix(f):
    S, ang = f['scale'], math.radians(f['angle'])
    ox, oy = f['origin']
    ca, sa = math.cos(-ang), math.sin(-ang)
    a, b, c = f['plane']['a'], f['plane']['b'], f['plane']['c']
    return np.array([[S * ca, -S * sa, 0, -S * (ca * ox - sa * oy)],
                     [S * sa, S * ca, 0, -S * (sa * ox + ca * oy)],
                     [-S * a, -S * b, S, -S * c + f.get('datum', 0.0)],
                     [0, 0, 0, 1]])


def cmd_frame(a):
    f = {'plane': json.load(open(a.plane)), 'scale': a.scale, 'origin': a.origin, 'angle': a.angle, 'datum': a.datum}
    f['matrix'] = frame_matrix(f).tolist()
    json.dump(f, open(a.out, 'w'), indent=1)
    print('wrote', a.out)


def to_site(P, f):
    M = np.array(f['matrix'])
    X = np.concatenate([P[:, :3].astype(np.float64), np.ones((len(P), 1))], 1) @ M.T
    return X[:, 0], X[:, 1], X[:, 2]


def fill_nan(a):
    m = np.isnan(a)
    if m.any():
        idx = ndimage.distance_transform_edt(m, return_distances=False, return_indices=True)
        a = a[tuple(idx)]
    return a


def cmd_dsm(a):
    import cv2
    from PIL import Image
    os.makedirs(a.out, exist_ok=True)
    P = np.load(a.points); f = json.load(open(a.frame))
    U, V, Z = to_site(P, f)
    u0, u1, v0, v1 = a.extent; r = a.res
    nu, nv = int((u1 - u0) / r), int((v1 - v0) / r)
    iu = ((U - u0) / r).astype(int); iv = ((v1 - V) / r).astype(int)
    ok = (iu >= 0) & (iu < nu) & (iv >= 0) & (iv < nv) & np.isfinite(Z)
    iu, iv, Zk, C = iu[ok], iv[ok], Z[ok], P[ok, 3:6]
    dsm = np.full((nv, nu), -1e9); np.maximum.at(dsm, (iv, iu), Zk)
    dsm[dsm < -1e8] = np.nan
    order = np.argsort(Zk)                                       # colour of the highest point per cell
    col = np.zeros((nv, nu, 3), np.uint8); col[iv[order], iu[order]] = C[order].astype(np.uint8)
    # mesh skirts / holes: cells far below their neighbourhood are not real surface
    med = ndimage.median_filter(fill_nan(dsm.copy()), size=max(3, int(10 / r) | 1))
    dsm[dsm < med - a.skirt] = np.nan
    dsm[dsm < np.nanmedian(dsm) - 4 * a.skirt - 10] = np.nan               # whole regions of skirt / no data
    holes = np.isnan(dsm)
    dsm = ndimage.median_filter(fill_nan(dsm), 3)
    k = max(3, int(a.ground_size / r) | 1)
    # bare ground: low percentile (robust to noise, unlike a pure min/opening) then smooth
    ground = ndimage.percentile_filter(dsm[::2, ::2], 8, size=max(3, k // 2))
    ground = ndimage.zoom(ground, (nv / ground.shape[0], nu / ground.shape[1]), order=1)[:nv, :nu]
    ground = ndimage.gaussian_filter(np.minimum(ground, dsm), k / 8)
    rel = dsm - ground
    np.save(os.path.join(a.out, 'dsm.npy'), dsm.astype(np.float32))
    np.save(os.path.join(a.out, 'ground.npy'), ground.astype(np.float32))
    np.save(os.path.join(a.out, 'rel.npy'), rel.astype(np.float32))
    np.save(os.path.join(a.out, 'holes.npy'), holes)
    Image.fromarray(col).save(os.path.join(a.out, 'local_ortho.png'))
    Image.fromarray((np.clip(rel / 12, 0, 1) * 255).astype(np.uint8)).save(os.path.join(a.out, 'rel_heights.png'))
    g = (ground - np.nanpercentile(ground, 1)) / (np.ptp(ground) + 1e-9)
    Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(os.path.join(a.out, 'ground.png'))
    # footprint candidates: elevated, not green
    hsv = cv2.cvtColor(col, cv2.COLOR_RGB2HSV).astype(float)
    green = (hsv[..., 0] > 30) & (hsv[..., 0] < 85) & (hsv[..., 1] > 40)
    b = ndimage.binary_closing(ndimage.binary_opening((rel > 2.0) & ~green, iterations=2), iterations=2)
    lab, n = ndimage.label(b)
    bld = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) * r * r < 8:
            continue
        (cx, cy), (w, h), ang = cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32))
        hh = float(np.median(rel[ys, xs]))
        bld.append(dict(u=u0 + cx * r, v=v1 - cy * r, w=w * r, d=h * r, rot=-ang, height=hh,
                        storeys=max(1, round(hh / 3.2)), fill=len(xs) / (w * h + 1e-6)))
    json.dump(bld, open(os.path.join(a.out, 'footprint_candidates.json'), 'w'), indent=1)
    # trees: green and tall
    t = ndimage.binary_opening(green & (rel > 2.0), iterations=2)
    lab, n = ndimage.label(t)
    trees = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = np.where(lab[sl] == i)
        if len(xs) * r * r < 2:
            continue
        ys = ys + sl[0].start; xs = xs + sl[1].start
        trees.append((u0 + xs.mean() * r, v1 - ys.mean() * r, math.sqrt(len(xs) / math.pi) * r,
                      float(np.percentile(rel[ys, xs], 90))))
    np.save(os.path.join(a.out, 'trees.npy'), np.array(trees, np.float32))
    print(f'grid {nu}x{nv} @ {r} m | ground {np.nanmin(ground):.2f}..{np.nanmax(ground):.2f} m | '
          f'{len(bld)} footprint candidates (hints only - merged blocks are common) | {len(trees)} tree blobs')


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('fit'); p.add_argument('points'); p.add_argument('--color', default='any')
    p.add_argument('--bbox', type=float, nargs=4); p.add_argument('--out', default='plane.json')
    p = sp.add_parser('angle'); p.add_argument('ortho'); p.add_argument('ortho_json')
    p = sp.add_parser('frame'); p.add_argument('--plane', required=True); p.add_argument('--scale', type=float, required=True)
    p.add_argument('--origin', type=float, nargs=2, required=True); p.add_argument('--angle', type=float, required=True)
    p.add_argument('--datum', type=float, default=0.0); p.add_argument('--out', default='frame.json')
    p = sp.add_parser('dsm'); p.add_argument('points'); p.add_argument('--frame', required=True)
    p.add_argument('--extent', type=float, nargs=4, required=True); p.add_argument('--res', type=float, default=0.3)
    p.add_argument('--ground-size', type=float, default=20.0)
    p.add_argument('--skirt', type=float, default=6.0, help='drop cells this far (m) below their 10 m neighbourhood'); p.add_argument('--out', required=True)
    a = ap.parse_args()
    {'fit': cmd_fit, 'angle': cmd_angle, 'frame': cmd_frame, 'dsm': cmd_dsm}[a.cmd](a)


if __name__ == '__main__':
    main()
