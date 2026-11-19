from pathlib import Path
import os
import subprocess
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from unused_input_sweep import independent


def test_cofactor_proof_rejects_any_actual_dependence_on_the_changed_input():
    assert independent(0x1111,2) and independent(0x1111,3)
    assert not independent(0x1111,0) and not independent(0x1111,1)
    assert independent(0xEFEF,3) and not independent(0xEFEF,2)
    for truth,index in [(0x10000,2),(-1,2),(0x1111,4)]:
        with pytest.raises(ValueError):independent(truth,index)


def test_native_sweep_runner_does_not_import_compiler_packages():
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[3]/'spikes/r1'))
    subprocess.run([sys.executable,'-S','-c','import unused_input_sweep'],check=True,env=env)
