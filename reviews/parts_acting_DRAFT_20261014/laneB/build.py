from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math,json,csv,base64,io,subprocess,hashlib
OUT=Path(__file__).resolve().parent; OUT.mkdir(parents=True,exist_ok=True)
for d in ['frames','drawings','keys','inbetweens']: (OUT/d).mkdir(exist_ok=True)
SRC=OUT.parent/'reference'/'A_B_C_comparison_DRAFT.png'
base=Image.open(SRC).convert('RGB').crop((1024,49,1536,332));base.save(OUT/'source_crop_DRAFT.png')
# Correct only the narrow old mouth stroke with neighboring skin samples.
original=base.copy();pix=base.load();op=original.load()
for x in range(247,286):
 t=(x-250)/33;yline=round(141-11*t-1.4*math.sin(max(0,min(1,t))*math.pi))
 for y in range(yline-2,yline+3):
  above=op[x,yline-4];below=op[x,yline+4];w=(y-(yline-4))/8
  pix[x,y]=tuple(round(a*(1-w)+b*w) for a,b in zip(above,below))
base.save(OUT/'clean_mouth_base_DRAFT.png')
# Each authored drawing has independently specified upper/lower lid depths, gaze, mouth curvature, brow lift.
# Local eye coordinates: tangent runs along original tilted eye corners; normal points down.
# Frames between these drawings are mathematical coordinate interpolation, not claimed as authored drawings.
authored={0:[-3.2,3.5,0,1.1,0],3:[-3.1,3.4,1.0,1.1,0],5:[-3.0,3.4,1.8,1.1,0],6:[-2.5,3.1,1.8,1.1,0],7:[-0.8,2.8,1.8,1.1,0],8:[1.8,2.5,1.8,1.1,0],9:[2.4,2.4,1.8,1.1,0],10:[-1.4,3.0,1.8,1.1,0],11:[-3.1,3.4,1.8,1.0,0],13:[-2.9,3.1,1.8,3.2,0.2],15:[-2.7,2.8,1.8,4.0,0.4],17:[-2.7,2.8,1.8,4.2,0.4],18:[-3.3,3.6,0.8,2.2,0.8],20:[-4.2,4.1,-1.0,-0.3,1.4],23:[-4.3,4.2,-1.3,-0.6,1.6]}
keyframes={0,5,9,11,17,23}
# Nine intermediate contour drawings authored directly in local eye coordinates.
# [upper control x fraction,y, upper control x fraction,y, lower control x fraction,y,lower control x fraction,y].
# Left/right differ deliberately; these entries are not derived by interpolating key drawings.
inbetween_controls={
3:([.25,-3.2,.72,-3.0,.74,3.5,.26,3.2],[.27,-3.1,.73,-3.2,.75,3.4,.24,3.3]),
6:([.24,-2.7,.70,-2.3,.76,3.2,.25,2.9],[.27,-2.5,.74,-2.4,.73,3.2,.25,3.0]),
7:([.23,-1.1,.72,-.5,.75,2.9,.27,2.5],[.28,-.7,.74,-.9,.72,2.8,.27,2.6]),
8:([.27,1.7,.72,1.9,.74,2.6,.26,2.4],[.26,1.8,.73,1.6,.74,2.7,.25,2.4]),
10:([.25,-1.7,.70,-1.0,.76,3.1,.24,2.7],[.27,-1.3,.74,-1.6,.73,3.2,.26,2.9]),
13:([.25,-2.9,.71,-2.8,.75,3.0,.27,2.8],[.27,-3.0,.74,-2.8,.72,3.1,.25,2.9]),
15:([.26,-2.8,.72,-2.6,.73,2.7,.28,2.5],[.27,-2.7,.74,-2.8,.74,2.8,.26,2.6]),
18:([.24,-3.4,.72,-3.0,.75,3.6,.25,3.2],[.26,-3.3,.75,-3.4,.73,3.7,.26,3.4]),
20:([.25,-4.4,.72,-4.0,.74,4.2,.26,3.8],[.26,-4.3,.74,-4.1,.73,4.3,.25,4.0])}
scale=3
# Construct and rasterize same explicit Bezier paths; no image warps.
def bez(a,b,c,d,n=40):
 return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in [0,1]) for t in [i/n for i in range(n+1)]]
