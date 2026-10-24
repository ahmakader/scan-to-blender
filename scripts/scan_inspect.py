"""Inspect scan files and export Z-up coloured points.

usage: python scan_inspect.py <file> [<file> ...] --out <dir> [--up y|z] [--samples-per-face 6]

Supports: PLY (binary/ascii; plain point clouds, meshes, and 3D Gaussian Splatting files with f_dc_*/opacity),
GLB/GLTF/OBJ/FBX-less meshes via trimesh (surface-sampled with texture colours), LAS/LAZ via laspy (optional),
XYZ/TXT (x y z [r g b]).
Writes <out>/points_<name>.npy  float32 [N, 6] = x, y, z (Z-up, scan units), r, g, b (0-255)
and prints a summary (format, counts, bounds, guessed up axis, colour stats).
"""
import argparse, os, sys
import numpy as np

PLY_TYPES = {'char': 'i1', 'uchar': 'u1', 'int8': 'i1', 'uint8': 'u1', 'short': 'i2', 'ushort': 'u2',
             'int16': 'i2', 'uint16': 'u2', 'int': 'i4', 'uint': 'u4', 'int32': 'i4', 'uint32': 'u4',
             'float': 'f4', 'float32': 'f4', 'double': 'f8', 'float64': 'f8'}
SH_C0 = 0.28209479177387814


def read_ply_vertices(path):
    with open(path, 'rb') as f:
        header = []
        while True:
            line = f.readline().decode('ascii', 'ignore').strip()
            header.append(line)
            if line == 'end_header':
                break
        fmt = next(l.split()[1] for l in header if l.startswith('format'))
        props, count, in_vertex = [], 0, False
        for l in header:
            p = l.split()
            if p[:1] == ['element']:
                in_vertex = p[1] == 'vertex'
                if in_vertex:
                    count = int(p[2])
            elif p[:1] == ['property'] and in_vertex:
                if p[1] == 'list':
                    raise ValueError('list property inside vertex element is not supported')
                props.append((p[2], PLY_TYPES[p[1]]))
        if fmt == 'ascii':
            data = np.loadtxt(f, max_rows=count)
            arr = np.zeros(count, dtype=[(n, 'f8') for n, _ in props])
            for i, (n, _) in enumerate(props):
                arr[n] = data[:, i]
            return arr, header
        endian = '<' if 'little' in fmt else '>'
        dt = np.dtype([(n, endian + t) for n, t in props])
        arr = np.frombuffer(f.read(dt.itemsize * count), dtype=dt, count=count)
        return arr, header


def ply_points(path):
    v, header = read_ply_vertices(path)
    names = v.dtype.names
    xyz = np.stack([v['x'], v['y'], v['z']], 1).astype(np.float64)
    kind = 'point cloud'
    if 'f_dc_0' in names:
        kind = '3D Gaussian Splatting'
        rgb = np.clip(0.5 + SH_C0 * np.stack([v['f_dc_0'], v['f_dc_1'], v['f_dc_2']], 1), 0, 1) * 255
        if 'opacity' in names:
            op = 1 / (1 + np.exp(-v['opacity'].astype(np.float64)))
            keep = op > 0.35
            if 'scale_0' in names:   # drop huge, blurry splats
                sc = np.exp(np.max(np.stack([v['scale_0'], v['scale_1'], v['scale_2']], 1), 1))
                keep &= sc < np.percentile(sc, 99)
            print(f'  splats kept (opacity>0.35, scale<p99): {keep.sum()} / {len(keep)}')
            xyz, rgb = xyz[keep], rgb[keep]
    elif {'red', 'green', 'blue'} <= set(names):
        rgb = np.stack([v['red'], v['green'], v['blue']], 1).astype(np.float64)
        if rgb.max() > 255:
            rgb = rgb / 256.0
    else:
        rgb = np.full((len(xyz), 3), 180.0)
    if any(l.startswith('element face') for l in header):
        kind += ' (mesh vertices only)'
    return xyz, rgb, kind, False


