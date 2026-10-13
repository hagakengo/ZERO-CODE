"""Original deterministic procedural synthesis; no recordings or external samples."""
from pathlib import Path
import array,csv,hashlib,json,math,random,wave,subprocess
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SR=48000; SPF=2000
CUES=[('A01',0,72,'air',True),('A02',72,144,'step',True),('A03',144,209,'cloth',True),('A04',209,216,'silence',True),('A05',216,230,'step',True),('A06',230,246,'cloth',True),('A07',246,253,'cloth',False),('A08',253,257,'contact',False),('A09',257,282,'cloth',False),('A10',282,300,'step',False),('A11',300,309,'tail',False),('A12',309,360,'silence',True)]
def write(path,x):
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,SR,0,'NONE','not compressed')); w.writeframes(x.tobytes())
def synth(kind,n,seed):
    rng=random.Random(seed); x=array.array('h'); low=0.; last=0.
    # One isolated gesture per cue; no invented repeating footfall cadence.
    for i in range(n):
        t=i/SR; u=i/max(n-1,1); noise=rng.uniform(-1,1); low=.92*low+.08*noise
        fade=min(1,t/.015,(n-1-i)/(SR*.025)); fade=max(0,fade)
        if kind=='air': y=.012*low*(.7+.3*math.sin(2*math.pi*.27*t))
        elif kind=='step':
            local=t-.06; y=0 if local<0 else .18*math.exp(-local*22)*(math.sin(2*math.pi*(105*local-30*local*local))+.45*low)
        elif kind=='cloth': y=.085*(noise-low)*math.sin(math.pi*u)**2*(.65+.35*math.sin(2*math.pi*17*t))
        elif kind=='contact': y=.18*math.exp(-t*48)*(.6*noise+math.sin(2*math.pi*155*t))
        elif kind=='tail': y=.04*low*math.exp(-t*15)
        else:y=0
        x.append(round(max(-.95,min(.95,y*fade))*32767))
    return x

def main():
    (ROOT/'audio').mkdir(exist_ok=True); (ROOT/'verification').mkdir(exist_ok=True)
    mix=array.array('h',[0])*(15*SR); rows=[]; checks=[]
    for idx,(cue,start,end,kind,inmix) in enumerate(CUES):
        x=synth(kind,(end-start)*SPF,10413+idx); name=f'{cue}_{kind}_DRAFT.wav'; write(ROOT/'audio'/name,x)
        if inmix:mix[start*SPF:end*SPF]=x
        rows.append(dict(status='DRAFT',cue=cue,start_frame=start,end_frame_exclusive=end,sample_start=start*SPF,sample_end=end*SPF,kind=kind,mix='included-provisional' if inmix else 'AUDITION_ONLY_EXCLUDED',file='audio/'+name,rights_source='Original arithmetic + seeded Python random noise; no external audio',dependency='design04-HOLD' if cue in ['A07','A08','A09'] else ('downstream-sync-pending' if cue in ['A10','A11'] else 'visual-sync-pending' if kind not in ['air','silence'] else 'independent')))
        checks.append({'file':name,'samples':len(x),'peak_integer':max(map(abs,x)),'sha256':hashlib.sha256((ROOT/'audio'/name).read_bytes()).hexdigest()})
    write(ROOT/'audio'/'pilot15_audio_PROVISIONAL_DRAFT.wav',mix)
    with (ROOT/'cue_sheet_DRAFT.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys()); writer.writeheader();writer.writerows(rows)
    for a,b in [(209,216),(246,309),(309,360)]:assert all(v==0 for v in mix[a*SPF:b*SPF])
    assert len(mix)==720000 and max(map(abs,mix))<32767
    decoded=[]
    for p in sorted((ROOT/'audio').glob('*.wav')):
        result=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
        assert result.returncode==0 and not result.stderr;decoded.append(p.name)
    result={'status':'TECHNICAL_PASS','sample_rate':SR,'channels':1,'pcm_bits':16,'duration_seconds':15,'samples':len(mix),'sample_per_frame_24fps':SPF,'silence_windows_frames_exclusive':[[209,216],[309,360]],'hold_exclusion_frames_exclusive':[246,309],'mix_peak_integer':max(map(abs,mix)),'wav_checks':checks,'full_decode_pass':decoded,'auditory_review':'NOT_PERFORMED','visual_sync':'NOT_APPROVED','direction':'UNJUDGED'}
    (ROOT/'verification'/'technical_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    im=Image.new('RGB',(1600,820),'#0b1220'); d=ImageDraw.Draw(im)
    d.text((35,22),'ZERO CODE | LANE C | ORIGINAL SYNTHETIC AUDIO DRAFT | 48 kHz / 16-bit mono',(220,235,245))
    d.text((35,45),'PROVISIONAL TIMING - NOT APPROVED SYNC | HELD A07-A11 EXCLUDED | NO VOICE / HUD',(220,235,245))
    for idx,(cue,a,b,kind,inc) in enumerate(CUES):
        y=85+idx*57;d.text((25,y),f'{cue} F{a:03}-{b-1:03} {kind} '+('PROVISIONAL' if inc else 'AUDITION ONLY'),(180,205,220))
        for px in range(1000):
            lo=px*len(mix)//1000;hi=(px+1)*len(mix)//1000;xx=540+px
            if lo//SPF>=a and lo//SPF<b:
                value=max(map(abs,mix[lo:hi]));amp=int(value/32768*100)
                d.line((xx,y+12-amp,xx,y+12+amp),fill='#62c5cb' if kind!='silence' else '#8ca4b0')
    im.save(ROOT/'waveform_overview.png')
if __name__=='__main__':main()
