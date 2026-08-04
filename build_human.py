"""
build_human.py — an anatomically-proportioned player, posed for a break.

Mesh: the MakeHuman base mesh (CC0, shipped inside MPFB2). It arrives Y-up
with three vertex blocks — body, helper geometry (for fitting clothes) and
joint cubes (small cubes marking every anatomical joint). We keep the body,
read the joint cubes to place bones exactly where the anatomy says they go,
bind with automatic weights, then pose the rig into a right-handed break
stance. Clothes are grown from the body itself: the shirt/jeans are copies of
the relevant vertex regions pushed out along their normals, so they drape
correctly no matter how the figure is posed.

Import and call build_player(); it returns (rig, objects) with the figure
standing at the origin facing +Y.
"""
import bpy
import json
import math
import os
from math import radians
from mathutils import Vector

HERE = os.path.dirname(os.path.realpath(__file__))
HUMAN_DIR = os.path.join(HERE, "assets", "human")
HEIGHT = 1.80                     # metres, heel to crown

# bone chains: (name, head-joint, tail-joint, parent)
SPINE = [
    ("pelvis", "joint-pelvis", "joint-spine-4", None),
    ("spine_01", "joint-spine-4", "joint-spine-3", "pelvis"),
    ("spine_02", "joint-spine-3", "joint-spine-2", "spine_01"),
    ("spine_03", "joint-spine-2", "joint-spine-1", "spine_02"),
    ("chest", "joint-spine-1", "joint-neck", "spine_03"),
    ("neck", "joint-neck", "joint-head", "chest"),
    ("head", "joint-head", "joint-head-2", "neck"),
]


def _limbs(s):
    """arm + leg chain for side s ('l' or 'r')"""
    j = lambda n: "joint-%s-%s" % (s, n)
    return [
        ("clavicle_%s" % s, j("clavicle"), j("shoulder"), "chest"),
        ("upperarm_%s" % s, j("shoulder"), j("elbow"), "clavicle_%s" % s),
        ("forearm_%s" % s, j("elbow"), j("hand"), "upperarm_%s" % s),
        ("hand_%s" % s, j("hand"), j("hand-2"), "forearm_%s" % s),
        ("thigh_%s" % s, j("upper-leg"), j("knee"), "pelvis"),
        ("shin_%s" % s, j("knee"), j("ankle"), "thigh_%s" % s),
        ("foot_%s" % s, j("ankle"), j("foot-1"), "shin_%s" % s),
    ]


def _fingers(s):
    """5 digits x 3 segments per hand"""
    out = []
    for d in range(1, 6):
        parent = "hand_%s" % s
        for seg in range(1, 4):
            nm = "f%d_%d_%s" % (d, seg, s)
            out.append((nm, "joint-%s-finger-%d-%d" % (s, d, seg),
                        "joint-%s-finger-%d-%d" % (s, d, seg + 1), parent))
            parent = nm
    return out


def _load_groups():
    with open(os.path.join(HUMAN_DIR, "vertex_groups.json")) as f:
        return json.load(f)


def _expand(ranges):
    out = []
    for a, b in ranges:
        out.extend(range(a, b + 1))
    return out


