# "Rack" — a pool-table build film (standalone pipeline test).
# Hologram assembly -> materialize -> the break -> settle -> fold back.
# 12 s seamless loop @30fps, landscape. Reuses the proven film rig.
#
#   Test frames: Blender -b -P pool_table.py -- --test 60 160 210
#   Full render: Blender -b -P pool_table.py -- --render
import bpy
import os
import sys
import math
from math import radians, sin, cos, pi

# ---------------------------------------------------------------- config ----
COL_BG    = (0.0062, 0.0058, 0.0042, 1.0)    # warm near-black stage
COL_FACE  = (0.0100, 0.0094, 0.0068, 1.0)
COL_LINE  = (0.81, 0.79, 0.72, 1.0)          # warm paper wireframes
COL_HOT   = (1.0, 0.985, 0.93, 1.0)
COL_GRID  = (0.030, 0.150, 0.085, 1.0)       # emerald floor grid
LINE_STR  = 2.4
INDIGO    = (0.75, 0.38, 0.05, 1.0)          # amber accent (rings, callouts)
INDIGO_HOT= (1.0, 0.72, 0.30, 1.0)
SKY       = (0.110, 0.456, 0.838, 1.0)
TEAL      = (0.026, 0.55, 0.30, 1.0)         # emerald aurora partner
DONE_GRN  = (0.10, 0.72, 0.32, 1.0)
WOOD      = (0.072, 0.027, 0.0085, 1.0)
WOOD_EDGE = (1.0, 0.70, 0.40, 1.0)
PAPER     = (0.52, 0.48, 0.40, 1.0)
FELT_GRN  = (0.012, 0.135, 0.055, 1.0)       # tournament green
WALNUT    = (0.62, 0.44, 0.30, 1.0)          # tint over Wood049

SS        = 2                                 # supersample factor
RES_X, RES_Y = 1600, 900
FPS       = 30
F_END     = 360                               # 12 s loop @30fps
WIRE_T    = 0.0028

IN = 0.0254
T  = 0.75 * IN
CAB_W, CAB_D, CAB_H = 36*IN, 24*IN, 34.5*IN
TOE_H, TOE_IN = 4*IN, 3*IN
DRW_H  = 6*IN
REVEAL = 0.125*IN
GAP    = 0.0009                               # joinery daylight: kills z-fight
FT = 0.3048
TBL_L, TBL_W = 2.90, 1.63                    # 9-ft table outer
PLAY_L, PLAY_W = 2.54, 1.27                  # 100 x 50 playfield
RAIL_H, BED_H = 0.80, 0.76
BALL_R = 0.028575
CHROME  = (0.85, 0.86, 0.88, 1.0)
LEATHER = (0.055, 0.032, 0.020, 1.0)


OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEX = OUT_DIR + "assets/tex/"
PLATES = OUT_DIR + "assets/plates/"


# ------------------------------------------------------------ fcurve utils --
def all_fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and act.fcurves is not None:
        try:
            return list(act.fcurves)
        except Exception:
            pass
    fcs = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in getattr(strip, "channelbags", []):
                fcs.extend(cb.fcurves)
    return fcs

def _style(o, path, frame, interp, easing, index=None):
    for fc in all_fcurves(o):
        if fc.data_path == path and (index is None or fc.array_index == index):
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.01:
                    kp.interpolation = interp
                    kp.easing = easing

def key_vec(o, path, frame, vec, interp="BEZIER", easing="EASE_OUT"):
    setattr(o, path, vec)
    o.keyframe_insert(data_path=path, frame=frame)
    _style(o, path, frame, interp, easing)

def key_idx(o, path, index, frame, value, interp="BEZIER", easing="EASE_OUT"):
    v = list(getattr(o, path))
    v[index] = value
    setattr(o, path, v)
    o.keyframe_insert(data_path=path, frame=frame, index=index)
    _style(o, path, frame, interp, easing, index)

def key_hide(o, frame, hidden):
    for x in [o] + list(o.children_recursive):
        x.hide_render = hidden
        x.keyframe_insert(data_path="hide_render", frame=frame)

# object.color drives the shared line material:
#   R -> 0 = white-hot, 1 = brand cyan      A -> emission strength multiplier
def state(o, frame, r=None, a=None, w=None, c=None, interp="BEZIER",
          easing="EASE_OUT", tree=True):
    """R: 0=hot 1=base | G: wood factor | B: confirmed-green | A: gain"""
    objs = [o] + (list(o.children_recursive) if tree else [])
    for x in objs:
        if r is not None:
            key_idx(x, "color", 0, frame, r, interp, easing)
        if w is not None:
            key_idx(x, "color", 1, frame, w, interp, easing)
        if c is not None:
            key_idx(x, "color", 2, frame, c, interp, easing)
        if a is not None:
            key_idx(x, "color", 3, frame, a, interp, easing)

def ghost_flicker(o, f0, settle=0.10):
    """hologram stutter-on, then hold dim"""
    for f, a in ((f0, 0.0), (f0+2, 0.13), (f0+5, 0.05), (f0+8, settle)):
        state(o, f, a=a, interp="CONSTANT")

# ---------------------------------------------------------------- scene -----
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
             bpy.data.cameras, bpy.data.curves):
    for x in list(coll):
        try:
            coll.remove(x)
        except Exception:
            pass

scene = bpy.context.scene
scene.render.resolution_x = RES_X * SS
scene.render.resolution_y = RES_Y * SS
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = F_END

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wbg = world.node_tree.nodes.get("Background")
wbg.inputs[0].default_value = COL_BG
wbg.inputs[1].default_value = 1.0

try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass

