"""
table_wpa.py — a 9-foot table built from the physics table's own geometry.

The previous version invented pocket shapes (cylindrical holes) and that is
most of why it read wrong: a real pocket is a *mouth* between two lips where
the cushion nose changes direction, with jaw faces cut back at 142 degrees at
the corners and 104 at the sides, a shelf of slate the ball must cross, and a
back draft on the vertical cut.

Rather than model that from scratch and hope it matches, this builds every
cushion and every jaw directly from the segments pooltool is actually
bouncing balls off. pooltool's table is configured from wpa_spec, so the
chain is: WPA document -> wpa_spec.py -> pooltool table -> this geometry.
The rendered cushion nose is the physics cushion nose, by construction.

    build(mats, table) -> dict of parts
"""
import bmesh
import bpy
import math
from math import atan2, cos, sin, radians
from mathutils import Vector

import wpa_spec as S


class _Seg:
    def __init__(self, d):
        self.p1 = d.get("p1")
        self.p2 = d.get("p2")
        self.center = d.get("center")
        self.radius = d.get("radius")


class _Pocket:
    def __init__(self, d):
        self.center = d["center"]
        self.radius = d["radius"]
        self.depth = d.get("depth", 0.08)


class _Segments:
    def __init__(self, lin, circ):
        self.linear = lin
        self.circular = circ


class TableGeometry:
    """
    The physics table's geometry, read back from table_wpa.json.

    Blender ships its own numpy so pooltool cannot be imported here; the
    numbers are exported once by export_table.py and consumed as data. Same
    segments, same pockets — just on the other side of a file.
    """

    def __init__(self, data):
        self.w = data["w"]
        self.l = data["l"]
        self.bed = data["bed"]
        self.ball_R = data["ball_R"]
        self.nose = data["nose"]
        self.cushion_segments = _Segments(
            {k: _Seg(v) for k, v in data["linear"].items()},
            {k: _Seg(v) for k, v in data["circular"].items()})
        self.pockets = {k: _Pocket(v) for k, v in data["pockets"].items()}


def load(path=None):
    import json
    import os
    if path is None:
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            "table_wpa.json")
    return TableGeometry(json.load(open(path)))


def make_specs():
    """A pooltool PocketTableSpecs carrying the WPA 9-foot numbers."""
    from pooltool.objects.table.specs import PocketTableSpecs
    length, width = S.TABLE_9FT
    return PocketTableSpecs(
        l=length,                       # sec.5  100 in
        w=width,                        # sec.5   50 in
        cushion_width=S.CUSHION_W,      # sec.7    2 in
        cushion_height=S.nose_height(),  # sec.7  63.5% of ball dia
        corner_pocket_width=S.CORNER_MOUTH,   # sec.9  4.5 in
        side_pocket_width=S.SIDE_MOUTH,       # sec.9  5.0 in
        corner_pocket_angle=S.CORNER_JAW_TUNE,
        side_pocket_angle=S.SIDE_JAW_TUNE,
        height=S.BED,                   # sec.2   30 in
        lights_height=S.BED + S.LIGHT_H,      # sec.15 44 in above the bed
    )


