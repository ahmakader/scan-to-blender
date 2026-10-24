"""Procedural tropical vegetation + Geometry-Nodes scattering."""
import math, random
import bpy
import numpy as np
from lib_mesh import MB
from lib_mat import MATS

UP = np.array([0, 0, 1.0])


def _n(v):
    return v / (np.linalg.norm(v) + 1e-9)


def asset_collection(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


# ============================================================ geometry-nodes scatter
def scatter(target, instance, density, attr=None, scale=(0.8, 1.2), seed=0, align=False, join=True,
            tilt=0.0, name=None, z_offset=0.0, poisson=None, collection_pick=True):
    """Scatter `instance` (collection or object) over `target` faces.
    density: instances per m^2 (multiplied by float point attribute `attr` if given)."""
    ng = bpy.data.node_groups.new(name or f'scatter_{target.name}', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, Lk = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    if poisson:
        dist.distribute_method = 'POISSON'
        dist.inputs['Distance Min'].default_value = poisson
        dist.inputs['Density Max'].default_value = density
    else:
        dist.inputs['Density'].default_value = density
    dist.inputs['Seed'].default_value = seed
    Lk.new(gi.outputs[0], dist.inputs['Mesh'])
    if attr:
        na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'
        na.inputs['Name'].default_value = attr
        if poisson:
            Lk.new(na.outputs['Attribute'], dist.inputs['Density Factor'])
        else:
            mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = density
            Lk.new(na.outputs['Attribute'], mul.inputs[0]); Lk.new(mul.outputs[0], dist.inputs['Density'])
    iop = N.new('GeometryNodeInstanceOnPoints')
    Lk.new(dist.outputs['Points'], iop.inputs['Points'])
    if isinstance(instance, bpy.types.Collection):
        ci = N.new('GeometryNodeCollectionInfo'); ci.transform_space = 'ORIGINAL'
        ci.inputs['Collection'].default_value = instance
        ci.inputs['Separate Children'].default_value = collection_pick
        ci.inputs['Reset Children'].default_value = True
        Lk.new(ci.outputs[0], iop.inputs['Instance'])
        iop.inputs['Pick Instance'].default_value = collection_pick
        if collection_pick:
            ri = N.new('FunctionNodeRandomValue'); ri.data_type = 'INT'
            ri.inputs['Seed'].default_value = seed + 11
            ri.inputs[4].default_value = 0; ri.inputs[5].default_value = 1000
            Lk.new(ri.outputs[2], iop.inputs['Instance Index'])
    else:
        oi = N.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = instance
        oi.inputs['As Instance'].default_value = True
        Lk.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
    rs.inputs[2].default_value = scale[0]; rs.inputs[3].default_value = scale[1]
    rs.inputs['Seed'].default_value = seed + 3
    Lk.new(rs.outputs[1], iop.inputs['Scale'])
    if align:
        Lk.new(dist.outputs['Rotation'], iop.inputs['Rotation'])
    rr = N.new('FunctionNodeRandomValue'); rr.data_type = 'FLOAT_VECTOR'
    rr.inputs[0].default_value = (-tilt, -tilt, 0); rr.inputs[1].default_value = (tilt, tilt, 2 * math.pi)
    rr.inputs['Seed'].default_value = seed + 5
    rot = N.new('GeometryNodeRotateInstances')
    Lk.new(iop.outputs[0], rot.inputs['Instances'])
    Lk.new(rr.outputs[0], rot.inputs['Rotation'])
    rot.inputs['Local Space'].default_value = True
    last = rot.outputs[0]
    if z_offset:
        tr = N.new('GeometryNodeTranslateInstances')
        tr.inputs['Translation'].default_value = (0, 0, z_offset)
        Lk.new(last, tr.inputs['Instances']); last = tr.outputs[0]
    if join:
        j = N.new('GeometryNodeJoinGeometry')
        Lk.new(last, j.inputs[0]); Lk.new(gi.outputs[0], j.inputs[0])
        last = j.outputs[0]
    Lk.new(last, go.inputs[0])
    md = target.modifiers.new(ng.name, 'NODES')
    md.node_group = ng
    return md


def set_point_attr(obj, name, values):
    a = obj.data.attributes.get(name) or obj.data.attributes.new(name, 'FLOAT', 'POINT')
    a.data.foreach_set('value', np.asarray(values, np.float32))


# ============================================================ small leaf / blade meshes
def leaf_mesh(name, coll, length, width, mat, fold=0.25, curve=0.15, n=6, shape='oval'):
    mb = MB(name)
    vs, fs = [], []
    for i in range(n + 1):
        t = i / n
        if shape == 'oval':
            w = width * math.sin(math.pi * min(1, t * 1.05)) ** 0.8
        elif shape == 'heart':
            w = width * (math.sin(math.pi * t) ** 0.6) * (1.25 - t * 0.5)
        else:  # lanceolate
            w = width * math.sin(math.pi * t) ** 1.2
        y = t * length
        z = -curve * length * t * t
        vs += [(-w / 2, y, z + fold * w), (0, y, z), (w / 2, y, z + fold * w)]
    for i in range(n):
        a = i * 3
        fs += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    mb.add(vs, fs, mat)
    ob = mb.build(coll)
    ob.data.shade_smooth()
    return ob


def grass_clump(name, coll, mat, blades=14, h=0.12, spread=0.06, w=0.006, seed=0, lean=0.5):
    r = random.Random(seed)
    mb = MB(name)
    for b in range(blades):
        a = r.uniform(0, 2 * math.pi); hh = h * r.uniform(0.6, 1.2)
        x0, y0 = r.uniform(-spread, spread), r.uniform(-spread, spread)
        dx, dy = math.cos(a), math.sin(a)
        bend = r.uniform(0.2, 1.0) * lean
        vs = []
        segs = 4
        for i in range(segs + 1):
            t = i / segs
            ww = w * (1 - t) + 0.0005
            px = x0 + dx * bend * hh * t * t; py = y0 + dy * bend * hh * t * t
            pz = hh * (t - 0.35 * bend * t * t)
            vs += [(px - dy * ww, py + dx * ww, pz), (px + dy * ww, py - dx * ww, pz)]
        fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(segs)]
        mb.add(vs, fs, mat)
    return mb.build(coll)


# ============================================================ coconut palm
def coconut_palm(name, coll, height=11.0, lean=(0.8, 0.2), seed=0, fronds=18, frond_len=4.8):
    r = random.Random(seed)
    mb = MB(name)
    M = MATS
    # trunk: gently curved, flared base, ringed
    pts, rad = [], []
    n = 34
    lx, ly = lean
    for i in range(n + 1):
        t = i / n
        z = height * t
        # palms lean then curve back up toward the light
        off = (t * 1.6 - t * t * 0.7)
        pts.append((lx * off, ly * off, z))
        rr = 0.15 + 0.06 * (1 - t) ** 2 + 0.12 * max(0, 0.08 - t) / 0.08
        rr *= 1 + 0.03 * math.sin(i * 2.7)
        rad.append(rr)
    mb.tube(pts, rad, M['bark_palm'], n=12)
    top = np.array(pts[-1])
    # frond boots + crown shaft
    mb.cyl(top[0], top[1], top[2] - 0.6, top[2] + 0.25, 0.2, M['leaf_palm_dry'], 0.26, n=10)
    # coconuts
    for k in range(r.randint(5, 11)):
        a = r.uniform(0, 2 * math.pi); rr = r.uniform(0.18, 0.3)
        mb.sphere(top[0] + rr * math.cos(a), top[1] + rr * math.sin(a), top[2] - r.uniform(0.25, 0.55), 0.12,
                  M['coconut'], 1, 1, 1.1, 8, 6)
    # fronds
    for f in range(fronds):
        az = 2 * math.pi * f / fronds + r.uniform(-0.15, 0.15)
        age = f / fronds                    # 0 = young (upright), 1 = old (drooping)
        dead = age > 0.93 and r.random() < 0.7
        el = math.radians(r.uniform(55, 70) - 85 * age ** 1.2)
        L = frond_len * r.uniform(0.85, 1.1) * (0.7 + 0.3 * min(1, age * 3))
        d = _n(np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]))
        p = top + d * 0.15 + np.array([0, 0, 0.1])
        g = 0.12 + 0.25 * age
        spine = [p.copy()]
        dirs = [d.copy()]
        segs = 22
        for s in range(segs):
            d = _n(d + np.array([0, 0, -g]) / segs * 2.2)
            p = p + d * L / segs
            spine.append(p.copy()); dirs.append(d.copy())
        mat = M['leaf_palm_dry'] if dead else M['leaf_palm']
        # rachis
        mb.tube(spine, [0.035 * (1 - i / segs) + 0.008 for i in range(segs + 1)], mat, n=5, cap=False)
        # leaflets
        pairs = 58
        for k in range(pairs):
            s = 0.06 + 0.92 * k / pairs
            idx = s * segs; i0 = int(idx); fr = idx - i0
            i1 = min(i0 + 1, segs)
            sp = spine[i0] * (1 - fr) + spine[i1] * fr
            sd = _n(dirs[i0] * (1 - fr) + dirs[i1] * fr)
            side = _n(np.cross(sd, UP))
            ll = (0.25 + 0.95 * math.sin(math.pi * (0.08 + s * 0.85)) ** 0.7) * L / 4.8
            for sg in (-1, 1):
                ld = _n(side * sg * 0.85 + sd * 0.55 - UP * (0.25 + 0.35 * s))
                ld = _n(ld + np.array([r.uniform(-.08, .08), r.uniform(-.08, .08), r.uniform(-.1, .05)]))
                wv = _n(np.cross(ld, sd)) * 0.042
                vs = []
                q = sp.copy(); dd = ld.copy()
                ns = 4
                for j in range(ns + 1):
                    tj = j / ns
                    wk = (math.sin(math.pi * min(1, 0.15 + tj * 0.9)) * 0.9 + 0.1) * (1 - tj * 0.6)
                    vs += [tuple(q - wv * wk), tuple(q + wv * wk)]
                    dd = _n(dd - UP * 0.18)
                    q = q + dd * ll / ns
                fs = [(2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2) for j in range(ns)]
                mb.add(vs, fs, mat)
    ob = mb.build(coll)
    return ob


