"""DRAFT hybrid: exact source raster + native GP feature drawings. No image squeeze."""
import bpy,math,pathlib,json,csv
O=pathlib.Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.frame_start=1;s.frame_end=24;s.render.fps=24
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1024;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard';s.world.color=(.8,.8,.8)
s.render.film_transparent=False
# Unlit reference plane, packed in native project.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0));base=bpy.context.object;base.name='SOURCE_C_fixed_identity_raster';base.scale=(256,141.5,1)
m=bpy.data.materials.new('Source_image_emission');m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(O/'reference_C_crop.png'));tex.image.pack();m.node_tree.links.new(tex.outputs['Color'],em.inputs[0]);m.node_tree.links.new(em.outputs[0],out.inputs['Surface']);base.data.materials.append(m)
bpy.ops.object.grease_pencil_add(type='EMPTY');obj=bpy.context.object;obj.name='C_FACE_editable_GP_DRAFT';obj.data.layers.remove(obj.data.layers[0]);obj.data.materials.clear()
def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def mat(name,rgb,fill=False):
 m=bpy.data.materials.new(name);bpy.data.materials.create_gpencil_data(m);g=m.grease_pencil;co=tuple(srgb(v/255) for v in rgb)+(1,);g.color=co;g.fill_color=co;g.show_fill=fill;g.show_stroke=not fill;obj.data.materials.append(m);return len(obj.data.materials)-1
ink=mat('ink',(49,41,41));white=mat('muted_sclera',(178,157,144),True);iris=mat('iris',(75,69,70),True);pupil=mat('pupil',(37,35,38),True);shine=mat('catchlight',(211,193,170),True);skinL=mat('skin_left_cover_DRAFT',(156,130,116),True);skinR=mat('skin_right_cover_DRAFT',(167,140,123),True)
def layer(name):
 l=obj.data.layers.new(name,set_active=True);l.use_lights=False;return l
cover=layer('01_source_eye_coverage_DRAFT');eyes=layer('02_sclera_drawing_keys');irises=layer('03_gaze_drawing_keys');lids=layer('04_upper_lower_and_closed_lids')
def draw(l,f,paths,z):
 d=l.frames.new(f).drawing
 if not paths:return
 d.add_strokes([len(p[0]) for p in paths])
 for st,(coords,mi,cyclic,radius) in zip(d.strokes,paths):
  st.material_index=mi;st.cyclic=cyclic
  for pt,(x,y) in zip(st.points,coords):pt.position=(x-256,141.5-y,z);pt.radius=radius;pt.opacity=1
 d.tag_positions_changed()
def bez(a,b,c,N=30):return [((1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0],(1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1]) for t in [i/(N-1) for i in range(N)]]
def ellipse(cx,cy,rx,ry):return [(cx+rx*math.cos(i*math.tau/48),cy+ry*math.sin(i*math.tau/48)) for i in range(48)]
# Draw small bounded strips; source preservation except these GP overlays.
patch=[]
for x,y,rgb in json.loads((O/'GP_skin_shading_samples.json').read_text()):
 mi=mat('skin_shade_%d_%d'%(x,y),rgb,True)
 patch.append(([(x,y),(x+1.03,y),(x+1.03,y+1.03),(x,y+1.03)],mi,True,.01))
draw(cover,1,patch,.10)
# Independent chosen pose controls; held drawings create exposure, no automated image transforms.
# frame, aperture, gaze offset, notice aperture addition
controls={1:(1,0,0),4:(1,.4,0),5:(1,1.3,0),6:(1,2.0,0),7:(.75,2,0),8:(.35,2,0),9:(0,2,0),11:(.45,2,0),12:(.9,2,0),13:(1,2,0),16:(1,2,.3),18:(1,1.8,.65),20:(1,1.6,1)}
keydata=json.loads((O/'eyelid_contour_keys_DRAFT.json').read_text())
def cubic(pts):
 return [tuple(sum((1-t)**(3-k)*t**k*[1,3,3,1][k]*pts[k][j] for k in range(4)) for j in range(2)) for t in [i/29 for i in range(30)]]
