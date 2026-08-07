# NYC Dive-Bar Pool Room — Complete Execution Handoff (2026-08-06, v2)

You are the implementing agent. This is your entire work order: environment
fixes, atmosphere upgrades, a refreshed 15-image gallery, and the fully
finished **break film with physics-driven sound**. It was written by the agent
that shipped the pocket revision, the register rebuild, and the tap fix. It
assumes you have no other context. Follow it literally, in the order of
Section 12. Where it says "verify," run the command and read the output before
continuing. Anything marked INVARIANT is not yours to reinterpret.

There is exactly **one human checkpoint** in this whole run (Section 6.4 —
David picks the break take from your top 3). Everything else you complete
without asking.

David's decisions, already made — do not re-ask:
- Film = the break only, EXACTLY ~30 seconds, physics-first, Soderbergh
  grammar: locked-off cameras, quick 1–3 s venue cuts, real-time 2–3 s
  break, a held overhead of where the balls land, then 1–2 s settle
  glances. No slow motion. No follow-up shots, no game logic.
- David picks the break take from agent-narrowed top 3 (one pause).
- Sound = ON: physics-timed ball/cushion/pocket sounds + low room tone.
  No music.
- Delivery = 1080p24 film + all 15 gallery stills re-rendered with the new
  atmosphere. Site gets both.

---

## 0. Ground truth

| Thing | Value |
|---|---|
| Project root | `/Users/davidmarsh/Desktop/Pool Table Test/nyc-dive-bar-pool-room` |
| Blender | `/Applications/Blender.app/Contents/MacOS/Blender` (5.2.0 LTS, only install) |
| Python (non-Blender) | `/Users/davidmarsh/Desktop/Pool Table Test/.venv/bin/python` (3.12; pooltool breaks on 3.14; numpy available) |
| ffmpeg / cwebp | `/opt/homebrew/bin/ffmpeg`, `/opt/homebrew/bin/cwebp` (installed, verified) |
| Git remote | `github.com/omgitsthedm/nyc-dive-bar-pool-room`, branch `master` |
| Live site | `pool-table-test.netlify.app`; site id file `../.netlify-site-id` |
| Frozen environment master | `blend/poolroom_master.blend` |
| Derived static preview | `blend/poolroom_pool_rebuild_preview.blend` |
| Derived gameplay scene | `blend/poolroom_gameplay_preview.blend` |
| Environment lock | `reports/environment_lock.json` — 2,143 objects, 82 materials, `de99efd0…` |
| Pool-system lock | `reports/pool_system_lock.json` — 355 objects, 30 materials, `0d7d3949…` |
| Geometry contract | `assets/data/table_wpa_geometry.json`, SHA `afe868b3…` — NEVER EDIT |
| Physics profile | `assets/data/pool_physics_profile.json` — NEVER EDIT (Section 1) |
| Frozen control break | `assets/data/shots/break_control.json`, trajectory hash `98d46617…` |

INVARIANT — three-blend discipline:
- Master is rebuilt only by `scripts/build_all.py`, only for the revisions
  this document authorizes (R1, A1–A6). Never edit any blend by hand.
- Static preview comes from `scripts/23_rebuild_pool_system.py` (reads master).
- Gameplay blend comes from `scripts/102_bake_pool_playback.py` (reads
  preview). It is regenerated output.
- Blends are git-ignored. After the run, copy all three into
  `blend-backups/<date>-film-run/`.

INVARIANT — deploy guard (this account hosts other client sites; an unflagged
deploy once landed on the wrong one):

```bash
cd "/Users/davidmarsh/Desktop/Pool Table Test/nyc-dive-bar-pool-room"
out=$(netlify deploy --prod --dir site --site "$(cat ../.netlify-site-id)" 2>&1)
echo "$out" | grep -qi "pool-table-test" || echo "WRONG SITE — ABORT"
```

INVARIANT — asset provenance: any downloaded asset (audio samples included)
must be CC0/public-domain, and its source URL, license, file hash and byte
size must be appended to `docs/SOURCE_MANIFEST.md` before use. If you cannot
verify the license, synthesize instead (Section 7.3 gives you the recipe).

---

## 0.5 Preflight (run these before anything; all four must pass)

```bash
cd "/Users/davidmarsh/Desktop/Pool Table Test/nyc-dive-bar-pool-room"
df -h . | tail -1                 # REQUIRE ≥ 25 GB free (film frames + stills + backups)
pgrep -x Blender && echo "GUI OPEN — STOP" || echo "no GUI"   # a GUI Blender with a project file open can silently save over a lock-managed blend; require none
git status --porcelain | head    # REQUIRE clean (or only files this run will touch)
netlify status | head -8 && gh auth status 2>&1 | head -3     # both must show authenticated
```

Wrap every render longer than 10 minutes in `caffeinate -dims <command>` so
the Mac cannot sleep mid-run. If any preflight fails, fix it or stop and
report — do not start a multi-hour run on a machine that can fall asleep,
run out of disk, or has a human's Blender window open on the same files.

---

## 1. THE PRIME DIRECTIVE — physics

The film's entire value is **balls behaving naturally**. Naturalness comes
from measured physics constants validated by contract, not from taste.

### 1.1 Authority chain (never redesign)

```
pooltool 0.6.0 (deterministic event solver, in .venv)
  → scripts/100_validate_pool_physics.py   15/15 contracts
  → scripts/101_export_pool_shot.py        240 Hz trajectory + exact event states → assets/data/shots/*.json
  → scripts/102_bake_pool_playback.py      location/quaternion F-curves into gameplay blend
  → scripts/103_validate_pool_playback.py  216/216 parity checks
```

Blender is a playback device (max errors: 0.015 mm, 0.069°). The scene has
**zero rigid bodies** and validators fail if one appears. Ball motion is
never hand-keyed. Ever.

