# Lane B — corrected vector contour drawings / DRAFT · HOLD

24 frames, 1 second, 24fps; half speed is 48 frames / 2 seconds / 24fps. Same 512×283 C/FILM crop and same phases as A: gaze 0–5, blink 6–11, slight smile 12–17, noticing 18–23. Source is a tilted three-quarter pose, not a corrected frontal model.

## Exact drawing accounting

- 6 authored vector key states: zero-based frames 0, 5, 9, 11, 17, 23.
- 9 authored vector intermediate contour states: frames 3, 6, 7, 8, 10, 13, 15, 18, 20. Their separate left/right Bézier control coordinates are explicitly specified in `inbetween_controls` in `build.py` and serialized in `authored_contours.json`. They are distinct script-authored eyelid contours, not interpolation of three raster keys.
- 9 further exposures use numerical parameter interpolation: frames 1, 2, 4, 12, 14, 16, 19, 21, 22. These are procedural coordinate inbetweens, not newly authored drawings.
- Traditional human hand-drawn inbetween count: **0**. Full-face independently redrawn inbetween count: **0**. This is a partial vector contour experiment; the requested professional full-drawing correction workflow remains unmet.

All 24 frames retain the same source silhouette, nose, chin and hair. Upper and lower lids use drawn cubic paths, not compressed eye images. Iris size stays fixed and is occluded by the lid aperture. SVG files contain editable paths above an embedded source raster. The facial drawing remains a hybrid raster/vector composition, not a complete vector character. `brow_parameter_UNUSED` is deliberately named: brows remain source pixels and are not animated. This is an important unfulfilled synchronization requirement.

`normal_24fps.mp4`, `half_speed_24fps.mp4`, `all_frames_sheet_DRAFT.png`, `keys/`, `inbetweens/`, `drawings/`, `exposure.csv`, and the self-contained relative-reference `build.py` are the deliverables. Rebuild needs Python/Pillow and FFmpeg; bundled source is `../reference/A_B_C_comparison_DRAFT.png`.

## Visual review and limitations

Frame sheet and enlarged closed frame were inspected as stills. Normal-speed continuous playback was **not viewed**. No artistic PASS or identity PASS is claimed. Initial mouth paintout was visibly pale and rectangular; replaced with a narrow neighboring-skin reconstruction. Original rejected closed frame is retained under `rejected_v1/`. Initial iris size change was corrected to fixed-size iris occlusion.

Remaining HOLD issues: local eyelid skin paintout and old line remnants do not blend convincingly with the film-style shading; brow/hair overlap needs human cleanup; slight smile/noticing is weak at normal viewing size; mouth retouch has a small residual shading patch. The near-static source head means head/hair synchronization is not tested. A/B is a limited procedural-feature comparison, not proof of finished anime acting.

Next useful work is human drawing correction in a layer-aware animation editor: trace and approve the C/FILM eye socket/eyebrow/hair occlusion, repaint a clean face plate, then author linked eyelid, cheek and mouth contours against the same exposure sheet. Do not promote this test or generate many more versions with the same paintout method.