# --------------------------------------------------------------- helpers ---
def _obj(name, verts, faces, mat, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
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
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return ob


def _boolean(target, cutter):
    m = target.modifiers.new("cut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
        return True
    except Exception:
        target.modifiers.remove(m)
        return False


# K-66 cushion cross-section. x is distance back from the nose, z is height
# above the cloth. The nose sits at 63.5% of a ball diameter (WPA sec.7) so a
# ball is struck above its centre of mass and stays down on the rebound.
def _profile(nose_z, width):
    return [
        (0.0000, nose_z),                       # the nose itself
        (0.0075, nose_z + 0.0060),              # rise over the nose
        (width, nose_z + 0.0135),               # back top, under the rail cap
        (width, 0.0),                           # back bottom, on the slate
        (0.0045, 0.0),                          # front foot
    ]


def _extrude_any(name, path, normals, prof, mat):
    """Sweep an arbitrary (back-distance, height) cross-section along a path."""
    verts, faces = [], []
    n = len(prof)
    for p, nrm in zip(path, normals):
        back = Vector((-nrm.x, -nrm.y, 0.0))
        for (dx, dz) in prof:
            verts.append(Vector((p.x + back.x * dx, p.y + back.y * dx,
                                 p.z + dz)))
    for i in range(len(path) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append([a + k, a + k2, b + k2, b + k])
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(len(verts) - n, len(verts))))
    return _obj(name, verts, faces, mat)


# The wooden sub-rail the cushion is glued to (WPA sec.9 calls it the "rail
# liner"): it sits on the slate behind the cushion and its face is what the
# 142/104 degree pocket cuts are made through, so it is visible in every jaw.
def _subrail_profile(nose_z, cushion_w, rail_w):
    return [
        (cushion_w, 0.0),
        (cushion_w, nose_z + 0.0135),
        (rail_w, nose_z + 0.0135),
        (rail_w, 0.0),
    ]


def _extrude_profile(name, path, normals, nose_z, width, mat):
    """
    Sweep the cushion profile along `path`. `normals[i]` is the inward-facing
    table normal at path[i]; the profile's local +x runs *away* from the
    playfield (back towards the rail), +z is up.
    """
    prof = _profile(nose_z, width)
    verts, faces = [], []
    n = len(prof)
    for i, (p, nrm) in enumerate(zip(path, normals)):
        back = Vector((-nrm.x, -nrm.y, 0.0))    # into the rail
        for (dx, dz) in prof:
            # p already carries the bed height; dz is measured off the cloth
            verts.append(Vector((p.x + back.x * dx, p.y + back.y * dx,
                                 p.z + dz)))
    for i in range(len(path) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append([a + k, a + k2, b + k2, b + k])
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(len(verts) - n, len(verts))))
    return _obj(name, verts, faces, mat)


def _segment_paths(table):
    """
    Walk pooltool's cushion segments and return sweep paths.

    Linear segments are straight runs; circular segments are the rounded lips
    at each pocket jaw. For each we also need the inward normal so the profile
    leans the right way.
    """
    runs = []
    cx, cy = table.w / 2.0, table.l / 2.0

    for key, seg in table.cushion_segments.linear.items():
        p1 = Vector((seg.p1[0], seg.p1[1], 0.0))
        p2 = Vector((seg.p2[0], seg.p2[1], 0.0))
        d = (p2 - p1)
        if d.length < 1e-6:
            continue
        d.normalize()
        nrm = Vector((-d.y, d.x, 0.0))
        mid = (p1 + p2) * 0.5
        seg_len = (p2 - p1).length
        if seg_len < 0.20:
            # A jaw face. Its playing side is the pocket throat, not the
            # middle of the table, so orienting it towards the table centre
            # swings the cushion body around and buries it in the mouth.
            pc = min(table.pockets.values(),
                     key=lambda pk: (mid - Vector((pk.center[0], pk.center[1],
                                                   0.0))).length)
            to_pocket = Vector((pc.center[0], pc.center[1], 0.0)) - mid
            if to_pocket.length > 1e-9 and to_pocket.dot(nrm) < 0:
                nrm = -nrm                  # face the throat; body goes behind
        elif (Vector((cx, cy, 0)) - mid).dot(nrm) < 0:
            nrm = -nrm                      # main rail: face the playfield
        runs.append(("lin_%s" % key, [p1, p2], [nrm, nrm], None))

    for key, seg in table.cushion_segments.circular.items():
        c = Vector((seg.center[0], seg.center[1], 0.0))
        r = seg.radius
        # the arc spans between whichever linear endpoints touch this circle
        touch = []
        for lk, ls in table.cushion_segments.linear.items():
            for p in (ls.p1, ls.p2):
                v = Vector((p[0], p[1], 0.0)) - c
                if abs(v.length - r) < 1e-3:
                    touch.append(atan2(v.y, v.x))
        if len(touch) < 2:
            continue
        touch = sorted(set(round(t, 6) for t in touch))
        if len(touch) > 2:
            pairs = [(abs(touch[i + 1] - touch[i]), touch[i], touch[i + 1])
                     for i in range(len(touch) - 1)]
            _, a0, a1 = min(pairs)
        else:
            a0, a1 = touch[0], touch[1]
        while a1 - a0 > math.pi:
            a1 -= 2 * math.pi
        while a0 - a1 > math.pi:
            a1 += 2 * math.pi
        steps = 8
        path, normals = [], []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            p = c + Vector((cos(a) * r, sin(a) * r, 0.0))
            path.append(p)
            normals.append(Vector((cos(a), sin(a), 0.0)))   # outward from arc
        # These fillets are small (a 21 mm jaw radius against a 51 mm cushion
        # body). Sweeping the full profile inwards overshoots the arc centre
        # and folds the geometry back out across the pocket throat, so the
        # body is clamped to stay inside its own radius.
        runs.append(("arc_%s" % key, path, normals, min(r * 0.75, None)
                     if False else r * 0.75))
    return runs


