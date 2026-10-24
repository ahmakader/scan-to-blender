"""Make the .blend light to navigate: heavy scatters / ocean detail / scan are viewport-off, render-on.

Run inside build.py before saving, or on an existing file:
  blender -b Amber_Resort_Lombok.blend -P build/viewport_light.py
"""
import bpy

HEAVY_PREFIXES = ("scatter_", "leaves_")


def apply(scene=None, save=False):
    scene = scene or bpy.context.scene
    n = 0
    for ob in bpy.data.objects:
        for md in ob.modifiers:
            if md.type == 'NODES' and md.name.startswith(HEAVY_PREFIXES):
                md.show_viewport = False          # grass, morning glory, debris, hill trees, leaf cards
                n += 1
            elif md.type == 'OCEAN':
                md.viewport_resolution = 4        # renders keep the full resolution
    vl = scene.view_layers[0]
    lc = vl.layer_collection.children.get('Scan_Reference')
    if lc:
        lc.exclude = True                         # tick it in the outliner to load the drone scan
    # open in solid mode with clipping suited to a 2 km scene
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type == 'VIEW_3D':
                for sp in area.spaces:
                    if sp.type == 'VIEW_3D':
                        sp.shading.type = 'SOLID'
                        sp.clip_start = 0.1
                        sp.clip_end = 5000
    print('viewport-light: disabled', n, 'scatter modifiers in viewport')
    if save:
        bpy.ops.wm.save_mainfile(compress=True)


if __name__ == '__main__':
    apply(save=True)
