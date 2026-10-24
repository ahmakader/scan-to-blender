"""Generic scene assembly: levelled scan terrain + layout-driven buildings + vegetation + water + sky + cameras.

blender -b --factory-startup -P build/build.py
Expects build/data/ from scripts/level_and_dsm.py dsm (ground.npy, local_ortho.png, trees.npy) and frame.json.
Grow this file per project: add building types, materials, props. Keep it re-runnable end to end.
"""
import bpy, json, math, os, random, sys
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
for mod in ('layout', 'lib_mesh', 'lib_mat', 'lib_veg', 'lib_arch', 'viewport_light'):
    sys.modules.pop(mod, None)
import layout as L
import lib_mat
from lib_mesh import MB, grid_mesh
import lib_veg as V
import lib_arch as A

D = os.path.join(HERE, 'data')
CFG = json.load(open(os.path.join(D, 'dsm_config.json')))   # {"extent": [u0,u1,v0,v1], "res": 0.3, "scan": "...glb"}
rng = random.Random(1)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
M = lib_mat.build_all()
M['_pool_main'] = M['_pool_tiles']('pool_tiles_main', -10, 10)
M['_pool_villa'] = M['_pool_tiles']('pool_tiles_villa', -2, 18)


def coll(name, parent=None):
    c = bpy.data.collections.new(name); (parent or scene.collection).children.link(c); return c


C_TER = coll('Terrain'); C_WAT = coll('Water'); C_SITE = coll(L.PROJECT.replace(' ', '_'))
C_BLD = coll('Buildings', C_SITE); C_COM = coll('Common_Areas', C_SITE); C_LAND = coll('Landscape', C_SITE)
C_VEG = coll('Vegetation'); C_PROPS = coll('Props'); C_FAR = coll('Distant_Landscape')
C_CAM = coll('Cameras_Lights'); C_ASSETS = coll('ASSETS'); C_SCAN = coll('Scan_Reference')

# ------------------------------------------------------------------ terrain from the levelled scan
G = np.load(os.path.join(D, 'ground.npy')).astype(np.float64)
u0, u1, v0, v1 = CFG['extent']; r = CFG['res']
nv, nu = G.shape
X0, X1, Y0, Y1 = u0 + r / 2, u0 + r / 2 + (nu - 1) * r, v1 - r / 2 - (nv - 1) * r, v1 - r / 2


def ground(x, y):
    fx = min(max((x - X0) / r, 0), nu - 1.001); fy = min(max((Y1 - y) / r, 0), nv - 1.001)
    i, j = int(fy), int(fx); ty, tx = fy - i, fx - j
    return (G[i, j] * (1 - tx) * (1 - ty) + G[i, j + 1] * tx * (1 - ty) + G[i + 1, j] * (1 - tx) * ty + G[i + 1, j + 1] * tx * ty)


# flatten building pads to L.PAD inside the boundary (scan ground is noisy under roofs)
xs = np.linspace(X0, X1, nu); ys = np.linspace(Y1, Y0, nv); XX, YY = np.meshgrid(xs, ys)


def inside_poly(px, py, poly):
    ins = np.zeros(np.shape(px), bool)
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        ins ^= ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1)
    return ins


site = inside_poly(XX, YY, L.BOUNDARY)
def blur(a, k=13):       # numpy-only box blur (Blender's Python has numpy but not scipy)
    ker = np.ones(k) / k
    a = np.apply_along_axis(lambda m: np.convolve(m, ker, 'same'), 0, a)
    return np.apply_along_axis(lambda m: np.convolve(m, ker, 'same'), 1, a)


soft = blur(site.astype(float))
G = soft * L.PAD + (1 - soft) * G
keep = np.ones((nv - 1, nu - 1), bool)
cx_, cy_ = (XX[:-1, :-1] + XX[1:, 1:]) / 2, (YY[:-1, :-1] + YY[1:, 1:]) / 2
for p in L.POOLS:
    keep &= ~((cx_ > p['x0'] - .3) & (cx_ < p['x1'] + .3) & (cy_ > p['y0'] - .3) & (cy_ < p['y1'] + .3))