# ============================================================ broadleaf trees with leaf-card canopies
def broadleaf_tree(name, coll, leaf_coll, height=11.0, spread=7.0, tiers=4, seed=0, trunk_r=0.35,
                   leaf_density=55.0, pad_r=(1.6, 2.4), pad_flat=0.5, bark='bark_grey', layered=True):
    r = random.Random(seed)
    mb = MB(name + '_wood')
    pads = MB(name + '_canopy')
    M = MATS
    tb = [(0, 0, 0), (r.uniform(-.2, .2), r.uniform(-.2, .2), height * 0.35), (r.uniform(-.3, .3), r.uniform(-.3, .3), height * 0.75)]
    mb.tube(tb, [trunk_r * 1.3, trunk_r * 0.85, trunk_r * 0.5], M[bark], n=12)
    for ti in range(tiers):
        h = height * (0.4 + 0.55 * ti / max(1, tiers - 1))
        nb = r.randint(4, 6)
        reach = spread * (1.0 - 0.55 * ti / max(1, tiers - 1)) * r.uniform(0.85, 1.1)
        for b in range(nb):
            a = 2 * math.pi * b / nb + r.uniform(-0.3, 0.3) + ti
            dx, dy = math.cos(a), math.sin(a)
            rise = 0.15 if layered else 0.45
            p0 = np.array([tb[1][0], tb[1][1], h])
            p1 = p0 + np.array([dx * reach * 0.5, dy * reach * 0.5, reach * rise * 0.6])
            p2 = p0 + np.array([dx * reach, dy * reach, reach * rise + r.uniform(-.3, .5)])
            br = trunk_r * 0.45 * (1 - 0.4 * ti / tiers)
            mb.tube([p0, p1, p2], [br, br * 0.6, br * 0.25], M[bark], n=7)
            for k in range(r.randint(5, 8)):
                t = r.uniform(0.4, 1.05)
                c = p0 * (1 - t) + p2 * t
                pr = r.uniform(*pad_r)
                pads.sphere(c[0] + r.uniform(-1.2, 1.2), c[1] + r.uniform(-1.2, 1.2), c[2] + r.uniform(-0.3, 0.9), pr,
                            M['leaf_broad'], r.uniform(0.9, 1.3), r.uniform(0.9, 1.3), pad_flat, 10, 6)
    top = np.array(tb[-1])
    pads.sphere(top[0], top[1], top[2] + 0.6, pad_r[1] * 1.1, M['leaf_broad'], 1.2, 1.2, pad_flat * 1.1, 10, 6)
    wood = mb.build(coll)
    can = pads.build(coll)
    if leaf_coll is not None:
        scatter(can, leaf_coll, leaf_density, scale=(0.9, 1.6), seed=seed, align=True, join=False, tilt=1.3,
                name=f'leaves_{name}')
    return wood, can


