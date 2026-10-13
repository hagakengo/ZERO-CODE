from PIL import Image,ImageDraw,ImageFont
import json,math,hashlib
from pathlib import Path
out=Path(__file__).parent
src=out.parent.parent/'parallel_production_DRAFT_20261014/lane1/A_C_FILM_MODEL_SHEET_DRAFT.png'
im=Image.open(src).convert('RGB')
views={
'FRONT_LABEL_TILTED':{'crop':[115,70,411,300],'points':{'eye_image_left':[232,183],'eye_image_right':[300,158],'nose_tip':[263,201],'mouth_center':[279,221],'chin':[282,265],'ear_visible':[352,174],'fringe_center_tip':[267,186]},'yaw':'not zero; not an orthographic front','occluded':['left ear','cranial contour','hair roots']},
'THREE_QUARTER':{'crop':[602,70,892,300],'points':{'eye_image_left':[693,185],'eye_image_right':[744,155],'nose_tip':[714,204],'mouth_center':[726,218],'chin':[740,258],'ear_visible':[818,167],'fringe_center_tip':[711,178]},'yaw':'oblique; angle not calibrated','occluded':['far ear','cranial contour','hair roots']},
'PROFILE':{'crop':[1128,70,1452,300],'points':{'eye_visible':[1345,168],'nose_tip':[1398,210],'mouth_center':[1364,229],'chin':[1345,268],'ear_visible':[1252,180],'fringe_center_tip':[1376,191]},'yaw':'profile-like; angle not calibrated','occluded':['far eye','far ear','cranial contour','hair roots']}}
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
canvas=Image.new('RGB',(1536,600),'#162029');d=ImageDraw.Draw(canvas)
d.text((22,14),'C / FILM — OBSERVED LANDMARKS | DRAFT / HOLD',font=font,fill='white')
colors=['#40e0d0','#ffb454','#ff77aa','#8dcaff','#ffee88','#bbaaff','#99ef88']
for i,(name,v) in enumerate(views.items()):
 x0,y0,x1,y1=v['crop']; scale=1.45
 crop=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*scale),int((y1-y0)*scale)))
 bx=i*512+18;by=72;canvas.paste(crop,(bx,by));d.text((bx,43),name,font=font,fill='white')
 for n,((k,(x,y)),c) in enumerate(zip(v['points'].items(),colors),1):
  xx=bx+(x-x0)*scale; yy=by+(y-y0)*scale
  d.ellipse((xx-4,yy-4,xx+4,yy+4),fill=c,outline='black');d.text((xx+5,yy-16),str(n),font=small,fill=c,stroke_width=1,stroke_fill='black')
  d.text((bx,417+(n-1)*20),f'{n} {k}: ({x}, {y})',font=small,fill=c)
 if 'eye_image_left' in v['points']:
  a=v['points']['eye_image_left'];b=v['points']['eye_image_right'];v['observed_eye_line_degrees']=round(math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])),2)
 d.text((bx,568),'Manual observation, +/- 4 px; no redrawing',font=small,fill='#c0ccd6')
canvas.save(out/'C_FILM_observed_landmarks_DRAFT.png')
data={'status':'DRAFT/HOLD','source_commit':'2b0f541ea9156b8e4c29e1299dbb7ede9eb783c4','source_path':'reviews/parallel_production_DRAFT_20261014/lane1/A_C_FILM_MODEL_SHEET_DRAFT.png','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_size':[1536,1024],'coordinate_system':'source pixels x right / y down','measurement_method':'manual visual annotations; not automated detection; points approximate +/-4 px','views':views,'identity_constraints':{'fixed':'Use one selected source drawing for expression tests; never regenerate each frame. Freeze chin, nose, ears, hair silhouette and costume. Eyelid, iris, brow and mouth deformation are bounded separate controls.','cross_view':'No inferred 3D landmark identity is certified. Existing drawings have uncalibrated camera, roll and expression; cannot claim a solved model.'}}
(out/'C_FILM_landmarks_DRAFT.json').write_text(json.dumps(data,indent=2))
