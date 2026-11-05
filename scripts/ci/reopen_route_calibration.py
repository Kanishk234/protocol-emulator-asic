"""Run under pinned OpenROAD Python; no-edit route reopening calibration."""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / 'scripts/ci'))
from openroad import Tech, Design
from route_segment_audit import compare, parse

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
for cell in ('sg13cmos5l_buf_2', 'sg13cmos5l_buf_4', 'sg13cmos5l_buf_8', 'sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2'):
    count = design.evalTclString('llength [get_lib_cells -quiet */' + cell + ']')
    assert int(count) > 0, 'Required Liberty cell missing: ' + cell
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
reference = json.loads(Path('spikes/phase2_stock_flow/route_reopen_reference.json').read_text())
canonical = json.dumps(parse((output / 'before.segments').read_text()), sort_keys=True, separators=(',', ':'))
assert hashlib.sha256(canonical.encode()).hexdigest() == reference['canonical_route_sha256'], 'Loaded geometry differs from frozen reference'
router.startIncremental()
edited = os.environ.get('LOCAL_ANTENNA_EDIT', 'false') == 'true'
intervention = None
if edited:
    from local_antenna_repair import apply
    intervention = apply(design, router, tech.getDB())
router.endIncremental(True)
router.writeSegments(str(output / 'after.segments'))
result = compare((output / 'before.segments').read_text(), (output / 'after.segments').read_text())
(output / 'geometry_result.json').write_text(json.dumps(result, indent=2) + '\n')
if edited:
    from local_antenna_repair import verify_after_router
    verify_after_router(tech.getDB(), intervention)
    def canonical_net(name):
        return name.replace('\\[', '[').replace('\\]', ']')
    allowed = set(intervention['allowed'])
    unexpected = [n for n in result['changed_nets'] if canonical_net(n) not in allowed]
    assert not unexpected, 'Unrelated route changed'
    result['unexpected_changed_nets'] = unexpected
    result['unchanged_routes_preserved'] = True
    (output / 'geometry_result.json').write_text(json.dumps(result, indent=2) + '\n')
    (output / 'intervention.json').write_text(json.dumps(intervention, indent=2) + '\n')
else:
    assert result['exact_roundtrip'], 'No-edit incremental operation changed routes'
design.writeDb(str(output / 'calibrated.odb'))
design.writeDef(str(output / 'calibrated.def'))
state['odb'] = str((output / 'calibrated.odb').resolve())
state['def'] = str((output / 'calibrated.def').resolve())
state['metrics'] = {}
(output / 'state_out.json').write_text(json.dumps(state, indent=2) + '\n')
