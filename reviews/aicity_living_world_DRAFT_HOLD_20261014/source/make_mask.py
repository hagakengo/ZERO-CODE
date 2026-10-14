from PIL import Image,ImageFilter
import numpy as np
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--background',required=True);p.add_argument('--out',required=True);a=p.parse_args()
im=Image.open(a.background).convert('RGB').resize((1080,1920));rgb=np.array(im).astype(float);h,w=rgb.shape[:2];y,x=np.mgrid[:h,:w];x=x/w;y=y/h
# Confined to existing central tower lights, not a blanket rectangular fade.
central=(x>.561)&(x<.677)&(y>.205)&(y<.482)
cyan=np.clip((rgb[:,:,2]-rgb[:,:,0]-12)/40,0,1)*np.clip((rgb[:,:,1]-55)/50,0,1)
warm=np.clip((rgb[:,:,0]-rgb[:,:,2]-6)/24,0,1)*np.clip((rgb[:,:,0]-55)/50,0,1)
lights=np.maximum(cyan,warm)*central
# A small section of associated cyan road bounce dims, preserving warm side lights.
reflection=np.exp(-((x-.64)/.055)**2)*((y>.65)&(y<.94))*cyan*.55
mask=np.maximum(lights,reflection)
Image.fromarray(np.uint8(mask*255)).filter(ImageFilter.GaussianBlur(.7)).save(a.out)
