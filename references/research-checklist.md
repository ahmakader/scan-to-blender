# Research brief for the subagent

Paste this (with the place filled in) as the subagent prompt. Ask for a structured report under ~900 words
with sources, plus downloaded reference photos.

```
I'm reconstructing <PLACE> (<town / address / country>) as a detailed Blender model from a drone scan.
The scan gives layout and heights; I need everything else. Use WebSearch (standard, then extended if thin)
and WebFetch on: the official website (and its media library / wp-json/wp/v2/media if WordPress), booking
sites, Google Maps descriptions, OpenStreetMap (Nominatim + Overpass for footprints), TripAdvisor, blogs,
news, architect/award pages, Wikipedia, Instagram captions.

Report, concretely:
1. Identity & location: exact name, address, GPS, which direction it faces, neighbours. If several places
   share the name, list them and say which matches the scan description: <what the scan shows>.
2. Architecture: style, building types, storeys, roof shapes and materials, wall finishes and colours,
   window/door types and frames, balconies, distinctive details, architect if known.
3. Program: number of rooms/units and their types/sizes, amenities (pool sizes, restaurant, lobby, spa...).
4. Exterior spaces: pools (shape, tiles, decks), terraces, paths, walls, fences, lighting, furniture.
5. Landscape: plant species, lawns, hard landscaping, trees.
6. Surroundings: terrain, water body, coastline/beach type, hills, islands, landmarks visible from the site.
7. Interiors visible from outside (lobby, restaurant, rooms): materials and furniture.
8. Images: up to 15 direct image URLs with a one-line description each; download 10 (jpg/png) into
   <out>/refs/ with descriptive file names (01_aerial_pool.jpg ...).
9. Gaps: what you could NOT find.
List every source URL.
```

## How to use the result
- Map each photo to a coverage gap from Phase 1 (façade of block X, pool deck, lobby roof...).
- Prefer photos for: materials, colours (convert to linear!), furniture, plant species, roof types.
- Prefer the scan for: positions, sizes, heights, terrain, tree positions.
- Where photos and scan disagree on layout, trust the scan; on appearance, trust the photos (they may be newer).
