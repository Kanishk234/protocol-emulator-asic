"""Conditional interface math must refuse changed topology or weaker premises."""
import copy
import json
import os
import subprocess
import sys

import pytest
import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripc.linked_budget import compose_linked_response
from tripc.response import analyze_queries, analyze_response


def inputs(program='i2c_target_eeprom_guard'):
    image, _ = tripc.compile_file(PROGRAMS / f'{program}.trw')
    queries = json.loads((PROGRAMS / 'analysis/i2c_memory_response.json').read_text())
    budget = json.loads((PROGRAMS / 'analysis/i2c_memory_linked_budget.json').read_text())
    return image, queries, budget


def change_field(word, **changes):
    word = int(word, 16)
    for name, value in changes.items():
        shift, width = S.SLOT_FIELDS[name]
        word = (word & ~(((1 << width) - 1) << shift)) | value << shift
    return hex(word)


@pytest.mark.parametrize('program', ['i2c_target_eeprom', 'i2c_target_eeprom_guard'])
def test_composition_and_fixed_interface_contract(program):
    image, queries, budget = inputs(program)
    results = analyze_queries(image, queries)
    for name, response in results.items():
        r = compose_linked_response(image, response, budget)
        assert r['status'] == 'conditional_pass'
        assert not r['entry_premises_proven'] and not r['unconditional_pin_bound']
        assert r['pipeline_clocks'] == dict(rx_publish=3, tx_accept=1, edge_to_drive=3, observation_reserve=1)
        p = r['profiles']['fast_plus_at_20ns']
        assert p['armed_by_clocks'] == (8 if name == 'address_ack' else 6)
        assert p['ready_margin_clocks'] == (4 if name == 'address_ack' else 6)
        assert p['target_low_setup_bound_clocks'] == 21
        assert r['profiles']['fast_at_20ns']['target_low_setup_bound_clocks'] == 61
        assert r['profiles']['standard_at_20ns']['target_low_setup_bound_clocks'] == 231


@pytest.mark.parametrize('key,value', [
    ('tx_preload', True), ('tx_lentok', False), ('txmode', 'level'),
    ('rxmode', 'off'), ('rx_edge', 'fall'), ('tx_edge', 'rise'),
    ('od', False), ('idle', 0), ('carrier', 2), ('pin_b', None), ('pin_b', 8),
])
def test_unsafe_pin_modes_are_not_certified(key, value):
    image, queries, budget = inputs()
    image['pins']['U0'][key] = value
    response = analyze_response(image, queries['address_ack'])
    assert compose_linked_response(image, response, budget)['status'] == 'unsupported'


def test_stale_lane_result_is_rejected():
    image, queries, budget = inputs()
    response = analyze_response(image, queries['address_ack'])
    image['lanes']['L0']['k'][1] ^= 2
    r = compose_linked_response(image, response, budget)
    assert r['status'] == 'unsupported' and 'compiled image' in r['reason']


@pytest.mark.parametrize('mutation', ['owner', 'source', 'tap', 'filter', 'ctrl', 'call', 'keep'])
def test_topology_and_future_stream_must_match(mutation):
    image, queries, budget = inputs()
    if mutation == 'owner':
        image['own'] = [row for row in image['own'] if row[0] != 16]
    elif mutation in ('source', 'tap', 'filter'):
        row = next(row for row in image['connect'] if row[0] == 'U0.tx')
        if mutation == 'source': row[1] = 'L0.O1'
        elif mutation == 'tap': row[2] = 'tap'
        else: row[3] = 0
    else:
        index = 11 if mutation == 'call' else 8  # outside the first address-ACK chain
        fields = ({'OP': S.OPS['CALL']} if mutation == 'call' else
                  {'OT': S.TAGS['CTRL']} if mutation == 'ctrl' else {'KT': 1})
        image['lanes']['L0']['slots'][index] = change_field(image['lanes']['L0']['slots'][index], **fields)
    response = analyze_response(image, queries['address_ack'])
    assert response['status'] == 'bounded'
    assert compose_linked_response(image, response, budget)['status'] == 'unsupported'


@pytest.mark.parametrize('field,value', [('response_edge_min', 8), ('sample_edge_min', 6)])
def test_insufficient_edge_budget_fails(field, value):
    image, queries, budget = inputs()
    budget['profiles']['fast_plus_at_20ns'][field] = value
    response = analyze_response(image, queries['address_ack'])
    assert compose_linked_response(image, response, budget)['status'] == 'insufficient_budget'


def test_internal_latency_knobs_cannot_be_overridden():
    image, queries, budget = inputs()
    response = analyze_response(image, queries['address_ack'])
    for bad in [dict(budget, rx_publish=0), dict(budget, profiles={})]:
        with pytest.raises(ValueError):
            compose_linked_response(image, response, bad)
    budget['profiles']['fast_plus_at_20ns']['required_setup'] = 0
    with pytest.raises(ValueError):
        compose_linked_response(image, response, budget)


def test_repository_profile_matches_existing_stimulus_policy():
    from protomodels.i2c_memory import MemoryController
    image, _, budget = inputs()
    for name, period, high, limits in [
        ('standard_at_20ns', 500, 250, (200, 235, 13)),
        ('fast_at_20ns', 125, 60, (30, 65, 5)),
        ('fast_plus_at_20ns', 50, 13, (13, 25, 3)),
    ]:
        p = budget['profiles'][name]
        assert (p['response_edge_min'], p['sample_edge_min'], p['required_setup']) == limits
        assert MemoryController(period, high).required_setup == p['required_setup']
    assert json.loads((PROGRAMS.parent / 'src/config.json').read_text())['CLOCK_PERIOD'] == 20
    assert image['params']['ADDR'] == 0x50


def test_cli_composes_only_when_requested_and_fails_on_bad_budget(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(PROGRAMS.parent / 'tools'))
    command = [sys.executable, '-m', 'tripc', str(PROGRAMS / 'i2c_target_eeprom_guard.trw'),
               '--response-queries', str(PROGRAMS / 'analysis/i2c_memory_response.json'),
               '--linked-budget', str(PROGRAMS / 'analysis/i2c_memory_linked_budget.json')]
    r = subprocess.run(command, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert '| address_ack/fast_plus_at_20ns | 8 | 4 | 21 | 3 | conditional pass |' in r.stdout
    assert 'Entry and queue premises are NOT proved' in r.stdout
    _, _, budget = inputs()
    bad = copy.deepcopy(budget)
    bad['profiles']['fast_plus_at_20ns']['response_edge_min'] = 1
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(bad))
    r = subprocess.run(command[:-1] + [str(path)], capture_output=True, text=True, env=env)
    assert r.returncode == 2 and 'insufficient' in r.stdout
