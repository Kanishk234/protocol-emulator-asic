"""Keep a diagnostic snapshot bound to the candidate it describes."""
import os
from pathlib import Path
import subprocess
import sys


def test_snapshot_cannot_escape_candidate_directory(tmp_path):
    root=Path(__file__).resolve().parents[3]
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,(root/'tools',root/'spikes/r1'))))
    command=[sys.executable,str(root/'spikes/r1/sa_cone.py')]
    for name in ('capsule','native','functional','out'):
        command+=['--'+name,str(tmp_path/name)]
    result=subprocess.run(command+['--snapshot','../other-case.json'],env=env,
                          capture_output=True,text=True,timeout=20)
    assert result.returncode!=0
    assert 'Snapshot must remain within the candidate output directory' in result.stderr
