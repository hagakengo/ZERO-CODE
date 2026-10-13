"""Extract a strict 6x2 sheet and expose saved drawings. No motion synthesis."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv, json, subprocess, tempfile, shutil

ROOT = Path(__file__).resolve().parents[1]
FPS = 24
EXPOSURES = [8, 6, 4, 6, 6, 6]  # 36 frames = 1.5 sec, proposed review timing

def run(args):
    subprocess.run(args, check=True, capture_output=True)

def main():
    sheet = Image.open(ROOT / 'images/A1_A2_action_keys_DRAFT.png').convert('RGB')
    width, height = sheet.size
    assert width % 6 == 0 and height % 2 == 0, sheet.size
    cw, ch = width // 6, height // 2
    keys = ROOT / 'images/keys'
    video = ROOT / 'video'
    keys.mkdir(exist_ok=True)
    video.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 25)
        small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
    except OSError:
        font = small = ImageFont.load_default()
    # One identical extraction and scale for every key; no per-key registration or warp.
    pair_images = []
    for col in range(6):
        canvas = Image.new('RGB', (1080, 1080), '#edf0f2')
        d = ImageDraw.Draw(canvas)
        d.text((24, 12), 'ZERO CODE | DRAFT / HOLD | KEY POSE TEST', font=font, fill='#1d2830')
        d.text((24, 47), 'A1 left / A2 right | proposed timing, no inbetweens | 24 fps', font=small, fill='#1d2830')
        for row, name in enumerate(['A1', 'A2']):
            crop = sheet.crop((col*cw, row*ch, (col+1)*cw, (row+1)*ch))
            crop.save(keys / f'{name}_K{col+1}.png')
            scaled = crop.resize((500, 1000), Image.Resampling.LANCZOS)
            canvas.paste(scaled, (20+row*540, 80))
        pair_images.append(canvas)
    frame_keys = [k for k, count in enumerate(EXPOSURES) for _ in range(count)]
    with (ROOT/'exposure.csv').open('w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['test_frame','time_seconds','A1_key','A2_key','status'])
        for i, k in enumerate(frame_keys):
            writer.writerow([i, f'{i/FPS:.6f}', f'A1_K{k+1}', f'A2_K{k+1}', 'DRAFT_HOLD'])
    with tempfile.TemporaryDirectory(prefix='zero-code-poses-') as tmp:
        tmp = Path(tmp)
        for i, k in enumerate(frame_keys):
            pair_images[k].save(tmp/f'{i:04d}.png')
        normal = video/'A1_A2_pose_test_normal_DRAFT.mp4'
        run(['ffmpeg','-y','-v','error','-framerate',str(FPS),'-i',str(tmp/'%04d.png'),
             '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-vf','setsar=1',
             '-movflags','+faststart',str(normal)])
        run(['ffmpeg','-y','-v','error','-stream_loop','3','-i',str(normal),
             '-c','copy','-movflags','+faststart',str(video/'A1_A2_pose_test_normal_4loops_DRAFT.mp4')])
    result = {}
    for movie in sorted(video.glob('*.mp4')):
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
            '-select_streams','v:0','-show_entries',
            'stream=width,height,r_frame_rate,nb_read_frames,pix_fmt,sample_aspect_ratio:format=duration',
            '-of','json',str(movie)]))
        run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'])
        s = probe['streams'][0]
        expected = 144 if '4loops' in movie.name else 36
        assert (s['width'],s['height'],s['r_frame_rate'],int(s['nb_read_frames'])) == (1080,1080,'24/1',expected)
        result[movie.name] = {**s, 'duration':probe['format']['duration'], 'full_decode':'PASS'}
    (ROOT/'verification/video_technical.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
