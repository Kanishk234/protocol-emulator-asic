#!/usr/bin/env python3
"""Prepare and audit the D-192 pre-routing trial without changing main inputs.

The flow is the qualified Classic sequence, stopped before detailed routing.
STA-only diagnostic configs may select corners/constraints and add reports;
no diagnostic process repairs or rewrites the saved physical design.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml

from functional_setup_frontier import parse_report

ROOT = Path(__file__).resolve().parents[2]
TOOLS = '0922544e6c7f6126047c3fba720b0437fa32a1b8'
PDK = '89d42ee6d2fd9b50b86a1aada6fee6673c3e6008'
IMAGE = 'ghcr.io/librelane/librelane:3.1.0.dev4'
IMAGE_DIGEST = 'sha256:af2405f5d48d8fe14d406ecce913811177a95e365e3b625859677307cace2469'
OPENROAD = 'dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
CORNERS = ('nom_fast_1p32V_m40C', 'nom_slow_1p08V_125C', 'nom_typ_1p20V_25C')
DEFAULT_DESIGN = ROOT / 'build/status_merge_screen/design'
SYNTH_VARIANTS = ('root-mode-synth', 'root-mode-b-edge-synth')
VARIANTS = ('status-merge', 'root-mode', 'root-mode-fanout7', 'root-mode-b-edge', *SYNTH_VARIANTS)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def one(root, pattern):
    found = list(Path(root).glob(pattern))
    if len(found) != 1:
        raise ValueError(f'Expected one {pattern}, found {len(found)}')
    return found[0]


def inventory(root):
    return {str(p.relative_to(root)): sha(p) for folder in ('src', 'macro')
            for p in sorted((root / folder).rglob('*')) if p.is_file()} | {'info.yaml': sha(root / 'info.yaml')}


def check_inputs(design):
    receipt = load(design / 'trial_inputs.json')
    if sha(ROOT / 'scripts/ci/functional_setup_frontier.py') != receipt['report_parser_sha256']:
        raise ValueError('Functional report parser changed after input binding')
    if sha(Path(__file__)) != receipt['screen_runner_sha256']:
        raise ValueError('Screen runner changed after input binding')
    for name, expected in receipt['candidate_inputs'].items():
        if sha(design / name) != expected:
            raise ValueError('Changed candidate input: ' + name)
    for name, expected in receipt['audit_helpers'].items():
        if sha(design / name) != expected:
            raise ValueError('Changed read-only audit helper: ' + name)
    return receipt


def prepare(design, *, variant="status-merge"):
    if variant not in VARIANTS:
        raise ValueError("Unknown screen variant")
    if design == ROOT or any(design.is_relative_to(ROOT / folder) for folder in ('src', 'macro', '.git')):
        raise ValueError('Trial must be outside qualified source/macro/Git directories')
    from repo_audit import audit
    audit(ROOT)  # Keep the qualified baseline check intact, before staging.
    patch = ROOT / 'spikes/phase3_status_merge/status_merge.patch'
    evidence = load(ROOT / 'docs/reports/phase3_status_merge_candidate_result.json')
    if sha(patch) != evidence['patch_sha256']:
        raise ValueError('Patch differs from verified candidate')
    chip = evidence['whole_chip_regressions']['verilator']
    if (chip['tests'], chip['failures'], chip['skips']) != (55, 0, 0):
        raise ValueError('Missing completed chip regression')
    for name, expected in evidence['source_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('Changed verified source: ' + name)
    for name, expected in evidence['formal_evidence_sha256'].items():
        if sha(ROOT / 'docs/reports' / name) != expected:
            raise ValueError('Changed formal receipt: ' + name)
    integration = load(ROOT / 'docs/reports/phase3_status_integration_formal_result.json')
    queue = load(ROOT / 'docs/reports/phase3_status_queue_formal_result.json')
    if not integration['all_pass'] or any(r['status'] != 'PASS' for r in queue['proofs'].values()):
        raise ValueError('Candidate formal evidence does not pass')
    if design.exists():
        raise ValueError('Trial directory already exists; choose a fresh directory')
    design.mkdir(parents=True)
    before = inventory(ROOT)
    for folder in ('src', 'macro'):
        shutil.copytree(ROOT / folder, design / folder)
    shutil.copyfile(ROOT / 'info.yaml', design / 'info.yaml')
    subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(patch)], cwd=design, check=True)
    expected = {**before, 'src/trw_pin_bs.v': evidence['candidate_sha256']}
    root_mode_patch_sha256 = None
    if variant != 'status-merge':
        root_mode_patch = patch.parent / 'root_mode/root_mode.patch'
        root_mode_patch_sha256 = sha(root_mode_patch)
        if root_mode_patch_sha256 != 'e7b6691ce4416e28ff26a7f941d72c8961223d40248420bb44123bd02edfc486':
            raise ValueError('Root-mode patch differs from the tested candidate')
        subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(root_mode_patch)],
                       cwd=design, check=True)
        expected['src/trw_pin_cfg.v'] = '02a63f1d46ad7360a0f9a8a56b004478b629540ce4eb25234235b7b4b9c43581'
    if variant in ('root-mode-b-edge', 'root-mode-b-edge-synth'):
        edge_patch = patch.parent / 'b_edge/share.patch'
        if sha(edge_patch) != '02cb9e6031cf1413ef48b91c254f7c1ffe903054c0290478bfa41cb8c3f6b5d5':
            raise ValueError('B-edge patch differs from the tested candidate')
        subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(edge_patch)],
                       cwd=design, check=True)
        expected['src/trw_pin_rx.v'] = '735334e1eb659bacc1eef6a63af4cb26dc78ab26841000a11d46cd144b0b761d'
        expected['src/trw_pin_unit.v'] = '6e3b4cdf98d5d89fc99c92800e23828b6ba6823eed876ce647b59783c30f3073'
    if variant == 'root-mode-fanout7':
        baseline_config = load(ROOT / 'src/config.json')
        if 'MAX_FANOUT_CONSTRAINT' in baseline_config:
            raise ValueError('Expected inherited baseline fanout constraint')
        trial_config = design / 'src/config.json'
        save(trial_config, {**baseline_config, 'MAX_FANOUT_CONSTRAINT': 7})
        expected['src/config.json'] = sha(trial_config)
    after = inventory(design)
    if after != expected:
        raise ValueError('Trial inputs differ from the selected candidate')
    if inventory(ROOT) != before:
        raise ValueError('Staging changed qualified inputs')
    (design / 'audit_helpers').mkdir()
    helpers = {}
    for name in ('status_merge_screen_audit.tcl', 'functional_setup_frontier.tcl'):
        target = design / 'audit_helpers' / name
        shutil.copyfile(ROOT / 'scripts/ci' / name, target)
        helpers[str(target.relative_to(design))] = sha(target)
    save(design / 'trial_inputs.json', dict(audit_helpers=helpers,
        baseline_inputs=before, candidate_inputs=after, patch_sha256=sha(patch),
        variant=variant, root_mode_patch_sha256=root_mode_patch_sha256,
        screen_runner_sha256=sha(Path(__file__)), report_parser_sha256=sha(ROOT/'scripts/ci/functional_setup_frontier.py'),
        workflow_sha256=sha(ROOT/'.github/workflows/status-merge-screen.yaml'),
        evidence_sha256=sha(ROOT / 'docs/reports/phase3_status_merge_candidate_result.json'),
        source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        official_workflows_changed=False, physical_qualified=False, official_gds_passed=False))


def generated(design):
    check_inputs(design)
    if subprocess.check_output(['git', '-C', str(design / 'tt'), 'rev-parse', 'HEAD'], text=True).strip() != TOOLS:
        raise ValueError('Wrong support-tools snapshot')
    if importlib.metadata.version('librelane') != '3.1.0.dev4':
        raise ValueError('Wrong LibreLane version')
    from librelane.common import get_ciel_pdk_hash
    from librelane.flows.classic import Classic
    from librelane.config import Meta
    if get_ciel_pdk_hash('ihp-sg13cmos5l') != PDK:
        raise ValueError('Wrong PDK revision')
    project = load(design / 'src/config.json')
    config = load(design / 'src/config_merged.json')
    if any(config.get(k) != v for k, v in project.items()):
        raise ValueError('Generated config differs from qualified project settings')
    if config['DIE_AREA'] != '0 0 1724.16 710.64' or config['CLOCK_PERIOD'] != 20 or config['RT_MAX_LAYER'] != 'Metal4':
        raise ValueError('Wrong tile, clock or routing limit')
    meta = Meta.from_dict(project['meta'])
    original = [s.id for s in Classic.Steps]
    actual = [s.id for s in Classic.Substitute(meta.substituting_steps).Steps]
    i = original.index('OpenROAD.ResizerTimingPostGRT')
    if actual != original[:i+1] + ['OpenROAD.RepairAntennas-1'] + original[i+1:]:
        raise ValueError('Qualified native step order changed')
    info = yaml.safe_load((design / 'info.yaml').read_text())['project']
    if config['VERILOG_FILES'] != ['dir::' + name for name in info['source_files']]:
        raise ValueError('Generated source list differs from reviewed design')
    if config['FP_DEF_TEMPLATE'] != 'dir::../tt/tech/ihp-sg13cmos5l/def/tt_block_8x4_pgvdd.def':
        raise ValueError('Wrong stock tile template')
    # No custom command/runtime substitution may change the pinned engine.
    for key in ('LIBRELANE_IMAGE_OVERRIDE', 'TRIPWIRE_NATIVE_RUNTIME', '_LLN_OVERRIDE_OPENROAD'):
        if os.environ.get(key):
            raise ValueError('Unexpected runtime override: ' + key)
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', IMAGE], text=True))
    if len(image) != 1 or f'ghcr.io/librelane/librelane@{IMAGE_DIGEST}' not in image[0]['RepoDigests']:
        raise ValueError('Wrong container digest')
    version = subprocess.check_output(['docker', 'run', '--rm', IMAGE, 'openroad', '-version'], text=True).strip()
    if version != OPENROAD:
        raise ValueError('Wrong OpenROAD build')
    save(design / 'engine.json', dict(tools=TOOLS, pdk=PDK, librelane='3.1.0.dev4',
                                     image_digest=IMAGE_DIGEST, openroad=version,
                                     merged_config_sha256=sha(design / 'src/config_merged.json')))


def invoke(design, config, output, pdk, *, source=None, stop=None, manual=True):
    output.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, '-m', 'librelane', '--docker-no-tty', '--dockerized',
               '--pdk-root', str(pdk), '--pdk', 'ihp-sg13cmos5l', '--run-tag', output.name,
               '--force-run-dir', str(output), '--hide-progress-bar']
    if manual:
        command += ['--manual-pdk']
    if source is not None:
        command += ['--with-initial-state', str(source)]
    if stop is not None:
        command += ['--to', stop]
    subprocess.run(command + [str(config)], cwd=design, check=True)


def flow(design):
    receipt = check_inputs(design)
    engine = load(design / 'engine.json')
    if sha(design / 'src/config_merged.json') != engine['merged_config_sha256']:
        raise ValueError('Merged config changed after binding')
    physical = design / 'runs/physical'
    synthesis_only = receipt['variant'] in SYNTH_VARIANTS
    stop = 'Yosys.Synthesis' if synthesis_only else 'OpenROAD.STAMidPNR-3'
    invoke(design, design / 'src/config_merged.json', physical,
           Path(os.environ['PDK_ROOT']), stop=stop, manual=False)
    if synthesis_only:
        netlist = one(physical, '*-yosys-synthesis/tt_um_tripwire.nl.v.json')
        save(physical / 'synthesis_result.json', dict(
            variant=receipt['variant'], netlist_sha256=sha(netlist),
            trial_inputs_sha256=sha(design / 'trial_inputs.json'),
            engine_sha256=sha(design / 'engine.json'),
            **b_input_loads(load(netlist)), physical_qualified=False))
        check_inputs(design)
        return
    if list((design / 'runs/physical').glob('*-openroad-detailedrouting')):
        raise ValueError('Screen unexpectedly performed detailed routing')
    one(design / 'runs/physical', '*-openroad-stamidpnr-3/state_out.json')
    check_inputs(design)


def b_input_loads(netlist):
    module = netlist['modules']['tt_um_tripwire']
    units = {}
    for unit in range(4):
        name = f'u_chip.g_unit[{unit}].u_unit.b_in'
        bit, = module['netnames'][name]['bits']
        loads = []
        drivers = []
        for instance, cell in module['cells'].items():
            for pin, bits in cell['connections'].items():
                if bit in bits:
                    endpoint = dict(instance=instance, cell=cell['type'], pin=pin)
                    direction = cell['port_directions'][pin]
                    if direction == 'input':
                        loads.append(endpoint)
                    elif direction == 'output':
                        drivers.append(endpoint)
                    else:
                        raise ValueError(f'Unexpected pin direction on {name}: {direction}')
        if len(drivers) != 1 or not loads:
            raise ValueError(f'Expected one driver and at least one load on {name}')
        units[str(unit)] = dict(driver=drivers[0], loads=loads)
    return dict(mapped_cells=len(module['cells']), b_inputs=units)


def numeric(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Missing/nonfinite metric: ' + label)
    return value


def implementation_cost(step):
    metrics = load(step / 'or_metrics_out.json')
    keys = {
        'stdcell_count': 'count__stdcell',
        'stdcell_area_um2': 'area__stdcell',
        'buffer_count': 'count__class:buffer',
        'clock_buffer_count': 'count__class:clock_buffer',
        'timing_repair_buffer_count': 'count__class:timing_repair_buffer',
        'antenna_cell_count': 'count__class:antenna_cell',
    }
    # OpenROAD may omit a cell class when no instances are present.
    return {label: metrics.get('design__instance__' + suffix)
            for label, suffix in keys.items()}


def qualify_corner(metrics, functional, corner):
    failures = []
    for kind in ('setup', 'hold'):
        key = f'timing__{kind}__ws__corner:{corner}'
        minimum = 0.05 if kind == 'hold' and corner == CORNERS[0] else 0
        if numeric(metrics.get(key), key) < minimum:
            failures.append(key)
        key = f'timing__{kind}_vio__count__corner:{corner}'
        value = metrics.get(key)
        if type(value) is not int or value < 0:
            raise ValueError('Missing/invalid violation count: ' + key)
        if value:
            failures.append(key)
    for kind in ('slew', 'cap', 'fanout'):
        key = f'design__max_{kind}_violation__count__corner:{corner}'
        value = metrics.get(key)
        if type(value) is not int or value < 0:
            raise ValueError('Missing/invalid electrical count: ' + key)
        if value:
            failures.append(key)
    if numeric(functional['worst_reported_setup_slack_ns'], 'functional setup') <= 0:
        failures.append(corner + ' functional setup is not positive')
    return failures


def read_sta(step, corner):
    raw = load(step / 'or_metrics_out.json')
    for name in ('max.rpt', 'min.rpt'):
        values = re.findall(r'([-+]?[0-9]+\.[0-9]+)\s+[-+0-9.]+\s+clock uncertainty', (step / name).read_text())
        if not values or any(abs(abs(float(v)) - 0.25) > 1e-9 for v in values):
            raise ValueError('Report does not confirm unchanged uncertainty')
    functional = parse_report((step / 'functional_setup_frontier.rpt').read_text(), corner)
    return raw, functional


def stock_signoff(output, resolved):
    # Official config has no custom SDC: LibreLane uses its pinned base.sdc.
    # An explicit source wrapper measures the same signoff constraint policy,
    # without relying on a non-existent generated src/signoff.sdc.
    if resolved.get('PNR_SDC_FILE') is not None or resolved.get('SIGNOFF_SDC_FILE') is not None:
        raise ValueError('Unexpected explicit constraint file in qualified flow')
    fallback = str(resolved.get('FALLBACK_SDC', ''))
    if not fallback.endswith('/base.sdc'):
        raise ValueError('Unexpected stock fallback constraints')
    path = output / 'stock-signoff.sdc'
    path.write_text('source $::env(SCRIPTS_DIR)/base.sdc\n')
    return path


def diagnostic_config(design, label, config):
    # Preserve dir:: resolution against src/, exactly as the merged config.
    path = design / 'src' / ('config_status_screen_' + label + '.json')
    save(path, config)
    return path


def audit(design):
    receipt = check_inputs(design)
    physical = design / 'runs/physical'
    if list(physical.glob('*-openroad-detailedrouting')):
        raise ValueError('Not a pre-routing screen')
    source = one(physical, '*-openroad-stamidpnr-3/state_out.json')
    state = load(source)
    paths = [source] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    before = {str(p): sha(p) for p in paths}
    timing = one(physical, '*-openroad-resizertimingpostgrt/state_out.json')
    antenna = one(physical, '*-openroad-repairantennas-1/state_out.json')
    if load(antenna.parent / 'state_in.json')['odb'] != load(timing)['odb'] or state['odb'] != load(antenna)['odb']:
        raise ValueError('Wrong final native repair/checkpoint chain')
    resolved = load(physical / 'resolved.json')
    if receipt['variant'] == 'root-mode-fanout7' and resolved.get('MAX_FANOUT_CONSTRAINT') != 7:
        raise ValueError('Native flow did not resolve the requested fanout constraint')
    pdk = Path(resolved['PDK_ROOT'])
    if pdk.name != PDK or resolved['GRT_ALLOW_CONGESTION'] is not False:
        raise ValueError('Wrong resolved PDK/congestion policy')
    repair_log = one(antenna.parent, '*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
    commands = re.findall(r'^\+ repair_antennas\b[^\n]*', repair_log, re.M)
    if len(commands) != 1 or '-allow_congestion' in commands[0] or '-diode_only' not in commands[0]:
        raise ValueError('Wrong final native antenna repair command')
    timing_log = (timing.parent / 'openroad-resizertimingpostgrt.log').read_text()
    totals = re.findall(r'(?m)^Total\s+\d+\s+\d+\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$', timing_log)
    if not totals:
        raise ValueError('Missing preceding full-route overflow measurement')
    output = design / 'runs/audit'
    output.mkdir(parents=True, exist_ok=False)
    base = load(design / 'src/config_merged.json')
    signoff = stock_signoff(output, resolved)
    reports = {}
    failures = []
    exports = []
    for constraint in ('pnr', 'signoff'):
        reports[constraint] = {}
        for corner in CORNERS:
            repeated = []
            evidence = []
            for iteration in range(2):
                config = {**base, 'meta': {'version': 1, 'flow': ['OpenROAD.STAMidPNR']},
                          'PNR_CORNERS': [corner], 'STA_EXTRA_CORNER_TCL_FILE': str(design / 'audit_helpers/status_merge_screen_audit.tcl')}
                if constraint == 'signoff':
                    config['PNR_SDC_FILE'] = str(signoff)
                name = f'{constraint}-{corner}-{iteration}'
                path = diagnostic_config(design, name, config)
                run = output / name
                invoke(design, path, run, pdk, source=source)
                step = one(run, '*-openroad-stamidpnr')
                raw, functional = read_sta(step, corner)
                repeated.append((raw, functional))
                evidence.append({name: sha(step / name) for name in ('or_metrics_out.json', 'functional_setup_frontier.rpt', 'max.rpt', 'min.rpt')})
                exports.append((sha(step / 'screen_native.nl.v'), sha(step / 'screen_native.pnl.v')))
            # Compare only all required gate values; runtime metrics may differ.
            raw, functional = repeated[0]
            checked = [k for k in raw if k.startswith(('timing__', 'design__max_')) and k.endswith('corner:' + corner)]
            if ({k: raw[k] for k in checked}, functional) != ({k: repeated[1][0].get(k) for k in checked}, repeated[1][1]):
                raise ValueError('Repeated STA gate/report values differ')
            failures += qualify_corner(raw, functional, corner)
            reports[constraint][corner] = dict(metrics={k: raw[k] for k in checked}, functional=functional, repeated_evidence_sha256=evidence)
    ant_config = {**base, 'meta': {'version': 1, 'flow': ['OpenROAD.CheckAntennas']}}
    ant_path = diagnostic_config(design, 'antenna', ant_config)
    invoke(design, ant_path, output / 'fresh-antenna', pdk, source=source)
    ant = load(one(output / 'fresh-antenna', '*-openroad-checkantennas/or_metrics_out.json'))
    for key in ('antenna__violating__nets', 'antenna__violating__pins'):
        if type(ant.get(key)) is not int or ant[key] < 0:
            raise ValueError('Missing/invalid fresh antenna metric')
        if ant[key]:
            failures.append(key)
    if len(set(exports)) != 1 or before != {str(p): sha(p) for p in paths}:
        raise ValueError('Read-only audits changed physical views/netlist exports')
    if int(totals[-1]):
        failures.append('Preceding full-route overflow')
    check_inputs(design)
    result = dict(trial_inputs_sha256=sha(design / 'trial_inputs.json'), engine_sha256=sha(design / 'engine.json'), signoff_wrapper_sha256=sha(signoff), native_fallback_sdc=resolved['FALLBACK_SDC'], screen_passed=not failures, failures=failures, reports=reports,
                  implementation_cost={
                      'before_final_antenna_repair': implementation_cost(timing.parent),
                      'after_final_antenna_repair': implementation_cost(one(antenna.parent, '*-openroad-diodeinsertion')),
                  },
                  antenna={k: ant[k] for k in ('antenna__violating__nets', 'antenna__violating__pins')},
                  preceding_full_route_overflow=int(totals[-1]),
                  overflow_scope='Zero prior full-route overflow plus congestion-prohibited final native incremental antenna repair',
                  unchanged_physical_view_sha256=before, exported_netlist_sha256=exports[0],
                  detailed_routing_performed=False, physical_qualified=False, official_gds_passed=False)
    save(output / 'screen_result.json', result)
    if failures:
        raise ValueError('Screen gates fail: ' + ', '.join(failures))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'generated', 'flow', 'audit'])
    parser.add_argument('--design', type=Path, default=DEFAULT_DESIGN)
    parser.add_argument('--variant', choices=VARIANTS, default='status-merge')
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare(args.design.resolve(), variant=args.variant)
    else:
        globals()[args.stage](args.design.resolve())
