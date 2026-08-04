"""
simulate_break.py — one clean, hard 8-ball break, simulated for film.

Rolls candidate breaks with slightly varied cue speed, contact point and aim
(the wobble any real player has) and keeps the most cinematic one: a legal
break that scatters the whole rack and drops at least one ball, so the film
has a pot to cut to. Trajectories are exported at 120 Hz — enough headroom to
run the film at 24 fps and still slow the impact down hard without stepping.

Output: break.json  {meta, balls:{id:{r:[[x,y,z]...], w:[[wx,wy,wz]...]}},
                     potted:{ball:pocket}, pot_frames:{ball:sample_index}}
"""
import json
import math
import os
import sys

import numpy as np
import pooltool as pt
from pooltool.constants import pocketed as STATE_POCKETED

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.join(HERE, "break.json")
RATE = 120.0                      # samples per second exported
TRIES = int(os.environ.get("BREAK_TRIES", "36"))


def quat_from_omega(samples_w, dt):
    """integrate angular velocity into per-sample orientation quaternions"""
    q = np.array([1.0, 0.0, 0.0, 0.0])
    out = [q.copy()]
    for w in samples_w[1:]:
        n = float(np.linalg.norm(w))
        if n < 1e-9:
            out.append(q.copy())
            continue
        ax = w / n
        half = 0.5 * n * dt
        dq = np.array([math.cos(half), *(ax * math.sin(half))])
        w0, x0, y0, z0 = dq
        w1, x1, y1, z1 = q
        q = np.array([
            w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1,
            w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1,
            w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1,
            w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1,
        ])
        q /= np.linalg.norm(q)
        out.append(q.copy())
    return out


def roll_one(seed):
    rng = np.random.default_rng(seed)
    table = pt.Table.default()
    balls = pt.get_rack(pt.GameType.EIGHTBALL, table=table,
                        ball_params=pt.BallParams.default(), spacing_factor=1e-4)
    cue_ball = balls["cue"]
    # break from behind the head string, a touch off centre like a real player
    cue_ball.state.rvw[0][0] = table.w * (0.5 + float(rng.normal(0, 0.045)))
    cue_ball.state.rvw[0][1] = table.l * 0.235
    cue_ball.state.rvw[0][2] = cue_ball.params.R
    cue_ball.state.s = 0

    cue = pt.Cue(cue_ball_id="cue")
    system = pt.System(table=table, balls=balls, cue=cue)
    # a hard, flat break: near the ball's centre, a hair below to keep it down
    V0 = float(rng.uniform(7.6, 8.5))
    phi = 90.0 + float(rng.normal(0, 0.35))
    system.cue.set_state(V0=V0, phi=phi, a=float(rng.normal(0, 0.012)),
                         b=float(rng.uniform(-0.09, -0.03)), theta=0.0)
    pt.simulate(system, inplace=True)
    return system, V0, phi


def score(system):
    """prefer breaks that pot balls, spread the rack and keep the cue on cloth"""
    potted = {}
    for bid, b in system.balls.items():
        if b.state.s == STATE_POCKETED:
            potted[bid] = None
    scratch = "cue" in potted
    objects = [b for b in potted if b != "cue"]
    # spread: mean distance of every object ball from the rack apex
    apex = np.array([system.table.w / 2, system.table.l * 0.75])
    d = []
    for bid, b in system.balls.items():
        if bid == "cue" or b.state.s == STATE_POCKETED:
            continue
        d.append(float(np.linalg.norm(b.state.rvw[0][:2] - apex)))
    spread = float(np.mean(d)) if d else 0.0
    if scratch:
        return -1e9, potted
    if "8" in objects:
        return -1e9, potted            # 8 on the break: not the film we want
    return len(objects) * 1000 + spread * 100, potted


def main():
    best = None
    for seed in range(TRIES):
        system, V0, phi = roll_one(seed)
        s, potted = score(system)
        n = len([b for b in potted if b != "cue"])
        print("seed %2d  V0=%.2f  potted=%d  score=%.0f" % (seed, V0, n, s))
        if best is None or s > best[0]:
            best = (s, seed, system, V0, phi, potted)
    s, seed, system, V0, phi, potted = best
    print("\nCHOSEN seed=%d V0=%.2f potted=%s" % (seed, V0, list(potted)))

    dt = 1.0 / RATE
    cont = pt.continuize(system, dt=dt, inplace=False)
    out_balls = {}
    n_samples = 0
    for bid, b in cont.balls.items():
        hist = b.history_cts
        rs = [list(map(float, st.rvw[0])) for st in hist.states]
        ws = [np.array(st.rvw[2], dtype=float) for st in hist.states]
        quats = quat_from_omega(ws, dt)
        out_balls[bid] = {"r": rs, "q": [list(map(float, q)) for q in quats]}
        n_samples = max(n_samples, len(rs))

    # when did each potted ball actually reach its pocket?
    pot_frames, pot_pocket = {}, {}
    R = system.balls["cue"].params.R
    pockets = {k: (float(p.center[0]), float(p.center[1]))
               for k, p in system.table.pockets.items()}
    for bid in potted:
        rs = out_balls[bid]["r"]
        for i, r in enumerate(rs):
            hit = None
            for pk, (px, py) in pockets.items():
                if math.hypot(r[0] - px, r[1] - py) < 0.055:
                    hit = pk
                    break
            if hit:
                pot_frames[bid] = i
                pot_pocket[bid] = hit
                break

    meta = {
        "rate": RATE, "n_samples": n_samples, "seed": seed, "V0": V0,
        "phi": phi, "ball_R": R,
        "table": {"w": float(system.table.w), "l": float(system.table.l)},
        "pockets": {k: [v[0], v[1]] for k, v in pockets.items()},
    }
    json.dump({"meta": meta, "balls": out_balls,
               "potted": pot_pocket, "pot_frames": pot_frames},
              open(OUT, "w"))
    print("wrote %s  (%d samples = %.2fs of action, potted %s)"
          % (OUT, n_samples, n_samples / RATE, pot_pocket))


if __name__ == "__main__":
    main()
