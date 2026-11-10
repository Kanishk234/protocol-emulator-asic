"""Bind a stock-toolchain compatibility probe; never qualify timing here."""
import argparse
import hashlib
import json
from pathlib import Path

import yaml

TOOLS = '9d13ff3e3e6202090740110438c6a10c1d62ca0f'
PDK = '89d42ee6d2fd9b50b86a1aada6fee6673c3e6008'
CONFIGS = {'35bacb325c12276dd63f7e33b99f94b5e0d4940f7b3a22a6bd1e63424bc4c97a',
           '4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7',
           '10f86189e185f681f3ad2485fbcbefd72cc284972fef0d21aa2e971b6111627d',
           '7ad565b1cf34dbb50a950a693eaabe093751e566b0f168f794dffd7423088355'}
SIZES = {'6x4': '0 0 1289.28 710.64', '8x4': '0 0 1724.16 710.64'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)): digest(p)
            for folder in ('src', 'macro')
            for p in sorted((root / folder).rglob('*')) if p.is_file()
            and p.suffix not in ('.json',)}


def prepare(root, tiles):
    assert tiles in SIZES, 'Unknown tile selection'
    config_sha = digest(root / 'src/config.json')
    assert config_sha in CONFIGS, 'Wrong reviewed clock75 timing control'
    info = yaml.safe_load((root / 'info.yaml').read_text())
    assert info['project']['tiles'] == '6x4', 'Wrong source geometry'
    assert info['project']['clock_hz'] == 50000000
    assert info['project']['top_module'] == 'tt_um_tripwire'
    assert len(info['project']['source_files']) > 1, 'Placeholder source list'
    receipt = {'tiles': tiles, 'source_files': info['project']['source_files'],
               'inputs': inventory(root), 'project_config_sha256': config_sha,
               'tools_sha': TOOLS, 'pdk_revision': PDK,
               'timing_qualified': False, 'official_gds_passed': False}
    info['project']['tiles'] = tiles
    (root / 'info.yaml').write_text(yaml.safe_dump(info, sort_keys=False))
    (root / 'compatibility-input.json').write_text(json.dumps(receipt, indent=2) + '\n')


def generated(root, tiles):
    receipt = json.loads((root / 'compatibility-input.json').read_text())
    assert inventory(root) == receipt['inputs'], 'Source/macro changed during generation'
    assert digest(root / 'src/config.json') == receipt['project_config_sha256']
    cfg = json.loads((root / 'src/config_merged.json').read_text())
    project = json.loads((root / 'src/config.json').read_text())
    for key, value in project.items():
        assert cfg.get(key) == value, 'Generated config changed project control: ' + key
    assert cfg['DIE_AREA'] == SIZES[tiles]
    assert cfg['RT_MAX_LAYER'] == 'Metal4'
    assert cfg['CLOCK_PERIOD'] == 20
    assert cfg['FP_DEF_TEMPLATE'] == f'dir::../tt/tech/ihp-sg13cmos5l/def/tt_block_{tiles}_pgvdd.def'
    assert cfg['VERILOG_FILES'] == ['dir::' + f for f in receipt['source_files']]
    template = root / 'tt/tech/ihp-sg13cmos5l/def' / f'tt_block_{tiles}_pgvdd.def'
    width, height = [round(float(x) * 1000) for x in SIZES[tiles].split()[2:]]
    assert f'DIEAREA ( 0 0 ) ( {width} {height} ) ;' in template.read_text()
    receipt.update(generated_config=cfg, def_sha256=digest(template),
                   generation_passed=True)
    (root / 'compatibility-generated.json').write_text(json.dumps(receipt, indent=2) + '\n')


def native(root, tiles):
    receipt = json.loads((root / 'compatibility-generated.json').read_text())
    run = root / 'runs/official-nov9-preflight'
    assert inventory(root) == receipt['inputs'], 'Native flow changed source inputs'
    resolved = json.loads((run / 'resolved.json').read_text())
    assert resolved['CLOCK_PERIOD'] == 20
    assert resolved['RT_MAX_LAYER'] == 'Metal4'
    corners = resolved['STA_CORNERS']
    assert set(corners) == {'nom_fast_1p32V_m40C', 'nom_typ_1p20V_25C', 'nom_slow_1p08V_125C'}
    assert resolved['MACROS'], 'Missing SRAM views'
    states = list(run.glob('*-openroad-generatepdn/state_out.json'))
    assert len(states) == 1, 'Native PDN step did not finish'
    assert not list(run.glob('*-openroad-globalplacement')), 'Probe exceeded PDN boundary'
    receipt.update(native_through_pdn_passed=True, sta_corners=corners,
                   resolved_pdk_root=resolved['PDK_ROOT'],
                   native_final_state_sha256=digest(states[0]))
    (root / 'compatibility-native.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'generated', 'native'])
    parser.add_argument('tiles', choices=list(SIZES))
    args = parser.parse_args()
    globals()[args.stage](Path('.'), args.tiles)
