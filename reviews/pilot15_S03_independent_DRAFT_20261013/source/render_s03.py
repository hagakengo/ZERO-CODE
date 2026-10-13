"""S03 tension-hold 2D layout animation adapted from repository S02 source. Python 3 + Pillow + ffmpeg.
No input imagery, models, fonts, audio, or third party assets used.
Run from any directory; output is contained in this review folder.
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math, random, subprocess, json, hashlib
R=Path(__file__).resolve().parents[1]
W,H=1080,1920
for d in ['frames','video','verification']: (R/d).mkdir(exist_ok=True)
rng=random.Random(103)
# Giant city canyon; vanishing point intentionally right of the protagonist.
bg=Image.new('RGB',(W,H)); d=ImageDraw.Draw(bg)
for y in range(H):
    a=math.exp(-((y-1100)/500)**2)
    d.line((0,y,W,y),fill=(int(7+18*a),int(12+28*a),int(22+34*a)))
# Soft atmospheric shafts (environment only).
fog=Image.new('RGBA',(W,H)); f=ImageDraw.Draw(fog)
f.polygon([(620,-100),(890,-100),(770,1280),(400,1280)], fill=(85,128,149,20))
f.ellipse((200,750,1050,1450),fill=(78,115,137,34))
bg=Image.alpha_composite(bg.convert('RGBA'),fog.filter(ImageFilter.GaussianBlur(95)))
d=ImageDraw.Draw(bg)
# Distant skyline, then monumental foreground facades.
for i in range(42):
    x=i*29+rng.randint(-14,14); top=rng.randint(720,1080); width=rng.randint(15,45)
    d.rectangle((x,top,x+width,1210),fill=(25,40,53))
    for yy in range(top+20,1190,24):
        if rng.random()<.45: d.line((x+5,yy,x+width-5,yy),fill=(51,72,85),width=2)
# Side masses create immense scale, no signage or symbols.
for side in [0,1]:
    def pts(p): return [(W-x if side else x,y) for x,y in p]
    d.polygon(pts([(0,0),(260,0),(326,1070),(415,1230),(0,1530)]),fill=(9,16,25))
    d.polygon(pts([(40,0),(180,0),(250,1100),(182,1190)]),fill=(16,25,36))
    for x in [30,105,190,245]:
        d.line(pts([(x,0),(x+68,1100)]),fill=(33,49,63),width=3)
    for yy in range(110,1070,105):
        d.line(pts([(0,yy),(265+yy*.05,yy+65)]),fill=(36,51,64),width=3)
    for yy in range(150,1020,145):
        d.polygon(pts([(45,yy),(120,yy+15),(124,yy+45),(49,yy+30)]),fill=(43,67,79))
# Architectural bridge, no event / activation.
d.polygon([(267,722),(828,677),(833,735),(279,783)],fill=(18,30,42))
d.line((280,783,832,735),fill=(64,88,102),width=3)
for x in range(320,800,65): d.line((x,719,x+3,756), fill=(38,54,68),width=5)
# Street plane and perspective seam pattern.
d.polygon([(415,1170),(700,1170),(1080,1920),(0,1920)],fill=(15,25,36))
for x in [-700,-150,280,790,1300,1800]:
    d.line((580,1160,x,1920),fill=(37,54,66),width=2)
for yy in [1220,1300,1410,1570,1790]:
    a=(yy-1170)/750
    d.line((415-415*a,yy,700+380*a,yy),fill=(37,54,66),width=2)
# Broad wet reflections; low contrast and environmental, not clothing glow.
wet=Image.new('RGBA',(W,H)); wd=ImageDraw.Draw(wet)
for i in range(55):
    yy=rng.randint(1200,1910); x=rng.choice([210,860])+rng.randint(-95,95)
    ww=rng.randint(8,90)
    wd.line((x-ww,yy,x+ww,yy),fill=(80,118,137,rng.randint(8,32)),width=rng.randint(1,5))
bg=Image.alpha_composite(bg,wet.filter(ImageFilter.GaussianBlur(2)))
# Stable deterministic rain particles; animation is held on threes.
rain=[(rng.randrange(W+70),rng.randrange(H+100),rng.randrange(15,36)) for _ in range(115)]
# Smooth filled closed shapes from explicit cubic Bezier control points.
def shape(draw,start,segments,fill):
    p=[start]; x0,y0=start
    for x1,y1,x2,y2,x3,y3 in segments:
        for j in range(1,17):
            t=j/16; s=1-t
            p.append((s*s*s*x0+3*s*s*t*x1+3*s*t*t*x2+t*t*t*x3,s*s*s*y0+3*s*s*t*y1+3*s*t*t*y2+t*t*t*y3))
        x0,y0=x3,y3
    draw.polygon(p,fill=fill)

def ease(a,b,t):
    u=max(0,min(1,(t-a)/(b-a))); return u*u*(3-2*u)
def pose(n):
    # Continue S02's settled stance. Compress into a launch-ready load without stepping.
    load=ease(6,38,n)
    settle=ease(42,56,n)
    x=16-5*load+2*settle
    y=8+14*load-3*settle
    bag=-5*math.sin(math.pi*ease(20,58,n))
    return x,y,1.0,0.0,bag
class PoseDraw:
    def __init__(self,draw,dx,dy): self.draw=draw; self.dx=dx; self.dy=dy
    def point(self,p):
        x,y=p; lean=max(0,min(1,(1490-y)/430))
        return (x+self.dx+.2*self.dx*lean,y+self.dy)
    def polygon(self,p,**kw): return self.draw.polygon([self.point(v) for v in p],**kw)
    def line(self,p,**kw):
        if isinstance(p[0],(int,float)): p=list(zip(p[::2],p[1::2]))
        return self.draw.line([self.point(v) for v in p],**kw)
    def rounded_rectangle(self,p,**kw):
        a=self.point(p[:2]); b=self.point(p[2:]); return self.draw.rounded_rectangle((*a,*b),**kw)
def render(frame):
    # Normal action on twos through F208; F209-F215 are one intentional held silence window.
    n=min((frame//2)*2,64)
    dx,dy,step,lift,bag_lag=pose(n)
    im=bg.copy(); d=ImageDraw.Draw(im)
    # Unresolved distant threat: featureless placeholder only, no face, costume, weapon or logo.
    approach=ease(0,54,n); ex=684; ey=1265+8*approach; sc=1.17+.08*approach
    d.ellipse((ex-10*sc,ey-62*sc,ex+10*sc,ey-42*sc),fill=(20,29,38))
    d.polygon([(ex-10*sc,ey-45*sc),(ex+10*sc,ey-45*sc),(ex+17*sc,ey-13*sc),(ex+10*sc,ey),(ex,ey-20*sc),(ex-7*sc,ey),(ex-15*sc,ey-12*sc)],fill=(20,29,38))
    shadow=Image.new('RGBA',(W,H)); sd=ImageDraw.Draw(shadow)
    sd.ellipse((333,1665,641,1715),fill=(0,0,0,120))
    im=Image.alpha_composite(im,shadow.filter(ImageFilter.GaussianBlur(13))); d=ImageDraw.Draw(im)
    # Original S01 leg contours are re-evaluated through joint-dependent warps.
    # Left foot remains fixed; right foot travels only during swing, then locks.
    rx=36*step; ry=-44*step-lift
    class LegDraw(PoseDraw):
        def point(self,p):
            x,y=p; a=max(0,min(1,(y-1475)/190)); right=x>=487
            knee=math.sin(math.pi*a)
            return (x+dx*(1-a)+(rx*a if right else -8*ease(4,18,n)*knee),
                    y+dy*(1-a)+(ry*a if right else 0))
    d=LegDraw(ImageDraw.Draw(im),dx,dy)
    # Charcoal cargo legs. No diagnostic lines, no emission.
    shape(d,(408,1460),[(430,1450,479,1450,486,1483),(479,1540,460,1600,450,1671),(433,1682,414,1680,397,1674),(400,1590,393,1511,408,1460)],(29,33,39))
    shape(d,(489,1464),[(516,1450,546,1459,552,1487),(558,1540,565,1620,574,1672),(560,1682,536,1684,523,1676),(507,1599,488,1541,489,1464)],(23,28,34))
    d.polygon([(402,1515),(433,1517),(430,1564),(400,1560)],fill=(36,41,47))
    d.polygon([(537,1517),(554,1514),(560,1564),(542,1568)],fill=(33,38,44))
    d.line((414,1576,416,1655),fill=(44,49,54),width=3)
    # Shoes and soles: anchored, exactly same pixels at every time.
    shape(d,(397,1665),[(415,1670,434,1671,451,1664),(459,1682,458,1697,450,1703),(427,1707,397,1707,376,1704),(370,1693,386,1679,397,1665)],(8,11,16))
    shape(d,(521,1667),[(538,1671,556,1675,574,1667),(583,1683,603,1690,604,1703),(580,1710,548,1709,527,1704),(521,1695,520,1684,521,1667)],(8,11,16))
    d.line((378,1703,449,1704),fill=(55,60,64),width=3)
    d.line((530,1704,601,1704),fill=(47,52,59),width=3)
    d=PoseDraw(ImageDraw.Draw(im),dx,dy)
    sleeve=4+5*ease(8,38,n)-2*ease(44,58,n)
    # Oversized torso and sleeves. Rear silhouette, neck / face never drawn.
    y=0
    shape(d,(399,1218+y),[(424,1193+y,526,1190+y,553,1218+y),(574,1290+y,570,1400+y,553,1478),(515,1495,444,1495,405,1476),(390,1390+y,378,1290+y,399,1218+y)],(17,21,27))
    shape(d,(399,1224+y),[(370,1237+y,353,1285+y,348,1326+y),(340,1372+y,346,1415,354+sleeve,1452),(367+sleeve,1462,389+sleeve,1457,394,1444),(387,1396,385,1352+y,402,1309+y),(412,1270+y,421,1235+y,399,1224+y)],(23,27,33))
    shape(d,(550,1220+y),[(581,1240+y,600,1302+y,604,1347+y),(608,1382+y,600,1420,594-sleeve,1450),(579-sleeve,1460,564-sleeve,1455,559,1443),(565,1391,564,1355+y,547,1311+y),(535,1270+y,533,1236+y,550,1220+y)],(14,18,24))
    d.line((365,1310+y,361,1371+y,370+sleeve,1421),fill=(44,48,54),width=3)
    d.line((586,1335+y,588,1393),fill=(32,37,43),width=3)
    d.rounded_rectangle((355+sleeve,1440,390+sleeve,1470),radius=7,fill=(10,14,20))
    d.rounded_rectangle((563-sleeve,1440,593-sleeve,1470),radius=7,fill=(9,12,17))
    # Shoulder straps visible beside backpack.
    shape(d,(411,1218+y),[(404,1270+y,406,1320+y,414,1353+y),(421,1359+y,427,1353+y,428,1345+y),(422,1290+y,423,1250+y,433,1220+y)],(42,45,49))
    shape(d,(533,1218+y),[(545,1256+y,551,1307+y,545,1350+y),(539,1357+y,531,1356+y,530,1346+y),(535,1290+y,530,1253+y,519,1220+y)],(31,35,40))
    # Structured blank angular black backpack, no emblem/panel text.
    by=bag_lag
    d.polygon([(429,1260+by),(521,1260+by),(543,1283+by),(543,1418+by),(525,1443+by),(423,1443+by),(407,1422+by),(407,1284+by)],fill=(7,10,14))
    d.polygon([(429,1260+by),(521,1260+by),(534,1281+by),(419,1281+by)],fill=(40,44,49))
    d.polygon([(419,1281+by),(534,1281+by),(534,1416+by),(520,1431+by),(426,1431+by),(419,1416+by)],fill=(23,27,32))
    d.polygon([(534,1281+by),(543,1283+by),(543,1418+by),(534,1416+by)],fill=(13,17,22))
    d.line((419,1283+by,419,1416+by,426,1431+by),fill=(57,60,64),width=2)
    # Rear hood overlaps shoulders. The entire head is enclosed in black cloth.
    shape(d,(407,1201+y),[(398,1175+y,400,1136+y,415,1108+y),(432,1080+y,456,1065+y,477,1061+y),(501,1068+y,526,1086+y,539,1118+y),(551,1147+y,550,1184+y,536,1207+y),(511,1227+y,447,1230+y,407,1201+y)],(26,30,37))
    shape(d,(420,1197+y),[(412,1152+y,425,1104+y,477,1073+y),(443,1118+y,444,1167+y,450,1208+y),(436,1207+y,427,1202+y,420,1197+y)],(38,42,49))
    shape(d,(479,1073+y),[(517,1092+y,537,1130+y,536,1176+y),(530,1197+y,507,1207+y,486,1213+y),(501,1178+y,505,1116+y,479,1073+y)],(18,22,29))
    d.line((407,1201+y,450,1219+y,494,1220+y,536,1207+y),fill=(51,54,60),width=2)

    rainlayer=Image.new('RGBA',(W,H)); rd=ImageDraw.Draw(rainlayer)
    for x,z,l in rain:
        # Continue prior rain timing; the last seven frames hold with the character.
        tick=47+n/3; yy=(z+tick*21)%(H+100)-50; xx=(x-tick*3)%(W+70)-35
        rd.line((xx,yy,xx-4,yy+l),fill=(112,137,154,45),width=1)
    im=Image.alpha_composite(im,rainlayer)
    beat='tension_hold' if n<8 else 'load' if n<40 else 'micro_settle' if frame<65 else 'silence_window'
    return im.convert('RGB'),dict(local_frame=frame,pilot_frame=144+frame,drawing=min(frame//2,32),exposure=(7 if frame>=65 else 2),beat=beat,root_dx=dx,root_dy=dy,right_foot_dx=rx,right_foot_dy=ry,swing_lift=lift,left_foot_fixed=True,right_foot_fixed=True,bag_lag_y=bag_lag)
records=[]
for n in range(72):
    im,rec=render(n); im.save(R/'frames'/f'F{n:03}.png'); records.append(rec)
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(R/'frames/F%03d.png'),'-frames:v','72','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(R/'video/S03_pre_dash_tension_DRAFT_24fps.mp4')],check=True)
(R/'verification/exposure_sheet.json').write_text(json.dumps(records,indent=2))
import csv
with (R/'exposure_sheet.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator="\n"); w.writeheader(); w.writerows(records)
board=Image.new('RGB',(1080,1080),(222,224,223)); bd=ImageDraw.Draw(board)
for j,n in enumerate([0,8,20,32,40,52,64,71]):
    thumb=Image.open(R/'frames'/f'F{n:03}.png').resize((243,432)); x=15+(j%4)*270; yy=35+(j//4)*520
    board.paste(thumb,(x,yy)); bd.text((x,yy+440),f'S03 L{n:03} / F{n+144:03}',fill=(25,30,35))
    bd.text((x,yy+458),records[n]['beat'],fill=(25,30,35))
board.save(R/'keyframes.png')
print('Rendered S03: 72 frames / twos through F208 / held F209-F215 / 3 seconds')
