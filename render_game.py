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
EVENTS = _load_events = __import__("json").load(open(OUT + "pocket_events.json"))
SLOMO = __import__("json").load(open(OUT + "break_slomo.json"))
SLOMO_F = 252              # frames of bullet-time insert
SLOMO_T0, SLOMO_T1 = 0.06, 1.30
GROUPS = GAME["shots"][-1].get("groups", {})

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
    """numbered equirect texture (UV sphere) — numbers roll with the ball"""
    m = principled("ball_" + bid, (1, 1, 1), rough=0.05, coat=0.6)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    img = nt.nodes.new("ShaderNodeTexImage")
    name = "ball_cue.png" if bid == "cue" else "ball_%s.png" % bid
    img.image = bpy.data.images.load(OUT + "assets/balls/" + name,
                                     check_existing=True)
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    return m


M_FELT = felt_material("felt")
M_WOOD = wood_material("rail_wood", WALNUT, scale=1.4, rough_mul=0.9)
M_FLOOR = wood_material("floor_wood", FLOOR_TINT, scale=0.45, rough_mul=1.55)
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

# ------------------------------------------------------------- dive bar -----
def brick_material(name, tint=(0.55, 0.40, 0.34)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.55, 0.55, 0.55)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])

    def img(suffix, non_color=False):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(
            TEX + "Bricks075A/Bricks075A_2K-JPG_" + suffix + ".jpg",
            check_existing=True)
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.3
        nt.links.new(mp.outputs[0], node.inputs["Vector"])
        return node

    col = img("Color")
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    mx.inputs[7].default_value = (*tint, 1.0)
    nt.links.new(col.outputs["Color"], mx.inputs[6])
    nt.links.new(mx.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.92
    nrm = img("NormalGL", True)
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.9
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])
    return m


def tin_material(name):
    m = principled(name, (0.070, 0.066, 0.058), rough=0.55, metal=0.6)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 8.0
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.offset = 0.0
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def neon_material(name, color, strength=42.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


M_BRICK = brick_material("brick")
M_TIN = tin_material("tin_ceiling")
M_NEON_PINK = neon_material("neon_pink", (1.0, 0.12, 0.35))
M_NEON_GRN = neon_material("neon_green", (0.15, 1.0, 0.35), 30.0)
M_EXIT = neon_material("exit_red", (1.0, 0.10, 0.06), 22.0)
M_GLASS = principled("bottle_glass", (0.35, 0.5, 0.35), rough=0.08)
try:
    M_GLASS.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.92
except Exception:
    pass
M_AMBER = principled("amber_beer", (0.75, 0.42, 0.05), rough=0.15)
M_STOOL = principled("stool_vinyl", (0.30, 0.05, 0.06), rough=0.5)
M_CHALK = principled("chalk_white", (0.85, 0.85, 0.80), rough=0.95)
M_BOARD = principled("chalkboard", (0.035, 0.040, 0.036), rough=0.85)

# replace plaster walls with brick + tin ceiling
for nm, mat in (("wall_n", M_BRICK), ("wall_s", M_BRICK),
                ("wall_e", M_BRICK), ("wall_w", M_BRICK),
                ("ceiling", M_TIN)):
    o = bpy.data.objects.get(nm)
    if o:
        o.data.materials.clear()
        o.data.materials.append(mat)

# drink rail + stools along the south wall
box("drink_rail", (5.2, 0.24, 0.045), (0, -3.55, 1.10), M_WOOD, bevel=0.004)
for i, sx in enumerate((-1.6, -0.2, 1.3)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.19, depth=0.055,
                                        location=(sx, -3.15, 0.72))
    seat = bpy.context.active_object
    seat.name = "stool_seat_%d" % i
    seat.data.materials.append(M_STOOL)
    shade_smooth(seat)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.03, depth=0.68,
                                        location=(sx, -3.15, 0.35))
    leg = bpy.context.active_object
    leg.name = "stool_post_%d" % i
    leg.data.materials.append(M_CHROME)
    bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.16, depth=0.02,
                                        location=(sx, -3.15, 0.06))
    base = bpy.context.active_object
    base.name = "stool_base_%d" % i
    base.data.materials.append(M_CHROME)

