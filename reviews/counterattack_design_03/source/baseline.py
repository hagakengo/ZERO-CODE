from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math,json,copy,subprocess,hashlib,zipfile,shutil
GROUND=734.0
def ik(a, b, facing):
    l, m = 112., 110.
    dx, dy = b[0]-a[0], b[1]-a[1]
    dist = math.hypot(dx, dy)
    assert abs(l-m) < dist < l+m, (a,b,dist)
    q = (l*l-m*m+dist*dist)/(2*dist)
    h = math.sqrt(l*l-q*q)
    return [a[0]+dx/dist*q+facing*dy/dist*h,
            a[1]+dy/dist*q-facing*dx/dist*h]

def shoe(ankle, face, angle=0):
    # Neutral sole: heel -10, toe +18 in anatomical facing direction.
    # All values are half-resolution camera coordinates, not world distances.
    v = [math.cos(angle)*face, math.sin(angle)*face]
    n = [-v[1]*face, v[0]*face]
    # n is the downward sole normal for either facing direction.
    heel = [ankle[0]-v[0]*10+n[0]*6, ankle[1]-v[1]*10+n[1]*6]
    toe = [heel[0]+v[0]*28, heel[1]+v[1]*28]
    return dict(ankle=list(ankle), heel=heel, toe=toe, angle=angle)

def mass_proxy(q):
    j = q['joints']; h=j['hip']; s=j['shoulder']
    segs=[(h,s,.48),(s,j['head'],.08)]
    for side in ['L','R']:
        segs += [(j[side+'_hip'],j[side+'_knee'],.10),
                 (j[side+'_knee'],j[side+'_ankle'],.06)]
    segs += [(s,j['fist'],.04),(s,j['guard'],.04)]
    return sum((a[0]+b[0])*.5*w for a,b,w in segs)/sum(w for a,b,w in segs)

def lerp(keys,t):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=t<=b:
            u=(t-a)/(b-a);s=u*u*(3-2*u)
            return x+(y-x)*s
    return keys[0][1] if t<keys[0][0] else keys[-1][1]

def step(t,start,end,x0,x1,height):
    if t<=start:return [x0,728]
    if t>=end:return [x1,728]
    u=(t-start)/(end-start)
    return [x0+(x1-x0)*(u*u*(3-2*u)),728-height*math.sin(math.pi*u)]

def arm(a,b,face):
    dx,dy=b[0]-a[0],b[1]-a[1];dist=math.hypot(dx,dy)
    assert 0<dist<106,(a,b,dist)
    h=math.sqrt(53*53-dist*dist/4)
    return [a[0]+dx/2-face*dy/dist*h,a[1]+dy/2+face*dx/dist*h]

def phase(t):
    if t<16:return 'PREPARE'
    if t<24:return 'ACCELERATE'
    if t==24:return 'CONTACT / DESIGN'
    if t==25:return 'COMPRESSION / DESIGN'
    if t<36:return 'REACTION'
    if t<56:return 'RETREAT / STEP'
    return 'RECOVER'

def pose(t):
    p=copy.deepcopy(base);p['proposal_frame']=t;p['phase']=phase(t)
    for who in ['hero','enemy']:
        q=p[who];j=q['joints'];face=q['facing']
        if who=='enemy':
            hx=lerp([(0,488),(12,482),(16,450),(20,390),(24,366),(30,366),(40,382),(71,382)],t)
            hy=lerp([(0,560),(12,565),(24,552),(30,554),(48,555),(71,552)],t)
            lean=lerp([(0,8),(12,5),(24,-14),(30,-12),(48,-4),(71,-4)],t)
            feet={'L':shoe([472,728],face),'R':shoe(step(t,4,12,397,330,30),face)}
        else:
            hx=lerp([(0,264),(16,264),(24,256),(25,254),(30,240),(36,185),(40,156),(50,156),(60,215),(71,220)],t)
            hy=lerp([(0,548),(24,550),(25,558),(30,562),(40,570),(50,565),(60,550),(71,550)],t)
            lean=lerp([(0,base['hero']['joints']['shoulder'][0]-264),(24,0),(25,-9),(30,-16),(40,-2),(50,4),(60,0),(71,0)],t)
            feet={'R':shoe([160,728],face),'L':shoe(step(t,40,50,304,240,36),face)}
        h=[hx,hy];s=[hx+lean,hy-112]
        j['hip']=h;j['shoulder']=s;j['head']=[s[0],s[1]-35]
        for side,v in feet.items():
            a=[hx+(4 if side=='L' else -4),hy]
            j[side+'_hip']=a;j[side+'_ankle']=v['ankle'];j[side+'_knee']=ik(a,v['ankle'],face)
        q['shoes']=feet;q['feet']={k:v['ankle'] for k,v in feet.items()}
        q['contacts']=[k for k,v in feet.items() if abs(v['heel'][1]-734)<1e-6]
        # Default guarded pose; attack targets are assigned below, after both bodies exist.
        u=min(t/12,1);u=u*u*(3-2*u)
        original=base[who]['joints'];original_s=original['shoulder']
        j['guard']=[s[n]+(original['guard'][n]-original_s[n])*(1-u)+[face*24,4][n]*u for n in [0,1]]
        j['guard_elbow']=arm(s,j['guard'],-face)
        j['fist']=[s[n]+(original['fist'][n]-original_s[n])*(1-u)+[face*35,30][n]*u for n in [0,1]]
        j['elbow']=arm([s[0]+face*7,s[1]+8],j['fist'],-face)
    q=p['enemy'];j=q['joints'];s=j['shoulder'];h=p['hero']['joints']['hip']
    if t<16:
        original=base['enemy']['joints'];offset=[original['fist'][n]-original['shoulder'][n] for n in [0,1]]
        target=[s[0]+lerp([(0,offset[0]),(12,12),(16,12)],t),s[1]+lerp([(0,offset[1]),(16,24)],t)]
    elif t<24:
        u=((t-16)/8)**2
        target=[(s[0]+12)*(1-u)+(h[0]+18)*u,(s[1]+24)*(1-u)+(h[1]-70)*u]
    elif t<=25:target=[h[0]+18,h[1]-70]
    else:
        reach=lerp([(26,90),(30,75),(40,38),(71,35)],t)
        target=[s[0]-reach,s[1]+42]
    j['fist']=target;j['elbow']=arm([s[0]-7,s[1]+8],target,1)
    for who in ['hero','enemy']:
        q=p[who];q['com_x']=mass_proxy(q)
        pts=[v[k][0] for v in q['shoes'].values() for k in ['heel','toe'] if abs(v[k][1]-734)<1e-6]
        q['support_interval']=[min(pts),max(pts)];q['proxy_inside']=min(pts)<=q['com_x']<=max(pts)
    return p

