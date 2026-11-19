"""Reject incomplete wire annotation and configuration substitutions."""
from pathlib import Path
import os
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from routed_timing import annotation, assert_cases


def test_prepared_runtime_imports_without_compiler_or_site_packages():
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[3]/'spikes/r1'))
    subprocess.run([sys.executable, '-S', '-c', 'import routed_timing'], env=env, check=True)


def report(first='Found 0 unannotated drivers.\n', second='Found 0 partially unannotated drivers.\n'):
    return ('R1_ANNOTATION_BEGIN\n'+first+second+'R1_ANNOTATION_END\n'
            'R1_ACTIVE_PIN\tu0/X\nR1_ACTIVE_PIN\tclock_buffer/X\nR1_ACTIVE_END\n')


def test_missing_spef_control_and_partial_clock_annotation_are_detected():
    assert annotation(report())['passed']
    for text in [report('Found 1 unannotated drivers.\n u0/X\n'),
                 report(second='Found 1 partially unannotated drivers.\n root_clock/X\n  clock_buffer/X\n')]:
        assert not annotation(text)['passed']
    assert annotation(report('Found 1 unannotated drivers.\n inactive/X\n'))['passed']
    assert annotation(report(second='Found 1 partially unannotated drivers.\n u0/X\n  inactive/A\n'))['passed']
    assert not annotation(report('Found 1 unannotated drivers.\n clock_buffer\\/X\n'))['passed']


@pytest.mark.parametrize('text', [
    report('Found 2 unannotated drivers.\n u0/X\n'),
    report('Found 1 unannotated drivers.\n u0/X\n', 'Found 1 partially unannotated drivers.\n u0/X\n'),
    report().replace('R1_ACTIVE_END\n', ''),
    report().replace('Found 0 unannotated drivers.', 'unknown format'),
    report()+'R1_ACTIVE_PIN\tu0/X\n',
])
def test_incomplete_or_ambiguous_annotation_cannot_pass(text):
    with pytest.raises(ValueError):
        annotation(text)


def test_real_loaded_configuration_cannot_be_substituted_duplicated_or_excepted():
    text = ('set p [get_pins -quiet {tile/_12_/Q}]\n'
            'if {[llength $p]!=1} {error "missing configuration pin"}\n'
            'set_case_analysis 1 $p\nincr observed')
    assert_cases(text, {'tile/_12_/Q': '1'})
    for changed in [text.replace('analysis 1', 'analysis 0'), text+text,
                    text+'\nset_false_path -through [all_inputs]']:
        with pytest.raises(ValueError):
            assert_cases(changed, {'tile/_12_/Q': '1'})
