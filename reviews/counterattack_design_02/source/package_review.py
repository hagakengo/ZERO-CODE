from pathlib import Path
import hashlib,json,zipfile
out=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
zip_path=out/'ZERO_CODE_counterattack_design_02_review.zip'
integrity=out/'verification/zip_integrity.json'
files=[p for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p not in [zip_path,integrity,out/'SHA256.json']]
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)}
(out/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files.append(out/'SHA256.json')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,str(p.relative_to(out)))
with zipfile.ZipFile(zip_path) as z:
    matches={str(p.relative_to(out)):z.read(str(p.relative_to(out)))==p.read_bytes() for p in files}
    assert all(matches.values()) and z.testzip() is None
integrity.write_text(json.dumps({'date':'2026-10-13 JST','zip_sha256':sha(zip_path),'zip_bytes':zip_path.stat().st_size,'file_count':len(files),'all_files_byte_identical':all(matches.values()),'zip_crc':'PASS','outside_only':['verification/zip_integrity.json','ZERO_CODE_counterattack_design_02_review.zip'],'matches':matches},ensure_ascii=False,indent=2))
print(json.dumps({'zip_bytes':zip_path.stat().st_size,'files':len(files),'zip_sha256':sha(zip_path)}))
