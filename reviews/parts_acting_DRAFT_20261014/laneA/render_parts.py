from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import cairosvg,base64,io,csv,subprocess,json
O=Path(__file__).resolve().parent; O.mkdir(parents=True,exist_ok=True)
for x in ['parts','frames','svg_frames']: (O/x).mkdir(exist_ok=True)
src=O.parent/'reference/A_B_C_comparison_DRAFT.png'
im=Image.open(src).convert('RGBA').crop((1024,49,1536,332)); im.save(O/'source_crop.png')
# Retain original construction and repaint only bounded feature bands by boundary colour interpolation.
clean=im.copy(); px=clean.load(); orig=im.load()
for x0,x1,y0,slope,wide in [(203,235,111,-.38,7),(263,300,84,-.37,8),(249,285,141,-.32,4)]:
 for x in range(x0,x1):
  cy=y0+slope*(x-x0); ya=int(cy-wide);yb=int(cy+wide)
  a=orig[x,ya];b=orig[x,yb]
  if x0==203:a=b=(156,130,116,255)
  if x0==263:a=b=(166,141,126,255)
  for y in range(ya+1,yb):
   t=(y-ya)/(yb-ya);px[x,y]=tuple(round(a[k]*(1-t)+b[k]*t) for k in range(3))+(255,)
clean.save(O/'clean_feature_base.png')
# Actual silhouette matte: no rectangular white-backed feature clips.
mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.polygon([(0,283),(13,271),(48,245),(73,224),(105,220),(125,174),(160,166),(192,159),(178,132),(161,148),(136,122),(116,124),(133,101),(123,83),(145,50),(137,30),(160,0),(297,0),(338,20),(361,26),(360,40),(383,46),(367,61),(380,71),(358,90),(362,122),(347,146),(341,165),(368,151),(396,141),(422,148),(449,181),(451,209),(493,226),(512,239),(512,283)],fill=255)
# Remove connected bright neutral source background, retaining dark character pixels.
from collections import deque
seen=set();q=deque([(x,0) for x in range(512)]+[(x,282) for x in range(512)]+[(0,y) for y in range(283)]+[(511,y) for y in range(283)])
while q:
 x,y=q.popleft()
 if (x,y) in seen or not (0<=x<512 and 0<=y<283):continue
 seen.add((x,y));rgb=orig[x,y][:3]
 if min(rgb)<184 or max(rgb)-min(rgb)>19:continue
 mask.putpixel((x,y),0);q.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
clean.putalpha(mask);clean.save(O/'parts/base_body_face.png')
hairmask=Image.new('L',im.size);ImageDraw.Draw(hairmask).polygon([(160,0),(298,0),(338,20),(362,26),(358,41),(383,46),(367,61),(380,71),(358,91),(362,122),(347,146),(338,142),(342,114),(323,98),(310,96),(305,108),(296,110),(292,90),(282,65),(267,63),(257,75),(252,92),(267,99),(251,96),(238,89),(239,108),(228,116),(231,97),(215,85),(202,94),(205,113),(213,123),(202,121),(196,132),(179,133),(161,148),(137,123),(116,124),(134,101),(123,83),(145,50),(137,30)],fill=255)
# Exclude eye repaint bands: original pupils must never reappear through the hair matte.
hd=ImageDraw.Draw(hairmask)
for x0,x1,y0,slope,wide in [(203,235,111,-.38,7),(263,300,84,-.37,8)]:
 for x in range(x0,x1):
  cy=y0+slope*(x-x0);hd.line((x,int(cy-wide)+1,x,int(cy+wide)-1),fill=0)
for y in range(283):
 for x in range(512):
  if mask.getpixel((x,y))==0:hairmask.putpixel((x,y),0)
