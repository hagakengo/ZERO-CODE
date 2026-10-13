"""Rebuild from preserved AI-generated raster drawings. No rig, warp, optical flow or morph.
Requires Python 3 and ffmpeg/ffprobe. Generated art itself is not deterministic;
prompts and exact source raster are retained for reproducible assembly.
"""
from pathlib import Path
import subprocess, json, csv, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
def run(*args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
source=ROOT/'drawing_sheet.png'
s=probe(source)['streams'][0]; w,h=s['width'],s['height']
exposures=[3,2,2,1,1,1,2,1,2,3,2,2,2,3,3]
phases=['ready','sink','deep anticipation','push','toe release','flight','dodge maximum','right contact','load','landing compression','bag catchup','left contact','recover','settle','hold']
keys={1,3,5,7,8,10,12,15}
rows=[]; frame=216
for i,duration in enumerate(exposures):
    col,row=i%5,i//5
    x0=round(col*w/5)+2; y0=round(row*h/3)+2
    cw=round((col+1)*w/5)-x0-2; ch=round((row+1)*h/3)-y0-2
    drawing=ROOT/'drawings'/f'D{i+1:02}.png'
    run('ffmpeg','-y','-v','error','-i',str(source),'-vf',f'crop={cw}:{ch}:{x0}:{y0}','-frames:v','1',str(drawing))
    # Identical viewport for every drawing. No individual normalization or translation.
    out=ROOT/'frames'/f'f{frame:03}.png'
    run('ffmpeg','-y','-v','error','-i',str(drawing),'-vf','scale=1000:1000:flags=lanczos,pad=1080:1920:40:460:color=0xaaaaaa','-frames:v','1',str(out))
    for offset in range(duration):
        target=ROOT/'frames'/f'f{frame+offset:03}.png'
        if offset: shutil.copyfile(out,target)
        rows.append([frame+offset,i+1,'key' if i+1 in keys else 'inbetween',duration,phases[i],hashlib.sha256(target.read_bytes()).hexdigest()])
    frame+=duration
assert frame==246
with (ROOT/'exposure.csv').open('w',newline='') as f:
    writer=csv.writer(f); writer.writerow(['global_frame','drawing','role','exposure_frames','intended_action_not_verified','sha256']);writer.writerows(rows)
video=ROOT/'video'
run('ffmpeg','-y','-v','error','-framerate','24','-start_number','216','-i',str(ROOT/'frames/f%03d.png'),'-frames:v','30','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video/'S04_DRAFT_normal.mp4'))
run('ffmpeg','-y','-v','error','-i',str(video/'S04_DRAFT_normal.mp4'),'-vf','setpts=2*PTS,tpad=stop_mode=clone:stop_duration=0.083333','-r','24','-frames:v','60','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video/'S04_DRAFT_half.mp4'))
old=ROOT/'reference_old_f0edded.mp4'
if old.exists():
    run('ffmpeg','-y','-v','error','-i',str(old),'-i',str(video/'S04_DRAFT_normal.mp4'),'-filter_complex','[0:v]scale=540:960[a];[1:v]scale=540:960[b];[a][b]hstack=inputs=2[v]','-map','[v]','-frames:v','30','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video/'comparison_normal.mp4'))
    run('ffmpeg','-y','-v','error','-stream_loop','5','-i',str(video/'comparison_normal.mp4'),'-c','copy',str(video/'comparison_normal_6loops.mp4'))
    run('ffmpeg','-y','-v','error','-i',str(video/'comparison_normal.mp4'),'-vf','setpts=2*PTS,tpad=stop_mode=clone:stop_duration=0.083333','-r','24','-frames:v','60','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(video/'comparison_half.mp4'))
report={}
for file in video.glob('*.mp4'):
    p=probe(file);v=p['streams'][0]
    run('ffmpeg','-v','error','-i',str(file),'-f','null','-')
    report[file.name]={k:v.get(k) for k in ['width','height','r_frame_rate','nb_read_frames','duration']}
assert report['S04_DRAFT_normal.mp4']['nb_read_frames']=='30'
assert report['S04_DRAFT_normal.mp4']['width']==1080
assert report['S04_DRAFT_normal.mp4']['height']==1920
(ROOT/'technical_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