engines = [e.identifier for e in
           bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
eevee = next((e for e in engines if "EEVEE" in e), None)
scene.render.engine = eevee or "CYCLES"
if scene.render.engine == "CYCLES":
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False

# ------------------------------------------------------------- materials ----
def line_material(name, base, hot, strength, turn_erase=False):
    """emission driven by per-object color: R picks hot->base, A scales power"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = hot      # A
    mix.inputs[7].default_value = base     # B
    nt.links.new(oi.outputs["Color"], sep.inputs[0])
    nt.links.new(sep.outputs["Red"], mix.inputs["Factor"])
    # G channel warms the linework during the wood reveal
    wmix = nt.nodes.new("ShaderNodeMix")
    wmix.data_type = "RGBA"
    wmix.inputs[7].default_value = WOOD_EDGE
    nt.links.new(mix.outputs[2], wmix.inputs[6])
    nt.links.new(sep.outputs["Green"], wmix.inputs["Factor"])
    # B channel: flip to confirmed-green (dims during the master-file beat)
    cmix = nt.nodes.new("ShaderNodeMix")
    cmix.data_type = "RGBA"
    cmix.inputs[7].default_value = DONE_GRN
    nt.links.new(wmix.outputs[2], cmix.inputs[6])
    nt.links.new(sep.outputs["Blue"], cmix.inputs["Factor"])
    nt.links.new(cmix.outputs[2], em.inputs["Color"])
    # strength = A * STR * (1 + 2.2*(1-R))  -> hot parts also burn brighter
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "SUBTRACT"
    m1.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Red"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY_ADD"
    m2.inputs[1].default_value = 1.25
    m2.inputs[2].default_value = 1.0
    nt.links.new(m1.outputs[0], m2.inputs[0])
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
    nt.links.new(oi.outputs["Alpha"], m3.inputs[0])
    nt.links.new(m2.outputs[0], m3.inputs[1])
    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
    m4.inputs[1].default_value = strength
    nt.links.new(m3.outputs[0], m4.inputs[0])
    nt.links.new(m4.outputs[0], em.inputs["Strength"])
    # alpha 0 must mean GONE, not black: mix to transparent below ~0.12
    f1 = nt.nodes.new("ShaderNodeMath"); f1.operation = "MULTIPLY"
    f1.inputs[1].default_value = 8.0
    nt.links.new(oi.outputs["Alpha"], f1.inputs[0])
    f2 = nt.nodes.new("ShaderNodeMath"); f2.operation = "MINIMUM"
    f2.inputs[1].default_value = 1.0
    nt.links.new(f1.outputs[0], f2.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(f2.outputs[0], ms.inputs["Fac"])
    nt.links.new(tr.outputs[0], ms.inputs[1])
    nt.links.new(em.outputs[0], ms.inputs[2])
    # the turn line erases wires below it, flaring on the way through
    if not turn_erase:
        nt.links.new(ms.outputs[0], out.inputs[0])
        return m
    mask, band = turn_mask_nodes(nt)
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(mask, inv.inputs[1])
    keep = nt.nodes.new("ShaderNodeMath"); keep.operation = "MAXIMUM"
    nt.links.new(inv.outputs[0], keep.inputs[0])
    nt.links.new(band, keep.inputs[1])
    ms2 = nt.nodes.new("ShaderNodeMixShader")
    tr2 = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(keep.outputs[0], ms2.inputs["Fac"])
    nt.links.new(tr2.outputs[0], ms2.inputs[1])
    nt.links.new(ms.outputs[0], ms2.inputs[2])
    nt.links.new(ms2.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m

def ghostface_material(name):
    """fully transparent faces for AR-target ghosts: wires only, X-ray"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m

def flat_material(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def face_material(name):
    """opaque occluder; ghost fill lerps to the bg color so it reads see-thru
    without alpha-sorting artifacts (depth still writes -> hidden-line holds)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(oi.outputs["Color"], sep.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = COL_BG     # ghost fill == background
    mix.inputs[7].default_value = COL_FACE
    nt.links.new(oi.outputs["Alpha"], mix.inputs["Factor"])
    # G channel: hologram fill -> lit walnut for the reveal beat
    wmix = nt.nodes.new("ShaderNodeMix")
    wmix.data_type = "RGBA"
    wmix.inputs[7].default_value = WOOD
    nt.links.new(mix.outputs[2], wmix.inputs[6])
    nt.links.new(sep.outputs["Green"], wmix.inputs["Factor"])
    # B channel: flip to confirmed-green (dims during the master-file beat)
    cmix = nt.nodes.new("ShaderNodeMix")
    cmix.data_type = "RGBA"
    cmix.inputs[7].default_value = DONE_GRN
    nt.links.new(wmix.outputs[2], cmix.inputs[6])
    nt.links.new(sep.outputs["Blue"], cmix.inputs["Factor"])
    nt.links.new(cmix.outputs[2], em.inputs["Color"])
    ws = nt.nodes.new("ShaderNodeMath"); ws.operation = "MULTIPLY_ADD"
    ws.inputs[1].default_value = 0.8         # wood lifts gently, not lava
    ws.inputs[2].default_value = 1.0
    nt.links.new(sep.outputs["Green"], ws.inputs[0])
    nt.links.new(ws.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def glass_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mixs = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = COL_LINE
    em.inputs["Strength"].default_value = 0.28
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = 0.13
    nt.links.new(oi.outputs["Alpha"], sc.inputs[0])
    nt.links.new(sc.outputs[0], mixs.inputs["Fac"])
    nt.links.new(tr.outputs[0], mixs.inputs[1])
    nt.links.new(em.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m

def turn_mask_nodes(nt, soften=0.02):
    """0 above the turn line, 1 below — driven by the turn_ctl empty's Z"""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    tz = nt.nodes.new("ShaderNodeValue")
    tz.name = "TurnZ"
    drv = tz.outputs[0].driver_add("default_value").driver
    drv.type = "AVERAGE"
    var = drv.variables.new()
    var.name = "z"
    var.targets[0].id = bpy.data.objects["turn_ctl"]
    var.targets[0].data_path = "location.z"
    d = nt.nodes.new("ShaderNodeMath"); d.operation = "SUBTRACT"
    nt.links.new(tz.outputs[0], d.inputs[0])
    nt.links.new(sep.outputs["Z"], d.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -soften
    mr.inputs["From Max"].default_value = soften
    mr.clamp = True
    nt.links.new(d.outputs[0], mr.inputs["Value"])
    band = nt.nodes.new("ShaderNodeMath"); band.operation = "ABSOLUTE"
    nt.links.new(d.outputs[0], band.inputs[0])
    bl = nt.nodes.new("ShaderNodeMapRange")
    bl.inputs["From Min"].default_value = 0.030
    bl.inputs["From Max"].default_value = 0.004
    bl.clamp = True
    nt.links.new(band.outputs[0], bl.inputs["Value"])
    return mr.outputs[0], bl.outputs[0]   # mask, edge-band

def pbr_branch(nt, tex_dir, tex_id, tint=(1, 1, 1, 1), rough_mul=1.0,
               metal=0.0, scale=1.6, paint=None):
    """box-projected Principled from an ambientCG 2K JPG set"""
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    def img(suffix, non_color=False):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(
            tex_dir + tex_id + "/" + tex_id + "_2K-JPG_" + suffix + ".jpg",
            check_existing=True)
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.3
        nt.links.new(mp.outputs[0], node.inputs["Vector"])
        return node
    if paint is not None:
        pr.inputs["Base Color"].default_value = paint
        pr.inputs["Roughness"].default_value = 0.38
        nrm = img("NormalGL", True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.12   # grain ghosting through paint
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], pr.inputs["Normal"])
        pr.inputs["Metallic"].default_value = 0.0
        return pr
    col = img("Color")
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.blend_type = "MULTIPLY"
    mixc.inputs["Factor"].default_value = 1.0
    mixc.inputs[7].default_value = tint
    nt.links.new(col.outputs["Color"], mixc.inputs[6])
    nt.links.new(mixc.outputs[2], pr.inputs["Base Color"])
    rough = img("Roughness", True)
    rmul = nt.nodes.new("ShaderNodeMath"); rmul.operation = "MULTIPLY"
    rmul.inputs[1].default_value = rough_mul
    rmul.use_clamp = True
    nt.links.new(rough.outputs["Color"], rmul.inputs[0])
    nt.links.new(rmul.outputs[0], pr.inputs["Roughness"])
    nrm = img("NormalGL", True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.7
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], pr.inputs["Normal"])
    pr.inputs["Metallic"].default_value = metal
    return pr

def face_material_v6(name, tex_id, tint=(1, 1, 1, 1), rough_mul=1.0,
                     scale=1.6, paint=None, metal=0.0):
    """hologram fill below the story, real PBR once the turn line passes"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    # holo branch (bg-lerp by alpha, same as before)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = COL_BG
    mix.inputs[7].default_value = COL_FACE
    nt.links.new(oi.outputs["Alpha"], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    # real branch
    pr = pbr_branch(nt, TEX, tex_id, tint, rough_mul, metal=metal,
                    scale=scale, paint=paint)
    mask, band = turn_mask_nodes(nt)
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mask, ms.inputs["Fac"])
    nt.links.new(em.outputs[0], ms.inputs[1])
    nt.links.new(pr.outputs[0], ms.inputs[2])
    # edge flare where the line crosses
    flare = nt.nodes.new("ShaderNodeEmission")
    flare.inputs["Color"].default_value = COL_HOT
    fs = nt.nodes.new("ShaderNodeMath"); fs.operation = "MULTIPLY"
    fs.inputs[1].default_value = 5.0
    nt.links.new(band, fs.inputs[0])
    nt.links.new(fs.outputs[0], flare.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(ms.outputs[0], add.inputs[0])
    nt.links.new(flare.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    return m

def hw_material_v6(name):
    """indigo hologram accent that becomes brushed metal"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    em.inputs["Color"].default_value = INDIGO
    st = nt.nodes.new("ShaderNodeMath"); st.operation = "MULTIPLY"
    st.inputs[1].default_value = 1.7
    nt.links.new(oi.outputs["Alpha"], st.inputs[0])
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    # transparent when the hologram is powered down
    f1 = nt.nodes.new("ShaderNodeMath"); f1.operation = "MULTIPLY"
    f1.inputs[1].default_value = 8.0
    nt.links.new(oi.outputs["Alpha"], f1.inputs[0])
    f2 = nt.nodes.new("ShaderNodeMath"); f2.operation = "MINIMUM"
    f2.inputs[1].default_value = 1.0
    nt.links.new(f1.outputs[0], f2.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    holo = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(f2.outputs[0], holo.inputs["Fac"])
    nt.links.new(tr.outputs[0], holo.inputs[1])
    nt.links.new(em.outputs[0], holo.inputs[2])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    pr = pbr_branch(nt, TEX, "Metal012", tint=(0.78, 0.52, 0.18, 1.0),
                    rough_mul=1.0, metal=0.85, scale=6.0)  # satin brass, warm in shadow
    mask, band = turn_mask_nodes(nt)
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mask, ms.inputs["Fac"])
    nt.links.new(holo.outputs[0], ms.inputs[1])
    nt.links.new(pr.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs[0])
    return m

def plate_material(name, img_path):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(img_path, check_existing=True)
    nt.links.new(tc.outputs["UV"], im.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(im.outputs["Color"], em.inputs["Color"])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    st = nt.nodes.new("ShaderNodeMath"); st.operation = "MULTIPLY"
    st.inputs[1].default_value = 0.30
    nt.links.new(oi.outputs["Alpha"], st.inputs[0])
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    f1 = nt.nodes.new("ShaderNodeMath"); f1.operation = "MULTIPLY"
    f1.inputs[1].default_value = 8.0
    nt.links.new(oi.outputs["Alpha"], f1.inputs[0])
    f2 = nt.nodes.new("ShaderNodeMath"); f2.operation = "MINIMUM"
    f2.inputs[1].default_value = 1.0
    nt.links.new(f1.outputs[0], f2.inputs[0])
    nt.links.new(f2.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m

# the turn controller must exist before materials build their drivers
turn_ctl = bpy.data.objects.new("turn_ctl", None)
bpy.context.collection.objects.link(turn_ctl)
turn_ctl.location = (0, 0, -0.5)

MAT = {
    "face":  face_material_v6("phc_face_paint", "Wood094",
                              paint=(0.575, 0.520, 0.428, 1.0)),   # BM Edgecomb Gray HC-173
    "face_marble": face_material_v6("phc_face_marble", "Marble012",
                              rough_mul=0.55, scale=0.42),
    "face_zinc": face_material_v6("phc_face_zinc", "Wood094",
                              paint=(0.115, 0.125, 0.135, 1.0)),
    "face_floor": face_material_v6("phc_face_floor", "Wood049",
                              tint=(0.80, 0.72, 0.62, 1.0), rough_mul=1.25,
                              scale=0.75),
    "face_plaster": face_material_v6("phc_face_plaster", "Wood094",
                              paint=PLASTER),
    "face_black": face_material_v6("phc_face_black", "Wood094",
                              paint=(0.012, 0.012, 0.013, 1.0)),
    "face_birch": face_material_v6("phc_face_birch", "Wood094",
                              rough_mul=1.0, scale=2.2),
    "line":  line_material("phc_line", COL_LINE, COL_HOT, LINE_STR,
                           turn_erase=True),
    "dimline": line_material("phc_dimline", COL_LINE, COL_HOT, LINE_STR),
    "hw":    hw_material_v6("phc_hw"),
    "hw_flat": line_material("phc_hw_flat", INDIGO, INDIGO_HOT, 1.7),
    "ring":  line_material("phc_ring", INDIGO, INDIGO_HOT, 2.0),
    "note":  line_material("phc_note", PAPER, PAPER, 0.50),
    "grid":  flat_material("phc_grid", COL_GRID, 0.85),
    "glass": glass_material("phc_glass"),
    "scan":  line_material("phc_scan", TEAL, COL_HOT, 2.4),
    "sky":   line_material("phc_sky", SKY, COL_HOT, 1.7),
    "done":  line_material("phc_done", DONE_GRN, COL_HOT, 1.7),
    "ghostface": ghostface_material("phc_ghostface"),
}

# --------------------------------------------------------------- builders ---
def add_box(name, dims, loc, wire=True, parent=None, line_mat=None,
            face_mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(face_mat or MAT["face"])
    o.data.materials.append(line_mat or MAT["line"])
    if wire:
        w = o.modifiers.new("wire", "WIREFRAME")
        w.thickness = WIRE_T
        w.use_replace = False
        w.material_offset = 1
        w.use_boundary = True
    b = o.modifiers.new("bevel", "BEVEL")
    b.width = 0.0012
    b.segments = 2
    b.angle_limit = radians(40)
    if parent:
        o.parent = parent
    return o

def add_solid(name, dims, loc, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o

# ---------------------------------------------------- cameras: the edit ----
# Quick-cut montage. Each shot has its own camera with a slow interior move;
# markers bind cameras to the timeline. Shot 1 and the final shot share CAM A
# with matched endpoints so the loop is seamless.
def cam_pos(az_deg, dist, h):
    a = radians(az_deg)
    return (dist * sin(a), -dist * cos(a), h)

def make_cam(name, tz, fstop, lens=78):
    tgt = bpy.data.objects.new(name + "_tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (0, 0, tz)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 60
    try:
        cd.dof.use_dof = True
        cd.dof.focus_object = tgt
        cd.dof.aperture_fstop = fstop
    except Exception:
        pass
    c = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(c)
    tr = c.constraints.new("TRACK_TO")
    tr.target = tgt
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    return c, tgt

# (name, az, dist, h, target_z, fstop, f_in, f_out, az2, dist2, h2, lens)
SHOTS = [
    ("CAM_A",  16, 8.6, 1.35, 1.02, 5.0,  66, 100, 18, 7.9, 1.30, 46),
    ("CAM_B",  33, 5.4, 0.55, 1.15, 3.6, 100, 160, 30, 5.1, 0.62, 46),
    ("CAM_Dm", 48, 2.3, 0.70, 0.55, 2.2, 160, 200, 44, 2.2, 0.74, 78),
    ("CAM_C", 0.5, 8.2, 1.15, 1.12, 5.6, 200, 306,  2, 7.9, 1.15, 46),
    ("CAM_Em",-30, 2.6, 0.75, 0.72, 2.2, 306, 370, -26, 2.5, 0.79, 78),
    ("CAM_E2",-14, 2.9, 0.80, 0.74, 2.4, 476, 566, -10, 2.7, 0.84, 78),
    ("CAM_D2", 22, 2.2, 1.15, 0.95, 2.0, 566, 648, 18, 2.1, 1.10, 78),
    ("CAM_G",  26, 2.9, 2.05, 2.30, 2.4, 648, 700, 23, 2.7, 2.10, 78),
    ("CAM_H",  -8, 3.3, 1.75, 1.90, 2.6, 700, 756, -5, 3.1, 1.80, 78),
    ("CAM_F",  27, 6.4, 1.45, 1.05, 4.5, 756, 840, 24, 6.1, 1.35, 46),
]
CAMS = {}
CAM_TGTS = {}
for name, az, d, h, tz, fs, f0, f1, az2, d2, h2, lens in SHOTS:
    c, tgt = make_cam(name, tz, fs, lens)
    CAMS[name] = c
    CAM_TGTS[name] = tgt
    key_vec(c, "location", f0, cam_pos(az, d, h), "BEZIER", "EASE_IN_OUT")
    key_vec(c, "location", f1, cam_pos(az2, d2, h2), "BEZIER", "EASE_IN_OUT")
    mk = scene.timeline_markers.new(name + "_cut", frame=f0)
    mk.camera = c

# document shots: flat-on open, fold-back close
docc, doct = make_cam("CAM_DOC", 1.44, 5.0, 50)
key_vec(docc, "location", 1, (0, -1.80, 1.52), "BEZIER", "EASE_IN_OUT")
key_vec(docc, "location", 66, (0, -2.15, 1.50), "BEZIER", "EASE_IN_OUT")
key_vec(docc, "location", 868, (0, -1.90, 1.30), "CONSTANT")
key_vec(docc, "location", 900, (0, -1.55, 1.35), "BEZIER", "EASE_IN_OUT")
mk = scene.timeline_markers.new("DOC_open", frame=1)
mk.camera = docc
mk = scene.timeline_markers.new("DOC_close", frame=868)
mk.camera = docc

camA = CAMS["CAM_A"]
key_vec(camA, "location", 370, cam_pos(15, 7.6, 1.22), "BEZIER", "EASE_IN_OUT")
key_vec(camA, "location", 476, cam_pos(11, 6.2, 1.05), "BEZIER", "EASE_IN_OUT")
mk = scene.timeline_markers.new("CAM_A_turn", frame=370)
mk.camera = camA
key_vec(camA, "location", 840, cam_pos(13, 6.9, 1.18), "BEZIER", "EASE_IN_OUT")
key_vec(camA, "location", 868, cam_pos(15, 7.6, 1.28), "BEZIER", "EASE_IN_OUT")
mk = scene.timeline_markers.new("CAM_A_close", frame=840)
mk.camera = camA
scene.camera = camA
cam = camA

# focus pulls: island drawer, then a slow marble-vein pan
t2 = CAM_TGTS["CAM_E2"]
key_vec(t2, "location", 476, (-0.35, -1.15, 0.62), "BEZIER", "EASE_IN_OUT")
key_vec(t2, "location", 512, (-0.35, -1.48, 0.56), "BEZIER", "EASE_IN_OUT")
key_vec(t2, "location", 566, (-0.35, -1.18, 0.62), "BEZIER", "EASE_IN_OUT")
t3 = CAM_TGTS["CAM_D2"]
key_vec(t3, "location", 566, (-0.9, -0.55, 0.95), "BEZIER", "EASE_IN_OUT")
key_vec(t3, "location", 648, (0.9, -0.55, 0.95), "BEZIER", "EASE_IN_OUT")
tG = CAM_TGTS["CAM_G"]
key_vec(tG, "location", 648, (-1.15, 1.25, 2.30), "BEZIER", "EASE_IN_OUT")
key_vec(tG, "location", 700, (-1.05, 1.25, 2.36), "BEZIER", "EASE_IN_OUT")
tH = CAM_TGTS["CAM_H"]
key_vec(tH, "location", 700, (0.0, 1.15, 1.85), "BEZIER", "EASE_IN_OUT")
key_vec(tH, "location", 756, (0.0, 1.15, 2.00), "BEZIER", "EASE_IN_OUT")
# -------------------------------------------------------------- floor grid --
import bmesh
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.004))
grid = bpy.context.active_object
grid.name = "floor_grid"
grid.scale = (3.6, 3.6, 1)
bpy.ops.object.transform_apply(scale=True)
bm = bmesh.new()
bm.from_mesh(grid.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=13, use_grid_fill=True)
bm.to_mesh(grid.data)
bm.free()
grid.data.materials.append(MAT["grid"])
gw = grid.modifiers.new("wire", "WIREFRAME")
gw.thickness = 0.0018
gw.use_replace = True
gw.use_boundary = True

# reflection catcher: barely-glossy dark sheet under the grids
refl = None
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.02))
refl = bpy.context.active_object
refl.name = "floor_reflect"
refl.scale = (9, 9, 1)
bpy.ops.object.transform_apply(scale=True)
rm = bpy.data.materials.new("phc_floor")
rm.use_nodes = True
rnt = rm.node_tree
rnt.nodes.clear()
rout = rnt.nodes.new("ShaderNodeOutputMaterial")
rgl = rnt.nodes.new("ShaderNodeBsdfGlossy")
rgl.inputs["Roughness"].default_value = 0.38
rgl.inputs["Color"].default_value = (0.55, 0.62, 0.70, 1.0)
rmx = rnt.nodes.new("ShaderNodeMixShader")
rdf = rnt.nodes.new("ShaderNodeBsdfDiffuse")
rdf.inputs["Color"].default_value = (0.002, 0.004, 0.008, 1.0)
rmx.inputs["Fac"].default_value = 0.18
rnt.links.new(rdf.outputs[0], rmx.inputs[1])
rnt.links.new(rgl.outputs[0], rmx.inputs[2])
rnt.links.new(rmx.outputs[0], rout.inputs[0])
refl.data.materials.append(rm)
for attr, val in (("use_raytracing", True),):
    try:
        setattr(scene.eevee, attr, val)
    except Exception:
        pass
try:
    scene.eevee.ray_tracing_options.resolution_scale = "1"
except Exception:
    pass

# ------------------------------------------------------------ aurora glows --
def aurora_glow(name, color, loc, sx, sz, strength):
    # NOTE: no transform_apply here — object-scale ellipse keeps local coords
    # normalized (+-0.5) for the spherical gradient, and apply broke rendering.
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = (radians(90), 0, 0)
    o.scale = (sx, sz, 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 1.0)
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"
    pw.inputs[1].default_value = 2.6
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    nt.links.new(mp.outputs[0], gr.inputs[0])
    nt.links.new(gr.outputs["Fac"], pw.inputs[0])
    nt.links.new(pw.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    o.data.materials.append(m)
    return o

aur1 = aurora_glow("aurora_indigo", INDIGO, (-1.3, 5.2, 1.5), 7.2, 4.6, 0.5)
aur2 = aurora_glow("aurora_teal", TEAL, (1.8, 5.6, 0.6), 5.6, 3.4, 0.32)
# one seamless drift cycle per loop
for f in range(1, F_END + 1, 6):
    t = 2 * pi * (f - 1) / F_END
    aur1.location.x = -1.3 + 0.55 * sin(t)
    aur1.keyframe_insert(data_path="location", frame=f, index=0)
    aur2.location.x = 1.8 - 0.7 * sin(t)
    aur2.keyframe_insert(data_path="location", frame=f, index=0)
    aur2.location.z = 0.6 + 0.25 * (1 - math.cos(t)) / 2
    aur2.keyframe_insert(data_path="location", frame=f, index=2)
for a in (aur1, aur2):
    for fc in all_fcurves(a):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ------------------------------------------------------------- the table ----
FRONT = -1
root = bpy.data.objects.new("set_root", None)
bpy.context.collection.objects.link(root)
face_y = -0.5
door_w = door_h = door_z = door_x = drw_w = drw_z = 0.0
STILE = 2.25 * IN

def grp_new(name, parent, loc=(0, 0, 0)):
    g = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(g)
    g.parent = parent
    g.location = loc
    return g

def shaker_door(name, w, h, ctr, parent):
    g = grp_new(name, parent, ctr)
    iw = w - 2 * STILE
    add_box(name + "_stL", (STILE, T, h), (-(w - STILE) / 2, 0, 0), parent=g)
    add_box(name + "_stR", (STILE, T, h), ((w - STILE) / 2, 0, 0), parent=g)
    add_box(name + "_rT", (iw - GAP, T, STILE), (0, 0, (h - STILE) / 2), parent=g)
    add_box(name + "_rB", (iw - GAP, T, STILE), (0, 0, -(h - STILE) / 2), parent=g)
    add_box(name + "_pnl", (iw - GAP, T * 0.38, h - 2 * STILE - GAP),
            (0, T * 0.2 * -FRONT, 0), parent=g)
    return g

def slab_door(name, w, h, ctr, parent):
    g = grp_new(name, parent, ctr)
    add_box(name + "_slab", (w, T, h), (0, 0, 0), parent=g)
    return g

def glass_door(name, w, h, ctr, parent):
    g = grp_new(name, parent, ctr)
    st = STILE * 0.8
    iw = w - 2 * st
    add_box(name + "_stL", (st, T, h), (-(w - st) / 2, 0, 0), parent=g)
    add_box(name + "_stR", (st, T, h), ((w - st) / 2, 0, 0), parent=g)
    add_box(name + "_rT", (iw - GAP, T, st), (0, 0, (h - st) / 2), parent=g)
    add_box(name + "_rB", (iw - GAP, T, st), (0, 0, -(h - st) / 2), parent=g)
    add_solid(name + "_glass", (iw - GAP, T * 0.15, h - 2 * st - GAP),
              (0, 0, 0), MAT["glass"], parent=g)
    return g

def knob(name, loc, parent):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.6 * IN,
                                        depth=1.0 * IN, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler.x = radians(90)
    o.data.materials.append(MAT["hw"])
    o.parent = parent
    return o

def bar_pull(name, loc, length, horizontal, parent):
    g = grp_new(name, parent, loc)
    add_solid(name + "_bar", (0.4 * IN, 0.4 * IN, length),
              (0, 1.2 * IN * FRONT, 0), MAT["hw"], parent=g)
    for s in (-1, 1):
        add_solid(name + "_p%+d" % s, (0.3 * IN, 1.2 * IN, 0.3 * IN),
                  (0, 0.6 * IN * FRONT, s * (length / 2 - 0.3 * IN)),
                  MAT["hw"], parent=g)
    if horizontal:
        g.rotation_euler.y = radians(90)
    return g




parts = []   # (obj_or_group, away_offset, order, home)

def unit(name, offset, order, loc=(0, 0, 0)):
    g = grp_new(name, root, loc)
    parts.append((g, offset, order, tuple(loc)))
    return g

def frustum(name, w0, d0, w1, d1, h, loc, mat, parent):
    import bmesh as bm_
    me = bpy.data.meshes.new(name)
    b = bm_.new()
    for (w, d, z) in ((w0, d0, 0.0), (w1, d1, h)):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            b.verts.new((sx * w / 2, sy * d / 2, z))
    b.verts.ensure_lookup_table()
    for f in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
              (0, 3, 2, 1), (4, 5, 6, 7)]:
        b.faces.new([b.verts[i] for i in f])
    b.to_mesh(me)
    b.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.data.materials.append(mat)
    o.data.materials.append(MAT["line"])
    w = o.modifiers.new("wire", "WIREFRAME")
    w.thickness = WIRE_T
    w.use_replace = False
    w.material_offset = 1
    w.use_boundary = True
    o.parent = parent
    return o

def ball(name, color, loc, parent):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14,
                                         radius=BALL_R, location=loc)
    o = bpy.context.active_object
    o.name = name
    m = face_material_v6("m_" + name, "Wood094", paint=color)
    # glossy phenolic: tighten the paint roughness on this instance
    for nd in m.node_tree.nodes:
        if nd.type == "BSDF_PRINCIPLED":
            nd.inputs["Roughness"].default_value = 0.07
    o.data.materials.append(m)
    o.data.materials.append(MAT["line"])
    w = o.modifiers.new("wire", "WIREFRAME")
    w.thickness = 0.0016
    w.use_replace = False
    w.material_offset = 1
    o.parent = parent
    return o

# ---- 0: floor shadow raft (thin dark sheet so the table grounds)
g = unit("stage", (0, 0, -0.3), 0)
add_box("raft", (5.4, 3.4, 0.04), (0, 0, -0.02), parent=g,
        face_mat=MAT["face_leather"])

# ---- legs (4 tapered)
LEG_IN_X, LEG_IN_Y = TBL_L / 2 - 0.28, TBL_W / 2 - 0.24
g = unit("legs", (0, 0, -0.5), 1)
for sx in (-1, 1):
    for sy in (-1, 1):
        frustum("leg_%+d%+d" % (sx, sy), 0.20, 0.20, 0.15, 0.15, 0.70,
                (sx * LEG_IN_X, sy * LEG_IN_Y, 0.0), MAT["face"], g)

# ---- body frame (aprons)
g = unit("frame", (0, 0, 0.5), 2)
add_box("apron_body", (TBL_L - 0.06, TBL_W - 0.06, 0.16),
        (0, 0, 0.70 - 0.08 + 0.08), parent=g)
for sx in (-1, 1):
    add_box("blind_%+d" % sx, (0.05, TBL_W - 0.10, 0.14),
            (sx * (TBL_L / 2 - 0.035), 0, 0.70), parent=g)

# ---- slate bed
g = unit("slate", (0, 0.7, 0.3), 3)
add_box("slate_bed", (PLAY_L + 0.24, PLAY_W + 0.24, 0.028),
        (0, 0, BED_H - 0.020), parent=g, face_mat=MAT["face_leather"])

# ---- felt (playfield + apron wrap)
g = unit("felt", (0, -0.7, 0.3), 4)
add_box("felt_bed", (PLAY_L + 0.26, PLAY_W + 0.26, 0.006),
        (0, 0, BED_H), parent=g, face_mat=MAT["face_felt"])

# ---- rails with cushions + top caps
g = unit("rails", (0, 0, 0.55), 5)
RW = (TBL_L - PLAY_L) / 2          # rail width ~0.18
for sy in (-1, 1):
    add_box("rail_y%+d" % sy, (TBL_L, RW, 0.045),
            (0, sy * (PLAY_W / 2 + RW / 2), RAIL_H - 0.0225), parent=g)
    add_box("cush_y%+d" % sy, (PLAY_L + 0.06, 0.045, 0.038),
            (0, sy * (PLAY_W / 2 + 0.0225), BED_H + 0.028), parent=g,
            face_mat=MAT["face_felt"])
for sx in (-1, 1):
    add_box("rail_x%+d" % sx, (RW, TBL_W - 2 * RW, 0.045),
            (sx * (PLAY_L / 2 + RW / 2), 0, RAIL_H - 0.0225), parent=g)
    add_box("cush_x%+d" % sx, (0.045, PLAY_W + 0.06, 0.038),
            (sx * (PLAY_L / 2 + 0.0225), 0, BED_H + 0.028), parent=g,
            face_mat=MAT["face_felt"])
# diamond sights (mother-of-pearl dots)
for sy in (-1, 1):
    for k in (-3, -2, -1, 1, 2, 3):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.011,
            depth=0.004, location=(k * PLAY_L / 8, sy * (PLAY_W / 2 + RW / 2),
                                   RAIL_H + 0.002))
        d = bpy.context.active_object
        d.name = "dia_y%+d_%d" % (sy, k)
        d.data.materials.append(MAT["face_ivory"])
        d.parent = g
