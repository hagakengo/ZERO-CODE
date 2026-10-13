from PIL import Image, ImageDraw, ImageFilter
import math, random
W,H=1080,1920
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
