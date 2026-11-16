from pathlib import Path
import subprocess

import pytest
import yaml

import cache_only_functional_audit as audit

ROOT = Path(__file__).resolve().parents[2]


def source_metadata():
    return dict(id=audit.SOURCE_RUN, head_sha=audit.SOURCE_SHA, head_branch='main',
                conclusion='failure', path='.github/workflows/gds-official-dev4-cache-no-owner-screen.yaml')


def test_exact_owner_identity_required():
    good = source_metadata()
    audit.validate_source_metadata(good)
    for key in good:
        with pytest.raises(ValueError):
            audit.validate_source_metadata({**good, key: 'wrong'})


@pytest.mark.parametrize('change', [{'CLOCK_PERIOD': 21}, {'CLOCK_UNCERTAINTY_CONSTRAINT': 0.1},
                                   {'PNR_SDC_FILE': 'custom'}, {'SIGNOFF_SDC_FILE': 'legacy'}])
def test_constraint_drift_rejected(change):
    audit.validate_stock_constraints({'CLOCK_PERIOD': 20})
    with pytest.raises(ValueError):
        audit.validate_stock_constraints({'CLOCK_PERIOD': 20, **change})


def test_workflow_restores_only_bound_owner_and_keeps_native_engine():
    w = yaml.safe_load((ROOT / '.github/workflows/gds-cache-only-functional-setup-audit.yaml').read_text())
    assert w['on'] == {'workflow_dispatch': {}}
    job = w['jobs']['audit']
    assert job['env']['SOURCE_RUN'] == str(audit.SOURCE_RUN)
    assert job['env']['SOURCE_ARTIFACT'] == 'official-dev4-cache-no-owner-43957277296'
    text = '\n'.join(s.get('run', '') for s in job['steps'])
    assert audit.SOURCE_SHA in text
    assert 'dcf36133a369abc8f3c5e5738cd4d82e4903c0e0' in text
    assert 'python scripts/ci/cache_only_functional_audit.py' in text
    assert 'repair_timing' not in text and 'DetailedRouting' not in text
    for step in job['steps']:
        if 'run' in step:
            subprocess.run(['bash', '-n'], input=step['run'], text=True, check=True)
    source = (ROOT / 'scripts/ci/cache_only_functional_audit.py').read_text()
    assert "extra_tcl=Path('scripts/ci/functional_setup_frontier.tcl')" in source
    assert "check_stock_report_uncertainty((matches[0].parent / filename).read_text())" in source
    assert 'if hashes() != before:' in source
    assert 'physical_repairs=False, detailed_routing_performed=False' in source
