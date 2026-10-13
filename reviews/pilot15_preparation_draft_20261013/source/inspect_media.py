#!/usr/bin/env python3
"""DRAFT read-only media inspection. Numerical PASS never means director approval."""
import argparse, hashlib, json, subprocess, sys
from fractions import Fraction
from pathlib import Path

PROFILES = {
    'design04': (1080, 1920, 72, False),
    'pilot-silent': (1080, 1920, 360, False),
    'pilot-audio': (1080, 1920, 360, True),
    'legacy-pilot': (720, 1280, 360, True),
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, choices=PROFILES)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    out = {'status': 'DRAFT', 'profile': args.profile, 'input': str(args.input),
           'director_approval': 'NOT_ASSESSED', 'rights': 'NOT_ASSESSED',
           'silence_windows_and_loudness': 'NOT_ASSESSED'}
    try:
        data = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-count_frames', '-show_streams',
            '-show_format', '-show_frames', '-show_entries',
            'stream:format:frame=media_type,best_effort_timestamp_time',
            '-of', 'json', str(args.input)], text=True))
        video = [s for s in data['streams'] if s['codec_type'] == 'video']
        audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
        if len(video) != 1:
            raise ValueError('Expected exactly one video stream')
        v = video[0]
        width, height, count, needs_audio = PROFILES[args.profile]
        timestamps = [Fraction(f['best_effort_timestamp_time']) for f in data['frames']
                      if f['media_type'] == 'video']
        cadence = len(timestamps) == count and all(
            abs((b-a)-Fraction(1,24)) <= Fraction(2,1000000)
            for a,b in zip(timestamps,timestamps[1:]))
        checks = {
            'resolution': (v['width'],v['height']) == (width,height),
            'aspect_9_16': v['width'] * 16 == v['height'] * 9,
            'pixel_aspect_policy': v.get('sample_aspect_ratio') == '1:1' or (args.profile in ('design04','legacy-pilot') and v.get('sample_aspect_ratio') is None),
            'no_rotation': not any(int(s.get('rotation',0)) % 360 for s in v.get('side_data_list',[])),
            'fps_average_24': Fraction(v['avg_frame_rate']) == 24,
            'fps_reported_24': Fraction(v['r_frame_rate']) == 24,
            'decoded_frames': int(v['nb_read_frames']) == count,
            'timestamp_cadence_24': cadence,
            'video_duration': abs(Fraction(v['duration'])-Fraction(count,24)) <= Fraction(1,1000),
            'h264': v['codec_name'] == 'h264',
            'yuv420p': v['pix_fmt'] == 'yuv420p',
            'audio_presence': bool(audio) == needs_audio,
        }
        decode = subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(args.input),
                                 '-f','null','-'],capture_output=True,text=True)
        checks['full_decode'] = decode.returncode == 0
        h = hashlib.sha256()
        with args.input.open('rb') as f:
            for block in iter(lambda: f.read(1024*1024),b''): h.update(block)
        out['warnings'] = ([] if v.get('sample_aspect_ratio') == '1:1' else ['Pixel aspect ratio is not explicitly 1:1; legacy profile permits absent metadata. Display aspect is not proven.'])
        out.update(sha256=h.hexdigest(), bytes=args.input.stat().st_size,
                   checks=checks, technical_pass=all(checks.values()),
                   video=v, audio_stream_count=len(audio), decode_errors=decode.stderr)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        out.update(technical_pass=False,error=str(exc))
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['technical_pass'] else 1

if __name__ == '__main__': sys.exit(main())