def frangipani(name, coll, seed=0, height=3.5):
    r = random.Random(seed)
    mb = MB(name)
    M = MATS

    def branch(p, d, length, rad, depth):
        q = p + d * length
        mid = (p + q) / 2 + np.array([0, 0, length * 0.08])
        mb.tube([p, mid, q], [rad, rad * 0.9, rad * 0.8], M['bark_grey'], n=7)
        if depth == 0:
            for k in range(7):  # leaf rosette
                a = 2 * math.pi * k / 7 + r.uniform(-.2, .2)
                ld = _n(np.array([math.cos(a), math.sin(a), r.uniform(0.6, 1.3)]))
                side = _n(np.cross(ld, UP)) * 0.05
                L = r.uniform(0.26, 0.36)
                vs = []
                for j in range(5):
                    t = j / 4; w = math.sin(math.pi * t) ** 0.9
                    c = q + ld * L * t - UP * 0.08 * t * t
                    vs += [tuple(c - side * w), tuple(c + side * w)]
                mb.add(vs, [(2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2) for j in range(4)], M['leaf_frangipani'])
            for k in range(r.randint(1, 3)):  # flower clusters
                c = q + np.array([r.uniform(-.06, .06), r.uniform(-.06, .06), 0.08])
                for pi_ in range(5):
                    a = 2 * math.pi * pi_ / 5
                    tip = c + np.array([math.cos(a) * 0.05, math.sin(a) * 0.05, 0.015])
                    sd = np.array([-math.sin(a), math.cos(a), 0]) * 0.02
                    mb.add([tuple(c), tuple(tip - sd + (tip - c) * 0.3), tuple(tip + (tip - c) * 0.5), tuple(tip + sd)],
                           [(0, 1, 2, 3)], M['flower_white'])
            return
        for k in range(r.choice((2, 3))):
            a = r.uniform(0, 2 * math.pi)
            nd = _n(d * 0.6 + np.array([math.cos(a), math.sin(a), 0.5]) * 0.6)
            branch(q, nd, length * r.uniform(0.6, 0.8), rad * 0.72, depth - 1)

    branch(np.zeros(3), np.array([0, 0, 1.0]), height * 0.35, 0.09, 4)
    return mb.build(coll)


