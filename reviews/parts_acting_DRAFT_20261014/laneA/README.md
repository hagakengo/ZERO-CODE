# Lane A — editable parts acting, DRAFT / HOLD

2026-10-14 JST. This is an isolated face-visible experiment authorised by the user, not a canon or MASTER change. C/FILM remains a candidate.

## Review

- `normal_24fps.mp4`: 24 frames, 24fps, 1 second, 1024×640.
- `half_speed_24fps.mp4`: same 24 drawings exposed twice, 48 frames, 24fps, 2 seconds.
- `acting_key_sheet_DRAFT.png`, `parts_sheet_DRAFT.png`.
- `editable_composite.svg`, `svg_frames/`, `parts/`, `exposure.csv`.

Shared crop: comparison sheet C panel (1024,49,1536,332). This is an existing tilted three-quarter face; no claim of corrected frontal anatomy. Original hair/jaw/nose structure remains fixed. Gaze frames 1–6, blink 7–12, smile 13–18, notice 19–24. Closed eyelid is a newly authored Bezier stroke in frames 9–10, not a vertically squashed eye image. All aperture variation is vector path coordinate drawing. Iris translation is clipped to each actual aperture. There are 24 procedural composite frame drawings, not 24 hand-drawn inbetweens; no imagegen was used.

## Actual separation and limitations

Six independently editable transparent vector feature groups: eye whites, irises, eyelids, brows, mouth, cheeks. Each has standalone SVG and transparent PNG. Base body/face and foreground hair are transparent masked raster assets. They are not white rectangular raster clips. The SVG embeds these two raster assets and names all groups. Hair is preserved from the same crop, not independently redesigned. The base still contains hair underneath the separate foreground hair: this is NOT complete hidden-face/hair reconstruction or a production-ready full rig.

The original eyes/mouth are locally painted out. Initial boundary-colour interpolation produced vertical dark eye artifacts; the current eye backplates use sampled solid skin tones. Hair mask excludes those feature bands to avoid restoring original pupils. The source backdrop is retained behind the composed subject in videos, so the coarse silhouette matte does not produce a jagged contrasting fringe in the review render. Transparent assets still need professional edge cleanup. Feature repaint band edges and removed hair detail can be visible. Eye shape and mouth line are an approximate vector tracing; C identity is unproven and eye contours/mouth differ from source. Brow remains partially duplicated by original obscured brow detail. These are material HOLD defects, not artistic PASS.

## Required correction

An animator must redraw clean skin and fringe overlap on distinct layers, match the original eyelid thickness/eye corner angles and iris scale, correct mouth expression curvature, and adjust timing after actual playback. One second compresses four emotional beats heavily. The current soft smile/notice should not be described as clearly communicated without user review.

Production inspected extracted still frames. Normal-speed continuous playback has NOT been watched. Full decode/fps checks are a separate technical verification done by independent lane D. Technical PASS does not imply acting/identity PASS.

`render_parts.py` is the source used for reproduction (Pillow, CairoSVG, FFmpeg). It uses the bundled ../reference source and is a diagnostic production script; no approved asset is overwritten.

Neutral `cheeks.png` has zero opacity by design. `parts/cheeks_smile.svg` and `.png` contain the nonempty smile cheek marks from frame 17, visible on the regenerated parts sheet. Moving foreground hair alone exposes duplicated original hair in the base; it is an editable overlay, not a freely movable finished hair rig.
