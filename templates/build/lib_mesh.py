"""Small geometry toolkit: accumulate boxes/cylinders/meshes per material, emit one object."""
import math
import bpy
import numpy as np


class MB:
    """Mesh builder. Coordinates are in a local frame (pivot + rotation about Z)."""

    def __init__(self, name, pivot=(0, 0, 0), rot_deg=0.0):
        self.name = name
        self.pivot = pivot
        self.rot = math.radians(rot_deg)
        self.v = []
        self.f = []
        self.fm = []
        self.mats = []

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def add(self, verts, faces, mat):
        mi = self._mi(mat)
        o = len(self.v)
        self.v.extend(verts)
        for fc in faces:
            self.f.append([i + o for i in fc])
            self.fm.append(mi)

    # -- primitives (local frame) -------------------------------------------------
    def box(self, x0, x1, y0, y1, z0, z1, mat, rz=0.0, about=None):
        vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if rz:
            cx, cy = about if about else ((x0 + x1) / 2, (y0 + y1) / 2)
            c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
            vs = [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c, z) for x, y, z in vs]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(vs, fs, mat)

    def cbox(self, cx, cy, cz, sx, sy, sz, mat, rz=0.0):
        self.box(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, mat, rz, (cx, cy))

    def cyl(self, cx, cy, z0, z1, r0, mat, r1=None, n=16, cap=True, rx=0.0):
        r1 = r0 if r1 is None else r1
        vs = []
        for z, r in ((z0, r0), (z1, r1)):
            for i in range(n):
                a = 2 * math.pi * i / n
                vs.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        fs = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        if cap:
            fs.append(tuple(range(n - 1, -1, -1)))
            fs.append(tuple(range(n, 2 * n)))
        self.add(vs, fs, mat)

    def tube(self, pts, radii, mat, n=10, cap=True):
        """Swept tube along a 3D polyline with per-point radius."""
        pts = [np.array(p, float) for p in pts]
        vs = []
        up = np.array([0, 0, 1.0])
        prev_x = None
        for i, p in enumerate(pts):
            t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            t /= (np.linalg.norm(t) + 1e-9)
            ref = up if abs(t @ up) < 0.95 else np.array([1.0, 0, 0])
            x = np.cross(ref, t); x /= np.linalg.norm(x) + 1e-9
            if prev_x is not None and x @ prev_x < 0:
                x = -x
            prev_x = x
            y = np.cross(t, x)
            for k in range(n):
                a = 2 * math.pi * k / n
                q = p + radii[i] * (math.cos(a) * x + math.sin(a) * y)
                vs.append(tuple(q))
        fs = []
        for i in range(len(pts) - 1):
            for k in range(n):
                a, b = i * n + k, i * n + (k + 1) % n
                fs.append((a, b, b + n, a + n))
        if cap:
            fs.append(tuple(range(n - 1, -1, -1)))
            L = (len(pts) - 1) * n
            fs.append(tuple(range(L, L + n)))
        self.add(vs, fs, mat)

    def prism(self, poly, z0, z1, mat, cap=True):
        n = len(poly)
        vs = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        fs = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        if cap:
            fs.append(tuple(range(n - 1, -1, -1)))
            fs.append(tuple(range(n, 2 * n)))
        self.add(vs, fs, mat)

    def quad(self, a, b, c, d, mat):
        self.add([a, b, c, d], [(0, 1, 2, 3)], mat)

    def sphere(self, cx, cy, cz, r, mat, sx=1, sy=1, sz=1, nu=12, nv=8):
        vs = [(cx, cy, cz - r * sz)]
        for j in range(1, nv):
            ph = -math.pi / 2 + math.pi * j / nv
            for i in range(nu):
                th = 2 * math.pi * i / nu
                vs.append((cx + r * sx * math.cos(ph) * math.cos(th), cy + r * sy * math.cos(ph) * math.sin(th),
                           cz + r * sz * math.sin(ph)))
        vs.append((cx, cy, cz + r * sz))
        fs = [(0, 1 + (i + 1) % nu, 1 + i) for i in range(nu)]
        for j in range(nv - 2):
            for i in range(nu):
                a = 1 + j * nu + i; b = 1 + j * nu + (i + 1) % nu
                fs.append((a, b, b + nu, a + nu))
        top = len(vs) - 1; base = 1 + (nv - 2) * nu
        fs += [(base + i, base + (i + 1) % nu, top) for i in range(nu)]
        self.add(vs, fs, mat)

    # -- facade wall with openings ----------------------------------------------
    def wall(self, x0, x1, y, t, z0, z1, mat, openings=(), axis='x', glass=None, frame=None, mullions=1):
        """Wall along x (or y) from x0..x1 at offset y, thickness t, with openings
        [(centre, width, sill, head)]. Openings get frames + glass panes if mats are given."""
        def B(a0, a1, b0, b1, c0, c1, m):
            if axis == 'x':
                self.box(a0, a1, b0, b1, c0, c1, m)
            else:
                self.box(b0, b1, a0, a1, c0, c1, m)
        ops = sorted(openings)
        cur = x0
        for c, w, s, h in ops:
            a, b = c - w / 2, c + w / 2
            if a > cur:
                B(cur, a, y - t / 2, y + t / 2, z0, z1, mat)
            if s > z0:
                B(a, b, y - t / 2, y + t / 2, z0, s, mat)
            if h < z1:
                B(a, b, y - t / 2, y + t / 2, h, z1, mat)
            if frame:
                fw = 0.07
                B(a, a + fw, y - 0.06, y + 0.06, s, h, frame)
                B(b - fw, b, y - 0.06, y + 0.06, s, h, frame)
                B(a, b, y - 0.06, y + 0.06, h - fw, h, frame)
                B(a, b, y - 0.06, y + 0.06, s, s + fw, frame)
                for k in range(1, mullions + 1):
                    mx = a + (b - a) * k / (mullions + 1)
                    B(mx - fw / 2, mx + fw / 2, y - 0.05, y + 0.05, s, h, frame)
            if glass:
                B(a + 0.03, b - 0.03, y - 0.012, y + 0.012, s + 0.03, h - 0.03, glass)
            cur = b
        if cur < x1:
            B(cur, x1, y - t / 2, y + t / 2, z0, z1, mat)

    # -- output -------------------------------------------------------------------
    def build(self, collection, smooth=False):
        if not self.v:
            return None
        px, py, pz = self.pivot
        V = np.array(self.v, float)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(V.tolist(), [], self.f)
        me.update(calc_edges=True)
        me.polygons.foreach_set('material_index', self.fm)
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(self.name, me)
        for m in self.mats:
            ob.data.materials.append(m)
        ob.location = (px, py, pz)
        ob.rotation_euler = (0, 0, self.rot)
        collection.objects.link(ob)
        return ob


