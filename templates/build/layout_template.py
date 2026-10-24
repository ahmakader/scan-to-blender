"""Site plan, traced from the scan orthophoto. THE file a human edits.

Frame: metres. x/y = site grid from frame.json (rotated to the dominant building angle, origin at the site
centre), z = metres above datum (sea level / street). Positions come from the scan; heights from the DSM;
appearance from reference photos.
"""
PROJECT = 'My Place'
PAD = 0.0                     # finished ground level of the main site (m above datum); from the levelled DSM
WATER_LEVEL = None            # e.g. 0.0 for a coastal site, None if no water body
SUN = dict(elevation=18, azimuth=78)   # degrees; azimuth measured from +y towards +x
LATITUDE = 0.0                # for notes / sky choice

# Buildings: one dict per building. type selects the builder in lib_arch / build.py.
#   c=(x, y) centre, w (along local x), d (along local y; +y side gets the main glazing/terrace),
#   rot (deg), storeys, plus type-specific flags.
BUILDINGS = [
    dict(name='Block_A', type='block', c=(0.0, 0.0), w=12.0, d=18.0, rot=0, storeys=2, pool=False),
    # dict(name='Hall', type='pavilion_hip', c=(-40, 20), w=48, d=15, rot=0, storeys=1),
]

# Site boundary (white wall unless the segment lies on `SOFT_EDGE_Y`, e.g. a beach fence)
BOUNDARY = [(-60, -40), (60, -40), (60, 40), (-60, 40)]
SOFT_EDGE_Y = None

POOLS = []        # dict(x0, x1, y0, y1, depth, infinity_edge=None|'y1')
PATHS = []        # list of polylines [(x, y), ...] -> stepping stones / paving
TREES_EXTRA = []  # (x, y, kind) planted by hand where the scan shows none
PROPS = []        # (kind, x, y, rot)

CAMERAS = [       # (name, location, target, lens); z=None means ground + 1.7 m (eye level)
    ('CAM_01_Aerial', (-80, -160, 90), (0, 0, 5), 30),
    ('CAM_02_Top_Down', (0, 0, 500), (0, 0.001, 0), 50),
    ('CAM_03_Eye_Level', (30, -70, None), (0, 0, 4), 26),   # keep eye-level cameras clear of walls (test-render!)
]