for f,(a,g,n) in controls.items():
 ep=[];ip=[];lp=[]
 for x,y,dx,dy in [(204,110,30,-11),(263,83,35,-13)]:
  if a==0:
   closed=cubic(keydata['upper_lid_keys']['closed']['L' if x==204 else 'R']);lp.append((closed,ink,False,.8));continue
  h=(4.5+n*1.8)*a
  kn='half_close' if a<.6 else 'quarter_close' if a<1 else 'notice' if n>.4 else 'neutral';en='L' if x==204 else 'R';upper=cubic(keydata['upper_lid_keys'][kn][en]);lower=cubic(keydata['lower_lid_support'][en])
  ep.append((upper+list(reversed(lower)),white,True,.1));lp.extend([(upper,ink,False,.83),(lower,ink,False,.32)])
  # Clip iris/pupil against explicit aperture using linear interpolation of bezier y at x.
  def bound(xx,pts):
   for p,q in zip(pts,pts[1:]):
    if p[0]<=xx<=q[0]:return p[1]+(q[1]-p[1])*(xx-p[0])/(q[0]-p[0])
   return pts[0][1] if xx<x else pts[-1][1]
  def clipped(rx,ry):
   co=ellipse(x+dx*.56+g,y+dy*.52,rx,ry)
   return [(xx,max(bound(xx,upper),min(bound(xx,lower),yy))) for xx,yy in co]
  ip.extend([(clipped(4.5,5.0),iris,True,.1),(clipped(1.6,4.2),pupil,True,.1)])
  if a>.8:ip.append((ellipse(x+dx*.54+g,y+dy*.52-.5,.65,.65),shine,True,.1))
 draw(eyes,f,ep,.12);draw(irises,f,ip,.14);draw(lids,f,lp,.16)
# Existing transparent fringe extraction stays above native feature drawings.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,.22));hair=bpy.context.object;hair.name='Existing_foreground_hair_raster_DRAFT';hair.scale=(256,141.5,1)
hm=bpy.data.materials.new('Hair_alpha_emission');hm.use_nodes=True;hn=hm.node_tree.nodes;hn.clear();ho=hn.new('ShaderNodeOutputMaterial');he=hn.new('ShaderNodeEmission');ht=hn.new('ShaderNodeTexImage');ht.image=bpy.data.images.load(str(O/'foreground_hair_existing_DRAFT.png'));ht.image.pack();tr=hn.new('ShaderNodeBsdfTransparent');mix=hn.new('ShaderNodeMixShader');hm.node_tree.links.new(ht.outputs['Color'],he.inputs[0]);hm.node_tree.links.new(ht.outputs['Alpha'],mix.inputs[0]);hm.node_tree.links.new(tr.outputs[0],mix.inputs[1]);hm.node_tree.links.new(he.outputs[0],mix.inputs[2]);hm.node_tree.links.new(mix.outputs[0],ho.inputs[0]);hair.data.materials.append(hm)
camd=bpy.data.cameras.new('locked_C_angle');cam=bpy.data.objects.new('locked_C_angle',camd);bpy.context.collection.objects.link(cam);cam.location=(0,0,1000);camd.type='ORTHO';camd.ortho_scale=512;s.camera=cam
s['status']='DRAFT/HOLD — GP/raster hybrid; not full character drawing, producer approval pending'
s['method']='5 explicitly specified cubic contour pairs; 13 procedural feature poses; held exposure; separate closed lid drawing; no eye image vertical scaling'
s['identity']='Exact raster silhouette / jaw / hair retained; eye patch boundary requires review'
(O/'frames').mkdir(exist_ok=True);s.render.filepath=str(O/'frames/frame_');s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'C_gaze_blink_DRAFT.blend'));bpy.ops.render.render(animation=True)
rows=[]
for f in range(1,25):
 k=max(k for k in controls if k<=f);rows.append([f,(f-1)/24,k,*controls[k], 'closed_lid' if controls[k][0]==0 else 'gaze' if f<7 else 'blink' if f<13 else 'notice'])
with (O/'exposure.csv').open('w') as q:
 w=csv.writer(q);w.writerow(['frame','time_seconds','drawing_key','aperture','gaze_px','notice','beat']);w.writerows(rows)
(O/'manifest.json').write_text(json.dumps({'tool':bpy.app.version_string,'status':'DRAFT/HOLD','fps':24,'frames':24,'chosen_feature_poses':len(controls),'GP_layer_drawing_counts':{l.name:len(l.frames) for l in obj.data.layers},'human_hand_drawn_count':0,'procedural_vector_poses':len(controls),'explicit_cubic_contour_pairs':5,'GP_skin_cover_quadrilaterals':len(patch),'interpolated_drawings':0,'held_exposure_frames':24-len(controls),'raster_source':'reference_C_crop.png','closed_lid_frames':[9,10],'head_hair_neck_motion':False},indent=2))
