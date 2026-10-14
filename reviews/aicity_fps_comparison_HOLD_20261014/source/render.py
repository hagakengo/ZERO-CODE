"""Local B-preserving continuous-time whole-painting camera experiment. Run with Python + numpy + Pillow; ffmpeg on PATH.
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
rng=np.random.default_rng(141016)
rain=rng.uniform(0,1,(490,3))
noise=np.asarray(Image.fromarray(rng.integers(0,255,(65,40),dtype=np.uint8)).resize((W,H)).filter(ImageFilter.GaussianBlur(22)),dtype=np.float32)/255
band=np.exp(-((y/H-.49)/.19)**2)*np.clip((x/W-.32)*4,0,1)*np.clip((.90-x/W)*7,0,1)
# Light modifies existing blue pixels, confined to tower band; no new lights.
light=((b[:,:,2]>b[:,:,0]*1.35)&(b[:,:,1]>100)).astype(np.float32)*np.exp(-((y/H-.294)/.018)**2)*np.exp(-((x/W-.635)/.09)**4)
def event(t):
 return -.48*math.exp(-((t-2.22)/.105)**2)+.12*math.exp(-((t-2.48)/.16)**2)-.10*max(0,min(1,(t-2.6)/.4))
def render(t):
 # Single painting: pillar, beam and city share one transform. No masks,
 # reconstructed hidden pixels, edge extension, or independently sliding architecture.
 fogfield=Image.fromarray(np.uint8(noise*255)).transform((W,H),Image.Transform.AFFINE,(1,0,t*19,0,1,0),Image.Resampling.BICUBIC)
 fog=(.022+.042*np.asarray(fogfield,dtype=np.float32)/255)*band
 f=b*(1+light[:,:,None]*event(t))
 f=f*(1-fog[:,:,None])+np.array([82,108,130])*fog[:,:,None]
 ground=np.clip((y/H-.63)/.37,0,1)
 reflection=np.exp(-((x/W-.63)/.12)**2)*ground*.05*event(t-.04)
 f*=1+reflection[:,:,None]
 im=Image.fromarray(np.uint8(np.clip(f,0,255))).convert('RGBA')
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for rx,ry,z in rain:
  xx=(rx*(W+180)-t*(35+55*z))%(W+180)-90; yy=(ry*(H+110)+t*(540+1150*z))%(H+110)-55
  d.line((xx,yy,xx-3-5*z,yy+10+35*z),fill=(156,184,209,round(16+32*z)),width=1 if z<.87 else 2)
 for k in range(24):
  q=(t*1.5+k*.337)%1;yy=H*(.67+(k%8)*.041);xx=(k*193+67)%W;r=(3+q*12)*(yy/H)**3
  d.ellipse((xx-r,yy-r*.18,xx+r,yy+r*.18),outline=(138,172,197,round((1-q)*31)))
 im=Image.alpha_composite(im,ov).convert('RGB')
 # Continuous slow push, overscan always inside original painting.
 scale=1.025+.025*(t/3); inv=1/scale
 cx=W*.60;cy=H*.48
 return im.transform((W,H),Image.Transform.AFFINE,(inv,0,cx*(1-inv),0,inv,cy*(1-inv)),Image.Resampling.BICUBIC)
for fps in (24,60):
 folder=a.scratch/str(fps);folder.mkdir(exist_ok=True)
 hashes=[]
 for i in range(3*fps):
  im=render(i/fps); hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
  im.save(folder/f'{i:04d}.png')
  if i in (0,fps,2*fps): im.save(root/f'frame_{fps}_{i//fps}s.png')
  if i%fps==0:print('render',fps,i,flush=True)
 (root/f'frame_hashes_{fps}.json').write_text(json.dumps(hashes,indent=2))
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
for fps in (24,60):
 video=root/f'AI_CITY_{fps}fps_DRAFT_HOLD.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-framerate',str(fps),'-i',str(a.scratch/str(fps)/'%04d.png'),'-i',str(wav),'-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','3','-movflags','+faststart',str(video)],check=True)
(root/'audio_measurements.json').write_text(json.dumps({'peak_dbfs':float(20*np.log10(np.max(np.abs(pcm)))),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(pcm**2)))),'clipped_samples':int(np.sum(np.abs(pcm)>=1)),'sample_rate':sr,'samples_per_channel':n,'listening':'UNVERIFIED','cue_center_s':2.22,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()},indent=2))
