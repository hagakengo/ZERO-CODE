from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as ET,csv
root=Path(__file__).resolve().parents[1]
report={"videos":[],"svg":[],"native":[],"protected_diff":[],"status":"DRAFT/HOLD","continuous_playback":"not performed; user normal-speed review required"}
for p in sorted(root.rglob('*.mp4')):
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
 v=next(s for s in data['streams'] if s['codec_type']=='video')
 check=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
 report['videos'].append({'path':str(p.relative_to(root)),'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'frames':v.get('nb_read_frames'),'duration':data['format']['duration'],'decode_pass':check.returncode==0,'errors':check.stderr})
for p in root.rglob('*.svg'):
 ET.parse(p);report['svg'].append(str(p.relative_to(root)))
for p in root.rglob('*'):
 if p.suffix in ['.blend','.kra','.ora','.tnz']:report['native'].append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size})
repo=root.parents[1]
changed=subprocess.check_output(['git','diff','2e6147a','--name-only'],cwd=repo,text=True).splitlines()
report['protected_diff']=[p for p in changed if p not in ['DIRECTOR_GUIDELINES.md','PRODUCTION_LOG.md'] and not p.startswith('reviews/pipeline_20261014/')]
assert not report['protected_diff'],report['protected_diff']
assert all(v['decode_pass'] for v in report['videos'])
(root/'lane5'/'technical_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
