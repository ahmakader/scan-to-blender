# Detail checklist

Use as a definition of "high detail". Not every item applies; skip with a reason, don't forget.

## Buildings
- Plinth / base course, finished floor level above ground
- Walls with real thickness (0.2–0.3 m), openings cut as pier/lintel/sill segments (no booleans needed)
- Every opening: frame (0.06–0.08 m), mullions/sliders, glass pane, sill; doors with leaves
- Recesses and depth: loggias, deep reveals, fins, overhangs, balconies with balustrades + handrail
- Roofs: flat (slab + parapet + membrane + scuppers + rooftop plant/tanks) or pitched (hip/gable shells
  with thickness, fascia, ridge cap, eaves, underside material)
- Interiors visible through glass: floor finish, bed/sofa/table, pendant light, rug
- Wall lights, signage, downpipes, AC units, meters (a few, where photos show them)
- Weathering: AO-driven dirt in corners, splash darkening at the base, subtle noise in render

## Site
- Terrain: flattened building pads, steps where levels change, retaining walls, ramps
- Paving types by mask (pavers, raked sand, lawn, gravel, decking) — procedural, with bump
- Pools: sunken basin with tiled walls/floor, coping, steps/sun-shelf, water surface just below coping,
  terrain hole cut beneath; infinity edges with catch gutter
- Walls, fences, gates, hedges, bollards, path stepping stones
- Furniture from photos: loungers, daybeds, cabanas, umbrellas, tables/chairs, planters
- Vehicles in car parks, boats on beaches, bikes — simple but correctly proportioned

## Vegetation
- Species from research (palms, broadleaf trees, flowering shrubs, grasses, ground cover)
- Procedural meshes with variants (5–7 per species), instanced via collection instances
- Leaf-card canopies via GN on hidden canopy pads; species-correct leaf size/shape
- Ground cover and lawns via GN scatter driven by point attributes from ortho masks; blocked under
  buildings/pools/paving
- Far hills: low-poly tree blobs at density from scan greenness / slope / curvature

## Surroundings
- Coarse terrain to ~1–2 km from the scan where reliable, modelled elsewhere (headlands, blind spots)
- Water: waves (Ocean modifier) near shore, far plane to horizon, shoreline foam, reef/breakers
- Seabed/lakebed with depth-tinted colour visible through shadow-clear water
- Distant landmasses, islands, sea stacks, inland ridges; cloud layer; distance haze

## Presentation
- Cameras: aerial establishing, top-down ortho, eye-level exterior, signature space, interior, wide context
- Sun + physical sky matched to location/orientation; AgX; denoising
- README: sources, what is scan / research / invented, rebuild commands
