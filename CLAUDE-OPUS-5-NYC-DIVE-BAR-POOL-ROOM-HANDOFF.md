# Claude Code Opus 5 Production Handoff

## Custom NYC Dive-Bar Pool Room and Premium 9-Foot Pool Table

**Status:** Ready for production  
**Prepared:** 2026-08-04  
**Target application:** Blender 5.2.0 LTS  
**Project slug:** `nyc-dive-bar-pool-room`  
**Final mode:** Static, cinematic environment. No gameplay, physics, animation, or interactive systems.


## 1. Execute This Brief End to End

Claude Code Opus 5: act as the production lead, environment artist, hard-surface modeler, material artist, lighting artist, and Blender technical director for this build.

Build a complete, premium-quality, photorealistic New York City dive-bar pool room from scratch. The scene must contain a fully modeled custom 9-foot slate pool table, a believable neighborhood bar, a complete architectural shell, premium physically based materials, intentional set dressing, proper billiard lighting, static racked balls, and final cinematic still renders.

This is not a game prototype and not a low-poly scene. The downloaded game-ready pool-table model is a benchmark and proportion reference only. The final table and environment must be rebuilt as clean, component-based, high-quality Blender geometry.

Proceed through modeling, materials, lighting, staging, render setup, validation, and packaging. Do not stop after research, blockout, or a first draft. Save checkpoint files and render reviews as you progress.

When this brief supplies a default, use it and continue. Do not pause to ask for aesthetic choices that are already resolved here.


## 2. Final Outcome

Create a fictional, independent New York neighborhood dive bar at approximately 1:15 a.m., shortly after closing on a rainy night. The front half contains the bar; the rear half opens into a dedicated pool room. The room should feel old, maintained enough to stay open, and genuinely used. It must not feel like a theme-park dive bar or a generic video-game tavern.

The hero object is a custom, unbranded, 9-foot, six-leg pool table inspired by the construction class and proportions of an Olhausen Remington with Cavalier rails. It should look like an expensive, restored heirloom placed inside a much rougher room:

- dark walnut hardwood with a deep, hand-rubbed finish;
- true 50 x 100 inch playing surface;
- three-piece 1-inch slate construction;
- dark tournament green worsted cloth;
- six turned floor-to-slate legs;
- leather shield drop pockets;
- blackened steel structural hardware;
- subtle mother-of-pearl rail sights;
- static, correctly sized phenolic balls arranged in a proper 8-ball rack.

The table should command the composition without making the environment feel like a furniture showroom.


## 3. Definition of Done

The project is complete only when all of the following exist and pass review:

- A self-contained Blender project under the canonical project path below.
- A fully modeled architectural shell and bar area, not a facade visible from only one camera.
- A component-based 9-foot pool table whose key dimensions pass an automated audit.
- Separate modeled slate, frame, legs, aprons, rails, cushions, sights, pocket facings, pocket irons, leather pockets, cloth, hardware, and levelers.
- Sixteen new, perfectly spherical 57.15 mm balls with readable generic numbers and correct solid/stripe colors.
- Fifteen object balls in a proper static 8-ball rack with the apex on the foot spot; the cue ball placed separately on the head side.
- Premium, physically plausible materials with scale-correct texture detail.
- A complete dive-bar material and prop pass with localized wear, grime, dust, water marks, and history.
- A lighting pass that makes the table playable and legible while retaining a dark late-night bar atmosphere.
- At least four final 4K still renders plus one optional 6K hero render.
- No physics, rigid bodies, simulations, game logic, ball animation, or gameplay code.
- No missing textures, absolute project-internal texture paths, broken links, floating props, interpenetration, obvious tiling, malformed text, or placeholder primitives visible in final renders.
- A source manifest, attribution file, dimension report, render settings note, and concise README.


## 4. Paths and Safety Boundaries

### Read-only reference library

Treat this entire directory as immutable source material:

```text
/Users/davidmarsh/Downloads/Pool Table Assets
```

Do not delete, rename, reorganize, convert in place, or overwrite anything in that directory. Do not run any downloaded platform client binary from the bundled Blendkit add-on tree.

### Canonical production project

Create the active project here, in accordance with the Playground workspace rules:

```text
/Users/davidmarsh/Documents/Playground/projects/nyc-dive-bar-pool-room
```

Before changing files:

1. Read `/Users/davidmarsh/Documents/Playground/AGENTS.md` and any nested instructions.
2. Confirm the canonical path with `pwd -P`.
3. If a Git repository is initialized, inspect status before editing and preserve unrelated work.
4. Keep the Downloads source library read-only.

### Verified Blender executable

```text
/Applications/Blender.app/Contents/MacOS/Blender
```

Verified version: Blender 5.2.0 LTS, Apple Silicon build dated 2026-07-14.

Use native Blender functionality wherever practical. The downloaded Blendkit source tree is a complete GPL add-on package, version `3.21.0-260628`; it is tooling, not project content. It is not required to complete this scene.


## 5. Source-of-Truth Hierarchy

When sources disagree, use this order:

1. Current World Pool-Billiard Association (WPA) equipment specifications for playfield, pockets, cushion nose, balls, lighting, and competition clearances.
2. Olhausen's own table-dimension sheet for the Remington/Cavalier exterior and heights.
3. The local Brunswick Metro installation manual for assembly relationships and hardware logic.
4. The local expired patent for hidden frame, load path, and cross-section logic.
5. The supplied Olhausen component breakdown for materials and product-family construction characteristics.
6. The downloaded 3D model for broad visual proportion, turned-leg language, pocket appearance, cues, and fixture silhouette.

Never promote a dimension inferred from the mesh or an unpublished wood-member size to an "official" specification. Mark such values as `DESIGN_DECISION` in the project documentation.

