"""Local Blender production: existing packed 2.5D scene + animated cel + masked light failure.
Usage: Blender -b --python build_scene.py -- --repo REPO --out OUTPUT --frames SCRATCH [--preview]
No camera zoom. Geometry is a shallow projection set, not a reconstructed city.
"""
import bpy,sys,argparse,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--frames',type=Path,required=True);p.add_argument('--preview',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);a.frames.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.repo.resolve()/'reviews/aicity_production_DRAFT_HOLD_20261014/AI_CITY_PRODUCTION_DRAFT_HOLD.blend'))
s=bpy.context.scene;s.eevee.taa_render_samples=16;s.render.resolution_percentage=100
# Replace inaccurate broad left occluder with traced connected column/beam silhouette.
ob=bpy.data.objects['Connected_foreground_column_and_overhead'];me=ob.data
screen=[(0,0),(.92,0),(.365,.18),(.33,.34),(.30,.50),(.285,.62),(.27,.68),(.35,.75),(.435,.80),(.44,.83),(.33,.81),(0,.78)]
uv=[(u,1-v) for u,v in screen];me.clear_geometry();me.from_pydata([((u-.5)*9,(v-.5)*16,3) for u,v in uv],[],[list(range(len(uv)))]);me.uv_layers.new()
for loop in me.loops:me.uv_layers.active.data[loop.index].uv=uv[loop.vertex_index]
# Original B remains packed. One mask affects matching windows and their wet-road reflection.
m=bpy.data.materials['B_handpainted_projection_graded'];nt=m.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');em=next(n for n in nt.nodes if n.type=='EMISSION')
mask=nt.nodes.new('ShaderNodeTexImage');mask.image=bpy.data.images.load(str(out/'light_mask.png'));mask.image.colorspace_settings.name='Non-Color';mask.image.pack()
value=nt.nodes.new('ShaderNodeValue');value.name='FAULT_STRENGTH_0_NORMAL_1_FAILED'
mult=nt.nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';nt.links.new(mask.outputs['Color'],mult.inputs[0]);nt.links.new(value.outputs[0],mult.inputs[1])
mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[2].default_value=(.055,.085,.13,1);nt.links.new(mult.outputs[0],mix.inputs[0]);nt.links.new(tex.outputs['Color'],mix.inputs[1]);nt.links.new(mix.outputs[0],em.inputs['Color'])
# Discrete irregular electrical drops, then permanent local outage at2s.
keys=[(1,0),(25,0),(26,.90),(28,0),(31,.98),(33,.15),(37,.95),(39,0),(44,.85),(46,.1),(49,1),(72,1)]
for f,v in keys:value.outputs[0].default_value=v;value.outputs[0].keyframe_insert('default_value',frame=f)
for fc in nt.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='CONSTANT'
# Separate cels are packed to make the saved .blend self-contained.
def pedestrian_motion(t):
 start,end=1.14,1.58
 if t<=start:travel=165*t
 elif t<end:
  u=(t-start)/(end-start);travel=165*(start+(end-start)*(u-u*u/2))
 else:travel=165*(start+(end-start)/2)
 return dict(travel_px=travel)