def _pocket_outline(table, key, pocket):
    """
    Plan-view outline of one pocket opening, taken from the jaw geometry:
    the two lips, the jaw faces running back at the WPA cut angle, and an arc
    closing the throat behind them.
    """
    c = Vector((pocket.center[0], pocket.center[1], 0.0))
    pts = []
    for lk, ls in table.cushion_segments.linear.items():
        for p in (ls.p1, ls.p2):
            v = Vector((p[0], p[1], 0.0))
            if (v - c).length < pocket.radius * 2.4:
                pts.append(v)
    if len(pts) < 3:
        return None
    # Sort around the centroid of the points, not the pocket centre: the
    # pocket centre sits behind the jaws, outside this polygon, and sorting
    # about an exterior point yields a self-crossing outline that booleans
    # away to nothing.
    mid = Vector((0.0, 0.0, 0.0))
    for v in pts:
        mid += v
    mid /= len(pts)
    return sorted(pts, key=lambda v: atan2(v.y - mid.y, v.x - mid.x)), mid


def build(mats, table):
    """
    mats: cloth, slate, rail, cushion, facing, sight, pouch, wood, metal
    table: a pooltool Table built from make_specs()
    """
    W, L = table.w, table.l
    BED = S.BED
    NOSE = S.nose_height()
    parts = {}

    def bl(x, y, z=0.0):
        return Vector((x - W / 2.0, y - L / 2.0, BED + z))

    # ------------------------------------------------------------ cushions --
    # WPA sec.13 covers the cushions in the same cloth as the bed, stretched
    # over the rubber and tucked behind a featherstrip. Rendering them as bare
    # rubber in a different green is the single most obvious tell that a table
    # is modelled rather than photographed.
    cushions, subrails = [], []
    for name, path, normals, width in _segment_paths(table):
        wpath = [bl(p.x, p.y) for p in path]
        ob = _extrude_profile("cushion_" + name, wpath, normals, NOSE,
                              width or S.CUSHION_W, mats["cloth"])
        for p in ob.data.polygons:
            p.use_smooth = name.startswith("arc")
        cushions.append(ob)
        if width is None:                       # straight runs only
            sr = _extrude_any("subrail_" + name, wpath, normals,
                              _subrail_profile(NOSE, S.CUSHION_W, S.RAIL_W),
                              mats["wood"])
            subrails.append(sr)
        # the featherstrip: a thin dark reveal where the cloth is tucked in
        fs = _extrude_any("feather_" + name, wpath, normals,
                          [(S.CUSHION_W - 0.004, NOSE + 0.0100),
                           (S.CUSHION_W - 0.004, NOSE + 0.0140),
                           (S.CUSHION_W + 0.001, NOSE + 0.0140),
                           (S.CUSHION_W + 0.001, NOSE + 0.0100)],
                          mats["facing"])
        cushions.append(fs)
    parts["cushions"] = cushions
    parts["subrails"] = subrails

    # ------------------------------------------------------------ the bed ---
    outer_w = W + 2 * S.RAIL_W
    outer_l = L + 2 * S.RAIL_W
    slate = _box("slate", (outer_w, outer_l, S.SLATE_T),
                 bl(W / 2, L / 2, -S.SLATE_T / 2), mats["slate"])
    cloth = _box("cloth", (outer_w, outer_l, 0.0035),
                 bl(W / 2, L / 2, -0.00175), mats["cloth"])
    frame = _box("slate_frame", (outer_w + 0.02, outer_l + 0.02,
                                 S.SLATE_FRAME_T),
                 bl(W / 2, L / 2, -S.SLATE_T - S.SLATE_FRAME_T / 2),
                 mats["wood"])

    # ------------------------------------------------------------- rails ----
    # Rail cap: a wooden board bolted on top of the sub-rail. Its inner edge
    # overhangs the cushion by a few millimetres (the lip a ball rattles
    # against on a bad pot) and its outer edge projects slightly past the
    # cabinet, so the cap reads as a separate plank and not as one solid mass.
    cap_bot = NOSE + 0.0135
    cap_h = 0.032
    rail_top = cap_bot + cap_h
    LIP = 0.009                       # overhang towards the playfield
    OVER = 0.007                      # overhang past the cabinet
    cap_w = (S.RAIL_W + OVER) - (S.CUSHION_W - LIP)
    inner = S.CUSHION_W - LIP
    rails = []
    for sgn in (-1.0, 1.0):
        rails.append(_box(
            "rail_x%+d" % sgn, (cap_w, outer_l + 2 * OVER, cap_h),
            bl(W / 2 + sgn * (W / 2 + inner + cap_w / 2), L / 2,
               cap_bot + cap_h / 2), mats["rail"], bevel=0.0022))
        rails.append(_box(
            "rail_y%+d" % sgn, (W + 2 * inner, cap_w, cap_h),
            bl(W / 2, L / 2 + sgn * (L / 2 + inner + cap_w / 2),
               cap_bot + cap_h / 2), mats["rail"], bevel=0.0022))

    for r in rails:                    # flatten the bevel before booleans
        bpy.context.view_layer.objects.active = r
        for m in list(r.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                r.modifiers.remove(m)

    # ---------------------------------------------------- pockets, for real --
    # One cutter per pocket: the plan outline swept downward with the WPA back
    # draft so the throat opens as it descends, then subtracted from cloth,
    # slate and rails. This is the difference between a hole and a pocket.
    draft = math.tan(radians(S.BACK_DRAFT_DEG))
    holes = {}
    for key, pocket in table.pockets.items():
        res = _pocket_outline(table, key, pocket)
        if res is None:
            continue
        outline, mid = res
        c = mid
        # widen the outline slightly outward so the cut clears the jaw faces
        ring = []
        for v in outline:
            d = (v - c)
            if d.length < 1e-6:
                continue
            d.normalize()
            # pull the cut *inside* the jaw line: widening past it undercuts
            # the slate the jaw cushions sit on and leaves them floating
            ring.append(v - d * 0.004)
        # Build the cutter with bmesh: an n-gon lofted downward and outward
        # by the WPA back draft. Hand-built face lists get culled by
        # mesh.validate() when the winding disagrees, which silently produced
        # a cutter that removed nothing.
        depth = 0.34
        bm = bmesh.new()
        top_v = [bm.verts.new(tuple(bl(p.x, p.y, 0.055))) for p in ring]
        bm.faces.new(top_v)
        bm.verts.ensure_lookup_table()
        bot_v = []
        for p in ring:
            d = (p - c)
            d.normalize()
            q = p + d * (draft * depth)
            bot_v.append(bm.verts.new(tuple(bl(q.x, q.y, 0.055 - depth))))
        n = len(ring)
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((top_v[k2], top_v[k], bot_v[k], bot_v[k2]))
        bm.faces.new(list(reversed(bot_v)))
        bm.normal_update()
        me = bpy.data.meshes.new("cut_%s" % key)
        bm.to_mesh(me)
        bm.free()
        cutter = bpy.data.objects.new("cut_%s" % key, me)
        bpy.context.collection.objects.link(cutter)
        for target in [cloth, slate, frame] + rails + subrails:
            # a pocket legitimately misses the rails on the far side of the
            # table, so only an outright modifier failure is worth reporting
            if not _boolean(target, cutter):
                print("  POCKET CUT FAILED: %s on %s" % (key, target.name))
        holes[key] = (bl(c.x, c.y, 0.0), pocket.radius)
        bpy.data.objects.remove(cutter)

    parts["slate"], parts["cloth"], parts["frame"] = slate, cloth, frame
    parts["rails"] = rails
    parts["holes"] = holes

    # ------------------------------------------------ sights on the rail ----
    # sec.6: 18 sights, centres 3-11/16 in from the cushion nose, 12.5 in apart
    sp = S.sight_spacing(L)
    sights = []
    off = S.SIGHT_FROM_NOSE
    for sgn in (-1.0, 1.0):
        for i in range(1, 8):
            if i == 4:
                continue                       # the side pocket sits here
            y = L * i / 8.0
            sights.append(_box(
                "sight", (S.SIGHT_DIAMOND[1], S.SIGHT_DIAMOND[0], 0.0025),
                bl(W / 2 + sgn * (W / 2 + off), y, rail_top - 0.0012),
                mats["sight"], rot=(0, 0, radians(45))))
        for i in (1, 2, 3):
            sights.append(_box(
                "sight", (S.SIGHT_DIAMOND[1], S.SIGHT_DIAMOND[0], 0.0025),
                bl(W * i / 4.0, L / 2 + sgn * (L / 2 + off),
                   rail_top - 0.0012), mats["sight"], rot=(0, 0, radians(45))))
    parts["sights"] = sights

    # ------------------------------------------- drop pockets under the bed --
    # sec.11: baskets must hold at least six balls.
    pouches = {}
    for key, (c, r) in holes.items():
        depth = S.BALL_D * 1.9
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=22, ring_count=14, radius=r * 1.30,
            location=(c.x, c.y, BED - depth))
        p = bpy.context.active_object
        p.name = "pouch_%s" % key
        bm = bmesh.new()
        bm.from_mesh(p.data)
        for v in list(bm.verts):
            if v.co.z > 0.0:
                bm.verts.remove(v)
        bm.to_mesh(p.data)
        bm.free()
        p.data.materials.append(mats["pouch"])
        sol = p.modifiers.new("thick", "SOLIDIFY")
        sol.thickness = 0.005
        for f in p.data.polygons:
            f.use_smooth = True
        pouches[key] = p
    parts["pouches"] = pouches

    # ---------------------------------------------------------- cabinet -----
    apron_h = 0.20
    ax = outer_w / 2 + 0.010
    ay = outer_l / 2 + 0.010
    aprons = [
        _box("apron_l", (0.032, outer_l + 0.02, apron_h),
             (-ax, 0, BED - S.SLATE_T - apron_h / 2), mats["wood"], bevel=0.002),
        _box("apron_r", (0.032, outer_l + 0.02, apron_h),
             (ax, 0, BED - S.SLATE_T - apron_h / 2), mats["wood"], bevel=0.002),
        _box("apron_b", (outer_w + 0.02, 0.032, apron_h),
             (0, -ay, BED - S.SLATE_T - apron_h / 2), mats["wood"], bevel=0.002),
        _box("apron_t", (outer_w + 0.02, 0.032, apron_h),
             (0, ay, BED - S.SLATE_T - apron_h / 2), mats["wood"], bevel=0.002),
    ]
    leg = 0.115
    leg_h = BED - S.SLATE_T - apron_h
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            legs.append(_box(
                "leg", (leg, leg, leg_h),
                (sx * (ax - leg / 2 + 0.004), sy * (ay - leg / 2 + 0.004),
                 leg_h / 2), mats["wood"], bevel=0.003))
    parts["aprons"], parts["legs"] = aprons, legs
    parts["bl"] = bl
    parts["rail_top"] = rail_top
    return parts


def drop_rest(key, holes):
    """Where a ball settles once it has fallen through pocket `key`."""
    c, r = holes[key]
    return Vector((c.x, c.y, S.BED - S.BALL_D * 1.9 + S.BALL_R * 0.6))
