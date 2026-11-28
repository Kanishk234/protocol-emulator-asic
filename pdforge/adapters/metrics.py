"""Conservative LibreLane metric ingestion: preserve stage/corner and source keys."""
import json
from pathlib import Path
from pdforge.core.evidence import sha, finite

MAPPING = {
 'timing__setup__ws': ('setup','ns'), 'timing__hold__ws': ('hold','ns'),
 'route__overflow': ('congestion','count'), 'route__drc_errors': ('drc','count'),
 'design__max_slew_violation__count': ('electrical','count'),
 'design__max_cap_violation__count': ('electrical','count'),
 'design__max_fanout_violation__count': ('electrical','count'),
 'antenna__violating__nets': ('antenna','count'),
 'design__instance__area': ('area','um2'), 'design__instance__utilization': ('utilization','ratio'),
 'design__lvs_error__count': ('lvs','count'), 'ir__drop__worst': ('pdn','V'),
 'clock__skew': ('cts','ns'), 'design__instance__unplaced__count': ('placement','count')}

def ingest_metrics(path, stage):
    path = Path(path)
    text = path.read_text()
    data = json.loads(text)
    result, unknown = [], []
    for key, value in data.items():
        base = key.split('__corner:')[0]
        if base not in MAPPING:
            unknown.append(key)
            continue
        category, unit = MAPPING[base]
        if value is None: continue
        finite(value)
        result.append({'key':key,'category':category,'value':value,'unit':unit,'stage':stage,
                       'corner':key.split('__corner:')[1] if '__corner:' in key else None,
                       'evidence':{'path':str(path.resolve()),'sha256':sha(path),
                                   'line':next((i for i,l in enumerate(text.splitlines(),1) if json.dumps(key) in l),1)}})
    return {'observations':result,'unmapped_keys':unknown,'missing_categories':sorted(set(MAPPING[k][0] for k in MAPPING)-{r['category'] for r in result}),
            'official_signoff':False}
