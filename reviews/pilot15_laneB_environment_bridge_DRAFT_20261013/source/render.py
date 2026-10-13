"""Independent procedural environment continuity comparison. No external assets.
Run python3 source/render.py. Source sources are read only, never executed in place.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,csv,subprocess,hashlib,math
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
for d in ['frames','video','verification']: (R/d).mkdir(exist_ok=True)
nss=[]
for shot in ['S01','S02']:
    p=REPO/f'reviews/pilot15_{shot}_independent_DRAFT_20261013/source/render_{shot.lower()}.py'
    src=p.read_text().split('\nrecords=[]')[0]
    # Suppress old precipitation only. Rendering and all pose math are preserved verbatim.
    src=src.replace('im=Image.alpha_composite(im,rainlayer)','pass # precipitation isolated below')
    ns={'__file__':str(R/'source'/f'{shot}.py')}; exec(compile(src,str(p),'exec'),ns)
    nss.append(ns)
assert nss[0]['rain']==nss[1]['rain']
records=[]; differences=[]
for g in range(144):
    s=g//72; l=g%72; im,pose=nss[s]['render'](l)
    base=im.copy(); layer=Image.new('RGBA',im.size); d=ImageDraw.Draw(layer)
    # Single rain clock on threes across both shots; conservative opaque holdout
    # excludes the full protagonist/feet and temporary enemy silhouette.
    tick=g//3
    def protected(x,y): return (325<=x<=650 and 1030<=y<=1730) or (650<=x<=720 and 1160<=y<=1300)
    for x,z,length in nss[0]['rain']:
        yy=(z+tick*21)%2020-50; xx=(x-tick*3)%1150-35
        if not any(protected(xx-a,yy+b) for a in [0,4] for b in [0,length]):
            d.line((xx,yy,xx-4,yy+length),fill=(112,137,154,45),width=1)
    # Quiet wet-street rings, away from actors. No flash, symbols or new event.
    for x,y,offset in [(175,1580,0),(870,1750,9),(810,1430,17)]:
        age=(tick+offset)%24
        if age<15:
            radius=3+age*1.8; alpha=int(28*(1-age/15))
            d.ellipse((x-radius,y-radius/5,x+radius,y+radius/5),outline=(91,115,132,alpha),width=1)
    im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
    assert im.crop((325,1030,651,1731)).tobytes()==base.crop((325,1030,651,1731)).tobytes()
    assert im.crop((650,1160,721,1301)).tobytes()==base.crop((650,1160,721,1301)).tobytes()
    im.save(R/'frames'/f'F{g:03}.png')
    records.append(dict(pilot_frame=g,shot=f'S0{s+1}',local_frame=l,rain_drawing=tick,rain_hold=3,character_pose=pose))
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(R/'frames/F%03d.png'),'-frames:v','144','-vf','setsar=1','-c:v','libx264','-crf','17','-preset','medium','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(R/'video/S01_S02_environment_bridge_DRAFT_24fps.mp4')],check=True)
(R/'verification/exposure_sheet.json').write_text(json.dumps(records,indent=2))
with (R/'exposure_sheet.csv').open('w') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['pilot_frame','shot','local_frame','character_exposure','rain_drawing','rain_hold'])
    for q in records:w.writerow([q['pilot_frame'],q['shot'],q['local_frame'],3 if q['pilot_frame']<72 else 2,q['rain_drawing'],3])
board=Image.new('RGB',(1080,1040),(225,225,219)); d=ImageDraw.Draw(board)
for j,g in enumerate([0,36,69,71,72,74,108,143]):
    x=15+j%4*270;y=20+j//4*510
    board.paste(Image.open(R/'frames'/f'F{g:03}.png').resize((243,432)),(x,y));d.text((x,y+440),f'F{g:03} rain D{g//3:02} DRAFT',fill=(20,25,30))
board.save(R/'keyframes.png')
# Boundary original/improved, factual image comparison only.
board=Image.new('RGB',(1080,560),(225,225,219)); d=ImageDraw.Draw(board)
for j,(shot,l,g) in enumerate([('S01',71,71),('S02',0,72)]):
    old=REPO/f'reviews/pilot15_{shot}_independent_DRAFT_20261013/frames/F{l:03}.png'
    for k,p in enumerate([old,R/'frames'/f'F{g:03}.png']):
        x=15+(j*2+k)*270; board.paste(Image.open(p).resize((243,432)),(x,40));d.text((x,10),f'F{g:03} '+('existing' if k==0 else 'environment DRAFT'),fill=(20,25,30))
board.save(R/'boundary_comparison.png')
(R/'verification/render_checks.json').write_text(json.dumps(dict(character_holdouts_exact_match_frames=144,enemy_holdouts_exact_match_frames=144,source_pose_math='verbatim; rain compositing disabled only',rain_tick_F071=23,rain_tick_F072=24,previous_S02_start_tick=23,normal_speed_visual_review='NOT PERFORMED'),indent=2))
print('Rendered 144 frames; character and enemy holdouts exact for every frame')
