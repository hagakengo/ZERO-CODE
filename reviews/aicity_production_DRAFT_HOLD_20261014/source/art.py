"""Non-generative, conservative B colour grade; original composition remains fixed."""
from PIL import Image, ImageFilter
from pathlib import Path
import hashlib, json, argparse

def grade(src, dst):
    original = Image.open(src).convert('RGB')
    # Only 12% of a 0.55 px blur: soften hard digital micro-edges without repainting.
    soft = Image.blend(original, original.filter(ImageFilter.GaussianBlur(.55)), .12)
    # Slightly lift deepest shadow detail while maintaining the original blue-black palette.
    # No posterization, outlining, relighting, recolouring window lights, or new objects.
    lut = [round(v + 1.8*(1-v/255)**3) for v in range(256)]
    result = soft.point(lut * 3)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    result.save(dst)
    return {'status':'DRAFT/HOLD', 'source':str(src), 'source_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),
            'output':str(dst), 'output_sha256':hashlib.sha256(Path(dst).read_bytes()).hexdigest(),
            'size':list(result.size), 'method':'12% blend of radius 0.55 px gaussian; <=1.8/255 shadow lift',
            'geometry_change':False, 'generation_or_external_upload':False,
            'artistic_limit':'Conservative technical grade only; cannot certify Japanese anime style transformation.'}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('source'); parser.add_argument('output'); parser.add_argument('--qa')
    a=parser.parse_args(); record=grade(a.source,a.output)
    if a.qa: Path(a.qa).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False))