def mesh_points(path, spf):
    import trimesh
    s = trimesh.load(path, force='scene')
    P, C = [], []
    for name, g in s.geometry.items():
        if not hasattr(g, 'faces') or len(g.faces) == 0:
            continue
        T = s.graph.get(s.graph.geometry_nodes[name][0])[0] if name in s.graph.geometry_nodes else np.eye(4)
        n = max(1000, int(len(g.faces) * spf))
        pts, fi = trimesh.sample.sample_surface(g, n)
        col = np.full((len(pts), 3), 180.0)
        vis = g.visual
        try:
            if hasattr(vis, 'uv') and vis.uv is not None and getattr(vis.material, 'baseColorTexture', None) is not None:
                img = np.asarray(vis.material.baseColorTexture.convert('RGB'))
                bary = trimesh.triangles.points_to_barycentric(g.triangles[fi], pts)
                uv = (vis.uv[g.faces[fi]] * bary[:, :, None]).sum(1)
                H, W = img.shape[:2]
                col = img[np.clip(((1 - uv[:, 1] % 1) * (H - 1)).astype(int), 0, H - 1),
                          np.clip(((uv[:, 0] % 1) * (W - 1)).astype(int), 0, W - 1)].astype(np.float64)
            elif hasattr(vis, 'face_colors'):
                col = vis.face_colors[fi, :3].astype(np.float64)
        except Exception as e:
            print('  colour lookup failed for', name, e)
        pts = trimesh.transform_points(pts, T)
        P.append(pts); C.append(col)
    xyz = np.concatenate(P); rgb = np.concatenate(C)
    gltf = path.lower().endswith(('.glb', '.gltf'))
    return xyz, rgb, f'mesh ({len(s.geometry)} parts)', gltf


def other_points(path):
    ext = path.lower().rsplit('.', 1)[-1]
    if ext in ('las', 'laz'):
        import laspy
        L = laspy.read(path)
        xyz = np.stack([L.x, L.y, L.z], 1)
        rgb = np.stack([L.red, L.green, L.blue], 1) / 256.0 if hasattr(L, 'red') else np.full((len(xyz), 3), 180.0)
        return xyz, rgb, 'LAS point cloud', False
    data = np.loadtxt(path, usecols=None)
    xyz = data[:, :3]
    rgb = data[:, 3:6] if data.shape[1] >= 6 else np.full((len(xyz), 3), 180.0)
    return xyz, rgb, 'XYZ text point cloud', False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--up', choices=['y', 'z', 'auto'], default='auto')
    ap.add_argument('--samples-per-face', type=float, default=6.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for path in a.files:
        print('=' * 70, '\n', path, f'({os.path.getsize(path) / 1e6:.1f} MB)')
        ext = path.lower().rsplit('.', 1)[-1]
        if ext == 'ply':
            xyz, rgb, kind, yup = ply_points(path)
        elif ext in ('glb', 'gltf', 'obj', 'stl', 'off', 'dae'):
            xyz, rgb, kind, yup = mesh_points(path, a.samples_per_face)
        else:
            xyz, rgb, kind, yup = other_points(path)
        ext_ = np.percentile(xyz, 99, 0) - np.percentile(xyz, 1, 0)
        up = a.up
        if up == 'auto':
            up = 'y' if (yup or np.argmin(ext_) == 1) else 'z'
        if up == 'y':      # glTF convention -> Blender: (x, -z, y)
            xyz = np.stack([xyz[:, 0], -xyz[:, 2], xyz[:, 1]], 1)
        print(f'  kind: {kind}\n  points: {len(xyz)}\n  up axis used: {up}  (1-99% extents x,y,z of source: {np.round(ext_, 3)})')
        for i, k in enumerate('XYZ'):
            print(f'  {k}: min {xyz[:, i].min():.3f}  p1 {np.percentile(xyz[:, i], 1):.3f}  '
                  f'median {np.median(xyz[:, i]):.3f}  p99 {np.percentile(xyz[:, i], 99):.3f}  max {xyz[:, i].max():.3f}')
        print(f'  colour mean RGB {np.round(rgb.mean(0), 1)}')
        name = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(a.out, f'points_{name}.npy')
        np.save(out, np.concatenate([xyz, rgb], 1).astype(np.float32))
        print('  ->', out)


if __name__ == '__main__':
    sys.exit(main())
