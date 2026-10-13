from pathlib import Path
import array,csv,hashlib,io,json,math,subprocess,wave
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
A='54e200c50053c9746c553c66b742de092809fe52'; C='b09937fe98558d419e18264db1874f02ee80226d'
AP='reviews/pilot15_S04_joined_DRAFT_20261013'; CP='reviews/pilot15_audio_lane_c_DRAFT_20261013'
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def blob(ref,path):return git('show',f'{ref}:{path}')
def run(*a):return subprocess.run(a,check=True,capture_output=True)
def pcm(data):
 with wave.open(io.BytesIO(data),'rb') as w:
  assert w.getparams()[:3]==(1,2,48000)
  x=array.array('h');x.frombytes(w.readframes(w.getnframes()));return x
for p in ['audio','video','verification','reference']: (R/p).mkdir(exist_ok=True)
refs={ref:git('rev-parse',ref).decode().strip() for ref in [A,C,'1633364fd9d0f733f02ee42f44ac3511d4abd419']}
rows=list(csv.DictReader(io.StringIO(blob(C,CP+'/cue_sheet_DRAFT.csv').decode())))
metrics=[]
for row in rows:
 data=blob(C,CP+'/'+row['file']); (R/row['file']).write_bytes(data);x=pcm(data); nz=[i for i,v in enumerate(x) if v];peak=max(map(abs,x));rms=(sum(v*v for v in x)/len(x))**.5
 metrics.append(dict(cue=row['cue'],frame_start=int(row['start_frame']),frame_end_exclusive=int(row['end_frame_exclusive']),samples=len(x),peak_integer=peak,peak_dbfs=20*math.log10(peak/32768) if peak else None,rms_dbfs=20*math.log10(rms/32768) if rms else None,clip_samples=sum(v in [-32768,32767] for v in x),first_nonzero_global_frame=int(row['start_frame'])+nz[0]/2000 if nz else None,peak_global_frame=int(row['start_frame'])+max(range(len(x)),key=lambda i:abs(x[i]))/2000 if peak else None,sha256=hashlib.sha256(data).hexdigest(),status=row['mix']))
full=blob(C,CP+'/audio/pilot15_audio_PROVISIONAL_DRAFT.wav'); (R/'audio/pilot15_audio_PROVISIONAL_DRAFT.wav').write_bytes(full); mix=pcm(full)
assert len(mix)==720000
silence=[]
for a,b in [(209,216),(246,309),(309,360)]:
 assert not any(mix[a*2000:b*2000]);silence.append([a,b])
x=mix[432000:492000]
with wave.open(str(R/'audio/S04_F216-245_SYNC_DRAFT.wav'),'wb') as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(x.tobytes())
video=blob(A,AP+'/video/S04_joined_F216-245_DRAFT_24fps.mp4');(R/'reference/S04_source_DRAFT.mp4').write_bytes(video)
(R/'reference/cue_sheet_source.csv').write_bytes(blob(C,CP+'/cue_sheet_DRAFT.csv'))
(R/'reference/S04_exposure_source.csv').write_bytes(blob(A,AP+'/exposure_sheet.csv'))
for name in ['RIGHTS.md','source/render_audio.py']:
 (R/'reference'/Path(name).name).write_bytes(blob(C,CP+'/'+name))
out=R/'video/S04_F216-245_AUDIO_SYNC_REVIEW_DRAFT.mp4'
run('ffmpeg','-y','-v','error','-i',str(R/'reference/S04_source_DRAFT.mp4'),'-i',str(R/'audio/S04_F216-245_SYNC_DRAFT.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t','1.25','-movflags','+faststart',str(out))
probe=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],v['nb_frames'])==(1080,1920,'24/1','30')
assert abs(float(v['duration'])-1.25)<1e-6 and abs(float(a['duration'])-1.25)<1e-6
run('ffmpeg','-v','error','-i',str(out),'-f','null','-')
hashes=[]
for p in [R/'reference/S04_source_DRAFT.mp4',out]:
 hashes.append(run('ffmpeg','-v','error','-i',str(p),'-map','0:v','-f','framemd5','-').stdout)
assert hashes[0]==hashes[1]
decoded=array.array('h');decoded.frombytes(run('ffmpeg','-v','error','-i',str(out),'-map','0:a','-f','s16le','-').stdout)
analysis={'status':'TECHNICAL_PASS','source_refs':refs,'cue_metrics':metrics,'original_track_samples':len(mix),'digital_silence_frame_windows_exclusive':silence,'s04_audio_samples':len(x),'s04_frame_map':'Local L000=F216, L014=F230, L029=F245; 2000 PCM samples/frame','video_stream_copy_decoded_frames_identical':True,'video_frames':30,'video_fps':v['r_frame_rate'],'video_dimensions':[1080,1920],'container_duration_seconds':float(probe['format']['duration']),'aac_stream_duration_seconds':float(a['duration']),'aac_full_decode_samples_including_padding':len(decoded),'aac_decoded_peak_integer':max(map(abs,decoded)),'aac_clip_samples':sum(z in [-32768,32767] for z in decoded),'all_wavs_decode_pass':[],'auditory_review':'NOT_PERFORMED: no direct audio perception capability','direction':'UNJUDGED','visual_contact_sync':'UNAPPROVED: cue window alignment only, no foot contact lock','hold':'Design04 HOLD; A07-A11 excluded'}
for p in sorted((R/'audio').glob('*.wav')):run('ffmpeg','-v','error','-i',str(p),'-f','null','-');analysis['all_wavs_decode_pass'].append(p.name)
(R/'verification/analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
(R/'verification/mp4_probe.json').write_text(json.dumps(probe,indent=2)+'\n')
print(json.dumps({k:analysis[k] for k in ['status','s04_audio_samples','aac_full_decode_samples_including_padding','aac_clip_samples']}))
