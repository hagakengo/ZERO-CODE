"""DRAFT/HOLD generic 3D construction test. NOT a C/FILM likeness render.
Python 3 + Pillow; ffmpeg on PATH. No source image is edited or sampled.
All frames project one immutable 3D mesh. Coordinates are a generic hypothesis.
"""
import math, json, csv, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
FRAMES=OUT/'frames'; FRAMES.mkdir(exist_ok=True)
W,H=960,720
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n): return ImageFont.truetype(FONT,n)
def smooth(t):
    t=max(0,min(1,t)); return t*t*t*(t*(t*6-15)+10)
def yaw(f): return 85*smooth((f-3)/18)
def hair_yaw(f): return 85*smooth((f-5)/18)
def rot(p,a):
    x,y,z=p; a=math.radians(a)
    return (x*math.cos(a)+z*math.sin(a),y,-x*math.sin(a)+z*math.cos(a))
def project(p): return (round(300+p[0]*152),round(343-p[1]*152))
def p3(u,v):
    # Single ellipsoid, tapered lower jaw. This is NOT fitted to C/FILM.
    s=math.sin(v); low=1 if math.cos(v)>-.28 else .68+.32*(1+math.cos(v))/.72
    return (.80*s*math.cos(u)*low,1.12*math.cos(v),.70*s*math.sin(u))
mesh=[]
for j in range(24):
    for k in range(48):
        v0=math.pi*j/24; v1=math.pi*(j+1)/24
        u0=2*math.pi*k/48; u1=2*math.pi*(k+1)/48
        q=[p3(u0,v0),p3(u1,v0),p3(u1,v1),p3(u0,v1)]
        mesh.append((q,(181,153,126)))
# Small 3D protruding wedge nose, not a painted triangle.
mesh.extend([
    ([(-.11,.20,.69),(0,.25,.95),(0,-.02,1.02),(-.12,-.07,.70)],(210,178,145)),
    ([(.11,.20,.69),(0,.25,.95),(0,-.02,1.02),(.12,-.07,.70)],(173,141,116)),
    ([(-.12,-.07,.70),(0,-.02,1.02),(.12,-.07,.70)],(145,119,100))])
# Ears are volumetric and occupy sides of the same head.
for side in (-1,1):
    for j in range(8):
        for k in range(12):
            def ep(j,k):
                v=math.pi*j/8; u=2*math.pi*k/12
                return (side*(.76+.12*math.sin(v)*math.cos(u)),.04+.22*math.cos(v),-.04+.13*math.sin(v)*math.sin(u))
            mesh.append(([ep(j,k),ep(j+1,k),ep(j+1,k+1),ep(j,k+1)],(166,134,113)))
landmarks={
 'eye_L':(-.31,.18,.60),'eye_R':(.31,.18,.60),
 'nose_root':(0,.27,.70),'nose_tip':(0,-.02,1.02),
 'ear_L':(-.83,.04,-.04),'ear_R':(.83,.04,-.04),
 'chin':(0,-1.12,0),'mouth':(0,-.39,.61),'crown':(0,1.12,0)}
def visibility(name,a):
    if name.startswith('eye_'):
        x,_,z=landmarks[name]; return rot((x/.8**2,0,z/.7**2),a)[2]>0
    if name=='ear_L': return a>18
    if name=='ear_R': return False
    return True

