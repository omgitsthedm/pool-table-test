# render_game.py — photoreal 8-ball game film from a frozen pooltool game.json
#
# Scene: 7-ft bar table built to pooltool's exact playfield geometry (cushion
# noses on the physics lines, pocket mouths at the physics pockets), textured
# worsted felt, walnut wood grain, chrome irons, phenolic balls with stripe
# bands, two cues, and an out-of-focus room (floor/walls/ceiling + billiard
# lamp). Import: every shot's 60 Hz ball trajectories + integrated roll
# quaternions become keyframes; cues stroke each shot; cameras cut per shot.
#
#   Look-dev stills:  Blender -b -P render_game.py -- --test 30 400 2000
#   Full render:      Blender -b -P render_game.py -- --render
import bpy
import bmesh
import json
import math
import os
import sys
from math import radians, atan2, sin, cos

# ---------------------------------------------------------------- config ----
OUT = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEX = OUT + "assets/tex/"
GAME = json.load(open(OUT + "game.json"))

FPS = 30
GAP_F = 48                 # frames between shots (cue approach)
INTRO_F, OUTRO_F = 45, 75
RES = (1280, 720)

W = GAME["meta"]["table"]["w"]          # 0.9906
L = GAME["meta"]["table"]["l"]          # 1.9812
BALL_R = GAME["meta"]["ball_R"]
BED = 0.79                              # felt surface height (visual)
NOSE_H = 0.037                          # cushion nose height above felt
RAIL_W = 0.145                          # wood rail width
RAIL_TOP = BED + 0.052
POCKETS = {k: v for k, v in GAME["meta"]["pockets"].items()}

FELT = (0.010, 0.112, 0.046, 1.0)
WALNUT = (0.235, 0.125, 0.065, 1.0)
FLOOR_TINT = (0.52, 0.38, 0.26, 1.0)
PLASTER = (0.062, 0.056, 0.048, 1.0)
BALL_COLORS = {
    "cue": (0.93, 0.91, 0.85), "8": (0.015, 0.015, 0.018),
    "1": (0.95, 0.72, 0.05), "2": (0.03, 0.12, 0.55), "3": (0.75, 0.06, 0.05),
    "4": (0.22, 0.04, 0.35), "5": (0.90, 0.28, 0.03), "6": (0.03, 0.32, 0.10),
    "7": (0.45, 0.07, 0.10),
    "9": (0.95, 0.72, 0.05), "10": (0.03, 0.12, 0.55), "11": (0.75, 0.06, 0.05),
    "12": (0.22, 0.04, 0.35), "13": (0.90, 0.28, 0.03), "14": (0.03, 0.32, 0.10),
    "15": (0.45, 0.07, 0.10),
}
STRIPES = {"9", "10", "11", "12", "13", "14", "15"}


def bl(x, y, z):
    """pooltool table coords -> Blender world (table centered at origin)."""
    return (x - W / 2, y - L / 2, BED + z)


# ---------------------------------------------------------------- scene -----
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
             bpy.data.cameras, bpy.data.curves, bpy.data.lights):
    for x in list(coll):
        try:
            coll.remove(x)
        except Exception:
            pass

scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.fps = FPS
scene.frame_start = 1

engines = [e.identifier for e in
           bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
scene.render.engine = next((e for e in engines if "EEVEE" in e), "CYCLES")
try:
    scene.eevee.use_raytracing = True
except Exception:
    pass
try:
    scene.view_settings.view_transform = "AgX"     # filmic-style grade
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.010, 0.008, 0.006, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.5

# ------------------------------------------------------------- materials ----


def principled(name, base, rough=0.5, metal=0.0, coat=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base[:3], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    for nm, v in (("Coat Weight", coat), ("Clearcoat", coat),
                  ("Sheen Weight", sheen), ("Sheen", sheen)):
        try:
            bsdf.inputs[nm].default_value = v
        except Exception:
            pass
    return m


def wood_material(name, tint, scale=1.0, rough_mul=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])

    def img(suffix, non_color=False):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(
            TEX + "Wood049/Wood049_2K-JPG_" + suffix + ".jpg", check_existing=True)
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.3
        nt.links.new(mp.outputs[0], node.inputs["Vector"])
        return node

    col = img("Color")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[7].default_value = (*tint[:3], 1.0)
    nt.links.new(col.outputs["Color"], mix.inputs[6])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    rough = img("Roughness", True)
    rm = nt.nodes.new("ShaderNodeMath")
    rm.operation = "MULTIPLY"
    rm.inputs[1].default_value = rough_mul
    rm.use_clamp = True
    nt.links.new(rough.outputs["Color"], rm.inputs[0])
    nt.links.new(rm.outputs[0], bsdf.inputs["Roughness"])
    nrm = img("NormalGL", True)
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.55
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])
    return m


