---
name: scan-to-blender
description: Reconstruct a real place as a detailed, layered Blender scene from a 3D scan (Gaussian splat .ply, point cloud .ply/.las/.xyz, textured mesh .glb/.gltf/.obj) plus web research. Use when the user provides a drone/phone/LiDAR scan of a building, resort, campus, street or landscape and wants a clean, high-detail, editable Blender model (not just the raw scan), including surroundings, terrain, water, vegetation and props. Triggers on "model this scan in Blender", "rebuild this place from my scan", "gaussian splat to blender", "turn this GLB/point cloud into a proper 3D model", "scan to 3D model".
---

# Scan → detailed Blender model

The scan is the **ground truth for layout, scale and heights**. Web research supplies **what the scan
cannot see** (façades under eaves, materials, interiors, signage, planting species, blind-spot
landscape). Everything is built as **procedural, re-runnable Python** so the user can edit the site
plan and rebuild.

Read `references/pitfalls.md` before writing any Blender code — every item there cost hours once.

## Inputs to collect (ask only for what is missing)

- Scan file paths (any of: 3DGS `.ply`, point cloud `.ply/.las/.xyz/.e57`, mesh `.glb/.gltf/.obj/.fbx`)
- Place name + location (address / town / GPS), and any facts the user knows (orientation, sizes, counts)
- Blender executable path and version (`blender --version`), GPU
- Output folder and final `.blend` name
- Desired look (time of day, season) — default: golden hour, current season at that latitude

Work in a project folder: `<out>/build/` (scripts), `<out>/build/data/` (derived data),
`<out>/refs/` (reference photos), `<out>/renders/`. Use the session scratchpad for throwaway files.

## Phase 1 — Understand the scan (no modelling yet)

1. `python scripts/scan_inspect.py <files...> --out <scratch>` — prints format (real 3DGS vs plain
   point cloud vs mesh), counts, bounds, guessed up-axis, and writes `points_*.npy` (x,y,z,r,g,b,
   Z-up). For 3DGS it converts SH DC colour and drops low-opacity splats.
2. If both a mesh and a cloud exist, check they share a frame: compare a distinctive feature
   (pool, roof corner) in both. Same frame → use the cloud for the wide surroundings and the mesh for
   the site.
3. `blender -b --factory-startup -P scripts/render_views.py -- <mesh> <scratch> 8192` — emission-shaded
   top-down orthophoto (8K, with a JSON describing pixel↔world mapping) and 4 obliques. **Look at
   them.** Describe the site to the user in 3–5 lines.
4. **Scale.** Measure known objects on grid crops (`scripts/grid_crop.py`): cars ≈ 4.5 m × 1.8 m,
   doors ≈ 2.1 m, parking bays 2.5 × 5 m, pool lanes 2.5 m, sun loungers 2 m. Cross-check with
   research (room sizes, pool length). State "N m per scan unit" with the evidence.
5. **Level.** `python scripts/level_and_dsm.py fit <points.npy> --mask <colour rule or bbox>` fits a
   plane to surfaces that must be horizontal (sea/lake surface is best, then courtyards/roads).
   Scans are often tilted several degrees. Two horizontal surfaces should give parallel planes —
   if not, investigate before continuing.
6. `python scripts/level_and_dsm.py dsm ...` → levelled DSM, bare-ground (grey opening), relative
   heights, footprint candidates, tree blobs, all in a **local site frame** rotated to the site grid
   (find the dominant building angle from the ortho). Storeys ≈ relative height / 3.2 m.
7. Write down coverage: what the scan resolves well and what is missing (façades, under canopies,
   water, occluded hills, far landscape). This list drives the research.

## Phase 2 — Research (run as a background subagent in parallel with Phase 1)

Brief the subagent with `references/research-checklist.md`. It must return a structured report
with sources, and download 10–15 reference photos into `<out>/refs/` with descriptive names. Read
the photos yourself; map each photo to the coverage gaps from step 7. Save all URLs to
`<out>/build/refs.txt`. Disambiguate places with the same name before trusting anything.

## Phase 3 — Plan (show the user before the full build)

