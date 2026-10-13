from pathlib import Path
import json,copy,inspect,math,subprocess,hashlib,csv
from PIL import Image,ImageDraw,ImageFont
import rig_reference as b
O=Path(__file__).resolve().parents[1];R=O.parents[1]
BASE='f12ce0246ad152dbce62873d3893dde3c0e87745'
for n in ['frames','video','verification','keyframes']:(O/n).mkdir(exist_ok=True)
reference=json.loads((O/'source/reference_poses04.json').read_text())
b.font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',25);b.small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',21)
src=inspect.getsource(b.render)
src=src.replace('up=[dx/l,dy/l];back=[dy/l,-dx/l]',"angle=p.get('bag_angle',0); dx,dy=dx*math.cos(angle)-dy*math.sin(angle),dx*math.sin(angle)+dy*math.cos(angle);up=[dx/l,dy/l];back=[dy/l,-dx/l]")
src=src.replace('h[0]+back[0]*24','h[0]+back[0]*24+p.get("bag_offset",0)')
src=src.replace('[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]',"[s[0]+20,s[1]+35],[h[0]+20-p.get('indent',0) if who=='hero' else h[0]+20,h[1]-45],[h[0]+20,h[1]+6],[h[0]-20,h[1]+6]")
src=src.replace('line(a,k,col,2);line(k,f,col,2)','pass # No colored rig lines on clothing')
src=src.replace("line([q['com_x'],545],[q['com_x'],734],(180,57,80),1)",'pass # Mass proxy retained in data only')
src=src.replace("if abs(point[1]-734)<1e-6:line([point[0]-4,738],[point[0]+4,738],(30,145,80),2)",'pass # No green contact guides')
src=src.replace("    t=p['proposal_frame']", """    if 19<=p['proposal_frame']<=32:
        j=p['enemy']['joints'];a=j['elbow'];f=j['fist']
        line(a,f,(75,82,85),9);line(a,f,(158,167,169),7)
        x,y=pt(f);d.polygon([(x-24,y-11),(x+12,y-11),(x+18,y-5),(x+18,y+10),(x-24,y+10)],fill=(158,167,169),outline=(70,77,80),width=2)
    t=p['proposal_frame']""")
src=src.replace('ZERO CODE / COUNTERATTACK DESIGN / P','ZERO CODE / CONTACT ALTERNATIVE DRAFT / Q')
src=src.replace("('1-frame' if 20<=t<=29 else '2-frame')","'24fps / independent draft'")
src=src.replace('PROPOSAL ONLY / provisional opponent / mass proxy','04 HOLD / roles unresolved / no pilot F allocation')
ns=dict(b.__dict__);exec(src,ns);render=ns['render']
# Q is local independent frame. Not a pilot F-number or an approved retime.
map_p=[round(q*22/19) for q in range(20)]+[23,24,25,25,25,26,27,28]+[round(29+(q-28)*12/13) for q in range(28,42)]+list(range(42,72))
assert len(map_p)==72 and map_p[42:]==list(range(42,72))
poses=[];rows=[]
for q,ref in enumerate(map_p):
 p=copy.deepcopy(reference[ref]);p['proposal_frame']=q;p['source_P']=ref
 p['bag_angle']*=0.58;p['bag_offset']*=0.7
 p['phase']='COMPRESSION HOLD / HYPOTHESIS' if 22<=q<=24 else ('CONTACT' if q==21 else b.phase(ref))
 poses.append(p);im=render(p);im.save(O/'frames'/f'Q{q:03}.png')
 contour=2*(p['hero']['joints']['hip'][0]+20-p['indent']);fist_left=2*p['enemy']['joints']['fist'][0]-24
 rows.append(dict(Q=q,source_design04_P=ref,pilot_F='UNASSIGNED',seconds=q/24,phase=p['phase'],fist_left_px=fist_left,abdomen_contour_px=contour,gap_px=fist_left-contour,indent_px=2*p['indent'],bag_angle_rad=p['bag_angle'],bag_offset_px=2*p['bag_offset'],hero_ground_contacts='|'.join(p['hero']['contacts']),image_sha256=hashlib.sha256((O/'frames'/f'Q{q:03}.png').read_bytes()).hexdigest()))
with (O/'exposure_sheet.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
(O/'source/poses_alternative.json').write_text(json.dumps(poses,indent=2))
video=O/'video/contact_alternative_DRAFT_24fps.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(O/'frames/Q%03d.png'),'-frames:v','72','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
keys=[0,16,20,21,22,24,25,29,33,38,42,50,51,71]
sheet=Image.new('RGB',(2160,1920),(231,229,220))
for i,q in enumerate(keys):
 im=Image.open(O/'frames'/f'Q{q:03}.png');im.save(O/'keyframes'/f'Q{q:03}.png');im=im.crop((160,700,1060,1530)).resize((540,498));x=i%4*540;y=i//4*480
 sheet.paste(im.resize((540,440)),(x,y+40));ImageDraw.Draw(sheet).text((x+10,y+8),f'Q{q:03} / ref P{map_p[q]:03}',font=b.small,fill='black')
sheet.save(O/'keyframes.png')
contact=Image.new('RGB',(2160,960),(231,229,220))
for i,q in enumerate([20,21,22,25]):
 im=Image.open(O/'frames'/f'Q{q:03}.png').crop((420,880,740,1140)).resize((540,440));contact.paste(im,(i*540,70));d=ImageDraw.Draw(contact);d.text((i*540+10,20),f'Q{q:03} gap {rows[q]["gap_px"]:.1f}px',font=b.font,fill='black')
contact.crop((0,0,2160,520)).save(O/'verification/contact_closeups.png')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]));s=probe['streams'][0]
assert (s['width'],s['height'],s['nb_read_frames'],s['avg_frame_rate'])==(1080,1920,'72','24/1')
assert len(probe['streams'])==1 and float(probe['format']['duration'])==3
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
assert all(poses[q]['hero']==reference[q]['hero'] for q in range(42,72))
assert all(poses[q]['hero']==poses[22]['hero'] for q in range(22,25))
# Head/body pause is experimental; it cannot prove impact perception.
checks={'technical':'PASS','direction':'UNJUDGED','normal_speed_continuous_viewing':'NOT_PERFORMED','dimensions':[1080,1920],'fps':'24/1','frames':72,'duration_seconds':3,'full_decode':'PASS','no_audio':True,'compression_hold_Q022_024':True,'retreat_hero_Q042_071_equals_design04_P042_071':True,'contact_Q021_gap_px':rows[21]['gap_px'],'precontact_Q020_gap_px':rows[20]['gap_px'],'compression_Q022_gap_px':rows[22]['gap_px'],'peak_bag_rotation_radians':max(abs(p['bag_angle']) for p in poses),'pilot_F_assignment':'NONE','probe':probe}
(O/'verification/technical_checks.json').write_text(json.dumps(checks,indent=2))
tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R,text=True).splitlines();bad=[]
for name in tracked:
 original=subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=R)
 if not (R/name).exists() or hashlib.sha256(original).digest()!=hashlib.sha256((R/name).read_bytes()).digest():bad.append(name)
assert not bad,bad
(O/'verification/protected_files.json').write_text(json.dumps({'baseline':BASE,'count':len(tracked),'changed':bad,'all_original_files_byte_equal':True},indent=2))
print(json.dumps({k:v for k,v in checks.items() if k!='probe'},indent=2))
