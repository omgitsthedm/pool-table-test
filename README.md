# Pool Table Test — a physics-true 8-ball game, rendered

A standalone demo: two moderate-skill AI players play a **complete game of
8-ball** under real billiards physics, and the whole game is rendered as a
cinematic film on a photoreal 7-foot bar table in an out-of-focus room.

**Demo:** [pool-table-test.netlify.app](https://pool-table-test.netlify.app) · film in `out/` once rendered.

## How it works

```
simulate_game.py ──► game.json ──► render_game.py ──► frames/ ──► ffmpeg ──► film
   (pooltool)        (frozen)        (Blender 5.2)
```

1. **Physics & the game** — [`simulate_game.py`](simulate_game.py) uses
   [pooltool](https://github.com/ekiefl/pooltool) (Kiefl, JOSS 2024) for
   event-based billiards physics: ball-ball impacts, cushion rebounds,
   sliding→rolling friction, spin. On top of it: two AI players with a
   moderate-skill model (aim wander that grows with shot distance, speed
   misjudgement, unintentional english), 8-ball flow (open table → groups on
   first legal pot → run your group → the 8), scratches with ball-in-hand,
   and a house rule: an 8 potted on the break is re-spotted (APA scores that
   a win; it would make a one-shot film). Every shot's trajectories are
   exported at 60 Hz with roll orientations integrated from angular velocity.
2. **The frozen take** — pooltool's internal RNG isn't fully seedable from
   outside, so reproducibility lives at the artifact level: `game.json` is
   the canonical take (34 shots, ~151 s of ball action, 3 scratches). Sam
   wins on stripes with a real heartbreak ending: Ray pots the 8 — and
   scratches the cue ball into the same pocket. The film always renders
   from this file.
3. **The film** — [`render_game.py`](render_game.py) rebuilds the table in
   Blender to pooltool's *exact* playfield geometry (cushion noses on the
   physics lines, pocket mouths at the physics pockets, 0.9906 × 1.9812 m
   seven-foot bar box), then: textured worsted felt (procedural cloth bump +
   sheen + wear), walnut wood grain (CC0 PBR), chrome pocket irons, a full
   regulation ball set (1–15, painted numbers and stripe bands that roll
   with the ball), two cues that stroke each shot and park on a wall rack,
   and a seedy dive-bar room: brick walls, tin ceiling, neon POOL and EXIT
   signs, back-bar bottle shelf, stools, drink rail with beers, dartboard,
   string bulbs, haze and dust motes — all melting into depth of field.
   The camera program: a chalk scoreboard intro, the break from directly
   overhead, a **bullet-time orbit** of the exploding rack (the break
   re-simulated at 1 kHz and retimed to 2 % speed), pocket-cam cuts as
   balls drop (a chalkboard tally X-es off each one), per-shot coverage on
   handheld-noise cameras, and a hold on the final heartbreak — Ray's 8
   drops and the pocket cam stays for the cue ball following it in. AgX
   "Punchy" grade, motion blur, silent by design.

## Run it

```bash
python3.12 -m venv .venv && .venv/bin/pip install pooltool-billiards
.venv/bin/python simulate_game.py            # roll a new game (optional)
blender -b -P render_game.py -- --test 30    # look-dev stills
blender -b -P render_game.py -- --render     # full film to frames/
ffmpeg -framerate 30 -i frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -movflags +faststart out/pool-game.mp4
```

## Honest limitations

- Players are present as agents and their cues, not human figures.
- Rules are bar-league flavored: no call-shot, simplified fouls (scratch →
  ball-in-hand anywhere).
- Cushion/pocket visual geometry matches the physics lines but is stylized:
  chrome irons + drop cups rather than sewn leather pouches, and no boolean
  pocket cuts through the rails.
- The room haze is faked with gradient-emission cones — EEVEE's real
  volumetrics render blocky froxel artifacts on dark walls at this scale.
- No sound, by design — this is a visual test.

## Credits & licenses

- Physics: [pooltool](https://github.com/ekiefl/pooltool) (MIT-style, see repo).
- Textures: [ambientCG](https://ambientcg.com) Wood049 / Metal012 (CC0).
- Everything else: original code in this repo (MIT).
