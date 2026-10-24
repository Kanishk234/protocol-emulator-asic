from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from run_timing import compare,parse_log,same_topology


def coverage():
    return dict(ffs={'active':dict(clock='X',clocked=True,fanout='OUT',data='X'),
                     'constant':dict(clock='X',clocked=True,fanout='',data='0'),
                     'inactive':dict(clock='0',clocked=False,fanout='',data='X')},
                endpoints={'active/D':1.2,'OUT':2.1},structural_loops=8)


def test_static_storage_and_real_active_paths_are_classified_separately():
    a=coverage();r=compare(a,deepcopy(a),3)
    assert (r['inactive_unobservable'],r['clocked_timed'],r['clocked_constant_data'])==(1,1,1)
    assert r['structural_loops']==8 and not r['loop_policy_sensitive']


@pytest.mark.parametrize('change',[lambda a:a['ffs']['inactive'].update(fanout='active/D'),
                                  lambda a:a['ffs']['inactive'].update(clock='X'),
                                  lambda a:a['ffs']['constant'].update(data='X')])
def test_missing_or_observable_clock_data_coverage_is_not_waived(change):
    a=coverage();change(a)
    with pytest.raises(ValueError):compare(a,deepcopy(a),3)


def test_loop_cut_policy_cannot_silently_change_a_path_or_omit_an_endpoint():
    a=coverage();b=deepcopy(a);b['endpoints']['active/D']-=0.01
    result=compare(a,b,3)
    assert result['loop_policy_sensitive'] and result['loop_policy_differences'][0]['endpoint']=='active/D'
    b=deepcopy(a);del b['endpoints']['OUT']
    with pytest.raises(ValueError,match='Loop policy'):compare(a,b,3)


def test_partial_logs_errors_duplicates_and_nonfinite_numbers_are_rejected():
    text='RUNSTA_CONFIGURATION 8736\nRUNSTA_CLOSED 8736\nRUNSTA_ENDPOINT\tactive/D\t1.2\nRUNSTA_END\n'
    assert parse_log(text)['endpoints']=={'active/D':1.2}
    for bad in [text.removesuffix('RUNSTA_END\n'),'Error: bad constraint\n'+text,
                text.replace('RUNSTA_CLOSED 8736','RUNSTA_CLOSED 8735'),
                text.replace('1.2','nan'),text.replace('RUNSTA_END','RUNSTA_ENDPOINT\tactive/D\t1.2\nRUNSTA_END')]:
        with pytest.raises(ValueError):parse_log(bad)


def test_structural_format_conversion_preserves_aliases_and_constants():
    a={'ports':{'I':{'direction':'input','bits':[1]},'O':{'direction':'output','bits':[2]}},
       'cells':{'u':{'type':'T','connections':{'A':[1],'X':[2],'EN':['1']}}}}
    b=deepcopy(a);b['ports']['I']['bits']=[10];b['ports']['O']['bits']=[20]
    b['cells']['u']['connections']={'A':[10],'X':[20],'EN':['1']};same_topology(a,b)
    b['cells']['u']['connections']['EN']=['0']
    with pytest.raises(ValueError,match='connectivity'):same_topology(a,b)
