"""
export_table.py — freeze the physics table's geometry to JSON.

Blender ships its own numpy, so pooltool cannot be imported inside Blender.
Instead the physics side owns the geometry and writes it out; the renderer
reads this file and builds cushions and pockets from the very segments the
simulator bounces balls off.

    .venv/bin/python export_table.py        ->  table_wpa.json
"""
import json
import os

import pooltool as pt

import wpa_spec as S

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.join(HERE, "table_wpa.json")


def make_specs():
    from pooltool.objects.table.specs import PocketTableSpecs
    length, width = S.TABLE_9FT
    return PocketTableSpecs(
        l=length,                              # WPA sec.5  100 in
        w=width,                               # WPA sec.5   50 in
        cushion_width=S.CUSHION_W,             # WPA sec.7    2 in
        cushion_height=S.nose_height(),        # WPA sec.7  63.5% ball dia
        corner_pocket_width=S.CORNER_MOUTH,    # WPA sec.9  4.5 in
        side_pocket_width=S.SIDE_MOUTH,        # WPA sec.9  5.0 in
        # calibrated so the built jaws measure 142 / 104 degrees
        corner_pocket_angle=S.CORNER_JAW_TUNE,
        side_pocket_angle=S.SIDE_JAW_TUNE,
        height=S.BED,                          # WPA sec.2   30 in
        lights_height=S.BED + S.LIGHT_H,       # WPA sec.15  44 in above bed
    )


def build_table():
    specs = make_specs()
    if hasattr(pt.Table, "from_table_specs"):
        return pt.Table.from_table_specs(specs)
    return pt.Table(specs=specs)


def main():
    table = build_table()
    data = {
        "w": float(table.w),
        "l": float(table.l),
        "bed": S.BED,
        "ball_R": S.BALL_R,
        "nose": S.nose_height(),
        "cushion_width": S.CUSHION_W,
        "linear": {
            k: {"p1": [float(x) for x in s.p1],
                "p2": [float(x) for x in s.p2]}
            for k, s in table.cushion_segments.linear.items()
        },
        "circular": {
            k: {"center": [float(x) for x in s.center],
                "radius": float(s.radius)}
            for k, s in table.cushion_segments.circular.items()
        },
        "pockets": {
            k: {"center": [float(x) for x in p.center],
                "radius": float(p.radius),
                "depth": float(getattr(p, "depth", 0.08))}
            for k, p in table.pockets.items()
        },
    }
    json.dump(data, open(OUT, "w"), indent=1)
    print("wrote %s" % OUT)
    print("  %.4f x %.4f m playfield, %d linear + %d circular cushion "
          "segments, %d pockets" % (data["w"], data["l"], len(data["linear"]),
                                    len(data["circular"]), len(data["pockets"])))
    # verify the jaw cut angles against WPA sec.9 while we are here
    import math
    lin = data["linear"]

    def ang(seg):
        dx = seg["p2"][0] - seg["p1"][0]
        dy = seg["p2"][1] - seg["p1"][1]
        return math.degrees(math.atan2(dy, dx))

    print("  jaw check (WPA sec.9: corner 142 deg +1, side 104 deg +1):")
    for jaw, rail, label in (("1", "18", "corner"), ("4", "3", "side")):
        if jaw in lin and rail in lin:
            a = abs(ang(lin[jaw]) - ang(lin[rail])) % 180
            print("     seg %-2s vs rail %-2s -> %.1f deg  (%s)"
                  % (jaw, rail, 180 - a if a < 90 else a, label))


if __name__ == "__main__":
    main()
