"""D097: paired native50/15 iterations on the same authenticated physical views."""
import json
import os
from pathlib import Path

import cloud_route_trace as trace


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Paired native experiment is hosted only')
    output=trace.ROOT/'build/route_early_stop'
    output.mkdir(exist_ok=False)
    result={'diagnostic_completed':False,'physical_acceptance':False,
            'configured_timing_acceptance':False,'cases':{}}
    try:
        for name,budget in (('control',50),('early_stop',15)):
            trace.OUT=output/name
            trace.main(budget)
            observed=json.loads((trace.OUT/'result.json').read_text())
            if observed.get('source_unchanged') is not True or observed.get('diagnostic_completed') is not True:
                raise ValueError('Incomplete native case')
            result['cases'][name]=observed
        control=result['cases']['control']['native_congestion'][-1]['total_overflow']
        candidate=result['cases']['early_stop']['native_congestion'][-1]['total_overflow']
        result.update(control_overflow=control,candidate_overflow=candidate,
                      improves_control=candidate<control,diagnostic_completed=True)
    except Exception as exc:
        result['error']=str(exc)
        raise
    finally:
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
