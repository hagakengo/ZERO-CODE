"""Original deterministic local rain/city synthesis, no external samples. DRAFT/HOLD."""
from pathlib import Path
import argparse, array, hashlib, json, math, random, wave

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
sr, duration = 48000, 3
rng = random.Random(2026101426)
states = [0.0, 0.0]
slow = [0.0, 0.0]
phase = 0.0
vals = []
# Small isolated droplets over the diffuse rain bed, intentionally understated.
drops = [(rng.uniform(.04, 2.95), rng.uniform(.001, .003), rng.uniform(950, 2100), rng.uniform(-.8, .8)) for _ in range(105)]
for i in range(sr * duration):
    t = i / sr
    common = rng.uniform(-1, 1)
    progress = max(0, min(1, (t - .5) / 2.0))
    vehicle_env = math.sin(math.pi * progress) ** 2 if .5 < t < 2.5 else 0
    # Distant muted electric vehicle: smooth broad pass, restrained Doppler.
    phase += 2 * math.pi * (116 - 22 * progress) / sr
    vehicle = vehicle_env * (.010 * math.sin(phase) + .003 * math.sin(phase * 2.01))
    pan = -.65 + 1.3 * progress
    droplets = [0.0, 0.0]
    for start, amp, freq, pos in drops:
        dt = t - start
        if 0 <= dt < .028:
            v = amp * math.exp(-dt * 250) * math.sin(2 * math.pi * freq * dt)
            droplets[0] += v * math.sqrt((1-pos)/2)
            droplets[1] += v * math.sqrt((1+pos)/2)
    edge = min(1, t/.035, (duration-t)/.065)
    for ch in range(2):
        n = .30 * common + .70 * rng.uniform(-1, 1)
        states[ch] += .23 * (n-states[ch])
        slow[ch] += .007 * (n-slow[ch])
        rain = .135 * (states[ch]-.55*slow[ch])
        city = .004 * math.sin(2*math.pi*57*t + ch*.3) + .002 * math.sin(2*math.pi*83*t)
        gain = math.sqrt((1 + (-pan if ch == 0 else pan))/2)
        vals.append(edge * (rain + city + vehicle*gain + droplets[ch]))
peak = max(map(abs, vals))
rms = math.sqrt(sum(v*v for v in vals)/len(vals))
pcm = array.array('h', (round(v*32767) for v in vals))
with wave.open(str(args.output), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
report = {'status':'DRAFT/HOLD', 'duration_seconds':duration, 'sample_rate_hz':sr, 'channels':2, 'pcm_bits':16, 'samples_per_channel':sr*duration, 'peak_dbfs':20*math.log10(peak), 'rms_dbfs':20*math.log10(rms), 'clipped_samples':sum(abs(v)>=1 for v in vals), 'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(), 'vehicle_se_seconds':[.5,2.5], 'listening':'UNVERIFIED: no auditory listening performed', 'perceptual_sync':'UNVERIFIED: SE envelope scheduled to 0.5–2.5 s; final picture not auditioned', 'provenance':'Original procedural Python standard-library synthesis, fixed seed. No external service, samples, uploads, music or voice.'}
qa = Path(__file__).resolve().parents[1] / 'AUDIO_QA.json'
qa.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
