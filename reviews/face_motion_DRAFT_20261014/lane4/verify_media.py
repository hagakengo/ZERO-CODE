import pathlib,subprocess,json,hashlib
root=pathlib.Path(__file__).resolve().parent.parent; out=root/'lane4';out.mkdir(exist_ok=True)
results=[]
for p in sorted(root.glob('lane[23]/*.mp4')):
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
 d=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True)
 s=next(x for x in probe['streams'] if x['codec_type']=='video')
 results.append({'file':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frame_count':s['nb_read_frames'],'fps':s['r_frame_rate'],'duration':probe['format']['duration'],'width':s['width'],'height':s['height'],'codec':s['codec_name'],'pixel_format':s['pix_fmt'],'all_frames_decoded':d.returncode==0 and not d.stderr,'decode_stderr':d.stderr.decode(),'continuous_playback_watched':False})
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(p),'-vf','scale=320:-1,tile=6x8','-frames:v','1',str(out/(p.stem+'_all_frames.png'))],check=True)
(out/'TECHNICAL_QA.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,indent=2))