def grid_mesh(name, H, x0, x1, y0, y1, collection, mat=None, uv=True, keep=None):
    """Heightfield mesh. H[row, col] with row 0 at y1 (north edge) and col 0 at x0.
    keep: optional boolean mask of cells to keep (False cells are removed)."""
    nv, nu = H.shape
    xs = np.linspace(x0, x1, nu)
    ys = np.linspace(y1, y0, nv)
    X, Y = np.meshgrid(xs, ys)
    V = np.stack([X.ravel(), Y.ravel(), H.ravel()], 1)
    idx = np.arange(nu * nv).reshape(nv, nu)
    a = idx[:-1, :-1]; b = idx[:-1, 1:]; c = idx[1:, 1:]; d = idx[1:, :-1]
    F = np.stack([a, d, c, b], -1)
    if keep is not None:
        F = F[keep]
    F = F.reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set('loop_start', np.arange(0, F.size, 4))
    me.polygons.foreach_set('loop_total', np.full(len(F), 4))
    me.update(calc_edges=True)
    if uv:
        uvl = me.uv_layers.new(name='UVMap')
        U = (V[:, 0] - x0) / (x1 - x0); Vv = (V[:, 1] - y0) / (y1 - y0)
        luv = np.stack([U[F.ravel()], Vv[F.ravel()]], 1)
        uvl.data.foreach_set('uv', luv.ravel())
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    if mat:
        ob.data.materials.append(mat)
    collection.objects.link(ob)
    return ob