### 1.2 Constants (locked; changing any = corrupting the deliverable)

57.15 mm / 0.168 kg balls · sliding friction 0.20 · rolling resistance
0.125 m/s² · sidespin decay 22 rad/s² · ball-ball restitution 0.97, friction
0.06–0.07 · cushion calibrated to ≈0.818 normal rebound · capture = ball
center crossing the 2D `PTX_SolverPocket_*` circle (3D `PTX_ShelfDrop_*` is
construction only). These pass every gate no matter what you set them to —
the gates check consistency, not truth — which is exactly why you are
forbidden to touch them. A wrong constant is the only silent failure in this
project.

### 1.3 Paid-for lessons (do not relearn)

1. Fractional-frame sampling: integer rounding once caused stutter AND
   pocket-snap. `102` interpolates between bracketing samples — keep it.
2. Event keys beat neighbor samples: Blender merges keys closer than ~0.01
   frame; `102` writes exact collision states last so they win — keep it.
3. Pocket drops are free-fall + one damped bounce (`103` checks continuity).
4. Cue/rack are staged after transform evaluation (parenting-order bug once
   collapsed them to origin) and the cue tip matches pooltool's a/b/theta
   contact to 0.00005 m/s.
5. Orientation integrates in collision-split segments (regression-tested).

### 1.4 Physics gate — run FIRST, before any other work

```bash
cd "/Users/davidmarsh/Desktop/Pool Table Test/nyc-dive-bar-pool-room"
../.venv/bin/python scripts/100_validate_pool_physics.py --repeat 10      # expect: physics audit: 15/15 passed
../.venv/bin/python scripts/91_validate_pool_geometry_contract.py         # expect: "passed": 68
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_gameplay_preview.blend -P scripts/103_validate_pool_playback.py   # expect: 216/216 passed
```

Any lower number: stop, fix, re-run. Nothing else proceeds on a red gate.

---

## 2. Work item R1 — register stands complete on top of the shelf

**Verified problem:** the register (base at `BACK_X + 0.20, BAR_Y, 0.92`, on
the `BAR_BackCabinet` top) sits in a 0.82 m bay cut only into bottle-shelf
row 0. Rows are `shelf_z = 1.18 + i * 0.34` in `scripts/30_build_bar.py`
(search `register_gap`): 1.18 / 1.52 / 1.86. The machine's crown tops at
≈1.59, so **row 1 (z 1.52) runs through its head**, and the under-shelf
fluorescent strip (material key `backbar_tube`, material name
`MAT_Bar_OldFluorescentTube`) crosses behind the drum.

**Fix (edit `scripts/30_build_bar.py` only):**
1. In the back-shelf loop, apply the row-0 split-around-`register_gap` logic
   to row `i == 1` too — including its `BAR_BackShelfLip_*` and any
   `BAR_BackShelfDust_*` at that row. Row 2 (1.86) stays full width.
2. Split every `backbar_tube`-material strip whose Y-span crosses
   `BAR_Y ± 0.41` into two flanking segments. No glow behind the machine.
3. The register does not move and does not shrink. Shelves yield.
4. Add camera `CAM_Audit_Register_50mm`: position `(BACK_X + 1.15, BAR_Y - 0.35, 1.35)`
   in `scripts/72_build_pool_audit_cameras.py`... **correction** — the
   register is environment, so add it in `scripts/70_build_cameras.py` with
   the other environment cameras, aimed at `(BACK_X + 0.20, BAR_Y, 1.25)`,
   50 mm lens. Register it in `scripts/83_render_pool_audit.py`'s
   `AUDIT_CAMERAS` tuple so it renders with the audit set.

**Acceptance:** ceremony green (Section 10); a render from
`CAM_Audit_Register_50mm` shows the full machine, paw feet to crown, with
clear air above the crown and no strip light crossing it.

---

## 3. Work items A1–A6 — atmosphere

### A1. Haze (biggest lever)
- New collection `07_ATMOSPHERE` (outside frozen collections — pool
  atmosphere is explicitly editable). Object `ATM_RoomHaze_Volume`: interior
  cube fitted 10 cm short of walls/ceiling, Principled Volume, density
  0.008 (render 13-CAM test at 0.004/0.008/0.012, keep best; far wall may
  lose at most ~1 stop), anisotropy +0.3, tint (1.0, 0.97, 0.92).
- ENGINE SPLIT (INVARIANT): Cycles stills use the REAL volume and hide the
  legacy fake cones (`ATM_PoolBeam_*`); EEVEE film hides the volume and uses
  the cones. Reason: this project measured EEVEE volumetrics rendering as
  blocky froxel dots on dark walls, and a camera inside a volume box can
  render black.
- IMPLEMENT THE SPLIT EXACTLY LIKE THIS (no other mechanism): the SAVED
  state of every blend keeps `ATM_RoomHaze_Volume.hide_render = True` and
  the cones visible (EEVEE-safe default, and the validators fingerprint the
  saved state). The RENDER ENTRY SCRIPTS flip it in memory, never saving:
  at the top of `scripts/84_render_cinematic_stills.py` (Cycles path) set
  `bpy.data.objects["ATM_RoomHaze_Volume"].hide_render = False` and
  `hide_render = True` for every object whose name starts `ATM_PoolBeam`;
  the film render script does the inverse. Render scripts already never
  save the file — keep it that way, and the locks never see the toggle.
- Verify all 15 stills cameras render non-black with the volume enabled
  (draft samples are fine for the check).

### A2. Cool accents (breaks the amber monotone)
- Cool leak at the service door (5500–6000 K, low power, motivated by
  `MAT_Env_ServiceDoor_UnderGlow`), cool CRT spill in the payphone corner.
  Optional third: restroom cage light goes colder.
- INVARIANT: every light needs a visible motivator; update the motivated-
  lights count expected by `95_audit_realism`/`96_audit_environment_staging`
  from 25/25 to the new N/N. An unmotivated light is a validator failure.

