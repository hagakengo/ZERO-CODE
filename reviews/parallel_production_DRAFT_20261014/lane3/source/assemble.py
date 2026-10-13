from pathlib import Path
from PIL import Image,ImageDraw
import json,math,csv,subprocess
R=Path(__file__).resolve().parents[1];(R/'drawings').mkdir(exist_ok=True);(R/'frames_2D').mkdir(exist_ok=True)
sheet=Image.open(R/'drawing_sheet_DRAFT.png');w,h=sheet.size
poses=json.loads((R/'motion.json').read_text())
# Constant isotropic scale across all keys. No per-key body resizing or optical flow.
scale=2.0
rows=[]
for i in range(15):
 x0=round((i%5)*w/5);x1=round((i%5+1)*w/5);y0=round((i//5)*h/3);y1=round((i//5+1)*h/3)
 cell=sheet.crop((x0+2,y0+2,x1-2,y1-2));cell.save(R/'drawings'/f'D{i:02}.png')
 cell=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
 for j in range(2):
  frame=216+i*2+j
  # Neutral constant canvas placement: character poses change in each drawing.
  # NO foot registration: generated sheet drift must remain visible to reviewer.
  im=Image.new('RGB',(1080,1920),(187,193,201));im.paste(cell,((1080-cell.width)//2,432))
  d=ImageDraw.Draw(im);d.text((40,65),f'S04 F{frame} / C-FILM AI DRAWINGS / DRAFT-HOLD',fill=(30,35,44),font_size=24)
  d.text((40,1770),'15 DRAWINGS ON 2s / NO OPTICAL FLOW / CONTACT & IDENTITY HOLD',fill=(30,35,44),font_size=21)
  im.save(R/'frames_2D'/f'f{frame}.png')
  rows.append([frame,f'D{i:02}',i*2+216,'AI key drawing held 2 frames; no synthetic inbetweens'])
with (R/'exposure_2D.csv').open('w') as out:
 q=csv.writer(out);q.writerow(['frame','drawing','guide_reference_frame','note']);q.writerows(rows)
def run(args):subprocess.run(['ffmpeg','-y','-v','error']+args,check=True)
enc=['-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart']
run(['-framerate','24','-start_number','216','-i',str(R/'frames_2D'/'f%03d.png'),'-frames:v','30']+enc+[str(R/'video'/'S04_2D_normal.mp4')])
run(['-i',str(R/'video'/'S04_guide_normal.mp4'),'-i',str(R/'video'/'S04_2D_normal.mp4'),'-filter_complex','hstack=inputs=2']+enc+[str(R/'video'/'comparison_guide_vs_2D.mp4')])
run(['-i',str(R/'video'/'comparison_guide_vs_2D.mp4'),'-vf','setpts=2*PTS,fps=24']+enc+[str(R/'video'/'comparison_half.mp4')])
run(['-stream_loop','5','-i',str(R/'video'/'comparison_guide_vs_2D.mp4'),'-frames:v','180']+enc+[str(R/'video'/'comparison_6loops.mp4')])
