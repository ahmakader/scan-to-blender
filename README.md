# scan-to-blender

A Claude Code **skill** that turns a 3D scan of a real place into a detailed, layered, editable Blender
scene. It accepts a Gaussian splat, a point cloud or a textured GLB/OBJ mesh. The skill researches the
place on the web for everything the scan can't see.

![example](examples/contact_sheet.jpg)
*Example: a beach resort in Lombok, rebuilt from a drone scan (point cloud + GLB) plus web research.*

## What it does

1. **Reads the scan:** format detection (3DGS / point cloud / mesh), Z-up conversion, 8K orthophoto,
   oblique views.
2. **Recovers real scale and level:** scale from cars, doors and parking bays; tilt removed by fitting the
   sea, lake or ground plane.
3. **Builds height maps:** DSM, bare ground and relative heights give footprints, storey counts and tree
   positions in a metric site frame.
4. **Researches the place** in a parallel subagent: official site, booking sites, OpenStreetMap, blogs. It
   downloads reference photos and fills the gaps the scan can't cover (façades, materials, interiors,
   plant species, blind-spot landscape).
5. **Plans the site:** footprints traced on labelled grid crops into a single editable `layout.py`, with
   an overlay on the scan for approval.
6. **Builds procedurally** with headless Blender Python: terrain, water, buildings with real openings,
   roofs, pools, furniture, procedural plants scattered with Geometry Nodes, distant landscape, sky and
   cameras. It uses a clean collection hierarchy and keeps the aligned scan as an excluded reference layer.
7. **Verifies in a loop:** low-res renders → contact sheet → fix → repeat. It then sets viewport-light
   mode and renders the finals.

## Install

```bash
# personal skill (all projects)
git clone https://github.com/ahmakader/scan-to-blender ~/.claude/skills/scan-to-blender
# or per project
git clone https://github.com/ahmakader/scan-to-blender .claude/skills/scan-to-blender
pip install -r ~/.claude/skills/scan-to-blender/requirements.txt
```

You need Blender 4.2+ (tested on 5.1) and Python 3.10+ with the packages in `requirements.txt`. A GPU is
recommended for Cycles.

## Use

In Claude Code:

```
/scan-to-blender
Scan: D:/scans/villa.ply and D:/scans/villa.glb
Place: Villa Xyz, Uluwatu, Bali. Faces the ocean to the west, 6 bedrooms.
Blender: C:/Program Files/Blender Foundation/Blender 5.1/blender.exe
Output: D:/projects/villa-xyz
```

Or just describe it ("model this scan of … in Blender with all the details"). The skill triggers from its
description.

## Contents

```
SKILL.md                      workflow Claude follows (phases, hierarchy, verification)
references/pitfalls.md        hard-won gotchas: linear colours, haze, ocean tiles, shadow-clear water...
references/research-checklist.md   brief for the research subagent
references/detail-checklist.md     what "high detail" means, element by element
scripts/scan_inspect.py       PLY / 3DGS / GLB / OBJ / LAS / XYZ -> Z-up coloured points + summary
scripts/render_views.py       Blender: emission orthophoto (+ pixel<->world json) and obliques
scripts/level_and_dsm.py      fit plane, dominant angle, site frame, DSM/ground/footprints/trees
scripts/grid_crop.py          labelled metric grid crops for tracing and measuring, with overlays
scripts/contact_sheet.py      preview grid of renders
scripts/render_cameras.py     Blender: render all/some cameras on GPU
scripts/viewport_light.py     Blender: make the .blend light to navigate (renders unchanged)
templates/build/              layout + build templates and libraries (mesh builder, materials,
                              architecture, vegetation), copied into each project and adapted
```

### Script quick reference

```bash
python scripts/scan_inspect.py scan.ply scan.glb --out work
blender -b --factory-startup -P scripts/render_views.py -- scan.glb work/views 8192
python scripts/level_and_dsm.py fit work/points_scan.npy --color water --out work/plane.json
python scripts/level_and_dsm.py angle work/views/ortho.png work/views/ortho.json
python scripts/level_and_dsm.py frame --plane work/plane.json --scale 60 --origin -0.35 -0.15 --angle -24 --out work/frame.json
python scripts/level_and_dsm.py dsm work/points_scan_glb.npy --frame work/frame.json --extent -110 110 -90 95 --out work/dsm
python scripts/grid_crop.py work/views/ortho.png work/views/ortho.json --frame work/frame.json --u 0 60 --v -20 40 --grid 2 --out crop.png
```

## Limitations

- Façades, interiors and fine details are **reconstructed from photos**, not measured. The skill labels what
  is estimated.
- Scale comes from known objects unless the scan is georeferenced; expect ±3–5 %.
- Gaussian splats are converted to points (DC colour, opacity-filtered). View-dependent colour is lost.
- The bundled `lib_arch.py` building types come from a tropical resort. Expect to add types for other
  architecture.

## License

MIT
