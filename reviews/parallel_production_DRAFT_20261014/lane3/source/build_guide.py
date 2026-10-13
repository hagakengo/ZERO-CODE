from pathlib import Path
import math,json,csv,subprocess
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
for d in ['guide_frames','cel_frames','mesh','video']: (R/d).mkdir(exist_ok=True)
def V(a,b):return tuple(x+y for x,y in zip(a,b))
def S(a,s):return tuple(x*s for x in a)
def sub(a,b):return V(a,S(b,-1))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return S(a,1/max(1e-8,math.sqrt(dot(a,a))))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def lerp(a,b,t):return a+(b-a)*t
def interp(f,ks):
 for (a,x),(b,y) in zip(ks,ks[1:]):
  if f<=b:
   t=max(0,(f-a)/(b-a));t=t*t*(3-2*t);return lerp(x,y,t)
 return ks[-1][1]
def rot(p,yaw):
 c,s=math.cos(yaw),math.sin(yaw);x,y,z=p;return (x*c+z*s,y,-x*s+z*c)
cam=(3.6,2.7,6.8); target=(.5,.9,0); forward=norm(sub(target,cam)); right=norm(cross(forward,(0,1,0))); up=cross(right,forward)
def proj(p):
 q=sub(p,cam);z=dot(q,forward);return (540+3000*dot(q,right)/z,1060-3000*dot(q,up)/z,z)
