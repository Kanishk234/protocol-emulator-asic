import copy
import json
from pathlib import Path
import pytest
import sram_bank_clean_route as runner
from postgrt_timing import CORNERS


def source():
    return (dict(id=runner.SOURCE_RUN, head_sha=runner.SOURCE_SHA, head_branch='main',
        conclusion='success', path='.github/workflows/gds-sram-bank-clean-screen.yaml'),
        dict(source_run=38172640071, clean_from_rtl=True, stock_classic=True,
             custom_image=False, added_cells_by_policy=0, relocated_instances=16,
             qualified=True, minimum_fast_hold_ns=.05, physical_screen_only=True, official_signoff=False))


def test_exact_provenance(): runner.validate_provenance(*source())


@pytest.mark.parametrize('part,key,value', [(0,'id',1),(0,'head_sha','wrong'),
    (0,'head_branch','other'),(0,'conclusion','failure'),(0,'path','wrong'),
    (1,'source_run',1),(1,'clean_from_rtl',False),(1,'stock_classic',False),
    (1,'custom_image',True),(1,'added_cells_by_policy',1),(1,'relocated_instances',14),
    (1,'qualified',False),(1,'minimum_fast_hold_ns',.01),(1,'physical_screen_only',False)])
def test_wrong_source_or_gate_rejected(part,key,value):
    args = list(source()); args[part][key] = value
    with pytest.raises(ValueError): runner.validate_provenance(*args)


