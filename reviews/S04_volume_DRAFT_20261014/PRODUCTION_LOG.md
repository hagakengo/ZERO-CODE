# Production log — 2026-10-14 JST

- Version: S04_volume_DRAFT_20261014 / DRAFT, quality and direction HOLD.
- Input: user-approved 3D guide → 2D cleanup experiment; 4dc7ecd previous drawing test; director guidelines, Visual Bible, rules, joined S04 review.
- Tools: Python3/Pillow custom 3D mesh projection; ffmpeg/ffprobe; built-in image_gen (two calls, second rejected).
- Goal: constrain shared anatomy and contact before 2D generation; expose remaining discontinuity instead of claiming production completion.
- Changed: world-space support anchors, fixed stance shoe orientation, two-bone IK, separate pelvis/shoulder rotations, fixed box backpack with keyed lag and common strap attachments; generated raster cleanup referenced to all guide poses; fixed-scale support-foot registration.
- Result: 30-frame 3D/2D normal and half-speed movies; old/new and guide/new comparisons; saved meshes, coordinates, contact/exposure table, registration audit, reproducible source.
- Worked: guide support anchors zero drift, fixed model dimensions, readable shared pose source; technical video specifications and decode pass.
- Failed/limited: source art resolution below request; two-foot 2D registration incomplete (max ~101px approximate residual); no force or cloth simulation; torso translation lacks sequential transmission; natural motion and body-weight feel not visually judged in continuous playback.
- Correction: last-row uncrossing edit widened stance excessively and was rejected; preserved with exact prompt. Initial art and early registration movie preserved as iteration01.
- Status: technical PASS; drawing/animation quality HOLD; no final design, no MASTER, no integration, no publication.
- Next action: user normal-speed comparison; then correct a short landing interval with explicit two-foot and pelvis constraints before color/effects polish. Avoid further independent pose batches as a substitute for contact cleanup.
