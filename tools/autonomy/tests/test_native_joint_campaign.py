import json
import pytest
from autonomy import native_joint_campaign as campaign
from autonomy.tests.test_capacity_cut import aggregate_graph


@pytest.fixture
def setup(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(campaign.fixed,'load_inputs',lambda *a,**k:(calls.append('authenticate') or ({'result_sha256':'a'*64},'raw','term','segments')))
    monkeypatch.setattr(campaign.coarse_global,'build',lambda *a,**k:(calls.append('seed') or {'graph':aggregate_graph()}))
    monkeypatch.setattr(campaign.capacity_cut,'discover_partition_certificate',lambda g:campaign.capacity_cut.certify_partition(g,side_nodes=['left']))
    def refine(*a,**kw):
        calls.append('refine')
        assert kw['max_additional']==5 and kw['max_rounds']==4 and kw['max_variables']==150000
        assert kw['records'][0]['certificate']['independently_verified_graph_infeasible']
        return dict(diagnostic_completed=True,termination='round_limit',history=[{}])
    monkeypatch.setattr(campaign.cut_refinement,'run',refine)
    return dict(revision='b'*40,run_id='123',attempt=1,output=tmp_path/'out'),calls


def test_native_joint_campaign_authenticates_before_bounded_loop_and_retains_scope(setup):
    kw,calls=setup;r=campaign.run('bundle',{},**kw)
    assert calls==['authenticate','seed','refine']
    assert r['diagnostic_completed'] and r['termination']=='round_limit'
    assert not r['native_route_installed'] and not r['physical_acceptance']
    assert json.loads((kw['output']/'summary.json').read_text())==r


def test_native_joint_auth_failure_prevents_models_outputs_and_solves(setup,monkeypatch):
    kw,calls=setup
    def fail(*a,**k):raise ValueError('Bad native controls')
    monkeypatch.setattr(campaign.fixed,'load_inputs',fail)
    with pytest.raises(ValueError):campaign.run('bundle',{},**kw)
    assert not calls and not kw['output'].exists()


def test_native_joint_seed_deficit_must_reproduce(setup,monkeypatch):
    kw,calls=setup;monkeypatch.setattr(campaign.capacity_cut,'discover_partition_certificate',lambda *a:None)
    with pytest.raises(ValueError,match='not reproduced'):campaign.run('bundle',{},**kw)
    assert calls==['authenticate','seed'] and not kw['output'].exists()


def test_native_joint_failure_retains_audit_and_explicit_failed_summary(setup,monkeypatch):
    kw,_=setup
    monkeypatch.setattr(campaign.cut_refinement,'run',lambda *a,**k:dict(diagnostic_completed=False,termination='error',history=[{}],error='fixture failure'))
    with pytest.raises(RuntimeError):campaign.run('bundle',{},**kw)
    assert (kw['output']/'input-audit.json').exists()
    assert not json.loads((kw['output']/'summary.json').read_text())['diagnostic_completed']


def test_native_joint_existing_result_is_preserved(setup):
    kw,_=setup;kw['output'].mkdir();(kw['output']/'good').write_text('keep')
    with pytest.raises(FileExistsError):campaign.run('bundle',{},**kw)
    assert (kw['output']/'good').read_text()=='keep'


def test_seed_constraints_roundtrip_rebuilds_models_and_proofs():
    from autonomy.tests.test_cut_cohort_native import inputs
    s,t,record=inputs();encoded=campaign.encode_seeds(s,t,[record])
    assert campaign.decode_seeds(s,t,encoded)==[record]


def pack(payload):
    import base64,zlib
    return base64.b64encode(zlib.compress(json.dumps(payload).encode())).decode()


@pytest.mark.parametrize('change',[
    {'raw_sha256':'different'},{'schema_version':True},{'extra':'not allowed'},{'cuts':[]},
])
def test_seed_schema_or_checkpoint_tamper_rejected(change):
    from autonomy.tests.test_cut_cohort_native import inputs
    s,t,record=inputs()
    payload=dict(schema_version=1,raw_sha256=s.sha256,terminal_sha256=t.sha256,
        cuts=[dict(slots=record['model']['provenance']['slots'],side_nodes=record['certificate']['side_nodes'])])
    payload.update(change)
    with pytest.raises(ValueError):campaign.decode_seeds(s,t,pack(payload))


def test_seed_deficit_is_recomputed_instead_of_importing_status():
    from autonomy.tests.test_corridor_extract import fixture
    from autonomy import coarse_global,capacity_cut
    s,t,_=fixture();model=coarse_global.build(s,t,slots=[0]);certificate=capacity_cut.certify_partition(model['graph'],side_nodes=['p0_0'])
    assert not certificate['independently_verified_graph_infeasible']
    encoded=campaign.encode_seeds(s,t,[dict(model=model,certificate=certificate)])
    with pytest.raises(ValueError,match='not a certified'):campaign.decode_seeds(s,t,encoded)


@pytest.mark.parametrize('encoded',['not base64!', '', 'eA=='])
def test_malformed_or_incomplete_seed_archive_rejected(encoded):
    with pytest.raises((ValueError,campaign.zlib.error)):campaign.decode_seeds(None,None,encoded)


def test_seed_decompression_is_bounded_and_trailing_archive_rejected(monkeypatch):
    import base64,zlib
    monkeypatch.setattr(campaign,'MAX_SEED_BYTES',16)
    oversized=base64.b64encode(zlib.compress(b'x'*1000)).decode()
    with pytest.raises(ValueError,match='oversized'):campaign.decode_seeds(None,None,oversized)
    trailing=base64.b64encode(zlib.compress(b'{}')+b'extra').decode()
    with pytest.raises(ValueError):campaign.decode_seeds(None,None,trailing)


def test_resume_seed_import_occurs_after_native_authentication(setup,monkeypatch):
    kw,calls=setup;seen=[]
    monkeypatch.setattr(campaign,'decode_seeds',lambda s,t,text:(seen.append(list(calls)) or [dict(model={},certificate={'independently_verified_graph_infeasible':True})]))
    campaign.run('bundle',{},seed_manifest='fixture',**kw)
    assert seen==[['authenticate','seed']]
