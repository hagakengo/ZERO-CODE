"""Blender 4.5 local-only spatial test; no B textures, no canonical character.
blender -b --python build_blocking.py -- --out OUT --frames SCRATCH
Optional --preview renders only frame 36. Final 72 frames are 0..71 / 24 seconds.
"""
import bpy, math, random, argparse, sys, json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--frames',type=Path,required=True);p.add_argument('--preview',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True);a.frames.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=16
s.render.resolution_x=540;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.fps=24;s.frame_start=1;s.frame_end=72
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard';s.world.color=(.12,.12,.12)
s.render.film_transparent=False
# Emission greybox: colors indicate depth groups only, not final art.
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*c,1);m.node_tree.links.new(e.outputs[0],o.inputs['Surface']);return m
near=mat('NEAR neutral',(.075,.085,.10));mid=mat('MID neutral',(.23,.25,.28));far=mat('FAR neutral',(.40,.43,.47));floor=mat('GROUND neutral',(.16,.18,.20));ink=mat('TEST SILHOUETTE NOT CANON',(.018,.022,.028));rainmat=mat('RAIN test',(.54,.58,.63));light=mat('TIMED LIGHT test',(.65,.69,.72));lane=mat('GROUND guides',(.29,.31,.34))
def box(name,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def sphere(name,loc,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);return o
box('ground',(0,25,-.12),(80,100,.2),floor)
# One immobile architecture assembly: actual connected column and beam.
arch=bpy.data.objects.new('ARCHITECTURE_LOCKED',None);s.collection.objects.link(arch)
for o in [box('left_column',(-2.15,-3,4.5),(.85,1.2,9),near),box('connected_overhead_beam',(0,-3,8.7),(5.2,1.2,.65),near),box('right_column',(2.15,-3,4.5),(.85,1.2,9),near)]:o.parent=arch
for x in [-7,7]:box('street_wall', (x,10,4),(5,27,8),mid)
for y,h,w in [(23,13,4),(33,21,5),(45,26,6)]:
 for x in [-7,7]:box('city_side', (x,y,h/2),(w,6,h),mid if y<33 else far)
box('central_tower',(0,60,18),(7,8,36),far)
# Bridge piers are coherent; transit moves BEHIND them.
for x in [-2.4,2.4]:box('bridge_pier',(x,19,4),(.9,1.3,8),mid)
box('bridge_deck',(0,19,5.05),(16,1.3,.4),mid)
transit=box('TEST_TRANSIT_NOT_CANON',(-6,25,6.4),(2.2,.8,.6),ink)
bollard=box('near_occluder',(.0,2.5,.9),(.46,.55,1.8),near)
for x in [-3.6,3.6]:
 box('curb',(x,15,.08),(.1,46,.16),lane)
 for y in range(0,40,4):box('rail_post',(x,y,.65),(.07,.07,1.3),mid)
 box('rail',(x,15,1.25),(.065,46,.065),mid)
# Abstract human scale witness; no hoodie/backpack/face or character design.
figure=bpy.data.objects.new('TEST_FIGURE_NOT_CANON',None);s.collection.objects.link(figure)
parts=[sphere('test_head',(0,0,1.65),(.14,.12,.16),ink),box('test_torso',(0,0,1.15),(.38,.23,.65),ink)]
for x in [-.12,.12]:parts.append(box('test_leg',(x,0,.43),(.13,.16,.83),ink))
for o in parts:o.parent=figure
signal=box('LIGHT_TEST',(0,55,24),(7.04,.15,.48),light)
# Rain streaks in world space, not a screen overlay; within open street only.
rng=random.Random(20261014);drops=[]
for i in range(110):
 x=rng.uniform(-3.4,3.4);y=rng.uniform(-1,45);z=rng.uniform(0,18);speed=rng.uniform(6,10)
 o=box('rain_%03d'%i,(x,y,z),(.012,.012,rng.uniform(.12,.30)),rainmat);o.rotation_euler[1]=-.10;drops.append((o,x,y,z,speed))
bpy.ops.object.camera_add(location=(0,-10,2.0));cam=bpy.context.object;cam.name='CAMERA_FIXED_LENS_DOLLY';cam.data.lens=30;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36;cam.data.clip_end=200;cam.rotation_euler=(Vector((0,25,9))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
# Dense keys make every frame explicit. Lens and orientation remain fixed.
tele=[]
for f in range(1,73):
 t=(f-1)/24;u=t/3;cam.location=(.65*u,-10+.45*u,2);cam.keyframe_insert('location',frame=f)
 figure.location=(-1.35+1.05*t,6,0);figure.keyframe_insert('location',frame=f)
 # very small gait indication, not a walk-cycle/acting validation
 for j,o in enumerate(parts[2:]):o.rotation_euler[0]=.16*math.sin(t*8+j*math.pi);o.keyframe_insert('rotation_euler',frame=f)
 transit.location.x=-6+4*t;transit.keyframe_insert('location',frame=f)
 e=next(n for n in light.node_tree.nodes if n.type=='EMISSION');e.inputs['Strength'].default_value=.25 if 51<=f<=55 else 1;e.inputs['Strength'].keyframe_insert('default_value',frame=f)
 for o,x,y,z,v in drops:o.location=(x+.08*t,y,(z-v*t)%18);o.keyframe_insert('location',frame=f)
 s.frame_set(f);bpy.context.view_layer.update()
 torso=figure.matrix_world@Vector((0,0,1.15));direction=(torso-cam.location);hit,loc,n,idx,obj,mx=s.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction.normalized(),distance=direction.length-.20)
 def project(pt):
  q=world_to_camera_view(s,cam,Vector(pt));return [round(q.x*540,3),round((1-q.y)*960,3)]
 tele.append({'frame':f,'time_s':t,'figure_center_px':project(torso),'occluder_px':project((0,2.5,1.15)),'figure_center_blocker':obj.name if hit else None,'near_anchor_px':project((-2.15,-3,4.5)),'mid_anchor_px':project((-2.4,19,4)),'far_anchor_px':project((0,60,18))})
# Keys default Bezier: set LINEAR for predictable subframe re-rendering.
for ob in bpy.data.objects:
 if ob.animation_data and ob.animation_data.action:
  for fc in ob.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
s.frame_set(1);s.render.filepath='//renders/frame_';s['STATUS']='DRAFT / HOLD; ADOPTED 0 SECONDS; GEOMETRY TEST ONLY';s['ART']='No B texture inserted; no canon design';s['FOG']='Intentionally omitted from depth baseline; not validated';s['FRAME_TIMES']='frame 1..72 = t 0..71/24, duration 3s at 24fps'
bpy.ops.wm.save_as_mainfile(filepath=str(a.out/'AI_CITY_BLOCKING_DRAFT_HOLD.blend'))
(a.out/'spatial_measurements.json').write_text(json.dumps(tele,indent=2))
if a.preview:
 s.frame_set(36);s.render.filepath=str(a.frames/'preview.png');bpy.ops.render.render(write_still=True)
else:
 s.render.filepath=str(a.frames.resolve()/'frame_');bpy.ops.render.render(animation=True)