### A3. Peeling paper corners
3–4 curled flaps (≤8 cm silhouette, 5–20 mm lift, subdivided + rolled, same
paper texture, real shadows): two on the wheat-paste history fields, one near
the dartboard, one behind the payphone. Worn, never trashy (cleanliness rule).

### A4. Wet floor life
Inside `MAT_Env_Floor_NeglectedConcrete` only (no new floor meshes): 2–3
masked gloss patches near drink rail/bar aisle (roughness 0.08–0.15, soft
falloff) + one mop-arc roughness gradient near the bar front.

### A5. Ceiling age
One pressed-tin panel sagged 8–12 mm (proportional edit in the tin builder) +
a water-stain ring texture patch near the restroom corner.

### A6. Neon imperfection
±10–15% per-tube emission variance across POOL and EXIT; one POOL tube at
70% ("tired"). Film phase: give ONLY the tired tube a 0.5–2 Hz flicker
F-curve. Stills: static variance.

---

## 4. Gallery refresh (all 15 stills)

After R1 + A1–A6 pass the ceremony:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_pool_rebuild_preview.blend -P scripts/84_render_cinematic_stills.py
```

(no camera args = all 15; Cycles, 96 spp, 1600×900; ~50–70 min total). Then
regenerate ALL webps (`cwebp -quiet -q 82 -m 6 <png> -o site/img/opening/<slug>.webp`
— the slug map is the existing filenames), deploy with the guard, and
byte-verify every image (`curl` each live URL, `cmp` against local).

---

## 5. Break candidate pipeline (deterministic — no dice)

Cue position, speed, and spin are SOLVER INPUTS. A candidate is a parameter
tuple, perfectly reproducible. You are not rolling dice; you are sweeping a
grid.

### 5.1 Shot schema
Create `assets/data/shots/candidates/breaks_sweep.json` — a list of shots:

```json
{ "id": "b_03", "cue_ball_y_offset_m": 0.05, "speed_mps": 10.73,
  "aim_jitter_deg": 0.15, "a": 0.0, "b": 0.12, "theta_deg": 0.0 }
