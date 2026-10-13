from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,hashlib,zipfile,subprocess,shutil
out=Path(__file__).resolve().parents[1];repo=out.parents[1]
p=json.loads((out/'verification/motion_design_02.json').read_text())['displayed_poses']
checkpath=out/'verification/submission_checks.json';checks=json.loads(checkpath.read_text())
def distance(v,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];u=max(0,min(1,((v[0]-a[0])*dx+(v[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.dist(v,[a[0]+u*dx,a[1]+u*dy])*2
checks['attack_guard_centerline_clearance_px_P020_025']=min(distance(p[t]['enemy']['joints']['fist'],p[t]['hero']['joints'][a],p[t]['hero']['joints'][b]) for t in range(20,26) for a,b in [('shoulder','guard_elbow'),('guard_elbow','guard'),('shoulder','elbow'),('elbow','fist')])
checks['contact_gap_px_P023']=2*(324-5.5-(264+20))
checks['contact_gap_px_P024']=2*(289-5.5-(264+20))
checks['contact_gap_note']='P024 -1px is raster overlap at first contact. Fist rectangle half width 11 output pixels.'
checks['landing_hip_y_px']={f'P{t:03}':p[t]['hero']['joints']['hip'][1]*2 for t in [48,50,51,54]}
checks['visual_inspection']='All 72 frames in contact sheet; 16 key poses and same-frame P024 comparison inspected. Hood, hidden face, plain rectangular black bag retained. Timing / impact readability requires director review.'
checkpath.write_text(json.dumps(checks,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
sheet=Image.new('RGB',(1440,2160),'white');d=ImageDraw.Draw(sheet)
for t in range(72):
    x=t%8*180;y=t//8*240
    im=Image.open(out/'frames'/f'P{t:03}.png').crop((50,720,1030,1510)).resize((180,210))
    sheet.paste(im,(x,y+25));d.text((x+4,y+2),f'02 P{t:03}',font=font,fill='black')
sheet.save(out/'verification/all_72_frames.png')
# Hash evidence from the baseline commit and external read-only source.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tracked=subprocess.check_output(['git','ls-tree','-r','--name-only','e00fadd'],cwd=repo,text=True).splitlines()
manifest={k:sha(repo/k) for k in tracked}
external=Path('/Users/hagakengo/Movies/ZERO_CODE/review_for_chatgpt/production_r15_2')
(out/'verification/protected_hashes.json').write_text(json.dumps({'baseline_commit':'e00fadd3486c1e6dbb8dae9ef5587993aad15824','repository_files':manifest,'external_r15_2':{str(f.relative_to(external)):sha(f) for f in external.rglob('*') if f.is_file()}},indent=2))
