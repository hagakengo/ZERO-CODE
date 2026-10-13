"""Reproducible 2D motion-design draft. Run with Python/Pillow and ffmpeg/ffprobe on PATH."""
from pathlib import Path
import json, copy, math, subprocess, hashlib, zipfile, shutil
from PIL import Image, ImageDraw, ImageFont
import baseline as b
OUT=Path(__file__).resolve().parents[1]
REPO=OUT.parents[1]
OLD=REPO/'reviews/counterattack_design_01'
DATA=json.loads((Path(__file__).parent/'baseline_poses.json').read_text())
old=DATA['displayed_poses']
b.base=copy.deepcopy(old[0])
font='/System/Library/Fonts/Helvetica.ttc'
b.font=ImageFont.truetype(font,25);b.small=ImageFont.truetype(font,21)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(REPO)):sha(p) for p in REPO.rglob('*') if p.is_file() and '.git' not in p.parts and OUT not in p.parents}
external=Path('/Users/hagakengo/Movies/ZERO_CODE/review_for_chatgpt/production_r15_2')
ext_before={str(p.relative_to(external)):sha(p) for p in external.rglob('*') if p.is_file()} if external.exists() else {}
L=b.lerp

def pose(t):
    if t<16:
        p=copy.deepcopy(old[t]);p['version']='02';p['indent']=0;return p
    p=copy.deepcopy(old[t]);p['version']='02';p['proposal_frame']=t
    indent=L([(16,0),(24,0),(25,12),(27,9),(30,2),(35,0),(71,0)],t)
    p['indent']=indent
    for who in ['hero','enemy']:
        q=p[who];j=q['joints'];face=q['facing']
        if who=='hero':
            hx=L([(16,264),(24,264),(26,264),(29,253),(35,215),(40,160),(50,160),(54,177),(60,211),(71,220)],t)
            hy=L([(16,548),(24,548),(25,552),(28,557),(35,566),(40,568),(48,566),(50,570),(51,577),(54,570),(60,552),(71,550)],t)
            sx=L([(16,264),(24,264),(25,268),(26,268),(29,247),(35,197),(40,148),(50,154),(54,174),(60,211),(71,220)],t)
            sy=L([(16,436),(24,436),(25,436),(26,438),(29,446),(35,454),(40,456),(48,454),(50,458),(51,465),(54,458),(60,440),(71,438)],t)
            headx=L([(16,264),(26,264),(28,268),(31,235),(35,190),(40,148),(50,154),(54,174),(60,211),(71,220)],t)
            feet={'R':b.shoe([160,728],face),'L':b.shoe(b.step(t,41,50,304,240,8),face)}
        else:
            hx=L([(16,450),(20,385),(23,347),(24,340),(27,340),(35,355),(48,382),(71,382)],t)
            hy=L([(16,560),(24,552),(30,554),(48,555),(71,552)],t)
            sx=hx+L([(16,2),(24,-14),(27,-14),(35,-8),(48,-4),(71,-4)],t);sy=hy-112;headx=sx
            feet={'L':b.shoe([472,728],face),'R':b.shoe([330,728],face)}
        h=[hx,hy];s=[sx,sy];j['hip']=h;j['shoulder']=s;j['head']=[headx,sy-35]
        for side,v in feet.items():
            a=[hx+(4 if side=='L' else -4),hy];j[side+'_hip']=a;j[side+'_ankle']=v['ankle'];j[side+'_knee']=b.ik(a,v['ankle'],face)
        q['shoes']=feet;q['feet']={k:v['ankle'] for k,v in feet.items()}
        j['guard']=[sx+face*24,sy+4];j['guard_elbow']=b.arm(s,j['guard'],-face)
        j['fist']=[sx+face*35,sy+30];j['elbow']=b.arm([sx+face*7,sy+8],j['fist'],-face)
    j=p['enemy']['joints'];s=j['shoulder'];h=p['hero']['joints']['hip']
    # Absolute path: increasing per-frame travel until P024, then 3-frame dwell.
    x=L([(16,464),(20,410),(21,386),(22,357),(23,324),(24,289),(25,277),(26,277),(27,278),(28,296),(31,321),(40,340),(71,343)],t)
    y=L([(16,470),(20,486),(23,501),(24,503),(25,507),(27,511),(31,486),(40,481),(71,480)],t)
    j['fist']=[x,y];j['elbow']=b.arm([s[0]-7,s[1]+8],j['fist'],1)
    for who in ['hero','enemy']:
        q=p[who];q['contacts']=[k for k,v in q['shoes'].items() if abs(v['heel'][1]-734)<1e-6]
        q['com_x']=b.mass_proxy(q)
        pts=[v[k][0] for v in q['shoes'].values() for k in ['heel','toe'] if abs(v[k][1]-734)<1e-6]
        q['support_interval']=[min(pts),max(pts)];q['proxy_inside']=min(pts)<=q['com_x']<=max(pts)
    p['phase']=b.phase(t)
    return p

