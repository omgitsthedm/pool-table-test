# Pool Table Test — Session Handoff

**Date:** 2026-08-04
**Author:** Claude Code (Opus 5)
**Root:** `/Users/davidmarsh/Desktop/Pool Table Test`
**Live:** https://pool-table-test.netlify.app
**Netlify site id:** `6672b41c-ca69-458a-852d-c156b4b13e64`
**GitHub (phase 1):** https://github.com/omgitsthedm/pool-table-test

---

## What this session covered

Two distinct projects share this folder. They are **not** the same codebase and
should not be merged.

| | Phase 1 — Physics break film | Phase 2 — NYC dive-bar room |
|---|---|---|
| Location | this folder (root level) | `nyc-dive-bar-pool-room/` |
| Goal | simulate and render a real 8-ball break | photoreal static environment, 9-ft hero table |
| Physics | yes — pooltool | **none, by brief** |
| Table | 9-ft, built to WPA spec | 9-ft, built to WPA + Olhausen spec |
| Engine | EEVEE | Cycles (stills), EEVEE (sweep) |
| Status | delivered | table/room/bar/lighting done; dressing + 4K open |
| Next owner | — | **Codex** |

Phase 2 has its own detailed handoff at
`nyc-dive-bar-pool-room/HANDOFF.md`. Read that one before touching that project.

---

## Phase 1 — The physics break film

### What it is

A 30-second film of a real 8-ball break. Ball motion is not animated by hand:
`simulate_break.py` runs [pooltool](https://github.com/ekiefl/pooltool)
(Kiefl, JOSS 2024), exports trajectories, and `render_break.py` replays them
in Blender. The cushion the renderer draws and the cushion the simulator
bounces off are the **same number**, passed into the table spec — so no rail
rebound in the film is visually lying about where it happened.

Final cut: 720 frames, 30.000 s, 24 fps, 1920×1080, 12 MB.
Encode/deploy: `finish_break.sh`.

### The arc it went through

It started as a full 34-shot game with two AI players, a dive-bar set, and
bullet-time. That version shipped. It was then cut back, on request, to a
single break with no figure and no on-screen copy — because the figure was the
part that kept failing (see below) and the physics was the part worth showing.

### Six defects reported and fixed

Each traced to a specific cause, not guessed at:

| Symptom | Actual cause | Fix |
|---|---|---|
| Flickering | slate top and cloth top both at z=0 — coplanar faces z-fighting | slate sunk one cloth-thickness |
| Bottom lip round the cabinet | rail cap overhanging a vertical apron | sides raked 15° flush to the cap edge (Knight, *Epoxyworks* 1993) |
| Cue passing through the table | 4.5° elevation put the shaft under the cap at the head rail | 7.5°, clears with shaft radius to spare |
| Choppy balls after the break | `sample_at()` **rounded to an integer** physics sample | fractional sampling, interpolated between bracketing samples |
| Ball snapping into the pocket | drop was a linear lerp to rest | free fall under g, then one damped bounce |
| Cue in front of the ball | cue body extended along the shot direction; tip buried inside the ball | rotated 180°, tip offset to `BALL_R + 0.006` |

**The stutter and the pocket snap were the same bug.** One integer rounding
caused two separately-reported symptoms.

### The human figure — three attempts, abandoned

This is the main thing that did not work, and the reasoning matters more than
the code:

1. **Hand-built from the MakeHuman CC0 base mesh.** Rigged from the mesh's own
   joint markers, posed with IK. Anatomically proportioned and it did stand at
   the table correctly — but it read as amateur. Clothes were grown from the
   body by pushing vertex regions along their normals, which is a legitimate
   technique but not a substitute for modelled garments.
2. **Blender Studio production rigs** (Snow, Rain, Einar — free, CC-BY, no
   login, downloaded and tested). All are **stylised**: Pixar proportions,
   bunny-ear hair, a mechanical prosthetic arm. Beside a photoreal WPA-spec
   table they wreck the shot.
3. **Posing a production rig headlessly.** The head detached and floated off,
   the arms ignored the IK targets because CloudRig sits in FK by default and
   the switch is buried in a custom property block, and the body clipped the
   table.

**Root problem:** posing characters blind, with no viewport and ~5 minutes per
guess. Production rigs are built for a human dragging controls and watching.
More iterations were not going to converge.

**Resolution:** the figure was dropped and the cue became the only actor. If a
person is ever wanted, the realistic route is a human opening one of the
downloaded rigs and dragging the arms into a stance — two minutes
interactively versus hours of blind guessing.

### Files that matter

```
simulate_break.py     physics sim -> break9.json
render_break.py       the renderer (cameras, cue choreography, pocket drops)
table_wpa.py          9-ft table built to spec, feeds pooltool its own geometry
wpa_spec.py           every WPA constant
make_balls.py         ball textures
finish_break.sh       encode + deploy + push
out/break.mp4         the delivered film
```

---

## Phase 2 — NYC dive-bar pool room

Full brief: `CLAUDE-OPUS-5-NYC-DIVE-BAR-POOL-ROOM-HANDOFF.md` plus
`CLAUDE-CODE-AMENDMENT-01-PATCHES.md` (amendment wins on conflict). Both are
also vendored inside the project at `docs/references/`.

### State

**Builds clean, 24/24 audit checks pass.**

```bash
cd nyc-dive-bar-pool-room
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/build_all.py
```

Done: room shell (walls, pressed-tin ceiling, conduit, radiator, storefront),
the 109-component hero table, 16 exact balls in a legal rack, the bar with a
working bartender side, 25 procedural materials, the three-shade fixture with
motivated practicals, 4 required cameras, and a 12-second sweep film.

Not done: **set dressing (Phase 6)** and **final 4K/EXR delivery (Phase 8b)**.

### Measured, not claimed

Every figure below comes from `90_validate_scene.py` measuring evaluated
geometry — it never restates the constants it is checking.

```
Playing surface      1.270000 x 2.540000 m
Exterior (Cavalier)  1.549400 x 2.819400 m
Floor to bed / rail  0.762000 / 0.800100 m
Cushion nose         36.290 mm   (WPA 35.719-36.862)
Slate                25.400 mm, three pieces
Balls                16/16 within 0.1 mm of 57.15 mm, uniform scale
Rack apex            0.000000 m from the foot spot
Basket depth         6/6 in the 100-120 mm band
Rigid bodies         0
```

### Five bugs found and fixed — do not reintroduce

1. **Blender's default startup Cube.** Spans −1..1 m, exactly where the room
   sits. It swallowed the 85 mm camera whole (pure black renders) and was the
   white box occluding the rack in the three-quarter view. Diagnosed by
   ray-casting from the camera: centre ray hit `Cube` at 0.116 m while the
   target sat 0.788 m away with a perfect 1.000 aim dot product. Bootstrap now
   purges it; the audit asserts `no_stray_startup_objects == 0`.
2. **K-66 cushion cannot sit on the bed.** The rubber's own height (1 3/16 in
   = 30.16 mm) is *shorter* than the nose contact height (63.5% of ball
   diameter = 36.29 mm). Seating it on the bed inverts the 66° face and pulls
   the nose 2.7 mm off the playfield line. The rubber glues to the sub-rail
   face, base 18.7 mm above the cloth.
