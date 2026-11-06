import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from validate_route_coverage import main


@pytest.mark.parametrize('fault', [None, 'coverage', 'geometry'])
def test_native_coverage_must_succeed_before_receipt(tmp_path, monkeypatch, fault):
    monkeypatch.chdir(tmp_path)
    root = Path('runs/route-reopen-calibration')
    root.mkdir(parents=True)
    (root / 'state_out.json').write_text(json.dumps({'odb': 'candidate.odb'}))
    segments = 'clock\n(\n0 0 Metal1 0 0 Metal3\n0 0 Metal3 10 0 Metal3\n)\n'
    (root / 'after.segments').write_text(segments)
    config = Path('runs/stock-official-baseline/resolved.json')
    config.parent.mkdir()
    config.write_text(json.dumps(dict(GRT_ADJUSTMENT=.3, GRT_LAYER_ADJUSTMENTS=[0, .3, .3, .3],
                                     RT_MIN_LAYER='Metal2', RT_MAX_LAYER='Metal4',
                                     GRT_MACRO_EXTENSION=2)))
    calls = []
    class Layer:
        def __init__(self, level):
            self.level = level
        def getName(self):
            return 'Metal' + str(self.level)
        def getRoutingLevel(self):
            return self.level
    class Tech:
        def getDB(self):
            return SimpleNamespace(getTech=lambda: SimpleNamespace(getLayers=lambda: [Layer(i) for i in range(1, 5)]))
    class Router:
        def __getattr__(self, name):
            if name.startswith('set') or name in ('addLayerAdjustment', 'initFastRoute'):
                return lambda *args: calls.append((name, args))
            raise AssertionError('Unreviewed native method: ' + name)
        def readSegments(self, path):
            calls.append(('readSegments', path))
            if fault == 'coverage':
                raise RuntimeError('Pin not covered')
        def writeSegments(self, path):
            Path(path).write_text(segments.replace('10 0', '20 0') if fault == 'geometry' else segments)
    class Design:
        def __init__(self, tech):
            pass
        def readDb(self, path):
            assert path == 'candidate.odb'
        def getGlobalRouter(self):
            return Router()
    monkeypatch.setitem(sys.modules, 'openroad', SimpleNamespace(Tech=Tech, Design=Design))
    if fault:
        with pytest.raises((AssertionError, RuntimeError)):
            main()
        assert not (root / 'native_coverage.json').exists()
    else:
        main()
        assert json.loads((root / 'native_coverage.json').read_text())['routed_nets'] == 1
        assert ('initFastRoute', (2, 4)) in calls