def banana(name, coll, seed=0, height=2.6):
    r = random.Random(seed)
    mb = MB(name)
    M = MATS
    mb.tube([(0, 0, 0), (0.05, 0, height * 0.5), (0.08, 0.02, height)], [0.14, 0.11, 0.08], M['leaf_banana'], n=10)
    for k in range(8):
        a = 2 * math.pi * k / 8 + r.uniform(-.3, .3)
        el = math.radians(r.uniform(20, 70))
        d = _n(np.array([math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)]))
        side = _n(np.cross(d, UP))
        p = np.array([0.08, 0.02, height * r.uniform(0.85, 1.0)])
        L = r.uniform(1.4, 2.1); W = r.uniform(0.28, 0.4)
        vs = []
        n = 10
        q = p.copy(); dd = d.copy()
        for j in range(n + 1):
            t = j / n
            w = W * math.sin(math.pi * min(1, 0.08 + t)) ** 0.5
            vs += [tuple(q - side * w + UP * 0.05 * w), tuple(q), tuple(q + side * w + UP * 0.05 * w)]
            dd = _n(dd - UP * 0.12)
            q = q + dd * L / n
        fs = []
        for j in range(n):
            a0 = j * 3
            fs += [(a0, a0 + 3, a0 + 4, a0 + 1), (a0 + 1, a0 + 4, a0 + 5, a0 + 2)]
        mb.add(vs, fs, M['leaf_banana'])
    return mb.build(coll)


