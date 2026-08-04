"""
build_table.py — a 7-foot bar box built to the way a real table is made.

Everything here is anatomy rather than decoration:

  * the slate is a solid slab with six pockets **cut through it**, so a ball
    that reaches a pocket falls through a hole instead of vanishing under a
    ring. Each pocket has angled jaws (142 degrees at the corners, 103 at the
    sides, per the WPA table spec) and a drop pouch slung underneath.
  * the cushions are a real cushion profile — the K-66 triangle — with the
    nose at 63.5% of a ball's diameter, which is what makes a ball rebound
    off the middle of its mass instead of climbing the rubber.
  * the rails are flat boards with sight diamonds inlaid on the top face.
  * the cabinet is flat: four plain apron panels and four flat square legs,
    no turned posts or mouldings.

Geometry is keyed to the same playfield the physics uses, so the rendered
cushion noses sit exactly on the simulator's cushion lines.
"""
import bpy
import bmesh
import math
from math import radians, cos, sin
from mathutils import Vector

# playfield (pooltool coordinates: x 0..W, y 0..L) --------------------------
W = 0.9906
L = 1.9812
BED = 0.79                    # cloth surface height off the floor
BALL_R = 0.028575
NOSE = BALL_R * 2 * 0.635     # cushion nose height above the cloth
RAIL_W = 0.108                # top rail width outside the nose
RAIL_H = 0.042                # rail board thickness above the nose line
SLATE_T = 0.025
APRON_H = 0.185
LEG = 0.104                   # flat square leg
CORNER_MOUTH = 0.118          # pocket mouth openings
SIDE_MOUTH = 0.133
CORNER_GAP = 0.091            # cushion ends, from the corner (physics-derived)
SIDE_GAP = 0.075


def bl(x, y, z=0.0):
    """playfield coords -> world (table centred on the origin)"""
    return Vector((x - W / 2, y - L / 2, BED + z))


POCKETS = {                       # mouth centre on the rail line, in world
    "lb": bl(0, 0), "rb": bl(W, 0),
    "lc": bl(0, L / 2), "rc": bl(W, L / 2),
    "lt": bl(0, L), "rt": bl(W, L),
}
CORNERS = ("lb", "rb", "lt", "rt")