for sx in (-1, 1):
    for k in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.011,
            depth=0.004, location=(sx * (PLAY_L / 2 + RW / 2), k * PLAY_W / 4,
                                   RAIL_H + 0.002))
        d = bpy.context.active_object
        d.name = "dia_x%+d_%d" % (sx, k)
        d.data.materials.append(MAT["face_ivory"])
        d.parent = g

# ---- pockets (6 leather drops with chrome irons)
g = unit("pockets", (0, 0, 0.45), 6)
PK = [(-TBL_L / 2 + 0.05, -TBL_W / 2 + 0.05), (0, -TBL_W / 2 + 0.02),
      (TBL_L / 2 - 0.05, -TBL_W / 2 + 0.05), (-TBL_L / 2 + 0.05, TBL_W / 2 - 0.05),
      (0, TBL_W / 2 - 0.02), (TBL_L / 2 - 0.05, TBL_W / 2 - 0.05)]
for i, (px, py) in enumerate(PK):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.062, minor_radius=0.013,
        major_segments=24, minor_segments=8, location=(px, py, RAIL_H - 0.005))
    t = bpy.context.active_object
    t.name = "pkt_iron_%d" % i
    t.data.materials.append(MAT["face_chrome"])
    t.parent = g
    bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.055, depth=0.10,
        location=(px, py, RAIL_H - 0.08))
    c = bpy.context.active_object
    c.name = "pkt_cup_%d" % i
    c.data.materials.append(MAT["face_leather"])
    c.parent = g