def shrub(name, coll, leaf_coll, seed=0, size=1.2, density=220.0, height=1.0):
    r = random.Random(seed)
    pads = MB(name)
    for k in range(r.randint(3, 6)):
        rr = size * r.uniform(0.4, 0.7)
        pads.sphere(r.uniform(-size * .5, size * .5), r.uniform(-size * .5, size * .5), height * r.uniform(0.4, 0.8), rr,
                    MATS['leaf_shrub'], 1, 1, 0.8, 10, 6)
    ob = pads.build(coll)
    scatter(ob, leaf_coll, density, scale=(0.8, 1.5), seed=seed, align=True, join=False, tilt=1.4, name=f'leaves_{name}')
    return ob


def low_poly_tree(name, coll, seed=0, h=7.0, r=3.0):
    """Cheap distant tree for the hills."""
    rnd = random.Random(seed)
    mb = MB(name)
    mb.tube([(0, 0, 0), (0, 0, h * 0.5)], [0.22, 0.15], MATS['bark_grey'], n=6)
    for k in range(rnd.randint(7, 11)):
        rr = r * rnd.uniform(0.3, 0.5)
        mb.sphere(rnd.uniform(-r * .55, r * .55), rnd.uniform(-r * .55, r * .55), h * rnd.uniform(0.5, 0.92), rr,
                  MATS['hill_tree'], 1, 1, 0.8, 8, 6)
    ob = mb.build(coll)
    ob.data.shade_smooth()
    return ob


def bamboo_clump(name, coll, leaf_coll, seed=0, h=5.5):
    r = random.Random(seed)
    mb = MB(name + '_culms')
    pads = MB(name + '_leaves')
    for k in range(r.randint(9, 15)):
        x, y = r.uniform(-.5, .5), r.uniform(-.5, .5)
        hh = h * r.uniform(0.75, 1.1)
        lx, ly = x * 0.5, y * 0.5
        mb.tube([(x, y, 0), (x + lx * 0.4, y + ly * 0.4, hh * 0.5), (x + lx, y + ly, hh)], [0.035, 0.03, 0.02], MATS['bamboo'], n=6)
        pads.sphere(x + lx, y + ly, hh * 0.8, 0.7, MATS['leaf_bamboo'], 0.8, 0.8, 1.4, 8, 5)
    c = mb.build(coll)
    p = pads.build(coll)
    scatter(p, leaf_coll, 160, scale=(0.8, 1.2), seed=seed, align=True, join=False, tilt=1.2, name=f'leaves_{name}')
    return c, p
