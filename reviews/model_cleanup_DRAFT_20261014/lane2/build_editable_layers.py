from pathlib import Path
import base64,json
p=Path(__file__).parent
png=p/'expression_cleanup_sheet_DRAFT.png'
regions={
'face_neutral':(12,95,490,380),'face_soft_smile':(521,95,490,380),'face_notice':(1033,95,490,380),
'eyelids_open_INCOMPLETE':(25,554,345,83),'eyelids_half_INCOMPLETE':(425,554,345,83),'eyelids_closed':(817,554,350,83),
'iris_left':(1250,564,85,80),'iris_right':(1400,564,85,80),
'brows_neutral':(25,762,230,55),'brows_soft':(282,762,230,55),'brows_notice':(537,762,230,55),
'mouth_neutral':(825,773,155,50),'mouth_smile':(1057,773,176,50),'mouth_notice':(1330,773,145,50),
'cheek_faint':(308,943,175,47),'cheek_strong':(563,943,178,47)}
data=base64.b64encode(png.read_bytes()).decode()
# Clipped raster source regions, not raster retouching, vector tracing, or warp.
svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1536" height="1024" viewBox="0 0 1536 1024">','<title>Editable clipping layers — DRAFT HOLD; raster subregions, not vector paths</title>',f'<defs><image id="source" width="1536" height="1024" href="data:image/png;base64,{data}"/>']
for name,(x,y,w,h) in regions.items():svg.append(f'<clipPath id="clip_{name}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
svg.append('</defs>')
for name in regions:svg.append(f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}"><use href="#source" clip-path="url(#clip_{name})"/></g>')
svg.append('</svg>')
(p/'expression_parts_layered_DRAFT.svg').write_text('\n'.join(svg))
(p/'regions_DRAFT.json').write_text(json.dumps({'source':png.name,'dimensions':[1536,1024],'status':'DRAFT/HOLD','type':'manually located clipped raster regions, no warp','regions':regions},indent=2))
print('Created editable named clipping layers and region manifest.')
