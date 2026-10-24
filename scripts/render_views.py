"""Render an emission-shaded top-down orthophoto + 4 oblique views of a scan mesh (Blender, headless).

blender -b --factory-startup -P render_views.py -- <mesh.glb|.gltf|.obj|.ply> <outdir> [ortho_px=8192]

Writes <outdir>/ortho.png, ortho.json (world bounds of the image, Blender Z-up frame) and obl_000..270.png.
Emission shading shows the scan's baked colours without new lighting, which makes tracing easier.
"""
import bpy, json, math, os, sys
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
path, out = a[0], a[1]
px = int(a[2]) if len(a) > 2 else 8192
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
ext = path.lower().rsplit('.', 1)[-1]
if ext in ('glb', 'gltf'):
    bpy.ops.import_scene.gltf(filepath=path)
elif ext == 'obj':
    bpy.ops.wm.obj_import(filepath=path)
elif ext == 'ply':
    bpy.ops.wm.ply_import(filepath=path)
elif ext == 'fbx':
    bpy.ops.import_scene.fbx(filepath=path)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
mn = Vector((1e18,) * 3); mx = Vector((-1e18,) * 3)
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
print('BOUNDS', tuple(mn), tuple(mx))

# emission from base colour texture or vertex colour
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    out_n = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if out_n and tex:
        e = nt.nodes.new('ShaderNodeEmission'); nt.links.new(tex.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out_n.inputs[0])
for o in objs:
    if not o.data.materials and o.data.color_attributes:
        m = bpy.data.materials.new('vcol'); m.use_nodes = True; nt = m.node_tree
        at = nt.nodes.new('ShaderNodeVertexColor'); e = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(at.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs[0])
        o.data.materials.append(m)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = 1e6
c = (mn + mx) / 2; size = max(mx.x - mn.x, mx.y - mn.y) * 1.02


def shot(name, loc, target, ortho=None, res=1600, lens=30):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho:
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)


cam.location = (c.x, c.y, mx.z + size); cam.rotation_euler = (0, 0, 0)   # exact top-down, +y up in image
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
sc.render.resolution_x = sc.render.resolution_y = px
sc.render.filepath = os.path.join(out, 'ortho.png')
bpy.ops.render.render(write_still=True)
json.dump({'x0': c.x - size / 2, 'x1': c.x + size / 2, 'y0': c.y - size / 2, 'y1': c.y + size / 2, 'px': px,
           'note': 'row 0 = y1 (north edge), col 0 = x0; Blender Z-up frame'},
          open(os.path.join(out, 'ortho.json'), 'w'), indent=1)
for ang in (0, 90, 180, 270):
    r = size * 0.9; t = math.radians(ang)
    shot(f'obl_{ang:03d}', (c.x + r * math.cos(t), c.y + r * math.sin(t), mx.z + size * 0.45), tuple(c))
print('DONE', out)
