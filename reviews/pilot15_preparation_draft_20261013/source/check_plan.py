#!/usr/bin/env python3
"""DRAFT: validate frame arithmetic only; no creative approval."""
import csv,json,sys
from pathlib import Path
D=Path(__file__).resolve().parents[1]

def main():
    errors=[]
    rows=list(csv.DictReader((D/'timeline_draft.csv').open()))
    end=0
    for r in rows:
        a,b=int(r['start_frame']),int(r['end_frame_exclusive'])
        if a!=end or b<=a: errors.append('Timeline gap/overlap: '+r['shot'])
        if int(r['frames'])!=b-a: errors.append('Frame count mismatch: '+r['shot'])
        if abs(float(r['start_seconds'])-a/24)>0.000001 or abs(float(r['end_seconds_exclusive'])-b/24)>0.000001: errors.append('Time mismatch: '+r['shot'])
        if r['status']!='DRAFT': errors.append('Missing DRAFT')
        end=b
    if end!=360: errors.append('Timeline does not end at F360')
    cues=list(csv.DictReader((D/'sound_cues_draft.csv').open()))
    for r in cues:
        if not 0<=int(r['start_frame'])<int(r['end_frame_exclusive'])<=360: errors.append('Invalid cue: '+r['cue'])
        if r['status']!='DRAFT' or not r['rights_source']: errors.append('Missing cue state/source')
    result={'status':'DRAFT','arithmetic_pass':not errors,'shots':len(rows),'total_frames':end,'fps':24,'duration_seconds':end/24,'cues':len(cues),'errors':errors,'director_approval':'NOT_ASSESSED'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return bool(errors)
if __name__=='__main__':sys.exit(main())
