"""ZERO CODE anonymous passer-by, DRAFT/HOLD; no character A/B identity.
Hand-shaped layered cel silhouette. draw_pedestrian(t) -> transparent 240x420 RGBA.
Feet baseline y=404. World translation must use pedestrian_motion(t)['travel_px']
(multiplier final figure height / 360), so walking feet and screen travel agree.
First flash 1.04s, response 1.14s, braking 1.14–1.58, upward head turn 1.30–1.75.
All shapes and timings editable, no external materials or generative services.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw
W,H,S=240,420,3

def ease(x):
    x=max(0.,min(1.,x)); return x*x*(3-2*x)

def pedestrian_motion(t):
    t=max(0.,min(3.,float(t)))
    start,end=1.14,1.58
    if t<=start: travel=165*t; speed=1.
    elif t<end:
        u=(t-start)/(end-start); travel=165*(start+(end-start)*(u-u*u/2)); speed=1-u
    else: travel=165*(start+(end-start)/2); speed=0.
    # accumulated gait phase ends with legs almost below hips rather than a frozen stride
    phase=travel/165*2*math.pi*1.42
    settle=ease((t-1.14)/.44)
    return dict(travel_px=travel,speed=speed,phase=phase,settle=settle,look=ease((t-1.28)/.46))

def draw_pedestrian(t):
    m=pedestrian_motion(t); p=m['phase']; moving=1-m['settle']; look=m['look']
    im=Image.new('RGBA',(W*S,H*S)); d=ImageDraw.Draw(im)
    ink=(8,12,18,255); cloth=(17,24,33,255); lit=(27,37,47,255); edge=(39,48,57,255)
    def poly(pts,fill): d.polygon([(round(x*S),round(y*S)) for x,y in pts],fill=fill)
    def ellipse(box,fill): d.ellipse(tuple(round(v*S) for v in box),fill=fill)
    def line(pts,fill,width=1): d.line([(round(x*S),round(y*S)) for x,y in pts],fill=fill,width=max(1,round(width*S)),joint='curve')
    bob=abs(math.sin(p))*2.4*moving; lean=2*moving-2*look
    # trouser legs: distinct cloth masses, knees, ankles, and shoe soles
    def leg(side,back=False):
        swing=math.sin(p+(math.pi if side else 0))*moving
        hipx=116+(9 if side else -8)+lean
        ankx=116+(7 if side else -6)+swing*52
        lift=max(0,-math.cos(p+(math.pi if side else 0)))*10*moving
        knee=(hipx*.45+ankx*.55+max(0,-swing)*10,338-lift*.45)
        ankle=(ankx,394-lift)
        color=ink if back else cloth
        poly([(hipx-12,281+bob),(hipx+13,282+bob),(knee[0]+10,knee[1]),(ankle[0]+7,ankle[1]),(ankle[0]-7,ankle[1]),(knee[0]-10,knee[1]+1)],color)
        poly([(ankx-8,389-lift),(ankx+8,390-lift),(ankx+15,397-lift),(ankx+22,398-lift),(ankx+21,404-lift),(ankx-9,404-lift),(ankx-11,399-lift)],ink)
        if not back:
            line([(hipx+8,300),(knee[0]+6,knee[1]-3),(ankx+4,387-lift)],lit,1.4)
            line([(ankx-5,402-lift),(ankx+19,402-lift)],lit,1)
    leg(1,True)
    # far sleeve partly hidden by coat, rounded gloved hand
    sw=math.sin(p)*moving*12
    poly([(126+lean,163+bob),(140+lean,169+bob),(145-sw*.5,212+bob),(136-sw,251),(128-sw,250),(132-sw*.5,211)],ink)
    ellipse((125-sw,246,138-sw,262),ink)
    leg(0)
    # coat collar, shoulder slope, asymmetric hem: anonymous rain commuter
    poly([(111+lean,146+bob),(128+lean,147+bob),(142+lean,166+bob),(141+lean,215+bob),(147+lean,282+bob),(131+lean,290+bob),(109+lean,287+bob),(92+lean,282+bob),(100+lean,224+bob),(94+lean,180+bob),(99+lean,159+bob)],ink)
    poly([(111+lean,156+bob),(130+lean,153+bob),(137+lean,172+bob),(133+lean,231+bob),(141+lean,279+bob),(127+lean,283+bob),(116+lean,277+bob),(117+lean,208+bob)],cloth)
    poly([(103+lean,160+bob),(111+lean,156+bob),(115+lean,180+bob),(108+lean,211+bob),(101+lean,250+bob),(97+lean,279+bob),(92+lean,280+bob),(100+lean,218+bob),(95+lean,181+bob)],lit)
    line([(120+lean,170+bob),(119+lean,237+bob),(125+lean,278+bob)],lit,1.3)
    line([(127+lean,240+bob),(136+lean,239+bob)],edge,1)
    # near sleeve swings opposite the forward leg; reaction bends elbow slightly
    shoulder=(101+lean,171+bob); elbow=(96+sw*.45+look*4,216+bob-look*7); wrist=(102+sw+look*18,254-look*26)
    poly([(shoulder[0]-7,shoulder[1]-6),(shoulder[0]+7,shoulder[1]+1),(elbow[0]+8,elbow[1]-2),(wrist[0]+6,wrist[1]-4),(wrist[0]+5,wrist[1]+7),(wrist[0]-5,wrist[1]+8),(elbow[0]-8,elbow[1]+3)],cloth)
    line([(shoulder[0]-6,shoulder[1]+2),(elbow[0]-5,elbow[1]),(wrist[0]-4,wrist[1])],lit,1.6)
    ellipse((wrist[0]-5,wrist[1]+2,wrist[0]+7,wrist[1]+17),ink)
    # hood/head continuous outline, obscured face. Upward profile change reads as attention.
    body_d=d
    head=Image.new('RGBA',(W*S,H*S)); d=ImageDraw.Draw(head)
    hx=116+lean-look*2; hy=121+bob-look*5
    poly([(hx-15,hy+18),(hx-19,hy+2),(hx-17,hy-17),(hx-8,hy-29),(hx+8,hy-30),(hx+21-look*5,hy-22),(hx+25-look*8,hy-9),(hx+28-look*7,hy-2),(hx+23-look*6,hy+4),(hx+22-look*8,hy+17),(hx+12,hy+28),(hx-2,hy+31)],ink)
    poly([(hx-15,hy-13),(hx-7,hy-25),(hx+7,hy-25),(hx+17,hy-18),(hx+12,hy-10),(hx+9,hy+12),(hx,hy+25),(hx-11,hy+17),(hx-15,hy+3)],cloth)
    line([(hx-15,hy-9),(hx-13,hy+8),(hx-4,hy+21)],lit,1.5)
    poly([(hx-7,hy+27),(hx+10,hy+23),(134+lean,153+bob),(120+lean,164+bob),(106+lean,152+bob)],ink)
    line([(hx+1,hy+29),(120+lean,157+bob),(131+lean,152+bob)],lit,1.4)
    head=head.rotate(15*look, resample=Image.Resampling.BICUBIC, center=((120+lean)*S,(154+bob)*S))
    im.alpha_composite(head)
    return im.resize((W,H),Image.Resampling.LANCZOS)

if __name__=='__main__':
    out=Path(__file__).resolve().parents[1]/'pedestrian'; out.mkdir(parents=True,exist_ok=True)
    for f in range(72): draw_pedestrian(f/24).save(out/f'{f:03d}.png')
    sheet=Image.new('RGB',(240*6,420),(65,75,85))
    for i,t in enumerate([0,.33,.66,1.15,1.5,2.5]): sheet.paste(draw_pedestrian(t),(240*i,0),draw_pedestrian(t))
    sheet.save(out/'contact_DRAFT_HOLD.jpg')