def path(points,fill='none',stroke='#241f20',width=.9,closed=False):
 p=[tuple(q) for q in points];s=f'M {p[0][0]:.3f},{p[0][1]:.3f} C '+ ' '.join(f'{q[0]:.3f},{q[1]:.3f}' for q in p[1:4]);
 if len(p)==7:s+=' C '+' '.join(f'{q[0]:.3f},{q[1]:.3f}' for q in p[4:]);
 if closed:s+=' Z'
 return s,fill,stroke,width

def eye(a,b,u,l,g):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);tx=dx/L;ty=dy/L;nx=-ty;ny=tx
 def P(x,y):return(a[0]+tx*x+nx*y,a[1]+ty*x+ny*y)
 return P,L,[P(0,0),P(L*.28,u),P(L*.72,u),P(L,0),P(L*.72,l),P(L*.28,l),P(0,0)]

def render(frame,vals):
 u,l,g,m,brow=vals; canvas=base.resize((1536,849),Image.Resampling.LANCZOS);draw=ImageDraw.Draw(canvas); shapes=[]
 def paint(shape):
  d,fill,stroke,width=shape;shapes.append(shape)
  # retain native control-point list in outer routine; rasterizer uses SVG-like parser numeric tokens
  import re
  nums=[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',d)];ps=list(zip(nums[::2],nums[1::2]));pts=bez(*ps[:4]);
  if len(ps)==7:pts+=bez(ps[3],*ps[4:]);
  pts=[(x*scale,y*scale) for x,y in pts]
  if fill!='none':draw.polygon(pts,fill=fill)
  if stroke!='none':draw.line(pts,fill=stroke,width=max(1,round(width*scale)),joint='curve')
 for eyeidx,(a,b,skin) in enumerate([((204,110),(234,99),'#a88a7e'),((263,83),(298,70),'#b19585')]):
  P,L,orig=eye(a,b,-9.0,9.0,g)
  # Exact localized paintout, does not move or duplicate original raster pixels.
  paint(path(orig,skin,'none',closed=True))
  P,L,cont=eye(a,b,u,l,g)
  if frame in inbetween_controls:
   z=inbetween_controls[frame][eyeidx]
   cont=[P(0,0),P(L*z[0],z[1]),P(L*z[2],z[3]),P(L,0),P(L*z[4],z[5]),P(L*z[6],z[7]),P(0,0)]
  if l-u>.5:
   paint(path(cont,'#c9b8aa','none',closed=True))
   cx=L*.57+g;cy=(u+l)*.25;rx=3.0;ry=3.5;center=P(cx,cy)
   # Iris is clipped by analytic eye envelope in sampled local coordinates.
   poly=[P(cx+rx*math.cos(2*math.pi*i/80),cy+ry*math.sin(2*math.pi*i/80)) for i in range(80)]
   iris_layer=Image.new('RGB',canvas.size,'#4f4947');mask=Image.new('L',canvas.size,0);md=ImageDraw.Draw(mask)
   outline=bez(*cont[:4])+bez(cont[3],*cont[4:]);md.polygon([(x*scale,y*scale) for x,y in outline],fill=255)
   iris_mask=Image.new('L',canvas.size,0);ImageDraw.Draw(iris_mask).polygon([(x*scale,y*scale) for x,y in poly],fill=255)
   from PIL import ImageChops
   canvas.paste(iris_layer,(0,0),ImageChops.multiply(mask,iris_mask));draw=ImageDraw.Draw(canvas)
   # Native SVG clipping keeps ellipse editable.
   idx=len(shapes);shapes.append(('IRIS',center,rx,ry,cont,poly))
  paint(path(cont,'none','#282326',.85,closed=True))
  paint(path(cont[:4],'none','#211d20',1.35))
 mouth=[(250,141),(260,135+m),(273,131+m),(283,130)]
 paint(path(mouth,'none','#473735',.85))
 if frame>=18:
  # lower contour of small parted mouth, smoothly introduced after smile
  opening=max(0,(frame-18)/5)*1.6
  paint(path([(250,141),(260,135+m+opening),(273,131+m+opening),(283,130)],'none','#765c54',.65))
 # Existing brows remain source; synchronized brow correction is explicitly unfinished.
 canvas=canvas.resize((768,424),Image.Resampling.LANCZOS)
 final=Image.new('RGB',(768,768),'#1b1e24');final.paste(canvas,(0,150));fd=ImageDraw.Draw(final)
 fd.text((22,26),'B | CORRECTED CONTOURS / DRAFT - HOLD',fill='white')
 phase='GAZE' if frame<6 else 'BLINK' if frame<12 else 'SLIGHT SMILE' if frame<18 else 'NOTICE'
 fd.text((22,620),f'{phase} | FRAME {frame+1:02d}/24 | tilted C/FILM source',fill='white')
 kind='AUTHORED VECTOR KEY' if frame in keyframes else 'AUTHORED VECTOR INBETWEEN' if frame in authored else 'PROCEDURAL COORDINATE INBETWEEN'
 fd.text((22,645),kind,fill='#e2b964');fd.text((22,680),'Brow/hair cleanup and identity approval: HOLD',fill='#d0d0d0')
 final.save(OUT/'frames'/f'{frame:03d}.png')
 b64=base64.b64encode((OUT/'clean_mouth_base_DRAFT.png').read_bytes()).decode();svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="283" viewBox="0 0 512 283"><title>DRAFT HOLD B frame {frame+1}; {kind}</title><image href="data:image/png;base64,{b64}" width="512" height="283"/>']
 for i,s in enumerate(shapes):
  if s[0]=='POLY':svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in s[1])+f'" fill="{s[2]}"/>')
  elif s[0]=='IRIS':
   _,c,rx,ry,cont,poly=s;d=path(cont,closed=True)[0];points=' '.join(f'{x},{y}' for x,y in poly);svg.append(f'<defs><clipPath id="eye{i}"><path d="{d}"/></clipPath></defs><polygon points="{points}" fill="#4f4947" clip-path="url(#eye{i})"/>')
  else:
   d,fill,stroke,w=s;svg.append(f'<path id="contour{i}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')
 svg.append('</svg>');(OUT/'drawings'/f'{frame:03d}.svg').write_text('\n'.join(svg))
 if frame in authored:
  final.save(OUT/('keys' if frame in keyframes else 'inbetweens')/f'{frame:03d}.png')
 return kind