def felt_material(name):
    """Deep worsted cloth: matte, sheened, finely bumped."""
    m = principled(name, FELT, rough=0.88, sheen=0.35)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1400.0
    noise.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def ball_material(bid):
    base = BALL_COLORS[bid]
    if bid not in STRIPES:
        m = principled("ball_" + bid, base, rough=0.05, coat=0.6)
        return m
    # stripe: white ball, colored equator band in the ball's own (Generated)
    # frame so the band rolls with the ball
    m = principled("ball_" + bid, (0.93, 0.91, 0.85), rough=0.05, coat=0.6)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    dist = nt.nodes.new("ShaderNodeMath")
    dist.operation = "ABSOLUTE"
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = 0.5
    nt.links.new(sep.outputs["Z"], sub.inputs[0])
    nt.links.new(sub.outputs[0], dist.inputs[0])
    band = nt.nodes.new("ShaderNodeMath")
    band.operation = "LESS_THAN"
    band.inputs[1].default_value = 0.185
    nt.links.new(dist.outputs[0], band.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.93, 0.91, 0.85, 1.0)
    mix.inputs[7].default_value = (*base, 1.0)
    nt.links.new(band.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


M_FELT = felt_material("felt")
M_WOOD = wood_material("rail_wood", WALNUT, scale=1.4, rough_mul=0.9)
M_FLOOR = wood_material("floor_wood", FLOOR_TINT, scale=0.45, rough_mul=1.15)
M_PLASTER = principled("plaster", PLASTER, rough=0.92)
M_CEIL = principled("ceiling", (0.035, 0.032, 0.028), rough=0.95)
M_CHROME = principled("chrome", (0.75, 0.76, 0.78), rough=0.22, metal=1.0)
M_LEATHER = principled("leather", (0.045, 0.028, 0.018), rough=0.6)
M_LAMPSHADE = principled("lampshade", (0.02, 0.10, 0.05), rough=0.4, metal=0.3)
M_CUE_SHAFT = principled("cue_shaft", (0.72, 0.58, 0.38), rough=0.35)
M_CUE_BUTT_A = wood_material("cue_butt_a", (0.22, 0.10, 0.05), scale=3.0)
M_CUE_BUTT_B = principled("cue_butt_b", (0.05, 0.05, 0.06), rough=0.3)


# --------------------------------------------------------------- helpers ----
def box(name, dims, loc, mat, rot=None, bevel=0.0015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def shade_smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


# ----------------------------------------------------------------- table ----
# bed + felt
box("bed", (W + 2 * RAIL_W, L + 2 * RAIL_W, 0.05), (0, 0, BED - 0.028), M_WOOD)
box("felt_bed", (W + 0.10, L + 0.10, 0.012), (0, 0, BED - 0.006), M_FELT,
    bevel=0)

# cushion noses (felt) — segmented between pocket mouths, ON the physics lines
CORNER_GAP = 0.091          # from pooltool cushion segment endpoints
SIDE_GAP = 0.075


def cushion(name, p1, p2, axis):
    length = math.dist(p1, p2)
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    dims = (length, 0.045, NOSE_H + 0.012) if axis == "x" else (0.045, length, NOSE_H + 0.012)
    off = 0.0225 if axis == "x" else 0.0225
    if axis == "x":
        loc = bl(mid[0], mid[1], 0)[0:2] + ()
        c = box(name, dims, (mid[0] - W / 2, mid[1] - L / 2 + (off if mid[1] > L / 2 else -off), BED + (NOSE_H + 0.012) / 2 - 0.004), M_FELT, bevel=0.004)
    else:
        c = box(name, dims, (mid[0] - W / 2 + (off if mid[0] > W / 2 else -off), mid[1] - L / 2, BED + (NOSE_H + 0.012) / 2 - 0.004), M_FELT, bevel=0.004)
    return c


# long rails (x = 0 and x = W), split by side pockets
for xs, side in ((0.0, -1), (W, 1)):
    cushion("cush_%s_b" % side, (xs, CORNER_GAP), (xs, L / 2 - SIDE_GAP), "y")
    cushion("cush_%s_t" % side, (xs, L / 2 + SIDE_GAP), (xs, L - CORNER_GAP), "y")
# end rails (y = 0 and y = L)
cushion("cush_bot", (CORNER_GAP, 0.0), (W - CORNER_GAP, 0.0), "x")
cushion("cush_top", (CORNER_GAP, L), (W - CORNER_GAP, L), "x")

# wood rails outside the cushions, same segmentation
def rail(name, p1, p2, axis):
    length = math.dist(p1, p2) + 0.06
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    if axis == "y":
        sgn = 1 if mid[0] > W / 2 else -1
        box(name, (RAIL_W, length, RAIL_TOP - BED + 0.02),
            (mid[0] - W / 2 + sgn * (RAIL_W / 2 + 0.045), mid[1] - L / 2,
             (RAIL_TOP + BED) / 2 - 0.008), M_WOOD, bevel=0.004)
    else:
        sgn = 1 if mid[1] > L / 2 else -1
        box(name, (length, RAIL_W, RAIL_TOP - BED + 0.02),
            (mid[0] - W / 2, mid[1] - L / 2 + sgn * (RAIL_W / 2 + 0.045),
             (RAIL_TOP + BED) / 2 - 0.008), M_WOOD, bevel=0.004)


for xs, side in ((0.0, "l"), (W, "r")):
    rail("rail_%s_b" % side, (xs, CORNER_GAP), (xs, L / 2 - SIDE_GAP), "y")
    rail("rail_%s_t" % side, (xs, L / 2 + SIDE_GAP), (xs, L - CORNER_GAP), "y")
rail("rail_bot", (CORNER_GAP, 0.0), (W - CORNER_GAP, 0.0), "x")
rail("rail_top", (CORNER_GAP, L), (W - CORNER_GAP, L), "x")

# pocket irons + leather cups at the physics pocket centers
for pid, c in POCKETS.items():
    px, py = c[0], c[1]
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.066, minor_radius=0.011, major_segments=28,
        minor_segments=10, location=(px - W / 2, py - L / 2, RAIL_TOP - 0.006))
    t = bpy.context.active_object
    t.name = "iron_" + pid
    t.data.materials.append(M_CHROME)
    shade_smooth(t)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=20, radius=0.058, depth=0.16,
        location=(px - W / 2, py - L / 2, BED - 0.05))
    cup = bpy.context.active_object
    cup.name = "cup_" + pid
    cup.data.materials.append(M_LEATHER)

