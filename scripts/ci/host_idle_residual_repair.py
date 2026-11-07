"""Run under pinned OpenROAD Python; no-edit route reopening calibration."""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / 'scripts/ci'))
from openroad import Tech, Design
from route_segment_audit import compare, parse
from checked_openroad_tcl import checked

manifest = json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
source = Path(manifest['source_state'])
state = json.loads(source.read_text())
output = Path('runs/route-reopen-calibration')
output.mkdir(exist_ok=False)
config = Path('runs/stock-official-baseline/resolved.json')
settings = json.loads(config.read_text())
tech = Tech()
from route_reopen_libraries import select
liberties = select(settings)
for liberty in liberties:
    assert Path(liberty).is_file(), 'Missing pinned Liberty: ' + liberty
    tech.readLiberty(liberty)
design = Design(tech)
design.readDb(state['odb'])
edited = os.environ.get('LOCAL_ANTENNA_EDIT', 'false') == 'true'
router = design.getGlobalRouter()
# Initialize capacities first. Loading saved guides then restores their usage.
# Same routing setup as the pinned OdbReader, without importing its host packages.
layers = {layer.getName(): layer for layer in tech.getDB().getTech().getLayers()}
routing_layers = [layer for layer in layers.values() if layer.getRoutingLevel() >= 1]
router.setAdjustment(float(settings['GRT_ADJUSTMENT']))
for layer, adjustment in zip(routing_layers, settings['GRT_LAYER_ADJUSTMENTS']):
    router.addLayerAdjustment(layer.getRoutingLevel(), float(adjustment))
minimum = layers[settings['RT_MIN_LAYER']].getRoutingLevel()
maximum = layers[settings['RT_MAX_LAYER']].getRoutingLevel()
clock_min = settings.get('RT_CLOCK_MIN_LAYER') or settings['RT_MIN_LAYER']
clock_max = settings.get('RT_CLOCK_MAX_LAYER') or settings['RT_MAX_LAYER']
router.setMinLayerForClock(layers[clock_min].getRoutingLevel())
router.setMaxLayerForClock(layers[clock_max].getRoutingLevel())
router.setMacroExtension(settings['GRT_MACRO_EXTENSION'])
router.setCongestionIterations(settings['GRT_OVERFLOW_ITERS'])
router.setAllowCongestion(settings['GRT_ALLOW_CONGESTION'])
router.setVerbose(True)
router.initFastRoute(minimum, maximum)
router.loadGuidesFromDB()
assert router.haveRoutes(), 'Missing restored routes'
router.writeSegments(str(output / 'before.segments'))

from local_antenna_repair import snapshot
from local_c_select_repair import apply_plan, verify_after_router, canonical
from host_idle_residual_selection import select as choose
plan = json.loads(Path('spikes/phase2_stock_flow/host_idle_residual_plan.json').read_text())
reference = json.loads(Path('spikes/phase2_stock_flow/host_idle_residual_reference.json').read_text())
assert manifest['run']['id'] == plan['source_run'] == reference['source_run']
assert hashlib.sha256(Path(state['odb']).read_bytes()).hexdigest() == manifest['files'][str(Path(state['odb']).relative_to(Path.cwd()))]
routes = parse((output / 'before.segments').read_text())
assert len(routes) == reference['routed_nets'], 'Wrong restored route count'
block = tech.getDB().getChip().getBlock()
initial = snapshot(block)
eligible = {}
for net in block.getNets():
    name = net.getName()
    if str(net.getSigType()) != 'SIGNAL' or name not in routes or name not in plan['congestion_signal_nets']:
        continue
    terms = list(net.getITerms())
    if len(terms) < 2 or len(terms) > 16:
        continue
    # Preserve every physical clock net, including any signal-typed aliases.
    if name.startswith(('clk', 'delaynet_')) or 'gclk' in name:
        continue
    eligible[name] = len(terms)
selected = choose(routes, plan['residual_edges'], eligible)
assert set(selected) == set(plan['congestion_signal_nets']), 'Wrong congestion crossings'
(output / 'selected_plan.json').write_text(json.dumps(dict(plan=plan, actual_selected_crossings=selected), indent=2)+'\n')
router.startIncremental()
intervention = None
if edited:
    intervention = apply_plan(design, router, tech.getDB(), plan)
    for name in selected:
        net = block.findNet(name)
        assert str(net.getSigType()) == 'SIGNAL'
        router.addDirtyNet(net)
router.endIncremental(True)
router.writeSegments(str(output / 'after.segments'))
router.writePinLocations(str(output / 'pin_locations.txt'))
result = compare((output / 'before.segments').read_text(), (output / 'after.segments').read_text())
if edited:
    verify_after_router(tech.getDB(), intervention)
    checked(design, 'check_placement -verbose')
    allowed = set(plan['allowed_signal_nets_to_reroute'])
    assert all(canonical(n) in allowed for n in result['changed_nets']), 'Unrelated route changed'
    intervention.update(post_router_placement_checked=True, clock_net_changed=False,
                        clock_timing_must_be_remeasured=True,
                        selected_actual_crossing_nets=selected,
                        added_diodes=8)
    (output / 'intervention.json').write_text(json.dumps(intervention, indent=2)+'\n')
else:
    assert snapshot(block) == initial, 'Control cell inventory changed'
    assert result['exact_roundtrip'], 'Control routes changed'
(output / 'geometry_result.json').write_text(json.dumps(result, indent=2)+'\n')
# endIncremental calls native finishGlobalRouting, which refreshes database
# congestion from live usage, prints demand/overflow, and saves all guides.
design.writeDb(str(output / 'calibrated.odb'))
design.writeDef(str(output / 'calibrated.def'))
state['odb'] = str((output / 'calibrated.odb').resolve())
state['def'] = str((output / 'calibrated.def').resolve())
for key, suffix, option in [('nl', 'nl.v', ''), ('pnl', 'pnl.v', '-include_pwr_gnd ')]:
    path = (output / ('calibrated.' + suffix)).resolve()
    checked(design, 'write_verilog ' + option + '{' + str(path) + '}')
    assert path.is_file() and path.stat().st_size > 0
    state[key] = str(path)
state['metrics'] = {}
(output / 'state_out.json').write_text(json.dumps(state, indent=2) + '\n')
