"""Ground unused R1 routing outputs using existing, explicitly padded GND slots.

No routed PIP, primitive setting, physical resource or production G1 image is
changed. The original FASM must reproduce the original image exactly first.
"""
import collections
import hashlib
import io
import json
from pathlib import Path
import pickle
import re

from compile.bitfile import BitFile
from compile.bitgen import fasm_features, words as encode_words


def ground_unused(original, spec, features, switches):
    if encode_words(features,spec)!=original:
        raise ValueError('Original FASM does not reproduce original image')
    used=collections.defaultdict(set);locked=collections.defaultdict(set)
    for feature in features:
        tile,source,dest=feature.split('.')
        used[tile].add(dest)
        locked[tile].update(spec['TileSpecs'][tile][source+'.'+dest])
    result=list(original);changes=[]
    arch=spec['ArchSpecs'];frames=arch['MaxFramesPerCol'];fbits=arch['FrameBitsPerRow']
    rows=1+max(int(tile.split('Y')[1]) for tile in spec['TileMap'])
    for tile,kind in spec['TileMap'].items():
        if kind=='NULL':continue
        groups=collections.defaultdict(list)
        for feature,bits in spec['TileSpecs'][tile].items():
            if bits:groups[feature.split('.')[1]].append(bits)
        for dest,entries in groups.items():
            if dest in used[tile]:continue
            indexes=set(entries[0]);width=len(indexes)
            if not 1<=width<=5 or any(set(entry)!=indexes for entry in entries):continue
            # All-ones is eligible only when not a selectable routed source.
            if any(all(value=='1' for value in entry.values()) for entry in entries):continue
            match=re.search(r'cus_mux\d+\s+inst_cus_mux\d+_'+re.escape(dest)+r'\s*\((.*?)\);',switches[kind],re.S)
            top=(1<<width)-1
            if match is None or not re.search(r'\.A'+str(top)+r'\(GND0\)',match[1]):continue
            if indexes & locked[tile]:raise ValueError('Unused selector overlaps an active feature')
            x,y=map(int,tile[1:].split('Y'))
            for index in indexes:
                if not isinstance(index,int) or not 0<=index<frames*fbits:
                    raise ValueError('Selector bit outside tile frames')
                frame,offset=divmod(index,fbits)
                word=1+(x*frames+frame)*(rows+1)+1+(rows-1-y)
                result[word]|=1<<offset
            changes.append(dict(tile=tile,output=dest,padding_slot=top,tile_bits=sorted(indexes)))
    return result,changes


class PlainSpec(pickle.Unpickler):
    def find_class(self,*args):
        raise ValueError('Executable object in bitstream specification')


def derive(model,case,original_image,out):
    model,case,out=map(Path,(model,case,out))
    manifest=json.loads((model/'resource-control.json').read_text())
    if manifest.get('radix')!='radix8_2':raise ValueError('Quiescence is an explicit R1 reduced-radix diagnostic')
    spec_path=model/'macro/fabulous/bitStreamSpec.bin'
    raw=spec_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['generated_sha256']['macro/fabulous/bitStreamSpec.bin']:
        raise ValueError('Changed frozen bitstream specification')
    spec=PlainSpec(io.BytesIO(raw)).load()
    types=set(spec['TileMap'].values())-{'NULL'}
    switches={};inputs=[spec_path,case/'design.fasm',original_image,Path(__file__)]
    for kind in sorted(types):
        path=model/'rtl'/(kind+'_switch_matrix.v');inputs.append(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['generated_sha256'][str(path.relative_to(model))]:
            raise ValueError('Changed generated switch matrix')
        switches[kind]=path.read_text()
    original=BitFile.load(original_image)
    if original.arch_version!=0xfe:raise ValueError('Production architecture is excluded')
    derived,changes=ground_unused(original.words,spec,fasm_features(case/'design.fasm'),switches)
    image=out/'quiesced.wbit';BitFile(original.arch_version,derived).save(image)
    record=dict(policy='unused-padded-GND-only',source_image_sha256=hashlib.sha256(Path(original_image).read_bytes()).hexdigest(),
                derived_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),grounded_outputs=len(changes),
                changed_bits=sum((a^b).bit_count() for a,b in zip(original.words,derived)),changes=changes,
                input_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
                scope='Existing padded GND selection on unrouted outputs only; no active feature or hardware change, no timing or physical acceptance.')
    (out/'quiescence.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return image,record,inputs