# aprons + legs (bar-box cabinet)
box("apron", (W + 2 * RAIL_W + 0.02, L + 2 * RAIL_W + 0.02, 0.22),
    (0, 0, BED - 0.17), M_WOOD, bevel=0.004)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("leg_%+d%+d" % (sx, sy), (0.16, 0.16, BED - 0.26),
            (sx * (W / 2 + 0.10), sy * (L / 2 + 0.10), (BED - 0.26) / 2),
            M_WOOD, bevel=0.006)

# diamond sights
for sy in (-1, 1):
    for k in (-3, -2, -1, 1, 2, 3):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12, radius=0.009, depth=0.003,
            location=(sy * (W / 2 + RAIL_W / 2 + 0.045) * 1.0, k * L / 8,
                      RAIL_TOP + 0.010))
        d = bpy.context.active_object
        d.name = "dia_%d_%d" % (sy, k)
        d.data.materials.append(principled("mop_%d_%d" % (sy, k),
                                           (0.85, 0.84, 0.80), rough=0.25,
                                           coat=0.4))
for sx in (-1, 1):
    for k in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12, radius=0.009, depth=0.003,
            location=(k * W / 4, sx * (L / 2 + RAIL_W / 2 + 0.045),
                      RAIL_TOP + 0.010))
        d = bpy.context.active_object
        d.data.materials.append(bpy.data.materials["mop_-1_-3"])

