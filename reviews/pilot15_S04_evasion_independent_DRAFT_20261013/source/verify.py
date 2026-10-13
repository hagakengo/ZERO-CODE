"""Technical checks only; never an aesthetic approval. Run inside this Git history."""
from pathlib import Path
import subprocess,json,hashlib,csv
from PIL import Image
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
BASE='ff5600598c95c00f39674ddc3683ef26a863bd43'
def cmd(args): return subprocess.check_output(args,cwd=REPO,text=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
media=R/'video/S04_evasion_DRAFT_24fps.mp4'
probe=json.loads(cmd(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(media)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
decode=subprocess.run(['ffmpeg','-v','error','-i',str(media),'-f','null','-'],capture_output=True,text=True)
checks={'resolution':(v['width'],v['height'])==(1080,1920),'fps':v['r_frame_rate']=='24/1' and v['avg_frame_rate']=='24/1','frames':int(v['nb_read_frames'])==16,'duration':abs(float(v['duration'])-16/24)<1e-6,'codec':v['codec_name']=='h264' and v['pix_fmt']=='yuv420p','no_audio':all(s['codec_type']!='audio' for s in probe['streams']),'full_decode':decode.returncode==0 and not decode.stderr.strip()}
files=sorted((R/'frames').glob('F*.png')); hashes=[]
for p in files:
    with Image.open(p) as im:
        im.load(); assert im.size==(1080,1920)
    hashes.append(sha(p))
checks['png_count_and_read']=len(files)==16
checks['distinct_composited_drawings']=len(set(hashes))==16
rows=list(csv.DictReader((R/'exposure_sheet.csv').open()))
checks['pilot_frame_mapping']=[int(x['pilot_frame']) for x in rows]==list(range(230,246))
checks['local_frame_mapping']=[int(x['local_frame']) for x in rows]==list(range(16))
checks['support_right_foot_fixed']=len({(x['right_foot_dx'],x['right_foot_dy']) for x in rows})==1
checks['left_landing_locked']=len({(x['left_foot_dx'],x['left_foot_dy']) for x in rows[10:]})==1
checks['anticipation_drop']=float(rows[3]['root_dy'])>float(rows[0]['root_dy'])
checks['lateral_evasion']=float(rows[10]['root_dx'])<float(rows[3]['root_dx'])-100
checks['recovery']=float(rows[15]['root_dy'])<float(rows[10]['root_dy'])
checks['bag_inertia']=min(float(x['bag_lag_y']) for x in rows)<0 and max(float(x['bag_lag_x']) for x in rows)>10
checks['two_frame_character_holds']=all(rows[a]['drawing']==rows[b]['drawing'] for a,b in [(0,1),(12,13),(14,15)])
prior=REPO/'reviews/pilot15_S04_step_independent_DRAFT_20261013'
last=list(csv.DictReader((prior/'exposure_sheet.csv').open()))[-1]
fields=['root_dx','root_dy','right_foot_dx','right_foot_dy','bag_lag_y']
checks['F229_F230_pose_connection']=all(abs(float(rows[0][k])-float(last[k]))<1e-9 for k in fields)
# Static comparison is evidence only; rainfall advances by one frame.
from PIL import ImageDraw, ImageChops
board=Image.new('RGB',(1080,1000),(222,224,223)); d=ImageDraw.Draw(board)
for j,p in enumerate([prior/'frames/F013.png',R/'frames/F000.png']):
    board.paste(Image.open(p).resize((500,889)),(20+540*j,35))
    d.text((20+540*j,940),['prior F229 / L013','evasion F230 / L000'][j],fill=(25,30,35))
board.save(R/'verification/connection.png')
checks['same_background']=True # Source background prefix is checked byte for byte below.
old=(prior/'source/render_s04.py').read_text(); new=(R/'source/render_s04_evasion.py').read_text()
checks['same_background']=old[old.index('rng=random.Random'):old.index('def pose(n):')].split('# Independent continuation')[0].split('def ease')[0]==new[new.index('rng=random.Random'):new.index('def pose(n):')].split('# Independent continuation')[0].split('def ease')[0]
# Git blob comparisons cover every pre-existing tracked file, including all S01 assets.
protected=[]
for line in cmd(['git','ls-tree','-r',BASE]).splitlines():
    info,path=line.split('\t',1); mode,typ,blob=info.split()
    if typ!='blob': continue
    p=REPO/path
    actual=cmd(['git','hash-object','--',path]).strip() if p.exists() else None
    protected.append({'path':path,'baseline_blob':blob,'actual_blob':actual,'unchanged':actual==blob})
checks['all_protected_files_unchanged']=all(x['unchanged'] for x in protected)
status='PASS' if all(checks.values()) else 'FAIL'
(R/'verification/protected_files.json').write_text(json.dumps({'base':BASE,'count':len(protected),'all_unchanged':checks['all_protected_files_unchanged'],'files':protected},indent=2))
(R/'verification/technical_checks.json').write_text(json.dumps({'status':status,'checks':checks,'unique_composited_drawings':len(set(hashes)),'decode_stderr':decode.stderr,'ffprobe':probe,'direction_status':'UNDETERMINED: no real-time continuous viewing or phone review performed','main_integration':False},indent=2))
print(json.dumps({'status':status,'checks':checks,'protected_count':len(protected)},indent=2))
assert status=='PASS'
