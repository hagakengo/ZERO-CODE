from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib,math,shutil
out=Path(__file__).resolve().parent; out.mkdir(parents=True,exist_ok=True)
old=out.parent
src=old/'reference/A_B_C_comparison_DRAFT.png'; original=old/'reference/user_reference_original.png'
crop=Image.open(src).crop((1024,49,1536,332)); crop.save(out/'common_C_FILM_crop_DRAFT.png')
points={'left_eye_outer':[204,110],'left_eye_inner':[234,99],'left_iris':[221,106],'right_eye_inner':[263,83],'right_eye_outer':[298,70],'right_iris':[282,77],'nose_tip':[249,117],'mouth_left':[250,141],'mouth_right':[283,130],'chin':[276,176],'left_brow_anchor':[212,85],'right_brow_anchor':[269,60],'bang_cross_nose':[261,103],'bang_over_left_eye':[223,91],'bang_right_tip':[309,107],'ear_right':[333,93]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j={'status':'DRAFT/HOLD','source_original':'../reference/user_reference_original.png','source_original_sha256':sha(original),'C_FILM_source':'../reference/A_B_C_comparison_DRAFT.png','C_FILM_source_sha256':sha(src),'crop_box_xyxy':[1024,49,1536,332],'crop_size':[512,283],'coordinate_system':'pixel x right, y down; source native resolution; screen left/right','view':'existing tilted three-quarter pose; NOT approved neutral frontal','landmarks_observed':points,'measurement_uncertainty_pixels':3,'eye_axis_angle_degrees':round(math.degrees(math.atan2(-29,61)),1),'tolerances_PROVISIONAL_not_design_approval':{'static_chin_nose_hair_outline_displacement_px':0,'eye_corner_displacement_px':1,'iris_gaze_offset_max_px':2,'brow_emotion_offset_max_px':2,'mouth_corner_emotion_offset_max_px':2,'hair_lock_roots_and_tips_displacement_px':0},'tolerance_meaning':'Engineering guardrails for same-pose A/B test; not artist-approved anatomical limits. Manual points uncertain +/-3 px; measure dynamic drift against the same source, never infer true front proportions from tilted face.'}
(out/'common_landmarks_DRAFT.json').write_text(json.dumps(j,indent=2),encoding='utf8')
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18); small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15)
im=Image.new('RGB',(1100,680),'#151b24'); d=ImageDraw.Draw(im);d.text((24,15),'C / FILM   OBSERVED POSE GUIDE   DRAFT / HOLD',font=font,fill='white'); im.paste(crop.resize((1024,566)),(24,60));d=ImageDraw.Draw(im)
for name,p in points.items():
 x,y=24+p[0]*2,60+p[1]*2; d.ellipse((x-4,y-4,x+4,y+4),fill='#5bffda')
for a,b in [('left_iris','right_iris'),('mouth_left','mouth_right')]:
 p,q=points[a],points[b]; d.line((24+p[0]*2,60+p[1]*2,24+q[0]*2,60+q[1]*2),fill='#ffc757',width=2)
for label,key,xy in [('L EYE','left_iris',(265,380)),('R EYE','right_iris',(770,130)),('NOSE','nose_tip',(760,300)),('CHIN','chin',(770,430)),('MOUTH','mouth_left',(265,470)),('BANG LOCK','bang_cross_nose',(710,55))]:
 p=points[key];d.line((xy[0],xy[1]+15,24+p[0]*2,60+p[1]*2),fill='#5bffda',width=1);d.text(xy,label,font=small,fill='#5bffda')
d.rectangle((24,632,1076,669),fill='#151b24');d.text((28,638),'Tilt is preserved. Points approximate +/-3 px. No approved frontal view is available.',font=font,fill='#ffc757');im.save(out/'landmark_guide_DRAFT.png')
prev=Image.open(old/'reference/head_model_v2_DRAFT.png'); prevcrop=prev.crop((50,0,770,610))
orig=Image.open(original).crop((50,80,330,320))
comparison=Image.new('RGB',(1440,570),'#151b24');dr=ImageDraw.Draw(comparison)
for x,label,img in [(0,'ORIGINAL A / provenance',orig),(480,'C / FILM chosen same-pose',crop),(960,'PREVIOUS FRONT / unapproved',prevcrop)]:
 dr.text((x+15,16),label,font=font,fill='white'); img=img.copy();img.thumbnail((460,440));comparison.paste(img,(x+(480-img.width)//2,60))
dr.text((20,520),'Different drawings and poses: direct pixel subtraction would be misleading. Human correction remains HOLD.',font=font,fill='#ffc757');comparison.save(out/'baseline_previous_comparison_DRAFT.png')
# Script is already stored alongside its deliverables.