# Starting point only: drapes the scan orthophoto. Replace inside the site with procedural masks
# (lawn / sand / paving / dry grass) as described in SKILL.md Phase 4 (compose.py), or roofs stay painted on the ground.
def terrain_material():
    m, t = lib_mat.new('terrain_scan')
    uv = t.node('ShaderNodeTexCoord')
    img = t.node('ShaderNodeTexImage', interpolation='Cubic')
    img.image = bpy.data.images.load(os.path.join(D, 'local_ortho.png'))
    t.link(uv.outputs['UV'], img.inputs['Vector'])
    geo = t.node('ShaderNodeNewGeometry')
    n = t.noise(geo.outputs['Position'], 0.8, 5)
    var = t.ramp(n.outputs['Fac'], [(0.0, (0.8, 0.8, 0.8)), (1.0, (1.1, 1.1, 1.05))])
    col = t.mix(1.0, img.outputs['Color'], var, 'MULTIPLY')
    t.output(t.principled(col, 0.85, t.bump(t.noise(geo.outputs['Position'], 6, 4).outputs['Fac'], 0.3, 0.05)))
    return m


T = grid_mesh('Terrain_Site', G, X0, X1, Y0, Y1, C_TER, terrain_material(), keep=keep)

# ------------------------------------------------------------------ water
if L.WATER_LEVEL is not None:
    m, t = lib_mat.new('water')
    t.output(lib_mat.shadow_clear(t, t.principled((0.8, 0.95, 0.94), 0.03, Transmission_Weight=1.0, IOR=1.333)))
    bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, L.WATER_LEVEL))
    w = bpy.context.object; w.name = 'Water_Surface'
    for c in w.users_collection: c.objects.unlink(w)
    C_WAT.objects.link(w); w.data.materials.append(m)

# ------------------------------------------------------------------ buildings from layout
for b in L.BUILDINGS:
    if b['type'] == 'block':
        A.villa(dict(b, c=b['c']), C_BLD, L.PAD, rng)
    elif b['type'] == 'pavilion_hip':
        A.restaurant(dict(c=b['c'], w=b['w'], d=b['d']), dict(c=(b['c'][0], b['c'][1] - b['d']), w=b['w'] / 2, d=b['d'] * 0.7),
                     C_COM, L.PAD, rng)
    else:
        print('TODO: builder for type', b['type'])
for p in L.POOLS:
    mb = MB('Pool', (0, 0, L.PAD))
    A.pool_basin(mb, p['x0'], p['x1'], p['y0'], p['y1'], -0.12, p.get('depth', 1.4), M['_pool_main'], 0.35,
                 M['concrete_grey'], p.get('infinity_edge'))
    mb.build(C_COM)
A.boundary(L.BOUNDARY, C_LAND, ground, L.SOFT_EDGE_Y if L.SOFT_EDGE_Y is not None else -1e9, rng)
if L.PATHS:
    pm = MB('Paths')
    for pts in L.PATHS:
        A.stepping_path(pm, pts, ground, rng)
    pm.build(C_LAND)

# ------------------------------------------------------------------ vegetation
c_leaf = V.asset_collection('leaf_cards', C_ASSETS)
V.leaf_mesh('leaf_a', c_leaf, 0.24, 0.13, M['leaf_broad']); V.leaf_mesh('leaf_b', c_leaf, 0.18, 0.11, M['leaf_broad'], curve=0.3)
trees_c = []
for k in range(3):
    c = V.asset_collection(f'tree_{k}', C_ASSETS)
    V.broadleaf_tree(f'tree_{k}', c, c_leaf, [9, 12, 6][k], [6, 8, 4][k], [3, 4, 2][k], 30 + k, leaf_density=22,
                     pad_r=(0.7, 1.25), pad_flat=0.6)
    trees_c.append(c)
