"""Technical checks only; never an aesthetic approval. Run inside this Git history."""
from pathlib import Path
import subprocess,json,hashlib,csv
from PIL import Image
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
BASE='fc3fdec22f114aa569e0e0da2bb676f7c35ce4d1'
def cmd(args): return subprocess.check_output(args,cwd=REPO,text=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
media=R/'video/S04_combat_step_DRAFT_24fps.mp4'
probe=json.loads(cmd(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(media)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
decode=subprocess.run(['ffmpeg','-v','error','-i',str(media),'-f','null','-'],capture_output=True,text=True)
checks={'resolution':(v['width'],v['height'])==(1080,1920),'fps':v['r_frame_rate']=='24/1' and v['avg_frame_rate']=='24/1','frames':int(v['nb_read_frames'])==14,'duration':abs(float(v['duration'])-14/24)<1e-6,'codec':v['codec_name']=='h264' and v['pix_fmt']=='yuv420p','no_audio':all(s['codec_type']!='audio' for s in probe['streams']),'full_decode':decode.returncode==0 and not decode.stderr.strip()}
files=sorted((R/'frames').glob('F*.png')); hashes=[]
for p in files:
    with Image.open(p) as im:
        im.load(); assert im.size==(1080,1920)
    hashes.append(sha(p))
checks['png_count_and_read']=len(files)==14
checks['distinct_composited_drawings']=len(set(hashes))==14
rows=list(csv.DictReader((R/'exposure_sheet.csv').open()))
checks['pilot_frame_mapping']=[int(x['pilot_frame']) for x in rows]==list(range(216,230))
checks['support_foot_fixed']=all(x['left_foot_fixed']=='True' for x in rows)
checks['landing_locked']=len({(x['right_foot_dx'],x['right_foot_dy']) for x in rows[11:]})==1
checks['preload_then_absorb']=float(rows[3]['root_dy'])>float(rows[0]['root_dy']) and float(rows[13]['root_dy'])>float(rows[11]['root_dy'])
checks['right_foot_travels']=float(rows[11]['right_foot_dx'])>float(rows[3]['right_foot_dx'])
checks['s03_root_connection']=(float(rows[0]['root_dx']),float(rows[0]['root_dy']))==(13.,19.)
checks['one_frame_exposures']=all(int(x['exposure'])==1 for x in rows)
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
