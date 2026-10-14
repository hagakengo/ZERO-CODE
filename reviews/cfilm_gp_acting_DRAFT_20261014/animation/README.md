# C/FILM C-view gaze / blink — DRAFT / HOLD

Actual Blender 4.5.14 Grease Pencil + fixed raster source hybrid. 24 frames at24fps, 1 second; half-speed export is48 frames/2 seconds. Native `.blend` contains packed original C-view raster and existing transparent foreground fringe; eyelids, iris, sclera and bounded skin coverage are editable GP strokes/fills. Same head angle, silhouette, jaw and hair remain fixed.

Five explicit cubic upper-lid contour pairs supplied in `eyelid_contour_keys_DRAFT.json`: neutral, quarter closure, half closure, closed, notice. These are agent-specified vector coordinates; human hand-drawn originals:0. Thirteen feature drawing key times (some have identical visible poses) are exposed across24frames; eleven remaining frames are holds. No numerical interpolation frames. Closure f9–10 omits sclera/iris and uses its own cubic stroke; no eye-image vertical compression. Gaze moves max2 source pixels; slight notice switches upper contour near end. This is not a fully drawn character or completed film scene.

The GP skin cleanup still has visible borders and source line traces; not approved identity/craft quality. No 3second neck/hair extension was made because facial cleanup remains HOLD. Normal-speed continuous viewing and producer approval remain required.

Reproduce from this directory with Blender4.5:

```sh
/path/to/Blender -b --python build_acting_gp.py
ffmpeg -framerate 24 -i frames/frame_%04d.png -frames:v 24 -c:v libx264 -pix_fmt yuv420p C_gaze_blink_normal_24fps_DRAFT.mp4
ffmpeg -framerate 24 -i frames/frame_%04d.png -vf 'setpts=2*PTS,fps=24' -frames:v 48 -c:v libx264 -pix_fmt yuv420p C_gaze_blink_half_24fps_DRAFT.mp4
```

`GP_skin_shading_samples.json` contains numeric palette samples for native GP coverage; original raster source is untouched. `exposure.csv` lists actual drawing exposure. Reopening and full decode are independently checked by QA. `failed_initial/previous_revision_DRAFT.blend1` is the immediately preceding shading revision, retained as failed draft evidence, not selected for delivery video.