```

Sweep: `cue_ball_y_offset_m` ∈ {−0.10, −0.05, 0, +0.05, +0.10} (along the
head string), `speed_mps` ∈ {9.8, 10.73, 11.6} (22–26 mph),
`b` ∈ {0.0, +0.12} (a touch of follow), `aim_jitter_deg` ∈ {0, ±0.15}.
That's 5×3×2×3 = 90 candidates. Extend `scripts/101_export_pool_shot.py`
with a `--shot <json>` argument that reads one tuple and simulates it
(default behavior without the flag must stay byte-identical: re-export the
control break and verify the trajectory hash is still `98d46617…` before and
after your edit — that is your no-regression proof).

### 5.2 Culling rules (encode exactly; solver-side, fast, no rendering)
Simulate all 90 (solver only, ~seconds each). REJECT any candidate where:
1. Cue ball is pocketed (scratch) — auto-reject.
2. Fewer than 4 object balls contact a cushion (illegal/weak break).
3. Spread failure: fewer than 12 of 15 object balls end ≥ 150 mm from their
   rack position.
4. Settle time > 12 s of action.
5. Any ball ends resting in a jaw mouth blocking a pocket circle center
   (looks broken to a lay viewer even though it's physical).
SCORE survivors: `score = balls_pocketed * 3 + rails_hit + spread_m + (1 if 8ball survives else 0) * 2`
(compute spread as mean final distance from rack centroid, meters). Rank,
keep top 3.

### 5.3 Top-3 proofs
For each finalist: bake into a THROWAWAY copy (never overwrite
`poolroom_gameplay_preview.blend` yet — pass `--out` to `102`), render a
6-frame proof set + a 10-second EEVEE overhead flyover at 720p, filenames
`renders/break_candidates/<id>/…`.

### 5.4 THE ONE PAUSE (mandatory)
Present David the three candidates: per candidate one contact sheet + the
10-second clip + one line of stats (balls pocketed, rails, spread, duration).
Ask: "Which break is the film?" **Do not proceed until he answers. Do not
pick for him. This is the only question you are allowed to ask in the whole
run.** Logistics: leave all proof files in `renders/break_candidates/`,
surface the three clips and sheets directly to David in chat, then END YOUR
TURN and wait. Do not poll, loop, or time out into picking one yourself —
steps 1–3 of Section 12 are already complete and committed at this point,
so the run is safe to sit paused for hours or days.

### 5.5 Freeze
Winner becomes `assets/data/shots/break_film.json`. Record its trajectory
SHA-256 in `docs/QA_REPORT.md` and `HANDOFF.md`. Bake it into the real
gameplay blend (`102`), validate (`103`, 216/216). The control break stays
untouched as the regression fixture.

---

## 6. The film (EEVEE, 1080p24, 30 seconds, physics-first)

### 6.1 Engine decision (already made — follow it)
The film is ~30 s ≈ 720 frames at 1080p24. It renders in EEVEE (this is how
the phase-1 break film shipped), with the A1 engine-split haze (fake cones
ON, real volume OFF), target 10–25 s/frame → ~2–5 h total. Render each shot
as a sequential frame range (sequential frames are 5–8× faster than random
access here — shader compile amortizes; measured project fact). Stills
remain Cycles. Nobody renders an animation in Cycles on this Mac.

### 6.2 Shot list — 30 seconds, Soderbergh grammar, physics is the star

David's direction: 30 seconds total; the venue gets 1–3 second QUICK cuts;
the break takes 1–3 seconds; then an overhead of where the balls land; the
last seconds are quick 1–2 s shots. Shoot it the way Soderbergh would:

- **Every camera is LOCKED OFF. Zero pans, zero dollies.** The energy comes
  from cutting, not moving. One exception: nothing. Static frames only.
- **Compose off-center and shoot through foregrounds** — through the tap
  handles, past the register drum's shoulder, between booth backs, under
  the fixture shades. Frames within frames; haze doing depth.
- **Warm against cool in the same frame** wherever possible (practicals vs
  the A2 accents). Lived-in reads through detail, not duration.
- **The edit is cut to the physics.** Act-2 cut points are DERIVED from the
  trajectory event list (pocket-drop and hard-collision timestamps), not
  placed by feel. Write the cut list programmatically from
  `break_film.json` events, then render exactly the frames each shot needs.
- No titles, no text, no camera moves, no slow motion. Real time is the
  flex: these are the actual physics.

THE CUT (≈30 s, 24 fps, ≈720 frames):

COLD OPEN — the room in glances (0:00–0:07, five static cuts):
1. 0:00.0–0:01.5 `CAM_Audit_StreetNeon_35mm` — neon in the wet glass.
2. 0:01.5–0:03.0 `CAM_Bar_Reverse_35mm` reframed tighter on the register
   drum + shelf light (duplicate as `CAM_Film_Register_50mm`).
3. 0:03.0–0:04.5 `CAM_Audit_PatronBarware_55mm` — condensation pint, lime
   wheel, open tab.
4. 0:04.5–0:06.0 `CAM_Audit_BoothPatina_60mm` — cracked vinyl, ring ghosts.
5. 0:06.0–0:07.0 `CAM_Audit_Lighting_35mm` — fixture cones in the haze,
   rack soft below. (J-cut: the cue's address sounds start under this shot.)

ADDRESS (0:07–0:10):
6. 0:07.0–0:09.0 NEW `CAM_Film_CueAddress_85mm` — low behind the cue ball
   down the head string, shallow DOF on the rack; cue settles to address.
7. 0:09.0–0:10.0 NEW `CAM_Film_TipInsert_100mm` — macro insert: tip a
   chalk's-width off the cue ball. One second of held breath.

THE BREAK (0:10–0:12.5):
8. 0:10.0–0:12.5 back to `CAM_Film_CueAddress_85mm` — strike and scatter,
   REAL TIME, ~2.5 s. Hard cut while balls are still moving.

WHERE THEY LAND (0:12.5–0:18):
9. 0:12.5–0:18.0 NEW `CAM_Film_BreakOverhead_24mm` — locked-off god shot,
   full table top-down: the spread develops, rails return, pockets swallow.
   The longest shot in the film. Nothing moves but physics.

THE SETTLE, IN GLANCES (0:18–0:28, quick cuts, each cut ON an event
timestamp from the trajectory — pocket drops and last hard rail contacts):
10–14. Five 1–2 s static inserts chosen from the winning take's actual
   events, in this priority: (a) a ball dropping into a leather basket
   (shoot from the pocket-audit angles, e.g. `CAM_PoolAudit_Corner_85mm`
   reframed), (b) a ball dying against a cushion nose, (c) sidespin
   visibly bleeding off a slowing ball (red spin-reference dot on the cue
   ball), (d) the cue ball drifting to its final stop, (e) the last ball
   anywhere to stop moving. Build these as `CAM_Film_Insert_A…E`; pick
   framings AFTER the take is frozen, because the framings depend on where
   the balls actually go.

STILLNESS (0:28–0:30):
15. 0:28.0–0:30.0 `CAM_Table_ThreeQuarter_50mm` — the settled table in the
    haze, one breath, cut to black.

New cameras (`CAM_Film_*`) are DUPLICATES built in
`scripts/70_build_cameras.py`; never move or repurpose the named audit
cameras (validators expect them static). Insert framings for shots 10–14
are authored after Section 5.5 freezes the take.

Camera propagation: cameras live OUTSIDE both locks (the freeze table says
cameras stay editable, and the pool lock covers only table/ball/proxy
objects). After adding or editing `CAM_Film_*`, rerun
`23_rebuild_pool_system.py` → `102_bake_pool_playback.py` →
`103_validate_pool_playback.py` so the cameras exist in the gameplay blend
you render from; both locks must still report PASS unchanged — no re-bank.

Pre-roll contingency for shots 6–8: the bake stages rack-lift and cue
address BEFORE the strike. If the baked pre-roll is shorter than the 3 s
the address shots need, HOLD the first address frame to fill — do not
re-bake, do not stretch physics time.

### 6.3 Slow motion — CUT from this film (David, 2026-08-06)
The 30-second cut has NO slow motion; real time is the point. For any
future replay request, the honest technique is documented here and only
here: re-bake the strike window at a stretched time scale from the SAME
frozen 240 Hz trajectory (never interpolate renders, never re-roll).
Precedent: phase 1's 1 kHz re-sim bullet time.

### 6.4 Render + encode (write `scripts/105_render_film.py`, modeled on
`scripts/84_render_cinematic_stills.py`'s structure — argparse, per-camera
loop, timing report)
- ONE global frame counter for the whole film:
  `film_frame(n) = n` where `n = round(film_time_s * 24)`, frames 0–719.
  Each shot in 6.2 is a contiguous film-frame range; render every shot into
  the SAME `renders/film_frames/%04d.png` numbering so ffmpeg assembles one
  pass with no concat step.
- Scene-time mapping (INVARIANT, same constant as audio):
  `scene_time_s = film_time_s − 10.0` relative to the strike; i.e. the
  baked strike event lands exactly at film frame 240. Shots 1–5 (cold
  open) are static environment frames — render them at any pre-strike
  scene frame where the cue/rack staging looks correct, held for their
  full range (a held frame is re-rendered once and copied, not re-rendered
  per frame).
- Per shot: bind `scene.camera` to the 6.2 camera, set the scene frame
  range from the mapping, EEVEE, 1920×1080, 24 fps, motion blur ON.
- Assemble: `ffmpeg -framerate 24 -i renders/film_frames/%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart site/break-film_silent.mp4`
- Poster: the frame at film 0:28.0 (frame 672, the settle-wide) →
  `cwebp -q 82` → `site/img/break-film-poster.webp`.

---

## 7. Sound (physics-driven; this is why the film will feel real)

### 7.1 Source of truth
The frozen `break_film.json` trajectory contains the solver's EVENT LIST
(collision type, time, participating balls, velocities) — `103` already
reads it for parity checks; reuse the same parser. Every audio hit is placed
at the event's exact time. Nothing is hand-timed.

### 7.2 Event → sound mapping (write `scripts/110_build_film_audio.py`, .venv python + numpy)
- ball–ball → "clack" sample. Gain = clamp(impact_speed / 8.0, 0.12, 1.0),
  perceptual: `gain = (v/vmax)^0.7`. Pitch variance ±3% random per hit
  (seed the RNG with the trajectory hash so audio is deterministic too).
- ball–cushion → soft "thump", gain from normal velocity, −8 dB vs clacks.
- pocket capture → leather "pluck" + basket rumble (two layers).
- cue strike → distinct hard "crack" (one event, the loudest single sound).
- The break itself: the first 50 ms after cue impact will stack many
  ball-ball events — cap simultaneous overlaps at 6 loudest to avoid
  clipping; sum, then peak-normalize the master to −1 dBFS.
- Timeline mapping for the 30 s cut: audio events are placed at
  `event_time + 10.0 s` (the strike lands at 0:10 in the film) for shots
  6–15; the overhead and insert shots all view the SAME continuous timeline,
  so one single mix covers the whole film — no per-shot audio work.
- Cold open (0:00–0:07): room tone only, plus a CC0 neon-buzz loop if PATH A
  finds one (optional). J-cut from 0:06: one soft cue-butt tap and cloth
  brush lead in under the fixture shot. The cue STRIKE at 0:10 is the first
  and loudest hard sound in the film — the quiet before it is deliberate.
- Because Act-2 cuts land ON event timestamps, the picture cuts and the
  sound hits are the same list — verify by printing both tables side by
  side; they must match to the frame.
- Room tone bed: −34 dBFS low bar rumble under everything, faded in/out.
- Output: 48 kHz stereo WAV, constant power pan by ball X position (subtle,
  ±20%). Mux: `ffmpeg -i break-film_silent.mp4 -i film_mix.wav -c:v copy -c:a aac -b:a 192k site/break-film.mp4`.

### 7.3 Samples — two allowed paths only
- PATH A (preferred): CC0 one-shots (billiard clack, felt thump, leather
  pocket, room tone). Only CC0/public domain. Append each to
  `docs/SOURCE_MANIFEST.md` with URL, license, SHA-256, bytes. If license
  is unclear → do not use.
- PATH B (fallback, fully offline): synthesize with numpy — clack = 2–6 kHz
  band-passed noise burst, 8 ms attack, 60 ms exponential decay, plus a
  1.8 kHz damped sine partial; cushion thump = 150–400 Hz noise, 120 ms
  decay; pocket = 90 Hz sine thud + short noise; room tone = brown noise
  low-passed at 300 Hz, −34 dBFS. Synthesized assets need no manifest entry
  but note the generator script in `docs/SOURCE_MANIFEST.md`.
- Either path: audio must remain deterministic (fixed seed, recorded hashes).

### 6.5 Final-film acceptance (before the site ships it)
- `ffprobe site/break-film.mp4` → duration 29.5–31.0 s, 1920×1080, 24 fps,
  h264 + aac streams present, file < 60 MB.
- Extract and LOOK at one frame per shot (15 frames): no black frames, no
  missing objects, the register/taps/table all present, haze reads.
- The overhead shot's final frame must match the frozen trajectory's
  terminal ball positions (compare against the settled-table proof render).
- Poster exists and is the 0:28 settle-wide frame.
- Plays in a browser (open the deployed URL after ship; confirm 200 + plays).

### 7.4 Audio acceptance
- Event count in the mix == event count in the trajectory JSON (print both).
- No sample clipping (report true peak ≤ −1 dBFS).
- Watch the first 3 seconds after impact with waveform + event table side
  by side: every visible collision has a sound, every sound has an event.

---

## 8. Site update

`site/index.html` gains ONE block above the 15 images: the film,
`<video controls poster="img/break-film-poster.webp" preload="metadata">`
with `break-film.mp4`. No autoplay (it has sound), no captions, no copy —
the silent-page rule still governs (zero explanatory text, zero JS). All 15
refreshed webps ship in the same deploy. Deploy with the guard; byte-verify
the mp4, poster, and all 15 images against local.

---

## 9. Commits (after each numbered phase, not one giant commit)

Order: (1) R1 + ceremony; (2) A1–A6 + ceremony + stills refresh + deploy;
(3) candidate pipeline code + sweep results; (4) frozen `break_film.json`
post-pick + rebake; (5) film frames excluded, film mp4 + audio script +
manifest + site + deploy. Message style: what changed, which locks/hashes
moved, gates observed. Push after each. Never commit blends, `tmp/`,
`renders/sweep/`, or `renders/film_frames/` (add the latter to
`.gitignore`).

---

## 10. Environment-revision ceremony (exact; run per environment batch)

```bash
cd "/Users/davidmarsh/Desktop/Pool Table Test/nyc-dive-bar-pool-room"
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/build_all.py
#   REQUIRED: "[audit] 93/93 passed"; realism + staging 0 required failures.
#   "BUILD COMPLETED WITH REQUIRED FAILURES" is EXPECTED (env-lock drift only).
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_master.blend -P scripts/98_validate_environment_lock.py -- --write
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_master.blend -P scripts/23_rebuild_pool_system.py
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_pool_rebuild_preview.blend -P scripts/99_bank_pool_system_lock.py
#   VERIFY first. Drift diff must show objects/geometry EMPTY; only derived-
#   material fingerprint cascade + environment_lock_changed acceptable → then --write.
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_pool_rebuild_preview.blend -P scripts/90_validate_scene.py      # 93/93
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_pool_rebuild_preview.blend -P scripts/102_bake_pool_playback.py
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_gameplay_preview.blend -P scripts/103_validate_pool_playback.py  # 216/216
/Applications/Blender.app/Contents/MacOS/Blender -b blend/poolroom_gameplay_preview.blend -P scripts/98_validate_environment_lock.py # PASS
```

Then: sync counts + BOTH lock hashes in `HANDOFF.md`, `README.md`,
`docs/QA_REPORT.md` (grep the old hashes); back up blends. The control-break
trajectory hash `98d46617…` must be unchanged by any environment work.

## 11. Hard don'ts

- No rigid bodies. No hand-keyed balls. No physics-constant edits, ever,
  for any reason, including "it looks better."
- No re-rolling breaks outside the Section 5 sweep; no picking the take
  yourself; no second question to David beyond Section 5.4.
- No lock re-banks except as the ceremony's approval step for THIS
  document's items. Never edit `table_wpa_geometry.json`.
- No unmotivated lights. No filth (worn, never dirty). No text/copy on the
  page or in the film. No non-CC0 audio. No Cycles animation renders.
- No deploy without the guard. No blends/frames/tmp in git.
- `scripts/83_render_pool_audit.py` keeps rendering isolation variants after
  your requested cameras — kill it once your frames exist.

## 12. Execution order (the whole run)

1. Section 1.4 baseline gate → green or stop.
2. R1 register bay → ceremony → audit render proof.
3. A1–A6 (one batch) → ceremony → 15-still Cycles refresh → webp → deploy →
   byte-verify → commit/push.
4. Candidate sweep (90 sims) → cull → top-3 proofs → **PAUSE: David picks.**
5. Freeze `break_film.json` → rebake → 216/216 → commit/push.
6. Film cameras + timeline → EEVEE 1080p24 frames → slow-mo re-bake window →
   assemble silent mp4.
7. Audio script → event-placed mix → mux → acceptance checks (7.4).
8. Site block + poster → deploy with guard → byte-verify mp4/poster/15
   images → final commit/push → blend backups → update this file's header
   with completion date and final hashes.

Budget expectation: sims minutes; stills ~1 h; film ~2–5 h; audio minutes.
If any gate goes red and two fix attempts fail, STOP and write a "BLOCKED"
section at the top of this file with the exact command and output — do not
improvise around a red gate.

---

## 13. APPENDIX — exact implementations for the four judgment items

These four items previously assumed implementer skill. They no longer do.
The code below was written against the REAL schemas in this repo (verified
2026-08-06 against `assets/data/shots/break_control.json` and the scripts).
Copy it, adjust only where a comment says ADJUST, and keep every marked
invariant.

### 13.A The audio mixer — `scripts/110_build_film_audio.py` (complete)

The trajectory JSON schema you are reading (verified):
`events` = list of `{"type": str, "time_s": float, "ids": [str], "balls":
[{"id": str, "initial": {"position_m": [x,y,z], "velocity_mps": [x,y,z],
"omega_rad_s": [...], "state": str}, "final": {...}}]}`.
Event types present: `stick_ball` (the cue strike, exactly one),
`ball_ball`, `ball_linear_cushion`, `ball_pocket`, plus motion transitions
`sliding_rolling` / `rolling_stationary` (NOT sounds — skip them, except
`rolling_stationary` may be read to find when the last ball stops).
Ball tracks: `balls[<id>] = {"samples": …, "capture_time_s": float|null,
"pocket_id": str|null, "number": int, …}`. `coordinate_contract` maps pool
coords to Blender world for panning.

```python
"""110_build_film_audio.py — deterministic physics-timed mix for the film.
Run with the project venv python. Writes reports/film_audio_manifest.json
and renders/film_audio/film_mix.wav. No external deps beyond numpy."""
import argparse, hashlib, json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
FILM_OFFSET_S = 10.0          # the strike lands at 0:10 in the film
FILM_LEN_S = 30.0
PAN_SCALE = 0.20              # +/-20% constant-power pan by pool X

