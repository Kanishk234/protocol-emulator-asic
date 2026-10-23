"""Fresh RTL -> reviewed repairs -> gated routing -> GDS/LVS -> TT package.

One live workspace, no physical artifact downloads. This is an integration
experiment, not the main official GDS workflow. Merged-GDS DRC is tested by the
unchanged TT precheck job; the separate raw Magic diagnostic remains failed.
"""
import copy
import json
import os
from pathlib import Path
import shutil

from native_stock_route import run_step
from sram_bank_clean_route import unique
from wire600_clean_route import main as route
from wire600_mux_margin import main as clean
from wire600_mux_margin_route import profile as route_profile
from wire600_mux_precheck import FIXTURES, classify_overlaps
from wire600_selective_plan import digest

WORKFLOW = '.github/workflows/gds-wire600-integrated-proof.yaml'
FINAL_NETLIST_SHA = 'c60823d33a9aa63b20ff4e07a934a4f1daa8b519c4ef2581c9d0b53599f13225'
OUTPUT = Path('runs/wire600-integrated-proof')
TAIL = ['Magic.StreamOut', 'KLayout.StreamOut', 'Magic.WriteLEF',
        'Magic.SpiceExtraction', 'Netgen.LVS', 'Checker.LVS']


def live_profile(run, run_id, head):
    expected = dict(id=int(run_id), head_sha=head, head_branch='main',
                    path=WORKFLOW, conclusion=None, status='in_progress')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong live integration run provenance')
    profile = route_profile()
    bound = copy.deepcopy(profile['binding'])
    # Historical forensic bundles include process-statistics/log/report hashes
    # that cannot identify a new execution. Retain every bound physical view,
    # constraint, source, and the audited state/proposal, then independently
    # reevaluate all current measured gates in the unchanged route helper.
    bound['files'] = {name: sha for name, sha in bound['files'].items()
                      if Path(name).suffix in ('.odb', '.def', '.v', '.sdc', '.lef')
                      or name in (bound['source_state'],
                                  str(profile['screen_root']/'repaired/proposal.json'))}
    if bound['source_state'] not in bound['files']:
        raise ValueError('Missing audited physical state binding')
    if not all(any(name.endswith(suffix) for name in bound['files'])
               for suffix in ('.odb', '.def', '.v', '.sdc')):
        raise ValueError('Incomplete live physical identity binding')
    bound['run_binding'] = {k: v for k, v in expected.items() if k != 'status'}
    profile['binding'] = bound
    return profile


def export_package(config, state, output, package_root):
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, state, output, TAIL)
    lvs = json.loads(unique(output, '*-netgen-lvs/state_out.json').read_text())
    if lvs['metrics'].get('design__lvs_error__count') != 0:
        raise ValueError('Fresh integrated LVS fails')
    extraction = unique(output, '*-magic-spiceextraction/state_out.json').parent
    overlaps = classify_overlaps(extraction/'feedback.xml')
    if json.loads((extraction/'state_out.json').read_text())['metrics'].get('magic__illegal_overlap__count') != overlaps:
        raise ValueError('Overlap feedback disagrees with extraction metrics')
    gds_state = json.loads(unique(output, '*-klayout-streamout/state_out.json').read_text())
    lef_state = json.loads(unique(output, '*-magic-writelef/state_out.json').read_text())
    package_root.mkdir(parents=True, exist_ok=False)
    submission = package_root/'tt_submission'
    submission.mkdir()
    hashes = {}
    for view, suffix, views in [('gds', '.gds', gds_state), ('lef', '.lef', lef_state)]:
        source = Path(views[view])
        if not source.is_file() or source.stat().st_size == 0 or not source.resolve().is_relative_to(output.resolve()):
            raise ValueError('Missing fresh integrated '+view)
        target = submission/('tt_um_tripwire'+suffix)
        shutil.copyfile(source, target)
        hashes[view] = digest(target)
        if hashes[view] != digest(source):
            raise ValueError('Changed integrated submission '+view)
    shutil.copyfile(FIXTURES/'mux_submission_info.yaml', package_root/'info.yaml')
    (submission/'pdk.json').write_text(json.dumps({'PDK': 'ihp-sg13cmos5l'})+'\n')
    return dict(lvs_errors=0, recorded_macro_overlap_markers=overlaps,
                magic_markers_waived=False, raw_magic_drc_rerun=False,
                precheck_required=True, precheck_passed=False, exported_sha256=hashes)


def main():
    for path in ('runs/native-stock-screen', 'runs/wire600-mux-margin-clean',
                 'runs/wire600-mux-margin-route', 'runs/extracted-timing', str(OUTPUT),
                 'submission-package', '/tmp/native-source-run.json'):
        if Path(path).exists():
            raise ValueError('Integration requires fresh workspace: '+path)
    run = json.loads(Path('/tmp/wire600-clean-source-run.json').read_text())
    profile = live_profile(run, os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_SHA'])
    clean()
    route(profile)
    drt = unique(profile['output']/'qualified-route/drt', '*-openroad-detailedrouting/state_out.json')
    final = Path(json.loads(drt.read_text())['nl'])
    if digest(final) != FINAL_NETLIST_SHA:
        raise ValueError('Fresh final netlist differs from passing routed replay')
    config = json.loads(Path('src/config_electrical_incremental_route.json').read_text())
    if config['CLOCK_PERIOD'] != 20:
        raise ValueError('Integrated clock differs from accepted recipe')
    state = unique(Path('runs/extracted-timing'), '*-openroad-stapostpnr/state_out.json')
    OUTPUT.mkdir(exist_ok=False)
    receipt = export_package(config, state, OUTPUT/'export', Path('submission-package'))
    receipt.update(run_id=run['id'], head_sha=run['head_sha'], clean_synthesis=True,
                   physical_checkpoint_downloaded=False, extracted_gates_pass=True,
                   netlist_sha256=digest(final), exact_passing_replay_netlist=True,
                   official_signoff=False, qualified=False)
    for target in (OUTPUT/'gates.json', Path('submission-package/diagnostic_identity.json')):
        target.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
