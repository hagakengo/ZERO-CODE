"""Encode the 72 local Blender PNGs and verify delivered video + measurements.
python package_verify.py --frames SCRATCH --out OUT
Requires ffmpeg/ffprobe only. No network, audio, generative tools or B upload.
"""
import argparse,subprocess,json,hashlib,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--frames',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def run(c):return subprocess.run(c,check=True,capture_output=True,text=True).stdout
mp4=a.out/'AI_CITY_BLOCKING_24fps_DRAFT_HOLD.mp4'
run(['ffmpeg','-y','-v','error','-framerate','24','-start_number','1','-i',str(a.frames/'frame_%04d.png'),'-frames:v','72','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(mp4)]));(a.out/'QA_PROBE.json').write_text(json.dumps(probe,indent=2))
v=probe['streams'][0];assert (v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==(540,960,'24/1','72');assert float(probe['format']['duration'])==3.0
run(['ffmpeg','-v','error','-i',str(mp4),'-f','null','-'])
run(['ffmpeg','-y','-v','error','-i',str(mp4),'-vf','fps=4,scale=216:384,tile=6x2','-frames:v','1',str(a.out/'BLOCKING_SEQUENCE_DRAFT_HOLD.jpg')])
r=json.loads((a.out/'spatial_measurements.json').read_text());d={}
for key in ['near_anchor_px','mid_anchor_px','far_anchor_px']:
 d[key]=round(math.dist(r[0][key],r[-1][key]),3)
assert d['near_anchor_px']>d['mid_anchor_px']>d['far_anchor_px']
blocked=[q['frame'] for q in r if q['figure_center_blocker']=='near_occluder'];assert blocked and r[0]['figure_center_blocker'] is None and r[-1]['figure_center_blocker'] is None
report={'status':'DRAFT/HOLD','adopted_seconds':0,'technical_video':'spec + complete decode verified','screen_anchor_displacement_px':d,'torso_center_blocked_frames':blocked,'frame_time':'(frame-1)/24 seconds','normal_speed_perception':'UNVERIFIED; user review required','audio':'NONE; intentional geometry test','rendered_png_count':len(list(a.frames.glob('frame_*.png'))),'blender':'4.5.14 LTS','model':'Astra selected per user; runtime model ID unavailable'}
(a.out/'QA_TECHNICAL.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,ensure_ascii=False))
