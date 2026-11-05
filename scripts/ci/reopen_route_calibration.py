"""Run under pinned OpenROAD Python; no-edit route reopening calibration."""
import hashlib
import json
import os
from pathlib import Path
import sys
import librelane
sys.path.insert(0, str(Path(librelane.__file__).parent / 'scripts/odbpy'))
sys.path.insert(0, str(Path.cwd() / 'scripts/ci'))
from reader import OdbReader
from route_segment_audit import compare, parse

manifest = json.loads(Path(os.environ['SOURCE_MANIFEST']).read_text())
source = Path(manifest['source_state'])
state = json.loads(source.read_text())
output = Path('runs/route-reopen-calibration')
output.mkdir(exist_ok=False)
config = Path('runs/stock-official-baseline/resolved.json')
reader = OdbReader(state['odb'], config_path=str(config))
router = reader.design.getGlobalRouter()
# Initialize capacities first. Loading saved guides then restores their usage.
reader._grt_setup(router)
router.loadGuidesFromDB()
assert router.haveRoutes(), 'Missing restored routes'
router.writeSegments(str(output / 'before.segments'))
reference = json.loads(Path('spikes/phase2_stock_flow/route_reopen_reference.json').read_text())
canonical = json.dumps(parse((output / 'before.segments').read_text()), sort_keys=True, separators=(',', ':'))
assert hashlib.sha256(canonical.encode()).hexdigest() == reference['canonical_route_sha256'], 'Loaded geometry differs from frozen reference'
router.startIncremental()
router.endIncremental(True)
router.writeSegments(str(output / 'after.segments'))
result = compare((output / 'before.segments').read_text(), (output / 'after.segments').read_text())
(output / 'geometry_result.json').write_text(json.dumps(result, indent=2) + '\n')
assert result['exact_roundtrip'], 'No-edit incremental operation changed routes'
reader.design.writeDb(str(output / 'calibrated.odb'))
reader.design.writeDef(str(output / 'calibrated.def'))
state['odb'] = str((output / 'calibrated.odb').resolve())
state['def'] = str((output / 'calibrated.def').resolve())
state['metrics'] = {}
(output / 'state_out.json').write_text(json.dumps(state, indent=2) + '\n')
