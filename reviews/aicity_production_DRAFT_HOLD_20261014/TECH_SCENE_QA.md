# Blender scene QA — DRAFT/HOLD

- Existing blocking .blend loaded; greybox, test figure, and original animated camera retained but hidden from rendering. No canonical character created.
- B grade packed into .blend. Fixed orthographic camera; unchanged B composition, no image zoom and no independent column translation. Camera parallax improvement is intentionally unclaimed.
- Actual shallow meshes: far city at depth 0, bridge parapet 1.3, street wall 2, connected left column/overhead 3. Vehicle depth 1.1 is occluded by parapet/foreground. Geometry is a fixed projection set, not a full city reconstruction.
- Independent animation: distant commuter vehicle with five warm windows moves left-to-right; 260 rain streaks at four depths; 20 expanding puddle rings. 72 independently rendered frames, no duplicated-frame interpolation.
- Technical silent MP4 probe: 1080×1920, 24/1 fps, 72 frames, duration 3.000 seconds. Representative frame 36 inspected visually: B composition retained; transit visible against bridge; no greybox figure. Normal-speed continuous playback not verified by this lane.
- Limits: B has baked rain/fog/lights; animated rainfall has no roof shelter simulation or splash simulation. No physical fog/lighting animation in Blender. Ring animation is stylized; rain wraps at screen limits. Parent may add restrained atmosphere in post.
- Reproduction: `Blender -b --python reviews/aicity_production_DRAFT_HOLD_20261014/source/build_production.py -- --out /output --frames /scratch/frames --art /background_B_grade.png`. Optional `--preview` renders frame 36 only. Repository path is inferred from script location. Frame output must stay outside committed source. Arguments and preview rerun checked locally.
