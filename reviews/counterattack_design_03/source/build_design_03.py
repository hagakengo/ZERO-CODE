from pathlib import Path
import json,copy,math,subprocess,shutil,hashlib,zipfile
from PIL import Image,ImageDraw,ImageFont
import baseline as b
O=Path(__file__).resolve().parents[1]; R=O.parents[1]; A=R/'reviews/counterattack_design_02'
poses=json.loads((A/'verification/motion_design_02.json').read_text())['displayed_poses']
b.font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',25); b.small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',21)
L=b.lerp
for t,p in enumerate(poses):
 p['version']='03';p['indent']=0
 if 23<=t<=39:
  j=p['hero']['joints']; h=j['hip'];s=j['shoulder']
  # Local abdomen moves first; chest, head, pelvis start at distinct frames.
  hx=L([(23,264),(28,264),(31,248),(35,215),(39,163)],t)
  sx=L([(23,264),(26,264),(28,256),(31,226),(35,197),(39,153)],t)
  headx=L([(23,264),(28,264),(30,258),(33,218),(35,190),(39,153)],t)
  h[0]=hx;s[0]=sx;j['head'][0]=headx
  p['indent']=L([(23,0),(24,0),(25,17),(26,19),(28,12),(31,5),(35,0),(39,0)],t)
  for side in ['L','R']:
   j[side+'_hip']=[hx+(4 if side=='L' else -4),h[1]]
   j[side+'_knee']=b.ik(j[side+'_hip'],j[side+'_ankle'],1)
  j['guard']=[sx+24,s[1]+4];j['guard_elbow']=b.arm(s,j['guard'],-1)
  j['fist']=[sx+35,s[1]+30];j['elbow']=b.arm([sx+7,s[1]+8],j['fist'],-1)
  p['hero']['com_x']=b.mass_proxy(p['hero'])
  # Visible fist left edge equals the local abdominal contour on P024/P025.
  ej=p['enemy']['joints'];y=h[1]-45
  x=L([(23,307),(24,289.5),(25,272.5),(26,270.5),(28,280),(31,321),(39,340)],t)
  ej['fist']=[x,y];ej['elbow']=b.arm([ej['shoulder'][0]-7,ej['shoulder'][1]+8],ej['fist'],1)
  p['enemy']['com_x']=b.mass_proxy(p['enemy'])
 # Bag follows delayed torso orientation, returns smoothly to original by P040.
 lag=max(0,t-3)
 p['bag_angle']=0
 if 26<=t<=39:
  now=poses[t]['hero']['joints']; prev=poses[lag]['hero']['joints']
  p['bag_angle']=(math.atan2(prev['shoulder'][0]-prev['hip'][0],prev['hip'][1]-prev['shoulder'][1])-math.atan2(now['shoulder'][0]-now['hip'][0],now['hip'][1]-now['shoulder'][1]))*min(1,(40-t)/3)
import inspect
src=inspect.getsource(b.render)
src=src.replace("up=[dx/l,dy/l];back=[dy/l,-dx/l]", "angle=p.get('bag_angle',0); dx,dy=dx*math.cos(angle)-dy*math.sin(angle),dx*math.sin(angle)+dy*math.cos(angle); up=[dx/l,dy/l];back=[dy/l,-dx/l]")
src=src.replace("[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]", "[h[0]+20-p.get('indent',0) if who=='hero' else h[0]+20,h[1]-45],[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]")
# Draw contact arm in front of torso with a dark non-glowing silhouette edge.
needle="    t=p['proposal_frame']"
insert="""    if 22<=p['proposal_frame']<=31:
        j=p['enemy']['joints'];a=j['elbow'];f=j['fist']
        line(a,f,(75,82,85),9);line(a,f,(158,167,169),7)
        x,y=pt(f);d.rectangle([x-11,y-11,x+11,y+11],fill=(158,167,169),outline=(70,77,80),width=2)
    t=p['proposal_frame']"""
src=src.replace(needle,insert).replace('COUNTERATTACK DESIGN /','COUNTERATTACK DESIGN 03 /')
ns=dict(b.__dict__);exec(src,ns);render=ns['render']
for n in ['frames','comparison','video','verification']:(O/n).mkdir(exist_ok=True)
for t,p in enumerate(poses):render(p).save(O/'frames'/f'P{t:03}.png')
f=shutil.which('ffmpeg');probe=shutil.which('ffprobe')
def run(args):subprocess.run([f,'-v','error','-y']+args,check=True)
v=O/'video/counterattack_design_03_24fps.mp4';cv=O/'comparison/02_vs_03_24fps.mp4'
run(['-framerate','24','-start_number','0','-i',str(O/'frames/P%03d.png'),'-frames:v','72','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(v)])
run(['-i',str(A/'video/counterattack_design_02_24fps.mp4'),'-i',str(v),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-frames:v','72','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(cv)])
dec=O/'verification/decoded02';dec.mkdir(exist_ok=True)
run(['-i',str(A/'video/counterattack_design_02_24fps.mp4'),'-start_number','0',str(dec/'P%03d.png')])
keys=[23,24,25,26,28,31,35,46,50,51]
sheet=Image.new('RGB',(2160,2750),'white')
for i,t in enumerate(keys):
 im=Image.new('RGB',(2160,1920));im.paste(Image.open(dec/f'P{t:03}.png'),(0,0));im.paste(Image.open(O/'frames'/f'P{t:03}.png'),(1080,0));d=ImageDraw.Draw(im);d.text((55,190),'02 HOLD',font=b.font,fill='black');d.text((1135,190),'03 DRAFT',font=b.font,fill='black');im.save(O/'comparison'/f'02_vs_03_P{t:03}.png')
 thumb=Image.open(O/'frames'/f'P{t:03}.png').crop((180,700,1040,1520)).resize((540,500));x=i%4*540;y=i//4*550;sheet.paste(thumb,(x,y+40));ImageDraw.Draw(sheet).text((x+10,y+8),f'03 DRAFT P{t:03}',font=b.small,fill='black')
sheet.crop((0,0,2160,1650)).save(O/'design_keyposes_03.png');shutil.rmtree(dec)
allim=Image.new('RGB',(2160,2880),'white')
for t in range(72):allim.paste(Image.open(O/'frames'/f'P{t:03}.png').resize((270,320)),(t%8*270,t//8*320))
allim.save(O/'verification/all_72_frames.png')
checks={'status':'DRAFT / 監督レビュー待ち','director_verdict':'PENDING','normal_speed_playback':'PENDING','videos':{},'adopted_poses_P042_051_unchanged':all(poses[t]['hero']==json.loads((A/'verification/motion_design_02.json').read_text())['displayed_poses'][t]['hero'] for t in range(42,52))}
for path in [v,cv]:
 q=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]));s=q['streams'][0];assert s['nb_read_frames']=='72' and s['avg_frame_rate']=='24/1' and s['codec_name']=='h264' and float(q['format']['duration'])==3
 run(['-xerror','-i',str(path),'-f','null','-']);checks['videos'][str(path.relative_to(O))]=q
(O/'verification/submission_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
(O/'source/poses03.json').write_text(json.dumps(poses,indent=2))
print('Rendered and decoded both 72-frame videos. Adopted poses preserved:',checks['adopted_poses_P042_051_unchanged'])
