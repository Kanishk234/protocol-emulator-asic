"""Bind functional replay to the authenticated pre-DRT native checkpoint."""
import hashlib
import json
from pathlib import Path
import zipfile

from closure_route import provenance, digest, SOURCE_RUN, CONFIG_SHA

ARTIFACT_ID = 13708390816
ARCHIVE_SHA = 'sha256:5bd617e3a926684728f8dd2a0e9dc1a54bbb6229449c2965b5eedfae6aa8a3fb'
NETLIST = 'runs/stock-official-baseline/44-openroad-resizertimingpostgrt/tt_um_tripwire.nl.v'
NETLIST_SHA = 'd235214bdfde0030f6791d476537ffddc147fd59bdf092d6081131cc7164f4e7'


def validate(run, artifact, archive, expected, output):
    provenance(run, artifact)
    if artifact.get('id') != ARTIFACT_ID or artifact.get('digest') != ARCHIVE_SHA:
        raise ValueError('Wrong authenticated native artifact')
    if 'sha256:' + digest(archive) != ARCHIVE_SHA:
        raise ValueError('Native archive bytes differ')
    if output.exists():
        raise ValueError('Refusing to replace a prior native netlist')
    with zipfile.ZipFile(archive) as bundle:
        # Do not extract arbitrary artifact paths into the test checkout.
        names = bundle.namelist()
        if names.count(NETLIST) != 1:
            raise ValueError('Missing unique native netlist')
        if hashlib.sha256(bundle.read('src/config.json')).hexdigest() != CONFIG_SHA:
            raise ValueError('Wrong native source project controls')
        for folder in ('src', 'macro'):
            local = {str(p.relative_to(expected)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (expected / folder).rglob('*') if p.is_file() and p.suffix != '.json'}
            native = {name: hashlib.sha256(bundle.read(name)).hexdigest() for name in names
                      if name.startswith(folder + '/') and not name.endswith(('/', '.json'))}
            if native != local:
                raise ValueError('Native hardware/macro files differ from expected preparation')
        if bundle.read('info.yaml') != (expected / 'info.yaml').read_bytes():
            raise ValueError('Wrong native metadata')
        data = bundle.read(NETLIST)
        if hashlib.sha256(data).hexdigest() != NETLIST_SHA:
            raise ValueError('Wrong final native netlist bytes')
    if b'module tt_um_tripwire' not in data or b'RM_IHPSG13_1P_512x16_c2_bm_bist' not in data:
        raise ValueError('Expected full-chip SRAM netlist')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    receipt = dict(source_run=SOURCE_RUN, artifact_id=ARTIFACT_ID,
                   archive_sha256=ARCHIVE_SHA, native_netlist=NETLIST,
                   netlist_sha256=NETLIST_SHA, functional_simulation_only=True,
                   detailed_routing_performed=False, sdf_annotated=False,
                   official_gds_qualified=False)
    output.with_suffix('.identity.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    import os
    root = Path.cwd()
    validate(json.loads(Path('native-source-run.json').read_text()),
             json.loads(Path('native-source-artifact.json').read_text()),
             Path('native-source.zip'), Path(os.environ['CLOSURE_EXPECTED_SOURCE']),
             root / 'build/closure-native-gl/netlist.v')
