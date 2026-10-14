"""Read-only technical verification for the final review MP4."""
import subprocess,json,sys
from pathlib import Path
p=Path(sys.argv[1]); out=Path(__file__).parent
raw=subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)])
data=json.loads(raw); v=next(s for s in data['streams'] if s['codec_type']=='video'); a=next(s for s in data['streams'] if s['codec_type']=='audio')
checks={'duration_15s':abs(float(data['format']['duration'])-15)<.05,'aspect_9_16':v['width']*16==v['height']*9,'fps_24':v['avg_frame_rate']=='24/1','frames_360':v.get('nb_read_frames')=='360','audio_present':True,'stereo':a.get('channels')==2,'audio_48k':a.get('sample_rate')=='48000'}
dec=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
checks['full_decode_without_errors']=dec.returncode==0 and not dec.stderr.strip()
report={'file':str(p.resolve()),'checks':checks,'all_pass':all(checks.values()),'metadata':data,'decode_stderr':dec.stderr}
(out/'technical_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(checks,indent=2))
