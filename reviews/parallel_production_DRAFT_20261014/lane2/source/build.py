from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
import csv,subprocess,json,hashlib
p=Path('outputs/lane2'); (p/'drawings').mkdir(exist_ok=True); (p/'frames').mkdir(exist_ok=True)
im=Image.open(p/'source/generated_sequence.png').convert('RGB')
w,h=im.size
holds=[6,4,4,4,4,6,6,8,4,6,6,14]
frames=[]; frame=1
for i,hold in enumerate(holds):
 x=i%4; y=i//4
 cell=im.crop((round(x*w/4),round(y*h/3),round((x+1)*w/4),round((y+1)*h/3)))
 cell.save(p/f'drawings/K{i+1:02d}.png')
 canvas=Image.new('RGB',(1080,1920),(25,29,35)); fit=ImageOps.contain(cell,(1080,1460));canvas.paste(fit,((1080-fit.width)//2,(1920-fit.height)//2))
 d=ImageDraw.Draw(canvas); d.text((35,45),'ZERO CODE / DAILY ACTING / DRAFT HOLD',fill='white');d.text((35,1830),'12 POSES / LIMITED ANIMATION TEST / NOT FINAL',fill='white')
 for j in range(hold):
  canvas.save(p/f'frames/F{frame:03d}.png');frames.append([frame,i+1,hold]);frame+=1
with open(p/'exposure.csv','w') as f:
 wr=csv.writer(f);wr.writerow(['frame_1_based','drawing','drawing_total_hold_frames']);wr.writerows(frames)
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(p/'frames/F%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(p/'daily_acting_DRAFT_24fps.mp4')],check=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(p/'daily_acting_DRAFT_24fps.mp4'),'-filter:v','setpts=2*PTS,tpad=stop_mode=clone:stop_duration=0.1,fps=24,trim=end_frame=144','-r','24','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(p/'daily_acting_DRAFT_half_speed.mp4')],check=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(p/'daily_acting_DRAFT_24fps.mp4'),'-i',str(p/'daily_acting_DRAFT_half_speed.mp4'),'-filter_complex','[0:v]scale=540:960,tpad=stop_mode=clone:stop_duration=3[a];[1:v]scale=540:960[b];[a][b]hstack=inputs=2[v]','-map','[v]','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(p/'daily_normal_vs_half_DRAFT.mp4')],check=True)
for name in ['daily_acting_DRAFT_24fps.mp4','daily_acting_DRAFT_half_speed.mp4','daily_normal_vs_half_DRAFT.mp4']:
 r=subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p/name)])
 (p/(name+'.probe.json')).write_bytes(r)
 subprocess.run(['ffmpeg','-v','error','-i',str(p/name),'-f','null','-'],check=True)
(p/'SHA256.json').write_text(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and f.name!='SHA256.json'},indent=2))
print('complete',im.size,'frames',len(frames))
