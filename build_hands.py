"""
build_hands.py — the two hands that matter, and bodies as shape only.

The player is staged the way pool is actually shot: the bridge hand on the
cloth and the grip hand on the butt are lit and detailed, everything above
the elbows falls into shadow. That is not a dodge around the hard problem —
WPA sec.15 asks for at least 520 lux on the bed and rails while explicitly
warning that light on the players "should not be blinding", so a table lit to
spec in a dark room puts the hands in the light and the bodies in silhouette
on its own.

Hands come from the Blender Studio Human Base Meshes bundle (CC0):
    assets/human/blender_studio_human_base_meshes.blend  ->  "realistic_hand"

    bridge_hand(...) -> object      an open rail bridge, thumb cocked up
    grip_hand(...)   -> object      wrapped around the butt
    silhouette(...)  -> object      a body-shaped blocker, unlit
"""
import bpy
import math
import os
from math import radians
from mathutils import Vector

import wpa_spec as S

HERE = os.path.dirname(os.path.realpath(__file__))
BUNDLE = os.path.join(HERE, "assets", "human",
                      "blender_studio_human_base_meshes.blend")
HAND_OBJ = "realistic_hand"
BODY_OBJ = "realistic_body_male"


def _append(name):
    """Pull one object out of the CC0 bundle."""
    before = set(bpy.data.objects)
    bpy.ops.wm.append(filepath=os.path.join(BUNDLE, "Object", name),
                      directory=os.path.join(BUNDLE, "Object") + os.sep,
                      filename=name)
    new = [o for o in bpy.data.objects if o not in before]
    return new[0] if new else None


def _strip_modifiers(ob):
    """The bundle ships multires/subsurf; bake nothing, just drop them."""
    for m in list(ob.modifiers):
        try:
            ob.modifiers.remove(m)
        except Exception:
            pass


def _fit(ob, target_len, axis=1):
    """Scale so the hand reads life-size: wrist to fingertip ~19 cm."""
    ob.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    dims = ob.dimensions
    longest = max(dims)
    if longest > 1e-6:
        s = target_len / longest
        ob.scale = (s, s, s)
    bpy.context.view_layer.update()
    return ob


HAND_LEN = 0.195                    # wrist crease to middle fingertip


def load_hand(name, mat, mirror=False):
    ob = _append(HAND_OBJ)
    if ob is None:
        return None
    ob.name = name
    _strip_modifiers(ob)
    _fit(ob, HAND_LEN)
    if mirror:
        ob.scale = (-ob.scale.x, ob.scale.y, ob.scale.z)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def bridge_hand(mat, at, aim_deg=90.0):
    """
    The bridge hand, planted on the cloth behind the cue ball. `at` is where
    the heel of the hand sits; the cue rides the V between thumb and knuckle,
    so the hand is turned to face up the aim line and tipped forward onto the
    fingertips.
    """
    ob = load_hand("hand_bridge", mat)
    if ob is None:
        return None
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (radians(-72), radians(4), radians(aim_deg + 8))
    ob.location = at
    return ob


def grip_hand(mat, at, aim_deg=90.0):
    """The stroke hand, wrapped under the butt a hand's width from the end."""
    ob = load_hand("hand_grip", mat, mirror=True)
    if ob is None:
        return None
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (radians(-96), radians(-6), radians(aim_deg - 4))
    ob.location = at
    return ob


def silhouette(name, at, height=1.80, facing_deg=0.0, mat=None):
    """
    A body-shaped blocker. It is never lit — it exists to occlude, so it reads
    as a shoulder line and a head against the room, and nothing about its
    surface can look wrong because no surface is ever seen.
    """
    ob = _append(BODY_OBJ)
    if ob is None:
        return None
    ob.name = name
    _strip_modifiers(ob)
    bpy.context.view_layer.update()
    h = max(ob.dimensions)
    if h > 1e-6:
        s = height / h
        ob.scale = (s, s, s)
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (0, 0, radians(facing_deg))
    ob.location = at
    ob.data.materials.clear()
    if mat:
        ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    # keep it out of the light entirely: no bounce, no highlight, just mass
    ob.visible_diffuse = False
    ob.visible_glossy = False
    return ob


def shadow_material(name="silhouette"):
    """Near-black, fully rough — it only ever shows as an edge."""
    # A black emission shader, not a dark diffuse: diffuse still picks up the
    # lamp and turns the figure into a lit grey nude, which is exactly the
    # failure mode we are avoiding. Emission at zero renders pure black under
    # any lighting, so the body can only ever be a shape.
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    em.inputs["Strength"].default_value = 0.0
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def skin_material(name="skin"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.34, 0.20, 0.145, 1.0)
    b.inputs["Roughness"].default_value = 0.52
    try:
        b.inputs["Subsurface Weight"].default_value = 0.16
        b.inputs["Subsurface Radius"].default_value = (0.10, 0.035, 0.02)
    except Exception:
        pass
    return m