- Trace every building on labelled grid crops of the ortho (`grid_crop.py` in the local frame,
  0.05-unit or 1 m grid). Auto-segmentation from the DSM merges neighbours — use it only as a
  hint. Record footprints in `build/layout.py` (copy `templates/build/layout_template.py`):
  centre, size, rotation, storeys, type, features (pool, balcony, roof type), all in metres.
- Decide per element: **scan-driven** (position, size, height, terrain) vs **reference-driven**
  (façade, materials, details) vs **invented** (only where neither exists — label it so in the README).
- Render a **top-down overlay of the planned footprints on the scan ortho** and show it with a
  one-paragraph plan (collections, asset list, cameras). Proceed unless the user objects.

## Phase 4 — Build (procedural, headless, rebuildable)

Copy `templates/build/*` into `<out>/build/` and adapt. Structure:

| File | Role |
|---|---|
| `prep.py` | scan → levelled heightmaps, ortho in local frame, tree detections (`build/data/`) |
| `compose.py` | final terrain: scan ground + flattened pads + modelled blind spots + water bed; material masks |
| `layout.py` | the site plan — the one file a human edits |
| `lib_mesh.py` | MeshBuilder (boxes, walls with openings+frames+glass, tubes, prisms, heightfield grids) |
| `lib_mat.py` | procedural Cycles materials (linear colours!), shadow-clear water, distance haze |
| `lib_arch.py` | building types, roofs, pools, furniture — one function per type, driven by layout entries |
| `lib_veg.py` | procedural plants + Geometry-Nodes scatter |
| `build.py` | assembles the scene, cameras, sun/sky, render settings, saves the .blend |
| `render.py` | renders cameras (`scripts/render_cameras.py`) |

Run with `blender -b --factory-startup -P build/build.py`. Never hand-edit the .blend as the source
of truth.

**Collection hierarchy** (exact names can follow the place):

```
Terrain            detailed site mesh (~0.3 m) + coarse surroundings (~3 m), hole-cut under pools
Water              sea/lake/river (Ocean modifier or plane), far plane to horizon, foam strips
<Site>
  Buildings_<type> one object per building (MeshBuilder output, multi-material)
  Common_Areas     lobby, restaurant, pools, amenities
  Landscape        walls, fences, paths, steps, hedges
Vegetation         collection instances of plant assets + GN scatters on terrain
Props              furniture outside buildings, vehicles, boats, lights, signage
Distant_Landscape  far hills, islands, clouds
Cameras_Lights     sun, sky, cameras
ASSETS             plant/leaf/prop source collections — EXCLUDED from view layer
Scan_Reference     original scan transformed into the model frame — EXCLUDED by default
```

**Detail bar** (see `references/detail-checklist.md`): real wall thickness; every opening has frame,
glass and sill; parapets/eaves/fascias; roof finish and rooftop plant; interiors visible through
glass; furniture where photos show it; lights; species-correct plants generated procedurally and
instanced; ground cover scattered by masks from the ortho; surroundings to the horizon.

## Phase 5 — Verify loop (mandatory)

After every build: render all cameras at ~1280 px / 32 spp → `scripts/contact_sheet.py` → **look**
→ list defects → fix → repeat. Typical 4–8 rounds. Each round also check:
- alignment proof: `blender -b scene.blend -P scripts/compare_scan_model.py -- render <cams> 1600 <dir>` then
  `python scripts/compare_scan_model.py build <dir> <renders> <cams>`. Every 50 % overlay must show walls, roof edges,
  pools and shorelines coinciding. Fix the layout until they do, and report any residual difference honestly
- cameras not inside walls or under ground (`ground(x,y) + 1.7` for eye level)
- no seams between detailed and coarse terrain, no terrain inside pools/water
- colours read as in the reference photos (linear vs sRGB!)

Finish with: `scripts/viewport_light.py` (heavy scatters viewport-off/render-on, scan excluded,
ocean low-res in viewport — then a test render proving renders are unchanged), final renders at
2560×1440, and a `README.md` stating what came from the scan, research, and invention, plus
rebuild steps, plus scan-vs-model side-by-sides and wipe GIFs from the same cameras. Report honestly what
is estimated.

## Communication

Tell the user what you are doing at each phase in a line or two; show the ortho, the overlay and
contact sheets. Ask only for decisions the scan, references and common sense can't settle.