def _load_shot(path):
    data = json.loads(Path(path).read_text())
    assert data["schema"] == "pool-shot-trajectory/v1"
    return data

def _seed_from(data):
    # deterministic audio: RNG seeded by the trajectory hash
    return int(data["trajectory_sha256"][:8], 16)

def _env(n_attack, n_decay):
    a = np.linspace(0.0, 1.0, max(n_attack, 1))
    d = np.exp(-np.linspace(0.0, 6.0, max(n_decay, 1)))
    return np.concatenate([a, d])

def _synth_clack(rng):
    n = int(0.068 * SR)
    noise = rng.standard_normal(n)
    # crude 2-6 kHz bandpass via FFT masking (deterministic, dependency-free)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec[(freqs < 2000) | (freqs > 6000)] = 0.0
    body = np.fft.irfft(spec, n)
    partial = np.sin(2 * np.pi * 1800 * np.arange(n) / SR) * 0.35
    s = (body / (np.abs(body).max() + 1e-9) + partial) * _env(int(0.008*SR), n - int(0.008*SR))[:n]
    return s / (np.abs(s).max() + 1e-9)

def _synth_thump(rng):
    n = int(0.12 * SR)
    noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise); freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec[(freqs < 150) | (freqs > 400)] = 0.0
    s = np.fft.irfft(spec, n) * _env(int(0.004*SR), n)[:n]
    return s / (np.abs(s).max() + 1e-9)

