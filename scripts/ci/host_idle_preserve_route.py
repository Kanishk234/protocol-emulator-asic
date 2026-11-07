"""Pinned-native local guide patch; no maze rerouting or timing relaxation."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'scripts/ci'))
from openroad import Tech, Design
from route_segment_audit import parse, compare
from route_attachment_audit import atomic_routes
from route_reopen_libraries import select
from checked_openroad_tcl import checked
from local_c_select_repair import apply_plan, verify_after_router, canonical
from covered_clock_repair import DeferredClock
from local_route_patch import edge, patch, audit, pins

root=Path('runs/route-reopen-calibration');root.mkdir(exist_ok=True)
manifest=json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
source=Path(manifest['source_state']);state=json.loads(source.read_text())
odb_path=Path(state['odb'])
assert hashlib.sha256(odb_path.read_bytes()).hexdigest()==manifest['files'][str(odb_path.relative_to(Path.cwd()))]
settings=json.loads(Path('runs/stock-official-baseline/resolved.json').read_text())
mode=os.environ['LOCAL_PATCH_MODE'];assert mode in ('probe','repair')
edited=os.environ.get('LOCAL_ANTENNA_EDIT')=='true'
tech=Tech()
for lib in select(settings):tech.readLiberty(lib)
design=Design(tech);design.readDb(str(odb_path));db=tech.getDB();block=db.getChip().getBlock()
plan=json.loads(Path('spikes/phase2_stock_flow/host_idle_residual_plan.json').read_text())
assert plan['source_run']==manifest['run']['id']==42305323874
plan['diodes']=plan['diodes'][:6]
plan['allowed_signal_nets_to_reroute']=[d['net'] for d in plan['diodes']]
intervention=None
if mode=='probe':
    grid=block.getGCellGrid();assert grid is not None
    xs=list(grid.getGridX());ys=list(grid.getGridY())
    assert all(b-a==7200 for points in (xs,ys) for a,b in zip(points,points[1:]))
    records=[]
    for name in ('Metal2','Metal3','Metal4'):
        layer=db.getTech().findLayer(name);horizontal=str(layer.getDirection())=='HORIZONTAL'
        for x in range(len(xs)):
            for y in range(len(ys)):
                cap=int(grid.getCapacity(layer,x,y));used=int(grid.getUsage(layer,x,y))
                if (horizontal and x+1==len(xs)) or (not horizontal and y+1==len(ys)):
                    assert used<=cap
                    continue
                a=[xs[x]+3600,ys[y]+3600,layer.getRoutingLevel()]
                b=[a[0]+(7200 if horizontal else 0),a[1]+(0 if horizontal else 7200),a[2]]
                records.append([a,b,cap,used])
    assert sum(max(0,u-c) for a,b,c,u in records)==2
    (root/'probe_grid.json').write_text(json.dumps(records)+'\n')
elif edited:
    intervention=apply_plan(design,DeferredClock(plan['allowed_signal_nets_to_reroute']),db,plan)

router=design.getGlobalRouter()
layers={l.getName():l for l in db.getTech().getLayers()}
routing_layers=[l for l in layers.values() if l.getRoutingLevel()>=1]
router.setAdjustment(float(settings['GRT_ADJUSTMENT']))
for layer,adjustment in zip(routing_layers,settings['GRT_LAYER_ADJUSTMENTS']):
    router.addLayerAdjustment(layer.getRoutingLevel(),float(adjustment))
router.setMinLayerForClock(layers[settings.get('RT_CLOCK_MIN_LAYER') or settings['RT_MIN_LAYER']].getRoutingLevel())
router.setMaxLayerForClock(layers[settings.get('RT_CLOCK_MAX_LAYER') or settings['RT_MAX_LAYER']].getRoutingLevel())
router.setMacroExtension(settings['GRT_MACRO_EXTENSION'])
router.setCongestionIterations(settings['GRT_OVERFLOW_ITERS'])
router.setAllowCongestion(settings['GRT_ALLOW_CONGESTION']);router.setVerbose(True)
router.initFastRoute(layers[settings['RT_MIN_LAYER']].getRoutingLevel(),layers[settings['RT_MAX_LAYER']].getRoutingLevel())
if mode=='probe':
    router.loadGuidesFromDB();assert router.haveRoutes()
    router.writeSegments(str(root/'probe.segments'));router.writePinLocations(str(root/'probe_pins.txt'))
    assert len(parse((root/'probe.segments').read_text()))==45192
    sys.exit(0)

shutil.copyfile(root/'probe.segments',root/'before.segments')
original=atomic_routes(parse((root/'probe.segments').read_text()))
reference=json.loads(Path('spikes/phase2_stock_flow/host_idle_local_route_reference.json').read_text())
assert reference['source_run']==manifest['run']['id']
assert hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()==reference['original_atomic_sha256'], 'Frozen original route geometry mismatch'
def numeric(rows):
    return [edge((a[0],a[1],int(a[2][5:])),(b[0],b[1],int(b[2][5:]))) for a,b in rows]
def symbolic(rows):
    return [((a[0],a[1],'Metal'+str(a[2])),(b[0],b[1],'Metal'+str(b[2]))) for a,b in rows]
bycanonical={canonical(n):n for n in original};assert len(bycanonical)==len(original)
router.writePinLocations(str(root/'prepared_pins.txt'))
prepared=pins((root/'prepared_pins.txt').read_text())
ledger=[];changed={}
if edited:
    policy=json.loads(Path('spikes/phase2_stock_flow/host_idle_wide_detour_policy.json').read_text())
    assert policy['source_run']==manifest['run']['id']
    assert hashlib.sha256((root/'probe_grid.json').read_bytes()).hexdigest()==policy['probe_grid_sha256'], 'Native capacity snapshot changed'
    detours=policy['detours']
    attachments=[]
    source_pins=pins((root/'probe_pins.txt').read_text())
    antenna=json.loads(Path('spikes/phase2_stock_flow/host_idle_antenna_42305323874.json').read_text())['rows']
    for diode,row in zip(plan['diodes'],antenna):
        name=bycanonical[diode['net']];receiver=diode['anchor']+'/'+diode['pin']
        assert canonical(row['net'])==diode['net'] and row['pin'].split()[0]==receiver
        # Use the original native-covered access point for the unchanged
        # receiver. Initial pin projection can differ from loadGuides' covered
        # access-point selection even when physical placement is identical.
        assert receiver in prepared[name]
        attachments.append(dict(net=name,receiver=source_pins[name][receiver]+(1,),
                                diode=prepared[name][diode['name']+'/A']+(1,),
                                maximum_layer=int(row['layer'][5:])))
    assert json.loads(json.dumps(attachments))==policy['attachments'], 'Native pin attachments changed'
    plan['allowed_signal_nets_to_reroute'] += [canonical(d['net']) for d in detours]
    free={edge(a,b):c-u for a,b,c,u in json.loads((root/'probe_grid.json').read_text())}
    relevant={n:numeric(original[n]) for n in {x['net'] for x in detours+attachments}}
    (root/'planning_inputs.json').write_text(json.dumps(dict(routes=relevant,
        detours=detours,attachments=attachments,capacity_input='probe_grid.json'),indent=2)+'\n')
    changed,ledger,remaining=patch(relevant,free,detours,attachments)
    assert hashlib.sha256(json.dumps(ledger,sort_keys=True,separators=(',',':')).encode()).hexdigest()==policy['ledger_sha256'], 'Reviewed route ledger changed'
    (root/'local_patch_plan.json').write_text(json.dumps(dict(ledger=ledger,attachments=attachments,
        detours=detours,maximum_predicted_overflow=max(0,-min(remaining.values())),
        diagnostic_only=True),indent=2)+'\n')
    import odb
    for name,segments in changed.items():
        net=block.findNet(name)
        assert net is not None and not net.isSpecial() and str(net.getSigType())=='SIGNAL'
        assert not canonical(name).startswith(('clk','delaynet_')) and 'gclk' not in name
        for guide in list(net.getGuides()):odb.dbGuide.destroy(guide)
        for a,b in segments:
            lower=db.getTech().findRoutingLayer(min(a[2],b[2]));upper=db.getTech().findRoutingLayer(max(a[2],b[2]))
            rect=odb.Rect(min(a[0],b[0])-3600,min(a[1],b[1])-3600,max(a[0],b[0])+3600,max(a[1],b[1])+3600)
            assert odb.dbGuide.create(net,lower,upper,rect,False) is not None
router.loadGuidesFromDB();assert router.haveRoutes()
router.writeSegments(str(root/'loaded.segments'))
loaded=atomic_routes(parse((root/'loaded.segments').read_text()))
expected=dict(original);expected.update({n:symbolic(rows) for n,rows in changed.items()})
# Every unchanged original edge and each planned removal/addition must match.
assert {n:sorted(s) for n,s in loaded.items()}=={n:sorted(s) for n,s in expected.items()}
if edited:audit({n:numeric(original[n]) for n in changed},{n:numeric(loaded[n]) for n in changed},ledger)
router.startIncremental();router.endIncremental(True)
router.writeSegments(str(root/'after.segments'));router.writePinLocations(str(root/'pin_locations.txt'))
final=atomic_routes(parse((root/'after.segments').read_text()))
assert final==loaded, 'Native finish altered planned geometry'
result=compare((root/'before.segments').read_text(),(root/'after.segments').read_text(),
               allowed=tuple(changed))
if edited:
    verify_after_router(db,intervention);checked(design,'check_placement -verbose')
    intervention.update(added_diodes=6,post_router_placement_checked=True,
                        selected_actual_crossing_nets=[d['net'] for d in detours],
                        clock_net_changed=False,clock_timing_must_be_remeasured=True,
                        exact_original_edges_preserved_except_two_detours=True,
                        local_patch_ledger=ledger)
    (root/'intervention.json').write_text(json.dumps(intervention,indent=2)+'\n')
else:assert result['exact_roundtrip']
(root/'geometry_result.json').write_text(json.dumps(result,indent=2)+'\n')
design.writeDb(str(root/'calibrated.odb'));design.writeDef(str(root/'calibrated.def'))
state['odb']=str((root/'calibrated.odb').resolve());state['def']=str((root/'calibrated.def').resolve())
for key,suffix,opt in [('nl','nl.v',''),('pnl','pnl.v','-include_pwr_gnd ')]:
    p=(root/('calibrated.'+suffix)).resolve();checked(design,'write_verilog '+opt+'{'+str(p)+'}');assert p.is_file();state[key]=str(p)
state['metrics']={};(root/'state_out.json').write_text(json.dumps(state,indent=2)+'\n')
