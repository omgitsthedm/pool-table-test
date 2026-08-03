"""Simulate a complete 8-ball game between two moderate-skill players.

Physics: pooltool (https://github.com/ekiefl/pooltool) — event-based billiards
simulation with ball-ball, cushion, spin and friction models. This script owns
the *game*: alternating turns under pooltool's 8-ball ruleset, a human-ish
skill model (aim noise, speed judgement, occasional english), ball-in-hand
handling, and a JSON export of every shot's 60 Hz ball trajectories with
integrated roll orientations for the Blender renderer.

Run:  .venv/bin/python simulate_game.py [seed]
Out:  game.json
"""

from __future__ import annotations

import json
import math
import random
import sys

import numpy as np
import pooltool as pt
from pooltool.constants import pocketed as STATE_POCKETED

DT = 1 / 60
MAX_SHOTS = 70
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 26

# ---------------------------------------------------------------- players ----
# Moderate skill: a couple of degrees of aim wander on long shots, decent
# speed control, small unintentional english. Enough to run 2-3 balls on a
# good day and rattle a pocket on a bad one.
PLAYERS = [
    {"name": "Ray", "aim_sd_deg": 1.1, "speed_sd": 0.22, "english_sd": 0.045},
    {"name": "Sam", "aim_sd_deg": 1.35, "speed_sd": 0.28, "english_sd": 0.055},
]


def ball_group(ruleset, player_idx: int) -> str | None:
    """'solids' | 'stripes' | None (open table)."""
    groups = getattr(ruleset, "active_group", None)
    if groups is None:
        return None
    try:
        g = ruleset.active_group(player_idx)  # may be API-dependent
        return str(g)
    except Exception:
        return None


def legal_targets(system: pt.System, groups: dict, player: str) -> list[str]:
    """Ball ids the active player may legally pot, honoring assigned groups."""
    on_table = [
        bid
        for bid, b in system.balls.items()
        if bid != "cue" and b.state.s != STATE_POCKETED
    ]
    solids = [b for b in on_table if b != "8" and int(b) <= 7]
    stripes = [b for b in on_table if b != "8" and int(b) >= 9]
    mine = groups.get(player)
    if mine == "solids":
        return solids if solids else ["8"]
    if mine == "stripes":
        return stripes if stripes else ["8"]
    return (solids + stripes) if (solids or stripes) else ["8"]


def choose_shot(system: pt.System, targets: list[str], skill: dict, rng) -> dict:
    """Pick the easiest pot among targets, aim with human noise."""
    pockets = list(system.table.pockets.values())
    best = None
    for bid in targets:
        if system.balls[bid].state.s == STATE_POCKETED:
            continue
        for pocket in pockets:
            try:
                phi = pt.pot.calc_potting_angle(
                    system.balls["cue"], system.balls[bid], system.table, pocket
                )
            except Exception:
                continue
            cue_r = system.balls["cue"].state.rvw[0]
            obj_r = system.balls[bid].state.rvw[0]
            dist = float(np.linalg.norm(np.array(obj_r) - np.array(cue_r)))
            # crude difficulty: distance + cut severity proxy
            direct = math.degrees(
                math.atan2(obj_r[1] - cue_r[1], obj_r[0] - cue_r[0])
            )
            cut = abs((phi - direct + 180) % 360 - 180)
            score = dist + cut / 40.0
            if cut > 82:
                continue  # nearly impossible cut — skip
            if best is None or score < best["score"]:
                best = {
                    "ball": bid,
                    "pocket": pocket.id,
                    "phi": phi,
                    "dist": dist,
                    "cut": cut,
                    "score": score,
                }
    if best is None:
        # safety: roll gently at the nearest legal ball
        bid = min(
            targets,
            key=lambda b: float(
                np.linalg.norm(
                    np.array(system.balls[b].state.rvw[0])
                    - np.array(system.balls["cue"].state.rvw[0])
                )
            ),
        )
        phi = pt.aim.at_ball(system, bid)
        return {
            "ball": bid,
            "pocket": None,
            "phi": phi + rng.gauss(0, skill["aim_sd_deg"]),
            "V0": 1.4 + rng.gauss(0, 0.1),
            "a": 0.0,
            "b": 0.0,
            "kind": "safety",
        }

    # human wobble scales a little with distance
    wobble = skill["aim_sd_deg"] * (0.7 + best["dist"] / 2.0)
    v_base = 1.8 + best["dist"] * 1.15 + best["cut"] / 60.0
    return {
        "ball": best["ball"],
        "pocket": best["pocket"],
        "phi": best["phi"] + rng.gauss(0, wobble),
        "V0": max(1.0, v_base + rng.gauss(0, skill["speed_sd"])),
        "a": rng.gauss(0, skill["english_sd"]),
        "b": rng.gauss(0, skill["english_sd"]) - 0.05,
        "kind": "pot",
    }