# ------------------------------------------------------------------ room ----
box("floor", (10, 12, 0.05), (0, 0, -0.028), M_FLOOR, bevel=0)
box("wall_n", (10, 0.1, 3.2), (0, 5.5, 1.6), M_PLASTER, bevel=0)
box("wall_s", (10, 0.1, 3.2), (0, -5.5, 1.6), M_PLASTER, bevel=0)
box("wall_e", (0.1, 12, 3.2), (4.6, 0, 1.6), M_PLASTER, bevel=0)
box("wall_w", (0.1, 12, 3.2), (-4.6, 0, 1.6), M_PLASTER, bevel=0)
box("ceiling", (10, 12, 0.1), (0, 0, 3.1), M_CEIL, bevel=0)
# wainscot rail on the near walls for depth
box("wainscot_n", (10, 0.06, 0.10), (0, 5.44, 1.0), M_WOOD, bevel=0.002)
box("wainscot_e", (0.06, 12, 0.10), (4.54, 0, 1.0), M_WOOD, bevel=0.002)

# billiard lamp: three shades over the table + emitters
def lampshade(x_off):
    box("shade_%d" % x_off, (0.34, 0.34, 0.16), (0, x_off * 0.62, 1.86),
        M_LAMPSHADE, bevel=0.006)
    inner = principled("lamp_in_%d" % x_off, (1, 1, 1), rough=0.5)
    nt = inner.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.82, 0.58, 1.0)
    em.inputs["Strength"].default_value = 30.0
    out = nt.nodes["Material Output"]
    nt.links.new(em.outputs[0], out.inputs[0])
    box("bulbplate_%d" % x_off, (0.28, 0.28, 0.012), (0, x_off * 0.62, 1.795),
        inner, bevel=0)
    ld = bpy.data.lights.new("lamp_%d" % x_off, "AREA")
    ld.shape = "SQUARE"
    ld.size = 0.32
    ld.energy = 150
    ld.color = (1.0, 0.85, 0.62)
    lo = bpy.data.objects.new("lamp_%d" % x_off, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (0, x_off * 0.62, 1.82)
    lo.rotation_euler = (0, 0, 0)


for k in (-1, 0, 1):
    lampshade(k)
box("lamp_bar", (0.06, 1.7, 0.03), (0, 0, 1.97), M_LAMPSHADE, bevel=0.004)
for k in (-1, 1):
    box("lamp_rod_%d" % k, (0.015, 0.015, 1.25), (0, k * 0.62, 2.46),
        M_LAMPSHADE, bevel=0)

fill = bpy.data.lights.new("fill", "AREA")
fill.size = 4.0
fill.energy = 280
fill.color = (0.75, 0.82, 1.0)
fo = bpy.data.objects.new("fill", fill)
bpy.context.collection.objects.link(fo)
fo.location = (-3.2, -2.5, 2.6)
fo.rotation_euler = (radians(-35), radians(-25), 0)

rim = bpy.data.lights.new("rim", "AREA")
rim.size = 2.2
rim.energy = 210
rim.color = (1.0, 0.9, 0.75)
ro = bpy.data.objects.new("rim", rim)
bpy.context.collection.objects.link(ro)
ro.location = (3.4, 3.0, 2.2)
ro.rotation_euler = (radians(-40), radians(30), 0)

# ----------------------------------------------------------------- balls ----
balls = {}
for bid in BALL_COLORS:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20,
                                         radius=BALL_R, location=(0, 0, -1))
    o = bpy.context.active_object
    o.name = "ball_" + bid
    o.data.materials.append(ball_material(bid))
    shade_smooth(o)
    o.rotation_mode = "QUATERNION"
    balls[bid] = o

# ------------------------------------------------------------------ cues ----
def make_cue(name, butt_mat):
    g = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(g)
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.0065, radius2=0.010,
                                    depth=0.74, location=(0.37, 0, 0))
    sh = bpy.context.active_object
    sh.name = name + "_shaft"
    sh.rotation_euler = (0, radians(90), 0)
    sh.data.materials.append(M_CUE_SHAFT)
    shade_smooth(sh)
    sh.parent = g
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.010, radius2=0.0145,
                                    depth=0.72, location=(1.10, 0, 0))
    bt = bpy.context.active_object
    bt.name = name + "_butt"
    bt.rotation_euler = (0, radians(90), 0)
    bt.data.materials.append(butt_mat)
    shade_smooth(bt)
    bt.parent = g
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0067, depth=0.012,
                                        location=(-0.006, 0, 0))
    tip = bpy.context.active_object
    tip.name = name + "_tip"
    tip.rotation_euler = (0, radians(90), 0)
    tip.data.materials.append(principled(name + "_tipm", (0.25, 0.42, 0.75),
                                         rough=0.8))
    tip.parent = g
    g.location = (0, 0, -2)
    return g


