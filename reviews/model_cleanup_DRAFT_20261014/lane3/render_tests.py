"""Rebuild diagnostic exposure videos; generated drawings are NOT reproducible by this script.
No pixel warp, morphing, or synthesized inbetweens. FFmpeg crops only for timeline assembly.
"""
from pathlib import Path
import subprocess, shutil, csv, json
P=Path(__file__).resolve().parent
ROOT=P.parent
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def run(args):
    subprocess.run(['ffmpeg','-y','-loglevel','error']+args,check=True)
def make(name,source,boxes,sequence,kind):
    folder=P/name; (folder/'keys').mkdir(parents=True,exist_ok=True); (folder/'frames').mkdir(exist_ok=True)
    for key,(x,y,w,h) in enumerate(boxes):
        filt=f'crop={w}:{h}:{x}:{y},scale=640:496:force_original_aspect_ratio=decrease,pad=640:576:(ow-iw)/2:60:color=0x191b1e'
        run(['-i',str(source),'-i',str(ROOT/'lane2/expression_cleanup_sheet_DRAFT.png'),'-filter_complex','[0:v]'+filt+'[base];[1:v]crop=260:50:400:0,scale=320:48[label];[base][label]overlay=160:0','-frames:v','1',str(folder/'keys'/f'key_{key}.png')])
    rows=[]
    for f,key in enumerate(sequence):
        shutil.copyfile(folder/'keys'/f'key_{key}.png',folder/'frames'/f'frame_{f:03d}.png')
        rows.append({'frame':f+1,'time_s':round(f/24,6),'key':key,'source':str(source.relative_to(ROOT)), 'crop_xywh':str(boxes[key]),'method':'held drawing; no interpolation'})
    with (folder/'exposure.csv').open('w') as o:
        w=csv.DictWriter(o,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    for half in (False,True):
        out=folder/('half_speed_24fps.mp4' if half else 'normal_24fps.mp4')
        run(['-framerate','12' if half else '24','-i',str(folder/'frames/frame_%03d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(out)])
    return folder
if __name__=='__main__':
    expression=make('expression_exposure_DRAFT',ROOT/'lane2/expression_cleanup_sheet_DRAFT.png',[(12,95,490,380),(522,95,490,380),(1034,95,490,380)],[0]*8+[1]*8+[2]*8,'3 KEY EXPRESSION COMPARISON')
    # Updated from inspected 2172x724 model sheet: equal source-cell widths, no morph.
    head=make('head_angle_comparison_DRAFT',ROOT/'lane1/head_model_v2_DRAFT.png',[(0,0,724,600),(724,0,724,600),(1448,0,724,600)],[0]*8+[1]*8+[2]*8,'3 ANGLE COMPARISON - NOT A TURN')
    blink=make('blink_key_replacement_DRAFT',ROOT/'lane2/blink_keys_DRAFT.png',[(14,76,700,600),(734,76,700,600),(1454,76,700,600)],[0]*7+[1]*2+[2]*3+[1]*2+[0]*10,'BLINK KEY REPLACEMENT')
    old=ROOT/'reference/previous_expression_DRAFT_24fps.mp4'
    filt="[0:v]scale=640:576:force_original_aspect_ratio=decrease,pad=640:576:(ow-iw)/2:(oh-ih)/2:color=0x191b1e[a];[1:v]scale=640:576[b];[a][b]hstack=inputs=2"
    run(['-i',str(old),'-i',str(expression/'normal_24fps.mp4'),'-filter_complex',filt,'-t','1','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'old_new_expression_comparison_DRAFT_24fps.mp4')])
    run(['-i',str(P/'old_new_expression_comparison_DRAFT_24fps.mp4'),'-vf','setpts=2*PTS,fps=24,tpad=stop_mode=clone:stop_duration=1','-frames:v','48','-r','24','-c:v','libx264','-pix_fmt','yuv420p',str(P/'old_new_expression_comparison_DRAFT_half_speed.mp4')])

    run(['-i',str(old),'-i',str(blink/'normal_24fps.mp4'),'-filter_complex',filt,'-t','1','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'old_new_blink_comparison_DRAFT_24fps.mp4')])

    run(['-i',str(ROOT/'reference/previous_head_volume_DRAFT_24fps.mp4'),'-i',str(head/'normal_24fps.mp4'),'-filter_complex',filt,'-t','1','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'old_new_head_comparison_DRAFT_24fps.mp4')])
