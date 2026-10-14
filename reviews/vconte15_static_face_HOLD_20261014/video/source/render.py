from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import math,random,subprocess,json
from pathlib import Path
W,H=720,1280; fps=24
out=Path(__file__).resolve().parents[1];assets=out/'assets';(out/'frames').mkdir(exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f=ImageFont.truetype(font,19); small=ImageFont.truetype(font,16); title=ImageFont.truetype(bold,69)
city=Image.open(assets/'city.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
back=Image.open(assets/'back.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
face=Image.open(assets/'face_evidence.png').convert('RGB')
random.seed(40);rain=[(random.randrange(W),random.randrange(H),random.randrange(250,700),random.randrange(12,31)) for _ in range(145)]
def txt(im,text,y,font=f,fill=(177,202,209),align='center'):
 d=ImageDraw.Draw(im); x=(W-d.textlength(text,font=font))/2 if align=='center' else 28;d.text((x,y),text,font=font,fill=fill)
def zoom(im,s):
 a=im.resize((round(W*s),round(H*s)),Image.Resampling.LANCZOS);x=(a.width-W)//2;y=(a.height-H)//2;return a.crop((x,y,x+W,y+H))
def atmosphere(im,t,strength=1):
 ov=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ov)
 for x,y,s,l in rain:
  yy=(y+t*s)%H;xx=(x+t*35)%W;d.line((xx,yy,xx-5,yy+l),fill=(157,194,210,round(50*strength)),width=1)
 for k in range(4):
  yy=720+70*math.sin(t*.38+k)+k*95;d.ellipse((-240+t*10,yy-90,900+t*10,yy+100),fill=(113,167,184,round(7*strength)))
 return Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
for i in range(360):
 t=i/fps
 if t<3:
  im=atmosphere(zoom(city,1+.035*t/3),t)
 elif t<6:
  im=atmosphere(zoom(back,1+.045*(t-3)/3),t)
 elif t<8:
  u=t-6;im=zoom(city,1.035)
  # All emissive city accents extinguish together, then isolated windows relight.
  p=im.load()
  for yy in range(H):
   for xx in range(W):
    r,g,b=p[xx,yy]
    if (g>r*1.45 and g>38) or (r>g*1.25 and r>80): p[xx,yy]=(8,14,21)
  im=ImageEnhance.Brightness(im).enhance(.72)
  if u>.55:
   d=ImageDraw.Draw(im)
   for k,(x,y) in enumerate([(220,340),(438,525),(73,690),(625,795),(329,465)]):
    if math.sin(u*(18+k*3)+k*2)>.48:d.rectangle((x,y,x+4,y+22),fill=(80,189,207))
  im=atmosphere(im,t,.55)
 elif t<11:
  im=Image.new('RGB',(W,H),(7,12,18));im.paste(face,((W-face.width)//2,430))
  txt(im,'S04 / FACE PLACEHOLDER',294)
  txt(im,'C/FILM full-resolution original: UNCONFIRMED',752,small)
  txt(im,'512 x 283 evidence crop / static / no enlargement',787,small)
  txt(im,'Framing and identity approval: HOLD',840,small,(142,161,170))
 elif t<13:
  # Defocused contour only: deliberately no clothing, face, age, or ability detail.
  im=Image.new('RGB',(W,H),(6,13,22));glow=Image.new('RGBA',(W,H));d=ImageDraw.Draw(glow)
  for r in range(250,0,-8):d.ellipse((360-r,620-r*1.5,360+r,620+r*1.5),fill=(100,182,205,int(135*(1-r/260))))
  im=Image.alpha_composite(im.convert('RGBA'),glow).convert('RGB');sh=Image.new('RGBA',(W,H));d=ImageDraw.Draw(sh)
  d.ellipse((327,450,393,535),fill=(2,7,12,255));d.polygon([(340,515),(306,563),(286,796),(432,796),(414,563),(383,515)],fill=(2,7,12,255))
  sh=sh.filter(ImageFilter.GaussianBlur(13));im=Image.alpha_composite(im.convert('RGBA'),sh).convert('RGB');im=atmosphere(im,t,.5)
  txt(im,'B / silhouette placeholder - design unconfirmed',1110,small)
 else:
  im=Image.new('RGB',(W,H),(5,9,15));d=ImageDraw.Draw(im);a=min(1,(t-13)*1.7);col=tuple(int(v*a) for v in (225,235,236));txt(im,'ZERO CODE',565,title,col);d.line((180,670,540,670),fill=(43,105,122),width=1);txt(im,'15 SECOND V-CONTÉ / REVIEW CUT',711,small)
 # Editorial watermark is outside worldbuilding, never HUD.
 d=ImageDraw.Draw(im);d.rectangle((0,0,W,64),fill=(5,10,16));d.text((26,23),'ZERO CODE   /   DRAFT - HOLD',font=f,fill=(168,194,202));d.text((W-100,25),f'{t:05.2f}s',font=small,fill=(113,145,156))
 im.save(out/'frames'/f'{i:04d}.png')
 if i%24==0:print(i,flush=True)
subprocess.run(['ffmpeg','-y','-framerate','24','-i',str(out/'frames/%04d.png'),'-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'silent.mp4')],check=True)