def place_ball_in_hand(system: pt.System, targets: list[str], kitchen_only: bool):
    """Simple legal cue placement with clearance from every ball."""
    R = system.balls["cue"].params.R
    w, l = system.table.w, system.table.l
    others = [
        np.array(b.state.rvw[0][:2])
        for bid, b in system.balls.items()
        if bid != "cue" and b.state.s != STATE_POCKETED
    ]
    tgt = next((t for t in targets if system.balls[t].state.s != STATE_POCKETED), None)
    tpos = (
        np.array(system.balls[tgt].state.rvw[0][:2]) if tgt else np.array([w / 2, l / 2])
    )
    best, best_d = None, 1e9
    for _ in range(400):
        x = random.uniform(R * 3, w - R * 3)
        y_hi = l / 4 if kitchen_only else l - R * 3
        y = random.uniform(R * 3, y_hi)
        p = np.array([x, y])
        if others and min(np.linalg.norm(p - o) for o in others) < R * 2.4:
            continue
        d = float(np.linalg.norm(p - tpos))
        if d < best_d:
            best, best_d = p, d
    if best is None:
        best = np.array([w / 2, l / 8])
    system.balls["cue"].state.rvw[0][0] = best[0]
    system.balls["cue"].state.rvw[0][1] = best[1]
    system.balls["cue"].state.s = 0


def integrate_orientations(states, R):
    """Cumulative quaternion per sample from angular velocity (world frame)."""
    q = np.array([1.0, 0.0, 0.0, 0.0])
    out = []
    prev_t = states[0].t if states else 0.0
    for st in states:
        dt = st.t - prev_t
        prev_t = st.t
        w = np.array(st.rvw[2])
        wn = np.linalg.norm(w)
        if wn > 1e-9 and dt > 0:
            axis = w / wn
            ang = wn * dt
            dq = np.array(
                [
                    math.cos(ang / 2),
                    *(axis * math.sin(ang / 2)),
                ]
            )
            # quaternion multiply dq * q
            w1, x1, y1, z1 = dq
            w2, x2, y2, z2 = q
            q = np.array(
                [
                    w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                    w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                    w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                    w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
                ]
            )
            q = q / np.linalg.norm(q)
        out.append([round(float(v), 5) for v in q])
    return out


def export_shot(system: pt.System) -> dict:
    data = {"duration": round(float(system.t), 4), "balls": {}}
    for bid, b in system.balls.items():
        states = b.history_cts.states
        if not states:
            continue
        rs = [[round(float(v), 5) for v in st.rvw[0]] for st in states]
        ts = [round(float(st.t), 4) for st in states]
        data["balls"][bid] = {
            "t": ts,
            "r": rs,
            "q": integrate_orientations(states, b.params.R),
            "final_state": int(states[-1].s),
        }
    return data


