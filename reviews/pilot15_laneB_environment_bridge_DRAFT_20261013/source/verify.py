from pathlib import Path
from PIL import Image
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]; BASE='f12ce0246ad152dbce62873d3893dde3c0e87745'
video=R/'video/S01_S02_environment_bridge_DRAFT_24fps.mp4'
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]));s=p['streams'][0]
assert (s['width'],s['height'],s['r_frame_rate'],s['nb_read_frames'])==(1080,1920,'24/1','144')
assert s['sample_aspect_ratio']=='1:1' and s['display_aspect_ratio']=='9:16'
assert abs(float(p['format']['duration'])-6)<.001
assert len(p['streams'])==1
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
frames=sorted((R/'frames').glob('F*.png'));assert len(frames)==144
for f in frames:
    with Image.open(f) as im: assert im.size==(1080,1920);im.verify()
records=json.loads((R/'verification/exposure_sheet.json').read_text())
for shot in ['S01','S02']:
    old=json.loads((REPO/f'reviews/pilot15_{shot}_independent_DRAFT_20261013/verification/exposure_sheet.json').read_text())
    offset=0 if shot=='S01' else 72
    for i,q in enumerate(old):assert records[offset+i]['character_pose']==q
files=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',BASE],text=True).splitlines()
changed=[]
for f in files:
    original=subprocess.check_output(['git','-C',str(REPO),'rev-parse',BASE+':'+f],text=True).strip()
    actual=subprocess.check_output(['git','-C',str(REPO),'hash-object',f],text=True).strip()
    if original!=actual:changed.append(f)
assert not changed
(R/'verification/protected_files.json').write_text(json.dumps(dict(base_commit=BASE,checked_count=len(files),changed=changed),indent=2))
(R/'verification/technical_checks.json').write_text(json.dumps(dict(status='TECHNICAL PASS',width=1080,height=1920,fps='24/1',sar='1:1',dar='9:16',frames=144,seconds=6,full_decode='PASS',png_read='PASS',original_character_pose_records_exact_match=144,original_character_exposures='S01 threes; S02 twos',rain='global threes 0..47',protected_files=len(files),visual_performance='UNJUDGED; no normal speed viewing'),indent=2))
print('Technical PASS:',len(files),'existing tracked files unchanged')