def build_player(name="player", height=HEIGHT, skin=None, shirt=None,
                 jeans=None, hair=None):
    groups = _load_groups()
    bpy.ops.wm.obj_import(filepath=os.path.join(HUMAN_DIR, "base.obj"))
    body = bpy.context.selected_objects[0]
    body.name = name + "_body"
    me = body.data

    # joint centroids in world space (the importer has already made it Z-up)
    M = body.matrix_world
    def joint(key):
        idx = [i for i in _expand(groups[key]) if i < len(me.vertices)]
        v = Vector((0, 0, 0))
        for i in idx:
            v += M @ me.vertices[i].co
        return v / len(idx)

    J = {k: joint(k) for k in groups if k.startswith("joint-")}

    # scale so the figure is `height` tall, feet on z=0
    top = max((M @ v.co).z for v in me.vertices)
    ground = J["joint-ground"].z
    s = height / (top - ground)

    # strip helper geometry and joint cubes — keep only the body block
    keep = set(_expand(groups["body"]))
    bm_del = [v.index for v in me.vertices if v.index not in keep]
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i in bm_del:
        me.vertices[i].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")

    # bake the import rotation, then scale into metres about the feet
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    for v in me.vertices:
        v.co = (v.co - Vector((0, 0, ground))) * s
    for k in J:
        J[k] = (J[k] - Vector((0, 0, ground))) * s

    # ---------------------------------------------------------------- rig ---
    arm_data = bpy.data.armatures.new(name + "_arm")
    rig = bpy.data.objects.new(name + "_rig", arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")

    chain = list(SPINE) + _limbs("l") + _limbs("r") + _fingers("l") + _fingers("r")
    made = {}
    for bname, hkey, tkey, parent in chain:
        if hkey not in J or tkey not in J:
            continue
        b = arm_data.edit_bones.new(bname)
        b.head = J[hkey]
        b.tail = J[tkey]
        if (b.tail - b.head).length < 1e-4:          # degenerate: nudge
            b.tail = b.head + Vector((0, 0, 0.01))
        if parent and parent in made:
            b.parent = made[parent]
        made[bname] = b
    bpy.ops.object.mode_set(mode="OBJECT")

    # bind with automatic weights (fall back to envelopes if it fails)
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except Exception:
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")

    # ------------------------------------------------------------ clothes ---
    # the base mesh carries no body-region groups, so cut the garments out of
    # the anatomy itself: the figure is in T-pose here, so a height band plus a
    # reach limit is an exact and stable way to describe a shirt or a jean.
    hip = J["joint-pelvis"].z
    neck = J["joint-neck"].z
    ankle = min(J["joint-l-ankle"].z, J["joint-r-ankle"].z)
    elbow_x = abs(J["joint-l-elbow"].x)

    made_objs = {"body": body, "rig": rig}
    if shirt is not None:
        made_objs["shirt"] = _garment(
            body, rig, name + "_shirt", shirt, 0.017,
            lambda p: (hip - 0.10) <= p.z <= (neck - 0.015)
            and abs(p.x) <= elbow_x * 0.82)
    if jeans is not None:
        made_objs["jeans"] = _garment(
            body, rig, name + "_jeans", jeans, 0.013,
            lambda p: (ankle + 0.03) <= p.z <= (hip + 0.02))
    if jeans is not None:
        made_objs["shoes"] = _garment(
            body, rig, name + "_shoes", jeans, 0.013,
            lambda p: p.z <= (ankle + 0.05))
    if skin is not None:
        body.data.materials.clear()
        body.data.materials.append(skin)
    if hair is not None:
        made_objs["hair"] = _hair(body, rig, J, name + "_hair", hair)
    return rig, made_objs, J


def _garment(body, rig, name, mat, offset, inside):
    """copy a body region and push it out along normals => cloth over skin"""
    me = body.data
    idx = {v.index for v in me.vertices if inside(v.co)}
    if len(idx) < 50:
        return None
    g = body.copy()
    g.data = me.copy()
    g.name = name
    bpy.context.collection.objects.link(g)
    gm = g.data
    drop = [v.index for v in gm.vertices if v.index not in idx]
    bpy.context.view_layer.objects.active = g
    for o in bpy.context.selected_objects:
        o.select_set(False)
    g.select_set(True)
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in gm.vertices:
        v.select = v.index in set(drop)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    if not len(gm.vertices):
        bpy.data.objects.remove(g)
        return None
    d = g.modifiers.new("puff", "DISPLACE")
    d.mid_level = 0.0
    d.strength = offset
    sm = g.modifiers.new("smooth", "SMOOTH")
    sm.factor = 0.5
    sm.iterations = 3
    sol = g.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.004
    gm.materials.clear()
    gm.materials.append(mat)
    for m in list(g.modifiers):
        if m.type == "ARMATURE":
            g.modifiers.remove(m)
    a = g.modifiers.new("rig", "ARMATURE")
    a.object = rig
    g.parent = rig
    return g


def _hair(body, rig, J, name, mat):
    """a simple swept cap over the skull — reads as short hair in low light"""
    head = J.get("joint-head")
    if head is None:
        return None
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16,
                                         radius=0.093, location=head)
    h = bpy.context.active_object
    h.name = name
    h.scale = (1.03, 1.12, 0.86)
    h.location = head + Vector((0, 0.010, 0.082))
    h.data.materials.append(mat)
    for p in h.data.polygons:
        p.use_smooth = True
    a = h.modifiers.new("rig", "ARMATURE")
    a.object = rig
    h.parent = rig
    hb = h.vertex_groups.new(name="head")
    hb.add(range(len(h.data.vertices)), 1.0, "REPLACE")
    return h


# ------------------------------------------------------------------ pose ----
# Bone-local Euler angles are only trustworthy on the spine, whose bones point
# straight up so local X really is "bend forward". Arms and legs point sideways
# and downwards, so their local axes are scrambled relative to the anatomy.
# Those get IK instead: we say where the hand or foot goes in world space and
# let the solver find the joint angles, which is also how the limb stays
# planted when the torso moves.

def pose(rig, bone, rx=0.0, ry=0.0, rz=0.0):
    pb = rig.pose.bones.get(bone)
    if pb is None:
        return
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (radians(rx), radians(ry), radians(rz))


def _empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    bpy.context.collection.objects.link(e)
    e.location = loc
    return e


