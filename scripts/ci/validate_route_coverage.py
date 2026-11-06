"""Independent pinned-native readSegments coverage/connectivity validation."""
import json
from pathlib import Path


def main():
    from openroad import Tech, Design
    from route_segment_audit import compare
    root = Path('runs/route-reopen-calibration')
    state = json.loads((root / 'state_out.json').read_text())
    tech = Tech()
    design = Design(tech)
    design.readDb(state['odb'])
    router = design.getGlobalRouter()
    settings = json.loads(Path('runs/stock-official-baseline/resolved.json').read_text())
    layers = {l.getName(): l for l in tech.getDB().getTech().getLayers()}
    routing_layers = [l for l in layers.values() if l.getRoutingLevel() >= 1]
    router.setAdjustment(float(settings['GRT_ADJUSTMENT']))
    for layer, adjustment in zip(routing_layers, settings['GRT_LAYER_ADJUSTMENTS']):
        router.addLayerAdjustment(layer.getRoutingLevel(), float(adjustment))
    router.setMinLayerForClock(layers[settings.get('RT_CLOCK_MIN_LAYER') or settings['RT_MIN_LAYER']].getRoutingLevel())
    router.setMaxLayerForClock(layers[settings.get('RT_CLOCK_MAX_LAYER') or settings['RT_MAX_LAYER']].getRoutingLevel())
    router.setMacroExtension(settings['GRT_MACRO_EXTENSION'])
    router.initFastRoute(layers[settings['RT_MIN_LAYER']].getRoutingLevel(),
                         layers[settings['RT_MAX_LAYER']].getRoutingLevel())
    # readSegments initializes the grid/pins and checks every routed net for
    # connected segments and coverage at its actual native connection layer.
    # Its initGridAndNets clears routes before reading. Do not call haveRoutes:
    # that API itself imports database guides as a side effect.
    router.readSegments(str(root / 'after.segments'))
    router.writeSegments(str(root / 'coverage-readback.segments'))
    result = compare((root / 'after.segments').read_text(),
                     (root / 'coverage-readback.segments').read_text())
    assert result['exact_roundtrip'], 'Coverage readback changed exported routes'
    (root / 'native_coverage.json').write_text(json.dumps(dict(
        all_routed_nets_connected_and_pins_covered=True,
        routed_nets=result['new_routed_nets'], independent_process=True,
        exact_route_roundtrip=True, official_flow_qualified=False), indent=2) + '\n')


if __name__ == '__main__':
    main()
