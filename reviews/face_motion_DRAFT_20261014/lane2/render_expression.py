from PIL import Image,ImageDraw,ImageFont
import numpy as np, csv, json, pathlib, shutil, subprocess
P=pathlib.Path(__file__).parent
base=Image.open(P/'source/source_front_crop.png').convert('RGB')
a=np.asarray(base); h,w=a.shape[:2]; Y,X=np.mgrid[:h,:w].astype(float)
def smooth(t): return np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
def g(x,y,sx,sy): return np.exp(-((X-x)/sx)**4-((Y-y)/sy)**4)
rows=[]; frames=[]
for f in range(24):
    smile=float(smooth((f-3)/7)*(1-smooth((f-15)/5)))
    notice=float(smooth((f-15)/7))
    blink=float(max(0,1-abs(f-7)/2))
    dx=np.zeros_like(X); dy=np.zeros_like(Y)
    # Every output samples this SAME source; no independently drawn/generated frames.
    # Continuous mouth-corner and cheek displacement; no moving head/camera.
    for cx,cy in [(246,155),(275,149)]: dy+=4.0*smile*g(cx,cy,10,8)
    for cx,cy in [(233,140),(292,133)]: dy+=0.8*smile*g(cx,cy,16,10)
    for cx,cy in [(211,109),(279,89)]:
        # Local eye compression is only a proxy for a proper eyelid drawing.
        mask=g(cx,cy,16,7)
        dy+=(Y-cy)*blink*1.65*mask
        dx-=1.4*notice*g(cx,cy,7,5)
    for cx,cy in [(213,91),(277,75)]: dy+=1.4*notice*g(cx,cy,16,3)
    xx=np.clip(X+dx,0,w-1); yy=np.clip(Y+dy,0,h-1)
    x0=xx.astype(int); y0=yy.astype(int); x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1)
    fx=(xx-x0)[...,None];fy=(yy-y0)[...,None]
    pix=(a[y0,x0]*(1-fx)*(1-fy)+a[y0,x1]*fx*(1-fy)+a[y1,x0]*(1-fx)*fy+a[y1,x1]*fx*fy).astype('uint8')
    im=Image.fromarray(pix).resize((998,590),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(1024,680),(25,27,30));canvas.paste(im,(13,45))
    d=ImageDraw.Draw(canvas);d.text((16,12),'LANE 2 / FIXED SOURCE FACE / DRAFT-HOLD',fill='white')
    d.text((16,647),f'f{f+1:02d}/24 | half-lid > slight smile > notice | local warp test',fill='white')
    (P/'frames').mkdir(exist_ok=True); canvas.save(P/'frames'/f'frame_{f:03d}.png'); frames.append(canvas)
    rows.append(dict(frame=f+1,time_s=round(f/24,6),smile=round(smile,4),blink_proxy=round(blink,4),notice=round(notice,4),source='ONE fixed FRONT crop',exposure=1))
with open(P/'exposure.csv','w') as out:
    c=csv.DictWriter(out,fieldnames=rows[0].keys()); c.writeheader();c.writerows(rows)
for f in [0,7,11,15,23]:frames[f].save(P/'keys'/f'key_f{f+1:02d}.png')
contact=Image.new('RGB',(1024*3,680*2),(20,20,20))
for n,f in enumerate([0,5,7,11,17,23]):contact.paste(frames[f],((n%3)*1024,(n//3)*680))
contact.resize((1536,680)).save(P/'expression_comparison_DRAFT.png')
for half,name in [(False,'expression_DRAFT_24fps.mp4'),(True,'expression_DRAFT_half_speed.mp4')]:
    cmd=['ffmpeg','-y','-loglevel','error','-framerate','12' if half else '24','-i',str(P/'frames/frame_%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(P/name)]
    subprocess.run(cmd,check=True)