W,H=240,420;display_scale=1.0;feet=1460;start=340
verts=[(-W/2*9/1080,-H/2*16/1920,0),(W/2*9/1080,-H/2*16/1920,0),(W/2*9/1080,H/2*16/1920,0),(-W/2*9/1080,H/2*16/1920,0)]
mesh=bpy.data.meshes.new('Hand_drawn_cel_quad');mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.uv_layers.new()
for i,loop in enumerate(mesh.loops):mesh.uv_layers.active.data[loop.index].uv=[(0,0),(1,0),(1,1),(0,1)][i]
for f in range(72):
 image=bpy.data.images.load(str(out/'pedestrian'/f'{f:03d}.png'));image.pack()
 mat=bpy.data.materials.new(f'Anonymous_CEL_{f:03d}');mat.use_nodes=True;mat.surface_render_method='DITHERED';n=mat.node_tree.nodes;n.clear();t=n.new('ShaderNodeTexImage');t.image=image;e=n.new('ShaderNodeEmission');tr=n.new('ShaderNodeBsdfTransparent');mx=n.new('ShaderNodeMixShader');op=n.new('ShaderNodeOutputMaterial');ln=mat.node_tree.links;ln.new(t.outputs['Color'],e.inputs['Color']);ln.new(t.outputs['Alpha'],mx.inputs[0]);ln.new(tr.outputs[0],mx.inputs[1]);ln.new(e.outputs[0],mx.inputs[2]);ln.new(mx.outputs[0],op.inputs[0])
 o=bpy.data.objects.new(f'Anonymous_passerby_CEL_{f:03d}',mesh.copy());s.collection.objects.link(o);o.data.materials.clear();o.data.materials.append(mat)
 centerx=start+pedestrian_motion(f/24)['travel_px'];centery=feet-404+H/2;o.location=((centerx/1080-.5)*9,(.5-centery/1920)*16,2.5)
 for frame,hide in [(1,True),(f+1,False),(f+2,True)]:
  if f==0 and frame==1 and hide:continue
  o.hide_render=hide;o.keyframe_insert('hide_render',frame=frame)
 if o.animation_data:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='CONSTANT'
# Small soft contact shadow is anchored to the planted foot baseline.
shimg=bpy.data.images.load(str(out/'contact_shadow.png'));shimg.pack()
shmat=bpy.data.materials.new('Soft_contact_shadow');shmat.use_nodes=True;shmat.surface_render_method='DITHERED';ns=shmat.node_tree.nodes;ns.clear();tx=ns.new('ShaderNodeTexImage');tx.image=shimg;ee=ns.new('ShaderNodeEmission');tt=ns.new('ShaderNodeBsdfTransparent');mm=ns.new('ShaderNodeMixShader');oo=ns.new('ShaderNodeOutputMaterial');ll=shmat.node_tree.links;ll.new(tx.outputs['Color'],ee.inputs['Color']);ll.new(tx.outputs['Alpha'],mm.inputs[0]);ll.new(tt.outputs[0],mm.inputs[1]);ll.new(ee.outputs[0],mm.inputs[2]);ll.new(mm.outputs[0],oo.inputs[0])
sh=bpy.data.objects.new('Foot_contact_shadow',mesh.copy());s.collection.objects.link(sh);sh.data.materials.clear();sh.data.materials.append(shmat);sh.scale=(.40,.10,1)
for f in range(72):
 sh.location=(((start+pedestrian_motion(f/24)['travel_px'])/1080-.5)*9,(.5-(feet-2)/1920)*16,2.4);sh.keyframe_insert('location',frame=f+1)
s['STATUS']='DRAFT/HOLD; producer approval pending; adopted0s/candidate3s. Anonymous commuter is not character A/B.'
s['LIVING_ACTION']='0-1 walk/traffic;1.04 flicker;1.14 deceleration;1.28 head/arm attention;1.58 stop;2s local outage;traffic/rain continue.'
s['LIMITATIONS']='Locked camera shallow projection; no full reconstructed city or camera parallax. B baked rain remains. Cel walk needs real-time artistic review.'
s.frame_set(1);s.render.filepath='//renders/frame_';bpy.ops.wm.save_as_mainfile(filepath=str(out/'AI_CITY_LIVING_DRAFT_HOLD.blend'))
if a.preview:
 for f in [1,24,31,38,49,72]:s.frame_set(f);s.render.filepath=str(a.frames.resolve()/f'preview_{f:04d}.png');bpy.ops.render.render(write_still=True)
else:s.render.filepath=str(a.frames.resolve()/'frame_');bpy.ops.render.render(animation=True)