def add_ik(rig, name_prefix="ik"):
    """
    Give the rig hand/foot goals plus elbow and knee poles.
    Returns a dict of empties you can move to pose the figure.
    """
    ctrl = {}
    pairs = (("hand", "forearm", 2, "elbow"), ("foot", "shin", 2, "knee"))
    for side in ("l", "r"):
        for goal, bone, count, pole_name in pairs:
            pb = rig.pose.bones.get("%s_%s" % (bone, side))
            if pb is None:
                continue
            tip = rig.matrix_world @ pb.tail
            tgt = _empty("%s_%s_%s" % (name_prefix, goal, side), tip)
            root = rig.pose.bones.get(
                "%s_%s" % ("upperarm" if goal == "hand" else "thigh", side))
            base = rig.matrix_world @ root.head
            mid = rig.matrix_world @ pb.head
            # push the pole out in front (elbows) or behind (knees)
            away = 0.6 if goal == "foot" else -0.6
            pol = _empty("%s_%s_%s" % (name_prefix, pole_name, side),
                         mid + Vector((0, away, 0)))
            ik = pb.constraints.new("IK")
            ik.target = tgt
            ik.chain_count = count
            ik.pole_target = pol
            ik.pole_angle = radians(-90)
            ctrl["%s_%s" % (goal, side)] = tgt
            ctrl["%s_%s" % (pole_name, side)] = pol
    return ctrl


def break_stance(rig, ctrl, cue_line_x=0.0, bed_z=0.79, ball_y=-0.495,
                 handed="r"):
    """
    A right-handed break, described the way a coach would: the cue runs up
    the aim line, the bridge hand plants on the cloth a forearm's length
    behind the ball, the grip hand sits near the butt, the back foot lines up
    under the cue and the front foot steps forward and across. The spine
    hinges at the hips so the chin drops onto the line of the shot.
    """
    o = 1.0 if handed == "r" else -1.0
    # stand the figure behind the ball, turned to face up the aim line (+Y).
    # the base mesh imports facing -Y, so it needs the half turn.
    rig.rotation_euler = (0.0, 0.0, math.pi - radians(19) * o)
    rig.location = (cue_line_x + 0.185 * o, ball_y - 1.10, 0.0)

    # torso hinge — spine bones point up, so local X is a clean forward bend
    pose(rig, "pelvis", rx=34)
    pose(rig, "spine_01", rx=13)
    pose(rig, "spine_02", rx=11)
    pose(rig, "spine_03", rx=8)
    pose(rig, "chest", rx=5)
    pose(rig, "neck", rx=-30, rz=13 * o)
    pose(rig, "head", rx=-20, rz=7 * o)

    # limb goals in world space
    ctrl["hand_l"].location = (cue_line_x - 0.005, ball_y - 0.30, bed_z + 0.045)
    ctrl["hand_r"].location = (cue_line_x + 0.058 * o, ball_y - 0.95, bed_z + 0.105)
    ctrl["foot_l"].location = (cue_line_x - 0.26 * o, ball_y - 0.92, 0.045)
    ctrl["foot_r"].location = (cue_line_x + 0.20 * o, ball_y - 1.34, 0.045)
    # elbows out and back, knees forward — keeps the limbs from inverting
    ctrl["elbow_l"].location = (cue_line_x - 0.55 * o, ball_y - 0.55, bed_z + 0.30)
    ctrl["elbow_r"].location = (cue_line_x + 0.66 * o, ball_y - 1.16, bed_z + 0.40)
    ctrl["knee_l"].location = (cue_line_x - 0.30 * o, ball_y - 0.30, 0.50)
    ctrl["knee_r"].location = (cue_line_x + 0.24 * o, ball_y - 0.80, 0.46)

    # hands: bridge fingers splayed on the cloth, grip fingers wrapped
    for d in range(1, 6):
        pose(rig, "f%d_1_l" % d, rx=-22, rz=(d - 3) * 8)
        pose(rig, "f%d_2_l" % d, rx=-34)
        pose(rig, "f%d_3_l" % d, rx=-28)
        curl = 64 if d > 1 else 36
        pose(rig, "f%d_1_r" % d, rx=-curl)
        pose(rig, "f%d_2_r" % d, rx=-curl - 6)
        pose(rig, "f%d_3_r" % d, rx=-curl + 8)


def stroke(ctrl, back, cue_line_x=0.0, bed_z=0.79, ball_y=-0.495, handed="r"):
    """
    back = metres the grip hand is drawn away from address.
    Only the grip hand moves; the bridge, stance and spine stay locked, which
    is exactly what a player's pre-shot routine looks like from the side.
    """
    o = 1.0 if handed == "r" else -1.0
    ctrl["hand_r"].location = (cue_line_x + 0.058 * o,
                               ball_y - 0.95 - back,
                               bed_z + 0.105 + back * 0.10)
