import json
import shlex
import xml.etree.ElementTree as ET

import pytest
from protocol_replay import ALL_TESTS, SHARDS, aggregate, check_xml, shell_filter, validate_metadata


def xml_file(root, shard):
    suite = ET.Element('testsuite')
    for name in sorted(ALL_TESTS):
        case = ET.SubElement(suite, 'testcase', classname='test_l3', name=name, sim_time_ns='100')
        if name not in SHARDS[shard]:
            ET.SubElement(case, 'skipped')
    path = root / ('results_' + shard + '.xml')
    ET.ElementTree(suite).write(path)
    return path


@pytest.mark.parametrize('shard', SHARDS)
def test_exact_coverage_and_filter(tmp_path, shard):
    import re
    pattern = shlex.split(shell_filter(shard).replace('$$', '$'))[0]
    assert {n for n in ALL_TESTS if re.search(pattern, 'test_l3.' + n)} == set(SHARDS[shard])
    assert check_xml(xml_file(tmp_path, shard), shard)['selected_count'] == len(SHARDS[shard])


@pytest.mark.parametrize('fault', ['missing', 'skip', 'failure', 'duplicate', 'zero', 'nan'])
def test_bad_selected_case_rejected(tmp_path, fault):
    path = xml_file(tmp_path, 'serial')
    tree = ET.parse(path)
    root = tree.getroot()
    case = next(c for c in root if c.get('name') in SHARDS['serial'])
    if fault == 'missing': root.remove(case)
    elif fault == 'skip': ET.SubElement(case, 'skipped')
    elif fault == 'failure': ET.SubElement(case, 'failure')
    elif fault == 'duplicate': root.append(case)
    else: case.set('sim_time_ns', 'nan' if fault == 'nan' else '0')
    tree.write(path)
    with pytest.raises(ValueError): check_xml(path, 'serial')


def test_aggregate_requires_same_inputs(tmp_path):
    identity = dict(sigrok_required=True, simulator='Tiny Tapeout Icarus 13', model_hashes=dict.fromkeys('abcd', 'hash'))
    for shard in SHARDS:
        path = xml_file(tmp_path, shard)
        receipt = dict(identity=identity, results=check_xml(path, shard))
        (tmp_path / ('receipt_' + shard + '.json')).write_text(json.dumps(receipt))
    assert aggregate(tmp_path, tmp_path / 'all')['passed'] == 22
    path = tmp_path / 'receipt_serial.json'
    receipt = json.loads(path.read_text());receipt['identity']['source_sha'] = 'changed'
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='identity'): aggregate(tmp_path, tmp_path / 'all')


def test_source_identity():
    run = dict(id=1, status='completed', conclusion='success', head_branch='main', path='.github/workflows/gds.yaml', head_sha='a'*40)
    commit = dict(commit='a'*40, workflow_url='https://github.com/owner/repo/actions/runs/1')
    validate_metadata(run, commit)
    branch = 'tripwire/d192-se0-official'
    candidate = dict(run, head_branch=branch)
    with pytest.raises(ValueError): validate_metadata(candidate, commit)
    validate_metadata(candidate, commit, expected_branch=branch)
    with pytest.raises(ValueError): validate_metadata(candidate, dict(commit, commit='b'*40), expected_branch=branch)
    with pytest.raises(ValueError): validate_metadata(dict(candidate, status='in_progress'), commit, expected_branch=branch)
    run['conclusion'] = 'failure'
    with pytest.raises(ValueError): validate_metadata(run, commit)


def test_filter_survives_make_and_shell():
    import os
    import subprocess
    import re
    env = dict(os.environ, COCOTB_TEST_FILTER=shell_filter('serial'))
    recipe = "all:\n\t@printf '%s' $(COCOTB_TEST_FILTER)\n"
    pattern = subprocess.check_output(['make', '--no-print-directory', '-f', '-'], input=recipe, text=True, env=env)
    assert {n for n in ALL_TESTS if re.search(pattern, 'test_l3.' + n)} == set(SHARDS['serial'])
