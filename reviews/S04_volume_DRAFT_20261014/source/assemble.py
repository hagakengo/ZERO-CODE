from pathlib import Path
from PIL import Image,ImageDraw
import json,math,csv,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
for d in ['drawings','frames_2d','video']: (R/d).mkdir(exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return [v/math.sqrt(dot(a,a)) for v in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
cam=(3.6,2.7,6.8);fw=norm(sub((.5,.9,0),cam));right=norm(cross(fw,(0,1,0)));up=cross(right,fw)
def pr(a):
 q=sub(a,cam);z=dot(q,fw);return [540+3000*dot(q,right)/z,1060-3000*dot(q,up)/z]
# Manually identified shoe sole centers in source sheet pixel coordinates, cell-local.
# These are approximate 2D registration landmarks, NOT measured anatomical joint coordinates.
L=[(69,337),(75,339),(89,338),(108,334),(106,329),(65,327),(100,309),(120,305),(121,303),(128,302),(113,291),(125,303),(168,313),(190,323),(178,318)]
Q=[(169,337),(170,339),(216,332),(218,316),(208,296),(185,313),(200,302),(213,326),(191,342),(183,349),(154,310),(165,313),(181,311),(206,314),(193,310)]
sheet=Image.open(R/'drawing_sheet_DRAFT.png').convert('RGB');poses=json.loads((R/'motion.json').read_text());scale=2.447368421;rows=[]
for i in range(15):
 x0=round(i%5*sheet.width/5);x1=round((i%5+1)*sheet.width/5);y0=round(i//5*sheet.height/3);y1=round((i//5+1)*sheet.height/3)
 cell=sheet.crop((x0,y0,x1,y1));cell.save(R/'drawings'/f'D{i+1:02}.png');pose=poses[2*i]
 if i<=5:anchor=L[i];target=pr(pose['left_foot']);mode='left support'
 elif i<=7:anchor=((L[i][0]+Q[i][0])/2,(L[i][1]+Q[i][1])/2);a,b=pr(pose['left_foot']),pr(pose['right_foot']);target=[(a[j]+b[j])/2 for j in range(2)];mode='airborne midpoint'
 else:anchor=Q[i];target=pr(pose['right_foot']);mode='right support'
 dx=round(target[0]-scale*anchor[0]);dy=round(target[1]-scale*anchor[1]);cell=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
 im=Image.new('RGB',(1080,1920),(177,188,197));im.paste(cell,(dx,dy));d=ImageDraw.Draw(im)
 d.text((60,70),'S04  |  GUIDE-REFERENCED 2D  DRAFT / HOLD',fill=(30,35,44),font_size=27)
 d.text((60,1700),'AI CLEANUP + SUPPORT-FOOT REGISTRATION',fill=(30,35,44),font_size=24)
 d.text((60,1750),'15 DRAWINGS / 2-FRAME EXPOSURE / FIXED SCALE',fill=(30,35,44),font_size=24)
 # Contact markers: registered support datum. The second sole can disagree with its guide.
 for side,src in [('left',L[i]),('right',Q[i])]:
  t=pr(pose[side+'_foot']);actual=(dx+scale*src[0],dy+scale*src[1]);error=math.dist(t,actual)
  rows.append({'drawing':i+1,'frame':216+2*i,'side':side,'contact':pose[side+'_contact'],'guide_x':t[0],'guide_y':t[1],'registered_x':actual[0],'registered_y':actual[1],'residual_px':error,'registration':mode,'translation_x':dx,'translation_y':dy,'fixed_scale':scale})
 for offset in [0,1]:im.save(R/'frames_2d'/f'f{216+2*i+offset}.png')
with (R/'registration_audit.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
run(['ffmpeg','-y','-v','error','-framerate','24','-start_number','216','-i',str(R/'frames_2d/f%03d.png'),'-frames:v','30','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'video/S04_2D_normal.mp4')])
for mode in ['guide','2D']:
 run(['ffmpeg','-y','-v','error','-i',str(R/f'video/S04_{mode}_normal.mp4'),'-vf','setpts=2*PTS,tpad=stop_mode=clone:stop_duration=0.083333','-r','24','-frames:v','60','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/f'video/S04_{mode}_half.mp4')])
old=R/'reference_4dc7ecd.mp4'
if old.exists():
 run(['ffmpeg','-y','-v','error','-i',str(old),'-i',str(R/'video/S04_guide_normal.mp4'),'-i',str(R/'video/S04_2D_normal.mp4'),'-filter_complex','[0:v]scale=360:640[a];[1:v]scale=360:640[b];[2:v]scale=360:640[c];[a][b][c]hstack=inputs=3[v]','-map','[v]','-frames:v','30','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(R/'video/comparison_old_guide_2D.mp4')])
 run(['ffmpeg','-y','-v','error','-stream_loop','5','-i',str(R/'video/comparison_old_guide_2D.mp4'),'-c','copy','-movflags','+faststart',str(R/'video/comparison_6loops.mp4')])
 run(['ffmpeg','-y','-v','error','-i',str(R/'video/comparison_old_guide_2D.mp4'),'-vf','setpts=2*PTS,tpad=stop_mode=clone:stop_duration=0.083333','-r','24','-frames:v','60','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(R/'video/comparison_half.mp4')])

for name,left,leftlabel in [('comparison_old_vs_2D',old,'OLD 4dc7ecd'),('comparison_guide_vs_2D',R/'video/S04_guide_normal.mp4','3D GUIDE')]:
 if not left.exists():continue
 filt="[0:v]scale=540:960[a];[1:v]scale=540:960[b];[a][b]hstack=inputs=2,drawtext=text='"+leftlabel+"':x=24:y=115:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7,drawtext=text='NEW 2D DRAFT':x=564:y=115:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7[v]"
 run(['ffmpeg','-y','-v','error','-i',str(left),'-i',str(R/'video/S04_2D_normal.mp4'),'-filter_complex',filt,'-map','[v]','-frames:v','30','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(R/'video'/f'{name}.mp4')])
 run(['ffmpeg','-y','-v','error','-stream_loop','5','-i',str(R/'video'/f'{name}.mp4'),'-c','copy','-movflags','+faststart',str(R/'video'/f'{name}_6loops.mp4')])

report={}
for file in (R/'video').glob('*.mp4'):
 p=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(file)]));v=p['streams'][0];run(['ffmpeg','-v','error','-i',str(file),'-f','null','-']);report[file.name]={k:v.get(k) for k in ['width','height','r_frame_rate','nb_read_frames','duration','pix_fmt']};report[file.name]['full_decode']='PASS'
for name in ['S04_guide_normal.mp4','S04_2D_normal.mp4']:
 v=report[name];assert (v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==(1080,1920,'30','24/1')
(R/'technical_validation.json').write_text(json.dumps(report,indent=2))
contact=[q['residual_px'] for q in rows if q['contact']]
(R/'registration_summary.json').write_text(json.dumps({'max_contact_sole_landmark_residual_px':max(contact),'mean_contact_sole_landmark_residual_px':sum(contact)/len(contact),'warning':'Approximate manual landmarks, held 2 frames. Both soles not solved simultaneously. Not a motion quality PASS.'},indent=2))
print(json.dumps(report));print('contact residual max',max(contact))
