"""Real Blender Grease Pencil editable drawing timing test; no character assets."""
import bpy, math, pathlib, json
out=pathlib.Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene; s.frame_start=1; s.frame_end=72; s.render.fps=24
s.render.engine='BLENDER_EEVEE_NEXT'; s.render.resolution_x=360; s.render.resolution_y=640; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.world.color=(.015,.02,.035); s.view_settings.view_transform='Standard'
bpy.ops.object.grease_pencil_add(type='EMPTY'); obj=bpy.context.object; obj.name='GP_Timing_Test_DRAFT'
obj.data.layers.remove(obj.data.layers[0])
m=bpy.data.materials.new('Orange_ink'); bpy.data.materials.create_gpencil_data(m); m.grease_pencil.color=(1,.45,.12,1); obj.data.materials.clear(); obj.data.materials.append(m)
layer=obj.data.layers.new('ball_and_delayed_ribbon',set_active=True)
layer.use_lights=False
for frame in range(1,73):
 d=layer.frames.new(frame).drawing; d.add_strokes([65,16,2]); t=(frame-1)/24
 x=-1.3+2.6*min(t/2.4,1); y=-1.52+2.3*abs(math.sin(math.pi*t/1.2))*math.exp(-.32*t)
 contact=abs(math.sin(math.pi*t/1.2))<.13
 sx,sy=(1.25,.72) if contact else (.94,1.06)
 for i,p in enumerate(d.strokes[0].points):
  a=i*math.tau/64; p.position=(x+.45*sx*math.cos(a),y+.45*sy*math.sin(a),.1); p.radius=.035; p.opacity=1
 for i,p in enumerate(d.strokes[1].points):
  u=i/15; tt=max(0,t-.18*u)
  p.position=(-1.3+2.6*min(tt/2.4,1)-.45*u,-1.52+2.3*abs(math.sin(math.pi*tt/1.2))*math.exp(-.32*tt)+.1+.7*u,.11); p.radius=.017; p.opacity=1
 for p,co in zip(d.strokes[2].points,[(-2.2,-2,0),(2.2,-2,0)]): p.position=co; p.radius=.01; p.opacity=.6
 d.tag_positions_changed()
camdata=bpy.data.cameras.new('locked_orthographic'); cam=bpy.data.objects.new('locked_orthographic',camdata); bpy.context.collection.objects.link(cam); cam.location=(0,.4,10); camdata.type='ORTHO'; camdata.ortho_scale=8; s.camera=cam
s['status']='DRAFT / HOLD — generic timing test, not C/FILM footage'
s['method']='Real GREASEPENCIL object; 72 editable drawings; formula-generated stroke points'
s.render.filepath=str(out/'frames'/'frame_'); (out/'frames').mkdir(exist_ok=True)
s.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=str(out/'gp_timing_DRAFT.blend'))
bpy.ops.render.render(animation=True)
(out/'render_manifest.json').write_text(json.dumps({'tool':bpy.app.version_string,'object_type':obj.type,'layers':len(obj.data.layers),'drawing_keys':len(layer.frames),'method':'actual GP strokes; deterministic point coordinates; not human hand drawing','frames':72,'fps':24,'duration_seconds':3,'resolution':[360,640],'identity':'not tested; generic ball/ribbon','status':'DRAFT/HOLD'},indent=2))