# two waiting beers on the rail
for i, sx in enumerate((-0.85, 0.55)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.038, depth=0.15,
                                        location=(sx, -3.55, 1.20))
    gl = bpy.context.active_object
    gl.name = "beer_glass_%d" % i
    gl.data.materials.append(M_GLASS)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.034, depth=0.11,
                                        location=(sx, -3.55, 1.185))
    bl_ = bpy.context.active_object
    bl_.name = "beer_liquid_%d" % i
    bl_.data.materials.append(M_AMBER)

# backlit bottle shelf on the east wall
box("shelf", (0.24, 2.4, 0.03), (4.42, 0.6, 1.45), M_WOOD, bevel=0.003)
box("shelf_glow", (0.03, 2.3, 0.05), (4.53, 0.6, 1.48), M_NEON_GRN, bevel=0)
import random as _rnd
_rnd.seed(7)
for i in range(11):
    by = -0.5 + i * 0.22 + _rnd.uniform(-0.03, 0.03)
    h = _rnd.uniform(0.22, 0.34)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=_rnd.uniform(0.032, 0.042),
                                        depth=h, location=(4.40, by, 1.465 + h / 2))
    bt = bpy.context.active_object
    bt.name = "bottle_%d" % i
    bt.data.materials.append(M_GLASS)
    shade_smooth(bt)

# neon POOL sign on the north brick
bpy.ops.object.text_add(location=(-0.95, 5.38, 2.05))
neon = bpy.context.active_object
neon.name = "neon_pool"
neon.data.body = "POOL"
neon.data.size = 0.42
neon.data.extrude = 0.012
neon.data.bevel_depth = 0.006
neon.rotation_euler = (radians(90), 0, 0)
neon.data.materials.append(M_NEON_PINK)
nl = bpy.data.lights.new("neon_l", "AREA")
nl.size = 1.4
nl.energy = 26
nl.color = (1.0, 0.25, 0.45)
nlo = bpy.data.objects.new("neon_l", nl)
bpy.context.collection.objects.link(nlo)
nlo.location = (-0.5, 5.1, 2.0)
nlo.rotation_euler = (radians(-80), 0, 0)

# EXIT sign + dark doorway on the west wall
box("door_inset", (0.06, 0.9, 2.1), (-4.52, 2.8, 1.05),
    principled("door_dark", (0.015, 0.013, 0.012), rough=0.9), bevel=0)
box("exit_box", (0.10, 0.34, 0.14), (-4.42, 2.8, 2.30), M_EXIT, bevel=0.004)

# dartboard on the west wall
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.22, depth=0.05,
                                    location=(-4.50, -1.4, 1.65))
db = bpy.context.active_object
db.name = "dartboard"
db.rotation_euler = (0, radians(90), 0)
db.data.materials.append(principled("dart_face", (0.10, 0.08, 0.06), rough=0.85))
bpy.ops.mesh.primitive_torus_add(major_radius=0.23, minor_radius=0.012,
                                 major_segments=28, minor_segments=8,
                                 location=(-4.47, -1.4, 1.65))
dr = bpy.context.active_object
dr.rotation_euler = (0, radians(90), 0)
dr.data.materials.append(M_CHROME)

# crooked frames + license plates on the walls
_rnd.seed(11)
for i, (fx, fy, fz, w, h, tilt) in enumerate((
        (1.9, 5.40, 1.75, 0.42, 0.55, 2.5), (2.9, 5.40, 1.9, 0.34, 0.26, -3.5),
        (-2.4, 5.40, 1.85, 0.5, 0.38, 1.8), (4.46, -1.8, 1.9, 0.4, 0.3, -2.0))):
    rot = (radians(90), radians(tilt), radians(180)) if fy > 5 else (radians(90), radians(tilt), radians(90))
    box("frame_%d" % i, (w, h, 0.03), (fx, fy, fz), M_WOOD, rot=rot, bevel=0.003)
    box("art_%d" % i, (w - 0.05, h - 0.05, 0.032), (fx, fy - 0.004 if fy > 5 else fx, fz),
        principled("art_m_%d" % i, (0.06 + i * 0.02, 0.05, 0.045), rough=0.6),
        rot=rot, bevel=0)
