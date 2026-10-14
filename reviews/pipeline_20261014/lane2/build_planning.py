from pathlib import Path
import csv,json,hashlib,xml.etree.ElementTree as ET
from html import escape
root=Path(__file__).resolve().parents[3]
base=Path(__file__).resolve().parent
lane3=base.parent/'lane3'
fields=['frame_1based','start_seconds','end_seconds','phase','key_pose','head_cell','hair_cell','eye_cell','mouth_cell','brow_cell','gaze_right_deg_PLAN','neck_yaw_deg_PLAN','hair_tip_lag_deg_PLAN','camera','sound_cue','status']
rows=[]
keys={1:'K001',13:'K013',21:'K021',25:'K025',31:'K031',37:'K037',43:'K043',49:'K049',55:'K055',61:'K061'}
for f in range(1,73):
    head='H00'; hair='T00'; eye='E00'; mouth='M00'; brow='B00'; gaze=neck=lag=0; cue=''; key=keys.get(f,'')
    if f<=12: phase='neutral'
    elif f<=24:
        phase='slight_smile'; mouth='M01' if f<17 else 'M02' if f<21 else 'M03';eye='E01' if f<17 else 'E02';brow='B01'
    elif f<=30:
        phase='eyes_lead';mouth='M03' if f<29 else 'M04';eye=f'E{3+(f-25)//2:02}';gaze=[5,5,10,10,12,12][f-25];brow='B02' if f>=27 else 'B01';cue='ANOMALY_TEST_CUE' if f==25 else ''
    elif f<=44:
        phase='neck_follows';i=(f-31)//2;head=f'H{i+1:02}';neck=[1,3,5,8,10,11.5,12][i];gaze=12-neck;eye='E06';mouth='M05';brow='B02';hair=f'T{max(0,i-1):02}';lag=[-1,-2,-3,-4,-4,-2.5,-1][i]
    elif f<=54:
        phase='hair_settles';head='H07';neck=12;eye='E06';mouth='M05';brow='B02';hair=f'T{[5,5,6,6,7,7,6,6,5,5][f-45]:02}';lag=[1,1,2,2,1,1,0.5,0.5,0,0][f-45]
    else:
        phase='attention_hold';head='H07';neck=12;hair='T05';eye='E07';mouth='M06';brow='B03'
    rows.append([f,f'{(f-1)/24:.6f}',f'{f/24:.6f}',phase,key,head,hair,eye,mouth,brow,gaze,neck,lag,'LOCKED',cue,'DRAFT/HOLD_PLAN_ONLY'])
with (base/'timesheet_DRAFT.csv').open('w',newline='') as out:
    w=csv.writer(out,lineterminator="\n");w.writerow(fields);w.writerows(rows)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1150" viewBox="0 0 1400 1150">','<rect width="1400" height="1150" fill="#101923"/>','<style>text{font-family:Arial,sans-serif;fill:#e7edf3}.note{font-size:19px}.title{font-size:29px;font-weight:bold}.ink{fill:none;stroke:#d6e0e9;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}</style>','<text x="35" y="44" class="title">TEST_AC01 / 3 s acting storyboard / DRAFT + HOLD</text>','<text x="35" y="75" class="note">ONE locked shot, FOUR moments. Schematic actor: NOT C/FILM likeness or final drawing.</text>']