palms_c = []
for k in range(4):
    c = V.asset_collection(f'palm_{k}', C_ASSETS)
    V.coconut_palm(f'palm_{k}', c, [9, 11, 13, 15][k], (rng.uniform(.3, 1.4), rng.uniform(-.4, .4)), 10 + k)
    palms_c.append(c)


def place(asset, x, y, s=1.0):
    e = bpy.data.objects.new(asset.name, None); e.instance_type = 'COLLECTION'; e.instance_collection = asset
    e.location = (x, y, ground(x, y) - 0.05); e.rotation_euler = (0, 0, rng.uniform(0, 6.283)); e.scale = (s, s, s)
    C_VEG.objects.link(e)


TR = np.load(os.path.join(D, 'trees.npy')) if os.path.exists(os.path.join(D, 'trees.npy')) else np.zeros((0, 4))
for x, y, rad, h in TR:
    place(rng.choice(trees_c if rad > 2.5 else palms_c), x, y, max(0.6, min(1.4, h / 10)))
for x, y, kind in L.TREES_EXTRA:
    place(rng.choice(palms_c if kind == 'palm' else trees_c), x, y)

# ------------------------------------------------------------------ scan reference (excluded by default)
fr = json.load(open(os.path.join(D, 'frame.json')))
scan = CFG.get('scan')
if scan and os.path.exists(scan) and scan.lower().endswith(('.glb', '.gltf')):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=scan)
    Mx = Matrix(fr['matrix'])
    for o in [o for o in bpy.data.objects if o not in before]:
        for c in o.users_collection: c.objects.unlink(o)
        if o.type == 'MESH':
            C_SCAN.objects.link(o); o.data.transform(Mx @ o.matrix_world); o.matrix_world = Matrix.Identity(4)
            o.hide_render = True
        else:
            bpy.data.objects.remove(o)

# ------------------------------------------------------------------ sky, sun, cameras, render
el, az = math.radians(L.SUN['elevation']), math.radians(L.SUN['azimuth'])
sd = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
world = bpy.data.worlds.new('Sky'); scene.world = world
wn = world.node_tree.nodes; wn.clear()
sky = wn.new('ShaderNodeTexSky')
for st in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
    try:
        sky.sky_type = st; break
    except TypeError:
        continue
for k, v in (('sun_elevation', el), ('sun_rotation', math.pi / 2 - math.atan2(sd.x, sd.y)), ('sun_disc', True)):
    if hasattr(sky, k):
        try: setattr(sky, k, v)
        except Exception: pass
bg = wn.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 0.32
wo = wn.new('ShaderNodeOutputWorld')
world.node_tree.links.new(sky.outputs[0], bg.inputs[0]); world.node_tree.links.new(bg.outputs[0], wo.inputs['Surface'])
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.4; sun.data.angle = math.radians(0.6); sun.data.color = (1.0, 0.92, 0.8)
sun.rotation_euler = sd.to_track_quat('Z', 'Y').to_euler(); C_CAM.objects.link(sun)
for name, loc, tgt, lens in L.CAMERAS:
    loc = (loc[0], loc[1], ground(loc[0], loc[1]) + 1.7 if loc[2] is None else loc[2])
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 30000
    ob = bpy.data.objects.new(name, cd); ob.location = loc
    ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); C_CAM.objects.link(ob)
    scene.camera = scene.camera or ob

scene.render.engine = 'CYCLES'; scene.cycles.samples = 256; scene.cycles.use_denoising = True
scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
scene.render.resolution_x, scene.render.resolution_y = 2560, 1440
try:
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = -0.5
vl = scene.view_layers[0]; vl.layer_collection.children['ASSETS'].exclude = True
sys.path.insert(0, os.path.join(ROOT, 'scripts')) if os.path.isdir(os.path.join(ROOT, 'scripts')) else None
try:
    import viewport_light; viewport_light.apply(scene)
except ImportError:
    print('copy scripts/viewport_light.py next to build.py to enable viewport-light mode')
out = os.path.join(ROOT, L.PROJECT.replace(' ', '_') + '.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out)