# ---- the rack (15 balls, triangle at the foot spot) + cue ball
BALL_COLS = [
    (0.85, 0.65, 0.05, 1.0), (0.05, 0.15, 0.55, 1.0), (0.70, 0.08, 0.06, 1.0),
    (0.25, 0.06, 0.35, 1.0), (0.85, 0.30, 0.04, 1.0), (0.05, 0.35, 0.12, 1.0),
    (0.42, 0.08, 0.10, 1.0), (0.02, 0.02, 0.02, 1.0), (0.85, 0.65, 0.05, 1.0),
    (0.05, 0.15, 0.55, 1.0), (0.70, 0.08, 0.06, 1.0), (0.25, 0.06, 0.35, 1.0),
    (0.85, 0.30, 0.04, 1.0), (0.05, 0.35, 0.12, 1.0), (0.42, 0.08, 0.10, 1.0),
]
FOOT_X = PLAY_L / 4
BZ = BED_H + BALL_R + 0.004
rack = unit("rack", (0, 0, 0.6), 7)
bi = 0
RACK_POS = []
for row in range(5):
    for k in range(row + 1):
        x = FOOT_X + row * BALL_R * 1.735
        y = (k - row / 2) * (BALL_R * 2.01)
        RACK_POS.append((x, y))
        ball("ball_%d" % bi, BALL_COLS[bi], (x, y, BZ), rack)
        bi += 1

