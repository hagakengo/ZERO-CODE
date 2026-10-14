"""Read-only render of six fixed-camera controls; does not save altered blend.
blender -b scene.blend --python render_fixed_camera_samples.py -- SCRATCH
"""
import bpy,sys
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--')+1]);s=bpy.context.scene;cam=s.camera
cam.animation_data_clear();cam.location=(0,-10,2)
for f in [1,24,30,36,48,72]:
 s.frame_set(f);s.render.filepath=str(p/f'control_{f:04d}.png');bpy.ops.render.render(write_still=True)
