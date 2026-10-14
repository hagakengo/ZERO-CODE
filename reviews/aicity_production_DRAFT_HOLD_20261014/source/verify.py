import json,subprocess,hashlib,sys
from pathlib import Path
p=Path(sys.argv[1]);out=Path(sys.argv[2])
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
checks={'duration_3s':abs(float(probe['format']['duration'])-3)<.001,'72_frames':int(v['nb_read_frames'])==72,'24fps':v['avg_frame_rate']=='24/1','1080x1920':(v['width'],v['height'])==(1080,1920),'audio_stereo_48k':a['sample_rate']=='48000' and a['channels']==2}
decode=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True)
checks['full_decode']=decode.returncode==0 and not decode.stderr
r={'status':'DRAFT/HOLD','checks':checks,'technical_pass':all(checks.values()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'probe':probe,'normal_speed_viewing':'UNVERIFIED','actual_listening':'UNVERIFIED','artistic_approval':'HOLD'}
out.write_text(json.dumps(r,indent=2));print(json.dumps(checks));assert all(checks.values())