cueg = unit("cueball", (-1.2, 0, 0.2), 8)
cue_ball = ball("cue_ball", (0.93, 0.91, 0.86, 1.0), (-PLAY_L / 4, 0, BZ), cueg)

# ---- cue stick (rests pointing at the cue ball, strikes on the break)
cs = unit("cue", (0, -1.0, 0.4), 9)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0065, depth=0.75,
    location=(-PLAY_L / 4 - 0.55, 0, BZ + 0.02))
sh = bpy.context.active_object
sh.name = "cue_shaft"
sh.rotation_euler = (0, radians(90), 0)
sh.data.materials.append(MAT["face_ivory"])
sh.parent = cs
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.011, depth=0.72,
    location=(-PLAY_L / 4 - 1.28, 0, BZ + 0.02))
bt = bpy.context.active_object
bt.name = "cue_butt"
bt.rotation_euler = (0, radians(90), 0)
bt.data.materials.append(MAT["face"])
bt.parent = cs

# ------------------------------------------------------ anchored dimensions --
dim_root = grp_new("dims", root)

font = None
for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf"):
    try:
        font = bpy.data.fonts.load(p)
        break
    except Exception:
        pass

LT = 0.0017   # annotation weight: finer than object lines
EXT = 2.0 * IN            # extension line length past the cabinet
OVER = 0.45 * IN          # overshoot past the dim line