def _synth_pocket(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 9.0)
    rattle = _synth_thump(rng)
    s = thud
    s[: len(rattle)] += rattle * 0.5
    return s / (np.abs(s).max() + 1e-9)

def _synth_crack(rng):
    s = _synth_clack(rng)
    n = int(0.02 * SR)
    s[:n] += rng.standard_normal(n) * np.exp(-np.linspace(0, 8, n)) * 0.8
    return s / (np.abs(s).max() + 1e-9)

def _room_tone(rng, n):
    # brown noise low-passed ~300 Hz at -34 dBFS
    w = np.cumsum(rng.standard_normal(n)); w /= (np.abs(w).max() + 1e-9)
    spec = np.fft.rfft(w); freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec[freqs > 300] = 0.0
    tone = np.fft.irfft(spec, n)
    return tone / (np.abs(tone).max() + 1e-9) * (10 ** (-34 / 20))

def _impact_speed(event):
    # relative speed of the two participants at event start
    vs = [np.array(b["initial"]["velocity_mps"]) for b in event["balls"]]
    if len(vs) == 1:
        return float(np.linalg.norm(vs[0]))
    return float(np.linalg.norm(vs[0] - vs[1]))

def _pan(event, half_w=0.635):
    xs = [b["initial"]["position_m"][0] for b in event["balls"]]
    return float(np.clip((np.mean(xs) / half_w) * PAN_SCALE, -1, 1))

