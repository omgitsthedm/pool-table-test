"""
render_break.py — thirty seconds of one break, at 24 fps.

  blender -b -P render_break.py -- --test 40 300 500
  blender -b -P render_break.py -- --render [start end]

The table comes from build_table (real pockets cut through the slate, flat
cabinet, K-66 cushions). No figure: the cue is the only actor, and it
on a joint-accurate rig, posed by IK), and the ball motion from break.json,
which pooltool simulated at 120 Hz. Balls that reach a pocket fall through the
hole and settle in the pouch underneath — no ring, no vanishing.

Film time is warped: the address and stroke play straight, the impact crawls,
then the table returns to real time as the rack spreads and the pots drop.
"""
import bpy
import json
import math
import os
import sys
from math import radians
from mathutils import Vector, Quaternion

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import build_table as BT           # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

FPS = 24
F_END = 720                        # 30.0 s
RES = (1920, 1080)
DATA = json.load(open(os.path.join(HERE, "break.json")))
META = DATA["meta"]
RATE = META["rate"]
N_SAMP = META["n_samples"]
BALL_R = META["ball_R"]
W, L = META["table"]["w"], META["table"]["l"]
BED = BT.BED

# --- beats -----------------------------------------------------------------
F_STRIKE = 250                     # cue tip meets the ball
F_SETTLE = 660                     # everything at rest; final wide
CUE_LEN = 1.47

# --- ball colours (numbers come from the painted equirect textures) --------
STRIPES = {"9", "10", "11", "12", "13", "14", "15"}


def sim_time(f):
    """film frame -> simulation seconds. Straight, then crawl, then back."""
    if f <= F_STRIKE:
        return 0.0
    if f <= 256:                                    # cue ball crossing, 50%
        return (f - F_STRIKE) / FPS * 0.50
    t0 = 6.0 / FPS * 0.50
    if f <= 430:                                    # the hit, ~6% speed
        return t0 + (f - 256) / FPS * 0.060
    t1 = t0 + (430 - 256) / FPS * 0.060
    if f <= 545:                                    # opening back up
        u = (f - 430) / (545 - 430)
        sp = 0.060 + (0.85 - 0.060) * (u * u)
        return t1 + (f - 430) / FPS * (0.060 + sp) * 0.5
    t2 = t1 + (545 - 430) / FPS * (0.060 + 0.85) * 0.5
    return min(t2 + (f - 545) / FPS * 1.0, (N_SAMP - 1) / RATE)


def sample_at(f):
    """film frame -> fractional physics sample (never rounded: rounding is
    what made the balls stutter through the slow-motion beats)"""
    return min(N_SAMP - 1.0, max(0.0, sim_time(f) * RATE))


def _lerp_sample(seq, t):
    i = int(math.floor(t))
    j = min(len(seq) - 1, i + 1)
    u = t - i
    a, b = seq[i], seq[j]
    return [a[k] + (b[k] - a[k]) * u for k in range(len(a))]


def stroke_back(f):
    """metres the grip hand / cue butt is drawn back, per film frame"""
    def ramp(a, b, u):
        u = min(1.0, max(0.0, u))
        return a + (b - a) * (u * u * (3 - 2 * u))
    if f < 96:                                   # stepping in, cue held back
        return ramp(0.34, 0.05, (f - 60) / 36.0) if f > 60 else 0.34
    if f < 128:                                  # practice stroke one
        return ramp(0.05, 0.17, (f - 96) / 32.0)
    if f < 156:
        return ramp(0.17, 0.03, (f - 128) / 28.0)
    if f < 188:                                  # practice stroke two
        return ramp(0.03, 0.19, (f - 156) / 32.0)
    if f < 214:
        return ramp(0.19, 0.02, (f - 188) / 26.0)
    if f < 238:                                  # the real backswing
        return ramp(0.02, 0.33, (f - 214) / 24.0)
    if f < F_STRIKE:                             # the pause, then fire
        return ramp(0.33, 0.0, (f - 238) / float(F_STRIKE - 238))
    if f < F_STRIKE + 26:                        # follow through
        return ramp(0.0, -0.13, (f - F_STRIKE) / 26.0)
    if f < F_STRIKE + 90:                        # ease off the shot
        return ramp(-0.13, -0.06, (f - F_STRIKE - 26) / 64.0)
    return -0.06


