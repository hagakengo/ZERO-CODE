"""ZERO CODE draft animatic: deterministic original synthesis, no external samples."""
import math, random, wave, struct, json
from pathlib import Path
SR=48000
DURATION=15
N=SR*DURATION
random.seed(20261014)
left=[0.0]*N
right=[0.0]*N

def add(start,duration,fn,gain=1.0,pan=0.0):
    n=int(duration*SR); off=int(start*SR)
    for j in range(n):
        if off+j>=N: break
        v=fn(j/SR,j)*gain
        left[off+j]+=v*math.sqrt((1-pan)/2)
        right[off+j]+=v*math.sqrt((1+pan)/2)

def edge(t,d,fade=.12):
    return max(0,min(1,t/fade,(d-t)/fade))

# Low environmental bed; deliberately ends before the face shot.
add(0,6,lambda t,j:(math.sin(2*math.pi*48*t)+.35*math.sin(2*math.pi*71*t))*edge(t,6,.5),.055)
# Rain: soft high frequency random texture, with sparse tiny transients.
prev=0.0
rain=[]
for j in range(3*SR):
    v=random.uniform(-1,1)
    rain.append((v-prev)*.045)
    prev=v
add(0,3,lambda t,j:rain[j]*edge(t,3,.18),1,-.20)
add(0,3,lambda t,j:rain[(j+371)%len(rain)]*edge(t,3,.18),.9,.25)
# Wind, gently smoothed noise.
wind=[]; state=0.0
for j in range(3*SR):
    state=.995*state+.005*random.uniform(-1,1)
    wind.append(state)
add(3,3,lambda t,j:wind[j]*edge(t,3,.3)*(.7+.3*math.sin(t*2)),.65,.08)
# Offscreen approach footsteps; do not imply visible locomotion.
for k,when in enumerate((3.18,3.83,4.49,5.16)):
    noise=[random.uniform(-1,1) for _ in range(int(.18*SR))]
    add(when,.18,lambda t,j,noise=noise:(.7*math.sin(2*math.pi*90*t)*math.exp(-t*40)+.25*noise[j]*math.exp(-t*65)),.17,(-.12 if k%2 else .12))
# City power-loss impact, decay to exact silence by 6.8 s.
add(6,.8,lambda t,j:(math.sin(2*math.pi*(52*t-14*t*t))+.23*math.sin(2*math.pi*105*t))*math.exp(-t*8)*min(1,t/.006)*edge(t,.8,.04),.36)
# 6.8-11.0 is exact digital silence (including 8-11 face shot).
# B's short electronic cue, no voice or lore.
add(11.18,.32,lambda t,j:(math.sin(2*math.pi*659.255*t)+.25*math.sin(2*math.pi*1318.51*t))*edge(t,.32,.025)*math.exp(-t*4),.11,-.12)
# Original short closing chord; soft onset, resolved fade before end.
for hz,g in ((55,.08),(110,.055),(164.8138,.035),(220,.025)):
    add(13,2,lambda t,j,hz=hz:math.sin(2*math.pi*hz*t)*edge(t,2,.18)*(.85-.25*t),g)
peak=max(max(abs(x) for x in left),max(abs(x) for x in right))
# Fixed safe headroom, no clipping or automatic loudness claims.
scale=min(1,.70/peak)
left=[x*scale for x in left]; right=[x*scale for x in right]
p=Path(__file__).parent
with wave.open(str(p/'zero_code_draft_audio_48k.wav'),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    data=bytearray()
    for l,r in zip(left,right):data.extend(struct.pack('<hh',round(l*32767),round(r*32767)))
    w.writeframes(data)
report={'status':'DRAFT/HOLD','duration_seconds':15,'sample_rate':SR,'channels':2,'samples_per_channel':N,'format':'PCM signed 16 bit','peak_dbfs':20*math.log10(peak*scale),'rms_dbfs':20*math.log10(math.sqrt(sum(x*x+y*y for x,y in zip(left,right))/(2*N))),'exact_silence_seconds':[6.8,11.0],'face_shot_silence_verified':all(x==0 for x in left[8*SR:11*SR]+right[8*SR:11*SR]),'source':'Original deterministic procedural synthesis; no external samples, uploads, or generated music services.','limitations':'Temporary sound design. No mix/master approval. Footsteps are offscreen approach cues; picture must not imply synchronized visible steps.'}
(p/'audio_measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