def render(p):
    im=Image.new('RGB',(1080,1920),(231,229,220));d=ImageDraw.Draw(im)
    pt=lambda p:tuple(round(v*2) for v in p)
    def line(a,b,c,w=3):d.line([pt(a),pt(b)],fill=c,width=w*2)
    def limb(a,b,c,w):
        dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);nx=-dy/l*w;ny=dx/l*w
        d.polygon([pt(x) for x in [(a[0]+nx,a[1]+ny),(b[0]+nx*.65,b[1]+ny*.65),(b[0]-nx*.65,b[1]-ny*.65),(a[0]-nx,a[1]-ny)]],fill=c)
    line([40,734],[510,734],(151,152,145),1)
    for who in ['enemy','hero']:
        q=p[who];j=q['joints'];s=j['shoulder'];h=j['hip'];head=j['head'];face=q['facing'];c=(33,37,40) if who=='hero' else (158,167,169)
        for side in ['R','L']:
            a,k,f=[j[side+n] for n in ['_hip','_knee','_ankle']]
            limb(a,k,c,11);limb(k,f,c,9)
            col=(37,128,166) if side=='L' else (215,128,54)
            line(a,k,col,2);line(k,f,col,2)
            v=q['shoes'][side];line(v['heel'],v['toe'],c,6)
            for tag in ['heel','toe']:
                point=v[tag]
                if abs(point[1]-734)<1e-6:line([point[0]-4,738],[point[0]+4,738],(30,145,80),2)
        if who=='hero':
            # Plain rigid backpack in the torso's local coordinate basis.
            dx,dy=s[0]-h[0],s[1]-h[1];l=math.hypot(dx,dy);up=[dx/l,dy/l];back=[dy/l,-dx/l]
            anchor=[h[0]+back[0]*24,h[1]+back[1]*24-8]
            d.polygon([pt([anchor[0]+up[0]*a+back[0]*b,anchor[1]+up[1]*a+back[1]*b]) for a,b in [(0,0),(0,24),(78,24),(78,0)]],fill=(7,9,11))
        d.polygon([pt(x) for x in [[s[0]-20,s[1]],[s[0]+20,s[1]],[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]]],fill=c)
        if who=='hero':line([s[0]-12,s[1]+8],[h[0]-10,h[1]-8],(13,16,18),3)
        armroot=[s[0]+face*7,s[1]+8]
        limb(armroot,j['elbow'],c,8)
        for a,b in [('shoulder','guard_elbow'),('guard_elbow','guard'),('elbow','fist')]:limb(j[a],j[b],c,8)
        for name in ['guard','fist']:
            x,y=pt(j[name]);d.rectangle([x-11,y-11,x+11,y+11],fill=c)
        limb(s,[head[0],head[1]+12],c,7)
        x,y=head
        if who=='hero':
            d.polygon([pt(v) for v in [(x-22,y+20),(x-25,y-9),(x-12,y-30),(x+10,y-30),(x+23,y-8),(x+19,y+20)]],fill=(24,27,30))
            d.polygon([pt(v) for v in [(x+5,y-17),(x+20,y-8),(x+16,y+13),(x+4,y+13)]],fill=(0,1,2))
        else:
            x,y=pt(head);d.ellipse([x-26,y-40,x+26,y+31],fill=c)
        line([q['com_x'],545],[q['com_x'],734],(180,57,80),1)
    t=p['proposal_frame']
    d.text((55,60),f'ZERO CODE / COUNTERATTACK DESIGN / P{t:03}',font=font,fill=(55,60,62))
    d.text((55,104),f'{t/24:.3f}s / {p["phase"]} / '+('1-frame' if 20<=t<=29 else '2-frame'),font=small,fill=(55,60,62))
    d.text((55,148),'PROPOSAL ONLY / provisional opponent / mass proxy',font=small,fill=(55,60,62))
    return im