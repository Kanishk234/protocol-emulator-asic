"""Audit a prepared full-chip checkout; never modify or qualify hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import yaml


def audit(root, reference):
    root, reference = Path(root).resolve(), Path(reference).resolve()
    info = yaml.safe_load((root / 'info.yaml').read_text())['project']
    assert info['tiles'] == '8x4' and info['clock_hz'] == 50_000_000
    assert info['top_module'] == 'tt_um_tripwire'
    sources = info['source_files']
    assert len(sources) == len(set(sources)), 'Duplicate synthesis sources'
    assert 'trw_chip.v' in sources, 'Placeholder-only design'
    make = (root / 'test/Makefile').read_text()
    match = re.search(r'^PROJECT_SOURCES\s*=\s*(.*)$', make, re.M)
    assert match and match[1].split() == sources, 'Simulation/synthesis source mismatch'
    for name in sources:
        assert Path(name).name == name and (root / 'src' / name).is_file(), name
    config = json.loads((root / 'src/config.json').read_text())
    assert config['CLOCK_PERIOD'] == 20
    if 'meta' in config:
        # D-182 configured Classic is a project input, not a generated step list.
        # Admit only the byte-identical config that passed screen/DRT/RCX/L3.
        expected = '0b7a388f659ae287b20580fbfa0572b36809df2fd04b63988c5499f3b66598bc'
        actual = hashlib.sha256((root / 'src/config.json').read_bytes()).hexdigest()
        assert actual == expected, 'Unreviewed project flow configuration'
        assert config['meta'] == {'version': 1, 'flow': 'Classic',
            'substituting_steps': {'+OpenROAD.ResizerTimingPostGRT': 'OpenROAD.RepairAntennas'}}
    macro_files = {}

    def local_paths(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from local_paths(item)
        elif isinstance(value, list):
            for item in value:
                yield from local_paths(item)
        elif isinstance(value, str) and value.startswith('dir::'):
            path = (root / 'src' / value[5:]).resolve()
            assert path.is_relative_to(root), 'Reference escapes checkout'
            assert path.is_file(), f'Missing project input: {value}'
            yield path
        elif isinstance(value, str) and value.startswith(('/', '~', '$')):
            raise AssertionError('Machine-specific macro path')

    assert config.get('MACROS'), 'Missing SRAM macro configuration'
    for path in local_paths(config['MACROS']):
        macro_files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for key in ('PDN_CFG',):
        assert config.get(key)
        list(local_paths(config[key]))
    for name in sources:
        assert not name.startswith('RM_IHPSG13_'), 'Synthesis blackbox duplicated in simulation list'
    assert 'sg13cmos5l_udp.v' in make and 'MACRO_MODELS' in make
    for directory in {p.parent for p in (root / 'macro').rglob('*.gds')}:
        assert (directory / 'LICENSE').is_file(), 'Missing macro redistribution license'
        assert (directory / 'PROVENANCE.json').is_file(), 'Missing macro provenance'
        provenance = json.loads((directory / 'PROVENANCE.json').read_text())
        for name, digest in provenance['files'].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    official = '.github/workflows/gds.yaml'
    assert (root / official).read_bytes() == (reference / official).read_bytes(), 'Official jobs changed'
    baseline = json.loads((reference / 'src/config.json').read_text())
    differences = {k: {'main': baseline.get(k), 'candidate': config.get(k)}
                   for k in sorted(set(baseline) | set(config))
                   if k != '//' and baseline.get(k) != config.get(k)}
    # AGENTS permits only these fields without a separate config-policy override.
    policy_review = sorted(set(differences) - {'CLOCK_PERIOD', 'PL_TARGET_DENSITY_PCT', 'MACROS'})
    return dict(input_checks_passed=True, adoption_ready=False, official_signoff=False,
                synthesis_sources=sources, macro_files=macro_files,
                config_differences=differences, config_policy_review_required=policy_review,
                remaining=['Resource/spec adoption decision', 'Config-policy review',
                           'Exact-source final verification', 'Extracted physical closure',
                           'Unchanged official GDS/precheck/GL'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.reference)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Input checks pass; adoption/signoff NOT qualified.')
    print('Config fields requiring policy review:', ', '.join(result['config_policy_review_required']))
