from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from prepare_closure_candidate import preparation, export, WORKFLOW


def test_uses_exact_workflow_preparation_without_launching_physical_flow():
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / WORKFLOW).read_text())
    scripts, env = preparation(workflow)
    assert len(scripts) == 2
    assert 'git apply --check' in scripts[0]
    assert scripts[1] == 'python scripts/ci/official_nov9_preflight.py prepare "8x4"'
    assert env['PORTABLE_VARIANT'] == 'clock75_hold125'


@pytest.mark.parametrize('mutation', ('geometry', 'profile', 'duplicate'))
def test_wrong_candidate_or_ambiguous_preparation_rejected(mutation):
    root = Path(__file__).resolve().parents[2]
    workflow = deepcopy(yaml.safe_load((root / WORKFLOW).read_text()))
    job = workflow['jobs']['screen']
    if mutation == 'geometry':
        job['strategy']['matrix']['tiles'].append('6x4')
    elif mutation == 'profile':
        job['env']['PORTABLE_VARIANT'] = 'clock75'
    else:
        job['steps'].append(deepcopy(job['steps'][1]))
    with pytest.raises(ValueError):
        preparation(workflow)


def test_existing_export_is_preserved(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    output = tmp_path / 'candidate'
    output.mkdir()
    (output / 'evidence').write_text('keep')
    with pytest.raises(ValueError, match='must not exist'):
        export(root, output)
    assert (output / 'evidence').read_text() == 'keep'


def test_export_inside_worktree_rejected(tmp_path):
    with pytest.raises(ValueError, match='outside'):
        export(tmp_path, tmp_path / 'build/candidate')
