"""Procedural Cycles materials library. ALL colour values are LINEAR (convert sRGB swatches first)."""
import bpy

MATS = {}
HAZE_COLOR = (0.66, 0.74, 0.84)
HAZE_STRENGTH = 1.0


class NT:
    def __init__(self, mat):
        self.nt = mat.node_tree
        self.n = self.nt.nodes
        self.l = self.nt.links
        self.n.clear()
        self.out = self.n.new('ShaderNodeOutputMaterial')

    def node(self, t, **kw):
        nd = self.n.new(t)
        for k, v in kw.items():
            if k.startswith('i_'):
                key = k[2:].replace('_', ' ')
                nd.inputs[key].default_value = v
            else:
                setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.l.new(a, b)

    # helpers --------------------------------------------------------------------
    def coord(self, kind='Object', scale=1.0):
        tc = self.node('ShaderNodeTexCoord')
        if scale == 1.0:
            return tc.outputs[kind]
        mp = self.node('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale) if not isinstance(scale, tuple) else scale
        self.link(tc.outputs[kind], mp.inputs['Vector'])
        return mp.outputs['Vector']

    def noise(self, vec, scale, detail=4, rough=0.55, dist=0.0):
        nz = self.node('ShaderNodeTexNoise', i_Scale=scale, i_Detail=detail, i_Roughness=rough, i_Distortion=dist)
        if vec is not None:
            self.link(vec, nz.inputs['Vector'])
        return nz

    def ramp(self, fac, stops):
        r = self.node('ShaderNodeValToRGB')
        cr = r.color_ramp
        cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
        for p, c in stops[1:-1]:
            e = cr.elements.new(p); e.color = (*c, 1)
        self.link(fac, r.inputs['Fac'])
        return r.outputs['Color']

    def mix(self, fac, a, b, blend='MIX'):
        m = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        if isinstance(fac, (int, float)):
            m.inputs[0].default_value = fac
        else:
            self.link(fac, m.inputs[0])
        for sock, v in ((m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, tuple):
                sock.default_value = (*v, 1) if len(v) == 3 else v
            else:
                self.link(v, sock)
        return m.outputs[2]

    def math(self, op, a, b=None, clamp=False):
        m = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.link(v, m.inputs[i])
        return m.outputs[0]

    def bump(self, height, strength=0.3, dist=0.02, normal=None):
        b = self.node('ShaderNodeBump', i_Strength=strength, i_Distance=dist)
        self.link(height, b.inputs['Height'])
        if normal is not None:
            self.link(normal, b.inputs['Normal'])
        return b.outputs['Normal']

    def principled(self, color, rough=0.5, normal=None, **kw):
        p = self.node('ShaderNodeBsdfPrincipled')
        if isinstance(color, tuple):
            p.inputs['Base Color'].default_value = (*color, 1)
        else:
            self.link(color, p.inputs['Base Color'])
        if isinstance(rough, (int, float)):
            p.inputs['Roughness'].default_value = rough
        else:
            self.link(rough, p.inputs['Roughness'])
        if normal is not None:
            self.link(normal, p.inputs['Normal'])
        for k, v in kw.items():
            key = k.replace('_', ' ')
            if isinstance(v, (int, float, tuple)):
                p.inputs[key].default_value = (*v, 1) if isinstance(v, tuple) and len(v) == 3 else v
            else:
                self.link(v, p.inputs[key])
        return p

    def output(self, shader, displacement=None, haze=None):
        sock = shader.outputs[0] if hasattr(shader, 'outputs') else shader
        if haze:
            # aerial perspective without a world volume: fade to sky colour with camera distance
            cd = self.node('ShaderNodeCameraData')
            f = self.math('SUBTRACT', 1.0, self.math('EXPONENT', self.math('DIVIDE', cd.outputs['View Distance'], -haze)), True)
            e = self.node('ShaderNodeEmission', i_Strength=HAZE_STRENGTH)
            e.inputs['Color'].default_value = (*HAZE_COLOR, 1)
            mx = self.node('ShaderNodeMixShader')
            self.link(f, mx.inputs[0]); self.link(sock, mx.inputs[1]); self.link(e.outputs[0], mx.inputs[2])
            sock = mx.outputs[0]
        self.link(sock, self.out.inputs['Surface'])
        if displacement is not None:
            self.link(displacement, self.out.inputs['Displacement'])


def new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    MATS[name] = m
    return m, NT(m)


def ao_dirt(t, color, amount=0.35, dist=0.6):
    ao = t.node('ShaderNodeAmbientOcclusion', samples=8, i_Distance=dist)
    f = t.math('POWER', ao.outputs['AO'], 1.8)
    return t.mix(t.math('MULTIPLY', t.math('SUBTRACT', 1.0, f, True), amount, True), color, (0.42, 0.40, 0.36))


def shadow_clear(t, shader):
    """Water lets sunlight through to the pool floor / seabed (caustic-free transmission)."""
    lp = t.node('ShaderNodeLightPath')
    tr = t.node('ShaderNodeBsdfTransparent')
    mx = t.node('ShaderNodeMixShader')
    t.link(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    t.link(shader.outputs[0] if hasattr(shader, 'outputs') else shader, mx.inputs[1]); t.link(tr.outputs[0], mx.inputs[2])
    return mx


def build_all():
    # ------------------------------------------------------------------ architecture
    m, t = new('render_white')
    v = t.coord('Object')
    n1 = t.noise(v, 6.0, 6, 0.6)
    n2 = t.noise(v, 0.6, 3, 0.5)
    base = t.mix(t.math('MULTIPLY', n2.outputs['Fac'], 0.35), (0.90, 0.89, 0.85), (0.80, 0.78, 0.72))
    col = ao_dirt(t, base, 0.55, 0.8)
    # rain streaks / ground splash dirt at the base of walls
    sep = t.node('ShaderNodeSeparateXYZ'); t.link(t.coord('Object'), sep.inputs[0])
    low = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', sep.outputs['Z'], 2.2, True), True)
    col = t.mix(t.math('MULTIPLY', low, 0.45), col, (0.62, 0.56, 0.47))
    t.output(t.principled(col, 0.82, t.bump(n1.outputs['Fac'], 0.12, 0.01)))

    m, t = new('roof_dark')
    v = t.coord('Object'); n = t.noise(v, 3.0, 6)
    col = t.ramp(n.outputs['Fac'], [(0.3, (0.075, 0.08, 0.085)), (0.7, (0.16, 0.165, 0.17))])
    t.output(t.principled(col, 0.92, t.bump(t.noise(v, 40, 4).outputs['Fac'], 0.35, 0.01)))

    m, t = new('concrete_grey')
    v = t.coord('Object'); n = t.noise(v, 2.5, 6, 0.62)
    col = t.ramp(n.outputs['Fac'], [(0.25, (0.2, 0.19, 0.175)), (0.75, (0.36, 0.35, 0.33))])
    t.output(t.principled(ao_dirt(t, col, 0.4), 0.78, t.bump(t.noise(v, 30, 5).outputs['Fac'], 0.25, 0.01)))

    m, t = new('terrazzo')
    v = t.coord('Object')
    vor = t.node('ShaderNodeTexVoronoi', i_Scale=60); t.link(v, vor.inputs['Vector'])
    col = t.ramp(vor.outputs['Distance'], [(0.0, (0.35, 0.33, 0.3)), (0.12, (0.78, 0.76, 0.72)), (1.0, (0.82, 0.8, 0.76))])
    t.output(t.principled(col, 0.25))

    def wood(name, dark, light, scale=(1, 18, 1), rough=0.55):
        m, t = new(name)
        v = t.coord('Object', scale)
        w = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', i_Scale=2.0, i_Distortion=6.0, i_Detail=4)
        t.link(v, w.inputs['Vector'])
        n = t.noise(t.coord('Object'), 8, 4)
        f = t.math('ADD', t.math('MULTIPLY', w.outputs['Fac'], 0.7), t.math('MULTIPLY', n.outputs['Fac'], 0.3))
        col = t.ramp(f, [(0.2, dark), (0.8, light)])
        t.output(t.principled(col, rough, t.bump(w.outputs['Fac'], 0.15, 0.005)))
    wood('teak', (0.18, 0.09, 0.04), (0.42, 0.25, 0.12))
    wood('teak_dark', (0.08, 0.05, 0.03), (0.2, 0.12, 0.07), rough=0.45)
    wood('timber_post', (0.22, 0.13, 0.07), (0.38, 0.24, 0.13), (1, 1, 12))

    m, t = new('deck_grey')                                 # weathered timber pool deck
    v = t.coord('Object')
    br = t.node('ShaderNodeTexBrick', offset=0.37, i_Scale=1.0, i_Mortar_Size=0.006, i_Brick_Width=2.4, i_Row_Height=0.145,
                i_Color1=(0.22, 0.2, 0.17, 1), i_Color2=(0.3, 0.27, 0.23, 1), i_Mortar=(0.04, 0.035, 0.03, 1))
    t.link(v, br.inputs['Vector'])
    gr = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=1.5, i_Distortion=8, i_Detail=5)
    t.link(t.coord('Object', (1.0, 12, 1)), gr.inputs['Vector'])
    col = t.mix(t.math('MULTIPLY', gr.outputs['Fac'], 0.25), br.outputs['Color'], (0.15, 0.13, 0.11))
    t.output(t.principled(col, 0.8, t.bump(t.math('ADD', br.outputs['Fac'], t.math('MULTIPLY', gr.outputs['Fac'], 0.2)), 0.4, 0.01)))

    m, t = new('glass')
    t.output(t.principled((0.85, 0.9, 0.9), 0.02, Transmission_Weight=1.0, IOR=1.5, Specular_IOR_Level=0.5))

    m, t = new('glass_dark')                                  # reflective glazing seen from outside
    t.output(t.principled((0.06, 0.07, 0.075), 0.03, Metallic=0.0, Coat_Weight=1.0, Coat_Roughness=0.02))

    m, t = new('thatch')
    v = t.coord('Object')
    w = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', i_Scale=60, i_Distortion=18, i_Detail=8, i_Detail_Scale=3)
    t.link(v, w.inputs['Vector'])
    n = t.noise(v, 4, 5)
    f = t.math('ADD', t.math('MULTIPLY', w.outputs['Fac'], 0.6), t.math('MULTIPLY', n.outputs['Fac'], 0.4))
    col = t.ramp(f, [(0.2, (0.10, 0.05, 0.018)), (0.55, (0.27, 0.15, 0.055)), (0.85, (0.45, 0.30, 0.13))])
    t.output(t.principled(col, 0.95, t.bump(f, 0.9, 0.04)))

    m, t = new('thatch_ceiling')
    v = t.coord('Object', (1, 1, 1))
    w = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=90, i_Distortion=12, i_Detail=6)
    t.link(v, w.inputs['Vector'])
    col = t.ramp(w.outputs['Fac'], [(0.2, (0.12, 0.07, 0.025)), (0.8, (0.36, 0.24, 0.1))])
    t.output(t.principled(col, 0.95, t.bump(w.outputs['Fac'], 0.6, 0.02)))

    m, t = new('reed')
    t.output(t.principled((0.47, 0.36, 0.2), 0.8, t.bump(t.noise(t.coord('Object', (1, 1, 40)), 10).outputs['Fac'], 0.3)))

    m, t = new('metal_pale')                                  # pale corrugated roof
    v = t.coord('Object')
    w = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', wave_profile='SIN', i_Scale=14, i_Distortion=0)
    t.link(v, w.inputs['Vector'])
    n = t.noise(v, 2, 5)
    col = t.ramp(n.outputs['Fac'], [(0.3, (0.55, 0.53, 0.48)), (0.75, (0.72, 0.7, 0.64))])
    t.output(t.principled(col, 0.5, t.bump(w.outputs['Fac'], 0.6, 0.03), Metallic=0.6))

    m, t = new('metal_dark_roof')                             # dark standing-seam / shingle roof
    v = t.coord('Object')
    br = t.node('ShaderNodeTexBrick', offset=0.5, i_Scale=1.0, i_Mortar_Size=0.01, i_Brick_Width=0.9, i_Row_Height=0.32,
                i_Color1=(0.09, 0.1, 0.11, 1), i_Color2=(0.13, 0.14, 0.15, 1), i_Mortar=(0.05, 0.05, 0.05, 1))
    t.link(v, br.inputs['Vector'])
    n = t.noise(v, 1.5, 4)
    col = t.mix(t.math('MULTIPLY', n.outputs['Fac'], 0.4), br.outputs['Color'], (0.2, 0.2, 0.2))
    t.output(t.principled(col, 0.7, t.bump(br.outputs['Fac'], 0.5, 0.01), Metallic=0.3))

    for name, c, r in (('fabric_cream', (0.83, 0.79, 0.7), 0.9), ('fabric_white', (0.9, 0.89, 0.86), 0.85),
                       ('fabric_teal', (0.1, 0.35, 0.36), 0.9), ('fabric_amber', (0.72, 0.42, 0.16), 0.9)):
        m, t = new(name)
        n = t.noise(t.coord('Object'), 120, 2)
        t.output(t.principled(c, r, t.bump(n.outputs['Fac'], 0.1, 0.002), Sheen_Weight=0.4))

    m, t = new('canvas_sheer')                                # cabana curtains
    p = t.principled((0.95, 0.94, 0.9), 0.8, Transmission_Weight=0.35, Alpha=0.85)
    t.output(p)

    m, t = new('rattan')
    v = t.coord('Object')
    ch = t.node('ShaderNodeTexChecker', i_Scale=60, i_Color1=(0.55, 0.38, 0.2, 1), i_Color2=(0.42, 0.27, 0.13, 1))
    t.link(v, ch.inputs['Vector'])
    t.output(t.principled(ch.outputs['Color'], 0.7, t.bump(ch.outputs['Fac'], 0.3, 0.003)))

    m, t = new('bamboo')
    v = t.coord('Object')
    w = t.node('ShaderNodeTexWave', wave_type='RINGS', i_Scale=0.0, i_Distortion=0)
    w2 = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', wave_profile='SAW', i_Scale=1.6, i_Distortion=0)
    t.link(v, w2.inputs['Vector'])
    col = t.ramp(w2.outputs['Fac'], [(0.0, (0.15, 0.1, 0.04)), (0.06, (0.4, 0.32, 0.13)), (1.0, (0.33, 0.27, 0.11))])
    t.output(t.principled(col, 0.45, t.bump(w2.outputs['Fac'], 0.2, 0.01)))

    m, t = new('paver_grey')
    v = t.coord('Object')
    br = t.node('ShaderNodeTexBrick', offset=0.5, i_Scale=1.0, i_Mortar_Size=0.012, i_Brick_Width=0.2, i_Row_Height=0.1,
                i_Color1=(0.38, 0.38, 0.37, 1), i_Color2=(0.5, 0.49, 0.47, 1), i_Mortar=(0.22, 0.21, 0.2, 1))
    t.link(v, br.inputs['Vector'])
    t.output(t.principled(ao_dirt(t, br.outputs['Color'], 0.3), 0.85, t.bump(br.outputs['Fac'], 0.6, 0.01)))

    m, t = new('stone_dark')
    n = t.noise(t.coord('Object'), 12, 6)
    t.output(t.principled(t.ramp(n.outputs['Fac'], [(0.3, (0.16, 0.16, 0.16)), (0.7, (0.3, 0.29, 0.28))]), 0.8,
                          t.bump(n.outputs['Fac'], 0.5, 0.01)))

    m, t = new('rock')
    v = t.coord('Object'); n = t.noise(v, 0.25, 8, 0.65, 0.5)
    vor = t.node('ShaderNodeTexVoronoi', i_Scale=0.8); t.link(v, vor.inputs['Vector'])
    col = t.ramp(n.outputs['Fac'], [(0.3, (0.2, 0.19, 0.17)), (0.55, (0.42, 0.39, 0.34)), (0.8, (0.55, 0.52, 0.46))])
    t.output(t.principled(col, 0.85, t.bump(t.math('ADD', n.outputs['Fac'], vor.outputs['Distance']), 1.0, 0.5)))

    m, t = new('terracotta_tiles')
    v = t.coord('Object')
    br = t.node('ShaderNodeTexBrick', offset=0.5, i_Scale=1.0, i_Mortar_Size=0.004, i_Brick_Width=0.1, i_Row_Height=0.1,
                i_Color1=(0.6, 0.27, 0.12, 1), i_Color2=(0.72, 0.38, 0.18, 1), i_Mortar=(0.75, 0.7, 0.62, 1))
    t.link(v, br.inputs['Vector'])
    t.output(t.principled(br.outputs['Color'], 0.35, t.bump(br.outputs['Fac'], 0.4, 0.005)))

    m, t = new('blue_glazed')
    v = t.coord('Object')
    br = t.node('ShaderNodeTexBrick', offset=0.0, i_Scale=1.0, i_Mortar_Size=0.004, i_Brick_Width=0.07, i_Row_Height=0.28,
                i_Color1=(0.17, 0.27, 0.32, 1), i_Color2=(0.24, 0.36, 0.41, 1), i_Mortar=(0.7, 0.7, 0.7, 1))
    t.link(v, br.inputs['Vector'])
    t.output(t.principled(br.outputs['Color'], 0.12, t.bump(br.outputs['Fac'], 0.3, 0.004)))

    # pool tiles: dark cobalt mosaic inland, turquoise towards the sea (local +y)
    def pool_tiles(name, y0, y1):
        m, t = new(name)
        v = t.coord('Object')
        br = t.node('ShaderNodeTexBrick', offset=0.0, i_Scale=1.0, i_Mortar_Size=0.003, i_Brick_Width=0.05, i_Row_Height=0.05,
                    i_Color1=(1, 1, 1, 1), i_Color2=(0.85, 0.85, 0.85, 1), i_Mortar=(0.75, 0.78, 0.8, 1))
        t.link(v, br.inputs['Vector'])
        sep = t.node('ShaderNodeSeparateXYZ'); t.link(t.coord('Object'), sep.inputs[0])
        g = t.math('DIVIDE', t.math('SUBTRACT', sep.outputs['Y'], y0), (y1 - y0))
        grad = t.ramp(g, [(0.0, (0.02, 0.06, 0.32)), (0.35, (0.03, 0.18, 0.5)), (0.7, (0.05, 0.42, 0.58)), (1.0, (0.12, 0.6, 0.62))])
        col = t.mix(1.0, grad, br.outputs['Color'], 'MULTIPLY')
        t.output(t.principled(col, 0.15, t.bump(br.outputs['Fac'], 0.3, 0.003)))
        return m
    MATS['_pool_tiles'] = pool_tiles

    m, t = new('pool_water')
    n = t.noise(t.coord('Object', (1, 1, 1)), 1.6, 3, 0.5)
    t.output(shadow_clear(t, t.principled((0.9, 0.98, 0.98), 0.0, t.bump(n.outputs['Fac'], 0.06, 0.05),
                                         Transmission_Weight=1.0, IOR=1.333)))

    # ------------------------------------------------------------------ vegetation
    def leaf(name, c1, c2, translucent=0.35, rough=0.45):
        m, t = new(name)
        oi = t.node('ShaderNodeObjectInfo')
        col = t.ramp(oi.outputs['Random'], [(0.0, c1), (1.0, c2)])
        p = t.principled(col, rough, Subsurface_Weight=0.0)
        tr = t.node('ShaderNodeBsdfTranslucent'); t.link(col, tr.inputs['Color'])
        mx = t.node('ShaderNodeMixShader', i_Fac=translucent)
        t.link(p.outputs[0], mx.inputs[1]); t.link(tr.outputs[0], mx.inputs[2])
        t.output(mx)
    leaf('leaf_palm', (0.10, 0.20, 0.03), (0.30, 0.36, 0.07), 0.3)
    leaf('leaf_palm_dry', (0.38, 0.26, 0.11), (0.55, 0.42, 0.2), 0.2, 0.7)
    leaf('leaf_broad', (0.04, 0.13, 0.02), (0.13, 0.24, 0.04), 0.25)
    leaf('leaf_shrub', (0.05, 0.16, 0.03), (0.16, 0.28, 0.05), 0.25)
    leaf('leaf_frangipani', (0.14, 0.3, 0.06), (0.26, 0.42, 0.1))
    leaf('leaf_banana', (0.22, 0.42, 0.08), (0.36, 0.52, 0.12), 0.45)
    leaf('leaf_bamboo', (0.25, 0.38, 0.08), (0.48, 0.5, 0.16))
    leaf('grass_lawn', (0.12, 0.3, 0.04), (0.3, 0.42, 0.1), 0.3, 0.55)
    leaf('grass_dry', (0.42, 0.33, 0.16), (0.68, 0.56, 0.32), 0.25, 0.75)
    leaf('morning_glory', (0.1, 0.3, 0.05), (0.2, 0.42, 0.08), 0.3)
    leaf('flower_white', (0.95, 0.92, 0.8), (0.98, 0.85, 0.45), 0.4, 0.5)
    leaf('flower_magenta', (0.7, 0.05, 0.35), (0.85, 0.15, 0.45), 0.4, 0.5)
    leaf('flower_red', (0.75, 0.08, 0.04), (0.9, 0.35, 0.05), 0.3, 0.5)

    m, t = new('hill_tree')
    oi = t.node('ShaderNodeObjectInfo')
    n = t.noise(t.coord('Object'), 1.5, 5)
    col = t.mix(n.outputs['Fac'], t.ramp(oi.outputs['Random'], [(0.0, (0.07, 0.15, 0.04)), (1.0, (0.22, 0.27, 0.08))]), (0.05, 0.1, 0.03))
    t.output(t.principled(col, 0.85, t.bump(t.noise(t.coord('Object'), 6, 4).outputs['Fac'], 0.6, 0.2)), haze=5000)

    m, t = new('bark_palm')
    v = t.coord('Object')
    w = t.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', wave_profile='SAW', i_Scale=6, i_Distortion=1.5, i_Detail=3)
    t.link(v, w.inputs['Vector'])
    n = t.noise(v, 20, 6)
    col = t.ramp(t.math('ADD', t.math('MULTIPLY', w.outputs['Fac'], 0.5), t.math('MULTIPLY', n.outputs['Fac'], 0.5)),
                 [(0.2, (0.1, 0.085, 0.07)), (0.6, (0.24, 0.21, 0.17)), (0.9, (0.33, 0.3, 0.25))])
    t.output(t.principled(col, 0.9, t.bump(t.math('ADD', w.outputs['Fac'], n.outputs['Fac']), 0.8, 0.02)))

    m, t = new('bark_grey')
    v = t.coord('Object'); n = t.noise(v, 6, 8, 0.65, 1.5)
    col = t.ramp(n.outputs['Fac'], [(0.3, (0.2, 0.18, 0.15)), (0.7, (0.42, 0.39, 0.34))])
    t.output(t.principled(col, 0.85, t.bump(n.outputs['Fac'], 0.7, 0.02)))

    m, t = new('coconut')
    t.output(t.principled((0.35, 0.33, 0.1), 0.5))

    # ------------------------------------------------------------------ vehicles & misc
    for name, c, met in (('car_white', (0.85, 0.86, 0.86), 0.0), ('car_silver', (0.5, 0.52, 0.54), 0.8),
                         ('car_black', (0.02, 0.02, 0.025), 0.3), ('tyre', (0.03, 0.03, 0.03), 0.0),
                         ('boat_blue', (0.05, 0.25, 0.6), 0.0), ('boat_red', (0.7, 0.1, 0.06), 0.0),
                         ('boat_yellow', (0.85, 0.65, 0.05), 0.0)):
        m, t = new(name)
        t.output(t.principled(c, 0.25 if 'car' in name else 0.6, Metallic=met, Coat_Weight=0.8 if 'car' in name else 0.0))

    m, t = new('lamp_warm')
    e = t.node('ShaderNodeEmission', i_Strength=6.0); e.inputs['Color'].default_value = (1.0, 0.72, 0.4, 1)
    t.output(e)

    m, t = new('mural')                                       # botanical murals on entrance walls
    v = t.coord('Object')
    vor = t.node('ShaderNodeTexVoronoi', i_Scale=1.8); t.link(v, vor.inputs['Vector'])
    n = t.noise(v, 3, 3, 0.5, 3)
    col = t.ramp(n.outputs['Fac'], [(0.0, (0.9, 0.88, 0.84)), (0.42, (0.9, 0.88, 0.84)), (0.48, (0.08, 0.38, 0.36)),
                                    (0.55, (0.72, 0.16, 0.1)), (0.62, (0.2, 0.45, 0.15)), (0.7, (0.9, 0.88, 0.84))])
    t.output(t.principled(col, 0.8))
    return MATS