rows=[]
for f in range(24):
 if f in authored: vals=authored[f]
 else:
  lo=max(k for k in authored if k<f);hi=min(k for k in authored if k>f);t=(f-lo)/(hi-lo);vals=[x+(y-x)*t for x,y in zip(authored[lo],authored[hi])]
 kind=render(f,vals);rows.append([f+1,f/24,kind,*vals])
with (OUT/'exposure.csv').open('w') as fh:
 w=csv.writer(fh);w.writerow(['frame_1based','time_s','drawing_method','upper_lid','lower_lid','gaze','mouth_curve','brow_parameter_UNUSED']);w.writerows(rows)
(OUT/'authored_contours.json').write_text(json.dumps({'status':'DRAFT/HOLD','source':str(SRC),'crop':[1024,49,1536,332],'authored_frame_0based':authored,'key_frames_0based':sorted(keyframes),'authored_key_count':6,'authored_vector_inbetween_count':9,'procedural_interpolation_frame_count':9,'traditional_hand_drawn_count':0,'direct_authored_inbetween_controls':inbetween_controls},indent=2))
for name,flt in [('normal_24fps.mp4','null'),('half_speed_24fps.mp4','setpts=2*PTS,fps=24')]:
 subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(OUT/'frames/%03d.png'),'-vf',flt,'-frames:v','24' if name.startswith('normal') else '48','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(OUT/name)],check=True)
sheet=Image.new('RGB',(1536,1152),'#1b1e24')
for f in range(24):sheet.paste(Image.open(OUT/'frames'/f'{f:03d}.png').resize((256,384)),((f%6)*256,(f//6)*288))
# 6 columns x4 rows, each reduced frame288 tall
sheet=Image.new('RGB',(1536,1152),'#1b1e24')
for f in range(24):sheet.paste(Image.open(OUT/'frames'/f'{f:03d}.png').resize((256,288)),((f%6)*256,(f//6)*288))
sheet.save(OUT/'all_frames_sheet_DRAFT.png')
