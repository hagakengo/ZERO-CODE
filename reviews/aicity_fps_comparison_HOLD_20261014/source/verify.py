from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1]
report={}
for fps in (24,60):
 p=r/f'AI_CITY_{fps}fps_DRAFT_HOLD.mp4'
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
 v=next(s for s in d['streams'] if s['codec_type']=='video');a=next(s for s in d['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1080,1920,f'{fps}/1',fps*3)
 assert float(v['duration'])==float(a['duration'])==3 and a['channels']==2 and a['sample_rate']=='48000'
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True)
 audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a','-f','s16le','-'])
 report[str(fps)]={'probe':d,'decoded_audio_sha256':hashlib.sha256(audio).hexdigest(),'decode':'PASS'}
h24=json.loads((r/'frame_hashes_24.json').read_text());h60=json.loads((r/'frame_hashes_60.json').read_text())
assert len(set(h24))==72 and len(set(h60))==180
assert all(h24[2*k]==h60[5*k] for k in range(36))
assert report['24']['decoded_audio_sha256']==report['60']['decoded_audio_sha256']
report['fairness']={'common_time_exact_rgb_matches':36,'unique_frames_24':72,'unique_frames_60':180,'decoded_audio_identical':True,'sample_times':'i/fps; same render(t), seeds, camera, effects and event; no interpolation'}
(r/'QA_TECHNICAL.json').write_text(json.dumps(report,indent=2))
print('PASS: specs, full decode, 36 shared-time exact matches, 252 unique frames, identical audio')