for i, (px, pz) in enumerate(((0.6, 2.45), (1.15, 2.32), (-1.5, 2.5))):
    box("plate_%d" % i, (0.30, 0.15, 0.01), (px, 5.40, pz),
        principled("plate_m_%d" % i, (0.5 + i * 0.1, 0.5, 0.45), rough=0.4, metal=0.6),
        rot=(radians(90), radians(_rnd.uniform(-4, 4)), radians(180)), bevel=0.002)

# string lights sagging across the near ceiling corner
for i in range(14):
    t = i / 13.0
    sx = -4.2 + t * 8.2
    sz = 2.85 - 0.35 * math.sin(math.pi * t)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.016,
                                         location=(sx, -3.9, sz))
    bulb = bpy.context.active_object
    bulb.name = "string_%d" % i
    bulb.data.materials.append(neon_material("bulb_%d" % i, (1.0, 0.65, 0.25), 14.0))

# chalkboard scoreboard on the north wall (right of the neon)
bl_light = bpy.data.lights.new("board_l", "AREA")
bl_light.size = 0.8
bl_light.energy = 30
bl_light.color = (1.0, 0.88, 0.7)
bl_obj = bpy.data.objects.new("board_l", bl_light)
bpy.context.collection.objects.link(bl_obj)
bl_obj.location = (2.65, 4.9, 2.35)
bl_obj.rotation_euler = (radians(-38), 0, 0)
box("board_frame", (1.30, 0.05, 0.95), (2.65, 5.42, 1.55), M_WOOD, bevel=0.004)
box("board", (1.20, 0.055, 0.85), (2.65, 5.415, 1.55), M_BOARD, bevel=0)