notes=[('F001–012 / 0–0.5 s','NEUTRAL','Half-lidded gaze; head and shoulders held.'),('F013–024 / 0.5–1 s','SMALL SMILE','Mouth corner then cheek / lower lid follow.'),('F025–030 / 1–1.25 s','EYES FIRST','Cue at 1.000 s. Eyes right; skull still.'),('F031–072 / 1.25–3 s','NECK → HAIR → HOLD','Shallow turn; tips settle; keep attention.')]
for i,(time,title,note) in enumerate(notes):
    x=35+(i%2)*690;y=105+(i//2)*500
    svg.append(f'<g id="moment_{i+1}" transform="translate({x},{y})"><rect width="640" height="470" rx="9" fill="#192632" stroke="#516574"/><text x="20" y="31" class="title">{title}</text><text x="20" y="60" class="note">{time}</text>')
    # 9:16 staging panel, editable hand-coded vector paths
    svg.append('<g id="frame_9x16" transform="translate(22,78)"><rect width="180" height="320" fill="#0b121b" stroke="#91a4b2"/><path d="M0 270L90 180L180 270M0 310L90 180L180 310M90 0V180" stroke="#344655" fill="none"/><path d="M8 45H55V245H8ZM125 15H170V240H125Z" fill="#18232d"/><path d="M15 95V190M155 55V220" stroke="#395d6b" stroke-width="3"/>')
    svg.append('<g id="schematic_actor" class="ink"><path d="M40 320L46 248Q65 228 74 224L75 204M105 204L107 224Q130 228 141 252L150 320"/><ellipse cx="90" cy="174" rx="35" ry="43"/><path d="M58 157Q63 123 87 126Q122 128 124 158M62 153L70 174L83 147L92 170L105 143L118 168"/>')
    shift=6 if i>=2 else 0
    svg.append(f'<path d="M66 177L81 176M96 176L112 177"/><circle cx="{75+shift}" cy="178" r="2" fill="#d6e0e9"/><circle cx="{102+shift}" cy="178" r="2" fill="#d6e0e9"/>')
    svg.append('<path d="M81 197Q91 202 103 195"/>' if i==1 else '<path d="M81 198L102 198"/>')
    svg.append('</g></g>')
    svg.append(f'<text x="230" y="115" class="note">{escape(note.split("; ")[0])}</text>')
    if i==2: svg.append('<path d="M240 165H530L515 155M530 165L515 175" stroke="#74c9d6" fill="none" stroke-width="3"/><text x="230" y="200" class="note">Gaze only. No head movement yet.</text>')
    if i==3: svg.append('<text x="230" y="160" class="note">F031 neck onset / F037 shoulders</text><text x="230" y="195" class="note">F045 tips overshoot / F055 settle</text><text x="230" y="230" class="note">No enemy / no power / no HUD.</text>')
    svg.append('<text x="230" y="300" class="note">9:16 / 1080 x 1920 / 24 fps</text><text x="230" y="334" class="note">See CSV for each exposure frame.</text><text x="230" y="368" class="note">Identity / acting: HOLD</text></g>')
svg.append('<text x="35" y="1130" class="note">72 frames is duration, not 72 unique drawings. No finished character animation has been claimed.</text></svg>')
(base/'storyboard_DRAFT.svg').write_text('\n'.join(svg))
layers=['BG_GUIDE','TORSO','NECK','HAIR_BACK','FACE_BASE','EAR_NEAR','EAR_FAR','EYE_WHITE','IRIS_NEAR','IRIS_FAR','LID_LOWER','LID_UPPER','BROW','MOUTH','CHEEK','HAIR_FRONT','SHADOW']
template=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1080" height="1920" viewBox="0 0 1080 1920">','<title>DRAFT HOLD: empty transparent production template; no C likeness drawn</title>']
for name in layers: template.append(f'<g id="{name}" data-layer-name="{name}"><desc>EMPTY: draw approved transparent artwork here</desc></g>')
template.append('<g id="GUIDES" opacity="0.4" data-export="hide"><path d="M540 0V1920M0 700H1080M0 1100H1080" stroke="#328dab" fill="none"/><text x="30" y="60" font-family="sans-serif" font-size="24" fill="#328dab">DRAFT / HOLD | empty layers | guides are not C measurements</text></g></svg>')
(lane3/'layer_template_DRAFT.svg').write_text('\n'.join(template))
for name in ['reference','model','keys','inbetweens','parts','scenes','export','review']:
    p=lane3/'production_template_DRAFT'/name;p.mkdir(parents=True,exist_ok=True)
    (p/'README.md').write_text(f'# {name} — DRAFT / HOLD\n\nEmpty production staging folder. No finished C/FILM artwork or native project is present. See ../../ASSET_PIPELINE_DRAFT.md.\n')
inputs=['reviews/model_cleanup_DRAFT_20261014/reference/user_reference_original.png','reviews/model_cleanup_DRAFT_20261014/reference/A_B_C_comparison_DRAFT.png','reviews/model_cleanup_DRAFT_20261014/lane1/head_model_v2_DRAFT.png','reviews/model_cleanup_DRAFT_20261014/lane2/expression_parts_layered_DRAFT.svg']
manifest={'date':'2026-10-14 JST','base_commit':'2e6147a','status':'DRAFT/HOLD','C_crop':'No C crop performed in this lane; right column in comparison sheet is a derived C candidate, distinct from original A/DENSE.','inputs':[{'repository_path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'bytes':(root/p).stat().st_size} for p in inputs]}
(lane3/'REFERENCE_MANIFEST_DRAFT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
ET.parse(base/'storyboard_DRAFT.svg');ET.parse(lane3/'layer_template_DRAFT.svg')
assert len(rows)==72 and rows[0][0]==1 and rows[-1][0]==72
assert abs(float(rows[-1][2])-3)<1e-6
assert manifest['inputs'][0]['sha256']=='bc3697df6c3c080985b226b285627d449124f1b9b58c9326ea6a316890057fad'
(base/'PLANNING_QA_DRAFT.json').write_text(json.dumps({'status':'PLANNING_TECHNICAL_PASS; DRAWING_HOLD','csv_rows':72,'fps_plan':24,'duration_seconds_plan':3,'svg_xml_parse':'PASS','original_hash':'MATCH','native_project_import':'NOT_TESTED','C_artwork':'NOT_CREATED','normal_speed_viewing':'NOT_PERFORMED'},indent=2)+'\n')
print('72 rows, 3 seconds planned, 2 SVG XML parse PASS, original hash MATCH; artwork HOLD')