def thin(name, a, b, parent, mat=None):
    """axis-aligned thin bar from a to b"""
    import mathutils
    va, vb = mathutils.Vector(a), mathutils.Vector(b)
    mid = (va + vb) / 2
    d = vb - va
    dims = (max(abs(d.x), LT), max(abs(d.y), LT), max(abs(d.z), LT))
    return add_solid(name, dims, mid, mat or MAT["dimline"], parent=parent)

def tick(name, loc, parent, plane="XZ"):
    """45-degree drafting tick crossing the dim line"""
    o = add_solid(name, (0.9 * IN, LT, LT), loc, MAT["dimline"], parent=parent)
    if plane == "XZ":
        o.rotation_euler.y = radians(45)
    else:                                   # dim line runs along Y, floor plane
        o.rotation_euler.z = radians(45)
    return o

def label(name, body, loc, parent, size=0.050, mat=None, align="CENTER"):
    c = bpy.data.curves.new(name, "FONT")
    c.body = body
    c.size = size
    c.align_x = align
    c.align_y = "CENTER"
    if font:
        c.font = font
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.data.materials.append(mat or MAT["dimline"])
    o.parent = parent
    b = o.constraints.new("TRACK_TO")      # billboard to camera
    b.target = cam
    b.track_axis = "TRACK_Z"
    b.up_axis = "UP_Y"
    return o

fy = -TBL_W / 2 - 0.10          # annotation plane off the near long rail

zt = RAIL_H + 0.30
for sgn in (-1, 1):
    thin("dl_ext%+d" % sgn, (sgn * TBL_L / 2, fy, RAIL_H + 0.05),
         (sgn * TBL_L / 2, fy, zt + 0.08), dim_root)
thin("dl_line", (-TBL_L / 2, fy, zt), (TBL_L / 2, fy, zt), dim_root)
for sgn in (-1, 1):
    tick("dl_tick%+d" % sgn, (sgn * TBL_L / 2, fy, zt), dim_root, "XZ")
label("dl_txt", "9'-0\"", (0, fy, zt + 0.11), dim_root)

xr = TBL_L / 2 + 0.28
for yy, nm in ((-PLAY_W / 2, "n"), (PLAY_W / 2, "f")):
    thin("dw_ext_" + nm, (TBL_L / 2 + 0.05, yy, BED_H), (xr + 0.07, yy, BED_H), dim_root)
thin("dw_line", (xr, -PLAY_W / 2, BED_H), (xr, PLAY_W / 2, BED_H), dim_root)
for yy in (-PLAY_W / 2, PLAY_W / 2):
    tick("dw_tick%.2f" % yy, (xr, yy, BED_H), dim_root, "YZ")
label("dw_txt", '50" PLAY', (xr + 0.16, 0, BED_H + 0.10), dim_root)

# --------------------------------------------------- part callouts (amber) --
import mathutils

def seg(name, a, b, parent, mat):
    """thin glowing segment between two 3D points"""
    va, vb = mathutils.Vector(a), mathutils.Vector(b)
    d = vb - va
    bpy.ops.mesh.primitive_cube_add(size=1, location=(va + vb) / 2)
    o = bpy.context.active_object
    o.name = name
    o.scale = (max(d.length, LT), LT, LT)
    bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = d.to_track_quat("X", "Z").to_euler()
    o.data.materials.append(mat)
    o.parent = parent
    return o

def callout(name, anchor, lab, text, f_show):
    g = grp_new("co_" + name, root)
    bpy.ops.mesh.primitive_cube_add(size=1, location=anchor)
    dot = bpy.context.active_object
    dot.name = "co_%s_dot" % name
    dot.scale = (0.011, 0.011, 0.011)
    bpy.ops.object.transform_apply(scale=True)
    dot.data.materials.append(MAT["hw_flat"])
    dot.parent = g
    seg("co_%s_lead" % name, anchor, lab, g, MAT["hw_flat"])
    ux = 0.02 if lab[0] < anchor[0] else -0.02
    t = label("co_%s_txt" % name, text, (lab[0] + (0.015 if ux < 0 else -0.015),
              lab[1], lab[2] + 0.028), g, size=0.031, mat=MAT["hw_flat"],
              align=("LEFT" if ux < 0 else "RIGHT"))
    # in / hold / out
    state(g, 1, a=0.0, r=1.0, interp="CONSTANT")
    state(g, f_show - 1, a=0.0, interp="CONSTANT")
    state(g, f_show, a=0.65, interp="CONSTANT")
    state(g, f_show + 2, a=0.2, interp="CONSTANT")
    state(g, f_show + 4, a=0.85, interp="CONSTANT")
    state(g, f_show + 78, a=0.85)
    state(g, f_show + 92, a=0.0)
    return g

callout("slate", (-0.9, -PLAY_W / 2 - 0.05, BED_H - 0.02), (-1.95, -1.35, 0.52),
        'SLATE BED · 3-PC · 1"', 132)
callout("felt", (0.4, -0.3, BED_H + 0.005), (1.55, -1.30, 0.98),
        'WORSTED CLOTH · TOURNAMENT GREEN', 148)
