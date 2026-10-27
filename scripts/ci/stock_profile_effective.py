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
    return result