3. **EXACT booleans drop material slots.** A boolean against a material-less
   cutter contributes an empty slot to the target.
4. **Material `_new()` must reuse, not remove.** Removing and recreating a
   datablock orphans every object already using it — which happens whenever a
   later stage rebuilds a shared material like walnut.
5. **The triangle rack** was placed by a bad centroid rotation and collapsed
   into a single stray block in front of the 1 ball. Removed.

### Open defects

1. **Ball numbers map rotated. HIGH.** Blocks Amendment Patch 4's gate. The
   decal art is correct — `assets/textures/balls/ball_01.png` has an upright
   "1". The fault is the equirect projection in `lib.uv_sphere()`. Fix there,
   not by rotating the source art.
2. **Set dressing not started.** Room is architecturally complete and lit but
   not inhabited.
3. **Final 4K/EXR not rendered.** Projected ~8 machine-hours for 4 × 4K +
   1 × 6K — measured, inside the 24 h gate, no sample reduction needed.

---

## Deployment

Both projects publish to the **same Netlify site**. The site currently serves
Phase 2: the sweep film plus the four camera stills and the measured
dimension table.

**Absolute rule:** every deploy uses an explicit `--site` flag. This account
holds other client sites and an unflagged deploy has previously landed on the
wrong one.

```bash
netlify deploy --prod --dir site --site 6672b41c-ca69-458a-852d-c156b4b13e64
```

`finish_break.sh` and `nyc-dive-bar-pool-room/scripts/finish_sweep.sh` both
carry a post-deploy guard that greps the output for the site name and aborts
otherwise.

Phase 1's `out/break.mp4` is intact and was never at risk, but it is **not**
currently on the site — Phase 2 replaced it. One `cp` restores it.

---

## Environment notes worth keeping

* **Blender 5.2.0 LTS**, build 2026-07-14, at
  `/Applications/Blender.app/Contents/MacOS/Blender`. Single install, nothing
  on PATH, no Steam/Homebrew copy reachable.
* **Never pipe gate commands through `tail`/`head`** — it eats exit codes.
* **EEVEE volumetrics** render as blocky froxel artifacts on dark walls at
  this scale; use faked gradient-emission cones instead.
* **A camera inside a volume-scatter box renders black.** Keep atmosphere
  volumes above table-level camera heights.
* **Blender 5.x slotted actions:** `action.fcurves` may be empty — fall
  through `layers` → `strips` → `channelbags`.
* **pooltool needs Python 3.12**; 3.14 fails dependency resolution.

---

## Recommended next actions

1. **Codex takes Phase 2.** Start with the ball-number UV rotation — it is the
   one HIGH defect and it gates Amendment Patch 4. Then set dressing, then the
   final 4K delivery. `nyc-dive-bar-pool-room/HANDOFF.md` has the detail.
2. **Decide what the site should show.** Right now it is Phase 2's sweep. If
   both films should live there, the page needs a second video block.
3. **Phase 1 needs nothing.** It is delivered, committed, and pushed.
