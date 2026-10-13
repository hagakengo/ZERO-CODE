from pathlib import Path
import json,math,subprocess,hashlib,csv
R=Path(__file__).resolve().parents[1];p=json.loads((R/'motion.json').read_text());report={}
for side in ['left','right']:
 segments=[];seg=[]
 for q in p:
  if q[side+'_contact']:seg.append(q)
  elif seg:segments.append(seg);seg=[]
 if seg:segments.append(seg)
 report[side+'_contact_segments']=[{'frames':[s[0]['frame'],s[-1]['frame']],'world_anchor_drift_m':max(math.dist(q[side+'_foot'],s[0][side+'_foot']) for q in s)} for s in segments]
report['max_segment_length_error_m']=max(abs(math.dist(q['hips'][i],q['knees'][i])-.55) for q in p for i in range(2))
report['max_shoulder_pelvis_yaw_difference_deg']=max(abs(q['pelvis_yaw_deg']-q['shoulder_yaw_deg']) for q in p)
report['contact_shoe_orientation']='Constant during stance. No toe-off articulation. Left shoe changes heading after release.'
report['caveat']='Kinematic contact/IK checks only. No mass, force, friction, collision or cloth simulation. Not a body-weight quality PASS.'
assert max(x['world_anchor_drift_m'] for side in ['left','right'] for x in report[side+'_contact_segments'])<1e-9
(R/'motion_checks.json').write_text(json.dumps(report,indent=2))
rows=[]
for i,q in enumerate(p):
 prev=p[max(0,i-1)];prev2=p[max(0,i-2)]
 rows.append([q['frame'],q['pelvis'][0],q['pelvis'][1],(q['pelvis'][0]-prev['pelvis'][0])*24,(q['pelvis'][0]-2*prev['pelvis'][0]+prev2['pelvis'][0])*24**2,q['pelvis_yaw_deg'],q['shoulder_yaw_deg'],q['left_contact'],q['right_contact']])
with (R/'kinematic_timeline.csv').open('w') as f:w=csv.writer(f);w.writerow(['frame','pelvis_x_m','pelvis_y_m','pelvis_vx_m_s','pelvis_ax_m_s2_NOT_FORCE','pelvis_yaw_deg','shoulder_yaw_deg','left_contact','right_contact']);w.writerows(rows)
# Full asset manifest to detect corruption independently of video decode.
manifest={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in R.rglob('*') if f.is_file() and f.name!='manifest_sha256.json'}
(R/'manifest_sha256.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(report,indent=2))
