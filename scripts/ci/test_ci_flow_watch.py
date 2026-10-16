import json
import sys

import pytest

from ci_flow_watch import run


def test_success_and_failure_exit_codes_and_logs_preserved(tmp_path):
    for code in (0, 7):
        log = tmp_path/f'flow{code}.log'
        result = run([sys.executable, '-u', '-c',
                      f'print("useful evidence", flush=True); raise SystemExit({code})'],
                     log, heartbeat=.02, total_timeout=5, synthesis_timeout=2)
        assert result == code
        assert 'useful evidence' in log.read_text()
        receipt = json.loads(log.with_suffix('.watch.json').read_text())
        assert receipt['returncode'] == code
        assert receipt['timeout_reason'] is None


@pytest.mark.parametrize('synthesis', [False, True])
def test_deadlines_stop_real_child_and_preserve_partial_output(tmp_path, synthesis):
    script = 'import time; '
    if synthesis:
        script += 'print("Running \'Yosys.Synthesis\' at step.py:1138", flush=True); '
    script += 'time.sleep(30)'
    log = tmp_path/'flow.log'
    result = run([sys.executable, '-u', '-c', script], log, heartbeat=.02,
                 total_timeout=3 if synthesis else .2, synthesis_timeout=.15)
    receipt = json.loads(log.with_suffix('.watch.json').read_text())
    assert result == 124
    assert receipt['timeout_reason'] == ('synthesis deadline' if synthesis else 'total flow deadline')
    assert receipt['elapsed_seconds'] < 3


def test_leaving_synthesis_disarms_its_deadline(tmp_path):
    script = ('import time; print("Running \'Yosys.Synthesis\'", flush=True); '
              'time.sleep(.06); print("Running \'OpenROAD.Floorplan\'", flush=True); '
              'time.sleep(.25)')
    assert run([sys.executable, '-u', '-c', script], tmp_path/'flow.log',
               heartbeat=.02, total_timeout=3, synthesis_timeout=.15) == 0


def test_refuses_to_overwrite_evidence(tmp_path):
    log = tmp_path/'flow.log'
    log.write_text('prior evidence')
    with pytest.raises(ValueError):
        run([sys.executable, '-c', 'pass'], log)
    assert log.read_text() == 'prior evidence'
