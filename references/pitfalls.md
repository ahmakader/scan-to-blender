# Pitfalls (each one has broken a real build)

## Scan data
- **glTF is Y-up, Blender is Z-up.** Blender's importer maps (x, y, z)gltf → (x, −z, y). Numpy code reading the
  GLB directly must do the same, or overlays come out mirrored.
- **Point clouds and meshes from one reconstruction usually share a frame and scale.** Verify on one feature
  before assuming — then use the cloud for wide surroundings.
- **Scans are tilted.** The fitted sea/ground plane is rarely level (5–6° is common). Level by subtracting the
  fitted plane (`z' = z − (a·x + b·y + c)`); two genuinely horizontal surfaces must give parallel planes.
- **Water reconstructs as noise.** Never use scanned heights over water; model the bed (gentle shelf, then
  drop-off) and put a water surface at the fitted level.
- **Mesh skirts and voids.** Photogrammetry meshes often have a grey-blue skirt and black holes at the
  edges. Exclude them from colour classification (they read as "sand"/"concrete") and from heightmaps.
- **Blind spots.** Hills block the drone's view; the cloud shows a black wedge behind them. Model those areas
  from photos instead of trusting sparse points.
- **DSM auto-segmentation merges buildings** that share walls. Trace footprints on labelled grid crops; use
  the DSM only for heights and as a hint.
- **Scale.** No scan has true metric scale unless georeferenced. Derive it from cars, doors, parking bays and
  cross-check with a researched dimension.

## Blender / Cycles
- **Node colour values are LINEAR.** A swatch picked as sRGB (0.55, 0.38, 0.18) renders washed-out beige-grey.
  Convert: `lin = ((c+0.055)/1.055)**2.4` (c > 0.04045). Sand ≈ (0.6, 0.5, 0.34), thatch ≈ (0.27, 0.15, 0.055),
  weathered timber ≈ (0.25, 0.22, 0.19).
- **World volume + sun lamp = black scene.** Sun light crosses infinite volume. For haze, blend each distant
  material to an emission haze colour with `1 − exp(−CameraData.ViewDistance / k)`.
- **Water/glass blocks sunlight** without caustics → black pool floors and seabeds. Mix the water shader with
  Transparent using Light Path → *Is Shadow Ray*.
- **Ocean modifier origin.** The generated grid grows from the first tile towards +x/+y
  (`[loc − size/2, loc − size/2 + size·repeat]`). Place it from its evaluated bounds, then add a huge flat far
  plane slightly below for the horizon. Foam from `use_foam` needs a high map-range threshold (≈1.0–1.6) or the
  sea turns into white camouflage.
- **Cameras inside geometry render black.** Place eye-level cameras at `ground(x, y) + 1.7`, interior cameras
  away from columns/walls, and test-render every camera.
- **Collection instances from an excluded collection still render** via Collection Info / instance_collection
  — so keep source assets in an excluded `ASSETS` collection.
- **Cycles flattens nested instancing.** Thousands of trees each carrying thousands of leaf instances can
  explode memory. Use leaf-card trees near the camera, low-poly blob trees for far hills.
- **Geometry Nodes Random Value** input indices: FLOAT_VECTOR min/max = 0/1, FLOAT = 2/3, INT = 4/5.
  Mix node (RGBA): factor = input 0, A = 6, B = 7, result = output 2.
- **Shader node inputs in 4.x/5.x:** Principled uses `Transmission Weight`, `Subsurface Weight`, `Coat Weight`,
  `Sheen Weight`, `Emission Color`. Sheen with a white tint greys out warm materials — leave it off for thatch/wood.
- **Sky texture type names changed across versions** (`NISHITA`, `MULTIPLE_SCATTERING`, …). Try a list.
- **AgX desaturates strong colours**; judge colour with a normal-strength sun, not emissive test colours.
- **Viewport weight.** Before handing over, disable GN scatter modifiers in the viewport
  (`show_viewport=False`, render stays on), set the Ocean `viewport_resolution` low, exclude the scan
  collection, open in Solid mode — then prove a render is unchanged.

## Process
- **Don't name helper scripts after stdlib modules** (`inspect.py`, `copy.py`, `types.py`) — scipy etc. will
  import yours.
- **Bash heredocs with nested quotes break.** Write patch scripts to files.
- **Low-res contact sheet every iteration.** Most defects (dark scene, wrong scale, seams, floating objects)
  are obvious at 640 px and invisible in code.
