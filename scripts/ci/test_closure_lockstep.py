import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('closure_l2', ROOT / 'test_internal/l2/run_injections.py')
l2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l2)


@pytest.mark.parametrize('output,mask', [('onehot', 'cand'), ('first_ready', 'ready')])
def test_priority_fault_reverses_every_nonempty_mask(output, mask):
    line = f"wire [11:0] {output} = {mask} & (~{mask} + 12'd1);"
    before, after = l2.priority_mutation(line)
    assert before == line
    expression = after.split('=', 1)[1].rstrip(';')
    for value in range(1, 4096):
        assert eval(expression, {'__builtins__': {}}, {mask: value}) == 1 << (value.bit_length() - 1)
    with pytest.raises(RuntimeError): l2.priority_mutation(line + '\n' + line)


def test_ambiguous_or_unknown_priority_is_not_credited():
    for text in ('unreviewed lane', "wire [11:0] onehot = cand & (~cand + 12'd1);\nwire [11:0] first_ready = ready & (~ready + 12'd1);"):
        with pytest.raises(RuntimeError): l2.priority_mutation(text)


@pytest.mark.parametrize('body,mutation,accepted', [
    ('<testcase/>', False, True), ('<testcase><failure/></testcase>', True, True),
    ('<testcase><skipped/></testcase>', False, False),
    ('<testcase><error/></testcase>', True, False),
    ('<testcase/>', True, False), ('', False, False),
])
def test_injection_credit_requires_actual_expected_xml(tmp_path, body, mutation, accepted):
    path = tmp_path / 'results.xml'; path.write_text('<testsuite>' + body + '</testsuite>')
    if accepted: l2.require_xml(path, mutation=mutation)
    else:
        with pytest.raises(RuntimeError): l2.require_xml(path, mutation=mutation)


def test_retained_control_evidence_is_not_deleted_or_overwritten(tmp_path, monkeypatch):
    monkeypatch.setenv('L2_EVIDENCE_DIR', str(tmp_path))
    with l2.evidence_directory('baseline-rx') as path: (path / 'actual.log').write_text('retain')
    assert (path / 'actual.log').read_text() == 'retain'
    with pytest.raises(FileExistsError):
        with l2.evidence_directory('baseline-rx'): pass


def test_selector_lockstep_uses_current_source_and_same_real_comparisons():
    import ast
    import re
    import yaml
    baseline = yaml.safe_load((ROOT / '.github/workflows/tripwire-closure-lockstep.yaml').read_text())
    current = yaml.safe_load((ROOT / '.github/workflows/tripwire-selector-lockstep.yaml').read_text())
    reference = {s.get('name'): s for s in baseline['jobs']['lockstep']['steps']}
    steps = {s.get('name'): s for s in current['jobs']['lockstep']['steps']}
    for name in ('Compare one million clocks on the current candidate',
                 'Require clean controls then detect both injected RTL faults'):
        assert steps[name]['run'] == reference[name]['run']
    prepare = steps['Prepare project venv and injection guards']['run']
    assert 'from selector_final_gl import prepare_expected, verify_expected' in prepare
    assert 'prepare_expected(root)' in prepare and 'verify_expected(root)' in prepare
    check = steps['Check actual outcomes and unchanged candidate']['run']
    assert 'candidate_inputs(root) ==' in check and 'verify_expected(root)' in check
    assert 'compared 1000000 clocks, zero divergences' in check
    for step in steps.values():
        for block in re.findall(r"python - <<'(PY(?:CODE)?)'\n(.*?)\n\1", step.get('run', ''), re.S):
            ast.parse(block[1])