callout("cushion", (PLAY_L / 2 - 0.2, PLAY_W / 2 + 0.04, RAIL_H - 0.01),
        (2.05, 1.15, 1.05), 'K-66 CUSHIONS', 162)
callout("pocket", (-TBL_L / 2 + 0.08, -TBL_W / 2 + 0.08, RAIL_H - 0.02),
        (-2.15, -1.05, 1.00), 'LEATHER DROP POCKETS', 118)

# ------------------------------------------------------------- fx objects ---
scan = add_solid("scan_plane", (5.9, 4.4, 0.0016),
                 (0, 0, 0), MAT["scan"])
sw = scan.modifiers.new("wire", "WIREFRAME")   # outline gate, not a lightbox
sw.thickness = 0.0045
sw.use_replace = True
sw.use_boundary = True
rings = []
def ring_for(o):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.0035,
                                     major_segments=48, minor_segments=6,
                                     location=(o.location.x, o.location.y, 0.002))
    r = bpy.context.active_object
    r.name = "ring_" + o.name
    r.data.materials.append(MAT["ring"])
    rings.append(r)
    return r

# =================================================================
# TIMELINE (30 fps / 600 f)
#   1-40    scan sweep up, ghost carcass flickers on in its wake
#   40-215  carcass parts fly in hot, cool on landing, rings
#   215-255 dimensions materialize
#   255-300 shaker fronts materialize (first dressing)
#   300-470 swap cycle: -> slab -> glass -> shaker
#   470-530 drawer beat
#   535-600 dissolve to ghosts, scan sweeps down, explode drift
# =================================================================
GHOST_A = 0.09

# ---- scan gate: boot sweep to soffit height, closing wipe-down
state(scan, 1, r=0.15, a=0.0)
key_idx(scan, "location", 2, 1, -0.03)
state(scan, 64, a=0.0, interp="CONSTANT")
state(scan, 68, a=0.5, interp="CONSTANT")
key_idx(scan, "location", 2, 66, -0.03)
key_idx(scan, "location", 2, 112, 3.00, "BEZIER", "EASE_IN_OUT")
state(scan, 104, a=0.45)
state(scan, 114, a=0.0)
key_idx(scan, "location", 2, 864, 3.00)
state(scan, 864, a=0.0, interp="CONSTANT")
state(scan, 867, a=0.45, interp="CONSTANT")
key_idx(scan, "location", 2, 897, -0.03, "BEZIER", "EASE_IN_OUT")
state(scan, 892, a=0.35)
state(scan, 899, a=0.0)

# ---- units: ghost targets -> flights -> rings
def ghost_unit(g):
    gg = grp_new(g.name + "_ghost", root, tuple(g.location))
    for ch in g.children_recursive:
        if ch.type != "MESH":
            continue
        c = ch.copy()
        c.name = ch.name + "_gh"
        bpy.context.collection.objects.link(c)
        c.parent = gg
        c.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
        c.location = ch.location
        c.rotation_euler = ch.rotation_euler
        if c.material_slots:
            c.material_slots[0].link = "OBJECT"
            c.material_slots[0].material = MAT["ghostface"]
    return gg

GHOSTS = []
for g, off, order, home in parts:
    f_in = 96 + order * 13
    dur = 30
    away = (home[0] + off[0], home[1] + off[1], home[2] + off[2])

    if g.name in ("base_L", "base_R", "range", "upL", "upR", "hood",
                  "island_base", "island_top"):
        gh = ghost_unit(g)
        gf = 64 + order * 3
        state(gh, 1, r=1.0, a=0.0, interp="CONSTANT")
        ghost_flicker(gh, gf, GHOST_A)
        state(gh, f_in + dur - 1, a=GHOST_A, interp="CONSTANT")
        state(gh, f_in + dur + 3, a=0.0)
        GHOSTS.append((gh, order))

    key_vec(g, "location", 1, away)
    key_vec(g, "location", f_in, away, "CONSTANT")
    key_vec(g, "location", f_in + dur, home, "EXPO", "EASE_OUT")
    state(g, 1, a=0.0, r=0.0, interp="CONSTANT")
    state(g, f_in - 1, a=0.0, interp="CONSTANT")
    state(g, f_in + 3, a=1.0)
    state(g, f_in + dur + 2, r=0.0)
    state(g, f_in + dur + 30, r=1.0)
    key_hide(g, 1, True)
    key_hide(g, f_in - 1, True)
    key_hide(g, f_in, False)

    rg = ring_for(g)
    rg.location = (home[0], home[1] if g.name.startswith("island") else 0.4,
                   0.004)
    fl = f_in + dur
    state(rg, 1, r=0.55, a=0.0, interp="CONSTANT")
    key_vec(rg, "scale", fl - 1, (0.05, 0.05, 0.05))
    state(rg, fl - 1, a=0.0, interp="CONSTANT")
    state(rg, fl, a=0.85, interp="CONSTANT")
    key_vec(rg, "scale", fl + 18, (0.62, 0.62, 0.62), "BEZIER", "EASE_OUT")
    state(rg, fl + 18, a=0.0)

# ---- THE SHEET: the east-wall elevation at 1:1 behind its own wireframe
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, WALL_Y - 0.02, 1.50))
sheet = bpy.context.active_object
sheet.name = "doc_sheet"
sheet.rotation_euler = (radians(90), 0, 0)
sheet.scale = (3.45, 2.62, 1)
sheet.data.materials.append(plate_material("m_doc_sheet", PLATES + "plate_A.png"))
sheet.parent = root
state(sheet, 1, a=0.0, r=1.0, interp="CONSTANT")
state(sheet, 6, a=0.35, interp="CONSTANT")
state(sheet, 8, a=0.12, interp="CONSTANT")
state(sheet, 10, a=1.0, interp="CONSTANT")     # the document wakes
state(sheet, 396, a=1.0)
state(sheet, 452, a=0.10)                      # the turn absorbs it
state(sheet, 540, a=0.10)
state(sheet, 560, a=0.0)
state(sheet, 852, a=0.0, interp="CONSTANT")    # fold-back: the page returns
state(sheet, 856, a=0.85, interp="CONSTANT")
state(sheet, 893, a=0.85)
state(sheet, 899, a=0.0)                       # lights out — loop

# ---- extraction: a read-line sweeps the sheet, value boxes flicker on
read = add_solid("doc_readline", (3.45, 0.012, 0.012), (0, WALL_Y - 0.05, 2.85),
                 MAT["scan"])
state(read, 1, r=0.3, a=0.0, interp="CONSTANT")
state(read, 26, a=0.0, interp="CONSTANT")
state(read, 28, a=0.7, interp="CONSTANT")
key_idx(read, "location", 2, 26, 2.85)
key_idx(read, "location", 2, 62, 0.28, "BEZIER", "EASE_IN_OUT")
state(read, 58, a=0.6)
state(read, 64, a=0.0)

VBOXES = [(-1.30, 2.30, 0.55, 0.22), (0.15, 1.95, 0.42, 0.18),
          (1.25, 1.60, 0.50, 0.20), (-0.55, 1.10, 0.62, 0.22),
          (0.85, 0.62, 0.46, 0.18)]
for bi, (bx, bz, bw, bh) in enumerate(VBOXES):
    gv = grp_new("vbox_%d" % bi, root, (bx, WALL_Y - 0.06, bz))
    for sx, sw, sh, ox, oz in ((0, bw, 0.008, 0, bh / 2), (0, bw, 0.008, 0, -bh / 2),
                               (1, 0.008, bh, bw / 2, 0), (1, 0.008, bh, -bw / 2, 0)):
        add_solid("vb_%d_%d%.2f" % (bi, sx, ox + oz), (sw, 0.010, sh), (ox, 0, oz),
                  MAT["sky"], parent=gv)
    f0 = 30 + int((2.85 - bz) / (2.85 - 0.28) * 32)
    state(gv, 1, r=1.0, a=0.0, interp="CONSTANT")
    state(gv, f0, a=0.0, interp="CONSTANT")
    state(gv, f0 + 2, a=0.9, interp="CONSTANT")
    state(gv, f0 + 4, a=0.3, interp="CONSTANT")
    state(gv, f0 + 6, a=0.85, interp="CONSTANT")
    state(gv, 92, a=0.85)
    state(gv, 106, a=0.0)                       # boxes hand off to the boot

