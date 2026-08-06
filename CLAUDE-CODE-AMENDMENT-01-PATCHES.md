# Amendment 01 — Pre-Kickoff Patches
## NYC Dive-Bar Pool Room Handoff

**Status:** Apply before Phase 0. These patches amend the original handoff dated 2026-08-04. Where this amendment and the original brief conflict, this amendment wins. Everything not addressed here remains in force.

---

## PATCH 1 — Relocate the Brittle Component-Breakdown Reference (HIGH)

The supplied Olhausen component breakdown currently lives at a volatile path:

```text
/Users/davidmarsh/.codex/attachments/4288f30b-497f-4352-b3d4-35b7e82aa844/pasted-text.txt
```

Required action during Phase 0, before any build stage:

1. Copy the full contents of that file verbatim into the canonical project at:

   ```text
   /Users/davidmarsh/Documents/Playground/projects/nyc-dive-bar-pool-room/docs/references/olhausen_component_breakdown.txt
   ```

2. Add it to `docs/SOURCE_MANIFEST.md` with its SHA-256, original path, and purpose.
3. Update every reference in the brief and in scripts to point at the project-internal copy.
4. Treat the `.codex/attachments` path as unavailable for the remainder of production. If the file cannot be read at Phase 0, stop and report — do not proceed from memory of its contents.

---

## PATCH 2 — Pocket Basket Depth Specification (MEDIUM)

The original brief specifies pocket mouths, cut angles, back draft, and facing thickness, but nothing below the pocket irons. Add the following locked values to Section 10 (Pocket geometry) and to `90_validate_scene.py`:

```text
Basket depth below slate bed plane:  100 to 120 mm; target 110 mm
Basket mouth taper:                  baskets narrow toward the base; no vertical
                                     parallel walls deeper than 60 mm
Ball clearance inside basket:        at least 6 balls of 57.15 mm diameter
                                     stackable without bridging or jamming
Leather wall thickness:              2.5 to 4 mm modeled thickness
Iron-to-basket attachment:           visible loop/strap fasteners, mechanically
                                     plausible, no floating leather
```

Validation additions to `reports/dimension_audit.json`:

- basket depth per pocket within the 100–120 mm range;
- no pocket-basket wall interpenetrating the slate, frame, or liner geometry;
- basket interior volume admits six tangent 57.15 mm spheres in a plausible stack.

These are `DESIGN_DECISION` values; record them in `docs/DESIGN_DECISIONS.md`.

---

## PATCH 3 — Cloth Specification Lock (MEDIUM)

Amend `MAT_Table_Cloth_DarkTournamentGreen` in Section 13 (Material Bible). Add:

```text
Product class:        worsted wool, Simonis 860 class
Weight:               approximately 21 oz per square yard (approx. 700 g/m2)
Nap direction:        directional nap running head end to foot end
                      (positive Y to negative Y in project coordinates);
                      sheen response must respect this direction at
                      grazing angles on both bed and rails
Weave scale:          micro-weave threads at true worsted pitch;
                      no thread larger than approximately 0.5 mm apparent width
```

The nap direction is not cosmetic: worsted cloth shows a directional sheen difference of a few percent in roughness/sheen between with-nap and against-nap views. Implement via anisotropy or a subtle directional roughness gradient keyed to the nap vector, and verify in the Phase 7 contact sheets from both the hero and reverse cameras.

---

## PATCH 4 — Ball Number Application Method (MEDIUM)

Ball numbers are the highest-risk readability element. Amend Section 11 (Balls):

1. Apply numbers and stripes as masked decal layers within the shared ball material node graph — not as curve objects, text objects, or floating geometry parented to spheres.
2. Number-circle specification:

   ```text
   Number circle diameter:   approximately 22 mm (real Aramith proportion)
   Number placement:         two per ball, on opposite hemispheres,
                             both upright when the ball rests in its
                             final racked orientation where composition allows
   Typography:               single licensed font from assets/fonts;
                             clean grotesque; underscore on 6 and 9
   ```

