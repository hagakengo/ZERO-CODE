"""Blender 4.5 native editable vector timing test, NOT character footage."""
import bpy, math, pathlib, json
out=pathlib.Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene; s.frame_start=1; s.frame_end=72; s.render.fps=24
s.render.engine='BLENDER_EEVEE_NEXT'; s.render.resolution_x=360; s.render.resolution_y=640; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.film_transparent=False
s.world.color=(0.012,0.018,0.03)
s.view_settings.view_transform='Standard'
def mat(name,color):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 n=m.node_tree.nodes; n.clear(); e=n.new('ShaderNodeEmission'); e.inputs[0].default_value=(*color,1); o=n.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(e.outputs[0],o.inputs[0]); return m
orange=mat('timing_marker_orange',(1,.34,.07)); white=mat('outline',(0.65,.79,.9)); blue=mat('baseline',(.12,.25,.38))
def line(name,points,material,cyclic=False,width=.018):
 c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=width; c.bevel_resolution=2
 p=c.splines.new('POLY'); p.points.add(len(points)-1)
 for q,co in zip(p.points,points): q.co=(*co,1)
 p.use_cyclic_u=cyclic
 ob=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(ob); c.materials.append(material); return ob
line('ground',[(-2.2,-2,0),(2.2,-2,0)],blue)
ball=line('editable_ball_outline',[(.45*math.cos(i*math.tau/64),.45*math.sin(i*math.tau/64),.1) for i in range(64)],orange,True,.03)
tail=line('follow_through_ribbon',[(0,0,.11)]*16,white)
# Four manually selected motion phases, deterministic curves and delayed follow-through.
for f in range(1,73):
 t=(f-1)/24
 x=-1.3+2.6*min(t/2.4,1)
 y=-1.52+2.3*abs(math.sin(math.pi*t/1.2))*math.exp(-.32*t)
 contact=abs(math.sin(math.pi*t/1.2))<.13
 ball.location=(x,y,0); ball.scale=(1.25 if contact else .94,.72 if contact else 1.06,1)
 ball.keyframe_insert('location',frame=f); ball.keyframe_insert('scale',frame=f)
 for i,p in enumerate(tail.data.splines[0].points):
  u=i/15; delay=.18*u; tt=max(0,t-delay)
  px=-1.3+2.6*min(tt/2.4,1)-.45*u
  py=-1.52+2.3*abs(math.sin(math.pi*tt/1.2))*math.exp(-.32*tt)+.1+.7*u
  p.co=(px,py,.11,1); p.keyframe_insert('co',frame=f)
camdata=bpy.data.cameras.new('locked_orthographic'); cam=bpy.data.objects.new('locked_orthographic',camdata); bpy.context.collection.objects.link(cam); cam.location=(0,.4,10); camdata.type='ORTHO'; camdata.ortho_scale=8; s.camera=cam
s['status']='DRAFT / HOLD — generic timing test, no C/FILM likeness claim'
s['method']='Blender editable Curve vector animation; not Grease Pencil drawing'
s.render.filepath=str(out/'frames'/'frame_'); (out/'frames').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'vector_timing_DRAFT.blend'))
bpy.ops.render.render(animation=True)
(out/'render_manifest.json').write_text(json.dumps({'tool':bpy.app.version_string,'method':'native CURVE poly splines, per-frame editable keys','frames':72,'fps':24,'duration_seconds':3,'resolution':[360,640],'character_identity':'not tested; generic marker','status':'DRAFT/HOLD'},indent=2))