# faked haze: gradient light cones under each lamp shade (noise-free,
# nearly invisible from straight above — exactly where volumetrics speckled)
def light_cone(name, y_off):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.62, radius2=0.16,
                                    depth=0.95, location=(0, y_off, 1.30))
    c = bpy.context.active_object
    c.name = name
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.5
    mr.inputs["From Max"].default_value = 0.5
    mr.inputs["To Min"].default_value = 0.015
    mr.inputs["To Max"].default_value = 0.10
    mr.clamp = True
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    sq = nt.nodes.new("ShaderNodeMath")
    sq.operation = "POWER"
    sq.inputs[1].default_value = 2.2
    nt.links.new(inv.outputs[0], sq.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(mr.outputs[0], mul.inputs[0])
    nt.links.new(sq.outputs[0], mul.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.86, 0.62, 1.0)
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.12
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    for attr, val in (("blend_method", "BLEND"),
                      ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    try:
        m.use_backface_culling = True
    except Exception:
        pass
    c.data.materials.append(m)
    return c

for k in (-1, 0, 1):
    light_cone("haze_cone_%d" % k, k * 0.62)

# dust motes drifting through the lamp light
_rnd.seed(23)
for i in range(30):
    mx = _rnd.uniform(-0.5, 0.5)
    my = _rnd.uniform(-0.9, 0.9)
    mz = _rnd.uniform(1.45, 1.70)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0007,
                                          location=(mx, my, mz))
    mote = bpy.context.active_object
    mote.name = "mote_%d" % i
    mote.data.materials.append(neon_material("mote_m", (1.0, 0.9, 0.7), 0.45)
                               if i == 0 else bpy.data.materials["mote_m"])
    mote.keyframe_insert("location", frame=1)
    mote.location = (mx + _rnd.uniform(-0.15, 0.15),
                     my + _rnd.uniform(-0.15, 0.15),
                     mz + _rnd.uniform(-0.10, 0.06))
    mote.keyframe_insert("location", frame=scene.frame_end or 7080)

# high-quality volumetrics (default froxels show as blocky dots)
for attr, val in (("volumetric_tile_size", "2"), ("volumetric_samples", 128),
                  ("volumetric_start", 0.1), ("volumetric_end", 14.0)):
    try:
        setattr(scene.eevee, attr, val)
    except Exception:
        pass

# motion blur + felt wear
scene.eevee.taa_render_samples = 32
scene.render.use_motion_blur = True
try:
    scene.render.motion_blur_shutter = 0.38
except Exception:
    pass
fn = M_FELT.node_tree
fb = fn.nodes["Principled BSDF"]
wear = fn.nodes.new("ShaderNodeTexNoise")
wear.inputs["Scale"].default_value = 3.2
wear.inputs["Detail"].default_value = 4.0
ramp = fn.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.42
ramp.color_ramp.elements[1].position = 0.72
fn.links.new(wear.outputs["Fac"], ramp.inputs[0])
mixw = fn.nodes.new("ShaderNodeMix")
mixw.data_type = "RGBA"
mixw.inputs["Factor"].default_value = 1.0
mixw.inputs[6].default_value = FELT
mixw.inputs[7].default_value = (FELT[0] * 1.5, FELT[1] * 1.25, FELT[2] * 1.3, 1.0)
fn.links.new(ramp.outputs["Color"], mixw.inputs["Factor"])
fn.links.new(mixw.outputs[2], fb.inputs["Base Color"])

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

# cue wall rack on the north wall (parked cues live here, vertical)
box("cuerack_hi", (1.0, 0.04, 0.06), (-2.9, 5.40, 1.95), M_WOOD, bevel=0.003)
box("cuerack_lo", (1.0, 0.04, 0.06), (-2.9, 5.40, 0.75), M_WOOD, bevel=0.003)

# chalk scoreboard content: names, ball discs, X marks, winner circle
def chalk_text(name, body, loc, size=0.085):
    bpy.ops.object.text_add(location=loc)
    t = bpy.context.active_object
    t.name = name
    t.data.body = body
    t.data.size = size
    t.data.align_x = "CENTER"
    t.rotation_euler = (radians(90), 0, 0)
    t.data.materials.append(M_CHALK)
    return t

chalk_text("board_title", "8-BALL", (2.65, 5.385, 1.86), 0.10)
chalk_text("board_ray", "RAY", (2.32, 5.385, 1.68))
chalk_text("board_sam", "SAM", (2.98, 5.385, 1.68))

BOARD_X = {"Ray": 2.32, "Sam": 2.98}
solids_ids = [str(i) for i in range(1, 8)]
stripes_ids = [str(i) for i in range(9, 16)]
ray_ids = solids_ids if GROUPS.get("Ray") == "solids" else stripes_ids
sam_ids = stripes_ids if ray_ids is solids_ids else solids_ids
DISC = {}
X_MARKS = {}
for col_x, ids in ((BOARD_X["Ray"], ray_ids), (BOARD_X["Sam"], sam_ids)):
    for k, bid in enumerate(ids):
        dz = 1.52 - (k // 4) * 0.115
        dx = col_x - 0.17 + (k % 4) * 0.115
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.038,
            depth=0.012, location=(dx, 5.385, dz))
        d = bpy.context.active_object
    #    d.rotation: face out
        d.rotation_euler = (radians(90), 0, 0)
        d.name = "disc_" + bid
        c = BALL_COLORS[bid]
        d.data.materials.append(principled("disc_m_" + bid,
                                           (c[0]*0.7, c[1]*0.7, c[2]*0.7),
                                           rough=0.8))
        DISC[bid] = d
        xg = bpy.data.objects.new("xmark_" + bid, None)
        bpy.context.collection.objects.link(xg)
        xg.location = (dx, 5.375, dz)
        for sgn in (-1, 1):
            xb = box("x_%s_%+d" % (bid, sgn), (0.085, 0.012, 0.014),
                     (0, 0, 0), M_CHALK, bevel=0)
            xb.parent = xg
            xb.rotation_euler = (0, sgn * radians(45), 0)
        X_MARKS[bid] = xg
# the 8 in the middle
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.045, depth=0.012,
                                    location=(2.65, 5.385, 1.28))
