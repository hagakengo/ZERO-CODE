from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, math, subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs' if (ROOT/'outputs').exists() else ROOT
(ROOT/'work/frames').mkdir(parents=True,exist_ok=True)
W,H=1080,1920
base=np.asarray(Image.open(OUT/'AI_CITY_ART_DRAFT.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)).astype(np.float32)
y,x=np.mgrid[0:H,0:W].astype(np.float32)
# Continuous proxy depth, not recovered 3D. Conservative displacement avoids exposed holes.
side=np.clip((np.abs(x-W*.5)/W-.15)/.30,0,1)
ground=np.clip((y/H-.85)/.15,0,1)
depth=.12+.65*side+.23*ground
rng=np.random.default_rng(10214)
rain=[(rng.uniform(-150,W+150),rng.uniform(0,H),rng.uniform(0,1)) for _ in range(630)]
noise=Image.fromarray(rng.integers(0,255,(90,60),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(24))
fog=np.asarray(noise).astype(np.float32)/255
light=(base[:,:,1]>base[:,:,0]*1.12)&(base[:,:,1]>85)
for i in range(72):
 t=i/24; u=t/3
 sx=np.clip(x+((u-.5)*13)*depth,0,W-1.001)
 sy=np.clip(y+((u-.5)*2)*depth,0,H-1.001)
 ix=sx.astype(int); iy=sy.astype(int);fx=(sx-ix)[...,None];fy=(sy-iy)[...,None]
 a=base[iy,ix]*(1-fx)+base[iy,ix+1]*fx
 b=base[iy+1,ix]*(1-fx)+base[iy+1,ix+1]*fx
 frame=a*(1-fy)+b*fy
 # Traveling cloud shadow is a broad illumination change, no event or blackout.
 shadow=1-.035*np.exp(-((x/W-.25-u*.5)/.28)**2)
 frame*=shadow[...,None]
 frame+=light[...,None]*np.array([1.2,3.0,3.3])*math.sin(t*1.7)
 band=np.exp(-((y/H-.72)/.13)**2)*(1-side*.65)
 moving=np.roll(fog,int(t*26),axis=1)
 alpha=(.018+.065*moving)*band
 frame=frame*(1-alpha[...,None])+np.array([117,145,159])*alpha[...,None]
 # Small reflection modulation confined to wet ground.
 refl=ground*np.sin(y*.105-t*6+x*.012)*.016
 frame*=1+refl[...,None]
 im=Image.fromarray(np.uint8(np.clip(frame,0,255))).convert('RGBA')
 overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
 for rx,ry,z in rain:
  speed=430+z*1100; yy=(ry+t*speed)%(H+100)-50;xx=(rx-t*(24+z*55))%(W+150)-75
  length=8+z*37;d.line((xx,yy,xx-3-z*6,yy+length),fill=(173,199,211,int(18+z*37)),width=1 if z<.8 else 2)
 # Expanding sparse rain impacts, perspective-scaled on street.
 for k in range(30):
  phase=(t*1.8+k*.371)%1;yy=H*.88+(k%7)/7*H*.12;xx=(k*173+51)%W
  rr=(3+phase*14)*(yy/H)**3
  d.ellipse((xx-rr,yy-rr*.18,xx+rr,yy+rr*.18),outline=(171,197,211,int((1-phase)*37)),width=1)
 im=Image.alpha_composite(im,overlay).convert('RGB')
 im.save(ROOT/'work/frames'/f'{i:04d}.png')
 if i%24==0:print('frame',i,flush=True)
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(ROOT/'work/frames/%04d.png'),'-i',str(OUT/'audio/city_3s.wav'),'-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-t','3','-movflags','+faststart',str(OUT/'ZERO_CODE_AI_CITY_3S_DRAFT_HOLD.mp4')],check=True)
