"""Example building types, roofs, pools and furniture (from a tropical beach-resort build). Adapt per project:
one function per building type, driven by entries in layout.py. Uses MATS names from lib_mat.py."""
import math, random
import numpy as np
from lib_mesh import MB
from lib_mat import MATS

PLINTH = 0.35
FLOOR = 3.4
SLAB = 0.3
PARAPET = 0.65
WALL = 0.25


# ============================================================ furniture (local-frame helpers on an MB)
def daybed(mb, x, y, z, rz=0, w=0.9, l=2.0):
    M = MATS
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    def P(dx, dy): return (x + dx * c - dy * s, y + dx * s + dy * c)
    def B(dx0, dx1, dy0, dy1, z0, z1, m):
        px, py = P((dx0 + dx1) / 2, (dy0 + dy1) / 2)
        mb.cbox(px, py, z + (z0 + z1) / 2, dx1 - dx0, dy1 - dy0, z1 - z0, m, rz)
    B(-w / 2, w / 2, -l / 2, l / 2, 0.12, 0.3, M['teak'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            B(sx * w / 2 - 0.04 * sx - 0.03, sx * w / 2 - 0.04 * sx + 0.03, sy * l / 2 - 0.05 * sy - 0.03, sy * l / 2 - 0.05 * sy + 0.03, 0, 0.12, M['teak'])
    B(-w / 2 + 0.03, w / 2 - 0.03, -l / 2 + 0.03, l / 2 - 0.03, 0.3, 0.44, M['fabric_cream'])
    B(-w / 2, w / 2, -l / 2, -l / 2 + 0.06, 0.3, 0.75, M['teak'])
    B(-w / 2 + 0.08, w / 2 - 0.08, -l / 2 + 0.06, -l / 2 + 0.24, 0.44, 0.78, M['fabric_white'])


def lounger(mb, x, y, z, rz=0):
    M = MATS
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    def B(dx, dy, dz, sx, sy, sz, m, tilt=0):
        mb.cbox(x + dx * c - dy * s, y + dx * s + dy * c, z + dz, sx, sy, sz, m, rz)
    B(0, 0.2, 0.28, 0.7, 1.5, 0.06, M['teak'])
    B(0, 0.2, 0.34, 0.66, 1.46, 0.07, M['fabric_cream'])
    for k in range(6):  # raised backrest steps
        B(0, -0.6 - k * 0.07, 0.38 + k * 0.08, 0.66, 0.08, 0.07, M['fabric_cream'])
    for sx in (-0.3, 0.3):
        for sy in (-0.45, 0.85):
            B(sx, sy, 0.13, 0.05, 0.05, 0.26, M['teak'])


def chair_rattan(mb, x, y, z, rz=0):
    M = MATS
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    def B(dx, dy, dz, sx, sy, sz, m):
        mb.cbox(x + dx * c - dy * s, y + dx * s + dy * c, z + dz, sx, sy, sz, m, rz)
    B(0, 0, 0.45, 0.5, 0.5, 0.06, M['rattan'])
    B(0, -0.23, 0.72, 0.5, 0.05, 0.5, M['rattan'])
    for sx in (-0.22, 0.22):
        for sy in (-0.22, 0.22):
            B(sx, sy, 0.21, 0.035, 0.035, 0.42, M['teak'])


def table_round(mb, x, y, z, r=0.45):
    M = MATS
    mb.cyl(x, y, z + 0.72, z + 0.76, r, M['teak'], n=20)
    mb.cyl(x, y, z, z + 0.72, 0.06, M['teak_dark'], 0.05, n=8)
    mb.cyl(x, y, z, z + 0.03, 0.25, M['teak_dark'], n=12)


def pendant(mb, x, y, ztop, drop=1.2, r=0.28):
    M = MATS
    mb.cyl(x, y, ztop - drop, ztop, 0.006, M['teak_dark'], n=4, cap=False)
    mb.sphere(x, y, ztop - drop - r * 0.6, r, M['rattan'], 1, 1, 0.75, 12, 8)
    mb.sphere(x, y, ztop - drop - r * 0.6, r * 0.3, M['lamp_warm'], nu=8, nv=6)


def bean_bag(mb, x, y, z, rz=0):
    mb.sphere(x, y, z + 0.28, 0.62, MATS['fabric_white'], 1.0, 0.9, 0.48, 16, 10)
    mb.sphere(x, y - 0.25, z + 0.55, 0.42, MATS['fabric_white'], 1.1, 0.6, 0.6, 12, 8)


def parasol_closed(mb, x, y, z, h=2.4):
    mb.cyl(x, y, z, z + h, 0.025, MATS['teak'], n=8)
    mb.cyl(x, y, z + h * 0.45, z + h, 0.12, MATS['fabric_white'], 0.03, n=12)
    mb.cyl(x, y, z - 0.02, z + 0.08, 0.22, MATS['stone_dark'], n=12)


def thatch_umbrella(mb, x, y, z, r=1.5, h=2.6):
    mb.cyl(x, y, z, z + h, 0.06, MATS['timber_post'], n=8)
    mb.cyl(x, y, z + h - 0.6, z + h + 0.15, r, MATS['thatch'], 0.08, n=24)
    mb.cyl(x, y, z + h - 0.75, z + h - 0.6, r * 1.02, MATS['thatch'], r, n=24, cap=False)


def cabana(mb, x, y, z, rz=0):
    M = MATS
    w, l, h = 2.2, 2.5, 2.5
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    def P(dx, dy): return x + dx * c - dy * s, y + dx * s + dy * c
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = P(sx * w / 2, sy * l / 2)
            mb.cbox(px, py, z + h / 2, 0.1, 0.1, h, M['teak'], rz)
            # tied-back curtains at each post
            mb.cyl(px - 0.08 * sx * c, py - 0.08 * sx * s, z + 0.1, z + h - 0.05, 0.09, M['canvas_sheer'], 0.14, n=8)
    mb.cbox(x, y, z + h + 0.05, w + 0.15, l + 0.15, 0.12, M['teak'], rz)
    mb.cbox(x, y, z + h + 0.17, w + 0.3, l + 0.3, 0.12, M['fabric_white'], rz)
    mb.cbox(x, y, z + 0.25, w - 0.2, l - 0.2, 0.3, M['teak'], rz)
    mb.cbox(x, y, z + 0.5, w - 0.25, l - 0.25, 0.2, M['fabric_white'], rz)
    for k in range(3):
        px, py = P(-0.6 + k * 0.6, -l / 2 + 0.35)
        mb.cbox(px, py, z + 0.78, 0.5, 0.18, 0.36, M['fabric_cream'] if k % 2 else M['fabric_amber'], rz)


def potted_plant(mb, x, y, z, r=0.3):
    mb.cyl(x, y, z, z + 0.55, r * 0.8, MATS['concrete_grey'], r, n=14)
    mb.sphere(x, y, z + 0.9, r * 1.4, MATS['leaf_shrub'], 1, 1, 1.1, 10, 7)


def bed(mb, x, y, z, rz=0):
    M = MATS
    mb.cbox(x, y, z + 0.25, 1.9, 2.1, 0.5, M['teak'], rz)
    mb.cbox(x, y + 0.05, z + 0.58, 1.85, 2.0, 0.18, M['fabric_white'], rz)
    mb.cbox(x, y - 1.0, z + 0.7, 2.0, 0.08, 1.2, M['teak_dark'], rz)
    for k in (-0.45, 0.45):
        mb.cbox(x + k, y - 0.75, z + 0.75, 0.7, 0.25, 0.18, M['fabric_white'], rz)
    mb.cbox(x, y + 0.65, z + 0.69, 1.9, 0.5, 0.05, M['fabric_amber'], rz)


# ============================================================ pools
def pool_basin(mb, x0, x1, y0, y1, water_z, depth, tile_mat, coping=0.35, coping_mat=None, infinity_edge=None):
    """Sunken basin in the MB local frame. water_z: water surface; coping top at water_z + 0.12."""
    M = MATS
    top = water_z + 0.12
    fl = water_z - depth
    t = 0.2
    mb.box(x0, x1, y0, y1, fl - t, fl, tile_mat)                  # floor
    mb.box(x0 - t, x0, y0 - t, y1 + t, fl - t, top - 0.05, tile_mat)
    mb.box(x1, x1 + t, y0 - t, y1 + t, fl - t, top - 0.05, tile_mat)
    mb.box(x0, x1, y0 - t, y0, fl - t, top - 0.05, tile_mat)
    if infinity_edge == 'y1':
        mb.box(x0, x1, y1, y1 + t, fl - t, water_z - 0.01, tile_mat)       # vanishing edge weir
        mb.box(x0 - t, x1 + t, y1 + t, y1 + 0.9, water_z - 0.6, water_z - 0.5, tile_mat)  # catch gutter
        mb.box(x0 - t, x1 + t, y1 + 0.9, y1 + 1.1, water_z - 0.6, top - 0.25, coping_mat or M['concrete_grey'])
    else:
        mb.box(x0, x1, y1, y1 + t, fl - t, top - 0.05, tile_mat)
    cm = coping_mat or M['concrete_grey']
    mb.box(x0 - coping, x0, y0 - coping, y1 + (0 if infinity_edge else coping), top - 0.05, top, cm)
    mb.box(x1, x1 + coping, y0 - coping, y1 + (0 if infinity_edge else coping), top - 0.05, top, cm)
    mb.box(x0, x1, y0 - coping, y0, top - 0.05, top, cm)
    if not infinity_edge:
        mb.box(x0, x1, y1, y1 + coping, top - 0.05, top, cm)
    # water (slightly inset so it never z-fights the tiles)
    mb.box(x0 + 0.002, x1 - 0.002, y0 + 0.002, y1 - 0.002 + (0.2 if infinity_edge else 0), fl + 0.01, water_z, M['pool_water'])


# ============================================================ villa
def villa(v, coll, pad, rng):
    M = MATS
    w, d = v['w'], v['d']
    st = v['storeys']
    mb = MB(v['name'], (v['c'][0], v['c'][1], pad), v['rot'])
    x0, x1, y0, y1 = -w / 2, w / 2, -d / 2, d / 2
    nunits = max(1, int(round(w / 10.5)))
    loggia = min(2.4, d * 0.18)
    yg = y1 - loggia                                        # recessed glass line
    z0 = PLINTH
    # plinth + floor
    mb.box(x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, 0, z0, M['concrete_grey'])
    mb.box(x0, x1, yg, y1, z0, z0 + 0.04, M['deck_grey'])
    mb.box(x0, x1, y0, yg, z0, z0 + 0.02, M['terrazzo'])
    top = z0
    for s in range(st):
        zb = top; zt = zb + FLOOR
        ux = np.linspace(x0, x1, nunits + 1)
        # side walls (full depth, framing the loggia)
        for xe in (x0 + WALL / 2, x1 - WALL / 2):
            ops = []
            if rng.random() < 0.7:
                ops.append(((y0 + yg) / 2, 1.3, zb + 1.0, zb + 2.4))
            mb.wall(y0, y1, xe, WALL, zb, zt, M['render_white'], ops, axis='y', glass=M['glass_dark'], frame=M['teak_dark'])
        # party walls between units, projecting as fins
        for k in range(1, nunits):
            mb.box(ux[k] - 0.15, ux[k] + 0.15, y0, y1 + 0.25, zb, zt, M['render_white'])
        for k in range(nunits):
            a, b = ux[k] + WALL, ux[k + 1] - WALL
            uw = b - a
            # seaward glazing: sliding doors
            npan = 3 if uw > 7 else 2
            gw = uw * 0.78
            ops = [((a + b) / 2 + (i - (npan - 1) / 2) * gw / npan, gw / npan - 0.02, zb + 0.02, zb + 2.75) for i in range(npan)]
            mb.wall(a, b, yg, 0.2, zb, zt, M['render_white'], ops, axis='x', glass=M['glass'], frame=M['teak_dark'], mullions=0)
            # back wall: door + high windows
            ops = [(a + uw * 0.3, 1.0, zb + 0.02, zb + 2.4), (a + uw * 0.72, 1.6, zb + 1.7, zb + 2.5)]
            mb.wall(a, b, y0 + WALL / 2, WALL, zb, zt, M['render_white'], ops if s == 0 else ops[1:] + [(a + uw * 0.3, 1.0, zb + 1.7, zb + 2.5)],
                    axis='x', glass=M['glass_dark'], frame=M['teak_dark'])
            if s == 0:
                mb.box(a + uw * 0.3 - 0.48, a + uw * 0.3 + 0.48, y0 - 0.02, y0 + 0.04, zb + 0.02, zb + 2.38, M['teak'])  # door leaf
                mb.box(a + uw * 0.3 + 0.6, a + uw * 0.3 + 0.75, y0 - 0.12, y0, zb + 2.0, zb + 2.25, M['lamp_warm'])
            # interior: a made bed seen through the glass, pendant, rug
            cx = (a + b) / 2
            bed(mb, cx, yg - 3.2, zb + 0.02)
            mb.box(cx - 1.6, cx + 1.6, yg - 4.8, yg - 1.2, zb + 0.02, zb + 0.03, M['fabric_cream'])
            pendant(mb, cx + 1.6, yg - 3.8, zt - 0.02, 0.9, 0.18)
            # loggia furniture
            if s == 0:
                lounger(mb, cx - 1.0, yg + 1.0, zb + 0.04, 90 + 180)
                potted_plant(mb, a + 0.5, y1 - 0.5, zb + 0.04, 0.28)
            else:
                chair_rattan(mb, cx - 0.6, yg + 0.8, zb, 180); chair_rattan(mb, cx + 0.6, yg + 0.8, zb, 180)
            # timber batten ceiling in the loggia
            for i in range(int(uw / 0.18)):
                xx = a + 0.1 + i * 0.18
                mb.box(xx, xx + 0.06, yg, y1, zt - 0.12, zt - 0.04, M['teak'])
        # slab above this storey
        mb.box(x0, x1, y0, y1, zt, zt + SLAB, M['render_white'])
        top = zt + SLAB
        if s < st - 1:
            # balcony balustrade (glass with teak handrail) on the upper floor
            mb.box(x0 + 0.3, x1 - 0.3, y1 - 0.12, y1 - 0.06, top, top + 1.0, M['glass'])
            mb.box(x0 + 0.3, x1 - 0.3, y1 - 0.15, y1 - 0.03, top + 1.0, top + 1.07, M['teak'])
    # parapet + dark roof membrane
    pz = top + PARAPET
    mb.box(x0, x1, y0, y0 + 0.3, top, pz, M['render_white'])
    mb.box(x0, x1, y1 - 0.3, y1, top, pz, M['render_white'])
    mb.box(x0, x0 + 0.3, y0, y1, top, pz, M['render_white'])
    mb.box(x1 - 0.3, x1, y0, y1, top, pz, M['render_white'])
    mb.box(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, top, top + 0.06, M['roof_dark'])
    # rooftop services
    for k in range(rng.randint(1, 3)):
        ax = rng.uniform(x0 + 1.2, x1 - 1.2); ay = rng.uniform(y0 + 1.2, y0 + d * 0.4)
        mb.cbox(ax, ay, top + 0.4, 0.9, 0.35, 0.65, M['concrete_grey'])
    if rng.random() < 0.5:
        mb.cyl(x0 + 1.5, y0 + 1.5, top + 0.06, top + 1.3, 0.55, M['concrete_grey'], n=14)
    for xs in (x0 + 1.0, x1 - 1.0):           # scupper spouts
        mb.box(xs - 0.08, xs + 0.08, y0 - 0.35, y0, top + 0.05, top + 0.15, M['concrete_grey'])
    # seaward terrace / private pool garden
    if v['pool']:
        pw = min(w * 0.72, 11.0); pd = 3.8
        px0, px1 = -pw / 2, pw / 2
        py0 = y1 + 2.2; py1 = py0 + pd
        mb.box(x0, x1, y1, py1 + 1.2, -0.05, z0, M['deck_grey'])
        pool_basin(mb, px0, px1, py0, py1, z0 - 0.15, 1.3, M['_pool_villa'], 0.3, M['concrete_grey'])
        # privacy walls enclosing the pool garden
        for xe in (x0, x1 - 0.22):
            mb.box(xe, xe + 0.22, y1, py1 + 1.2, 0, 1.9, M['render_white'])
        for i in range(2):
            lounger(mb, px0 + 1.6 + i * 1.0, y1 + 1.15, z0, -90)
        thatch_umbrella(mb, px1 - 1.0, y1 + 1.1, z0, 1.1, 2.3)
    else:
        mb.box(x0 + 0.5, x1 - 0.5, y1, y1 + 2.0, 0, z0 - 0.02, M['deck_grey'])
    return mb.build(coll)


# ============================================================ hip roof helper
def hip_roof(mb, cx, cy, W, D, z, pitch_deg, top_mat, under_mat, thick=0.15, fascia_mat=None):
    """Hip roof over a W x D (W >= D) rectangle centred at cx, cy with eaves at height z."""
    if D > W:
        raise ValueError('hip_roof expects W >= D')
    rise = D / 2 * math.tan(math.radians(pitch_deg))
    r0 = (cx - (W - D) / 2, cy, z + rise); r1 = (cx + (W - D) / 2, cy, z + rise)
    A = (cx - W / 2, cy - D / 2, z); B = (cx + W / 2, cy - D / 2, z)
    C = (cx + W / 2, cy + D / 2, z); Dd = (cx - W / 2, cy + D / 2, z)
    for off, m in ((0.0, top_mat), (-thick, under_mat)):
        o = lambda p: (p[0], p[1], p[2] + off)
        if off == 0:
            mb.quad(o(A), o(B), o(r1), o(r0), m); mb.quad(o(C), o(Dd), o(r0), o(r1), m)
            mb.add([o(B), o(C), o(r1)], [(0, 1, 2)], m); mb.add([o(Dd), o(A), o(r0)], [(0, 1, 2)], m)
        else:
            mb.quad(o(r0), o(r1), o(B), o(A), m); mb.quad(o(r1), o(r0), o(Dd), o(C), m)
            mb.add([o(r1), o(C), o(B)], [(0, 1, 2)], m); mb.add([o(r0), o(A), o(Dd)], [(0, 1, 2)], m)
    fm = fascia_mat or MATS['teak_dark']
    mb.box(A[0], B[0], A[1] - 0.04, A[1] + 0.04, z - 0.3, z, fm)
    mb.box(Dd[0], C[0], C[1] - 0.04, C[1] + 0.04, z - 0.3, z, fm)
    mb.box(A[0] - 0.04, A[0] + 0.04, A[1], Dd[1], z - 0.3, z, fm)
    mb.box(B[0] - 0.04, B[0] + 0.04, B[1], C[1], z - 0.3, z, fm)
    mb.box(r0[0], r1[0], cy - 0.12, cy + 0.12, z + rise - 0.05, z + rise + 0.08, fm)   # ridge cap


# ============================================================ Bayside restaurant & bar
def restaurant(spec, wing, coll, pad, rng):
    M = MATS
    W, D = spec['w'], spec['d']
    mb = MB('Bayside_Restaurant', (spec['c'][0], spec['c'][1], pad))
    fz = 0.45
    mb.box(-W / 2 - 0.4, W / 2 + 0.4, -D / 2 - 0.4, D / 2 + 4.2, 0, fz, M['terrazzo'])
    colh = 4.1
    nb = int(round(W / 4.1))
    xs = np.linspace(-W / 2 + 0.4, W / 2 - 0.4, nb + 1)
    for i, x in enumerate(xs):
        for y in (-D / 2 + 0.4, D / 2 - 0.4) + ((0.0,) if i % 2 == 0 else ()):
            m = M['blue_glazed'] if (i % 3 == 1 and y > 0) else M['concrete_grey']
            mb.cbox(x, y, fz + colh / 2, 0.48, 0.48, colh, m)
    zb = fz + colh
    # ring beams + thatch ceiling
    mb.box(-W / 2, W / 2, -D / 2, -D / 2 + 0.5, zb, zb + 0.55, M['concrete_grey'])
    mb.box(-W / 2, W / 2, D / 2 - 0.5, D / 2, zb, zb + 0.55, M['concrete_grey'])
    mb.box(-W / 2, -W / 2 + 0.5, -D / 2, D / 2, zb, zb + 0.55, M['concrete_grey'])
    mb.box(W / 2 - 0.5, W / 2, -D / 2, D / 2, zb, zb + 0.55, M['concrete_grey'])
    mb.box(-W / 2 + 0.5, W / 2 - 0.5, -D / 2 + 0.5, D / 2 - 0.5, zb + 0.05, zb + 0.1, M['thatch_ceiling'])
    for x in np.arange(-W / 2 + 1.0, W / 2 - 0.5, 1.4):  # exposed joists
        mb.box(x, x + 0.12, -D / 2 + 0.5, D / 2 - 0.5, zb - 0.12, zb + 0.05, M['teak_dark'])
    hip_roof(mb, 0, 0, W + 2.6, D + 2.6, zb + 0.55, 21, M['metal_dark_roof'], M['thatch_ceiling'])
    # reed-slat pergola over the beach-side colonnade
    py0, py1 = D / 2, D / 2 + 4.0
    pz = fz + 3.3
    for x in xs:
        mb.cbox(x, py1 - 0.25, fz + 1.65, 0.38, 0.38, 3.3, M['concrete_grey'])
    mb.box(-W / 2, W / 2, py1 - 0.45, py1 - 0.05, pz, pz + 0.3, M['concrete_grey'])
    for x in np.arange(-W / 2, W / 2, 0.14):
        mb.box(x, x + 0.05, py0 - 1.2, py1 + 0.3, pz + 0.3, pz + 0.34, M['reed'])
        if rng.random() < 0.6:   # ragged drooping reed ends
            mb.box(x, x + 0.04, py1 + 0.3, py1 + 0.34, pz + 0.05, pz + 0.34, M['reed'])
    for i in range(len(xs) - 1):
        daybed(mb, (xs[i] + xs[i + 1]) / 2, py0 + 1.9, fz, 0, 0.95, 2.0)
    # bar with amber terracotta geometric tile front and back-bar shelving
    bx0, bx1, by = -6.0, 6.0, -D / 2 + 2.6
    mb.box(bx0, bx1, by - 0.35, by + 0.35, fz, fz + 1.05, M['terracotta_tiles'])
    mb.box(bx0 - 0.1, bx1 + 0.1, by - 0.45, by + 0.45, fz + 1.05, fz + 1.12, M['teak'])
    mb.box(bx0, bx1, -D / 2 + 0.55, -D / 2 + 0.95, fz, fz + 3.2, M['teak_dark'])
    for row in range(3):
        mb.box(bx0, bx1, -D / 2 + 0.9, -D / 2 + 1.25, fz + 1.2 + row * 0.6, fz + 1.24 + row * 0.6, M['teak'])
        for k in range(30):
            bxp = bx0 + 0.25 + k * 0.38
            mb.cyl(bxp, -D / 2 + 1.07, fz + 1.24 + row * 0.6, fz + 1.55 + row * 0.6, 0.04,
                   rng.choice([M['glass_dark'], M['boat_yellow'], M['glass'], M['fabric_amber']]), n=8)
    for k in range(9):
        x = bx0 + 0.7 + k * 1.3
        mb.cyl(x, by + 0.75, fz, fz + 0.72, 0.03, M['teak_dark'], n=6)
        mb.cyl(x, by + 0.75, fz + 0.72, fz + 0.78, 0.2, M['rattan'], n=12)
    # dining: round teak tables with rattan chairs + pendants
    for x in np.arange(-W / 2 + 3, W / 2 - 2, 3.4):
        for y in (-1.2, 2.8):
            if abs(x) < 7 and y < 0:
                continue
            table_round(mb, x, y, fz)
            for a in range(4):
                ang = math.radians(a * 90 + 45)
                chair_rattan(mb, x + 0.8 * math.cos(ang), y + 0.8 * math.sin(ang), fz, math.degrees(ang) + 90)
            pendant(mb, x, y, zb, 1.5, 0.3)
    # lounge sofas near the front
    for x in np.arange(-W / 2 + 4, W / 2 - 3, 8.5):
        mb.box(x - 1.3, x + 1.3, D / 2 - 2.2, D / 2 - 1.4, fz, fz + 0.42, M['teak'])
        mb.box(x - 1.25, x + 1.25, D / 2 - 2.15, D / 2 - 1.45, fz + 0.42, fz + 0.6, M['fabric_cream'])
        mb.box(x - 1.3, x + 1.3, D / 2 - 1.5, D / 2 - 1.35, fz, fz + 0.85, M['teak'])
        table_round(mb, x, D / 2 - 3.1, fz, 0.4)
        for k in (-0.8, 0, 0.8):
            mb.cbox(x + k, D / 2 - 1.6, fz + 0.75, 0.5, 0.15, 0.4, M['fabric_white'])
    # potted palms between columns
    for x in xs[1:-1:2]:
        potted_plant(mb, x, -D / 2 + 1.3, fz, 0.35)
    # string lights along the pergola edge
    for x in np.arange(-W / 2, W / 2, 0.6):
        mb.sphere(x, py1 + 0.35, pz - 0.15 - 0.15 * math.sin((x % 4.1) / 4.1 * math.pi), 0.04, M['lamp_warm'], nu=6, nv=4)
    ob = mb.build(coll)

    # back-of-house wing: enclosed white block with a pale corrugated hip roof
    wb = MB('Bayside_Kitchen_Spa', (wing['c'][0], wing['c'][1], pad))
    Ww, Dw = wing['w'], wing['d']
    wb.box(-Ww / 2, Ww / 2, -Dw / 2, Dw / 2, 0, PLINTH, M['concrete_grey'])
    h = 3.6
    wb.wall(-Ww / 2, Ww / 2, -Dw / 2 + 0.12, WALL, PLINTH, h, M['render_white'],
            [(-Ww / 4, 1.2, PLINTH + 1.0, PLINTH + 2.2), (Ww / 4, 1.2, PLINTH + 1.0, PLINTH + 2.2), (0, 1.1, PLINTH, PLINTH + 2.3)],
            glass=M['glass_dark'], frame=M['teak_dark'])
    wb.wall(-Ww / 2, Ww / 2, Dw / 2 - 0.12, WALL, PLINTH, h, M['render_white'],
            [(x, 1.4, PLINTH + 0.9, PLINTH + 2.4) for x in np.linspace(-Ww / 2 + 2, Ww / 2 - 2, 5)],
            glass=M['glass_dark'], frame=M['teak_dark'])
    wb.wall(-Dw / 2, Dw / 2, -Ww / 2 + 0.12, WALL, PLINTH, h, M['render_white'], [(0, 1.2, PLINTH + 1.0, PLINTH + 2.2)], axis='y',
            glass=M['glass_dark'], frame=M['teak_dark'])
    wb.wall(-Dw / 2, Dw / 2, Ww / 2 - 0.12, WALL, PLINTH, h, M['render_white'], [], axis='y')
    wb.box(-Ww / 2, Ww / 2, -Dw / 2, Dw / 2, h, h + 0.25, M['render_white'])
    hip_roof(wb, 0, 0, Ww + 1.6, Dw + 1.6, h + 0.25, 18, M['metal_pale'], M['render_white'])
    for k in range(4):
        wb.cbox(-Ww / 2 + 2 + k * 2.2, -Dw / 2 - 0.5, 0.6, 0.9, 0.4, 0.7, M['concrete_grey'])   # AC units
    wb.build(coll)
    return ob


# ============================================================ entrance lobby (Sasak pyramid thatch)
def lobby(spec, coll, pad):
    M = MATS
    cx, cy = spec['c']
    r = spec['r']
    mb = MB('Lobby_Reception', (cx, cy, pad))
    mb.cyl(0, 0, 0, 0.3, r + 0.6, M['concrete_grey'], n=40)
    mb.cyl(0, 0, 0.3, 0.32, r + 0.3, M['terrazzo'], n=40)
    n = 48
    h = 3.0
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 1) / n
        am = math.atan2(math.sin((a0 + a1) / 2), math.cos((a0 + a1) / 2))
        if abs(am + math.pi / 2) < 0.85:
            continue   # open entrance towards the driveway (-y)
        if abs(am - math.pi / 2) < 0.5:
            continue   # opening to the resort
        p = [(r * math.cos(a0), r * math.sin(a0)), (r * math.cos(a1), r * math.sin(a1)),
             ((r - 0.3) * math.cos(a1), (r - 0.3) * math.sin(a1)), ((r - 0.3) * math.cos(a0), (r - 0.3) * math.sin(a0))]
        mb.prism(p, 0.3, h, M['render_white'])
    for a in (-math.pi / 2 - 0.85, -math.pi / 2 + 0.85, math.pi / 2 - 0.5, math.pi / 2 + 0.5):   # timber posts at openings
        mb.cyl((r - 0.15) * math.cos(a), (r - 0.15) * math.sin(a), 0.3, h + 0.2, 0.14, M['timber_post'], n=10)
    for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
        mb.cyl((r + 1.6) * math.cos(a + 0.2), (r + 1.6) * math.sin(a + 0.2), 0.3, h + 0.1, 0.11, M['timber_post'], n=8)
    # steep conical alang-alang roof with fringe and bamboo lattice
    R = r + 2.6
    ez = h + 0.2
    apex = ez + 6.2
    mb.cyl(0, 0, ez, apex, R, M['thatch'], 0.15, n=64, cap=False)
    mb.cyl(0, 0, ez - 0.25, ez, R + 0.05, M['thatch'], R, n=64, cap=False)
    mb.cyl(0, 0, ez - 0.25, ez - 0.24, R + 0.05, M['thatch_ceiling'], n=64)
    for fam in (1, -1):
        for k in range(28):
            a0 = 2 * math.pi * k / 28
            pts, rad = [], []
            for j in range(13):
                t = j / 12
                rr = R * (1 - t) + 0.15 * t + 0.04
                a = a0 + fam * t * 1.1
                pts.append((rr * math.cos(a), rr * math.sin(a), ez + (apex - ez) * t + 0.03))
                rad.append(0.014)
            mb.tube(pts, rad, M['bamboo'], n=4, cap=False)
    mb.cyl(0, 0, apex - 0.2, apex + 0.6, 0.18, M['thatch'], 0.05, n=12)
    mb.cyl(0, 0, apex + 0.5, apex + 2.2, 0.06, M['timber_post'], 0.01, n=8)   # finial spike
    # reception desk + stools
    mb.box(-1.6, 1.6, 1.0, 1.7, 0.32, 1.4, M['teak'])
    mb.box(-1.7, 1.7, 0.95, 1.75, 1.4, 1.46, M['teak_dark'])
    for x in (-1.0, 0, 1.0):
        mb.cyl(x, 0.5, 0.32, 1.0, 0.03, M['teak_dark'], n=6); mb.cyl(x, 0.5, 1.0, 1.06, 0.18, M['rattan'], n=10)
    pendant(mb, 0, 0.4, ez + 2.5, 1.8, 0.35)
    return mb.build(coll)


def gate_pavilion(c, coll, pad, rot=0):
    """Tall gabled thatch pavilion on timber posts with mural walls and white steps."""
    M = MATS
    mb = MB('Entrance_Pavilion', (c[0], c[1], pad), rot)
    W, D = 4.6, 6.0
    for k in range(4):
        mb.box(-W / 2 - 0.9 + k * 0.3, W / 2 + 0.9 - k * 0.3, -D / 2 - 1.4 + k * 0.35, -D / 2 - 1.05 + k * 0.35, 0, 0.15 * (k + 1), M['render_white'])
    mb.box(-W / 2, W / 2, -D / 2, D / 2, 0, 0.6, M['render_white'])
    for sx in (-1, 1):
        mb.box(sx * W / 2 - 0.2, sx * W / 2 + 0.2, -D / 2 + 0.5, D / 2 - 0.5, 0.6, 2.6, M['mural'])
        for sy in (-1, 1):
            mb.cyl(sx * (W / 2 - 0.1), sy * (D / 2 - 0.2), 0.6, 3.4, 0.13, M['timber_post'], n=10)
    hz = 3.4; rz = hz + 3.4; ov = 1.4
    for sx in (-1, 1):
        a = (sx * (W / 2 + ov), -D / 2 - ov, hz - 0.6); b = (0, -D / 2 - ov, rz)
        c2 = (0, D / 2 + ov, rz); d = (sx * (W / 2 + ov), D / 2 + ov, hz - 0.6)
        for off in (0.0, 0.35):
            o = lambda p: (p[0] - sx * off * 0.6, p[1], p[2] - off)
            mb.quad(o(a), o(b), o(c2), o(d), M['thatch'] if off == 0 else M['thatch_ceiling'])
        mb.quad((a[0], a[1], a[2] - 0.35), a, d, (d[0], d[1], d[2] - 0.35), M['thatch'])
    mb.box(-0.15, 0.15, -D / 2 - ov, D / 2 + ov, rz - 0.1, rz + 0.15, M['thatch'])
    return mb.build(coll)


def yoga_shala(spec, coll, pad):
    M = MATS
    mb = MB('Yoga_Shala', (spec['c'][0], spec['c'][1], pad))
    W, D = spec['w'], spec['d']
    mb.box(-W / 2, W / 2, -D / 2, D / 2, 0, 0.6, M['concrete_grey'])
    mb.box(-W / 2 + 0.1, W / 2 - 0.1, -D / 2 + 0.1, D / 2 - 0.1, 0.6, 0.62, M['terrazzo'])
    for sx in (-1, 1):
        for y in np.linspace(-D / 2 + 0.3, D / 2 - 0.3, 4):
            mb.cyl(sx * (W / 2 - 0.3), y, 0.62, 3.3, 0.12, M['timber_post'], n=10)
    hz = 3.3; rz = hz + W * 0.55; ov = 1.2
    for sx in (-1, 1):
        a = (sx * (W / 2 + ov), -D / 2 - ov * 0.6, hz - 0.5); b = (0, -D / 2 - ov * 0.6, rz)
        c2 = (0, D / 2 + ov * 0.6, rz); d = (sx * (W / 2 + ov), D / 2 + ov * 0.6, hz - 0.5)
        mb.quad(a, b, c2, d, M['thatch'])
        mb.quad((a[0], a[1], a[2] - 0.3), (b[0], b[1], b[2] - 0.3), (c2[0], c2[1], c2[2] - 0.3), (d[0], d[1], d[2] - 0.3), M['thatch_ceiling'])
        mb.quad((a[0], a[1], a[2] - 0.3), a, d, (d[0], d[1], d[2] - 0.3), M['thatch'])
    for k in range(6):   # yoga mats
        mb.box(-W / 2 + 1.2 + (k % 2) * 3.0, -W / 2 + 2.0 + (k % 2) * 3.0, -D / 2 + 1.5 + (k // 2) * 3.5,
               -D / 2 + 3.3 + (k // 2) * 3.5, 0.62, 0.635, M['fabric_teal'])
    return mb.build(coll)


def pergola(spec, coll, pad):
    M = MATS
    mb = MB('Garden_Pergola', (spec['c'][0], spec['c'][1], pad))
    W, D = spec['w'], spec['d']
    for x in np.arange(-W / 2, W / 2 + 0.1, 3.0):
        for y in (-D / 2, D / 2):
            mb.cbox(x, y, 1.35, 0.15, 0.15, 2.7, M['timber_post'])
    for y in (-D / 2, D / 2):
        mb.box(-W / 2, W / 2, y - 0.08, y + 0.08, 2.7, 2.95, M['teak'])
    for x in np.arange(-W / 2, W / 2, 0.45):
        mb.box(x, x + 0.06, -D / 2 - 0.4, D / 2 + 0.4, 2.95, 3.1, M['teak'])
    return mb.build(coll)


# ============================================================ main pool deck
def main_pool(P, SH, coll, pad, rng):
    M = MATS
    mb = MB('Main_Pool', (0, 0, pad))
    wz = -0.12
    x0, x1, y0, y1 = P['x0'], P['x1'], P['y0'], P['y1']
    tiles = M['_pool_main']
    # deck platforms
    mb.box(x1 + 0.35, x1 + 3.6, y0 - 4.0, y1, -0.3, 0.0, M['deck_grey'])            # bean-bag side
    mb.box(x0 - 7.5, x0 - 0.35, SH['y1'] + 0.35, y1, -0.3, 0.0, M['deck_grey'])      # cabana side
    mb.box(x0 - 7.5, x1 + 3.6, y0 - 4.2, y0 - 2.8, -0.3, 0.0, M['deck_grey'])        # inland end
    pool_basin(mb, x0, x1, y0, y1, wz, 1.5, tiles, 0.35, M['concrete_grey'], infinity_edge='y1')
    # stepped shallow sun-shelf, offset to the inland west corner (photos)
    sx0, sx1, sy0, sy1 = SH['x0'], SH['x1'], SH['y0'], SH['y1']
    pool_basin(mb, sx0, x0 + 0.01, sy0, sy1, wz, 0.45, tiles, 0.35, M['concrete_grey'])
    for k in range(3):
        mb.box(sx0 + 0.6 + k * 1.5, sx0 + 1.6 + k * 1.5, sy0 + 0.4, sy1 - 0.4, wz - 0.45, wz - 0.22, tiles)
    for k in range(3):   # entry steps in the main basin
        mb.box(x0, x0 + 1.2 - k * 0.35, y0, y0 + 2.5, wz - 1.5, wz - 0.3 - k * 0.38, tiles)
    # bean bags with closed white parasols on the east deck
    for i in range(12):
        y = y0 - 1.5 + i * 1.95
        bean_bag(mb, x1 + 1.8, y, 0.0)
        if i % 2 == 0:
            parasol_closed(mb, x1 + 2.9, y + 0.95, 0.0)
    # cabanas (daybeds with white canopies) on the west deck
    for i, y in enumerate((SH['y1'] + 2.2, SH['y1'] + 5.4, SH['y1'] + 8.6)):
        cabana(mb, x0 - 3.6, y, 0.0, 0)
    thatch_umbrella(mb, (x0 + x1) / 2 - 1.0, y0 - 3.5, 0.0, 1.6)
    lounger(mb, (x0 + x1) / 2 - 2.6, y0 - 3.5, 0.0, 0); lounger(mb, (x0 + x1) / 2 + 0.6, y0 - 3.5, 0.0, 0)
    # stepping-stone pads in raked sand towards the restaurant
    for k in range(14):
        a = rng.uniform(-0.25, 0.25)
        mb.cyl(x0 - 8.5 - k * 0.15 + a, y0 - 1.0 + k * 1.1, -0.06, 0.02, rng.uniform(0.32, 0.42), M['stone_dark'], n=14)
    return mb.build(coll)


# ============================================================ walls, fences, paths
def boundary(points, coll, ground, beach_y, rng):
    M = MATS
    mb = MB('Compound_Walls')
    n = len(points)
    for i in range(n):
        (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        if L < 0.5:
            continue
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        beach_side = abs(ay - beach_y) < 1 and abs(by - beach_y) < 1
        segs = max(1, int(L / 2.5))
        for k in range(segs):
            t0, t1 = k / segs, (k + 1) / segs
            x0, y0 = ax + (bx - ax) * t0, ay + (by - ay) * t0
            x1, y1 = ax + (bx - ax) * t1, ay + (by - ay) * t1
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            gz = ground(cx, cy)
            ln = L / segs
            if beach_side:
                if (k % 9) in (4,):      # gaps where the paths reach the beach
                    continue
                mb.cbox(cx, cy, gz + 0.3, ln + 0.02, 0.5, 0.6, M['stone_dark'], ang)    # low stone berm wall
                for j in range(int(ln / 0.07)):                                        # woven bamboo fence
                    tx = x0 + (x1 - x0) * j / (ln / 0.07); ty = y0 + (y1 - y0) * j / (ln / 0.07)
                    mb.cyl(tx, ty, gz + 0.55, gz + 1.45 + 0.08 * math.sin(j * 1.7), 0.03, M['bamboo'], n=5)
                for hz in (0.85, 1.25):
                    mb.cbox(cx, cy, gz + hz, ln, 0.05, 0.05, M['bamboo'], ang)
            else:
                mb.cbox(cx, cy, gz + 1.0, ln + 0.05, 0.25, 2.3, M['render_white'], ang)
                mb.cbox(cx, cy, gz + 2.18, ln + 0.05, 0.35, 0.08, M['concrete_grey'], ang)
    return mb.build(coll)


def stepping_path(mb, pts, ground, rng, spacing=0.8):
    M = MATS
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        L = math.hypot(bx - ax, by - ay)
        for k in range(int(L / spacing)):
            t = k / max(1, L / spacing)
            x = ax + (bx - ax) * t + rng.uniform(-0.15, 0.15); y = ay + (by - ay) * t + rng.uniform(-0.15, 0.15)
            z = ground(x, y)
            mb.cyl(x, y, z - 0.05, z + 0.035, rng.uniform(0.3, 0.4), M['stone_dark'], n=12)
