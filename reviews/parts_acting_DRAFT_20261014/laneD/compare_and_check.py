"""Build labelled comparisons and independently probe/decode delivered videos.
Usage: python compare_and_check.py A_NORMAL.mp4 B_NORMAL.mp4 OLD_NORMAL.mp4
Requires ffmpeg/ffprobe and Pillow. No drawing synthesis is performed here.
"""
from pathlib import Path
import subprocess, json, sys, shutil
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'

def ff(args):
    subprocess.run(['ffmpeg','-y','-v','error',*map(str,args)],check=True)

def compare(inputs, labels, name, crops):
    panels=[]
    font=ImageFont.truetype(FONT,20)
    folder=HERE/'decoded'/name
    folder.mkdir(parents=True,exist_ok=True)
    for i,(path,label,crop) in enumerate(zip(inputs,labels,crops)):
        part=folder/str(i); part.mkdir(exist_ok=True)
        ff(['-i',path,'-vf',crop+',fps=24,scale=640:354:force_original_aspect_ratio=decrease','-frames:v','24',part/'f%03d.png'])
        panels.append(sorted(part.glob('f*.png')))
    for frame in range(24):
        im=Image.new('RGB',(640*len(inputs),408),(23,28,34));d=ImageDraw.Draw(im)
        for i,(files,label) in enumerate(zip(panels,labels)):
            q=Image.open(files[frame]).convert('RGB')
            im.paste(q,(i*640+(640-q.width)//2,48))
            d.text((i*640+16,14),label,font=font,fill='white')
        im.save(folder/f'comparison_{frame:03d}.png')
    normal=HERE/f'{name}_normal_24fps_DRAFT.mp4'
    ff(['-framerate','24','-i',folder/'comparison_%03d.png','-frames:v','24','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',normal])
    ff(['-i',normal,'-vf','setpts=2*PTS,fps=24,tpad=stop_mode=clone:stop_duration=1','-frames:v','48','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',HERE/f'{name}_half_24fps_DRAFT.mp4'])
    return normal

def contact(path,name):
    folder=HERE/'decoded'/name
    folder.mkdir(parents=True,exist_ok=True)
    ff(['-i',path,folder/'f%03d.png'])
    files=sorted(folder.glob('f*.png'))
    tilew=480; tileh=230
    sheet=Image.new('RGB',(tilew*4,tileh*6),(22,27,33))
    d=ImageDraw.Draw(sheet); font=ImageFont.truetype(FONT,16)
    for i,file in enumerate(files[:24]):
        im=Image.open(file).convert('RGB'); im.thumbnail((tilew,tileh-26))
        x=i%4*tilew; y=i//4*tileh
        sheet.paste(im,(x+(tilew-im.width)//2,y+26))
        d.text((x+8,y+4),f'F{i+1:02d}  {i/24:.3f}s / DRAFT-HOLD',font=font,fill='white')
    sheet.save(HERE/f'{name}_all24_DRAFT.png')

def checks():
    rows=[]
    for path in sorted(ROOT.rglob('*.mp4')):
        p=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)],capture_output=True,text=True,check=True)
        s=json.loads(p.stdout)['streams'][0]
        decode=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True)
        expected=48 if ('half' in path.name or 'half_speed' in path.name) else 24
        passed=s.get('r_frame_rate')=='24/1' and int(s.get('nb_read_frames','0'))==expected and abs(float(s.get('duration','0'))-expected/24)<.001 and decode.returncode==0
        rows.append({'path':str(path.relative_to(ROOT)),**s,'expected_frames':expected,'full_decode':decode.returncode==0,'technical_pass':passed,'decode_errors':decode.stderr[:1000]})
    (HERE/'TECHNICAL_QA.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'videos':len(rows),'pass':sum(r['technical_pass'] for r in rows),'fail':[r['path'] for r in rows if not r['technical_pass']]},indent=2))

if __name__=='__main__':
    if len(sys.argv)==4:
        a,b,old=map(Path,sys.argv[1:])
        acrop='crop=1024:566:0:40'; bcrop='crop=768:424:0:150'
        ab=compare([a,b],['A - PARTS / HOLD','B - DRAWINGS / HOLD'],'AB_comparison',[acrop,bcrop])
        prev=compare([old,a,b],['PREVIOUS - DIFFERENT TEST','A - PARTS / HOLD','B - DRAWINGS / HOLD'],'previous_AB',['crop=640:496:0:60',acrop,bcrop])
        contact(ab,'AB_comparison'); contact(prev,'previous_AB')
        preview=Image.new('RGB',(1280,438*4),(23,28,34));d=ImageDraw.Draw(preview)
        font=ImageFont.truetype(FONT,20)
        for row,(f,label) in enumerate([(0,'F01 / gaze'),(9,'F10 / blink'),(17,'F18 / slight smile'),(23,'F24 / notice')]):
            q=Image.open(HERE/'decoded/AB_comparison'/f'comparison_{f:03d}.png')
            preview.paste(q,(0,row*438+30))
            d.text((16,row*438+4),label+' - DRAFT / HOLD',font=font,fill='#e9bf73')
        preview.save(HERE/'review_preview_DRAFT.png')
        shutil.rmtree(HERE/'decoded')
    checks()
