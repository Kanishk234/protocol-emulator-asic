"""Measured risk-class repair: exact paired evidence, no signoff relaxation."""
import hashlib
import json
from pathlib import Path
from combined_physical_plan import plan as build, target_call as emit, validate_change as conserve
from electrical_risk_inventory import inventory

BINDING={'source_run': 38689478738, 'nl_sha': '908463cf840bc09f34ad94e0c08a3773a86cb7ac22893506d1dd2cc7855f9b40', 'def_sha': 'a7ad3e784cd9823a3fabf3e06643387fae050ebc9269dad6b678f4761cb992fa', 'report_sha': 'e5b17bd603775c98ceb6f3728a5de8a21831953eba1ffb59dd2ebaaa2fac0ce4', 'checks_sha': {'nom_typ_1p20V_25C': '9b15ca2ee158458de0d5fe3d676c3f89d5d0641ec58ebb58e89187d9b702357e', 'nom_slow_1p08V_125C': 'dc37d189b36d943984004c8d4a85ef14bb630310f2cbcdb47229afd47c12e196', 'nom_fast_1p32V_m40C': 'd2352189d4f2c0f519ae3e89cf159ab5671f1762a215344c730dff9bc5adf0d7'}, 'prefix': 'tripwire_margin_risk_38689478738_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 4, 'setup': {}, 'targets': {}, 'normalize_instances': True, 'preventive_sources': {'_03012_': ['slew'], '_03775_': ['slew'], '_03801_': ['fanout'], '_03807_': ['fanout'], '_03811_': ['fanout'], '_03933_': ['fanout'], '_04460_': ['slew'], '_04467_': ['capacitance', 'slew'], '_04486_': ['slew'], '_04493_': ['slew'], '_04496_': ['slew'], '_06754_': ['fanout'], '_07690_': ['slew'], '_07879_': ['fanout'], '_07894_': ['capacitance', 'slew'], '_08040_': ['slew'], '_09434_': ['slew'], '_10017_': ['slew'], '_10088_': ['fanout', 'slew'], '_10098_': ['slew'], '_12455_': ['slew'], '_16318_': ['fanout', 'slew'], '_16423_': ['slew'], '_17347_': ['slew'], '_17350_': ['slew'], '_17357_': ['slew'], '_20007_': ['slew'], '_20038_': ['slew'], '_20047_': ['slew'], '_20084_': ['slew'], '_20111_': ['slew'], '_20453_': ['slew'], '_20459_': ['slew'], '_20475_': ['slew'], '_21180_': ['slew'], 'net7208': ['capacitance'], 'net7430': ['fanout'], 'net7432': ['fanout'], 'net7472': ['fanout'], 'net7743': ['fanout'], 'net8062': ['capacitance'], 'net8063': ['capacitance'], 'net8390': ['fanout'], 'net8554': ['capacitance', 'fanout'], 'net8636': ['fanout'], 'net8647': ['capacitance'], 'net8915': ['fanout'], 'net8952': ['fanout'], 'net8966': ['fanout'], 'tripwire_combined_21_net': ['fanout'], 'tripwire_combined_35_net': ['fanout'], 'tripwire_decode_combined_4_net': ['fanout'], 'tripwire_hold_electrical_136_net': ['fanout'], 'u_chip.g_lane[0].ot[19]': ['fanout'], 'u_chip.g_lane[0].u_lane.time_now[2]': ['fanout'], 'u_chip.g_lane[0].u_lane.time_now[6]': ['fanout'], 'u_chip.g_lane[0].u_lane.time_now[9]': ['fanout'], 'u_chip.g_lane[1].regs[1]': ['fanout'], 'u_chip.g_lane[1].regs[8]': ['fanout'], 'u_chip.g_unit[0].u_prod.tok[10]': ['fanout'], 'u_chip.g_unit[0].u_prod.tok[15]': ['fanout'], 'u_chip.port_state[61]': ['fanout'], 'u_chip.port_state[63]': ['fanout'], 'u_chip.port_state[65]': ['fanout']}}
MARGIN_SHA='ead349bd780b2ae18405d1aae2d9d62851f4f1755fcad0dd9fa79ddec9c7128e'
PROTECTED={'clknet_2_1__leaf_u_chip.g_unit[0].u_cfg.g_word[0].g_stored.gclk': ['fanout']}


def plan(*args, evidence=Path('runs/electrical-margin-probe/summary.json')):
    if hashlib.sha256(args[0].encode()).hexdigest() != BINDING['nl_sha']:
        raise ValueError('Wrong margin-risk netlist')
    data = evidence.read_bytes()
    if hashlib.sha256(data).hexdigest() != MARGIN_SHA:
        raise ValueError('Wrong paired margin summary')
    actual = inventory(json.loads(data), args[0], args[1])
    if actual['sources'] != BINDING['preventive_sources'] or actual['protected_sources'] != PROTECTED:
        raise ValueError('Risk-class selection changed')
    result = build(*args, binding=BINDING)
    if result['added_buffers'] != 123 or result['total_electrical_target_nets'] != 64:
        raise ValueError('Wrong bounded risk-class repair count')
    return result


def target_call(layout, proposal):
    return emit(layout, proposal, binding=BINDING)


def validate_change(before, after, proposal):
    return conserve(before, after, proposal, binding=BINDING)