d8 = bpy.context.active_object
d8.rotation_euler = (radians(90), 0, 0)
d8.name = "disc_8"
d8.data.materials.append(principled("disc_m_8", (0.02, 0.02, 0.02), rough=0.8))
DISC["8"] = d8
x8 = bpy.data.objects.new("xmark_8", None)
bpy.context.collection.objects.link(x8)
x8.location = (2.65, 5.375, 1.28)
for sgn in (-1, 1):
    xb = box("x_8_%+d" % sgn, (0.10, 0.012, 0.016), (0, 0, 0), M_CHALK, bevel=0)
    xb.parent = x8
    xb.rotation_euler = (0, sgn * radians(45), 0)
X_MARKS["8"] = x8

# winner circle + WINS text (hidden until the end)
bpy.ops.mesh.primitive_torus_add(major_radius=0.24, minor_radius=0.011,
                                 major_segments=28, minor_segments=6,
                                 location=(2.98, 5.375, 1.68))
wc = bpy.context.active_object
wc.name = "winner_circle"
wc.rotation_euler = (radians(90), 0, 0)
wc.data.materials.append(M_CHALK)
wins_t = chalk_text("board_wins", "WINS", (2.98, 5.375, 1.05), 0.11)

# ------------------------------------------------------------- animation ----
def key_loc(o, f, loc):
    o.location = loc
    o.keyframe_insert("location", frame=f)


def key_quat(o, f, q):
    o.rotation_quaternion = q
    o.keyframe_insert("rotation_quaternion", frame=f)


