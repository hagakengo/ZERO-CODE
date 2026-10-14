"""Reuse prior 0–3s synthesis, soften HF, add quiet correlated wind. No outside samples."""
from pathlib import Path
import wave, array, math, random, json, hashlib
root=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
src=parser.parse_args().source
out=root/'audio'; out.mkdir(parents=True,exist_ok=True)
with wave.open(str(src),'rb') as w:
 assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(48000,2,2)
 a=array.array('h',w.readframes(144000))
random.seed(2026101403)
state=[0.,0.]; wind=[0.,0.]; vals=[]
# Preserve original stereo rain and low city hum; reduce harsh top octave with one-pole LP.
for i in range(144000):
 t=i/48000
 edge=min(1,t/.025,(3-t)/.08)
 slow=.70+.20*math.sin(t*1.4)+.10*math.sin(t*.45)
 common=random.uniform(-1,1)
 for ch in range(2):
  state[ch]+=.62*(a[2*i+ch]/32768-state[ch])
  wind[ch]=.998*wind[ch]+.002*(.7*common+.3*random.uniform(-1,1))
  vals.append((state[ch]*1.15+wind[ch]*.34*slow)*edge)
peak=max(map(abs,vals)); rms=math.sqrt(sum(v*v for v in vals)/len(vals))
pcm=array.array('h',(round(v*32767) for v in vals))
path=out/'city_3s.wav'
with wave.open(str(path),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm.tobytes())
report={'status':'DRAFT/HOLD','duration_s':3,'sample_rate_hz':48000,'channels':2,'samples_per_channel':144000,'peak_dbfs':20*math.log10(peak),'rms_dbfs':20*math.log10(rms),'clipped_samples':sum(abs(v)>=1 for v in vals),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'listening':'UNVERIFIED — no auditory playback capability used','reuse':'Entire prior first 3 seconds, filtered/gain adjusted. Added quiet original deterministic wind noise; retained prior distant city 48/71 Hz hum. No music, voice, lore cues, third-party samples or uploads.'}
(out/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(out/'NOTES.md').write_text('# AI CITY 3秒音響 — DRAFT / HOLD\n\n前回15秒WAVの0–3秒全体を再利用。雨の高域を穏やかにし、低い都市音を維持、弱いステレオ風音を追加。音楽・声・足音・新規設定のキューなし。既存素材は変更していない。\n\n原素材: `reviews/vconte15_static_face_HOLD_20261014/audio/zero_code_draft_audio_48k.wav`。前回ソースを確認し、雨/48・71 Hz都市低音がローカル手続き合成であることを確認。今回の風音も固定seedによるローカル合成。外部素材/外部アップロードなし。\n\n数値検査: 3.000秒、48 kHz、ステレオ、PCM16、144,000 samples/channel。Peak %.2f dBFS、RMS %.2f dBFS、クリップ0。\n\n**実聴・芸術的なミックス評価・知覚的同期は未検証。** 数値検査は音の自然さを保証しない。背景音として使用し、最終的にはヘッドホン/携帯スピーカーの両方で、雨の硬さ、低音の唸り、映像スケールとの整合を確認する。\n' % (report['peak_dbfs'],report['rms_dbfs']))
print(json.dumps(report,ensure_ascii=False,indent=2))
