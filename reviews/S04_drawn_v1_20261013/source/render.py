"""Explicit replacement drawings; no tweening, IK, image warps, camera motion or FX.
Python 3 + Pillow + ffmpeg/ffprobe. Run from any working directory.
Each row is a deliberately authored drawing, NOT a sampled interpolation curve.
Coordinates are in a 1080x1920 scene; limb paths are inked as tapered contours.
"""
from PIL import Image, ImageDraw
from pathlib import Path
import math, csv, json, subprocess, hashlib
from background import bg
R=Path(__file__).resolve().parents[1]
for n in ['frames','keys','video','verification']: (R/n).mkdir(exist_ok=True)
# exposure, beat, pelvis, shoulder, hood, knees L/R, ankles L/R,
# elbows L/R, hands L/R, shoulder slant, hip slant, bag lag x/y, hem lag
# F216-218 still; then twos; F226-231 on ones; settle on twos then three.
D=[
(3,'hold',(490,1460),(477,1230),(475,1150),(433,1565),(548,1560),(423,1680),(562,1676),(367,1344),(592,1340),(369,1450),(588,1448),-4,5,0,0,0),
(2,'anticipation',(480,1484),(469,1258),(472,1175),(410,1570),(554,1578),(423,1680),(562,1676),(350,1370),(610,1360),(386,1444),(578,1456),8,-8,6,-6,7),
(2,'compress',(470,1498),(482,1267),(478,1186),(397,1577),(555,1586),(423,1680),(568,1676),(365,1380),(608,1350),(407,1440),(570,1415),16,-13,-6,-10,10),
(2,'push',(493,1472),(514,1242),(508,1160),(424,1572),(586,1545),(423,1680),(610,1630),(387,1360),(621,1308),(428,1404),(581,1352),19,-14,-13,2,-12),
(1,'accelerate',(521,1448),(547,1223),(538,1140),(450,1555),(612,1514),(439,1673),(646,1600),(421,1340),(642,1270),(466,1354),(607,1314),20,-14,-18,10,-21),
(1,'drive',(546,1432),(574,1218),(564,1132),(482,1541),(635,1504),(469,1650),(670,1590),(450,1320),(661,1262),(499,1317),(624,1309),16,-12,-20,14,-27),
(1,'reach',(569,1436),(592,1226),(586,1140),(516,1538),(646,1515),(507,1640),(679,1604),(476,1320),(674,1280),(519,1300),(638,1330),10,-8,-20,11,-23),
(1,'plant',(584,1457),(600,1246),(597,1159),(546,1550),(648,1530),(543,1655),(681,1623),(483,1342),(684,1318),(517,1334),(652,1380),3,-3,-16,4,-16),
(1,'cut_load',(584,1482),(580,1273),(582,1186),(543,1572),(650,1540),(543,1655),(681,1623),(462,1360),(680,1347),(500,1384),(641,1420),-15,13,8,-10,14),
(1,'cut_push',(563,1488),(542,1272),(545,1185),(515,1575),(643,1553),(511,1672),(681,1623),(425,1352),(645,1380),(460,1392),(594,1431),-24,18,23,-8,25),
(2,'lateral',(526,1472),(493,1250),(497,1164),(464,1572),(605,1549),(464,1690),(660,1623),(383,1325),(605,1374),(417,1377),(552,1418),-27,19,31,4,30),
(2,'lateral_reach',(478,1468),(443,1244),(450,1159),(405,1570),(559,1555),(392,1700),(621,1640),(335,1328),(548,1370),(370,1396),(498,1420),-23,17,30,9,26),
(2,'catch',(442,1490),(414,1269),(420,1180),(365,1590),(514,1580),(355,1700),(579,1683),(310,1365),(516,1388),(346,1440),(472,1450),-16,11,22,-5,19),
(2,'absorb',(424,1506),(413,1290),(413,1201),(367,1598),(487,1599),(355,1700),(555,1700),(314,1393),(511,1403),(350,1470),(473,1478),-7,6,8,-13,10),
(2,'recover',(428,1485),(431,1265),(426,1175),(376,1588),(488,1586),(355,1700),(555,1700),(332,1384),(535,1372),(359,1465),(503,1459),7,-6,-10,2,-7),
(3,'settle',(433,1469),(438,1244),(435,1155),(384,1580),(491,1578),(355,1700),(555,1700),(342,1360),(544,1352),(363,1450),(521,1449),6,-5,-5,7,-4),
]
D.insert(5,(1,'drive_breakdown',(534,1438),(561,1219),(551,1135),(466,1546),(624,1508),(453,1660),(660,1592),(435,1331),(652,1264),(483,1334),(616,1310),18,-13,-20,13,-25))
D.insert(9,(1,'plant_breakdown',(584,1470),(593,1259),(591,1172),(546,1562),(649,1534),(543,1655),(681,1623),(474,1351),(684,1332),(509,1358),(649,1400),-5,5,-5,-4,-1))
# 18 drawings = 30f. Keys chosen at extrema; the other drawings are authored inbetweens.
assert sum(p[0] for p in D)==30
KEYS={0,2,6,8,11,13,15,17}
def add(a,b):return a[0]+b[0],a[1]+b[1]
def ribbon(d,pts,widths,fill):
    # Tapered hand-inked silhouette between independently specified joints.
    left=[];right=[]
    for i,(p,w) in enumerate(zip(pts,widths)):
        a=pts[max(0,i-1)];b=pts[min(len(pts)-1,i+1)]
        vx,vy=b[0]-a[0],b[1]-a[1];q=math.hypot(vx,vy) or 1
        nx,ny=-vy/q*w,vx/q*w
        left.append((p[0]+nx,p[1]+ny));right.append((p[0]-nx,p[1]-ny))
    poly=left+right[::-1];d.polygon(poly,fill=fill);d.line(poly+[poly[0]],fill=(9,12,17),width=3)
    return left,right