def build(shot_path, out_dir):
    data = _load_shot(shot_path)
    rng = np.random.default_rng(_seed_from(data))
    samples = {"stick_ball": _synth_crack(rng), "ball_ball": _synth_clack(rng),
               "ball_linear_cushion": _synth_thump(rng),
               "ball_pocket": _synth_pocket(rng)}
    n_total = int(FILM_LEN_S * SR)
    left = np.zeros(n_total); right = np.zeros(n_total)
    placed = []
    audible = [e for e in data["events"] if e["type"] in samples]
    # cap overlapping hits in any 50 ms window to the 6 loudest
    audible.sort(key=lambda e: (round(e["time_s"] / 0.05), -_impact_speed(e)))
    window_counts = {}
    for e in audible:
        w = round(e["time_s"] / 0.05)
        window_counts[w] = window_counts.get(w, 0) + 1
        if window_counts[w] > 6:
            continue
        t = e["time_s"] + FILM_OFFSET_S
        if t >= FILM_LEN_S:
            continue
        v = _impact_speed(e)
        gain = float(np.clip((v / 8.0) ** 0.7, 0.12, 1.0))
        if e["type"] == "ball_linear_cushion":
            gain *= 10 ** (-8 / 20)
        s = samples[e["type"]]
        # ±3% deterministic pitch variance via resample-by-index
        rate = 1.0 + (rng.random() - 0.5) * 0.06
        idx = np.clip((np.arange(int(len(s) / rate)) * rate).astype(int), 0, len(s) - 1)
        s = s[idx] * gain
        i0 = int(t * SR); i1 = min(i0 + len(s), n_total)
        pan = _pan(e)
        lg, rg = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        left[i0:i1] += s[: i1 - i0] * lg
        right[i0:i1] += s[: i1 - i0] * rg
        placed.append({"type": e["type"], "time_s": e["time_s"],
                       "film_time_s": t, "gain": gain, "ids": e["ids"]})
    tone = _room_tone(rng, n_total)
    left += tone; right += tone
    peak = max(np.abs(left).max(), np.abs(right).max())
    target = 10 ** (-1 / 20)                     # -1 dBFS true peak
    if peak > target:
        left *= target / peak; right *= target / peak
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "film_mix.wav"
    pcm = np.stack([left, right], axis=1)
    pcm16 = (np.clip(pcm, -1, 1) * 32767).astype("<i2")
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(SR)
        handle.writeframes(pcm16.tobytes())
    manifest = {"shot": str(shot_path), "events_total": len(audible),
                "events_placed": len(placed), "sample_rate": SR,
                "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
                "placed": placed}
    (ROOT / "reports" / "film_audio_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n")
    print("audio: placed %d/%d events -> %s" %
          (len(placed), len(audible), wav_path))
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--shot", default=str(ROOT / "assets/data/shots/break_film.json"))
    p.add_argument("--out", default=str(ROOT / "renders/film_audio"))
    a = p.parse_args()
    raise SystemExit(build(a.shot, Path(a.out)))