all_metrics=[]; exposure=[]
for f in range(24):
    a=yaw(f); ha=hair_yaw(f); gaze=12*smooth(f/4)*(1-smooth((f-7)/14))
    im=Image.new('RGB',(W,H),(18,24,32)); d=ImageDraw.Draw(im)
    d.text((28,22),'LANE 3  /  VOLUME & TIMING TEST',font=font(27),fill='#e6eff5')
    d.text((28,59),'DRAFT / HOLD  -  GENERIC MESH; C/FILM LIKENESS NOT IMPLEMENTED',font=font(17),fill='#ffbb66')
    # Fixed shoulders/neck; no zoom or planar rotation.
    d.polygon([(160,622),(203,547),(267,521),(270,470),(330,470),(335,521),(396,547),(438,622)],fill='#28323d',outline='#718294')
    d.rectangle((270,461,330,533),fill='#9f8874')
    faces=[]
    for q,col in mesh:
        r=[rot(p,a) for p in q]; z=sum(p[2] for p in r)/len(r)
        # painter render; all mesh triangles/quads are opaque
        shade=.74+.26*max(0,min(1,(z+.7)/1.7))
        faces.append((z,r,tuple(int(c*shade) for c in col)))
    # Geometric cap with fixed topology, independently delayed yaw.
    for j in range(7):
        for k in range(24):
            v0=.10+1.12*j/7; v1=.10+1.12*(j+1)/7
            u0=2*math.pi*k/24; u1=2*math.pi*(k+1)/24
            def hp(u,v): return (.87*math.sin(v)*math.cos(u),1.20*math.cos(v)+.07,.77*math.sin(v)*math.sin(u))
            r=[rot(p,ha) for p in [hp(u0,v0),hp(u1,v0),hp(u1,v1),hp(u0,v1)]]
            faces.append((sum(p[2] for p in r)/4,r,(38+(k%3)*5,45+(k%3)*5,55+(k%3)*5)))
    for i in range(7):
        x=-.65+i*.20
        q=[(x-.12,.64,.64),(x+.12,.64,.64),(x+.04,.25+(i%3)*.06,.75)]
        r=[rot(p,ha) for p in q]; faces.append((sum(p[2] for p in r)/3,r,(32+i*2,38+i*2,46+i*2)))
    for z,r,col in sorted(faces,key=lambda x:x[0]): d.polygon([project(p) for p in r],fill=col)
    # Rigid semi-open eye curves have invariant local shapes.
    for side in (-1,1):
        name='eye_L' if side<0 else 'eye_R'
        if visibility(name,a):
            eye=[(side*.31+t,.18+.018*math.sin((t+.17)/.34*math.pi),.60) for t in [i*.017-.17 for i in range(21)]]
            lower=[(x,y-.065,z) for x,y,z in eye]
            d.polygon([project(rot(p,a)) for p in eye+lower[::-1]],fill='#b2b5ac')
            d.line([project(rot(p,a)) for p in eye],fill='#172028',width=3)
            iris=project(rot((side*.31+gaze*.002,.15,.609),a)); d.ellipse((iris[0]-3,iris[1]-5,iris[0]+3,iris[1]+5),fill='#202e34')
            brow=[(side*.31+t,.29+.025*(1-abs(t)/.17),.60) for t in [-.17,0,.17]]
            d.line([project(rot(p,a)) for p in brow],fill='#262830',width=3)
    mouth=[(t,-.39,.61) for t in [-.12,0,.12]]
    d.line([project(rot(p,a)) for p in mouth],fill='#48392f',width=2)
    record={'frame':f+1,'head_yaw_deg':round(a,6),'hair_yaw_deg':round(ha,6),'gaze_lead_deg':round(gaze,6),'landmarks':{}}
    for name,p in landmarks.items():
        r=rot(p,a); xy=project(r); vis=visibility(name,a)
        record['landmarks'][name]={'local_xyz':p,'rotated_xyz':r,'screen_xy':xy,'visible_test':vis}
        if vis:
            d.ellipse((xy[0]-3,xy[1]-3,xy[0]+3,xy[1]+3),fill='#78e1da')
    all_metrics.append(record)
    d.line((563,108,563,631),fill='#354553',width=2)
    info=[('FRAME',f'{f+1:02d} / 24'),('HEAD YAW',f'{a:05.1f} deg'),('HAIR YAW',f'{ha:05.1f} deg'),('GAZE LEAD',f'{gaze:04.1f} deg'),('EXPRESSION','FIXED'),('CAMERA','LOCKED / ORTHOGRAPHIC')]
    for i,(k,v) in enumerate(info):
        y=129+i*63; d.text((592,y),k,font=font(15),fill='#8ba3b6'); d.text((592,y+22),v,font=font(21),fill='#e0ecf4')
    d.text((592,540),'C identity: NOT TESTED',font=font(19),fill='#ffbb66')
    d.text((592,570),'Clothing: NOT IMPLEMENTED',font=font(17),fill='#b0bfcc')
    d.text((28,655),'ONE 3D MESH / 24 projected samples / 0 independently generated drawings',font=font(18),fill='#95b5c9')
    d.text((28,683),'Technical motion probe only. Rigid mannequin; not finished character animation.',font=font(16),fill='#93a4b3')
    im.save(FRAMES/f'{f:03}.png')
    phase='eye lead' if f<3 else 'head acceleration' if f<12 else 'head deceleration' if f<22 else 'hair settle'
    exposure.append([f+1,f'{f/24:.6f}',f'{a:.6f}',f'{ha:.6f}',f'{gaze:.6f}',phase,'single immutable mesh projection','fixed semi-open','not C/FILM'])
with (OUT/'exposure_sheet.csv').open('w') as fp:
    w=csv.writer(fp);w.writerow(['frame','time_seconds','head_yaw_degrees','hair_yaw_degrees','gaze_lead_degrees','phase','drawing_method','expression','identity_status']);w.writerows(exposure)
(OUT/'projected_landmarks.json').write_text(json.dumps(all_metrics,indent=2))
(OUT/'model_definition.json').write_text(json.dumps({'status':'DRAFT/HOLD; GENERIC, NOT C/FILM FIT','landmarks':landmarks,'skull':'ellipsoid with tapered lower jaw; 24x48 quads','yaw':'0 to 85 degrees, quintic smoothstep frames 4-22','hair':'generic cap and 7 wedges; 2-frame delayed yaw','camera':'fixed orthographic; 152 px/unit'},indent=2))
for name,rate in [('head_turn_VOLUME_TEST_DRAFT_24fps.mp4',24),('head_turn_VOLUME_TEST_DRAFT_half_speed.mp4',12)]:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(rate),'-i',str(FRAMES/'%03d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(OUT/name)],check=True)
contact=Image.new('RGB',(960*3,720*2))
for j,f in enumerate([0,4,9,14,19,23]):
    img=Image.open(FRAMES/f'{f:03}.png'); contact.paste(img,((j%3)*960,(j//3)*720))
contact.save(OUT/'key_poses_VOLUME_TEST_DRAFT.png')
print('rendered 24 projected frames and two H.264 videos')
