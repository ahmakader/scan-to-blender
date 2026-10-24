"""Prove the model matches the scan: render the aligned scan layer from the model's own cameras, then build
side-by-sides, 50 % overlays and wipe GIFs against the model renders.

1) blender -b scene.blend -P compare_scan_model.py -- render CAM_01,CAM_04 1600 <outdir>
      renders <outdir>/<cam>_scan.png from the 'Scan_Reference*' collection with flat baked colours
2) python compare_scan_model.py build <outdir> <model_render_dir> CAM_01,CAM_04
      writes compare_<cam>.jpg (scan | model), overlay_<cam>.jpg (50 % blend) and wipe_<cam>.gif
Check the overlays: walls, roof edges, pools and shorelines must coincide.
"""
import os, sys


def render(cams, width, outdir):
    import bpy
    sc = bpy.context.scene
    vl = sc.view_layers[0]
    scan_lc = next(lc for lc in vl.layer_collection.children if lc.name.startswith('Scan_Reference'))
    for lc in vl.layer_collection.children:
        lc.exclude = lc not in (scan_lc,) and not lc.name.startswith('Cameras')
    objs = list(scan_lc.collection.all_objects)
    for o in objs:
        o.hide_render = False
    # every material slot -> emission of its base texture (the scan's baked light), otherwise unlit slots
    # render dark and the result looks like camouflage
    scan_mats = {sl.material for o in objs for sl in o.material_slots if sl.material}
    for m in scan_mats:
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
        if out and tex:
            e = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(tex.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out.inputs['Surface'])
    w = bpy.data.worlds.new('plain'); sc.world = w
    bg = w.node_tree.nodes.get('Background') or w.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = width; sc.render.resolution_y = int(width * 9 / 16)
    os.makedirs(outdir, exist_ok=True)
    for name in cams:
        sc.camera = bpy.data.objects[name]
        sc.render.filepath = os.path.join(outdir, name + '_scan.png')
        bpy.ops.render.render(write_still=True)


def build(outdir, model_dir, cams):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('arialbd.ttf', 18)
    except Exception:
        font = ImageFont.load_default()

    def tag(im, t, right=False):
        d = ImageDraw.Draw(im); tw = int(d.textlength(t, font=font)) + 16
        x = im.width - tw if right else 0
        d.rectangle([x, 0, x + tw, 28], fill=(0, 0, 0)); d.text((x + 8, 4), t, fill=(255, 255, 255), font=font)
        return im
    W, H = 800, 450
    for cam in cams:
        s = Image.open(os.path.join(outdir, cam + '_scan.png')).convert('RGB').resize((W, H), Image.LANCZOS)
        m = Image.open(os.path.join(model_dir, cam + '.png')).convert('RGB').resize((W, H), Image.LANCZOS)
        pair = Image.new('RGB', (2 * W + 8, H), (255, 255, 255))
        pair.paste(tag(s.copy(), 'Drone scan'), (0, 0)); pair.paste(tag(m.copy(), 'Blender model'), (W + 8, 0))
        pair.save(os.path.join(outdir, f'compare_{cam}.jpg'), quality=86)
        tag(Image.blend(s, m, 0.5), '50% overlay').save(os.path.join(outdir, f'overlay_{cam}.jpg'), quality=86)
        w, h = 560, 315
        s2, m2 = s.resize((w, h)), m.resize((w, h))
        pal = Image.blend(s2, m2, 0.5).quantize(colors=160)
        frames, dur = [], []
        for k in list(range(13)) + list(range(12, -1, -1)):
            x = int(w * k / 12)
            f = m2.copy(); f.paste(s2.crop((x, 0, w, h)), (x, 0))
            ImageDraw.Draw(f).line([(x, 0), (x, h)], fill=(255, 230, 0), width=3)
            tag(f, 'Blender model'); tag(f, 'Drone scan', right=True)
            frames.append(f.quantize(palette=pal, dither=Image.Dither.NONE)); dur.append(900 if k in (0, 12) else 90)
        frames[0].save(os.path.join(outdir, f'wipe_{cam}.gif'), save_all=True, append_images=frames[1:],
                       duration=dur, loop=0, optimize=True)
    print('built comparisons for', cams)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'render':
        render(args[1].split(','), int(args[2]), args[3])
    else:
        build(args[1], args[2], args[3].split(','))
