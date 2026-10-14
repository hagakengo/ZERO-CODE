"""Local B-preserving 2.5D composite. Run with Python + numpy + Pillow; ffmpeg on PATH.
No generative reconstruction, external samples or network. Intermediates use --scratch.
"""
from pathlib import Path
import argparse, subprocess, math, wave, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];repo=root.parents[1]
src=repo/'reviews/aicity_style_ab_HOLD_20261014/B_HANDPAINTED_DRAFT_HOLD.png'
a.scratch.mkdir(parents=True,exist_ok=True)
W,H=1080,1920
base=Image.open(src).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
b=np.asarray(base,dtype=np.float32);y,x=np.mgrid[:H,:W].astype(np.float32)
# Exact visible left pillar only. Background behind original pillar is never revealed.
mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon([(0,0),(454,0),(388,350),(364,600),(335,930),(302,1240),(286,1440),(460,1495),(467,1620),(0,1600)],fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(.65))
fg=base.convert('RGBA');fg.putalpha(mask)
rng=np.random.default_rng(141016)
rain=rng.uniform(0,1,(490,3))
noise=np.asarray(Image.fromarray(rng.integers(0,255,(65,40),dtype=np.uint8)).resize((W,H)).filter(ImageFilter.GaussianBlur(22)),dtype=np.float32)/255
band=np.exp(-((y/H-.49)/.19)**2)*np.clip((x/W-.32)*4,0,1)*np.clip((.90-x/W)*7,0,1)
# Light modifies existing blue pixels, confined to tower band; no new lights.
light=((b[:,:,2]>b[:,:,0]*1.35)&(b[:,:,1]>100)).astype(np.float32)*np.exp(-((y/H-.294)/.018)**2)*np.exp(-((x/W-.635)/.09)**4)
def event(t):
 return -.48*math.exp(-((t-2.22)/.105)**2)+.12*math.exp(-((t-2.48)/.16)**2)-.10*max(0,min(1,(t-2.6)/.4))
for i in range(72):
 t=i/24
 # Hold mostly obscured through 0.8s, continuous reveal settles at 2s.
 u=max(0,min(1,(t-.75)/1.25));ease=u*u*(3-2*u);shift=round(190*(1-ease))
 fog=(.022+.042*np.roll(noise,round(t*19),axis=1))*band
 f=b*(1+light[:,:,None]*event(t))
 f=f*(1-fog[:,:,None])+np.array([82,108,130])*fog[:,:,None]
 ground=np.clip((y/H-.63)/.37,0,1)
 reflection=np.exp(-((x/W-.63)/.12)**2)*ground*.05*event(t-.04)
 f*=1+reflection[:,:,None]
 im=Image.fromarray(np.uint8(np.clip(f,0,255))).convert('RGBA')
 im.alpha_composite(fg,(shift,0))
 # Fill entering left edge from same dark wall, no uncovered strip.
 if shift: im.paste(base.crop((0,0,shift,H)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(0,0))
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for rx,ry,z in rain:
  xx=(rx*(W+180)-t*(35+55*z))%(W+180)-90; yy=(ry*(H+110)+t*(540+1150*z))%(H+110)-55
  d.line((xx,yy,xx-3-5*z,yy+10+35*z),fill=(156,184,209,round(16+32*z)),width=1 if z<.87 else 2)
 for k in range(24):
  q=(t*1.5+k*.337)%1;yy=H*(.67+(k%8)*.041);xx=(k*193+67)%W;r=(3+q*12)*(yy/H)**3
  d.ellipse((xx-r,yy-r*.18,xx+r,yy+r*.18),outline=(138,172,197,round((1-q)*31)))
 im=Image.alpha_composite(im,ov).convert('RGB');im.save(a.scratch/f'{i:04d}.png')
 if i%24==0:print('render',i,flush=True)
# Original deterministic stereo rain + city hum + subdued electrical dip/recovery cue.
sr=48000;n=sr*3;tt=np.arange(n)/sr;rng=np.random.default_rng(141017)
channels=[]
for ch in range(2):
 white=rng.normal(0,1,n);smooth=np.convolve(white,np.ones(7)/7,mode='same')
 low=np.convolve(white,np.ones(1600)/1600,mode='same')
 hum=.018*np.sin(2*np.pi*49*tt+ch*.13)+.009*np.sin(2*np.pi*73*tt)
 cue=.016*np.exp(-((tt-2.22)/.10)**2)*np.sin(2*np.pi*(190*tt+8*np.sin(tt*9)))
 s=.075*smooth+.28*low+hum+cue
 s*=np.minimum(1,tt/.025)*np.minimum(1,(3-tt)/.08);channels.append(s)
pcm=np.stack(channels,axis=1);wav=a.scratch/'sound.wav'
with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((pcm*32767).astype('<i2').tobytes())
video=root/'ZERO_CODE_AI_CITY_B_3S_DRAFT_HOLD.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(a.scratch/'%04d.png'),'-i',str(wav),'-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','3','-movflags','+faststart',str(video)],check=True)
(root/'audio_measurements.json').write_text(json.dumps({'peak_dbfs':float(20*np.log10(np.max(np.abs(pcm)))),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(pcm**2)))),'clipped_samples':int(np.sum(np.abs(pcm)>=1)),'sample_rate':sr,'samples_per_channel':n,'listening':'UNVERIFIED','cue_center_s':2.22,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()},indent=2))
