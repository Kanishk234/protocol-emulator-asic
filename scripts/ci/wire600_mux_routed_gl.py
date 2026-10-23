"""Exact final-route protocol replay, gated by independently audited extraction."""
import hashlib
import json
from pathlib import Path

from electrical_report import audit_corners
from event_nor2_screen import logical_cells
from native_route_gl import validate_electrical
from native_stock_route import qualified
from postgrt_timing import CORNERS
from sram_bank_clean_route import unique

PROFILE = json.loads((Path(__file__).parent/'fixtures/wire600_selective/mux_routed_gl.json').read_text())


def validate(root, run):
    root=Path(root)
    for name,sha in PROFILE['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('Changed final routed evidence: '+name)
    result=validate_electrical(root,run,PROFILE['netlist_sha256'],profile=PROFILE)
    extracted=root/'runs/extracted-timing'
    summary=json.loads((extracted/'corner_summary.json').read_text())
    sta=unique(extracted,'*-openroad-stapostpnr/state_out.json').parent
    measured=audit_corners(sta,CORNERS)
    if measured!=json.loads((extracted/'electrical_summary.json').read_text()):
        raise ValueError('Extracted electrical summary differs from reports')
    if not all(row['no_reported_electrical_violations'] for row in measured.values()):
        raise ValueError('Final extracted electrical reports fail')
    metrics=json.loads((sta/'state_out.json').read_text())['metrics']
    if any(metrics.get(k)!=v for k,v in summary.items()):
        raise ValueError('Extracted timing summary differs from fresh state')
    antenna=json.loads(unique(extracted,'*-openroad-checkantennas/or_metrics_out.json').read_text())
    if not qualified({'corners':{c:{'after':summary} for c in CORNERS}},antenna):
        raise ValueError('Final extracted timing/antenna gates fail')
    final=extracted/'08-openroad-fillinsertion/tt_um_tripwire.nl.v'
    if logical_cells(Path(result['netlist']).read_text())!=logical_cells(final.read_text()):
        raise ValueError('Extraction netlist differs logically from final route')
    return dict(result,extracted_gates_independently_audited=True)