### Current official verification links

- [WPA rules](https://www.wpapool.com/wp-content/uploads/2026/01/2026.01.02-WPA-Rules.pdf)
- [WPA equipment specifications](https://www.wpapool.com/wp-content/uploads/2024/01/RECOMMENDED-EQUIPMENT-SPECIFICATIONS.pdf)
- [Olhausen outside dimensions](https://www.olhausenbilliards.com/wp-content/uploads/2021/03/Outside-Table-Dimensions_2019.pdf)
- [Olhausen catalog containing the Remington](https://waves-console-olhausen-billiards.s3.amazonaws.com/products/22006/Olhausen-Catalog_single_nb_lr.pdf)


## 6. Local Reference Inventory and Exact Use

### A. Engineering and assembly references

#### `Metro2005.pdf`

Absolute path:

```text
/Users/davidmarsh/Downloads/Pool Table Assets/Metro2005.pdf
```

This 15-page Brunswick Metro installation manual is the primary local assembly reference.

- Pages 3-4: baseframe, four cross-support sills, leg brackets, diagonal squaring, and levelers.
- Pages 5-6: center/end slate placement, equal overhang, countersunk fasteners, wedges, leveling, and filled joints.
- Pages 7-9: bed-cloth attachment and pocket-cut treatment.
- Pages 10-11: rail cloth, featherstrip, cushion nose, facings, folds, and staples.
- Pages 12-14: six-rail assembly, apron attachment, 18 rail studs through the slate, straightness check, and pocket installation.
- Page 15: ball-return system. Do not reproduce this subsystem because the target uses drop pockets.

Use this manual to make the table mechanically believable. Do not copy Brunswick branding or its exact exterior styling.

#### `US3263996.pdf`

Absolute path:

```text
/Users/davidmarsh/Downloads/Pool Table Assets/US3263996.pdf
```

This is the expired 1966 patent "Billiard and Pool Table Construction" by David H. Braun.

- PDF page 1 / Figure 1: plan and partial cutaway showing three slate slabs, rail, pockets, bed, supports, and frame.
- PDF page 2 / Figures 2-3: base frame and end elevation.
- PDF page 3 / Figure 4: full end cross-section through rail, slate, floor, bed, apron, central beam, and feet.
- PDF page 4 / Figures 5 and 8: frame joints and transverse cross-sections.
- PDF page 5 / Figures 6-7: side elevation and leg/support details.
- PDF pages 6-7: description of the plywood beam, intersecting supports, three-piece slate, bolted assembly, rail attachment, apron, and structural intent.

Use the patent for hidden frame and load-path logic. Translate it into a premium modern hardwood and plywood structure; do not reproduce the dated fiberglass exterior.

#### Supplied Olhausen component breakdown

Absolute path:

```text
/Users/davidmarsh/.codex/attachments/4288f30b-497f-4352-b3d4-35b7e82aa844/pasted-text.txt
```

Use this for the intended material stack and Remington product-family character:

- solid kiln-dried hardwood;
- flat paneled apron with routed detail;
- floor-to-slate leg load path;
- Uniliner-style slate support body;
- bolt-through cross-bracing;
- three-piece, 1-inch, diamond-honed slate;
- T-nut rail attachment;
- K-66 class cushion profile;
- leather shield drop pockets;
- worsted tournament cloth;
- steel brackets and fasteners.

Important corrections and qualifications:

- The pasted text's approximate 32-inch playing-surface height conflicts with Olhausen's official dimension sheet. Use 30 inches to the playing surface and 31.5 inches to the rail top.
- Use the WPA corner-pocket limit of 4.5 to 4.625 inches, not the broader 4.75-inch statement in the pasted text.
- Several internal wood-member dimensions are not published. Treat any chosen internal member size as an explicitly documented design decision.

### B. Downloaded 3D benchmark

The following files are different packages of the same underlying Sketchfab asset, "Pool Table Traditional" by fizyman.

#### Preferred visual benchmark

```text
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional-2.glb
```

- 79.3 MB GLB.
- 20 mesh objects, 17,026 vertices, 24,266 polygons.
- Same geometry as the smaller GLB and FBX.
- Highest embedded texture set: table/light/cues up to 4096 x 4096; balls 2048 x 2048.
- Easiest single-file visual benchmark.

#### Lightweight benchmark

```text
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional.glb
```

- 7.2 MB GLB.
- Identical geometry and object count.
- Embedded textures limited to 1024 x 1024.
- Use only for lightweight imports or diagnostics.

#### Editable-source package

```text
/Users/davidmarsh/Downloads/Pool Table Assets/pool-table-traditional/source/pool_table_scene.fbx
/Users/davidmarsh/Downloads/Pool Table Assets/pool-table-traditional/textures
```

- Same 24,266-polygon scene.
- External 4K textures and 2K ball texture.
- FBX import reports legacy material-link warnings in Blender 5.2.
- Use only if external textures or source object transforms need inspection.

#### Extracted glTF package

```text
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional/scene.gltf
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional/scene.bin
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional/textures
```

- Same model with external 4K/2K textures.
- Useful for inspecting source nodes, UVs, and texture assignments.

#### USDZ package

```text
/Users/davidmarsh/Downloads/Pool Table Assets/Pool_Table_Traditional.usdz
```

- Same geometry.
- Reduced 1024/512 texture set.
- Blender 5.2 emits material-binding warnings on import.
- Keep only as an interchange check; do not use as production source.

#### License and required attribution

```text
/Users/davidmarsh/Downloads/Pool Table Assets/pool_table_traditional/license.txt
```

The benchmark is CC-BY-4.0 and permits commercial use with attribution. If any source mesh, texture, UV, or recognizable derivative survives into the final project, include this credit in `docs/ATTRIBUTION.md` and in any public release:

> This work is based on "Pool Table Traditional" by fizyman, licensed under CC-BY-4.0. Source: https://sketchfab.com/3d-models/pool-table-traditional-e0b938c0c2e74eb794a49ebde2543977

Preserve the attribution even if the model is ultimately used only as an internal benchmark; this keeps provenance clear.

### C. Files that are not design references

The Python modules, platform executables, thumbnails, icons, manifest, `client/`, `blendfiles/`, `bl_ui_widgets/`, and other add-on folders at the root of the Downloads directory comprise the Blendkit add-on package. Do not inspect them as scene design assets, copy them into the project, or execute the bundled clients.


## 7. Benchmark Model Audit

The downloaded mesh is useful but not suitable as the final table.

### Measured inside Blender 5.2

Main table mesh:

```text
1.406698 m wide x 2.491151 m long x 0.815253 m high
55.38 in wide x 98.08 in long x 32.10 in high
14,084 vertices / 19,954 polygons after GLB import
one monolithic table mesh
one atlas-based table material
```

Interpretation:

- It is approximately an 8-foot traditional table, not the target 9-foot table.
- It is close to an 8-foot Cavalier exterior but is not exact.
- The six-leg silhouette, turned profiles, fringe/drop pockets, and general rail/apron relationship are useful style references.
- The table, rails, pockets, legs, cloth, and internal structure are not separated into production components.
- The geometry does not expose a buildable slate, frame, cushion, or rail system.

Other benchmark objects:

- Three-shade light: approximately 0.404 x 1.212 x 0.865 m including suspension; only 700 polygons.
- Two cues: approximately 1.477 m long, close to a standard 58-inch cue.
- Sixteen balls are present, but several use non-uniform transforms and measure as large as roughly 75 mm in one axis. They are not reliable precision spheres.

Production instruction:

- Put the imported high-resolution GLB in a hidden, locked `99_REFERENCE` collection.
- Never scale it and call it the final table.
- Rebuild all hero geometry parametrically and component by component.
- Replace every ball, cue, light, material, and table component intended for final camera use.


## 8. Creative Direction

### Narrative

The bar has occupied the ground floor of a prewar New York tenement for decades. It is fictional and should not duplicate a real venue. The scene is set after closing on a rainy night. Someone has freshly racked the balls but has not started the next game. A half-finished drink, chalk dust, damp coats, crooked stools, and a glowing back bar imply people without requiring character models.

The visual thesis is contrast:

- **Hero table:** valuable, restored, tactile, dark walnut, carefully lit.
- **Room:** scarred, patched, stained, crowded, warm, and credible.
- **Outside:** cool, wet, blue-green street spill through dirty glass.

### Authentic NYC cues

Use these architectural and environmental signals with restraint:

- long, narrow storefront footprint with the bar toward the front and pool room at the rear;
- pressed-tin ceiling with repeated panels, patched paint, and exposed conduit;
- old plaster over masonry with one selectively exposed brick section;
- dark, worn hardwood plank floor with an authentic traffic path;
- painted steam radiator and pipes;
- narrow front windows with rain streaks and reversed fictional lettering;
- aged back-bar mirror with perimeter desilvering;
- old wood bar face, stainless service inserts, brass foot rail, and mismatched stools;
- layered fictional flyers, local-band posters, league notices, stickers, tape residue, and handwritten specials;
- wall cue rack, bridge cue, chalk shelf, score beads, triangle rack, table brush, clock, and small television switched off or showing an abstract low-brightness screen;
- jukebox or compact music corner, old speaker boxes, exit sign, fire extinguisher, and service door;
- condensation rings, bottle drips, scuffed chair rails, worn door push plates, and grime localized to plausible contact zones.

### Anti-goals

Do not produce:

- a pristine luxury lounge;
- a generic Irish-pub kit;
- a saloon, speakeasy, casino, sports-bar franchise, or cyberpunk nightclub;
- Times Square neon overload;
- graffiti on every surface;
- uniform dirt/noise applied to everything;
- opaque black materials with no readable response;
- excessive volumetric fog;
- visible copyrighted beer, liquor, sports-team, or music logos;
- AI-generated gibberish text on signs or posters;
- people, gameplay UI, active smoking, rats, or caricatured filth.


## 9. Architectural Plan

Use metric units with `1 Blender unit = 1 meter`. Apply transforms on authored geometry. Model at real scale.

### Room shell

Use this default clear interior footprint:

```text
Width:  6.55 m / 21 ft 6 in
Length: 11.58 m / 38 ft 0 in
Ceiling: 3.15 m / 10 ft 4 in
```

The footprint may contain shallow wall offsets, columns, a rear service niche, and a short restroom corridor, but preserve the pool-table clearance envelope.

### Coordinate convention

- Global Z = up.
- Room long axis = Y.
- Front/street end = negative Y.
- Rear pool room = positive Y.
- Place the table center approximately at `(0.25, 2.15, 0)`.
- Table long axis runs along Y.
- Foot end points toward negative Y, facing the bar.
- Head end points toward positive Y.

### Pool clearance

The 9-foot playing surface plus 58-inch cues requires a minimum nominal cue envelope of approximately:

```text
4.216 m wide x 5.486 m long
13 ft 10 in wide x 18 ft 0 in long
```

Use the stronger WPA obstacle clearance target where the room allows it: 1.83 m / 6 feet from the outside rail to walls, furniture, or other hard obstacles. The bar may occupy the front half of the room but must not intrude into the rear table's functional cue envelope.

### Bar placement

- Place the main bar along the west/front portion of the room.
- Length: approximately 4.2 m / 13 ft 9 in.
- Guest-side depth: approximately 0.75 m / 29.5 in.
- Finished height: 1.067 m / 42 in.
- Keep the bar and stools forward of the pool clearance zone.
- Include four to five mismatched stools, but avoid a perfect evenly spaced lineup.
- Include a lower service counter, sink, speed rail, taps, bottle storage, glass racks, and credible bartender work space.
- Back bar should include shelves, a desilvered mirror, practical lamps, a small refrigerator, generic bottles, and restrained clutter.

### Architecture completeness

Build the whole camera-visible volume and plausible off-camera returns. Include wall thickness, door/window reveals, baseboards, ceiling transitions, conduit attachment, and floor-to-wall contact. Do not rely on infinitely thin planes for primary architecture.


## 10. Hero Pool Table: Locked Dimensions

The target is a custom, unbranded, 9-foot, six-leg, Remington-class table with Cavalier-width rails. It is not a branded replica.

### Primary dimensions

```text
Playing surface:                1.2700 x 2.5400 m   / 50 x 100 in
Outside Cavalier dimensions:   1.5494 x 2.8194 m   / 61 x 111 in
Floor to playing surface:      0.7620 m            / 30 in
Floor to top of rail:          0.8001 m            / 31.5 in
Nominal rail plan width:       0.1397 m            / 5.5 in
Slate thickness:               0.0254 m minimum    / 1 in
Under-slate wood liner:        0.01905 m minimum   / 0.75 in
Ball diameter:                 0.05715 m            / 2.25 in
Ball radius:                   0.028575 m
```

The playing surface dimensions are measured between opposing cushion noses. The exterior dimensions are measured to the farthest rail/cabinet edges.

### Slate and flatness representation

Model three equal slate sections with seams crossing the short axis. Give the slate actual thickness and separate wooden liners. Include countersunk attachment positions and hidden shims/wedges in an engineering-detail collection.

Use the WPA tolerances as validation metadata even though the static Blender mesh is mathematically flat:

- lengthwise flatness within 0.508 mm;
- widthwise flatness within 0.254 mm;
- joints coplanar within 0.127 mm;
- center deflection no more than 0.762 mm under the defined load, documented but not simulated.

### Rails, sights, and cushions

```text
Rail and cushion total width:  WPA range 101.6 to 190.5 mm
Chosen target:                 139.7 mm / 5.5 in
Sight spacing, 9-foot table:   317.5 mm / 12.5 in
Sight-center offset from nose: 93.6625 mm / 3 11/16 in
Sight count:                   18, or 17 plus one original flush nameplate
Cushion nose height:           35.719 to 36.862 mm above bed
Preferred cushion nose height: approximately 36.29 mm / 63.5% of ball diameter
```

Model six independent hardwood rail bodies and six independent cushion pieces. Include featherstrip grooves, featherstrips, K-66-class triangular cushion sections, rail-bolt inserts, pocket facings, and cloth wrapping. Do not represent the cushion as a painted strip on the table mesh.

Use 18 rail studs/bolts through the slate/frame relationship, following the Metro manual's logic. Keep hardware mechanically plausible and avoid impossible inaccessible fasteners.

### Pocket geometry

Use values near the center of the permitted ranges while preserving the exact range in project metadata:

```text
Corner mouth permitted: 114.30 to 117.475 mm / 4.5 to 4.625 in
Corner mouth target:    115.89 mm / 4.5625 in
Side mouth permitted:   127.00 to 130.175 mm / 5 to 5.125 in
Side mouth target:      128.59 mm / 5.0625 in
Corner cut angle:       142 degrees +/- 1 degree
Side cut angle:         104 degrees +/- 1 degree
Vertical back draft:    12 to 15 degrees; target 13.5 degrees
Corner shelf:           25.4 to 57.15 mm / 1 to 2.25 in
Side shelf:             0 to 9.525 mm / 0 to 0.375 in
Pocket-facing thickness: 1.588 to 6.35 mm; target about 3.175 mm
```

Model the pocket mouths, slate cuts, cushion jaws, facings, steel pocket irons, and leather baskets as separate geometry. Each drop pocket should plausibly hold at least six balls. No ball-return system.

### Cabinet, frame, and six-leg load path

Use a premium original structure that combines the local references:

- six turned solid-walnut legs: four corners plus two long-side center supports;
- floor-to-slate vertical load path;
- adjustable blackened-steel levelers and anchor plates;
- rectangular perimeter sill frame;
- four transverse support sills, with explicit support under both slate seams;
- reinforced longitudinal members and a central bolt-through beam/crossbrace system;
- broad Uniliner-style slate-support ledge;
- slate liners around the perimeter and seams;
- flat-panel aprons with restrained routed detail;
- knock-down apron brackets and removable rail assembly;
- hidden bolts, washers, T-nuts, and steel plates where physically appropriate.

Member sizes not published by the sources must be selected for a credible 9-foot, approximately 900-1,000 lb table and documented in `docs/DESIGN_DECISIONS.md`. Do not claim they are original Olhausen measurements.

Make the full internal structure visible in a disabled `TABLE_ENGINEERING` collection or view layer so future exploded renders remain possible. Final beauty renders should show the assembled table.

### Original styling

- Use six turned legs inspired by, but more refined than, the benchmark mesh.
- Use flat apron panels with subtle routed molding.
- Avoid an Olhausen logo/nameplate and exact proprietary ornament.
- Create an original small flush brass or blackened-steel plaque with fictional, readable lettering only if it materially improves the close-up.
- Use shield-style leather drop pockets rather than fringe-heavy tassels.
- Keep carvings restrained; the premium impression should come from proportion, joinery, finish, and material response.


## 11. Balls, Rack, Cues, and Table Accessories

### Balls

Create all balls from a new shared high-resolution sphere mesh. Do not reuse the distorted benchmark balls.

- Diameter: exactly 57.15 mm.
- Every instance must have uniform scale `(1, 1, 1)` after application.
- Use one cue ball and object balls 1 through 15.
- Solids: 1 yellow, 2 blue, 3 red, 4 purple, 5 orange, 6 green, 7 maroon, 8 black.
- Stripes: 9 through 15 use matching band colors.
- Each number appears twice on opposite sides with clean, readable, original generic typography.
- Underscore 6 and 9.
- Phenolic-resin material: near-white base, index of refraction (IOR) approximately 1.5, low roughness, subtle clearcoat, fine micro-scratches, no mirror-plastic look.

### Static 8-ball rack

- Long table axis = Y.
- Foot rail = negative Y.
- Foot spot is at local table coordinate `(0, -0.635, bed_z)` relative to the playing-surface center.
- Put the apex ball center directly over the foot spot.
- Build five tangent rows using exact 57.15 mm ball diameter.
- Row-to-row center spacing is `sqrt(3) / 2 * diameter`, approximately 49.493 mm.
- Put the 8 ball at the center of the triangle.
- Put one solid and one stripe in the two rear corners.
- Do not put the 8 ball at the apex.
- Place the wooden triangle rack around the balls with realistic 1-2 mm visual clearance and a smooth cloth-contact edge.
- Keep all balls static. Do not add rigid bodies, collision, drivers, or constraints.

Place the cue ball separately near the head string, with deliberate but natural composition. Add two premium 58-inch cues, one bridge cue, chalk cubes, a rail brush, and a wall rack. Cues may use the benchmark only for length/proportion reference; rebuild hero-visible cues with separate tip, ferrule, shaft, wrap, butt, and bumper.


## 12. Environment Asset List

Model or assemble the following. Hero and medium-distance assets must hold up in 4K renders.

### Architecture

- floor, walls, ceiling, shallow columns, door/window openings;
- pressed-tin ceiling panels with edge trim and selective damage;
- exposed conduit, junction boxes, radiator, steam pipes, sprinkler pipe, and vents;
- front door, dirty storefront glazing, transom, rain-streaked exterior glass;
- rear/service door and short restroom/service corridor;
- baseboards, chair rail or low wall paneling, patched plaster, selective brick reveal;
- one fire exit sign and one fire extinguisher in plausible locations.

### Bar

- guest bar top, worn wood face, service counter, sink, drip trays, speed rail, taps, foot rail;
- four or five mismatched stools with localized wear;
- back-bar shelving and desilvered mirror;
- generic liquor bottles with varied glass thickness, fill levels, labels, and cap types;
- generic beer bottles/cans, clean and used glasses, bar mats, coasters, napkins, straws;
- small refrigerator/cooler, cash-register silhouette, tip jar, check presenter, towels;
- warm practical lamps and a low-brightness fictional neon sign.

### Pool room

- hero table and all accessories;
- three-shade green enamel billiard light, rebuilt at high quality;
- wall cue rack, score beads, chalk ledge, clock, table brush, spare rack;
- two small mismatched spectator tables and chairs outside cue clearance;
- one wall-mounted television or speaker pair, visually subordinate;
- framed generic league sheet and fictional tournament flyer.

### Story and clutter

- half-finished rocks glass or beer glass;
- water rings, a folded receipt, coins, matchbook, bent coaster;
- one damp umbrella near the entry and subtle wet footprints, not puddles everywhere;
- crooked posters, layered tape, removed-sticker ghosts, pinholes;
- cleaning bucket/mop partially visible in service area, not hero foreground;
- dust in inaccessible corners, chalk dust near the table, hand grease on rail touch zones.

Use linked instances for repeated bottles, glasses, ceiling tiles, and small props. Create enough controlled variation that repetition is not obvious.


## 13. Material Bible

All material detail must be physically scaled. Large visual changes should come from geometry and meaningful masks, not generic procedural noise applied uniformly.

### Table walnut

`MAT_Table_Walnut_Clearcoat`

- deep natural walnut, not near-black diffuse;
- correct grain direction per rail, apron, leg, and frame member;
- visible end grain where construction exposes it;
- layered pore normal at real wood-pore scale;
- satin/semigloss clear finish with roughness variation approximately 0.22-0.38;
- subtle edge polish where hands contact rails;
- restrained hairline scratches visible only at grazing angles;
- no heavy chipped paint because this is restored hardwood.

### Cloth

`MAT_Table_Cloth_DarkTournamentGreen`

- deep traditional bottle/tournament green;
- nap-free worsted appearance;
- roughness approximately 0.6-0.75;
- subtle sheen and grazing-angle fiber response;
- micro weave at correct scale, never a fuzzy carpet displacement;
- light chalk accumulation near the head string, foot spot, and rails;
- no giant repeating weave or obvious texture seams.

### Leather pockets

`MAT_Pocket_Leather_Oxblood`

- dark oxblood/brown vegetable-tanned leather;
- modeled thickness, stitched seams, folded edges, and basket depth;
- slight polished wear around pocket lips;
- dry creasing and small tonal variation, not cracked ruin.

### Metal

- blackened steel for brackets, bolts, irons, and levelers;
- aged brass for bar foot rail and selected fixtures;
- mother-of-pearl or pale inlay for rail sights;
- chrome/stainless only where functionally appropriate at the bar;
- use edge highlights, micro-scratches, fingerprints, and oxidation selectively.

### Slate

- honed dark gray stone with a cut edge and subtle layering;
- mostly hidden in final assembly;
- avoid marble veining or glossy countertop behavior.

### Floor

`MAT_Env_Floor_WornOak`

- individual plank variation and real seams;
- worn finish in traffic lanes, darker accumulation at edges;
- occasional repaired plank and small gouges;
- cool wet highlights near entry only;
- no blanket grunge mask.

### Walls and ceiling

- warm dirty off-white or tobacco-cream plaster with patch repairs;
- deep oxblood/green lower wall or panel sections where composition benefits;
- painted tin ceiling with layered repainting, edge oxidation, and small water staining;
- exposed brick should be irregular, dusty, and mortar-rich, not a perfectly tiled red brick texture.

### Mirror and glass

- physically thick glass where silhouette reveals it;
- back-bar mirror with perimeter desilvering and cleaned central zones;
- storefront glass with rain streaks, fingerprints at handles, dust at frame edges;
- bottle glass with correct IOR, liquid meniscus, and wall thickness.

### Grime logic

Wear must answer one of these questions:

- Where do hands touch?
- Where do shoes travel?
- Where does liquid collect?
- Where does dust settle because cleaning cannot reach?
- Where does sunlight, moisture, or heat age the material?

If a mark has no physical story, remove it.


## 14. Lighting and Atmosphere

### Lighting goal

The pool table is the best-lit surface in the room, but the space must retain a dark, warm, after-hours mood. The table light should reveal accurate cloth color, ball numbers, pocket geometry, wood grain, and rail highlights without clipping.

### Billiard fixture

Rebuild the benchmark's three-shade light as a premium fixture:

- approximately 1.2-1.35 m long;
- three deep green enamel shades with warm white interiors;
- modeled bulb sockets, bulbs, vents, fasteners, chain/rod suspension, ceiling canopy, and wiring;
- center exactly above the playing surface;
- fixture parallel to the table long axis;
- treat it as non-movable and keep its lowest part at least 1.65 m / 65 inches above the bed, following the WPA non-movable-light recommendation;
- tune light spread so bed and rails receive visually even illumination, with no hot center and dead corners.

Use the WPA target as the design benchmark:

- at least 520 lux across bed and rails;
- at least 50 lux in the broader venue;
- no direct glare approaching the player's eye line.

Blender light wattage is not a direct lux meter. Use physically plausible fixture placement, evenness checks, false-color/histogram inspection if available, and restrained exposure. Record the final light energies and exposure in `docs/RENDER_SETTINGS.md`.

### Supporting lights

- Pool fixture: neutral-warm 2900-3200 K, high color rendering.
- Bar pendants/practicals: 2200-2600 K.
- Small fictional red neon practical: saturated but not clipping.
- Street/window spill: rainy blue-green 6000-7500 K.
- Subtle cooler service-light contamination near the rear door if composition needs separation.
- Do not add invisible cinematic rim lights unless they are motivated by an actual fixture or opening.

### Atmosphere

- Use a subtle localized volume so the brightest pool-light beam can reveal a hint of dust.
- Keep volumetric density low enough that blacks remain clean and the room does not look smoky.
- Use damp-night reflections and window rain to imply weather.
- No active cigarette smoke.

### Render engine and color

- Final engine: Cycles.
- Use the Metal graphics processing unit (GPU) backend if stable; provide a central processing unit (CPU) fallback.
- Color management: AgX with Medium High Contrast or a carefully justified adjacent look.
- Preview samples: 64-128 with denoising.
- Final samples: 512 minimum; increase for unresolved glass, volume, or caustic noise.
- Use adaptive sampling and OpenImageDenoise without wiping out wood pores or cloth texture.
- Clamp indirect only if necessary to control isolated fireflies; do not flatten highlights.


## 15. Cameras and Final Images

Use physically plausible camera heights and focal lengths. Avoid ultra-wide distortion that makes the table dimensions unreadable.

### Required cameras

#### `CAM_Hero_Entry_28mm`

- View from front/entry toward the rear pool room.
- Pool table is dominant; bar remains readable along one side.
- Show the warm/cool lighting contrast and NYC storefront depth.
- 28-32 mm full-frame equivalent.
- Final: 3840 x 2160 and optional 6144 x 3456.

#### `CAM_Table_ThreeQuarter_50mm`

- Low-to-medium three-quarter table view.
- Show walnut grain, turned legs, shield pockets, racked balls, and light reflections.
- Keep verticals controlled.
- 45-60 mm equivalent.

#### `CAM_Rack_Detail_85mm`

- Focus on the racked balls, cloth weave, foot spot, rail sights, pocket leather, and wood finish.
- Use modest depth of field; keep enough of the rack readable.
- 70-100 mm equivalent.

#### `CAM_Bar_Reverse_35mm`

- Reverse view from pool-room side toward the bar and rainy storefront.
- Table edge may frame the foreground.
- 32-40 mm equivalent.

### Optional camera

`CAM_Engineering_Exploded` may show internal construction on a neutral background, but it must not replace any required beauty render.

### Output

- Save 16-bit half-float OpenEXR masters where practical.
- Save display-ready 4K PNG versions.
- Keep raw and graded outputs separate.
- Do not use destructive over-sharpening, crushed blacks, excessive bloom, fake chromatic aberration, or heavy vignette.


## 16. Blender Project Architecture

Recommended directory structure:

```text
nyc-dive-bar-pool-room/
  README.md
  AGENTS.md                     # only if project-specific guidance is needed
  blend/
    poolroom_master.blend
    checkpoints/
      01_blockout.blend
      02_table_geometry.blend
      03_architecture.blend
      04_materials.blend
      05_lighting.blend
      06_final.blend
  scripts/
    00_bootstrap_scene.py
    10_build_architecture.py
    20_build_pool_table.py
    21_build_table_hardware.py
    22_build_balls_and_rack.py
    30_build_bar.py
    40_build_materials.py
    50_set_dress.py
    60_build_lighting.py
    70_build_cameras.py
    80_render_checkpoints.py
    90_validate_scene.py
    build_all.py
  assets/
    source/                     # copied working derivatives only, with provenance
    textures/
    decals/
    fonts/
  docs/
    SOURCE_MANIFEST.md
    ATTRIBUTION.md
    DESIGN_DECISIONS.md
    TABLE_SPEC.md
    RENDER_SETTINGS.md
    QA_REPORT.md
  reports/
    dimension_audit.json
    scene_audit.json
    asset_manifest.json
  renders/
    checkpoints/
    final_exr/
    final_png/
    contact_sheets/
```

### Collection structure

```text
00_GUIDES
01_ARCHITECTURE
02_TABLE_VISIBLE
03_TABLE_ENGINEERING
04_BAR
05_HERO_PROPS
06_SET_DRESSING
07_LIGHTS
08_CAMERAS
09_ATMOSPHERE
99_REFERENCE_LOCKED
```

### Naming

- `PT_` pool-table components.
- `ENV_` architectural components.
- `BAR_` bar components.
- `PROP_` props.
- `LGT_` lights and fixtures.
- `CAM_` cameras.
- `MAT_` materials.
- `REF_` imported references.

Examples:

```text
PT_Slate_Center
PT_Rail_Long_West
PT_Cushion_End_Foot
PT_PocketIron_Corner_SW
PT_Leg_Mid_East
PT_Ball_08
BAR_BackMirror
ENV_TinCeiling_Panel_A
LGT_Pool_Key_Center
```

### Modeling standards

- Metric units and real-world dimensions.
- Applied transforms on authored meshes.
- Sensible origins and local axes.
- Bevel real edges based on physical material and scale.
- Weighted normals or native smooth-by-angle only where appropriate.
- Non-destructive modifiers remain editable unless applying them improves stability and is documented.
- Separate components that are separate in real life.
- Use linked data for repeated instances.
- Use custom properties on `PT_TableRoot` for all locked dimensions.
- Keep reference objects disabled in final render view layers.
- Use relative paths inside the project.
- Never leave a production asset dependent on the Downloads folder at final handoff.


## 17. Procedural Build Requirements

The table and room should be reproducible through modular Blender Python scripts. Scripts are part of the deliverable, not disposable scaffolding.

### Required behavior

- `build_all.py` builds or updates the scene in a deterministic order.
- Scripts are idempotent: rerunning a stage replaces or updates its owned collection rather than duplicating everything.
- Locked table dimensions live in one constants/config section, not scattered magic numbers.
- Separate geometry construction from material assignment and scene staging.
- Use Blender's data API where possible; minimize context-sensitive operator dependence.
- Save after each major stage.
- On failure, exit nonzero and report the exact stage/object.
- Do not conceal errors with broad exception handlers.

### Dimension validation

`90_validate_scene.py` must measure the actual final geometry and write `reports/dimension_audit.json`.

At minimum verify:

- playing surface: 1.2700 x 2.5400 m;
- exterior table: 1.5494 x 2.8194 m;
- playing surface Z: 0.7620 m above finished floor;
- top rail Z: 0.8001 m above finished floor;
- slate thickness: at least 0.0254 m;
- all 16 balls: 0.05715 m diameter within 0.1 mm and uniform in X/Y/Z;
- cushion nose height: within the WPA range;
- corner and side mouth targets within allowed ranges;
- rack apex over the foot spot within 0.5 mm;
- no racked-ball center spacing less than the ball diameter minus 0.1 mm;
- pool light centered over the playfield;
- no hard obstacle intrudes into the designated cue-clearance volume;
- reference collection excluded from final render view layers.

Use tighter tolerances where feasible, but do not fake precision by rounding report output.

### Scene validation

Also report:

- missing external files;
- unapplied non-uniform scale on production meshes;
- duplicate object names;
- unassigned material slots;
- zero-area faces and obvious non-manifold defects on hero hard-surface objects;
- cameras missing from required list;
- lights not assigned to intended collections;
- physics/rigid-body objects, which must total zero;
- broken text/decal image paths;
- final render dimensions and engine.


## 18. Production Sequence and Checkpoints

### Phase 0: Preflight and source lock

- Read workspace instructions.
- Create canonical project structure.
- Generate SHA-256/source manifest for the local PDFs, relevant model packages, and license.
- Copy only working derivatives that are actually needed; never alter Downloads originals.
- Create `docs/ATTRIBUTION.md` immediately.

**Exit gate:** source manifest identifies each relevant file, license, purpose, and whether it may survive into final output.

### Phase 1: Scale blockout

- Set units, room shell, table bounding box, bar volume, windows, doors, and cue-clearance guide.
- Add temporary cameras and basic neutral lighting.
- Render four grayscale blockout views.

**Exit gate:** the table reads as the focal point; the bar does not obstruct cue clearance; architecture feels like a plausible narrow NYC storefront.

### Phase 2: Pool-table engineering model

- Build frame, six legs, slate, rails, cushions, pockets, hardware, aprons, and levelers.
- Use separate objects and exact locked dimensions.
- Add engineering collection and optional exploded offsets.
- Run dimension audit before materials.

**Exit gate:** table passes geometry dimensions; pocket and cushion relationships read correctly in cross-section; no benchmark mesh is visible.

### Phase 3: Balls and accessories

- Build new ball master and 16 instances.
- Create readable generic numbers and stripes.
- Rack object balls correctly and place cue ball.
- Build rack, cues, bridge, chalk, brush, and wall rack.

**Exit gate:** balls are exact spheres with uniform transforms; rack layout passes audit; no physics components exist.

### Phase 4: Architecture and bar refinement

- Finish wall thickness, ceiling, floor, bar, back bar, service details, windows, doors, radiator, pipes, conduit, and fixtures.
- Resolve every camera-visible transition.

**Exit gate:** clay renders have no empty voids, paper-thin hero surfaces, implausible intersections, or incomplete reverse angles.

### Phase 5: Premium materials

- Complete table materials first.
- Complete architecture and bar materials.
- Add localized wear and grime masks.
- Check texture scale using close and wide cameras.

**Exit gate:** wood, cloth, leather, balls, glass, metal, plaster, brick, floor, and mirror remain distinguishable under neutral test lighting.

### Phase 6: Set dressing

- Add bar equipment, bottles, glassware, stools, posters, notices, pool accessories, and narrative details.
- Preserve negative space and cue movement.
- Use original/generic art and readable fictional text.

**Exit gate:** the room feels inhabited and specific but not cluttered for its own sake; no repeated asset pattern is obvious.

### Phase 7: Lighting and look development

- Build and light the three-shade pool fixture.
- Add motivated bar practicals, neon, and street spill.
- Tune exposure, contrast, volume, and wet-night reflections.
- Produce lighting contact sheets at consistent exposure.

**Exit gate:** cloth and ball numbers read clearly; table illumination is even; no clipping, crushed wood, dead corners, or arbitrary rim lights.

### Phase 8: Final cameras and renders

- Finalize four required cameras.
- Render 4K previews, inspect, fix defects, and rerender.
- Render EXR masters and PNG deliveries.
- Create a final contact sheet.

**Exit gate:** every required camera passes visual QA at 100% crop in hero areas.

### Phase 9: Package and handoff

- Make paths relative.
- Confirm all assets resolve from the canonical project directory.
- Run final scene and dimension audits.
- Write README, render settings, design decisions, attribution, and QA report.
- Save clean final `.blend` with reference collections disabled.

**Exit gate:** a new Blender session can open and render the project without reading from Downloads, installing an add-on, or repairing paths.


## 19. Visual Quality Gate

Perform explicit final inspection for all of the following:

### Table

- Exact 9-foot proportions, not a scaled 8-foot mesh.
- Six credible load-bearing legs and levelers.
- Rail, cushion, slate, cloth, pocket, and apron layers read correctly.
- No paper-thin leather or impossible pocket baskets.
- Pocket mouths are symmetric and correctly angled.
- Sights are flush, evenly spaced, and not floating.
- Wood grain direction follows each component.
- Cloth weave is subtle and correctly scaled.
- Balls are round, tangent in rack, readable, and not intersecting.
- No gameplay or physics data.

### Environment

- Table clearance remains believable.
- Bar has a functional bartender side.
- Doors, windows, radiator, pipes, conduit, and fixtures attach to architecture.
- Floor wear follows traffic patterns.
- Grime accumulates logically.
- Props have weight and contact shadows.
- Bottles have varied but physically plausible glass/liquid.
- Posters and labels are original and readable where the camera can resolve them.
- No floating dust cards, fake puddles, excessive smoke, or universal grunge.

### Lighting and render

- Ball highlights are controlled and not clipped.
- Cloth color remains green rather than black or fluorescent.
- Pool-light falloff is even across rails and corners.
- Warm bar and cool street colors remain motivated.
- Window and mirror reflections are coherent.
- Glass, volume, and dark wood are noise-free at delivery resolution.
- Depth of field supports the composition without hiding unfinished geometry.
- No fireflies, broken alpha, texture seams, banding, or denoiser smearing.

### Technical

- Required object names and cameras exist.
- No missing images or absolute internal paths.
- No duplicate staging caused by rerun scripts.
- No hidden benchmark object leaks into renders.
- No rigid bodies or simulation caches.
- All reports pass or document an intentional exception.
- Source attribution is present.


## 20. Final Deliverables

Deliver all of the following under the canonical project directory:

1. `blend/poolroom_master.blend`
2. Modular scripts plus `scripts/build_all.py`
3. Stable checkpoint `.blend` files
4. Four required 4K final PNG renders
5. Matching EXR masters
6. Optional 6K hero render
7. Final render contact sheet
8. `docs/TABLE_SPEC.md`
9. `docs/DESIGN_DECISIONS.md`
10. `docs/SOURCE_MANIFEST.md`
11. `docs/ATTRIBUTION.md`
12. `docs/RENDER_SETTINGS.md`
13. `docs/QA_REPORT.md`
14. `reports/dimension_audit.json`
15. `reports/scene_audit.json`
16. `reports/asset_manifest.json`
17. Root `README.md` with exact open, rebuild, validation, and render instructions

The final closeout must state:

- what was built;
- what source material was incorporated versus used only as reference;
- the exact table dimensions achieved;
- which validation checks passed;
- final render paths;
- any remaining known limitations;
- the single recommended next step, if any.


## 21. Non-Negotiable Constraints

- No physics.
- No gameplay.
- No animation requirement.
- No rigid bodies.
- No game-engine export requirement.
- No scaling the downloaded model into a supposed 9-foot final.
- No destructive edits to the reference library.
- No executing bundled Blendkit client binaries.
- No unlicensed external assets.
- No copyrighted real-world logos unless separately authorized and licensed.
- No vague completion claim based only on a blockout or viewport screenshot.
- No stopping before final renders, audits, documentation, and packaged Blender files exist.

If a technical failure occurs, preserve the last valid checkpoint, record the exact error and attempted workaround, and continue through a safe alternative where possible.


## 22. Final Creative Standard

The intended result should feel like a still from a prestige New York crime drama or an architectural editorial about a beloved neighborhood bar - not a game level, asset-store demo, glossy hospitality render, or nostalgia caricature.

The room should be beautiful because it is observed carefully: real dimensions, honest materials, motivated light, accumulated history, and disciplined composition. The expensive table and the battered room should elevate each other.