def key_hide(o, f, hidden):
    for x in [o] + list(o.children_recursive):
        x.hide_render = hidden
        x.keyframe_insert("hide_render", frame=f)


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
B0 = None                       # bullet-time insert start frame

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
    if si == 0:
        B0 = frame - (trim // 2) - GAP_F + 9
        frame += SLOMO_F                # bullet-time insert lives inside shot 1

F_END = frame + OUTRO_F
scene.frame_end = F_END

# slomo time curve: decel -> crawl -> accel across the insert
def slomo_time(f):
    if f < 30:
        u = f / 30.0
        return SLOMO_T0 + (0.30 - SLOMO_T0) * (1 - (1 - u) ** 2)
    if f < 210:
        return 0.30 + (0.90 - 0.30) * ((f - 30) / 180.0)
    u = (f - 210) / (SLOMO_F - 210)
    return 0.90 + (SLOMO_T1 - 0.90) * (u ** 2)


def slomo_quats():
    """integrate ball orientations through the 1 kHz slomo data"""
    out = {}
    for bid, tr in SLOMO["balls"].items():
        q = [1.0, 0.0, 0.0, 0.0]
        qs = [list(q)]
        for i in range(1, len(tr["t"])):
            dt = tr["t"][i] - tr["t"][i - 1]
            w = tr["w"][i]
            wn = math.sqrt(w[0] ** 2 + w[1] ** 2 + w[2] ** 2)
            if wn > 1e-9:
                ang = wn * dt
                ax = [w[0] / wn, w[1] / wn, w[2] / wn]
                sa = math.sin(ang / 2)
                dq = [math.cos(ang / 2), ax[0] * sa, ax[1] * sa, ax[2] * sa]
                w1, x1, y1, z1 = dq
                w2, x2, y2, z2 = q
                q = [w1*w2 - x1*x2 - y1*y2 - z1*z2,
                     w1*x2 + x1*w2 + y1*z2 - z1*y2,
                     w1*y2 - x1*z2 + y1*w2 + z1*x2,
                     w1*z2 + x1*y2 - y1*x2 + z1*w2]
                n = math.sqrt(sum(v * v for v in q))
                q = [v / n for v in q]
            qs.append(list(q))
        out[bid] = qs
    return out


SLOMO_Q = slomo_quats()

# ball keyframes
for start, si, shot, trim, d in SHOT_STARTS:
    if si == 0 and B0 is not None:
        resume_sample = int(SLOMO_T1 * 60)        # 60 Hz sample after insert
        b_end = B0 + SLOMO_F
        for bid, tr in shot["balls"].items():
            o = balls[bid]
            # phase A: real speed to the impact
            for i in range(0, 18, 2):
                f = start + i // 2
                x, y, z = tr["r"][i]
                key_loc(o, f, bl(x, y, z))
                q = tr["q"][i]
                key_quat(o, f, (q[0], q[1], q[2], q[3]))
            # phase B: bullet time from the 1 kHz re-sim
            st = SLOMO["balls"].get(bid)
            if st:
                for f in range(0, SLOMO_F, 1):
                    ts = slomo_time(f)
                    idx = min(int(ts * 1000), len(st["t"]) - 1)
                    x, y, z = st["r"][idx]
                    key_loc(o, B0 + f, bl(x, y, z))
                    q = SLOMO_Q[bid][idx]
                    key_quat(o, B0 + f, (q[0], q[1], q[2], q[3]))
            # phase C: back to real speed, from the frozen take
            n = min(trim + 1, len(tr["t"]))
            for i in range(resume_sample, n, 2):
                f = b_end + (i - resume_sample) // 2
                x, y, z = tr["r"][i]
                key_loc(o, f, bl(x, y, z))
                q = tr["q"][i]
                key_quat(o, f, (q[0], q[1], q[2], q[3]))
        continue
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
STRIKE_BACK = 0.09
for start, si, shot, trim, d in SHOT_STARTS:
    cue = CUES.get(shot["player"], cue_a)
    other = cue_b if cue is cue_a else cue_a
    c0 = shot["balls"]["cue"]["r"][0]
    bx, by, bz = bl(c0[0], c0[1], c0[2])
    ang = atan2(d[1], d[0]) + math.pi   # butt behind the ball, tip toward it
    # elevate over a near cushion like a real player (pocket mouths are open)
    pitch = 4.0
    for s_back in [x * 0.02 for x in range(1, 74)]:
        px = c0[0] - d[0] * s_back
        py = c0[1] - d[1] * s_back
        if not (0 <= px <= W and 0 <= py <= L):
            dp = min(math.hypot(px - q[0], py - q[1]) for q in POCKETS.values())
            if dp >= 0.10:
                need = math.degrees(math.atan(
                    (0.045 + 0.015 + 0.004 - (BALL_R + 0.01)) / s_back))
                pitch = max(pitch, min(need, 16.0))
            break
    cue.rotation_euler = (0, radians(-pitch), 0)
    tip_off = BALL_R + 0.006            # tip rests at the ball's surface

    def cue_pos(back, lift=0.0):
        return (bx - d[0] * (tip_off + back), by - d[1] * (tip_off + back),
                bz + 0.01 + lift)

    ready_f = start - GAP_F + 10
    key_loc(cue, ready_f - 6, cue_pos(0.34, 0.28))
    cue.rotation_euler = (0, radians(-pitch), ang)
    cue.keyframe_insert("rotation_euler", frame=ready_f - 6)
    cue.keyframe_insert("rotation_euler", frame=start + 20)
    key_loc(cue, ready_f, cue_pos(0.05))
    key_loc(cue, start - 12, cue_pos(0.05))
    key_loc(cue, start - 4, cue_pos(STRIKE_BACK + 0.10))
    key_loc(cue, start, cue_pos(0.0))
    key_loc(cue, start + 5, cue_pos(0.07))
    hold = SLOMO_F if si == 0 else 0
    key_loc(cue, start + 5 + hold, cue_pos(0.07))
    key_loc(cue, start + 22 + hold, cue_pos(0.30, 0.18))
    rack_x = -2.72 if cue is cue_a else -3.08
    key_loc(cue, start + 50 + hold, (rack_x, 5.32, 1.32))
    cue.rotation_euler = (0, radians(-pitch), ang)
    cue.keyframe_insert("rotation_euler", frame=start + 24 + hold)
    cue.rotation_euler = (0, radians(-90), 0)
    cue.keyframe_insert("rotation_euler", frame=start + 50 + hold)
    # idle cue rests in the wall rack
    other_x = -2.72 if other is cue_a else -3.08
    key_loc(other, ready_f, (other_x, 5.32, 1.32))
    other.rotation_euler = (0, radians(-90), 0)
    other.keyframe_insert("rotation_euler", frame=ready_f)

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
cam_top, t_top = make_cam("cam_top", 5.0, 30)
cam_pkt, t_pkt = make_cam("cam_pkt", 2.2, 58)
cam_orbit, t_orbit = make_cam("cam_orbit", 2.8, 55)
cam_board, t_board = make_cam("cam_board", 3.5, 55)
scene.camera = cam_board

CYCLE = [cam_three, cam_low, cam_side, cam_low, cam_top]
T_OF = {cam_low: t_low, cam_side: t_side, cam_three: t_three, cam_top: t_top}

# board intro: names on the chalkboard, slow push
key_loc(cam_board, 1, (2.65, 4.05, 1.55))
key_loc(cam_board, INTRO_F, (2.65, 4.42, 1.55))
key_loc(t_board, 1, (2.65, 5.4, 1.55))
mk = scene.timeline_markers.new("intro", frame=1)
mk.camera = cam_board

# overhead break
first_start = SHOT_STARTS[0][0]
mk = scene.timeline_markers.new("break_top", frame=INTRO_F + 1)
mk.camera = cam_top
key_loc(cam_top, INTRO_F + 1, (0.0, -0.42, 1.66))
key_loc(cam_top, first_start + 8, (0.0, -0.30, 1.62))
key_loc(t_top, INTRO_F + 1, (0, 0.25, BED))

# bullet-time orbit around the rack
FOOT = bl(W / 2, L * 0.75, 0)
mk = scene.timeline_markers.new("bullet", frame=B0)
mk.camera = cam_orbit
key_loc(t_orbit, B0, (FOOT[0], FOOT[1] - 0.18, BED + 0.05))
for f in range(0, SLOMO_F + 1, 6):
    a0 = radians(210 + 130 * (f / SLOMO_F))
    r = 1.05 - 0.25 * (f / SLOMO_F)
    key_loc(cam_orbit, B0 + f,
            (FOOT[0] + r * cos(a0), FOOT[1] + r * sin(a0),
             BED + 0.34 - 0.10 * (f / SLOMO_F)))
# after the insert: side wide watches the spread resolve
mk = scene.timeline_markers.new("break_resolve", frame=B0 + SLOMO_F)
mk.camera = cam_side
key_loc(cam_side, B0 + SLOMO_F, (2.45, -0.8, BED + 0.6))
key_loc(t_side, B0 + SLOMO_F, (0, 0.3, BED + 0.02))

# per-shot cameras (skipping the break, which is choreographed above)
EV_BY_SHOT = {}
for e in EVENTS:
    EV_BY_SHOT.setdefault(e["shot"], []).append(e)

for start, si, shot, trim, d in SHOT_STARTS:
    if si == 0:
        shot_end = B0 + SLOMO_F + (trim - int(SLOMO_T1 * 60)) // 2
    else:
        shot_end = start + trim // 2
    cam = cam_low if si in (0,) else CYCLE[si % len(CYCLE)]
    if si > 0:
        tgt = T_OF[cam]
        c0 = shot["balls"]["cue"]["r"][0]
        bx, by, bz = bl(c0[0], c0[1], c0[2])
        tgt_ball = shot.get("target")
        tb = shot["balls"].get(tgt_ball)
        t0 = bl(*tb["r"][0]) if tb else (0, 0, BED)
        mid = ((bx + t0[0]) / 2, (by + t0[1]) / 2, BED + 0.02)
        f_cut = start - GAP_F + 8
        mk = scene.timeline_markers.new("s%d" % si, frame=max(1, f_cut))
        mk.camera = cam
        if cam is cam_low:
            px_, py_ = -d[1], d[0]
            pos = (bx - d[0] * 1.30 + px_ * 0.30, by - d[1] * 1.30 + py_ * 0.30,
                   BED + 0.26)
            pos2 = (bx - d[0] * 1.18 + px_ * 0.26, by - d[1] * 1.18 + py_ * 0.26,
                    BED + 0.30)
        elif cam is cam_side:
            side = 1 if by < 0 else -1
            pos = (2.45, side * 0.9, BED + 0.55)
            pos2 = (2.3, side * 0.7, BED + 0.5)
        elif cam is cam_top:
            pos = (0.05, -0.15, 1.64)
            pos2 = (0.0, 0.15, 1.64)
        else:
            sidex = 1 if bx < 0 else -1
            pos = (sidex * 2.2, -2.3, 1.45)
            pos2 = (sidex * 2.05, -2.05, 1.38)
        dur = trim // 2 + GAP_F
        key_loc(cam, f_cut, pos)
        key_loc(cam, f_cut + dur, pos2)
        key_loc(tgt, f_cut, mid)
        key_loc(tgt, f_cut + int(dur * 0.4), (t0[0], t0[1], BED + 0.02))

    # pocket cuts: first two events of the shot get close-ups
    evs = sorted(EV_BY_SHOT.get(si, []), key=lambda e: e["i"])[:2]
    for k, e in enumerate(evs):
        if si == 0:
            resume = int(SLOMO_T1 * 60)
            ev_f = (B0 + SLOMO_F + (e["i"] - resume) // 2
                    if e["i"] >= resume else start + e["i"] // 2)
        else:
            ev_f = start + e["i"] // 2
        pc = POCKETS[e["pocket"]]
        px, py, pz = bl(pc[0], pc[1], 0)
        inx = 1 if px < 0 else -1
        iny = 1 if py < 0 else -1
        mk = scene.timeline_markers.new("pk%d_%d" % (si, k), frame=max(1, ev_f - 12))
        mk.camera = cam_pkt
        key_loc(cam_pkt, ev_f - 12, (px + inx * 0.34, py + iny * 0.30, BED + 0.16))
        key_loc(cam_pkt, ev_f + 14, (px + inx * 0.30, py + iny * 0.26, BED + 0.19))
        key_loc(t_pkt, ev_f - 12, (px, py, BED + 0.01))
        back_f = ev_f + (26 if not (si == 33 and e["ball"] == "cue") else 44)
        if si == 33 and e["ball"] == "8":
            continue          # hold the pocket cam: the cue is coming too
        mk = scene.timeline_markers.new("pkb%d_%d" % (si, k), frame=back_f)
        mk.camera = cam if si > 0 else cam_side

    # chalkboard X marks land as balls drop
    for e in EV_BY_SHOT.get(si, []):
        if e["ball"] == "cue":
            continue
        xg = X_MARKS.get(e["ball"])
        if not xg:
            continue
        if si == 0:
            resume = int(SLOMO_T1 * 60)
            ev_f = (B0 + SLOMO_F + (e["i"] - resume) // 2
                    if e["i"] >= resume else start + e["i"] // 2)
        else:
            ev_f = start + e["i"] // 2
        key_hide(xg, 1, True)
        key_hide(xg, ev_f + 18, False)

# X marks default hidden even if never potted
for bid, xg in X_MARKS.items():
    if not any(fc for fc in []):
        pass
for bid, xg in X_MARKS.items():
    xg.hide_render = xg.hide_render  # no-op; hidden state set above where used
for bid, xg in X_MARKS.items():
    potted = any(e["ball"] == bid for e in EVENTS)
    if not potted:
        key_hide(xg, 1, True)

# winner card: hidden until the outro
key_hide(bpy.data.objects["winner_circle"], 1, True)
key_hide(bpy.data.objects["board_wins"], 1, True)
key_hide(bpy.data.objects["winner_circle"], F_END - OUTRO_F + 18, False)
key_hide(bpy.data.objects["board_wins"], F_END - OUTRO_F + 30, False)

# closing: pocket-cam heartbreak already held; then the board tells it
mk = scene.timeline_markers.new("outro", frame=F_END - OUTRO_F + 12)
mk.camera = cam_board
key_loc(cam_board, F_END - OUTRO_F + 12, (2.65, 4.5, 1.55))
key_loc(cam_board, F_END, (2.65, 4.15, 1.55))

# handheld: subtle noise on every camera
for c in (cam_low, cam_side, cam_three, cam_top, cam_pkt, cam_orbit, cam_board):
    ad = c.animation_data
    if not ad or not ad.action:
        continue
    fcs = []
    act = ad.action
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
        if fc.data_path == "location":
            m = fc.modifiers.new("NOISE")
            m.strength = 0.006
            m.scale = 34.0
            m.phase = fc.array_index * 7.7

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
