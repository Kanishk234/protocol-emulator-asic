"""One-variable stock project-input trials on the verified combined RTL."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

BASE_PROFILE = 'rtl_shared_minbuf2_host_idle_ff'
BASE_RUN = 42305323874
BASE_CONFIG_SHA256 = '920caf31abceebb82e52707538061011689bdcfa02fcf1c13057c0cdf0abd567'
CLOCK75_CONFIG_SHA256 = '35bacb325c12276dd63f7e33b99f94b5e0d4940f7b3a22a6bd1e63424bc4c97a'
HOLD125_CONFIG_SHA256 = '4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7'
HOLD125_RUN = 42681697462
HOLD125_ARTIFACT_ID = 13708390816
VARIANTS = {
    'density64': {'PL_TARGET_DENSITY_PCT': 64},
    'clock75': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75},
    'late125': {'GRT_RESIZER_HOLD_SLACK_MARGIN': 0.125},
    'mode_ff': {},
    'debug_align': {},
    'clock75_wire180': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75,
                        'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH': 180},
    'clock75_slew25': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75,
                       'GRT_DESIGN_REPAIR_MAX_SLEW_PCT': 25},
    'clock75_constants_drive': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75},
    'clock75_all_drive': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75},
    'clock75_constants_ff': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75},
    'clock75_hold125': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75,
                        'GRT_RESIZER_HOLD_SLACK_MARGIN': 0.125},
    'clock75_hold100': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75,
                        'GRT_RESIZER_HOLD_SLACK_MARGIN': 0.10},
    'clock75_hold125_setup250': {'CTS_SINK_CLUSTERING_MAX_DIAMETER': 75,
                                 'GRT_RESIZER_HOLD_SLACK_MARGIN': 0.125,
                                 'GRT_RESIZER_SETUP_SLACK_MARGIN': 2.5},
}


def require_smoke(evidence):
    smoke = evidence.get('chip_smoke', {})
    if (evidence.get('chip_smoke_status') != 'passed'
            or (smoke.get('passed'), smoke.get('failed'), smoke.get('skipped')) != (5, 0, 0)):
        raise ValueError('Missing matched five-case chip smoke evidence')


def select(config, selected, variant):
    if variant not in VARIANTS:
        raise ValueError('Unreviewed stock project trial')
    blob = json.dumps(config, indent=2) + '\n'
    if hashlib.sha256(blob.encode()).hexdigest() != BASE_CONFIG_SHA256:
        raise ValueError('Wrong combined source project configuration')
    if (selected.get('profile') != BASE_PROFILE
            or selected.get('config_sha256') != BASE_CONFIG_SHA256
            or selected.get('rtl_patch') != 'shared_priority'
            or any(selected.get(k) is not True for k in ('c_select', 'idle_ff', 'host_port_align'))):
        raise ValueError('Wrong combined source profile')
    result, receipt = deepcopy(config), deepcopy(selected)
    result.update(VARIANTS[variant])
    receipt.update(profile='portable_' + variant, variant=variant,
                   comparison_reference_run=BASE_RUN,
                   comparison_reference_config_sha256=BASE_CONFIG_SHA256,
                   additional_changes_from_reference=deepcopy(VARIANTS[variant]),
                   hardware_unchanged=variant not in ('mode_ff', 'debug_align', 'clock75_constants_drive', 'clock75_all_drive', 'clock75_constants_ff'),
                   mode_ff=variant == 'mode_ff', host_debug_align=variant == 'debug_align',
                   clean_from_rtl=True, manual_checkpoint_repairs=False,
                   official_gds_signoff=False)
    receipt['changes'].update(VARIANTS[variant])
    receipt['config_sha256'] = hashlib.sha256((json.dumps(result, indent=2) + '\n').encode()).hexdigest()
    if variant == 'mode_ff':
        receipt['additional_changes_from_reference'] = {'source_patch': 'mode_ff/mode_ff_storage.patch'}
    if variant == 'debug_align':
        receipt['additional_changes_from_reference'] = {'source_patch': 'host_debug_align/host_debug_align.patch'}
    if variant.startswith('clock75_'):
        reference = deepcopy(config)
        reference.update(VARIANTS['clock75'])
        reference_sha = hashlib.sha256((json.dumps(reference, indent=2) + '\n').encode()).hexdigest()
        if reference_sha != CLOCK75_CONFIG_SHA256:
            raise ValueError('Clock75 comparison configuration drift')
        delta = {k: v for k, v in result.items() if reference.get(k) != v}
        if variant == 'clock75_hold125_setup250':
            hold125_reference = deepcopy(config)
            hold125_reference.update(VARIANTS['clock75_hold125'])
            hold125_sha = hashlib.sha256((json.dumps(hold125_reference, indent=2) + '\n').encode()).hexdigest()
            if hold125_sha != HOLD125_CONFIG_SHA256:
                raise ValueError('Hold125 comparison configuration drift')
            setup_delta = {k: v for k, v in result.items() if hold125_reference.get(k) != v}
            if setup_delta != {'GRT_RESIZER_SETUP_SLACK_MARGIN': 2.5}:
                raise ValueError('Setup250 must change only the setup margin from hold125')
            receipt.update(comparison_reference_run=HOLD125_RUN,
                           comparison_reference_artifact_id=HOLD125_ARTIFACT_ID,
                           comparison_reference_config_sha256=hold125_sha,
                           additional_changes_from_reference=setup_delta)
            return result, receipt
        source_variant = {'clock75_constants_drive': 'constants', 'clock75_all_drive': 'all_words'}.get(variant)
        if variant == 'clock75_constants_ff':
            if delta:
                raise ValueError('Root-storage trial must retain clock75 configuration')
            delta = {'source_patch': 'slot_root_storage/constants.patch'}
            receipt['slot_root_storage'] = 'constants'
        elif source_variant:
            if delta:
                raise ValueError('Source enable-drive trial must retain clock75 configuration')
            delta = {'source_patch': 'slot_enable_drive/' + source_variant + '.patch'}
            receipt['slot_enable_drive'] = source_variant
        elif len(delta) != 1:
            raise ValueError('Residual trial must change one field from clock75')
        receipt.update(comparison_reference_run=42456273203,
                       comparison_reference_artifact_id=13611529602,
                       comparison_reference_config_sha256=reference_sha,
                       additional_changes_from_reference=delta)
    return result, receipt


def prepare(root, variant):
    root = Path(root)
    config_path = root / 'src/config.json'
    selected_path = root / 'spikes/phase2_stock_flow/selected_profile.json'
    config, receipt = select(json.loads(config_path.read_text()),
                             json.loads(selected_path.read_text()), variant)
    if variant == 'mode_ff':
        from apply_mode_ff import apply
        evidence_dir = root / 'spikes/phase2_stock_flow/mode_ff'
        evidence = json.loads((evidence_dir / 'evidence.json').read_text())
        proofs = evidence.get('proofs', [])
        expected = {(0, 461), (1, 560)}
        if {(p['full'], p['equivalence_points']) for p in proofs} != expected:
            raise ValueError('Missing complete mode-storage equivalence evidence')
        if any(p['phase_cycles'] < 2080 or p['phase_checks'] < 10400 for p in proofs):
            raise ValueError('Missing phase/reset coverage')
        require_smoke(evidence)
        receipt['source_application'] = apply(root, evidence_dir)
    if variant == 'debug_align':
        from apply_host_debug_align import apply
        evidence_dir = root / 'spikes/phase2_stock_flow/host_debug_align'
        evidence = json.loads((evidence_dir / 'evidence.json').read_text())
        proofs = evidence.get('proofs', [])
        if {(p['nl'], p['nu'], p['points']) for p in proofs} != {(2, 4, 1062), (3, 6, 1144)}:
            raise ValueError('Missing complete host debug alignment equivalence evidence')
        require_smoke(evidence)
        receipt['source_application'] = apply(root, evidence_dir)
    if receipt.get('slot_enable_drive'):
        from apply_slot_enable_drive import apply
        evidence_dir = root / 'spikes/phase2_stock_flow/slot_enable_drive'
        source_variant = receipt['slot_enable_drive']
        evidence = json.loads((evidence_dir / 'evidence.json').read_text())['variants'][source_variant]
        if {(p['mode'], p['equivalence_points']) for p in evidence.get('proofs', [])} != {('asic', 872), ('flops', 752)}:
            raise ValueError('Missing actual synthesis-path module equivalence evidence')
        if (evidence.get('foundry_phase_cycles', 0) < 3125
                or evidence.get('foundry_phase_checks', 0) < 12288
                or evidence.get('wrong_enable_mutant_rejected') is not True):
            raise ValueError('Missing real foundry-cell phase/reset/negative-control evidence')
        require_smoke(evidence)
        receipt['source_application'] = apply(root, evidence_dir, source_variant)
    if receipt.get('slot_root_storage'):
        from apply_slot_root_storage import apply
        evidence_dir = root / 'spikes/phase2_stock_flow/slot_root_storage'
        evidence = json.loads((evidence_dir/'evidence.json').read_text())['variants']['constants']
        if {(p['mode'], p['equivalence_points']) for p in evidence.get('proofs', [])} != {('asic', 768), ('flops', 752)}:
            raise ValueError('Missing root-storage module equivalence evidence')
        if (evidence.get('mapped_foundry_phase_cycles', 0) < 3125
                or evidence.get('mapped_foundry_phase_checks', 0) < 12288
                or evidence.get('wrong_reset_mutant_rejected') is not True):
            raise ValueError('Missing mapped-cell phase/reset and negative-control evidence')
        require_smoke(evidence)
        receipt['source_application'] = apply(root, evidence_dir, 'constants')
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    selected_path.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