cue_a = make_cue("cue_ray", M_CUE_BUTT_A)
cue_b = make_cue("cue_sam", M_CUE_BUTT_B)
CUES = {"Ray": cue_a, "Sam": cue_b}

# ------------------------------------------------------------- animation ----
def key_loc(o, f, loc):
    o.location = loc
    o.keyframe_insert("location", frame=f)


def key_quat(o, f, q):
    o.rotation_quaternion = q
    o.keyframe_insert("rotation_quaternion", frame=f)


def linearize(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    fcs = []
    if hasattr(act, "fcurves"):
        try:
            fcs = list(act.fcurves)
        except Exception:
            fcs = []
    if not fcs:
        for layer in getattr(act, "layers", []):
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    fcs.extend(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def shot_trim(shot):
    """last sample index where anything still moves, + small settle pad"""
    last = 0
    for bid, tr in shot["balls"].items():
        rs = tr["r"]
        for i in range(1, len(rs)):
            dx = abs(rs[i][0] - rs[i - 1][0]) + abs(rs[i][1] - rs[i - 1][1])
            if dx > 2.5e-5:
                last = max(last, i)
    return min(last + 14, max(len(tr["t"]) for tr in shot["balls"].values()) - 1)


frame = INTRO_F + 1
SHOT_STARTS = []
cue_dirs = []

for si, shot in enumerate(GAME["shots"]):
    trim = shot_trim(shot)
    # cue direction from the cue ball's first real displacement
    ctr = shot["balls"]["cue"]
    d = (1.0, 0.0)
    for i in range(1, min(30, len(ctr["r"]))):
        dx = ctr["r"][i][0] - ctr["r"][0][0]
        dy = ctr["r"][i][1] - ctr["r"][0][1]
        if abs(dx) + abs(dy) > 1e-4:
            n = math.hypot(dx, dy)
            d = (dx / n, dy / n)
            break
    cue_dirs.append(d)
    SHOT_STARTS.append((frame, si, shot, trim, d))
    frame += (trim // 2) + GAP_F        # 60 Hz data -> 30 fps keys

F_END = frame + OUTRO_F
scene.frame_end = F_END

# ball keyframes
for start, si, shot, trim, d in SHOT_STARTS:
    for bid, tr in shot["balls"].items():
        o = balls[bid]
        n = min(trim + 1, len(tr["t"]))
        for i in range(0, n, 2):
            f = start + i // 2
            x, y, z = tr["r"][i]
            key_loc(o, f, bl(x, y, z))
            q = tr["q"][i]
            key_quat(o, f, (q[0], q[1], q[2], q[3]))

for o in balls.values():
    linearize(o)

# cue stick choreography per shot
STRIKE_BACK = 0.055
for start, si, shot, trim, d in SHOT_STARTS:
    cue = CUES.get(shot["player"], cue_a)
    other = cue_b if cue is cue_a else cue_a
    c0 = shot["balls"]["cue"]["r"][0]
    bx, by, bz = bl(c0[0], c0[1], c0[2])
    ang = atan2(d[1], d[0])
    cue.rotation_euler = (0, radians(-4), 0)
    tip_off = 0.015

    def cue_pos(back, lift=0.0):
        return (bx - d[0] * (tip_off + back), by - d[1] * (tip_off + back),
                bz + 0.01 + lift)

    ready_f = start - GAP_F + 10
    key_loc(cue, ready_f - 6, cue_pos(0.30, 0.25))
    cue.keyframe_insert("rotation_euler", frame=ready_f - 6)
    cue.rotation_euler = (0, radians(-4), ang)
    cue.keyframe_insert("rotation_euler", frame=ready_f)
    key_loc(cue, ready_f, cue_pos(0.06))
    key_loc(cue, start - 10, cue_pos(0.06))
    key_loc(cue, start - 4, cue_pos(STRIKE_BACK + 0.06))
    key_loc(cue, start, cue_pos(0.002))
    key_loc(cue, start + 6, cue_pos(0.09))
    key_loc(cue, start + 22, cue_pos(0.30, 0.18))
    key_loc(cue, start + 46, (2.9 if d[0] < 0 else -2.9, -3.6, 0.5))
    # park the idle cue out of frame
    key_loc(other, ready_f, (3.6, -4.4, 0.4))

for c in (cue_a, cue_b):
    linearize(c)

# ----------------------------------------------------------------- camera ---
def make_cam(name, fstop=3.2, lens=50):
    tgt = bpy.data.objects.new(name + "_t", None)
    bpy.context.collection.objects.link(tgt)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
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


cam_low, t_low = make_cam("cam_low", 2.5, 62)
cam_side, t_side = make_cam("cam_side", 3.5, 45)
cam_three, t_three = make_cam("cam_three", 3.2, 40)
cam_top, t_top = make_cam("cam_top", 5.0, 35)
scene.camera = cam_three

CYCLE = [cam_three, cam_low, cam_side, cam_low, cam_top]
T_OF = {cam_low: t_low, cam_side: t_side, cam_three: t_three, cam_top: t_top}

# opening establisher
key_loc(cam_three, 1, (2.6, -3.1, 1.75))
key_loc(t_three, 1, (0, 0, BED))
mk = scene.timeline_markers.new("open", frame=1)
mk.camera = cam_three
key_loc(cam_three, INTRO_F + 20, (2.35, -2.85, 1.62))

for start, si, shot, trim, d in SHOT_STARTS:
    cam = cam_low if si == 0 else CYCLE[si % len(CYCLE)]
    tgt = T_OF[cam]
    c0 = shot["balls"]["cue"]["r"][0]
    bx, by, bz = bl(c0[0], c0[1], c0[2])
    tgt_ball = shot.get("target")
    tb = shot["balls"].get(tgt_ball)
    if tb:
        t0 = bl(*tb["r"][0])
    else:
        t0 = (0, 0, BED)
    mid = ((bx + t0[0]) / 2, (by + t0[1]) / 2, BED + 0.02)
    f_cut = start - GAP_F + 8
    mk = scene.timeline_markers.new("s%d" % si, frame=max(1, f_cut))
    mk.camera = cam
    ang = atan2(d[1], d[0])
    if cam is cam_low:
        pos = (bx - d[0] * 1.15, by - d[1] * 1.15, BED + 0.18)
        pos2 = (bx - d[0] * 1.05, by - d[1] * 1.05, BED + 0.22)
    elif cam is cam_side:
        side = 1 if by < 0 else -1
        pos = (2.45, side * 0.9, BED + 0.55)
        pos2 = (2.3, side * 0.7, BED + 0.5)
    elif cam is cam_top:
        pos = (0.35, -0.3, BED + 2.05)
        pos2 = (0.3, 0.2, BED + 2.05)
    else:
        sidex = 1 if bx < 0 else -1
        pos = (sidex * 2.2, -2.3, 1.45)
        pos2 = (sidex * 2.05, -2.05, 1.38)
    dur = (trim // 2) + GAP_F
    key_loc(cam, f_cut, pos)
    key_loc(cam, f_cut + dur, pos2)
    key_loc(tgt, f_cut, mid)
    key_loc(tgt, f_cut + int(dur * 0.4), (t0[0], t0[1], BED + 0.02))

# closing: pull wide on the winner's 8-ball drop
key_loc(cam_three, F_END - OUTRO_F + 6, (2.7, -3.2, 1.8))
key_loc(cam_three, F_END, (3.1, -3.7, 2.05))
key_loc(t_three, F_END - OUTRO_F + 6, (0, 0, BED))
mk = scene.timeline_markers.new("close", frame=F_END - OUTRO_F + 6)
mk.camera = cam_three

# ================================================================= output ==
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
print("film frames:", F_END, "(%.1f s)" % (F_END / FPS))

if argv and argv[0] == "--test":
    for f in argv[1:]:
        scene.frame_set(int(f))
        scene.render.filepath = OUT + "out/test_%05d.png" % int(f)
        bpy.ops.render.render(write_still=True)
elif argv and argv[0] == "--render":
    if len(argv) >= 3:
        scene.frame_start = int(argv[1])
        scene.frame_end = int(argv[2])
    scene.render.filepath = OUT + "frames/f_"
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "pool.blend")
    bpy.ops.render.render(animation=True)
elif argv and argv[0] == "--save":
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "pool.blend")