# ---------------------------------------------------------------- scene -----
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
             bpy.data.cameras, bpy.data.lights, bpy.data.images,
             bpy.data.armatures):
    for x in list(coll):
        try:
            coll.remove(x)
        except Exception:
            pass

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, F_END
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.eevee.taa_render_samples = 32
scene.render.use_motion_blur = True
try:
    scene.render.motion_blur_shutter = 0.42
except Exception:
    pass
scene.render.image_settings.file_format = "PNG"


def principled(name, col, rough=0.5, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except Exception:
        pass
    return m


def tex_material(name, folder, scale=1.0, rough_mul=1.0):
    """ambientCG PBR set -> principled with colour/roughness/normal"""
    base = os.path.join(HERE, "assets", "tex", folder)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    co = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
    found = {}
    if os.path.isdir(base):
        for f in os.listdir(base):
            lf = f.lower()
            for key, tag in (("col", "color"), ("rgh", "rough"),
                             ("nrm", "normal")):
                if key in lf and tag not in found:
                    found[tag] = os.path.join(base, f)
    if "color" in found:
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(found["color"])
        n.projection = "BOX"
        n.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        nt.links.new(n.outputs["Color"], bsdf.inputs["Base Color"])
    if "rough" in found:
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(found["rough"])
        n.image.colorspace_settings.name = "Non-Color"
        n.projection = "BOX"
        n.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        mult = nt.nodes.new("ShaderNodeMath")
        mult.operation = "MULTIPLY"
        mult.inputs[1].default_value = rough_mul
        nt.links.new(n.outputs["Color"], mult.inputs[0])
        nt.links.new(mult.outputs[0], bsdf.inputs["Roughness"])
    if "normal" in found:
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(found["normal"])
        n.image.colorspace_settings.name = "Non-Color"
        n.projection = "BOX"
        n.projection_blend = 0.25
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.7
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def cloth_material():
    m = bpy.data.materials.new("cloth")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.012, 0.115, 0.052, 1.0)
    b.inputs["Roughness"].default_value = 0.94
    try:
        b.inputs["Sheen Weight"].default_value = 0.35
    except Exception:
        pass
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 900.0
    n.inputs["Detail"].default_value = 3.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


M_WOOD = tex_material("wood", "Wood049", scale=1.4, rough_mul=0.85)
M_RAIL = tex_material("rail", "Wood049", scale=2.2, rough_mul=0.55)
M_BRICK = tex_material("brick", "Bricks075A", scale=1.2, rough_mul=1.0)
M_CLOTH = cloth_material()
M_RUBBER = principled("rubber", (0.020, 0.075, 0.036), 0.72)
M_POUCH = principled("pouch", (0.055, 0.040, 0.032), 0.78)
M_SIGHT = principled("sight", (0.88, 0.86, 0.79), 0.22)
M_METAL = principled("metal", (0.62, 0.63, 0.66), 0.24, metal=1.0)
M_FLOOR = tex_material("floor", "Wood049", scale=1.1, rough_mul=1.5)

TABLE = BT.build({"cloth": M_CLOTH, "wood": M_WOOD, "rail": M_RAIL,
                  "rubber": M_RUBBER, "pouch": M_POUCH, "sight": M_SIGHT,
                  "metal": M_METAL})
HOLES = TABLE["holes"]

# ------------------------------------------------------------------ room ----
ROOM_W, ROOM_L, ROOM_H = 7.4, 9.0, 2.72


def wall(name, dims, loc, mat, rot=None):
    return BT._box(name, dims, loc, mat, rot=rot)


