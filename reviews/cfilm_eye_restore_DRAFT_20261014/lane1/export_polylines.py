import xml.etree.ElementTree as E,re,json
from pathlib import Path
p=Path('outputs/eye_restore_DRAFT_20261014/lane1/C_face_vector_ROUGH_DRAFT.svg'); root=E.parse(p).getroot(); result=[]
def walk(el,style={},group=''):
 st={**style,**el.attrib}; group=el.get('id',group)
 if el.tag.endswith('path'):
  tok=re.findall(r'[MLQCZ]|-?\d*\.?\d+',el.get('d'));i=0;points=[];start=None;cmd=None
  def emit(closed=False):
   if len(points)>1: result.append(dict(points=points.copy(),fill=None if st.get('fill')=='none' else st.get('fill','#000000'),stroke=None if st.get('stroke')=='none' else st.get('stroke'),stroke_width=float(st.get('stroke-width',1)),closed=closed,group=group))
  while i<len(tok):
   if tok[i] in 'MLQCZ':cmd=tok[i];i+=1
   if cmd=='Z':emit(True);points=[];cmd=None;continue
   n={'M':2,'L':2,'Q':4,'C':6}[cmd];v=list(map(float,tok[i:i+n]));i+=n
   if cmd=='M':
    if points:emit()
    points=[v];start=v;cmd='L'
   elif cmd=='L':points.append(v)
   else:
    a=points[-1]; b=v[:2]; c=v[2:4]; end=c if cmd=='Q' else v[4:6]
    for k in range(1,17):
     t=k/16;u=1-t
     q=[u*u*a[j]+2*u*t*b[j]+t*t*c[j] if cmd=='Q' else u**3*a[j]+3*u*u*t*b[j]+3*u*t*t*c[j]+t**3*end[j] for j in range(2)];points.append(q)
  emit()
 for ch in el:walk(ch,st,group)
walk(root)
p.with_name('C_face_polylines_ROUGH_DRAFT.json').write_text(json.dumps({'status':'DRAFT/HOLD identity not approved','viewBox':[0,0,512,283],'method':'Explicitly authored Bezier rough; 16 samples per curve, no raster embedding','polylines':result},indent=2))
print(len(result))