# Same camera and renderer. The single torso edit makes local abdominal compression visible.
import inspect
render_source=inspect.getsource(b.render)
render_source=render_source.replace("d.polygon([pt(x) for x in [[s[0]-20,s[1]],[s[0]+20,s[1]],[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]]],fill=c)","d.polygon([pt(x) for x in [[s[0]-20,s[1]],[s[0]+20,s[1]],[h[0]+20-p.get('indent',0) if who=='hero' else h[0]+20,h[1]-45],[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]]],fill=c)")
render_source=render_source.replace("DESIGN / P{t:03}","DESIGN {p.get('version','01')} / P{t:03}")
render_source=render_source.replace("('1-frame' if 20<=t<=29 else '2-frame')","('1-frame' if p.get('version')=='02' and 16<=t<=55 else ('1-frame' if 20<=t<=29 else '2-frame'))")
ns=dict(b.__dict__);exec(render_source,ns);render=ns['render']
poses=[pose(t) for t in range(72)]
for name in ['frames','comparison','video','verification']:(OUT/name).mkdir(exist_ok=True)
for t,p in enumerate(poses):render(p).save(OUT/'frames'/f'P{t:03}.png')
ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
subprocess.run([ffmpeg,'-v','error','-y','-framerate','24','-i',str(OUT/'frames/P%03d.png'),'-frames:v','72','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-profile:v','high','-level:v','4.0','-movflags','+faststart',str(OUT/'video/counterattack_design_02_24fps.mp4')],check=True)
# Comparison decodes the actual submitted 01 MP4, rather than substituting its pose data.
TMP=OUT/'comparison'/'decoded_01';TMP.mkdir(exist_ok=True)
subprocess.run([ffmpeg,'-v','error','-y','-i',str(OLD/'video/counterattack_retreat_design_24fps.mp4'),'-start_number','0',str(TMP/'P%03d.png')],check=True)
KEYS=[20,23,24,25,26,28,31,35,40,42,44,46,48,50,51,55]
for t in KEYS:
    im=Image.new('RGB',(2160,1920),'white');im.paste(Image.open(TMP/f'P{t:03}.png'),(0,0));im.paste(Image.open(OUT/'frames'/f'P{t:03}.png'),(1080,0))
    d=ImageDraw.Draw(im);d.text((55,190),f'01 HOLD / P{t:03}',font=b.font,fill='black');d.text((1135,190),f'02 DRAFT / P{t:03}',font=b.font,fill='black')
    im.save(OUT/'comparison'/f'01_vs_02_P{t:03}.png')
subprocess.run([ffmpeg,'-v','error','-y','-i',str(OLD/'video/counterattack_retreat_design_24fps.mp4'),'-i',str(OUT/'video/counterattack_design_02_24fps.mp4'),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-frames:v','72','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-level:v','5.0','-movflags','+faststart',str(OUT/'comparison/01_vs_02_24fps.mp4')],check=True)
shutil.rmtree(TMP)
sheet=Image.new('RGB',(2160,2200),'white');d=ImageDraw.Draw(sheet)
for i,t in enumerate(KEYS):
    thumb=Image.open(OUT/'frames'/f'P{t:03}.png').crop((190,720,1030,1550)).resize((540,500));x=i%4*540;y=i//4*550
    sheet.paste(thumb,(x,y+40));d.text((x+10,y+8),f'02 DRAFT / P{t:03}',font=b.small,fill='black')
sheet.save(OUT/'design_keyposes_02.png')
(OUT/'verification/motion_design_02.json').write_text(json.dumps({'displayed_poses':poses},indent=2))
checks={'date':'2026-10-13 JST','status':'DRAFT / 監督レビュー待ち','camera':'same 1080x1920, coordinates x2, ground y1468; no camera transform','videos':{},'protected_repository_files_unchanged':all(sha(REPO/k)==v for k,v in protected.items()),'protected_external_r15_2_unchanged':all(sha(external/k)==v for k,v in ext_before.items()),'external_r15_2_file_count':len(ext_before),'browser_playback':'未検証','director_verdict':'PENDING','mass_proxy_flags':[]}
for video in [OUT/'video/counterattack_design_02_24fps.mp4',OUT/'comparison/01_vs_02_24fps.mp4']:
    probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]));subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
    st=probe['streams'][0];assert st['nb_read_frames']=='72' and st['avg_frame_rate']=='24/1' and float(probe['format']['duration'])==3 and st['codec_name']=='h264'
    checks['videos'][str(video.relative_to(OUT))]={'probe':probe,'full_decode':'PASS','sha256':sha(video),'bytes':video.stat().st_size}
maxerr=0;slip=0;reverse=[]
for t,p in enumerate(poses):
    for who in ['hero','enemy']:
        q=p[who];j=q['joints']
        if not q['proxy_inside']:checks['mass_proxy_flags'].append([t,who])
        for side in ['L','R']:
            a,k,f=[j[side+n] for n in ['_hip','_knee','_ankle']]
            maxerr=max(maxerr,abs(math.dist(a,k)-112)*2,abs(math.dist(k,f)-110)*2)
            if ((k[0]-a[0])*(f[1]-a[1])-(k[1]-a[1])*(f[0]-a[0]))*q['facing']<=0:reverse.append([t,who,side])
            if t:
                for tag in ['heel','toe']:
                    prev=poses[t-1][who]['shoes'][side][tag];now=q['shoes'][side][tag]
                    if abs(prev[1]-734)<1e-6 and abs(now[1]-734)<1e-6:slip=max(slip,2*math.dist(prev,now))
checks.update(bone_length_max_error_px=maxerr,planted_point_max_slip_px=slip,knee_reversals=reverse,front_foot_max_lift_px_P042_050=max((728-poses[t]['hero']['shoes']['L']['ankle'][1])*2 for t in range(42,51)),contact_sequence={str(t):{'fist':poses[t]['enemy']['joints']['fist'],'hip':poses[t]['hero']['joints']['hip'],'indent_px':poses[t]['indent']*2} for t in [23,24,25]},attack_travel_px_P020_024=[2*math.dist(poses[t]['enemy']['joints']['fist'],poses[t-1]['enemy']['joints']['fist']) for t in range(20,25)])
(OUT/'verification/submission_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in checks.items() if k!='videos'},ensure_ascii=False,indent=2))
