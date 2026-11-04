"""Check that a stock screen exercised its selected native control."""
import json
import math
from pathlib import Path
import re


def one(root, pattern):
    paths = list(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f'Expected one {pattern}, found {len(paths)}')
    return paths[0]


def number(text, command, flag):
    values = re.findall(r'(?m)^\+ ' + re.escape(command) + r'\b[^\n]* '
                        + re.escape(flag) + r'\s+(\S+)', text)
    if not values:
        raise ValueError(f'Missing native {command} {flag}')
    return float(values[-1])


def validate(root, selected):
    root = Path(root)
    config = json.loads((root / 'resolved.json').read_text())
    for key, expected in selected['changes'].items():
        actual = config.get(key)
        if isinstance(expected, bool):
            matched = actual is expected
        elif isinstance(expected, str):
            allowed = ((key == 'SYNTH_BUFFER_CELL' and expected == 'sg13cmos5l_buf_2/A/X')
                       or (key == 'RSZ_DONT_TOUCH_RX'
                           and expected == r'(^|[./])trw_guard_mask_(node|diode)$'))
            if not allowed:
                raise ValueError('Unreviewed string control')
            matched = actual == expected
        elif isinstance(expected, list):
            allowed = ((key == 'EXTRA_EXCLUDED_CELLS' and expected in (
                ['sg13cmos5l_dlygate4sd3_1'], ['sg13cmos5l_buf_1']))
                or (key == 'GRT_LAYER_ADJUSTMENTS' and expected == [0, 0, 0.08, 0, 0]))
            if not allowed:
                raise ValueError('Unreviewed cell exclusion')
            matched = actual == expected
        else:
            matched = (isinstance(actual, (int, float)) and math.isfinite(actual)
                       and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9))
        if not matched:
            raise ValueError(f'Resolved profile mismatch: {key}')
    log = one(root, '*-openroad-globalplacement/openroad-globalplacement.log').read_text()
    values = re.findall(r'Placement target density:\s+([0-9.]+)', log)
    if not values:
        raise ValueError('Missing effective placement density')
    density = float(values[0]) * 100
    if ('PL_TARGET_DENSITY_PCT' in selected['changes']
            and not math.isclose(density, selected['changes']['PL_TARGET_DENSITY_PCT'], abs_tol=1e-6)):
        raise ValueError('Requested density was clamped; control did not take effect')
    result = dict(profile=selected['profile'], changes=selected['changes'],
                  requested_density_pct=config['PL_TARGET_DENSITY_PCT'],
                  initial_effective_density_pct=density)
    if selected['changes'].get('PL_OPTIMIZE_MIRRORING') is False:
        reviewed = []
        for stage in ('detailedplacement', 'resizertimingpostcts', 'resizertimingpostgrt'):
            path = one(root, f'*-openroad-{stage}/openroad-{stage}.log')
            text = path.read_text()
            if not re.search(r'(?m)^\+ detailed_placement\b', text):
                raise ValueError(f'Missing native legalization in {stage}')
            if re.search(r'(?m)^\+ optimize_mirroring\b|\[INFO DPL-0020\] Mirrored', text):
                raise ValueError(f'Placement mirroring remains active in {stage}')
            reviewed.append(str(path.relative_to(root)))
        result['native_mirroring_disabled_logs'] = reviewed
    if 'CTS_SINK_CLUSTERING_MAX_DIAMETER' in selected['changes']:
        if config.get('CTS_SINK_CLUSTERING_ENABLE') is not True or config.get('CTS_SINK_CLUSTERING_SIZE') != 8:
            raise ValueError('Clock diameter control requires enabled eight-sink clustering')
        text = one(root, '*-openroad-cts/openroad-cts.log').read_text()
        value = number(text, 'clock_tree_synthesis', '-sink_clustering_max_diameter')
        if not math.isclose(value, selected['changes']['CTS_SINK_CLUSTERING_MAX_DIAMETER'], abs_tol=1e-9):
            raise ValueError('Clock sink diameter control was not exercised')
        result['native_clock_cluster_max_diameter_um'] = value
        result['native_clock_cluster_size'] = 8
    if 'CTS_DISTANCE_BETWEEN_BUFFERS' in selected['changes']:
        text = one(root, '*-openroad-cts/openroad-cts.log').read_text()
        value = number(text, 'clock_tree_synthesis', '-distance_between_buffers')
        if not math.isclose(value, selected['changes']['CTS_DISTANCE_BETWEEN_BUFFERS'], abs_tol=1e-9):
            raise ValueError('Clock buffer spacing control was not exercised')
        result['native_clock_buffer_spacing_um'] = value
    if selected['changes'].get('CTS_BALANCE_LEVELS') is True:
        text = one(root, '*-openroad-cts/openroad-cts.log').read_text()
        commands = re.findall(r'(?m)^\+ clock_tree_synthesis\b[^\n]*', text)
        if not commands or '-balance_levels' not in commands[-1].split():
            raise ValueError('Clock-level balancing was not exercised')
        result['native_clock_balance_levels'] = True
    if 'EXTRA_EXCLUDED_CELLS' in selected['changes']:
        text = one(root, '*-openroad-resizertimingpostgrt/tt_um_tripwire.nl.v').read_text()
        excluded = selected['changes']['EXTRA_EXCLUDED_CELLS'][0]
        if re.search(r'\b' + re.escape(excluded) + r'\s+\S+\s*\(', text):
            raise ValueError('Excluded cell remains in final netlist: ' + excluded)
        counts = {master: len(re.findall(r'\b' + master + r'\s+\S+\s*\(', text))
                  for master in ('sg13cmos5l_dlygate4sd1_1', 'sg13cmos5l_dlygate4sd2_1',
                                 'sg13cmos5l_buf_1', 'sg13cmos5l_buf_2',
                                 'sg13cmos5l_buf_4', 'sg13cmos5l_buf_8', 'sg13cmos5l_buf_16')}
        if not any(counts.values()):
            raise ValueError('Missing mapped replacement cells')
        if excluded == 'sg13cmos5l_dlygate4sd3_1':
            result['excluded_coarse_delay_cells'] = 0
        else:
            if config.get('SYNTH_BUFFER_CELL') != 'sg13cmos5l_buf_2/A/X':
                raise ValueError('Small-buffer exclusion requires matching explicit buffer cell')
            if not re.search(r'\bsg13cmos5l_buf_(?:2|4|8|16)\s+\S+\s*\(', text):
                raise ValueError('Missing stronger replacement buffers')
            result['excluded_small_buffer_cells'] = 0
        result['replacement_cell_counts'] = counts
    if 'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH' in selected['changes']:
        text = one(root, '*-openroad-repairdesignpostgrt/openroad-repairdesignpostgrt.log').read_text()
        value = number(text, 'repair_design', '-max_wire_length')
        if not math.isclose(value, selected['changes']['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'], abs_tol=1e-9):
            raise ValueError('Wire-length control was not exercised')
        result['native_max_wire_length_um'] = value
    if 'GRT_DESIGN_REPAIR_MAX_SLEW_PCT' in selected['changes']:
        text = one(root, '*-openroad-repairdesignpostgrt/openroad-repairdesignpostgrt.log').read_text()
        value = number(text, 'repair_design', '-slew_margin')
        if not math.isclose(value, selected['changes']['GRT_DESIGN_REPAIR_MAX_SLEW_PCT'], abs_tol=1e-9):
            raise ValueError('Slew repair margin was not exercised')
        result['native_slew_repair_margin_pct'] = value
    if selected['changes'].get('RUN_POST_GRT_RESIZER_TIMING') is True:
        one(root, '*-openroad-resizertimingpostgrt/state_out.json')
        text = one(root, '*-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log').read_text()
        value = number(text, 'repair_timing', '-hold_margin')
        if not math.isclose(value, selected['changes']['GRT_RESIZER_HOLD_SLACK_MARGIN'], abs_tol=1e-9):
            raise ValueError('Late hold target was not exercised')
        if config.get('GRT_RESIZER_RUN_GRT') is not True:
            raise ValueError('Native late rerouting must remain enabled')
        result['native_late_hold_target_ns'] = value
    if selected['changes'].get('GRT_ANTENNA_REPAIR_DIODE_ONLY') is True:
        text = one(root, '*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
        commands = re.findall(r'(?m)^\+ repair_antennas\b[^\n]*', text)
        if not commands or '-diode_only' not in commands[-1] or '-jumper_only' in commands[-1]:
            raise ValueError('Diode-only antenna control was not exercised')
        if config.get('GRT_ANTENNA_REPAIR_JUMPER_ONLY') is True:
            raise ValueError('Conflicting native antenna modes')
        result['native_antenna_mode'] = 'diode_only'
    if 'GRT_ANTENNA_REPAIR_MARGIN' in selected['changes']:
        text = one(root, '*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
        value = number(text, 'repair_antennas', '-ratio_margin')
        if value != selected['changes']['GRT_ANTENNA_REPAIR_MARGIN']:
            raise ValueError('Antenna repair margin was not exercised')
        result['native_antenna_repair_margin_pct'] = value
    if 'PL_RESIZER_HOLD_SLACK_MARGIN' in selected['changes']:
        text = one(root, '*-openroad-resizertimingpostcts/openroad-resizertimingpostcts.log').read_text()
        value = number(text, 'repair_timing', '-hold_margin')
        if not math.isclose(value, selected['changes']['PL_RESIZER_HOLD_SLACK_MARGIN'], abs_tol=1e-9):
            raise ValueError('Early hold target was not exercised')
        result['native_early_hold_target_ns'] = value
    if 'GRT_ADJUSTMENT' in selected['changes']:
        if any(config.get('GRT_LAYER_ADJUSTMENTS', [])):
            raise ValueError('Layer overrides make the global reserve control ambiguous')
        pattern = ('*-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log'
                   if selected['changes'].get('RUN_POST_GRT_RESIZER_TIMING')
                   else '*-openroad-globalrouting/openroad-globalrouting.log')
        text = one(root, pattern).read_text()
        values = re.findall(r'Global adjustment:\s+([0-9.]+)%', text)
        if not values or not all(math.isclose(float(v)/100, selected['changes']['GRT_ADJUSTMENT'], abs_tol=1e-9) for v in values):
            raise ValueError('Global routing reserve was not exercised')
        result['native_global_adjustment'] = float(values[-1])/100
        result['routing_resources'] = {
            layer: dict(original=int(original), derated=int(derated))
            for layer, original, derated in re.findall(
                r'(?m)^\s*(\w+)\s+(?:Horizontal|Vertical)\s+(\d+)\s+(\d+)\s+[0-9.]+%', text)
        }
    if 'GRT_LAYER_ADJUSTMENTS' in selected['changes']:
        if config.get('GRT_ADJUSTMENT') != 0.16:
            raise ValueError('Metal3 control requires fixed global reserve')
        text = one(root, '*-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log').read_text()
        values = re.findall(r'Global adjustment:\s+([0-9.]+)%', text)
        if not values or any(float(v) != 16 for v in values):
            raise ValueError('Global reserve changed during Metal3 control')
        rows = re.findall(r'(?m)^\s*(Metal[234])\s+(?:Horizontal|Vertical)\s+(\d+)\s+(\d+)\s+[0-9.]+%', text)
        reference = {'Metal2': (232949, 186595), 'Metal3': (281986, 231982),
                     'Metal4': (228835, 182846)}
        for layer, (original, derated) in reference.items():
            found = [(int(a), int(b)) for name, a, b in rows if name == layer]
            if not found:
                raise ValueError('Missing layer resource evidence: ' + layer)
            for a, b in found:
                if a != original or (not derated < b < original if layer == 'Metal3' else b != derated):
                    raise ValueError('Wrong or ineffective Metal3 resource control: ' + layer)
        result['routing_resources'] = {name: dict(original=int(a), derated=int(b)) for name, a, b in rows}
    return result
