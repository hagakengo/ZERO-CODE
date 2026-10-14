# C/FILM same-pose identity guide — DRAFT / HOLD

2026-10-14 JST. This isolated face-visible test is within the current user approval. No canon or MASTER promotion.

## Reference provenance

`C_FILM_same_pose_reference_DRAFT.png` is an unchanged byte copy of previous `laneA/source_crop.png`, itself crop `(1024,49)-(1536,332)` of the C panel of `A_B_C_comparison_DRAFT.png`. It is 512×283. The source is an existing tilted three-quarter view, not an approved neutral frontal drawing. Hair top was already cut off by that panel. The original user planning sheet and this C candidate are different images; do not claim an original-source pixel match.

## Features to preserve

- Screen-left fringe is dense and strongly occludes the eye. Long central strands cross between the eyes toward the nose. Do not expose both eyes symmetrically or mirror the hair.
- Screen-left eye `(204,110)-(234,99)`, screen-right eye `(263,83)-(298,70)`. Eye openings remain slender with a half-lidded expression. Manual landmark uncertainty is ±3 px.
- Pupil centers `(221,106)` and `(282,77)` give the existing tilted eye axis. Preserve fixed corners during gaze and blink. Pupils may translate at most 2 source pixels in this small acting test; never cross lid or fringe boundaries.
- Nose tip `(249,117)`, chin `(276,176)`, right ear `(333,93)` remain fixed. Preserve narrow tapered jaw and original cheek/chin shadows. No head-angle correction is required.
- Mouth `(250,141)-(283,130)` has a slight rising line. A small notice does not require an open mouth, cheek widening, or a different jaw.
- Foreground hair must occlude animated eyes. Static hair is acceptable for the priority 1-second test. Moving an overlay while identical hair remains in the base creates duplicate locks and is not a finished hair rig.

## Editable eyelid candidates

`eyelid_contour_keys_DRAFT.json` supplies five separate cubic contour definitions per eye: neutral, quarter close, half close, fully closed and slight notice. Control coordinates are explicitly authored. `eyelid_key_sheet_DRAFT.svg` displays these vector contours with fixed orange corners. These are procedural vector correction candidates, not human hand-drawn original animation. Closed eyes contain no iris and use one dedicated contour; no vertically compressed eye raster is used.

The candidates intentionally keep the head/corners fixed. The closed line bends toward lower-lid support. During reopening, use the same supported shapes in reverse before the slight upper-lid lift. One-second timing must prioritize gaze → blink → notice without adding a smile beat.

## Existing defect and conservative cover bounds

Visual inspection of the old `clean_feature_base.png` shows flat rectangular skin bands and interrupted fringe around both eyes. Reusing it unchanged repeats a known defect. Narrow sloped cleanup candidates in source coordinates are left `[(202,104),(235,92),(238,104),(205,118)]`, right `[(261,77),(298,64),(302,77),(265,91)]`. These are conservative cover bounds, not skin-painted final art. They intersect hair; foreground fringe must be restored above the drawing layers. Original line remnants, flat skin boundaries, duplicated brows, loss of hair contour or overly light sclera are HOLD defects.

## Assessment

Same-pose source can preserve the fixed jaw, nose and asymmetric silhouette exactly. Native GP moving lids/irises advance editability. This does not prove a newly drawn full character model, natural acting, or finished film. Five lid contour pairs are provided; human hand-drawn inbetweens: 0. Image generation: 0. New raster edits in this asset lane: 0. Final technical/visual QA and user normal-speed playback approval remain separate gates.
