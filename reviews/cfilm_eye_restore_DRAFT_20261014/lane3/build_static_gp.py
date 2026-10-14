"""Import explicitly authored sampled drawing paths. Static poses only, DRAFT/HOLD."""
import bpy,json,pathlib
O=pathlib.Path(__file__).resolve().parent
I=O/'drawing_paths_DRAFT.json'
data=json.loads(I.read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.frame_start=1;s.frame_end=1;s.render.fps=24
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1024;s.render.resolution_y=566;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.film_transparent=True;s.view_settings.view_transform='Standard'
def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def color(h):
 h=h.lstrip('#');return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
poses=data.get('poses',{'open':data.get('paths',[])})
report={'status':'DRAFT/HOLD','tool':bpy.app.version_string,'frame_range':[1,1],'animation_produced':False,'poses':{}}
objects=[]
for name,paths in poses.items():
 bpy.ops.object.grease_pencil_add(type='EMPTY');ob=bpy.context.object;ob.name='C_FULL_FACE_'+name+'_DRAFT';ob.data.layers.remove(ob.data.layers[0]);ob.data.materials.clear();objects.append(ob)
 mats={};layers={};drawings={};nst=0
 def mat(h,fill):
  key=(h,fill)
  if key not in mats:
   m=bpy.data.materials.new(name+'_'+h+('_fill' if fill else '_ink'));bpy.data.materials.create_gpencil_data(m);g=m.grease_pencil;g.color=color(h);g.fill_color=color(h);g.show_fill=fill;g.show_stroke=not fill;ob.data.materials.append(m);mats[key]=len(ob.data.materials)-1
  return mats[key]
 for index,p in enumerate(paths):
  group=p.get('group','drawing');ln=f'{index:03d}_{group}'
  layer=ob.data.layers.new(ln,set_active=True);layer.use_lights=False;d=layer.frames.new(1).drawing
  pts=p['points']
  for fill,h in [(True,p.get('fill')),(False,p.get('stroke'))]:
   if not h or h=='none' or len(pts)<2:continue
   d.add_strokes([len(pts)]);st=d.strokes[-1];st.material_index=mat(h,fill);st.cyclic=fill or p.get('closed',False)
   for pt,(x,y) in zip(st.points,pts):pt.position=(x-256,141.5-y,index*.01+(.002 if not fill else 0));pt.radius=max(.02,p.get('stroke_width',1)/2);pt.opacity=1
   nst+=1
  d.tag_positions_changed()
 ob['status']='DRAFT/HOLD: explicitly authored Bezier rough, identity not approved';report['poses'][name]={'layers':len(ob.data.layers),'strokes':nst,'source_paths':len(paths)}
camd=bpy.data.cameras.new('static_review');cam=bpy.data.objects.new('static_review',camd);bpy.context.collection.objects.link(cam);cam.location=(0,0,1000);camd.type='ORTHO';camd.ortho_scale=512;s.camera=cam
s['status']='DRAFT/HOLD; user still-face approval required before any animation';s['raster_images_used']=0;s['skin_repair_overlays']=0;s['authorship']='AI coordinate-authored vector rough; no human hand drawing; no image generation'
for i,ob in enumerate(objects):ob.hide_render=i!=0;ob.hide_viewport=i!=0
s.render.filepath=str(O/'GP_open_static_DRAFT.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'C_eye_restore_static_DRAFT.blend'));bpy.ops.render.render(write_still=True)
(O/'native_build_report_DRAFT.json').write_text(json.dumps(report,indent=2))
