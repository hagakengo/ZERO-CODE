from pathlib import Path
import json,subprocess,math,csv
R=Path(__file__).resolve().parents[1]
poses=json.loads((R/'motion.json').read_text())
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
contact={}
for side,regions in [('left',[(216,226),(240,245)]),('right',[(216,217),(233,245)])]:
 for a,b in regions:
  ps=[p[f'{side}_foot'] for p in poses if a<=p['frame']<=b]
  contact[f'{side}_{a}-{b}']=max(dist(ps[0],p) for p in ps)
res=max(abs(dist(a,b)-.55) for p in poses for h,k,a in zip(p['hips'],p['knees'],p['ankles']) for a,b in [(h,k),(k,a)])
checks={'contact_world_displacement_m':contact,'max_leg_length_error_m':res,'max_shoulder_pelvis_difference_deg':max(abs(p['pelvis_yaw_deg']-p['shoulder_yaw_deg']) for p in poses),'technical':{},'viewing':'Normal-speed uninterrupted visual playback NOT performed. Still frames inspected. Art/direction HOLD.'}
for v in sorted((R/'video').glob('*.mp4')):
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)]));video=[x for x in probe['streams'] if x['codec_type']=='video'][0]
 dec=subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],capture_output=True)
 checks['technical'][v.name]={'width':video['width'],'height':video['height'],'fps':video['r_frame_rate'],'frames':video['nb_read_frames'],'duration':probe['format']['duration'],'audio_streams':len([x for x in probe['streams'] if x['codec_type']=='audio']),'full_decode':dec.returncode==0,'decode_error':dec.stderr.decode()}
(R/'technical_validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
