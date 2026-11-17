"""Require integration inputs to match the routed, extracted and replayed candidate."""
import hashlib
import json
from pathlib import Path

import yaml

MANIFEST='spikes/phase2_stock_flow/cache_final_antenna/integration_manifest.json'


def verify(root):
    root=Path(root).resolve()
    manifest=json.loads((root/MANIFEST).read_text())
    for name,expected in manifest['physical_inputs'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing/unsafe physical input: '+name)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Changed qualified physical input: '+name)
    for name,key in [('tools/tripwire_spec.py','python_tables_sha256'),('.github/workflows/gds.yaml','official_workflow_sha256')]:
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=manifest[key]:raise ValueError('Changed replay/official input: '+name)
    spec=yaml.safe_load((root/'spec/tripwire.yaml').read_text())
    if spec['fabric']['lanes']!=2 or spec['fabric']['units']!=4 or spec['pin_config']['units']!=[['pulse','carrier','bitsync'],[],[],[]]:
        raise ValueError('Integrated resource shape differs from qualified replay')
    return dict(physical_inputs_match=True,replay_encodings_match=True,official_workflow_unchanged=True,
                screen_run=manifest['screen_run'],route_extraction_run=manifest['route_extraction_run'],
                full_protocol_run=manifest['full_protocol_run'],official_gds_signoff=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',nargs='?',default='.')
    print(json.dumps(verify(p.parse_args().root),indent=2))
