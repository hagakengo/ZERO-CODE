from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import subprocess,json,csv,hashlib,io,statistics
R=Path(__file__).resolve().parents[1]; repo=R.parents[1]
A='54e200c50053c9746c553c66b742de092809fe52';B='1633364fd9d0f733f02ee42f44ac3511d4abd419';C='b09937fe98558d419e18264db1874f02ee80226d'
for d in ['images','verification']: (R/d).mkdir(exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
def blob(c,p):return git('show',c+':'+p)
def sha(b):return hashlib.sha256(b).hexdigest()
def frame(name,n):
    folder={'S01':'pilot15_S01_independent_DRAFT_20261013','S02':'pilot15_S02_independent_DRAFT_20261013','S03':'pilot15_S03_independent_DRAFT_20261013','S04':'pilot15_S04_joined_DRAFT_20261013','B':'pilot15_laneB_environment_bridge_DRAFT_20261013'}[name]
    return Image.open(io.BytesIO(blob(B if name=='B' else A,f'reviews/{folder}/frames/F{n:03}.png'))).convert('RGB')
sources=[('S01',0,72,'pilot15_S01_independent_DRAFT_20261013','S01_silence_DRAFT_24fps.mp4'),('S02',72,72,'pilot15_S02_independent_DRAFT_20261013','S02_stance_step_DRAFT_24fps.mp4'),('S03',144,72,'pilot15_S03_independent_DRAFT_20261013','S03_pre_dash_tension_DRAFT_24fps.mp4'),('S04',216,30,'pilot15_S04_joined_DRAFT_20261013','S04_joined_F216-245_DRAFT_24fps.mp4'),('B',0,144,'pilot15_laneB_environment_bridge_DRAFT_20261013','S01_S02_environment_bridge_DRAFT_24fps.mp4')]
probes=[];metrics=[]
for name,start,count,folder,movie in sources:
    data=blob(B if name=='B' else A,f'reviews/{folder}/video/{movie}');p=R/'verification'/('_'+name+'.mp4');p.write_bytes(data)
    pr=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(p)]));s=pr['streams'][0]
    dec=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],capture_output=True)
    probes.append(dict(source=name,sha256=sha(data),resolution=[s['width'],s['height']],fps=s['avg_frame_rate'],count=int(s['nb_read_frames']),expected_count=count,full_decode=dec.returncode==0 and not dec.stderr,technical_pass=s['width']==1080 and s['height']==1920 and s['avg_frame_rate']=='24/1' and int(s['nb_read_frames'])==count and dec.returncode==0));p.unlink()
    prev=None
    for n in range(count):
        im=frame(name,n); small=im.resize((270,480));a=small.crop((0,0,270,220));b=small.crop((70,255,170,445))
        if prev:
            delta=ImageChops.difference(small,prev[0]); env=ImageChops.difference(a,prev[1]); char=ImageChops.difference(b,prev[2])
            metrics.append(dict(source=name,pilot_frame=start+n,mean_abs_rgb=round(statistics.mean(ImageStat.Stat(delta).mean),6),environment_top_mean_abs_rgb=round(statistics.mean(ImageStat.Stat(env).mean),6),character_roi_mean_abs_rgb=round(statistics.mean(ImageStat.Stat(char).mean),6)))
        prev=(small,a,b)
with (R/'verification/frame_differences.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=metrics[0]);w.writeheader();w.writerows(metrics)
(R/'verification/media_checks.json').write_text(json.dumps(probes,indent=2));assert all(p['technical_pass'] for p in probes)
# Human-readable static comparison sheets. No re-timing or sequence integration.
def sheet(file,items,cols=4,crop=None):
    tw,th=(270,480) if crop is None else (300,390);out=Image.new('RGB',(tw*cols,(th+34)*((len(items)+cols-1)//cols)),(238,238,238));d=ImageDraw.Draw(out)
    for i,(name,n,label) in enumerate(items):
        im=frame(name,n)
        if crop:im=im.crop(crop)
        im.thumbnail((tw,th));x=(i%cols)*tw;y=(i//cols)*(th+34);out.paste(im,(x,y+34));d.text((x+7,y+10),label,fill=(0,0,0))
    out.save(R/'images'/file)
sheet('shot_boundaries.png',[('S01',71,'S01 F071'),('S02',0,'S02 F072'),('S02',71,'S02 F143'),('S03',0,'S03 F144'),('S03',71,'S03 F215'),('S04',0,'S04 F216'),('S04',13,'S04 F229'),('S04',14,'S04 F230')])
sheet('S04_all_30_frames.png',[('S04',i,f'F{216+i}') for i in range(30)],6)
sheet('S04_contact_bag_detail.png',[('S04',i,f'F{216+i}') for i in [0,3,7,11,13,14,17,20,24,25,27,29]],4,(320,1030,720,1610))
sheet('environment_boundary_comparison.png',[('S01',69,'OLD F069'),('S01',71,'OLD F071'),('S02',0,'OLD F072'),('S02',2,'OLD F074'),('B',69,'NEW F069'),('B',71,'NEW F071'),('B',72,'NEW F072'),('B',74,'NEW F074')])
# Compare every pre-existing blob to baseline A, including original 701 subset.
protected=[]
for p in git('ls-tree','-r','--name-only',A).decode().splitlines():
    protected.append(dict(path=p,unchanged=blob(A,p)==(repo/p).read_bytes()))
(R/'verification/protected_files.json').write_text(json.dumps(dict(base=A,count=len(protected),all_unchanged=all(x['unchanged'] for x in protected),files=protected),indent=2));assert all(x['unchanged'] for x in protected)
(R/'verification/provenance.json').write_text(json.dumps(dict(A=A,B=B,C=C,method='git objects pinned; ffprobe full count; ffmpeg full decode; Pillow downsampled ROI mean absolute RGB deltas. Metrics do not prove perceptual quality.',normal_speed_viewing=False,direction_status='UNDETERMINED'),indent=2))
print(json.dumps({'technical':'PASS','videos':len(probes),'frame_delta_rows':len(metrics),'protected':len(protected)}))
rows=[]
for folder in ['pilot15_S04_step_independent_DRAFT_20261013','pilot15_S04_evasion_independent_DRAFT_20261013']:
    for row in csv.DictReader((repo/'reviews'/folder/'exposure_sheet.csv').open()):
        rows.append({k:row.get(k,'') for k in ['pilot_frame','drawing','beat','root_dx','root_dy','right_foot_dx','right_foot_dy','left_foot_dx','left_foot_dy','bag_lag_y','bag_lag_x']})
with (R/'verification/S04_pose_audit.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