hair=im.copy();hair.putalpha(hairmask);hair.save(O/'parts/foreground_hair.png')
# Base contains hair too; foreground extraction is editable but no hidden-hair reconstruction claimed.
def wrap(s):return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="283" viewBox="0 0 512 283">'+s+'</svg>'
def path(s,fill='none',stroke='#302b2b',w=1.3):return f'<path d="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"/>'
def components(f):
 # Explicit aperture drawing, not transform-scaled images. Full closure uses a separate stroke drawing.
 closure=[0]*6+[.25,.65,1,1,.55,.15]+[0]*12
 c=closure[f]; smile=max(0,min(1,(f-11)/5)) if f<18 else max(0,1-(f-18)/3)
 notice=max(0,min(1,(f-18)/4));gaze=min(1,f/5)*1.8-notice*2.5
 p={}; eye='';iris='';lids=''
 for name,x,y,dx,dy in [('L',204,110,30,-11),('R',263,83,35,-13)]:
  h=(5.8+notice*3)*(1-c)
  upper=f'M {x},{y} Q {x+dx*.44},{y+dy*.46-h:.2f} {x+dx},{y+dy}'
  lower=f' Q {x+dx*.53},{y+dy*.5+h:.2f} {x},{y} Z'
  if c<.99:
   eye+=path(upper+lower,'#c1b0a6','#4a3b39',.65)
   iris+=f'<defs><clipPath id="eye{name}"><path d="{upper+lower}"/></clipPath></defs><g clip-path="url(#eye{name})"><ellipse cx="{x+dx*.56+gaze:.2f}" cy="{y+dy*.52}" rx="4.6" ry="5.3" fill="#555054"/><ellipse cx="{x+dx*.56+gaze:.2f}" cy="{y+dy*.52}" rx="1.8" ry="4.4" fill="#29272c"/><circle cx="{x+dx*.52+gaze}" cy="{y+dy*.52-1.5}" r=".8" fill="#ddd0bc"/></g>'
   lids+=path(upper,w=1.65)
  else:lids+=path(f'M {x},{y} Q {x+dx*.45},{y+dy*.44+2.3} {x+dx},{y+dy}',w=1.7)
 p['eye_whites']=eye;p['irises']=iris;p['eyelids']=lids
 # Original eyebrows remain partially under fringe; new independent accents follow observed slope.
 p['brows']=path(f'M 207,{91-notice*2:.2f} Q 218,{87-notice*3:.2f} 230,{87-notice*1:.2f}',w=1.5)+path(f'M 262,{65-notice*4:.2f} Q 276,{58-notice*4:.2f} 291,{60-notice*2:.2f}',w=1.8)
 p['mouth']=path(f'M 250,141 Q 264,{133+smile*4-notice*2:.2f} 283,{130-smile*1.5+notice:.2f}',w=1.25)
 if notice>.2:p['mouth']+=path(f'M 260,138 Q 267,{139+notice*1.8:.2f} 273,134',w=.65)
 p['cheeks']=f'<g opacity="{smile*.18}">'+path('M 240,124 Q 242,126 244,126',stroke='#a65950',w=2)+path('M 286,101 Q 290,102 292,100',stroke='#a65950',w=2)+'</g>'
 return p
b64=base64.b64encode((O/'parts/base_body_face.png').read_bytes()).decode();h64=base64.b64encode((O/'parts/foreground_hair.png').read_bytes()).decode()
rows=[]
for f in range(24):
 p=components(f); groups=f'<g id="base"><image width="512" height="283" xlink:href="data:image/png;base64,{b64}"/></g>'+''.join(f'<g id="{n}">{s}</g>' for n,s in p.items())+f'<g id="foreground_hair"><image width="512" height="283" xlink:href="data:image/png;base64,{h64}"/></g>'
 svg=wrap(groups);(O/'svg_frames'/f'{f:03}.svg').write_text(svg)
 rendered=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=1024,output_height=566)))
 canvas=Image.new('RGB',(1024,640),'#e7e5e3');canvas.paste(im.resize((1024,566)),(0,40));canvas.paste(rendered,(0,40),rendered);dr=ImageDraw.Draw(canvas);dr.text((18,12),f'A | EDITABLE PARTS | DRAFT / HOLD | frame {f+1:02}/24',fill='#202020');dr.text((18,615),'Existing tilted C view / not a corrected frontal model',fill='#202020');canvas.save(O/'frames'/f'{f:03}.png')
 rows.append([f+1,f/24,['gaze','blink','smile','notice'][f//6],f'svg_frames/{f:03}.svg','procedural vector path drawing; fixed source silhouette'])
 if f==16:
  cheeksvg=wrap(p['cheeks']);(O/'parts/cheeks_smile.svg').write_text(cheeksvg);cairosvg.svg2png(bytestring=cheeksvg.encode(),write_to=str(O/'parts/cheeks_smile.png'))
 if f==0:
  (O/'editable_composite.svg').write_text(svg)
  for n,s in p.items():
   (O/'parts'/f'{n}.svg').write_text(wrap(s));cairosvg.svg2png(bytestring=wrap(s).encode(),write_to=str(O/'parts'/f'{n}.png'))
with (O/'exposure.csv').open('w') as out:
 w=csv.writer(out,lineterminator="\n");w.writerow(['frame','time_seconds','beat','source','method']);w.writerows(rows)
for name,vf in [('normal_24fps.mp4',None),('half_speed_24fps.mp4','setpts=2*PTS,fps=24')]:
 cmd=['ffmpeg','-v','error','-y','-framerate','24','-i',str(O/'frames/%03d.png')]
 if vf:cmd+=['-vf',vf]
 cmd+=['-frames:v','48' if vf else '24','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(O/name)];subprocess.run(cmd,check=True)
# transparent assets on checkerboard sheet
files=list((O/'parts').glob('*.png'));sheet=Image.new('RGB',(1024,((len(files)+1)//2)*320),'white');ds=ImageDraw.Draw(sheet)
for i,file in enumerate(files):
 x=(i%2)*512;y=(i//2)*320
 for yy in range(y+24,y+307,16):
  for xx in range(x,x+512,16):ds.rectangle((xx,yy,xx+15,yy+15),fill=('#d5d5d5' if ((xx-x)//16+(yy-y)//16)%2 else '#fafafa'))
 q=Image.open(file);sheet.paste(q,(x,y+24),q);ds.text((x+8,y+5),file.stem+' / DRAFT HOLD',fill='black')
sheet.save(O/'parts_sheet_DRAFT.png')
frames=Image.new('RGB',(1024,640*4),'white')
for i,f in enumerate([0,8,16,23]):frames.paste(Image.open(O/'frames'/f'{f:03}.png'),(0,i*640))
frames.save(O/'acting_key_sheet_DRAFT.png')