def main():
    random.seed(SEED)
    np.random.seed(SEED)          # pooltool's rack jitter draws from numpy
    rng = random.Random(SEED * 7)

    table = pt.Table.default()
    balls = pt.get_rack(pt.GameType.EIGHTBALL, table, spacing_factor=1e-3)
    cue = pt.Cue(cue_ball_id="cue")
    system = pt.System(cue=cue, table=table, balls=balls)

    players = [pt.Player(p["name"]) for p in PLAYERS]
    ruleset = pt.get_ruleset(pt.GameType.EIGHTBALL)(players=players)

    shots = []
    winner = None
    ball_in_hand = False
    groups: dict = {}          # player name -> 'solids' | 'stripes'

    for shot_no in range(MAX_SHOTS):
        idx = players.index(ruleset.active_player) if ruleset.active_player in players else 0
        skill = PLAYERS[idx]
        is_break = shot_no == 0
        pname = PLAYERS[idx]["name"]

        targets = legal_targets(system, groups, pname)
        if is_break:
            # proper power break: cue ball on the head spot, dead center
            cb = system.balls["cue"]
            cb.state.rvw[0][0] = table.w / 2
            cb.state.rvw[0][1] = table.l * 0.25
            cb.state.s = 0
        elif ball_in_hand:
            place_ball_in_hand(system, targets, kitchen_only=False)
            targets = legal_targets(system, groups, pname)
        if is_break:
            plan = {
                "ball": "1",
                "pocket": None,
                "phi": pt.aim.at_ball(system, "1") + rng.gauss(0, 0.25),
                "V0": 8.2 + rng.gauss(0, 0.3),
                "a": 0.0,
                "b": -0.06,
                "kind": "break",
            }
        else:
            plan = choose_shot(system, targets, skill, rng)

        system.strike(
            V0=float(np.clip(plan["V0"], 0.8, 8.5)),
            phi=plan["phi"] % 360,
            a=float(np.clip(plan.get("a", 0), -0.35, 0.35)),
            b=float(np.clip(plan.get("b", 0), -0.4, 0.3)),
        )
        pt.simulate(system, inplace=True)
        pt.continuize(system, dt=DT, inplace=True)

        pocketed_now = [
            bid
            for bid, b in system.balls.items()
            if b.state.s == STATE_POCKETED and bid != "cue"
        ]
        cue_scratched = system.balls["cue"].state.s == STATE_POCKETED

        shot_record = export_shot(system)
        shot_record.update(
            {
                "player": PLAYERS[idx]["name"],
                "kind": plan["kind"],
                "target": plan["ball"],
                "called_pocket": plan.get("pocket"),
                "scratch": bool(cue_scratched),
            }
        )

        # let the ruleset judge legality, turns, and game over
        ruleset.process_and_advance(system)
        info = ruleset.shot_info
        shot_record["legal"] = bool(getattr(info, "legal", True))
        shot_record["turn_over"] = bool(getattr(info, "turn_over", True))
        game_over = bool(getattr(info, "game_over", False))
        shot_record["game_over"] = game_over
        shots.append(shot_record)

        # house rule for the demo: an 8 potted on the break is re-spotted at
        # the foot spot (APA scores it a win; that makes a one-shot film)
        if is_break and system.balls["8"].state.s == STATE_POCKETED:
            e = system.balls["8"]
            e.state.s = 0
            e.state.rvw[0][0] = table.w / 2
            e.state.rvw[0][1] = table.l * 0.75
            e.state.rvw[0][2] = e.params.R
            e.state.rvw[1][:] = 0
            e.state.rvw[2][:] = 0
            print("        8 on the break — re-spotted (house rule)")

        # groups decide on the first legal pot after the break
        if not groups and not is_break and pocketed_now and not cue_scratched:
            first = next((b for b in pocketed_now if b != "8"), None)
            if first is not None:
                mine = "solids" if int(first) <= 7 else "stripes"
                other = "stripes" if mine == "solids" else "solids"
                groups[pname] = mine
                groups[PLAYERS[1 - idx]["name"]] = other
                print(
                    f"        groups: {pname}={mine}, "
                    f"{PLAYERS[1 - idx]['name']}={other}"
                )
        shot_record["groups"] = dict(groups)

        eight_down = system.balls["8"].state.s == STATE_POCKETED
        print(
            f"shot {shot_no + 1:>2} · {shot_record['player']:<4} {plan['kind']:<6}"
            f" -> {plan['ball']:>3}  pocketed={pocketed_now}"
            f"{' SCRATCH' if cue_scratched else ''}"
            f"{' GAME OVER' if game_over or eight_down else ''}"
        )

        if game_over or eight_down:
            # group-aware verdict: potting the 8 wins only when your group is
            # cleared and the cue stayed up; otherwise it hands the game over
            # our house-rules verdict is authoritative (the library ruleset
            # assumes call-shot flow we don't use)
            on_the_eight = targets == ["8"]
            legal_win = eight_down and on_the_eight and not cue_scratched
            winner = pname if legal_win else PLAYERS[1 - idx]["name"]
            shot_record["verdict"] = "win" if winner == pname else "loss"
            break

        ball_in_hand = cue_scratched or not shot_record["legal"]
        if cue_scratched:
            # ruleset respots; make sure the cue exists on-table for placement
            system.balls["cue"].state.s = 0

        # fresh system for the next shot from the settled positions
        system = pt.System(
            cue=pt.Cue(cue_ball_id="cue"),
            table=table,
            balls={bid: b.copy() for bid, b in system.balls.items()},
        )
        for b in system.balls.values():
            b.history.states.clear()
            b.history_cts.states.clear()

    meta = {
        "seed": SEED,
        "dt": DT,
        "table": {"w": table.w, "l": table.l},
        "ball_R": system.balls["cue"].params.R,
        "players": [p["name"] for p in PLAYERS],
        "winner": winner,
        "n_shots": len(shots),
        "pockets": {
            pid: [round(float(v), 5) for v in p.center]
            for pid, p in table.pockets.items()
        },
    }
    with open("game.json", "w") as f:
        json.dump({"meta": meta, "shots": shots}, f)
    print(
        f"\nwinner: {winner} in {len(shots)} shots — game.json written "
        f"({sum(len(s['balls'].get('cue', {}).get('t', [])) for s in shots)} cue samples)"
    )


if __name__ == "__main__":
    main()
