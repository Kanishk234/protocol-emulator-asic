"""Read-only stage diagnosis; failed source never becomes route-qualified."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from native_setup_reserve_screen import capture_setup
from electrical_margin_summary import parse

SOURCE_RUN = 39468700509
SOURCE_SHA = '53b35a63873ebc4181f60dab1a6a09f9de6b7518'
CORNER = 'nom_slow_1p08V_125C'
STAGES = ('39-openroad-globalrouting', '41-openroad-repairdesignpostgrt', '43-openroad-repairantennas',
          '44-openroad-resizertimingpostgrt', '45-openroad-repairantennas-1')
HASHES = {'trw_pin_bs.v': 'c77f87ce20a8b2f7eec2b58b4db72476ccf4eb5fc89dde4d60b9461f486a346d',
          'trw_pin_cfg.v': 'd17c05bfe5ca002eb5ca09885727bee039766f815817c27a9b56da6041b7adc7',
          'trw_pin_tx.v': '29bdf26b9cf3d1939d8b8efe7833ac7d6ca1042c71e33c7065462f10e3c7951f',
          'signoff.sdc': '63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa'}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(run, config):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main', conclusion='failure',
                    path='.github/workflows/gds-native-tx-cursor-setup-reserve-screen.yaml')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong failed source provenance')
    if config.get('CLOCK_PERIOD') != 20 or config.get('PL_TARGET_DENSITY_PCT') != 56:
        raise ValueError('Wrong source timing or density')
    for name, expected_hash in HASHES.items():
        if digest(Path('src') / name) != expected_hash:
            raise ValueError('Wrong source bytes: '+name)


def stage_config(config):
    return dict(config, meta={'version': config.get('meta', {}).get('version', 1),
                             'flow': ['OpenROAD.STAMidPNR']},
                PNR_CORNERS=[CORNER], RSZ_CORNERS=[CORNER], OPENROAD_THREADS=4,
                PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                SIGNOFF_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                STA_EXTRA_CORNER_TCL_FILE=str(Path('workflow-src/scripts/ci/native_stage_probe.tcl').resolve()))


def main():
    root = Path('runs/native-stock-screen')
    config = json.loads(Path('src/config_native_stock.json').read_text())
    validate(json.loads(Path('/tmp/native-source-run.json').read_text()), config)
    output = Path('runs/native-stage-probe'); output.mkdir(exist_ok=False)
    receipt = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, diagnostic_only=True,
                   qualified=False, repair_performed=False, stages={})
    for stage in STAGES:
        state = root/'flow'/stage/'state_out.json'
        data = json.loads(state.read_text())
        odb = Path(data['odb'])
        if not odb.resolve().is_relative_to(state.parent.resolve()) or odb.name != 'tt_um_tripwire.odb':
            raise ValueError('Wrong stage database')
        before = digest(odb)
        cfg = stage_config(config)
        path = output/(stage+'.json'); path.write_text(json.dumps(cfg, indent=2)+'\n')
        out = output/stage; out.mkdir()
        subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
            '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
            '--run-tag', 'stage-probe', '--force-run-dir', str(out), '--hide-progress-bar',
            '--with-initial-state', str(state), str(path)], check=True)
        if digest(odb) != before or list(out.glob('*-openroad-*routing')):
            raise ValueError('Diagnostic mutated its source or ran routing')
        reports = list(out.glob('*-openroad-stamidpnr/electrical_margin.rpt'))
        captures = list(out.glob('*-openroad-stamidpnr/capture_setup.rpt'))
        if len(reports) != 1 or len(captures) != 1:
            raise ValueError('Missing unique stage evidence')
        corner, electrical = parse(reports[0].read_text())
        if corner != CORNER or set(electrical['nets']) != {'_09431_', '_21816_'}:
            raise ValueError('Wrong stage diagnostic coverage')
        receipt['stages'][stage] = dict(odb_sha256=before,
            capture_setup_ns=capture_setup(captures[0].read_text()), electrical=electrical)
        (output/'diagnosis.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(stage, json.dumps(receipt['stages'][stage]), flush=True)


if __name__ == '__main__':
    main()
