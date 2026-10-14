"""Local restrained 2D atmosphere composite after depth-aware Blender rendering.
Not a volumetric simulation. Keeps architecture and composition stationary.
"""
from pathlib import Path
import sys,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
src,dst=map(Path,sys.argv[1:3]);dst.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(sorted(src.glob('frame_*.png'))):
 im=Image.open(p).convert('RGB');w,h=im.size;t=i/24
 y,x=np.mgrid[0:h,0:w].astype(np.float32);x/=w;y/=h
 mask=Image.new('L',(w,h));d=ImageDraw.Draw(mask)
 d.polygon([(int(w*u),int(h*v)) for u,v in [(.38,.39),(.79,.39),(.76,.55),(.69,.63),(.69,.69),(.40,.65),(.34,.54)]],fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(22))
 field=(.50+.25*np.sin(14*x+4*y-t*.7)+.25*np.sin(29*x-8*y+t*.45))
 fog=np.asarray(mask,dtype=np.float32)/255 * np.exp(-((y-.56)/.105)**2) * field *.025
 a=np.asarray(im,dtype=np.float32);a=a*(1-fog[:,:,None])+np.array([88,116,139])*fog[:,:,None]
 # Painted cyan band only, using cyan channel selection; <= 1.5% slow variation.
 region=np.exp(-((x-.635)/.07)**8-((y-.298)/.018)**8)
 blue=np.clip((a[:,:,2]-a[:,:,0]-12)/40,0,1)
 pulse=1+.015*math.sin(t*2.1)*region*blue
 a*=pulse[:,:,None]
 Image.fromarray(np.uint8(np.clip(a,0,255))).save(dst/p.name)
print('composited',i+1,'frames')
