#!/usr/bin/env python3
"""Rebuild the DRAFT/HOLD key-drawing exposure test; Python stdlib + FFmpeg.

No facial drawing, warping, optical-flow, dissolves, camera movement or AI calls.
The PNG sheet is the saved, non-deterministic image-generation source.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPOSURES = [12, 3, 3, 3, 3, 3, 3, 18]
FPS = 24


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True)


def main():
    assert sum(EXPOSURES) == 48
    for folder in ['keys', 'frames', 'qa']:
        (ROOT / folder).mkdir(exist_ok=True)
    sheet = ROOT / 'source/acting_keys_v01_DRAFT_HOLD.png'
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'json', str(sheet)]))
    assert (info['streams'][0]['width'], info['streams'][0]['height']) == (1536, 1024)
    rows = []
    frame = 1
    for key, hold in enumerate(EXPOSURES, 1):
        x, y = ((key - 1) % 4) * 384, ((key - 1) // 4) * 512
        path = ROOT / f'keys/K{key:02d}.png'
        ffmpeg('-i', sheet, '-vf', f'crop=384:512:{x}:{y}', '-frames:v', 1, path)
        for _ in range(hold):
            dest = ROOT / f'frames/frame_{frame:03d}.png'
            shutil.copyfile(path, dest)
            rows.append([frame, f'{(frame-1)/FPS:.6f}', key, hashlib.sha256(dest.read_bytes()).hexdigest()])
            frame += 1
    with (ROOT / 'source/exposure_sheet.csv').open('w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['frame_1based', 'start_seconds', 'key_drawing', 'png_sha256'])
        writer.writerows(rows)
    movie = ROOT / 'protagonist_A_2s_KEY_TEST_DRAFT_HOLD.mp4'
    ffmpeg('-framerate', FPS, '-start_number', 1, '-i', ROOT / 'frames/frame_%03d.png',
           '-frames:v', 48, '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', 16,
           '-pix_fmt', 'yuv420p', '-r', FPS, '-movflags', '+faststart',
           '-metadata', 'title=ZERO CODE A | KEY DRAWING TEST | DRAFT HOLD',
           '-metadata', 'comment=8 drawings exposed over 48 frames. Not a finished animation. User approval pending.', movie)
    # Reference front view is uniformly resized and padded; all test keys are native size.
    ffmpeg('-i', ROOT / 'reference/model_sheet.png', '-i', ROOT / 'keys/K01.png',
           '-i', ROOT / 'keys/K06.png', '-i', ROOT / 'keys/K08.png',
           '-filter_complex', '[0:v]crop=512:528:0:0,scale=384:396,pad=384:512:0:58:color=0xdddddd[r];[r][1:v][2:v][3:v]hstack=inputs=4[out]',
           '-map', '[out]', '-frames:v', 1, ROOT / 'qa/reference_K01_K06_K08.png')
    for frame in [1, 16, 25, 48]:
        ffmpeg('-i', movie, '-vf', f'select=eq(n\\,{frame-1})', '-frames:v', 1,
               ROOT / f'qa/decoded_frame_{frame:03d}.png')
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration:format=duration',
        '-of', 'json', str(movie)]))
    stream = probe['streams'][0]
    assert stream['nb_read_frames'] == '48', probe
    assert stream['r_frame_rate'] == '24/1', probe
    assert abs(float(probe['format']['duration']) - 2) < 0.0001, probe
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(movie), '-f', 'null', '-'], check=True)
    (ROOT / 'qa/technical_probe.json').write_text(json.dumps(probe, indent=2) + '\n')
    print(json.dumps(probe, indent=2))


if __name__ == '__main__':
    main()
