"""Verify regenerated historical controls against authenticated passing hashes.

No hash substitution or new control is accepted when reconstruction differs.
"""
import argparse
import json
from pathlib import Path
from assembly_catalog import sha


def verify_model(model,expected):
    model=Path(model).resolve()
    if sha(model/'resource-control.json')!=expected['model_sha256']:
        raise ValueError('Recovered model manifest differs from original passing control')
    data=json.loads((model/'resource-control.json').read_text())
    if not data['passed'] or data['global_tracks']!=expected['tracks'] or data['radix']!=expected['radix']:
        raise ValueError('Recovered model identity differs')
    for relative,digest in data['generated_sha256'].items():
        path=(model/relative).resolve()
        if not path.is_relative_to(model) or sha(path)!=digest:
            raise ValueError('Recovered generated model file differs: '+relative)
    return len(data['generated_sha256'])


def verify_primary(model,case,expected):
    from compile.bitfile import BitFile
    from compile.bitgen import gen_words
    count=verify_model(model,expected);model,case=Path(model),Path(case)
    image=case/'concurrency.wbit'
    if sha(image)!=expected['image_sha256']:
        raise ValueError('Recovered primary image differs from original passing control')
    bits=BitFile.load(image)
    if bits.arch_version!=0xfe or gen_words(case/'design.fasm',model/'macro/fabulous/bitStreamSpec.bin')!=bits.words:
        raise ValueError('Recovered FASM/image encoding differs')
    return dict(passed=True,generated_files_checked=count,model_sha256=expected['model_sha256'],
                image_sha256=expected['image_sha256'],original_control_bytes_reproduced=True,
                physical_acceptance=False,timing_acceptance=False,
                scope='Historical model/image byte identity only; current RTL simulation is a separate required gate.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True);p.add_argument('--case',type=Path)
    p.add_argument('--tracks',choices=('4','8'),required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();expected=json.loads(Path(__file__).with_name('rtl_control_recovery_sources.json').read_text())['profiles'][a.tracks]
    result=verify_primary(a.model,a.case,expected) if a.case else dict(generated_files_checked=verify_model(a.model,expected))
    a.out.write_text(json.dumps(result,indent=2)+'\n')