# ---- glass-upper LED panels wake with the lights
for nm in ("led_upL", "led_upR"):
    o = bpy.data.objects[nm]
    state(o, 1, a=0.0, r=1.0, interp="CONSTANT")
    state(o, 446, a=0.0, interp="CONSTANT")
    state(o, 464, a=0.9)
    state(o, 846, a=0.9)
    state(o, 886, a=0.0)

# ---- warm accent lights (under-cabinet + pendant) bloom on with the turn
uc_lights = []
for xc in (-1.28, 1.28):
    lo, ld = area_light("uc_%s" % xc, (xc, 1.10, 1.42),
                        (radians(180), 0, 0), 0.9, 0, (1.0, 0.78, 0.52))
    uc_lights.append(ld)
plo, pld = area_light("pendant_l", (0, -0.57, 1.98),
                      (radians(180), 0, 0), 1.8, 0, (1.0, 0.80, 0.55))
uc_lights.append(pld)
for ld in uc_lights:
    key_light(ld, 1, 0.0)
    key_light(ld, 404, 0.0)
    key_light(ld, 458, 26.0)
    key_light(ld, 848, 26.0)
    key_light(ld, 888, 0.0)

# ---- dims materialize (survive the turn, flip green at master file)
state(dim_root, 1, a=0.0, r=1.0)
state(dim_root, 270, a=0.0, interp="CONSTANT")
for i, ch in enumerate(dim_root.children):
    f0 = 272 + (i % 7) * 4
    state(ch, f0, a=0.0, interp="CONSTANT")
    state(ch, f0 + 3, a=0.9, interp="CONSTANT")
    state(ch, f0 + 5, a=0.35, interp="CONSTANT")
    state(ch, f0 + 8, a=1.0, interp="CONSTANT")
state(dim_root, 866, a=1.0)
state(dim_root, 878, a=0.0)
state(dim_root, 826, c=0.0)
state(dim_root, 838, c=1.0)
state(dim_root, 862, c=1.0)
state(dim_root, 874, c=0.0)

# ---- review stamps: the feature tour
def stamp(text, loc, f0, f1, mat, size=0.052):
    t = label("stamp_%d" % f0, text, loc, root, size=size, mat=mat, align="LEFT")
    state(t, 1, a=0.0, r=1.0, interp="CONSTANT")
    state(t, f0 - 1, a=0.0, interp="CONSTANT")
    state(t, f0, a=0.6, interp="CONSTANT")
    state(t, f0 + 2, a=0.2, interp="CONSTANT")
    state(t, f0 + 4, a=0.9, interp="CONSTANT")
    state(t, f1 - 10, a=0.9)
    state(t, f1, a=0.0)
    return t

stamp("SHAKER · EDGECOMB GRAY HC-173", (1.35, 0.72, 1.30), 308, 368, MAT["sky"])
stamp("GNA TEXTURED GLASS · VERIFIED", (-2.05, 1.05, 2.62), 652, 700, MAT["sky"])
stamp("MATTE ZINC · NO VERTICAL STRAPS", (0.85, 1.05, 2.55), 704, 752, MAT["sky"])
stamp("CALACATTA BRASIL · BALTIC BIRCH", (1.45, -1.15, 1.25), 760, 808, MAT["sky"])
stamp("MASTER FILE · SET WITH RECEIPTS", (-1.15, 0.72, 3.18), 824, 868,
      MAT["done"], size=0.070)

# ---- hero drawer beat: birch box glides out under the macro
hero_g = bpy.data.objects["hero_drawer"]
key_vec(hero_g, "location", 476, (0, 0, 0), "BEZIER", "EASE_IN_OUT")
key_vec(hero_g, "location", 508, (0, -0.44, 0), "BEZIER", "EASE_IN_OUT")
key_vec(hero_g, "location", 528, (0, -0.44, 0), "BEZIER", "EASE_IN_OUT")
key_vec(hero_g, "location", 558, (0, 0, 0), "BEZIER", "EASE_IN_OUT")

# ---- end of loop: dissolve in place, ghost cameo, scan wipes down
for g, off, order, home in parts:
    fe = 854 + (12 - order) * 2
    state(g, fe, a=1.0)
    state(g, min(fe + 12, 897), a=0.0)
    key_idx(g, "location", 2, fe, home[2])
    key_idx(g, "location", 2, min(fe + 14, 898), home[2] + 0.04,
            "BEZIER", "EASE_IN")
    key_hide(g, min(fe + 13, 898), True)
for gh, order in GHOSTS:
    f_g = 862 + order * 2
    state(gh, f_g - 1, a=0.0, interp="CONSTANT")
    ghost_flicker(gh, f_g, GHOST_A)
    state(gh, 898, a=0.0, interp="CONSTANT")

# G channel (wood factor) defaults to 1.0 on fresh objects — zero it globally
# AFTER all animation so nothing renders walnut outside the reveal window.
for ob in bpy.data.objects:
    if ob.type in {"MESH", "FONT", "CURVE"}:
        key_idx(ob, "color", 1, 1, 0.0)
        key_idx(ob, "color", 2, 1, 0.0)

# ================================================================ compost ==
# 5.x: compositor lives in a node group on scene.compositing_node_group
nt = None
comp = None
if hasattr(scene, "compositing_node_group"):
    ng = bpy.data.node_groups.new("phc_comp", "CompositorNodeTree")
    scene.compositing_node_group = ng
    nt = ng
    try:
        ng.interface.new_socket("Image", in_out="OUTPUT",
                                socket_type="NodeSocketColor")
    except Exception:
        pass
    comp = nt.nodes.new("NodeGroupOutput")
else:
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()
    comp = nt.nodes.new("CompositorNodeComposite")
rl = nt.nodes.new("CompositorNodeRLayers")
glare = nt.nodes.new("CompositorNodeGlare")
for prop in ("glare_type", "mode"):
    if hasattr(glare, prop):
        for val in ("BLOOM", "FOG_GLOW"):
            try:
                setattr(glare, prop, val)
                break
            except Exception:
                continue
        break
for attr, val in (("quality", "HIGH"), ("mix", -0.55), ("threshold", 0.9),
                  ("size", 7), ("strength", 0.6), ("smoothness", 0.1)):
    try:
        setattr(glare, attr, val)
    except Exception:
        pass
for nm, val in (("Threshold", 1.15), ("Strength", 0.30), ("Smoothness", 0.12),
                ("Size", 0.42)):
    try:
        glare.inputs[nm].default_value = val
    except Exception:
        pass
nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
nt.links.new(glare.outputs[0], comp.inputs[0])
# (vignette is applied at encode time via ffmpeg — compositor APIs drift too
# much across 5.x to build it here reliably)

# ================================================================= output ==
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

if argv and argv[0] == "--test":
    scene.render.resolution_percentage = 25 if SS == 2 else 50
    for f in argv[1:]:
        scene.frame_set(int(f))
        scene.render.filepath = OUT_DIR + "out/test_%04d.png" % int(f)
        bpy.ops.render.render(write_still=True)
elif argv and argv[0] == "--render":
    scene.render.resolution_percentage = 100
    scene.render.filepath = OUT_DIR + "frames/f_"
    bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + "cabinet.blend")
    bpy.ops.render.render(animation=True)
elif argv and argv[0] == "--save":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + "cabinet.blend")

print("PHC cabinet v2 done. engine=%s res=%dx%d" %
      (scene.render.engine, scene.render.resolution_x, scene.render.resolution_y))
