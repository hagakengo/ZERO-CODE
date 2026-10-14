"""Original procedural environment/audio layout experiment, DRAFT/HOLD. Stdlib only."""
from pathlib import Path
import math, random, wave, struct, json, hashlib
P=Path(__file__).resolve().parent
SR=48000; N=SR*3
# Layered SVG, true vector primitives, no external/raster dependencies.
s=['''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1080" height="1920" viewBox="0 0 1080 1920"><title>AI CITY environment layout — DRAFT / HOLD</title><desc>Original vector layout prototype. No character, logo, enemy, HUD or story event. Central acting space deliberately reserved. Not approved production background.</desc><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#060c19"/><stop offset="1" stop-color="#203c55"/></linearGradient><linearGradient id="road" x2="0" y2="1"><stop stop-color="#132b3d"/><stop offset="1" stop-color="#060b13"/></linearGradient><linearGradient id="fog" x2="0" y2="1"><stop stop-color="#57819b" stop-opacity="0"/><stop offset=".6" stop-color="#57819b" stop-opacity=".2"/><stop offset="1" stop-color="#57819b" stop-opacity="0"/></linearGradient></defs>''']
def group(name): s.append(f'<g id="{name}" data-layer="{name}">')
def end(): s.append('</g>')
group('01_sky'); s.append('<rect width="1080" height="1920" fill="url(#sky)"/>');end()
group('02_distant_towers')
for x,y,w,h in [(100,450,100,780),(250,280,110,930),(420,650,75,530),(570,350,95,860),(700,530,90,690),(840,180,140,1040)]:
 s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#142a3d"/><path d="M{x+w-8} {y+25}v{h-35}" stroke="#297c96" stroke-width="3"/>')
end();group('03_mid_architecture')
for pts in ['0,50 240,160 240,1280 0,1500','1080,0 810,200 810,1280 1080,1500','40,360 170,400 170,1260 40,1350','1040,370 905,420 905,1300 1040,1420']:
 s.append(f'<polygon points="{pts}" fill="#0a1523" stroke="#223a4d" stroke-width="3"/>')
s.append('<path d="M230 480H825V535H230Z" fill="#0a1420" stroke="#26485d" stroke-width="3"/><path d="M240 538H810" stroke="#39a4b8" stroke-opacity=".65" stroke-width="4"/>')
for x in [70,130,940,1000]:
 for y in range(490,1160,110): s.append(f'<path d="M{x} {y}h16v35h-16Z" fill="#2b6179" opacity=".5"/>')
end();group('04_wet_street');s.append('<path d="M0 1920V1400L435 1180H650L1080 1400V1920Z" fill="url(#road)"/>')
for x in [-300,0,270,810,1080,1380]: s.append(f'<path d="M540 1180L{x} 1920" stroke="#243e50" stroke-width="3"/>')
for y in [1260,1370,1550,1820]:s.append(f'<path d="M0 {y}H1080" stroke="#1c3447" stroke-width="3"/>')
for x,y,w in [(200,1450,110),(750,1510,130),(130,1720,130),(860,1820,170),(330,1300,60)]:s.append(f'<path d="M{x} {y}h{w}l-25 13h-{w}Z" fill="#38a0b8" opacity=".22"/>')
end();group('05_foreground_occlusion');s.append('<path d="M0 1920V1380L120 1320V1920Z M1080 1920V1350L990 1305V1920Z" fill="#040912"/>');end()
group('06_environment_lights');s.append('<path d="M228 700v410M820 750v350" stroke="#3bb8ca" opacity=".6" stroke-width="5"/><rect x="930" y="1230" width="9" height="25" fill="#bd794d"/>');end()
group('07_fog');s.append('<rect y="850" width="1080" height="700" fill="url(#fog)"/>');end();s.append('</svg>')
(P/'AI_CITY_background_DRAFT.svg').write_text('\n'.join(s))
# Deterministic sound synthesis, no samples, no musical melody.
rng=random.Random(20261014)
air=[]; hum=[]; cue=[]; state=0.
for i in range(N):
 t=i/SR; fade=min(1,t/.035,(3-t)/.12); fade=max(0,fade)
 state=.985*state+.015*rng.uniform(-1,1)
 a=state*.13*fade
 h=(math.sin(2*math.pi*52*t)*.022+math.sin(2*math.pi*104*t)*.006)*(1+.1*math.sin(2*math.pi*.7*t))*fade
 dt=t-1.0
 c=0.
 if dt>=0:
  env=(1-math.exp(-dt*100))*math.exp(-dt*9)
  c=(math.sin(2*math.pi*(720*dt-70*dt*dt))*.065+math.sin(2*math.pi*1093*dt)*.019)*env*fade
 air.append(a);hum.append(h);cue.append(c)
def wav(name, arr, pan=0):
 left=math.sqrt((1-pan)/2);right=math.sqrt((1+pan)/2)
 with wave.open(str(P/name),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
  w.writeframes(b''.join(struct.pack('<hh',round(max(-1,min(1,v*left))*32767),round(max(-1,min(1,v*right))*32767)) for v in arr))
for name,arr,pan in [('stem_air_DRAFT.wav',air,0),('stem_city_hum_DRAFT.wav',hum,-.15),('stem_notice_cue_DRAFT.wav',cue,.55)]:wav(name,arr,pan)
# Mix retains actual stem panning.
with wave.open(str(P/'mix_3s_DRAFT.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
 data=[];peak=0.;sumsq=0.
 for a,h,c in zip(air,hum,cue):
  for val in [a/math.sqrt(2)+h*math.sqrt(1.15/2)+c*math.sqrt(.45/2),a/math.sqrt(2)+h*math.sqrt(.85/2)+c*math.sqrt(1.55/2)]:
   peak=max(peak,abs(val));sumsq+=val*val;data.append(round(val*32767))
 w.writeframes(struct.pack('<'+'h'*len(data),*data))
manifest={'status':'DRAFT/HOLD','audio_seconds':3,'sample_rate':SR,'channels':2,'samples_per_channel':N,'peak_dbfs':20*math.log10(peak),'rms_dbfs':20*math.log10(math.sqrt(sumsq/(2*N))),'cue_onset_seconds':1.0,'cue_onset_frame_24fps_zero_based':24,'cue_onset_frame_one_based':25,'seed':20261014,'rights':'Original procedural synthesis; no samples, recordings, melody or external media.'}
manifest['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.glob('*')) if p.suffix in ['.svg','.wav']}
(P/'qa_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
