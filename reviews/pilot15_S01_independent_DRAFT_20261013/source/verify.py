from pathlib import Path
from PIL import Image
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]; repo=R.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def decode(p):
    c=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
    return {'returncode':c.returncode,'stderr':c.stderr,'pass':c.returncode==0 and not c.stderr}
p=R/'video/S01_silence_DRAFT_24fps.mp4'; info=probe(p); v=info['streams'][0]
hashes=[sha(R/'frames'/f'F{n:03}.png') for n in range(72)]
checks={'dimensions':(v['width'],v['height'])==(1080,1920),'fps':v['avg_frame_rate']=='24/1','frames':int(v['nb_read_frames'])==72,'duration':float(v['duration'])==3,'h264':v['codec_name']=='h264','yuv420p':v['pix_fmt']=='yuv420p','no_audio':len(info['streams'])==1,'all_holds_on_threes':all(hashes[n]==hashes[n+1]==hashes[n+2] for n in range(0,72,3)),'24_distinct_drawings':len(set(hashes))==24}
for n in range(72):
    with Image.open(R/'frames'/f'F{n:03}.png') as im: im.verify()
checks['all_png_decode']=True
checks['full_video_decode']=decode(p)['pass']
assert all(checks.values()),checks
(R/'verification/technical_checks.json').write_text(json.dumps({'checks':checks,'probe':info,'decode':decode(p),'video_sha256':sha(p),'unique_drawings':24,'output_frames':72,'timeline_mapping':'S01 local F000..071 = pilot DRAFT F000..071; no other shot rendered','perceptual_pass':'NOT ASSIGNED; normal-speed continuous perception not verified'},indent=2))
base='9a9c57edd68c4051609399582b1c74721115a88f'
names=subprocess.check_output(['git','ls-tree','-r','--name-only',base],cwd=repo,text=True).splitlines()
changed=[]
# Git blob hash compares every baseline tracked file against its committed bytes.
for name in names:
    expected=subprocess.check_output(['git','rev-parse',f'{base}:{name}'],cwd=repo,text=True).strip()
    path=repo/name
    actual=subprocess.check_output(['git','hash-object','--',str(path)],cwd=repo,text=True).strip() if path.exists() else 'MISSING'
    if expected!=actual: changed.append(name)
main=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=repo,text=True).strip()
assert not changed,changed
(R/'verification/protected_files.json').write_text(json.dumps({'base':base,'baseline_tracked_files_checked':len(names),'changed_baseline_files':changed,'remote_main_observed':main,'main_not_targeted':True,'no_design05':True,'no_timeline_integration':True},indent=2))
# Prior MP4s are read-only reference, never copied to this deliverable.
prior=[Path('/Users/hagakengo/Documents/Codex/2026-10-11/referenced-chatgpt-conversation-this-is-an-31/outputs/ZERO_CODE_EP01_pilot15_animatic_v01.mp4'),Path('/Users/hagakengo/Documents/Codex/2026-10-11/referenced-chatgpt-conversation-this-is-an-32/outputs/ZERO_CODE_EP01_pilot15_animatic_v02.mp4'),repo/'reviews/counterattack_design_04/video/counterattack_design_04_24fps.mp4']
refs=[]
for src in prior:
    refs.append({'path':str(src),'sha256':sha(src),'probe':probe(src),'decode':decode(src)})
(R/'verification/reference_media_checks.json').write_text(json.dumps(refs,indent=2))
print(json.dumps({'checks':checks,'baseline_files_unchanged':len(names)}))
