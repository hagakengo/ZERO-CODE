"""Exact-source S04 assembly. Python 3/Pillow and ffmpeg/ffprobe. No existing asset writes."""
from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,hashlib,csv,shutil,io,math
R=Path(__file__).resolve().parents[1]; repo=R.parents[1]
BASE='f12ce0246ad152dbce62873d3893dde3c0e87745'
STEP='ff5600598c95c00f39674ddc3683ef26a863bd43'
S='reviews/pilot15_S04_step_independent_DRAFT_20261013'
E='reviews/pilot15_S04_evasion_independent_DRAFT_20261013'
def run(args): return subprocess.check_output(args,cwd=repo)
def sha(b): return hashlib.sha256(b).hexdigest()
for sub in ['frames','video','verification']: (R/sub).mkdir(exist_ok=True)
tracked=run(['git','ls-tree','-r','--name-only',BASE]).decode().splitlines()
protected=[]
for p in tracked:
    old=run(['git','show',BASE+':'+p]); current=(repo/p).read_bytes()
    protected.append({'path':p,'sha256':sha(old),'unchanged':old==current})
rows=[]
for local in range(30):
    commit,folder,source_local=(STEP,S,local) if local<14 else (BASE,E,local-14)
    source=f'{folder}/frames/F{source_local:03}.png'
    original=run(['git','show',commit+':'+source])
    assert original==(repo/source).read_bytes(),source
    dst=R/'frames'/f'F{local:03}.png'; dst.write_bytes(original)
    im=Image.open(io.BytesIO(original)); im.load(); assert im.size==(1080,1920)
    rows.append({'local_frame':local,'pilot_frame':216+local,'time_seconds':f'{local/24:.9f}','source_commit':commit,'source_path':source,'source_local_frame':source_local,'sha256':sha(original)})
with (R/'exposure_sheet.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
video=R/'video/S04_joined_F216-245_DRAFT_24fps.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(R/'frames/F%03d.png'),'-frames:v','30','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(video)],check=True)
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]))
decode=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True)
s=probe['streams'][0]
# Decode every output frame and quantify H.264 encoding error against exact PNG source sequence.
raw=run(['ffmpeg','-v','error','-i',str(video),'-f','rawvideo','-pix_fmt','rgb24','-'])
from PIL import ImageChops, ImageStat
frame_bytes=1080*1920*3
quality=[]
for n in range(30):
    actual=Image.frombytes('RGB',(1080,1920),raw[n*frame_bytes:(n+1)*frame_bytes])
    expected=Image.open(R/'frames'/f'F{n:03}.png').convert('RGB')
    mse=sum(ImageStat.Stat(ImageChops.difference(actual,expected)).sum2)/frame_bytes
    quality.append({'local_frame':n,'pilot_frame':n+216,'psnr_db':round(10*math.log10(255**2/mse),4) if mse else None})
a=json.loads((repo/S/'verification/exposure_sheet.json').read_text())[-1]
b=json.loads((repo/E/'verification/exposure_sheet.json').read_text())[0]
keys=['root_dx','root_dy','right_foot_dx','right_foot_dy','bag_lag_y']
connection={k:{'F229':a[k],'F230':b[k],'equal':abs(a[k]-b[k])<1e-8} for k in keys}
checks={'resolution':(s['width'],s['height'])==(1080,1920),'fps':s['avg_frame_rate']=='24/1','frames':int(s['nb_read_frames'])==30,'duration':abs(float(s['duration'])-1.25)<1e-6,'no_audio':len(probe['streams'])==1,'full_decode':decode.returncode==0 and not decode.stderr,'all_30_pngs_exact_to_pinned_commits':all(sha((R/'frames'/f'F{x["local_frame"]:03}.png').read_bytes())==x['sha256'] for x in rows),'no_drop_repeat_or_interpolation':len(rows)==30 and [x['pilot_frame'] for x in rows]==list(range(216,246)),'boundary_pose_parameters':all(x['equal'] for x in connection.values()),'all_prior_tracked_files_unchanged':all(x['unchanged'] for x in protected),'decoded_rgb_30_frames':len(raw)==frame_bytes*30,'all_output_psnr_above_40db':all(x['psnr_db']>40 for x in quality)}
(R/'verification/protected_files.json').write_text(json.dumps({'base_commit':BASE,'count':len(protected),'files':protected},indent=2))
(R/'verification/technical_checks.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'boundary_parameters':connection,'encoding_psnr':quality,'ffprobe':probe,'direction_status':'UNDETERMINED: no real-time continuous viewing, phone review, or director approval','note':'Exact PNG source sequence. Standard H.264 yuv420p MP4 is lossy; PSNR checks encoding only, not artistic continuity.'},indent=2))
# Contact sheet and boundary comparison are review artifacts, not frames inserted in MP4.
for name,indices in [('keyframes.png',[0,6,13,14,20,24,29]),('verification/connection.png',[12,13,14,15])]:
    tw,th=270,480; out=Image.new('RGB',(tw*len(indices),th+38),(245,245,245));d=ImageDraw.Draw(out)
    for i,n in enumerate(indices):
        thumb=Image.open(R/'frames'/f'F{n:03}.png').convert('RGB').resize((tw,th))
        out.paste(thumb,(i*tw,38));d.text((i*tw+8,12),f'F{216+n} / L{n:03}',fill=(0,0,0))
    out.save(R/name)
assert all(checks.values()),checks
print(json.dumps({'status':'PASS','protected':len(protected),'psnr_min':min(x['psnr_db'] for x in quality),'boundary':connection}))