def render(p,i):
    exp,beat,hip,sh,head,kl,kr,al,ar,el,er,hl,hr,ss,hs,bx,by,hem=p
    im=bg.convert('RGB').copy();d=ImageDraw.Draw(im)
    # Same unresolved distant placeholder, held throughout; no enemy action is invented.
    d.ellipse((671,1197,697,1222),fill=(20,29,38));d.polygon([(671,1219),(697,1219),(705,1257),(697,1275),(684,1251),(675,1275),(665,1258)],fill=(20,29,38))
    for ankle in [al,ar]:
        d.ellipse((ankle[0]-43,ankle[1]+17,ankle[0]+45,ankle[1]+34),fill=(9,15,22))
    lh=add(hip,(-40,hs));rh=add(hip,(40,-hs))
    for a,k,h,side in [(ar,kr,rh,1),(al,kl,lh,0)]:
        ribbon(d,[h,k,a],[38,30,21],(29,34,42) if side else (37,42,49))
        # Knee crease, thigh pocket and calf plane track the actual bent drawing.
        mid=((h[0]+k[0])/2,(h[1]+k[1])/2)
        d.polygon([add(mid,(-20,-20)),add(mid,(13,-17)),add(mid,(18,19)),add(mid,(-17,22))],fill=(43,48,54))
        d.line([add(k,(-19,-4)),add(k,(0,5)),add(k,(15,-2))],fill=(17,22,29),width=4)
        d.line([add(k,(-12,14)),add(a,(-10,-17))],fill=(53,57,63),width=3)
        # Heel rise and ankle pitch authored through knee/ankle relation, black sneakers.
        lift=max(0,1680-a[1]);toe=(a[0]+(23 if side else -25),a[1]+20)
        foot=[add(a,(-21,-12)),add(a,(19,-10)),add(toe,(20,0)),add(toe,(20,10)),add(a,(-30,25)),add(a,(-33,13))]
        # Toe pivot angle authored per drawing, not interpolated ankle translation.
        anglesL=[0,0,0,-12,-23,-28,-32,-24,-12,-4,0,0,0,0,0,0,0,0]
        anglesR=[0,0,-3,10,15,18,15,9,0,0,0,-12,-18,-12,-5,0,0,0]
        angle=math.radians((anglesR if side else anglesL)[i]);pivot=foot[3]
        def turn(q):
            x,y=q[0]-pivot[0],q[1]-pivot[1]
            return (pivot[0]+x*math.cos(angle)-y*math.sin(angle),pivot[1]+x*math.sin(angle)+y*math.cos(angle))
        d.polygon([turn(q) for q in foot],fill=(8,11,16))
        d.line([turn(foot[4]),turn(foot[3])],fill=(63,65,69),width=4)
    ls=add(sh,(-72,ss));rs=add(sh,(72,-ss))
    # Bent sleeves swing counter to legs. Hands remain covered, face never drawn.
    for s,e,h,col in [(rs,er,hr,(19,24,31)),(ls,el,hl,(31,36,43))]:
        ribbon(d,[s,e,h],[34,29,18],col)
        d.line([add(e,(-17,0)),add(e,(3,9)),add(e,(15,0))],fill=(51,55,61),width=3)
        d.ellipse((h[0]-18,h[1]-9,h[0]+17,h[1]+22),fill=(10,13,18))
    # Torso outline redrawn per pose: shoulder/hip opposing axes and hem drag.
    hemL=add(hip,(-83+hem,29));hemR=add(hip,(75+hem,21))
    contour=[add(ls,(-10,0)),add(sh,(-16,-25)),add(rs,(8,0)),add(rs,(19,90)),add(hip,(68,hs-25)),hemR,add(hip,(8+hem,34)),hemL,add(hip,(-76,-27)),add(ls,(-16,103))]
    d.polygon(contour,fill=(23,28,35));d.line(contour+[contour[0]],fill=(9,13,19),width=3)
    d.polygon([add(ls,(1,27)),add(sh,(-40,83)),add(hip,(-44,13)),hemL,add(hip,(-76,-27))],fill=(34,39,46))
    d.line([hemL,add(hip,(hem,24)),hemR],fill=(50,54,59),width=4)
    for off in [-48,47]:
        d.line([add(sh,(off,155)),add(hip,(off//2+hem,-5)),add(hip,(off+hem,12))],fill=(43,48,54),width=3)
    # Rectangular rigid blank bag: projection varies with shoulder twist; independent lag.
    center=add(sh,(bx,119+by));u=(56, -ss*.37);v=(0,82)
    tl=(center[0]-u[0],center[1]-u[1]-v[1]);tr=(center[0]+u[0],center[1]+u[1]-v[1]);br=(tr[0],tr[1]+164);bl=(tl[0],tl[1]+164)
    for s,t in [(ls,tl),(rs,tr)]:d.line([add(s,(13 if s==ls else -13,5)),t],fill=(55,58,62),width=13)
    d.polygon([add(tl,(-8,-8)),add(tr,(9,-8)),add(br,(9,7)),add(bl,(-8,7))],fill=(8,11,16))
    d.polygon([tl,tr,br,bl],fill=(32,36,42));d.polygon([tr,add(tr,(9,-8)),add(br,(9,7)),br],fill=(16,20,27))
    d.line([bl,tl,tr],fill=(62,65,69),width=3)
    # Hood is an enclosed rear silhouette, independently offset from the torso.
    hx,hy=head
    hood=[(hx-61,hy+53),(hx-65,hy+4),(hx-49,hy-51),(hx-22,hy-76),(hx+6,hy-88),(hx+36,hy-69),(hx+57,hy-34),(hx+65,hy+17),(hx+49,hy+60),(hx+8,hy+74),(hx-34,hy+67)]
    d.polygon(hood,fill=(29,34,42));d.line(hood+[hood[0]],fill=(9,13,19),width=3)
    d.polygon([(hx-61,hy+53),(hx-57,hy-4),(hx-35,hy-53),(hx+6,hy-88),(hx-11,hy-36),(hx-18,hy+19),(hx-8,hy+68),(hx-34,hy+67)],fill=(42,46,54))
    d.polygon([(hx+6,hy-88),(hx+36,hy-69),(hx+57,hy-34),(hx+65,hy+17),(hx+49,hy+60),(hx+8,hy+74),(hx+23,hy+11)],fill=(20,25,33))
    d.line([(hx-57,hy+54),(hx-16,hy+70),(hx+20,hy+70),(hx+49,hy+60)],fill=(56,60,65),width=3)
    return im
rows=[];frame=216
for i,p in enumerate(D):
    im=render(p,i); im.save(R/'keys'/f'D{i:02}_{p[1]}.png')
    for j in range(p[0]):
        out=R/'frames'/f'F{frame:03}.png';im.save(out)
        rows.append(dict(frame=frame,local=frame-216,drawing=f'D{i:02}',type='key' if i in KEYS else 'inbetween',exposure=p[0],beat=p[1],pelvis=str(p[2]),shoulder=str(p[3]),left_ankle=str(p[7]),right_ankle=str(p[8]),sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
        frame+=1
with (R/'exposure.csv').open('w') as f:
    w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
# Contact sheet includes full body and scene; no content crop in deliverable video.
board=Image.new('RGB',(1440,2250),(224,225,227));d=ImageDraw.Draw(board)
for i,p in enumerate(D):
    x=i%4*360;y=i//4*450
    im=render(p,i).crop((235,1020,820,1770)).resize((328,420))
    board.paste(im,(x+16,y+10));d.text((x+16,y+431),f'D{i:02} {p[1]} / {p[0]}f',fill=(15,20,30))
board.save(R/'drawing_board.png')
old=R.parent/'pilot15_S04_joined_DRAFT_20261013/video/S04_joined_F216-245_DRAFT_24fps.mp4'
def run(args): subprocess.run(args,check=True)
def enc(out,extra):
    run(['ffmpeg','-y','-v','error']+extra+['-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(R/'video'/out)])
enc('S04_drawn_DRAFT_24fps.mp4',['-framerate','24','-start_number','216','-i',str(R/'frames/F%03d.png'),'-vf','setsar=1','-frames:v','30'])
for speed,label in [(1,'normal'),(2,'half')]:
    filt=f'[0:v]setpts={speed}*(PTS-STARTPTS),scale=540:960,setsar=1[a];[1:v]setpts={speed}*(PTS-STARTPTS),scale=540:960,setsar=1[b];[a][b]hstack,fps=24[v]'
    enc(f'comparison_{label}.mp4',['-i',str(old),'-i',str(R/'video/S04_drawn_DRAFT_24fps.mp4'),'-filter_complex',filt,'-map','[v]'])
# Repeated viewing for the short beat: ordinary speed, no additional holds between loops.
run(['ffmpeg','-y','-v','error','-stream_loop','5','-i',str(R/'video/comparison_normal.mp4'),'-c','copy',str(R/'video/comparison_normal_6loops.mp4')])
checks={}
for p in sorted((R/'video').glob('*.mp4')):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
    s=info['streams'][0];checks[p.name]={k:s.get(k) for k in ['codec_name','pix_fmt','width','height','r_frame_rate','nb_read_frames','duration','sample_aspect_ratio','display_aspect_ratio']}
    run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'])
    checks[p.name]['decode']='PASS'
s=checks['S04_drawn_DRAFT_24fps.mp4'];assert (s['width'],s['height'],s['nb_read_frames'],s['r_frame_rate'])==(1080,1920,'30','24/1')
checks['drawings']=len(D);checks['exposure_total']=len(rows);checks['direction']='UNJUDGED: no continuous visual playback by agent';checks['motion_quality']='not inferred from automated tests'
(R/'verification/technical.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
