"""Render cameras of a .blend headless.

blender -b scene.blend -P render_cameras.py -- <camera-name-substring|all> <width> <samples> <outdir>
16:9 output, GPU (OptiX > CUDA > HIP > Metal > CPU), denoised. Files: <outdir>/<camera>.png
"""
import bpy, os, sys

a = sys.argv[sys.argv.index('--') + 1:]
which, width, samples, outdir = a[0], int(a[1]), int(a[2]), a[3]
sc = bpy.context.scene
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dev in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
        try:
            prefs.compute_device_type = dev; prefs.get_devices()
            if any(d.type == dev for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == dev
                sc.cycles.device = 'GPU'
                break
        except TypeError:
            continue
except Exception as e:
    print('GPU setup failed, using CPU:', e)
sc.render.engine = 'CYCLES'
sc.cycles.samples = samples; sc.cycles.use_denoising = True
sc.render.resolution_x = width; sc.render.resolution_y = int(width * 9 / 16); sc.render.resolution_percentage = 100
os.makedirs(outdir, exist_ok=True)
for ob in sorted((o for o in sc.objects if o.type == 'CAMERA'), key=lambda o: o.name):
    if which != 'all' and which not in ob.name:
        continue
    sc.camera = ob
    sc.render.filepath = os.path.join(outdir, ob.name + '.png')
    bpy.ops.render.render(write_still=True)