def box(c,dim,yaw,color,faces):
 pts=[V(c,rot((x*dim[0]/2,y*dim[1]/2,z*dim[2]/2),yaw)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 for ids in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]:faces.append(([pts[i] for i in ids],color))
def tube(a,b,r1,r2,color,faces,n=8):
 axis=norm(sub(b,a));u=norm(cross(axis,(0,0,1)));v=cross(axis,u)
 rings=[[V(c,V(S(u,r*math.cos(i*2*math.pi/n)),S(v,r*math.sin(i*2*math.pi/n)))) for i in range(n)] for c,r in [(a,r1),(b,r2)]]
 for i in range(n):faces.append(([rings[0][i],rings[0][(i+1)%n],rings[1][(i+1)%n],rings[1][i]],color))
 faces.extend([(rings[0],color),(rings[1],color)])
def ik(hip,ankle):
 # Equal segment lengths, knee bends forward (-Z). No interpolation of foot coordinates while planted.
 d=sub(ankle,hip);length=math.sqrt(dot(d,d));mid=S(V(hip,ankle),.5);direction=norm(d);bend=norm(sub((0,0,-1),S(direction,dot((0,0,-1),direction))))
 return V(mid,S(bend,math.sqrt(max(0,.55**2-(length/2)**2))))
records=[];allposes=[]
for f in range(30):
 x=interp(f,[(0,-.08),(5,-.18),(10,.08),(17,.72),(22,.84),(29,.83)])
 y=interp(f,[(0,.98),(5,.79),(10,1.02),(14,1.16),(17,.97),(21,.78),(29,.98)])
 py=math.radians(interp(f,[(0,-8),(5,-18),(10,12),(17,20),(22,4),(29,0)]));sy=math.radians(interp(f,[(0,8),(6,-4),(12,-18),(19,13),(25,-5),(29,0)]))
 pelvis=(x,y,0)
 # Thorax and head have distinct delay/compensation, rather than fixed offsets.
 lean=interp(f,[(0,-.04),(5,-.14),(9,-.20),(14,-.09),(17,.10),(21,.03),(25,-.04),(29,0)])
 chest=(x+lean,y+.43-abs(lean)*.30,-.08)
 headcomp=interp(f,[(0,0),(8,.05),(14,.10),(19,-.08),(24,.03),(29,0)])
 hood=(chest[0]+headcomp,y+.79-abs(lean)*.30,-.07)
 hem_lag=interp(f,[(0,0),(7,.025),(13,-.08),(18,-.11),(23,.05),(29,0)])
 lf=(-.35,0,.10) if f<=10 else (interp(f,[(10,-.35),(16,.48),(24,1.22),(29,1.22)]),interp(f,[(10,0),(15,.35),(24,0),(29,0)]),.1)
 rf=(interp(f,[(0,.28),(1,.28),(5,.32),(12,.68),(17,.97),(29,.97)]),interp(f,[(0,0),(1,0),(5,.08),(12,.33),(17,0),(29,0)]),-.13)
 hips=[V(pelvis,rot((s*.16,0,0),py)) for s in [-1,1]];ankles=[V(lf,(0,.07,0)),V(rf,(0,.07,0))];knees=[ik(h,a) for h,a in zip(hips,ankles)]
 baglag=interp(f,[(0,0),(5,.025),(10,-.09),(15,-.15),(18,-.12),(23,.06),(29,0)])
 bag=V(chest,(baglag,.015,.27));bagyaw=sy+math.radians(interp(f,[(0,0),(12,8),(19,-9),(29,0)]))
 pose={'frame':f+216,'pelvis':pelvis,'chest':chest,'hood':hood,'left_foot':lf,'right_foot':rf,'hips':hips,'knees':knees,'ankles':ankles,'pelvis_yaw_deg':math.degrees(py),'shoulder_yaw_deg':math.degrees(sy),'bag':bag,'bag_yaw':bagyaw,'thorax_lateral_offset':lean,'head_compensation':headcomp,'hem_lag':hem_lag,'left_contact':f<=10 or f>=24,'right_contact':f<=1 or f>=17};allposes.append(pose)
 for mode in ['guide','cel']:
  faces=[];col=(115,138,160) if mode=='guide' else (29,32,39);pants=(90,111,134) if mode=='guide' else (37,40,48)
  for side,(h,k,a,foot) in enumerate(zip(hips,knees,ankles,[lf,rf])):
   tube(h,k,.145,.115,pants,faces);tube(k,a,.12,.065,pants,faces);box(V(foot,(0,.055,-.045)),(.18,.11,.32),(math.radians(-8) if f<=10 else 0) if side==0 else 0,(45,49,58),faces)
  box(V(pelvis,(0,.025,0)),(.42,.25,.29),py,col,faces)
  tube(V(pelvis,(0,.08,0)),chest,.24,.29,col,faces,n=10)
  # Exposed face PROXY. C hair/eyes identity cannot be reproduced by these primitives.
  tube(V(chest,(0,.02,0)),V(hood,(0,-.12,0)),.10,.12,col,faces,n=8)
  # Faceted head, broad film-like dark planes; facial anchors are only proxy geometry.
  tube(V(hood,(0,-.14,0)),V(hood,(0,.09,0)),.135,.17,(179,143,125) if mode=='cel' else (156,162,166),faces,n=10)
  tube(V(hood,(0,.08,0)),V(hood,(0,.18,-.02)),.18,.095,(18,21,27),faces,n=10)
  hy=sy*.65
  for side in [-1,1]:
   eye=V(hood,rot((side*.065,.015,.14),hy));box(eye,(.047,.012,.014),hy,(27,27,33),faces)
  box(V(hood,rot((0,-.07,.135),hy)),(.045,.008,.012),hy,(64,46,44),faces)
  # Separate fringe wedges remain same topology across 30 frames.
  for q in range(7):
   xx=(q-3)*.043
   pts=[V(hood,rot((xx-.03,.13,.12),hy)),V(hood,rot((xx+.03,.13,.12),hy)),V(hood,rot((xx+.015,-.025-(q%3)*.013,.15),hy))]
   faces.append((pts,(18,21,27)))
  # Hoodie rests at neck; delayed hem and front opening are geometry, not texture warp.
  tube(V(chest,(0,-.03,-.01)),V(chest,(0,.07,-.03)),.22,.15,col,faces,n=8)
  tube(V(pelvis,(hem_lag,-.08,0)),V(pelvis,(0,.12,0)),.27,.25,col,faces,n=10)
  for side in [-1,1]:
   top=V(chest,rot((side*.06,0,.25),sy));base=V(pelvis,(side*.05+hem_lag,.03,.245))
   tube(top,base,.013,.013,(63,65,72),faces,n=4)
  for s in [-1,1]:
   shoulder=V(chest,rot((s*.28,.02,0),sy));elbow=V(shoulder,(s*.12,-.23,-.14));hand=V(elbow,(-s*.06,-.18,-.19))
   tube(shoulder,elbow,.12,.105,col,faces);tube(elbow,hand,.105,.065,col,faces);box(hand,(.10,.13,.10),sy,(55,58,65),faces)
  box(bag,(.41,.50,.22),bagyaw,(53,58,67) if mode=='cel' else (139,112,74),faces)
  for s in [-1,1]:
   top=V(chest,rot((s*.18,.12,.08),sy));end=V(bag,rot((s*.15,-.17,.06),bagyaw));tube(top,end,.025,.025,(68,72,81),faces,n=4)
  im=Image.new('RGB',(1080,1920),(187,193,201));draw=ImageDraw.Draw(im)
  for i in range(-4,6):
   for a,b in [((i*.5,0,-2),(i*.5,0,2)),((-2,0,i*.5),(3,0,i*.5))]:draw.line([proj(a)[:2],proj(b)[:2]],fill=(151,158,170),width=2)
  # Planted world-space footprints for visual registration.
  for foot,contact in [(lf,pose['left_contact']),(rf,pose['right_contact'])]:
   if contact:
    p=proj(foot);draw.ellipse((p[0]-25,p[1]-8,p[0]+25,p[1]+8),fill=(91,104,109))
  for pts,c in sorted(faces,key=lambda fc:sum(proj(p)[2] for p in fc[0])/len(fc[0]),reverse=True):
   n=norm(cross(sub(pts[1],pts[0]),sub(pts[2],pts[0])));light=.65+.35*abs(dot(n,norm((-1,2,2))));light= .70 if light<.82 else 1.12
   color=tuple(min(255,int(v*light)) for v in c);draw.polygon([proj(p)[:2] for p in pts],fill=color,outline=(24,29,37),width=3 if mode=='cel' else 1)
  draw.text((60,70),f'S04 v2  F{f+216}  |  {"3D VOLUME GUIDE" if mode=="guide" else "CEL-STYLE PROXY (NOT DRAWN ANIMATION)"}  DRAFT / HOLD',fill=(30,35,44),font_size=20)
  draw.text((60,1790),'C/FILM EXPLORATION / FACE & COSTUME IDENTITY HOLD',fill=(30,35,44),font_size=24)
  if mode=='guide':
   for a,b,c in [(pelvis,chest,(210,90,70)),(hips[0],hips[1],(225,152,42))]:draw.line([proj(a)[:2],proj(b)[:2]],fill=c,width=7)
   draw.text((60,1650),f'pelvis {math.degrees(py):+.1f} deg   shoulders {math.degrees(sy):+.1f} deg',fill=(30,35,44),font_size=24)
  im.save(R/f'{mode}_frames'/f'f{f+216:03}.png')
  if mode=='guide':
   lines=[];idx=1
   for pts,c in faces:
    lines.extend('v %.6f %.6f %.6f'%p for p in pts);lines.append('f '+' '.join(str(i) for i in range(idx,idx+len(pts))));idx+=len(pts)
   (R/'mesh'/f'f{f+216}.obj').write_text('\n'.join(lines))
 records.append([f+216,*lf,*rf,*pelvis,math.degrees(py),math.degrees(sy),pose['left_contact'],pose['right_contact']])
(R/'motion.json').write_text(json.dumps(allposes,indent=2))
with (R/'exposure_contact.csv').open('w') as out:
 w=csv.writer(out);w.writerow(['frame','Lx','Ly','Lz','Rx','Ry','Rz','pelvis_x','pelvis_y','pelvis_z','pelvis_yaw','shoulder_yaw','L_contact','R_contact']);w.writerows(records)
keys=[216,221,226,229,233,237,240,245]
sheet=Image.new('RGB',(1080*4,1920*2),(187,193,201))
for i,f in enumerate(keys):sheet.paste(Image.open(R/'guide_frames'/f'f{f}.png'),((i%4)*1080,(i//4)*1920))
sheet.resize((2160,1920)).save(R/'guide_keyposes.png')
for mode in ['guide','cel']:
 subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-start_number','216','-i',str(R/f'{mode}_frames'/'f%03d.png'),'-frames:v','30','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'video'/f'S04_{mode}_normal.mp4')],check=True)
print('30 new articulated 3D poses / OBJ / cel-style proxy. Identity HOLD.')