wall("floor", (ROOM_W, ROOM_L, 0.04), (0, 0, -0.02), M_FLOOR)
wall("ceil", (ROOM_W, ROOM_L, 0.04), (0, 0, ROOM_H), principled(
    "tin", (0.055, 0.050, 0.045), 0.55, metal=0.6))
for sx in (-1, 1):
    wall("wall_x%+d" % sx, (0.06, ROOM_L, ROOM_H),
         (sx * ROOM_W / 2, 0, ROOM_H / 2), M_BRICK)
for sy in (-1, 1):
    wall("wall_y%+d" % sy, (ROOM_W, 0.06, ROOM_H),
         (0, sy * ROOM_L / 2, ROOM_H / 2), M_BRICK)

# billiard lamp: three shades on a rail over the table
LAMP_Z = 1.62
lamp_lights = []
for k in (-1, 0, 1):
    y = k * 0.62
    BT._cyl("shade_%d" % k, 0.20, 0.15, (0, y, LAMP_Z + 0.075),
            principled("shade_%d" % k, (0.045, 0.040, 0.038), 0.5, metal=0.7),
            verts=28)
    BT._cyl("rod_%d" % k, 0.008, ROOM_H - LAMP_Z - 0.15,
            (0, y, LAMP_Z + 0.15 + (ROOM_H - LAMP_Z - 0.15) / 2), M_METAL,
            verts=10)
    ld = bpy.data.lights.new("lamp_%d" % k, "AREA")
    ld.energy = 165.0
    ld.size = 0.30
    ld.color = (1.0, 0.90, 0.74)
    lo = bpy.data.objects.new("lamp_%d" % k, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (0, y, LAMP_Z + 0.01)
    lamp_lights.append(lo)

fill = bpy.data.lights.new("fill", "AREA")
fill.energy = 55.0
fill.size = 3.0
fill.color = (0.75, 0.80, 1.0)
fo = bpy.data.objects.new("fill", fill)
bpy.context.collection.objects.link(fo)
fo.location = (-2.4, -1.9, 1.95)
fo.rotation_euler = (radians(52), 0, radians(-38))

rim = bpy.data.lights.new("rim", "AREA")
rim.energy = 190.0
rim.size = 2.2
rim.color = (1.0, 0.72, 0.46)
ro = bpy.data.objects.new("rim", rim)
bpy.context.collection.objects.link(ro)
ro.location = (-1.9, -2.9, 2.05)
ro.rotation_euler = (radians(64), 0, radians(-150))

pkey = bpy.data.lights.new("player_key", "AREA")
pkey.energy = 140.0
pkey.size = 1.5
pkey.color = (1.0, 0.86, 0.68)
pk = bpy.data.objects.new("player_key", pkey)
bpy.context.collection.objects.link(pk)
pk.location = (2.15, -1.55, 1.92)
pk.rotation_euler = (radians(58), 0, radians(112))

und = bpy.data.lights.new("under", "POINT")
und.energy = 58.0
und.shadow_soft_size = 0.35
und.color = (1.0, 0.84, 0.66)
uo = bpy.data.objects.new("under", und)
bpy.context.collection.objects.link(uo)
uo.location = (0, 0, BED - 0.17)

world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (
    0.020, 0.017, 0.014, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
scene.world = world

# ----------------------------------------------------------------- balls ----
def ball_material(bid):
    m = bpy.data.materials.new("ball_%s" % bid)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.075
    try:
        b.inputs["Coat Weight"].default_value = 0.85
        b.inputs["Coat Roughness"].default_value = 0.04
    except Exception:
        pass
    path = os.path.join(HERE, "assets", "balls", "ball_%s.png" % bid)
    if os.path.exists(path):
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(path)
        nt.links.new(img.outputs["Color"], b.inputs["Base Color"])
    return m


BALLS = {}
for bid in DATA["balls"]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32,
                                         radius=BALL_R)
    ob = bpy.context.active_object
    ob.name = "ball_%s" % bid
    ob.data.materials.append(ball_material(bid))
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.rotation_mode = "QUATERNION"
    BALLS[bid] = ob

POTTED = DATA["potted"]
POT_SAMPLE = DATA["pot_frames"]
FALL_S = 0.42                       # seconds of sim time the drop occupies


def ball_pos(bid, f):
    """world position for `bid` at film frame f, including the pocket drop"""
    t = sample_at(f)
    r = DATA["balls"][bid]["r"]
    t = min(t, len(r) - 1.0)
    i = int(math.floor(t))
    x, y, z = _lerp_sample(r, t)
    p = Vector((x - W / 2, y - L / 2, BED + z))
    if bid in POTTED:
        ps = POT_SAMPLE.get(bid)
        if ps is not None and t >= ps:
            c, rad = HOLES[POTTED[bid]]
            rest = BT.drop_target(POTTED[bid], HOLES)
            u = min(1.0, (t - ps) / max(1.0, FALL_S * RATE))
            mouth = Vector((p.x, p.y, BED + BALL_R))
            lip = Vector((c.x, c.y, BED + BALL_R))
            if u < 0.18:                       # slides over the lip
                k = u / 0.18
                return mouth.lerp(lip, k)
            # free fall under gravity, then one damped bounce in the pouch
            k = (u - 0.18) / 0.82
            fall = lip.z - rest.z
            tf = math.sqrt(max(1e-6, 2.0 * fall / 9.81))
            tt = k * tf * 1.55
            z = lip.z - 0.5 * 9.81 * tt * tt
            drop = lip.lerp(rest, min(1.0, k * 1.1))
            if z > rest.z:
                drop.z = z
            else:                              # settle: one small damped hop
                over = (tt - tf) / max(1e-6, tf)
                drop.z = rest.z + abs(math.sin(over * 3.0)) * 0.016 * \
                    math.exp(-over * 4.0)
            return drop
    return p


def ball_quat(bid, f):
    q = DATA["balls"][bid]["q"]
    i = int(math.floor(min(sample_at(f), len(q) - 1.0)))
    w, x, y, z = q[i]
    return Quaternion((w, x, y, z))


# ------------------------------------------------------------- the player ---


CB0 = DATA["balls"]["cue"]["r"][0]
BALL_Y = CB0[1] - L / 2
CUE_X = CB0[0] - W / 2

bpy.context.view_layer.update()

# ------------------------------------------------------------------- cue ----
cue_mats = (principled("cue_shaft", (0.72, 0.56, 0.33), 0.22),
            principled("cue_butt", (0.075, 0.045, 0.035), 0.28))
shaft = BT._cyl("cue_shaft", 0.0068, CUE_LEN * 0.56, (0, 0, 0), cue_mats[0],
                verts=20)
butt = BT._cyl("cue_butt", 0.0122, CUE_LEN * 0.44, (0, 0, 0), cue_mats[1],
               verts=20)
tip = BT._cyl("cue_tip", 0.0066, 0.012, (0, 0, 0),
              principled("tip", (0.30, 0.42, 0.55), 0.55), verts=16)
CUE = bpy.data.objects.new("cue", None)
bpy.context.collection.objects.link(CUE)
for part, off in ((shaft, CUE_LEN * 0.28), (butt, CUE_LEN * 0.78),
                  (tip, -0.006)):
    part.parent = CUE
    part.location = (0, 0, -off)
    part.rotation_euler = (0, 0, 0)
CUE.rotation_euler = (radians(-90) - radians(7.5), 0, 0)


def cue_place(f):
    """tip rides the aim line; back-off comes from the stroke curve"""
    back = stroke_back(f)
    tipz = BED + BALL_R + 0.004
    return (CUE_X, BALL_Y - BALL_R - 0.004 - back, tipz + back * 0.1317)


# ------------------------------------------------------------------ keys ----
def key_loc(o, f, loc):
    o.location = loc
    o.keyframe_insert("location", frame=f)


def linearize(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    curves = list(getattr(act, "fcurves", []) or [])
    if not curves:
        for lay in getattr(act, "layers", []):
            for st in getattr(lay, "strips", []):
                for cb in getattr(st, "channelbags", []):
                    curves.extend(cb.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


for f in range(1, F_END + 1):
    for bid, ob in BALLS.items():
        ob.location = ball_pos(bid, f)
        ob.keyframe_insert("location", frame=f)
        ob.rotation_quaternion = ball_quat(bid, f)
        ob.keyframe_insert("rotation_quaternion", frame=f)
    key_loc(CUE, f, cue_place(f))

for ob in list(BALLS.values()) + [CUE]:
    linearize(ob)

# ---------------------------------------------------------------- cameras ---
def make_cam(name, lens, fstop=2.8):
    tgt = bpy.data.objects.new(name + "_t", None)
    bpy.context.collection.objects.link(tgt)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.focus_object = tgt
    cd.dof.aperture_fstop = fstop
    c = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(c)
    con = c.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return c, tgt


RACK = Vector((CUE_X, L * 0.25, BED + BALL_R))     # rack apex area
CUEBALL = Vector((CUE_X, BALL_Y, BED + BALL_R))


def marker(name, frame, cam):
    mk = scene.timeline_markers.new(name, frame=frame)
    mk.camera = cam


# 1. establishing wide — the room, the table, the player stepping in
cam_wide, t_wide = make_cam("cam_wide", 34, 3.4)
key_loc(cam_wide, 1, (2.42, -2.62, 1.72))
key_loc(cam_wide, 96, (2.06, -2.30, 1.55))
key_loc(t_wide, 1, (CUE_X, -0.10, BED + 0.02))
marker("wide", 1, cam_wide)

# 2. the stance and the practice strokes, from the side
cam_side, t_side = make_cam("cam_side", 42, 2.8)
key_loc(cam_side, 96, (2.00, BALL_Y - 0.96, BED + 0.40))
key_loc(cam_side, 214, (1.78, BALL_Y - 0.80, BED + 0.32))
key_loc(t_side, 96, (CUE_X + 0.02, BALL_Y - 0.52, BED + 0.19))
marker("side", 96, cam_side)

# 3. down the cue at the ball — the last backswing and the pause
cam_line, t_line = make_cam("cam_line", 58, 3.2)
key_loc(cam_line, 214, (CUE_X + 0.20, BALL_Y - 0.86, BED + 0.235))
key_loc(cam_line, F_STRIKE, (CUE_X + 0.16, BALL_Y - 0.70, BED + 0.205))
key_loc(t_line, 214, (CUE_X, BALL_Y + 0.02, BED + BALL_R))
marker("line", 214, cam_line)

# 4. the strike, low and tight on the cue ball
cam_hit, t_hit = make_cam("cam_hit", 72, 2.6)
key_loc(cam_hit, F_STRIKE, (CUE_X - 0.52, BALL_Y + 0.06, BED + 0.115))
key_loc(cam_hit, 300, (CUE_X - 0.46, BALL_Y + 0.40, BED + 0.105))
key_loc(t_hit, F_STRIKE, (CUE_X, BALL_Y + 0.06, BED + BALL_R))
key_loc(t_hit, 300, (CUE_X, L * 0.16, BED + BALL_R))
marker("hit", F_STRIKE, cam_hit)

# 5. the rack blowing apart, orbiting through the slow motion
cam_orb, t_orb = make_cam("cam_orb", 52, 2.2)
for i in range(0, 15):
    f = 300 + i * 10
    a = radians(-118 + i * 9.0)
    rad = 1.16 - i * 0.020
    key_loc(cam_orb, f, (RACK.x + math.cos(a) * rad,
                         RACK.y + math.sin(a) * rad,
                         BED + 0.30 - i * 0.006))
key_loc(t_orb, 300, (RACK.x, RACK.y - 0.06, BED + BALL_R))
key_loc(t_orb, 450, (RACK.x, RACK.y + 0.04, BED + BALL_R))
marker("orbit", 300, cam_orb)

# 6. a ball falls in — pocket cam, watching it drop through into the pouch
pot_order = sorted(POT_SAMPLE.items(), key=lambda kv: kv[1])
cam_pkt, t_pkt = make_cam("cam_pkt", 62, 3.0)


def frame_for_sample(s):
    lo, hi = 1, F_END
    while lo < hi:
        mid = (lo + hi) // 2
        if sample_at(mid) < s:
            lo = mid + 1
        else:
            hi = mid
    return lo


cuts = []
for bid, s in pot_order:
    cuts.append((bid, frame_for_sample(s)))
cuts = [c for c in cuts if c[1] > 455]
if cuts:
    bid, cf = cuts[-1] if len(cuts) == 1 else cuts[0]
    key = POTTED[bid]
    c, rad = HOLES[key]
    ax = BT.pocket_axis(key)
    start = max(462, cf - 26)
    # stay outside the rail and look down through the mouth, so the ball
    # is seen rolling in, dropping, and settling in the pouch below
    key_loc(cam_pkt, start, (c.x + ax.x * 0.66, c.y + ax.y * 0.66, BED + 0.62))
    key_loc(cam_pkt, cf + 62, (c.x + ax.x * 0.40, c.y + ax.y * 0.40,
                               BED + 0.46))
    key_loc(t_pkt, start, (c.x - ax.x * 0.10, c.y - ax.y * 0.10,
                           BED + BALL_R))
    key_loc(t_pkt, cf + 62, (c.x, c.y, BED - 0.062))
    marker("pocket", start, cam_pkt)
    LAST_CUT = cf + 62
else:
    LAST_CUT = 470

# 7. settle — pull back out to the room with the rack spread
cam_out, t_out = make_cam("cam_out", 38, 3.0)
key_loc(cam_out, F_SETTLE, (1.62, -2.05, BED + 0.62))
key_loc(cam_out, F_END, (1.94, -2.42, BED + 0.78))
key_loc(t_out, F_SETTLE, (CUE_X, 0.05, BED))
marker("settle", max(F_SETTLE, LAST_CUT + 2), cam_out)

for c in (cam_wide, cam_side, cam_line, cam_hit, cam_orb, cam_pkt, cam_out):
    linearize(c)
    for con in c.constraints:
        pass
    # a little handheld life on every camera
    if c.animation_data and c.animation_data.action:
        acts = list(getattr(c.animation_data.action, "fcurves", []) or [])
        if not acts:
            for lay in getattr(c.animation_data.action, "layers", []):
                for st in getattr(lay, "strips", []):
                    for cb in getattr(st, "channelbags", []):
                        acts.extend(cb.fcurves)
        for fc in acts:
            n = fc.modifiers.new("NOISE")
            n.strength = 0.0055
            n.scale = 30.0
            n.phase = fc.array_index * 7.3

scene.camera = cam_wide

# ---------------------------------------------------------------- output ----
OUTDIR = os.path.join(HERE, "out")
os.makedirs(OUTDIR, exist_ok=True)

if argv and argv[0] == "--test":
    for a in argv[1:]:
        scene.frame_set(int(a))
        scene.render.filepath = os.path.join(OUTDIR, "brk_%05d.png" % int(a))
        bpy.ops.render.render(write_still=True)
elif argv and argv[0] == "--render":
    if len(argv) >= 3:
        scene.frame_start, scene.frame_end = int(argv[1]), int(argv[2])
    scene.render.filepath = os.path.join(HERE, "frames_break", "b_")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, "break.blend"))
    bpy.ops.render.render(animation=True)
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, "break.blend"))

print("film frames: %d (%.1f s)  potted: %s" % (F_END, F_END / FPS, POTTED))