def test_workflow_downloads_exact_qualified_screen():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-sram-bank-clean-route.yaml').read_text())
    d = next(s for s in w['jobs']['harden']['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id'] == runner.SOURCE_RUN
    assert d['with']['name'] == 'gds-sram-bank-clean-38184574265'


@pytest.mark.parametrize('cleanup', [False,True])
@pytest.mark.parametrize('fault', [None,'placement','topology','overflow','hold','antenna','missing','rewire'])
def test_complete_clean_history_and_checkpoint_required(tmp_path, monkeypatch, cleanup, fault):
    monkeypatch.chdir(tmp_path)
    def write(path, text): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
    root = Path('runs/sram-bank-clean-screen'); flow = root/'flow'
    nl = 'sg13cmos5l_buf_4 buf (.A(a), .X(x));'
    reference = Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v')
    write(reference,nl)
    write(flow/'32-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v',nl+' changed' if fault == 'topology' else nl)
    if fault == 'topology':
        write(flow/'32-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v', nl.replace('.A(a)', '.A(other)'))
    proposal = {'proposals':[dict(instance='buf', new_location=[100,200,'N'])]}
    layout = '- buf sg13cmos5l_buf_4 + PLACED ( 100 200 ) N ;'
    write(flow/'33-odb-manualglobalplacement/tt_um_tripwire.def',layout)
    write(flow/'34-openroad-detailedplacement/tt_um_tripwire.def',layout.replace('100 200','200 200') if fault == 'placement' else layout)
    log = 'Final congestion report:\n'+''.join(f'Metal{i} 100 100 0.0% 0 / 0 / 0\n' for i in range(1,5))
    write(flow/'40-openroad-globalrouting/openroad-globalrouting.log', log.replace('0 / 0 / 0','1 / 0 / 0') if fault == 'overflow' else log)
    initial = flow/'43-openroad-resizertimingpostgrt/state_out.json'
    views = {}
    for key in ('odb','def','nl','pnl','sdc'):
        p = initial.parent/('chip.'+key); write(p,nl); views[key] = str(p.resolve())
    write(initial,json.dumps(views))
    source_state = initial
    if cleanup:
        base = root/'antenna-cleanup'
        write(base/'resolved.json',json.dumps({'GRT_ALLOW_CONGESTION':False}))
        write(base/'1-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log','repair_antennas')
        source_state = base/'2-openroad-checkantennas/state_out.json'
        after = dict(views)
        path = source_state.parent/'fresh.nl.v'
        write(path,nl.replace('.A(a)', '.A(other)') if fault == 'rewire' else nl+'\nsg13cmos5l_antennanp ant (.A(x));')
        after['nl'] = str(path.resolve()); write(source_state,json.dumps(after))
    if fault == 'rewire' and not cleanup:
        write(source_state,json.dumps(dict(views,nl='/missing')))
    metrics_path = source_state.parent/'or_metrics_out.json' if cleanup else root/'antenna/1-openroad-checkantennas/or_metrics_out.json'
    write(metrics_path,json.dumps({'antenna__violating__nets':1 if fault == 'antenna' else 0,'antenna__violating__pins':0}))
    timing = {'after_state':str(source_state.resolve()),'corners':{c:{'after':{
        f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.049 if fault == 'hold' else .08}} for c in CORNERS}}
    write(root/'timing/comparison.json',json.dumps(timing))
    if fault == 'missing': Path(views['odb']).unlink()
    if fault:
        with pytest.raises((ValueError,FileNotFoundError)): runner.validate_checkpoint(root,proposal)
    else:
        assert runner.validate_checkpoint(root,proposal).resolve() == source_state.resolve()


@pytest.mark.parametrize('timing_ok', [False,True])
@pytest.mark.parametrize('antenna_ok', [False,True])
def test_drt_and_extraction_require_fresh_gates(tmp_path, monkeypatch, timing_ok, antenna_ok):
    import sys,types
    monkeypatch.chdir(tmp_path); monkeypatch.setenv('PDK_ROOT','/pdk')
    monkeypatch.setenv('LIBRELANE_IMAGE_OVERRIDE','unreviewed')
    Path('src').mkdir(); Path('runs').mkdir()
    source_state = Path('source.json'); calls = []; extracted = []
    original = Path('source.v'); original.write_text('sg13cmos5l_buf_4 original (.A(a), .X(x));')
    source_state.write_text(json.dumps({'nl':str(original)}))
    def step(config, initial, output, steps):
        assert initial == source_state and 'LIBRELANE_IMAGE_OVERRIDE' not in runner.os.environ
        calls.append(steps)
        if steps == ['OpenROAD.CheckAntennas']:
            p = output/'1-openroad-checkantennas/or_metrics_out.json'; p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'antenna__violating__nets':0 if antenna_ok else 1,'antenna__violating__pins':0}))
        if steps == ['OpenROAD.DetailedRouting']:
            p = output/'1-openroad-detailedrouting/state_out.json'; p.parent.mkdir(parents=True)
            nl = p.parent/'fresh.v'; nl.write_text(original.read_text()+'\nsg13cmos5l_antennanp newdiode (.A(x));')
            p.write_text(json.dumps({'nl':str(nl)}))
    def sta(path, initial, output, pdk, repaired, sdc):
        assert initial == repaired == source_state
        output.mkdir(parents=True); (output/'comparison.json').write_text(json.dumps({'corners':{c:{'after':{
            f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.06 if timing_ok else .049}} for c in CORNERS}}))
    monkeypatch.setattr(runner,'run_step',step); monkeypatch.setattr(runner,'screen',sta)
    monkeypatch.setitem(sys.modules,'extracted_timing',types.SimpleNamespace(main=lambda p:extracted.append(p)))
    output = Path('runs/newroute')
    if timing_ok and antenna_ok:
        runner.continue_route({},source_state,output)
        assert calls == [['OpenROAD.CheckAntennas'],['OpenROAD.DetailedRouting']]
        assert extracted == [output/'drt']
    else:
        with pytest.raises(ValueError): runner.continue_route({},source_state,output)
        assert calls == [['OpenROAD.CheckAntennas']] and not extracted


def test_fresh_drt_export_catches_hidden_changes_after_stale_antenna_nl(tmp_path):
    before = tmp_path/'before.v'; before.write_text('sg13cmos5l_buf_4 original (.A(a), .X(x));')
    source_state = tmp_path/'source.json'; source_state.write_text(json.dumps({'nl':str(before)}))
    drt = tmp_path/'drt'; stage = drt/'1-openroad-detailedrouting'; stage.mkdir(parents=True)
    final = stage/'final.v'; final.write_text(before.read_text().replace('.A(a)', '.A(other)'))
    (stage/'state_out.json').write_text(json.dumps({'nl':str(final)}))
    with pytest.raises(ValueError): runner.validate_final_route(source_state,drt)
