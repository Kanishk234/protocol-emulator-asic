"""Hand-computed native cost diagnostics; no EDA or alternative ledger."""
import hashlib
import json

import pytest

from autonomy import native_costs as costs


def snapshot(*, scalar=3, demand=1, soft=True, clock=True, usage=1, off_support=0, multiplicity=1, second=False):
    rows=['SCHEMA\twarp-native-corridor-v1','INDEXING\tzero_based_fast_route_layers_and_grid',
          'MODEL_GATE\tusage_ledger_verified\tfalse','VIA_MODEL\tglobal_route_steps_only_no_physical_cut_capacity',
          'GRID\t2\t2\t1\t0\t0\t100',f'EDGE\tH\t0\t0\t0\t10\t{usage}\t0\t10',
          f'EDGE\tH\t0\t0\t1\t10\t{off_support}\t0\t10',
          'EDGE\tV\t0\t0\t0\t10\t0\t0\t10','EDGE\tV\t0\t1\t0\t10\t0\t0\t10']
    settings=[(scalar,demand,soft,clock,multiplicity)]
    if second:settings.append((1,1,False,False,1))
    for slot,(sc,dem,so,cl,count) in enumerate(settings):
        rows.extend([f'NET\t{slot}\t{11+slot}\tnet_{slot}\t{int(cl)}\t{int(so)}\t{sc}\t0\t0\t0\t2',
            f'DEMAND\t{slot}\t0\t{dem}',f'PIN\t{slot}\t0\t0\t0\t0',f'PIN\t{slot}\t1\t1\t0\t0',
            f'TREE\t{slot}\t2\t2\t1',f'TREE_EDGE\t{slot}\t0\t1\t0\t1\t0\t1\t{count}\t{count+1}'])
        for index in range(count):
            a,b=(0,1) if index%2==0 else (1,0)
            rows.append(f'STEP\t{slot}\t0\t{index}\t{a}\t0\t0\t{b}\t0\t0\t{dem}')
    rows.append(f'COMPLETE\t{len(settings)}\t{len(settings)}\t{sum(item[4] for item in settings)}')
    return ('\n'.join(rows)+'\n').encode()


def test_clean_layer_ledger_despite_divergent_soft_scalar():
    raw=snapshot(scalar=3,demand=1,usage=1)
    result=costs.diagnose_bytes(raw)
    assert result['original_usage_ledger_reconciled']
    assert not result['comparison']['all_edge_exact_match']
    assert result['comparison']['residual_support_edges']==0
    assert result['comparison']['hypothesis_only_support_edges']==1
    assert result['soft_scalar_not_one']==[{'slot':0,'database_id':11,'name':'net_0',
        'clock':True,'scalar_cost':3,'layer_demands':[1]}]
    assert result['input_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['hypothetical_weighting_accepted'] is False


@pytest.mark.parametrize('scalar,demand,usage,residual',[(3,1,3,2),(0,1,0,-1)])
def test_exact_signed_fingerprint_is_diagnostic_only(scalar,demand,usage,residual):
    result=costs.diagnose_bytes(snapshot(scalar=scalar,demand=demand,usage=usage))
    comp=result['comparison']
    assert comp['all_edge_exact_match'] and comp['support_exact_match']
    assert comp['overlap_same_sign_edges']==1 and comp['overlap_equal_absolute_magnitude_edges']==1
    assert comp['residual']['signed_sum']==residual
    assert result['edge_comparisons'][0]['raw_minus_layer_multiset']==residual
    assert not result['original_usage_ledger_reconciled']
    assert not result['hypothetical_weighting_accepted']
    assert not result['native_inputs_authenticated'] and not result['physical_acceptance']


def test_residual_off_hypothesis_support_is_not_hidden():
    result=costs.diagnose_bytes(snapshot(usage=3,off_support=4))
    comp=result['comparison']
    assert comp['off_hypothesis_support_edges']==1
    assert comp['residual_minus_hypothesis_l1']==4
    assert not comp['all_edge_exact_match'] and not comp['support_exact_match']
    assert len(result['edge_comparisons'])==2


def test_opposite_sign_and_wrong_magnitude_reported_exactly():
    result=costs.diagnose_bytes(snapshot(scalar=3,demand=1,usage=0))
    comp=result['comparison']
    assert comp['overlap_opposite_sign_edges']==1 and comp['overlap_same_sign_edges']==0
    assert comp['overlap_equal_absolute_magnitude_edges']==0
    assert comp['residual_minus_hypothesis_l1']==3


def test_multiset_occurrences_are_not_deduplicated():
    result=costs.diagnose_bytes(snapshot(scalar=3,demand=1,usage=9,multiplicity=3))
    row=result['edge_comparisons'][0]
    assert row['layer_multiset_usage']==3
    assert row['raw_minus_layer_multiset']==6
    assert row['hypothetical_soft_scalar_minus_layer']==6
    assert result['comparison']['all_edge_exact_match']


def test_nonsoft_scalar_difference_is_excluded_from_hypothesis():
    result=costs.diagnose_bytes(snapshot(scalar=3,demand=2,usage=3,soft=False))
    assert result['soft_scalar_not_one']==[]
    assert result['comparison']['hypothesis_support_edges']==0
    assert result['comparison']['off_hypothesis_support_edges']==1


def test_full_group_distribution_preserves_clock_and_demands():
    result=costs.diagnose_bytes(snapshot(usage=2,second=True))
    assert result['live_net_count']==sum(row['net_count'] for row in result['cost_distribution'])==2
    assert result['cost_distribution']==[
        {'soft_ndr':False,'clock':False,'scalar_cost':1,'layer_demands':[1],'net_count':1},
        {'soft_ndr':True,'clock':True,'scalar_cost':3,'layer_demands':[1],'net_count':1}]
    assert result['original_usage_ledger_reconciled']


def test_deterministic_output_and_file_hash(tmp_path):
    path=tmp_path/'native.tsv';raw=snapshot();path.write_bytes(raw)
    first=costs.diagnose_file(path);second=costs.diagnose_file(path)
    assert json.dumps(first,sort_keys=True)==json.dumps(second,sort_keys=True)
    assert first['raw_edge_count']==4 and first['input_sha256']==hashlib.sha256(raw).hexdigest()


def test_malformed_export_is_rejected_without_hypothesis_repair():
    with pytest.raises(ValueError):costs.diagnose_bytes(snapshot()[:-5])