```

Acceptance additions: `events_placed` must equal `events_total` minus only
overlap-capped hits; print both. If PATH A (CC0 samples) is used instead of
the synths, load the WAVs in place of `_synth_*` outputs — everything else
stays identical.

### 13.B The `--shot` extension to `scripts/101_export_pool_shot.py` (exact)

Verified anchors: `101`'s `main()` already has `--fixture`, `--sample-rate`,
`--out` (lines ~17–22). The strike is built in
`scripts/pool_game_physics.py` from a fixture row dict — grep
`cue_speed_mps` there (≈line 292): `"V0": row["cue_speed_mps"],
"phi": row["phi_deg"], "theta": row["theta_deg"]` — meaning speed/aim/spin
already flow from a plain dict. Implementation:

1. In `101`, add `parser.add_argument("--shot", type=Path, default=None)`.
2. When `--shot` is given, load the candidate JSON
   (schema in Section 5.1) and build the SAME row dict the control fixture
   uses, overriding: `cue_speed_mps = speed_mps`,
   `phi_deg = base_phi + aim_jitter_deg`, `theta_deg`, spin offsets
   `a`, `b`, and the cue-ball start position shifted by
   `cue_ball_y_offset_m` along the head string. Find where the control
   fixture defines the cue ball start and phi (grep `break_control` /
   `phi` in `pool_game_physics.py`); pass your values through the same
   code path — do not write a parallel simulator.
3. Output name: `--out assets/data/shots/candidates/out/<id>.json`.
4. NO-REGRESSION PROOF (mandatory, run before and after your edit):
   `../.venv/bin/python scripts/101_export_pool_shot.py` with no args, then
   `python - <<'E'` … read the JSON and print `trajectory_sha256` `E` —
   it must print `98d46617…` both times. If it changes, your edit leaked
   into the default path; fix before continuing.

### 13.C Peeling paper flaps — complete builder (drop into `scripts/55_age_and_story.py`)

Placement anchors are DATA, not judgment: wall art is laid out from
`C.DD_WALL_ART_LAYOUT` (tuples of `(name, wall, horizontal, z, width,
height, tilt)` — see `scripts/50_set_dress.py` ≈line 187). Curl corners of
named art planes. Add to config:
`DD_PAPER_CURLS = [(art_name, corner, lift_m, roll_deg), …]` with four
entries; corners are `"SW"|"SE"|"NW"|"NE"`; use lifts 0.008–0.020 and rolls
40–120°. Builder:

```python
def _paper_curl(art_object_name, corner, lift, roll_deg, mats):
    """A curled corner flap matching an existing flat art plane.

    The flap is an 8x8 grid strip parented to the art plane's corner,
    rolled around the corner's diagonal axis with per-row angle growth, so
    the free tip lifts off the wall while the attached edge stays flush."""
    import bmesh
    from mathutils import Matrix, Vector
    art = bpy.data.objects[art_object_name]
    w = art.dimensions.y * 0.16   # flap spans ~16% of the art width
    h = art.dimensions.z * 0.16
    mesh = bpy.data.meshes.new("ENV_PaperCurl_" + art_object_name + corner)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=0.5)
    sx = -1.0 if "W" in corner else 1.0
    sz = -1.0 if "S" in corner else 1.0
    for v in bm.verts:
        u = v.co.x + 0.5          # 0 at attached edge, 1 at free tip
        vv = v.co.y + 0.5
        angle = math.radians(roll_deg) * (u ** 1.6)
        r = max(lift / max(math.radians(roll_deg), 1e-3), 0.004)
        v.co = Vector((
            sx * (0.5 - u) * w,
            r * math.sin(angle) + lift * (u ** 2),   # off-wall
            sz * (0.5 - vv) * h))
        # rotate the roll around the corner diagonal so both edges peel
    bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new(mesh.name, mesh)
    # position at the chosen corner of the art plane, in the art's frame
    off = Vector((sx * (art.dimensions.y / 2 - w / 2), 0.001,
                  sz * (art.dimensions.z / 2 - h / 2)))
    ob.matrix_world = art.matrix_world @ Matrix.Translation(off)
    ob.data.materials.append(art.data.materials[0])   # same paper texture
    link_to_same_collection_as(art, ob)               # helper exists in L
    ob["paper_curl"] = True
    return ob
```

ADJUST: the exact bend math above is a starting shape — the acceptance is
geometric, not aesthetic: (a) attached edge within 1 mm of the wall plane,
(b) free tip lifted `lift` ± 30%, (c) flap casts a visible contact shadow in
a closeup render, (d) silhouette ≤ 8 cm. Render each flap once
(scratch camera 0.5 m away) and check those four; iterate the two
constants (`1.6` exponent, `r` floor) at most twice, then accept.

### 13.D Settle-insert cameras — formulas, not taste

All positions are computable from the frozen shot JSON. Pool→Blender:
`coordinate_contract` in the JSON (`blender_world_from_pool` +
`pool_origin`); bed height 0.762, ball center rest z = 0.790575.

Selection (write as a small script; run after the take freezes):
1. Load events + per-ball tracks. Let `P` = ball_pocket events sorted by
   time, `C` = ball_linear_cushion events after 1.5 s sorted by impact
   speed desc, `S` = per-ball final rest positions, `t_end` = last
   `rolling_stationary` time.
2. Insert A (pocket drop): first event in `P` (skip if none). Camera:
   `pocket_center + outward_xy * 0.55` at z = bed + 0.25, look at
   `pocket_center` at z = bed − 0.05, 85 mm, f/2.8-equivalent DOF focused
   on the pocket. `outward_xy` = unit vector from table center to pocket.
3. Insert B (cushion die): first event in `C`. Camera: stand 0.60 m from
   the impact point ALONG the cushion (pick the direction with more table
   in frame: dot the view axis against table center), z = bed + 0.18,
   100 mm, look at the impact point at ball height.
4. Insert C (spin bleed): the ball with the highest |omega_z| at
   t = 2.0 s (read `samples`). Frame it dead center, camera 0.45 m away
   perpendicular to its travel direction, z = bed + 0.15, 100 mm — the red
   spin dot on the cue ball makes rotation legible; prefer the cue ball if
   its |omega| ≥ 60% of the max.
5. Insert D (cue ball stops): camera 0.50 m behind the cue ball's final
   rest along its final travel direction, z = bed + 0.20, 85 mm, focus on
   the ball, table receding beyond.
6. Insert E (last ball stops): ball whose `rolling_stationary` is `t_end`;
   same framing rule as D.
7. Cut times: each insert covers `[event_time − 0.4 s, event_time + 1.0 s]`
   in trajectory time (+ FILM_OFFSET 10.0 s), clamped into 0:18–0:28 in
   priority order A→E; drop inserts that don't fit; a minimum of 4 must
   fit or you widen the window to 0:17–0:28.
8. Build cameras `CAM_Film_Insert_A…E` with those transforms in
   `scripts/70_build_cameras.py` (duplicated pattern), render, and check
   each insert's subject is inside the middle 50% of frame — if not, the
   look-at math has an axis error (the classic mistake is forgetting the
   pool→Blender offset; verify with the cue ball's known rest position
   first).

END OF APPENDIX — with this section, the four items are recipes like
everything else. A model that can follow Section 10 can follow this.
