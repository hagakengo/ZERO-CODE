"""Local Blender shallow projection set; retained original blocking hidden. Fixed camera deliberately preserves B architecture."""
import bpy, math, random, sys, argparse
from pathlib import Path
from mathutils import Vector
repo=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=repo/'reviews/aicity_production_DRAFT_HOLD_20261014');p.add_argument('--frames',type=Path,default=Path.cwd()/'work/render_city');p.add_argument('--art',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=a.out.resolve();frames=a.frames.resolve();out.mkdir(exist_ok=True,parents=True);frames.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(repo/'reviews/aicity_25d_blocking_HOLD_20261014/AI_CITY_BLOCKING_DRAFT_HOLD.blend'))
s=bpy.context.scene
for ob in list(bpy.data.objects): ob.hide_render=True;ob.hide_set(True)
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=16
s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.frame_start=1;s.frame_end=72
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world.color=(0,0,0)
s.render.image_settings.file_format='PNG'
W=9;H=16
img=bpy.data.images.load(str(a.art or out/'background_B_grade.png'));img.pack()
m=bpy.data.materials.new('B_handpainted_projection_graded');m.use_nodes=True;n=m.node_tree.nodes;n.clear();tex=n.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';em=n.new('ShaderNodeEmission');op=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);m.node_tree.links.new(em.outputs[0],op.inputs[0])
def plane(name,uvs,z):
 verts=[((u-.5)*W,(v-.5)*H,z) for u,v in uvs];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[list(range(len(verts)))]);me.uv_layers.new()
 for loop in me.loops:me.uv_layers.active.data[loop.index].uv=uvs[loop.vertex_index]
 ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);ob.data.materials.append(m);return ob
plane('B_far_city_projection',[(0,0),(1,0),(1,1),(0,1)],0)
# All UVs sample the unchanged B. Foreground geometry stays fixed and connected.
plane('Connected_foreground_column_and_overhead',[(0,0),(.28,0),(.28,.19),(.24,.29),(.30,.63),(.36,.82),(.93,1),(0,1)],3)
plane('Right_street_wall_occluder',[(.99,0),(1,0),(1,1),(.86,.98),(.84,.61),(.79,.50),(.71,.43),(.73,.34),(.99,.33)],2)
# At the painted bridge, its front parapet occludes the lower half of the vehicle.
plane('Bridge_front_parapet',[(.40,.420),(.72,.428),(.72,.438),(.40,.429)],1.3)
bpy.ops.object.camera_add(location=(0,0,25));cam=bpy.context.object;cam.name='PRODUCTION_LOCKED_CAMERA';cam.data.type='ORTHO';cam.data.ortho_scale=H;cam.rotation_euler=(0,0,0);s.camera=cam
# Emissive hand-painted-like subdued fills.
def color(name,c):
 mm=bpy.data.materials.new(name);mm.use_nodes=True;ns=mm.node_tree.nodes;ns.clear();e=ns.new('ShaderNodeEmission');e.inputs[0].default_value=(*c,1);o=ns.new('ShaderNodeOutputMaterial');mm.node_tree.links.new(e.outputs[0],o.inputs[0]);return mm
body=color('transit charcoal blue',(.022,.044,.059));win=color('muted warm cabin windows',(.40,.25,.095));rain=color('rain cool grey',(.13,.20,.27));ripple=color('puddle glints',(.11,.19,.24));cyan=color('distant headlights',(.31,.43,.46))
def box(name,loc,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);return o
car=bpy.data.objects.new('Independent_distant_transit',None);s.collection.objects.link(car)
for ob in [box('transit_body',(0,0,0),(.43,.078,.045),body),box('transit_roof',(0,.046,-.005),(.35,.028,.04),body)]:ob.parent=car
for x in [-.14,-.07,0,.07,.14]:
 o=box('transit_window',(x,.012,.027),(.042,.031,.008),win);o.parent=car
o=box('small_transit_headlight',(.218,-.006,.03),(.016,.014,.01),cyan);o.parent=car
rng=random.Random(20261014);drops=[]
for i in range(260):
 x=rng.uniform(-4.4,4.4);y=rng.uniform(-8,8);z=rng.choice([.8,1.8,3.8,4.2]);v=rng.uniform(5,12);length=rng.uniform(.035,.19)
 o=box('rain_world_%03d'%i,(x,y,z),(.004,length,.003),rain);o.rotation_euler.z=-.10;drops.append((o,x,y,z,v))
# Thin elliptical rings animate over the painted road; no displacement of the source artwork.
rings=[]
for i in range(20):
 u=rng.uniform(.32,.95);v=rng.uniform(.07,.32);phase=rng.random()
 cu=bpy.data.curves.new('puddle_ring','CURVE');cu.dimensions='3D';cu.bevel_depth=.003;cu.bevel_resolution=0;sp=cu.splines.new('POLY');sp.points.add(31)
 for j,p in enumerate(sp.points):ang=j/32*2*math.pi;p.co=(math.cos(ang),math.sin(ang)*.22,0,1)
 sp.use_cyclic_u=True;o=bpy.data.objects.new('Independent_puddle_ripple',cu);s.collection.objects.link(o);o.location=((u-.5)*W,(v-.5)*H,1.5);cu.materials.append(ripple);rings.append((o,phase,rng.uniform(.06,.15)))
for f in range(1,73):
 t=(f-1)/24
 car.location=((-1.65+1.40*t),(.445-.5)*H+.024,1.1);car.keyframe_insert('location',frame=f)
 for o,x,y,z,speed in drops:
  o.location=(x-.12*t,((y-speed*t+8)%16)-8,z);o.keyframe_insert('location',frame=f)
 for o,phase,size in rings:
  q=(t*.85+phase)%1;scale=size*(.18+q);o.scale=(scale,scale,1);o.keyframe_insert('scale',frame=f)
for o in [car]+[x[0] for x in drops]+[x[0] for x in rings]:
 if o.animation_data:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
s['STATUS']='DRAFT/HOLD. Adopted 0 sec. 3 sec candidate. No characters.';s['METHOD']='Existing blocking retained hidden; fixed camera shallow 3D projection, connected foreground occlusion, independent transit/rain/ripples. Camera parallax intentionally not claimed.'
s.frame_set(36);s.render.filepath=str(out/'preview_frame36.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'AI_CITY_PRODUCTION_DRAFT_HOLD.blend'));bpy.ops.render.render(write_still=True)
if not a.preview:
 s.render.filepath=str(frames/'frame_');bpy.ops.render.render(animation=True)