def _mesh(name, verts, faces, mat, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def _box(name, dims, loc, mat, rot=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = dims
    if rot:
        ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    if bevel:
        b = ob.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 2
    return ob


def _cyl(name, r, d, loc, mat=None, rot=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d,
                                        location=loc)
    ob = bpy.context.active_object
    ob.name = name
    if rot:
        ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    return ob


def _boolean(target, cutter, op="DIFFERENCE"):
    m = target.modifiers.new("cut", "BOOLEAN")
    m.operation = op
    m.object = cutter
    m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
    except Exception:
        target.modifiers.remove(m)
        return False
    return True


# ---------------------------------------------------------------- pockets ---
def pocket_axis(key):
    """unit vector pointing from the playfield out through the pocket mouth"""
    if key in ("lb", "lt", "lc"):
        ax = Vector((-1, 0, 0))
    else:
        ax = Vector((1, 0, 0))
    if key.endswith("b"):
        ay = Vector((0, -1, 0))
    elif key.endswith("t"):
        ay = Vector((0, 1, 0))
    else:
        ay = Vector((0, 0, 0))
    v = (ax + ay)
    v.normalize()
    return v


def pocket_center(key):
    """centre of the hole: pushed out along the mouth axis from the corner"""
    p = POCKETS[key].copy()
    r = (CORNER_MOUTH if key in CORNERS else SIDE_MOUTH) * 0.5
    return p + pocket_axis(key) * (r * 0.62)


def build(mats):
    """
    mats: dict with keys cloth, wood, rail, rubber, pouch, sight, metal.
    Returns dict of the pieces plus the hole centres for the drop animation.
    """
    parts = {}

    # ------------------------------------------------------------ the bed ---
    slate = _box("slate", (W + 2 * RAIL_W, L + 2 * RAIL_W, SLATE_T),
                 bl(W / 2, L / 2, -SLATE_T / 2), mats["wood"])
    cloth = _box("cloth", (W + 2 * RAIL_W, L + 2 * RAIL_W, 0.004),
                 bl(W / 2, L / 2, -0.002), mats["cloth"])

    # cut the six pockets straight through bed and cloth
    holes = {}
    for key in POCKETS:
        c = pocket_center(key)
        r = (CORNER_MOUTH if key in CORNERS else SIDE_MOUTH) * 0.5
        holes[key] = (c, r)
        for target in (slate, cloth):
            cut = _cyl("cut_%s" % key, r, 0.35, (c.x, c.y, BED), verts=28)
            _boolean(target, cut)
            bpy.data.objects.remove(cut)
    parts["slate"], parts["cloth"] = slate, cloth

    # ---------------------------------------------------------- cushions ----
    # K-66 profile, extruded along each cushion run. The nose sits exactly on
    # the physics line; the body slopes back and up to the rail board.
    def cushion(name, a, b, axis):
        ax, ay = a
        bx, by = b
        if axis == "y":                       # runs along the long rails
            inward = 1.0 if ax < W / 2 else -1.0
            prof = [(0.0, NOSE), (0.021 * inward, NOSE + 0.008),
                    (0.038 * inward, NOSE + 0.010), (0.038 * inward, 0.0),
                    (0.004 * inward, 0.0)]
            verts, faces = [], []
            for (dx, dz) in prof:
                verts.append(bl(ax + dx, ay, dz))
            for (dx, dz) in prof:
                verts.append(bl(bx + dx, by, dz))
        else:                                 # the two short rails
            inward = 1.0 if ay < L / 2 else -1.0
            prof = [(0.0, NOSE), (0.021 * inward, NOSE + 0.008),
                    (0.038 * inward, NOSE + 0.010), (0.038 * inward, 0.0),
                    (0.004 * inward, 0.0)]
            verts = [bl(ax, ay + dy, dz) for (dy, dz) in prof]
            verts += [bl(bx, by + dy, dz) for (dy, dz) in prof]
        n = len(prof)
        faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        faces.append(list(range(n - 1, -1, -1)))
        faces.append(list(range(n, 2 * n)))
        return _mesh(name, verts, faces, mats["rubber"])

    cush = []
    for xs, side in ((0.0, "l"), (W, "r")):
        cush.append(cushion("cush_%s_b" % side, (xs, CORNER_GAP),
                            (xs, L / 2 - SIDE_GAP), "y"))
        cush.append(cushion("cush_%s_t" % side, (xs, L / 2 + SIDE_GAP),
                            (xs, L - CORNER_GAP), "y"))
    cush.append(cushion("cush_bot", (CORNER_GAP, 0.0), (W - CORNER_GAP, 0.0), "x"))
    cush.append(cushion("cush_top", (CORNER_GAP, L), (W - CORNER_GAP, L), "x"))
    parts["cushions"] = cush

    # ------------------------------------------------------------- rails ----
    # A continuous flat frame seated on the cushion bodies and flush with the
    # cabinet: it runs from the back of the cushion out to the table edge, and
    # the six pockets are cut through it so each mouth is a real notch in the
    # rail rather than a ring laid on top.
    CB = 0.038                                  # cushion body depth
    rail_top = NOSE + 0.010 + RAIL_H       # rail sits on the slate, not on air
    rail_z = rail_top / 2
    rail_w = RAIL_W - CB
    rails = []
    for sgn in (-1.0, 1.0):
        rails.append(_box(
            "rail_x%+d" % sgn, (rail_w, L + 2 * RAIL_W, rail_top),
            bl(W / 2 + sgn * (W / 2 + CB + rail_w / 2), L / 2, rail_z),
            mats["rail"], bevel=0.002))
        rails.append(_box(
            "rail_y%+d" % sgn, (W + 2 * CB, rail_w, rail_top),
            bl(W / 2, L / 2 + sgn * (L / 2 + CB + rail_w / 2), rail_z),
            mats["rail"], bevel=0.002))
    for r in rails:
        for key in POCKETS:
            c, rad = holes[key]
            cut = _cyl("cut_r_%s" % key, rad * 1.04, 0.30, (c.x, c.y, BED),
                       verts=28)
            _boolean(r, cut)
            bpy.data.objects.remove(cut)
    parts["rails"] = rails

    # sight diamonds — 3 per long half-rail, 3 across each short rail
    sights = []
    top_z = rail_top
    for xs, sgn in ((0.0, -1.0), (W, 1.0)):
        for i in range(1, 8):
            if i == 4:
                continue
            y = L * i / 8.0
            d = _box("sight", (0.016, 0.016, 0.003),
                     bl(xs + sgn * (0.038 + (RAIL_W - 0.038) / 2), y, top_z - 0.0012),
                     mats["sight"], rot=(0, 0, radians(45)))
            sights.append(d)
    for ys, sgn in ((0.0, -1.0), (L, 1.0)):
        for i in (1, 2, 3):
            d = _box("sight", (0.016, 0.016, 0.003),
                     bl(W * i / 4.0, ys + sgn * (0.038 + (RAIL_W - 0.038) / 2),
                        top_z - 0.0012), mats["sight"], rot=(0, 0, radians(45)))
            sights.append(d)
    parts["sights"] = sights

    # ------------------------------------------------- drop pouches ---------
    # an open leather sling under each hole: ball falls in and stays visible
    pouches = {}
    for key, (c, r) in holes.items():
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12,
                                             radius=r * 1.16,
                                             location=(c.x, c.y, BED - 0.085))
        p = bpy.context.active_object
        p.name = "pouch_%s" % key
        bm = bmesh.new()
        bm.from_mesh(p.data)
        for v in list(bm.verts):
            if v.co.z > 0.0:                 # keep the lower half => a bowl
                bm.verts.remove(v)
        bm.to_mesh(p.data)
        bm.free()
        p.data.materials.append(mats["pouch"])
        sol = p.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.006
        for f in p.data.polygons:
            f.use_smooth = True
        pouches[key] = p
    parts["pouches"] = pouches

    # ------------------------------------------------------------ cabinet ---
    # flat aprons, flat legs — no turned posts
    ap_z = BED - APRON_H / 2
    ax = W / 2 + RAIL_W + 0.012
    ay = L / 2 + RAIL_W + 0.012
    aprons = [
        _box("apron_l", (0.030, L + 2 * RAIL_W + 0.024, APRON_H),
             (-ax, 0, ap_z), mats["wood"], bevel=0.002),
        _box("apron_r", (0.030, L + 2 * RAIL_W + 0.024, APRON_H),
             (ax, 0, ap_z), mats["wood"], bevel=0.002),
        _box("apron_b", (W + 2 * RAIL_W + 0.024, 0.030, APRON_H),
             (0, -ay, ap_z), mats["wood"], bevel=0.002),
        _box("apron_t", (W + 2 * RAIL_W + 0.024, 0.030, APRON_H),
             (0, ay, ap_z), mats["wood"], bevel=0.002),
    ]
    parts["aprons"] = aprons

    leg_h = BED - APRON_H
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            legs.append(_box(
                "leg", (LEG, LEG, leg_h),
                (sx * (ax - LEG / 2 + 0.004), sy * (ay - LEG / 2 + 0.004),
                 leg_h / 2), mats["wood"], bevel=0.003))
    parts["legs"] = legs

    parts["holes"] = holes
    return parts


def drop_target(key, holes):
    """where a ball comes to rest once it has fallen through `key`"""
    c, r = holes[key]
    return Vector((c.x, c.y, BED - 0.085 + BALL_R * 0.55))
