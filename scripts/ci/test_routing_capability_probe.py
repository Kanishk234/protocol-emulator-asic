import pytest
from routing_capability_probe import summarize


def sample(flags=True):
    s='\n'.join(f'TRIPWIRE CAPABILITY {c} 1' for c in ['global_route','read_guides','read_global_route_segments','write_global_route_segments','probe_complete'])
    return s+'\nTRIPWIRE HELP BEGIN global_route\n'+('-start_incremental -end_incremental' if flags else 'global_route')+'\nTRIPWIRE HELP END global_route\n'


def test_incremental_capability_is_not_route_preservation_proof():
    x=summarize(sample())
    assert x['incremental_flags_documented']
    assert not x['checkpoint_restoration_tested'] and not x['unchanged_routes_preserved']
    assert not x['physical_change_applied'] and not x['official_signoff']


def test_missing_incremental_flag_not_supported():
    assert not summarize(sample(False))['incremental_flags_documented']


@pytest.mark.parametrize('fault',['missing','duplicate','incomplete'])
def test_bad_probe_evidence_refused(fault):
    s=sample()
    if fault=='missing':s=s.replace('TRIPWIRE CAPABILITY read_guides 1','')
    elif fault=='duplicate':s+='TRIPWIRE CAPABILITY read_guides 1\n'
    else:s=s.replace('probe_complete 1','probe_complete 0')
    with pytest.raises(ValueError):summarize(s)