3. QA gate: `CAM_Rack_Detail_85mm` must resolve at least the 1, 8, and one stripe number crisply at 100% crop in the final 4K render. If numbers smear at delivery resolution, increase decal texture resolution rather than adding geometry.
4. Stripe band proportions: stripe width approximately half the ball diameter, centered on the equator, with clean white fields above and below at the correct Aramith-style ratio.

---

## PATCH 5 — Render Budget Gate (MEDIUM)

Cycles + volumes + glass at 512+ samples and 6144 x 3456 will not render quickly on any single machine. Add a hard checkpoint between Phase 7 and Phase 8:

1. During Phase 7, render `CAM_Table_ThreeQuarter_50mm` at final 4K settings (512 samples, denoising, final light rig, final materials). Record wall-clock time, sample count, device (Metal GPU or CPU), and memory peak in `docs/RENDER_SETTINGS.md`.
2. Gate Phase 8 on a total budget: estimated full delivery (4 x 4K + 1 x 6K) must be projected from the measured frame time. If the projection exceeds 24 machine-hours, apply exactly one of the following, in this order, and document the choice:
   - reduce final samples to 384 with adaptive sampling and verify no noise regression at 100% crop;
   - restrict the 6K hero to the table region via a render-border crop and upscale policy documented in RENDER_SETTINGS.md;
   - drop the optional 6K hero entirely (4K set is still required and non-negotiable).
3. Never compensate for render time by lowering hero-area quality, disabling denoising, or crushing blacks to hide noise.

---

## PATCH 6 — Font License Tracking (LOW)

Amend Phase 0 and `docs/SOURCE_MANIFEST.md`:

- Every file in `assets/fonts/` gets a manifest row: font name, foundry/author, license type, license file path or URL, and permitted-use confirmation for rendered still images.
- No font without a documented license may appear in any final render. If in doubt, substitute an OFL-licensed grotesque and record the substitution in `docs/DESIGN_DECISIONS.md`.

---

## PATCH 7 — Texel Density Metric (LOW)

Amend Section 13 (Material Bible) and `90_validate_scene.py`:

```text
Hero surfaces (table, balls, bar top):     at least 1024 px per meter of UV space
Mid-distance surfaces (walls, floor, bar): at least 512 px per meter
Background/props:                          at least 256 px per meter
```

`90_validate_scene.py` should flag any material whose effective texture resolution falls below its tier at its closest required camera. A qualitative "looks blurry" catch in Phase 8 is too late — this must be measurable earlier.

---

## PATCH 8 — Slate Section Documentation (LOW)

Three equal 33.33-inch slate sections are an acceptable design choice, but real 9-foot slates are typically unequal with a larger center piece. Action:

- Keep equal sections if preferred for script simplicity, but record the choice explicitly in `docs/DESIGN_DECISIONS.md` with one sentence of rationale.
- Alternatively, model unequal sections (approximately 30 / 40 / 30 inches along the long axis). Either is acceptable; silence on the choice is not.

---

## PATCH 9 — Version String Verification (LOW)

Before Phase 0 exits:

1. Run the verified executable with `--version` and record the exact output in `docs/SOURCE_MANIFEST.md` and the root README.
2. Confirm the resolved binary is `/Applications/Blender.app/Contents/MacOS/Blender` and no other Blender install (Steam, Homebrew, older app bundle) is reachable by the build scripts.
3. All scripts must target the recorded version's Python API exactly. Do not write version-agnostic fallback shims; pin and proceed.

---

## Acceptance Criteria for This Amendment

This amendment is fully applied when:

- the component breakdown exists at the project-internal path with a manifest entry;
- pocket baskets pass the new depth and capacity audit checks;
- the cloth material has the locked weight, nap direction, and weave scale values;
- ball numbers render crisply at 100% crop in the rack-detail camera;
- `docs/RENDER_SETTINGS.md` contains a measured 4K frame time and a documented Phase 8 budget decision;
- every font has a manifest license row;
- texel-density checks run in `90_validate_scene.py`;
- the slate section choice is documented;
- the Blender version string is recorded and matches the executed binary.

Proceed with the original production sequence unchanged after these patches are in place.
