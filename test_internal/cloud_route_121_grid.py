"""Read-only native congestion grid on the authenticated15-budget121 checkpoint."""
import json
import os
from pathlib import Path
import sys

import cloud_route_trace as trace
from audit_native_grid import audit

PATCH=trace.ROOT/'patches/grt_grid_observer.tcl'
EXPECTED_SEGMENTS='19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c'


def observed_trace(original,patch):
    start='set warp_grid [[ord::get_db_block] getGCellGrid]'
    stop='close $warp_grid_file'
    if patch.count(start)!=1 or patch.count(stop)!=1:
        raise ValueError('Nonunique calibrated grid export body')
    body=patch[patch.index(start):patch.index(stop)+len(stop)]+'\n'
    anchor='    write_global_route_segments $::env(STEP_DIR)/native-segments.txt\n'
    if original.count(anchor)!=1 or 'global_route' in body or 'return ' in body:
        raise ValueError('Grid observation body or anchor differs')
    changed=original.replace(anchor,anchor+body)
    if changed.replace(body,'',1)!=original:
        raise ValueError('Grid observer changes more than observation')
    return changed


def main():
    trace.OUT=trace.ROOT/'build/route_121_grid'
    trace.main(15,worker=__file__)
    output=trace.OUT/'result.json'
    result=json.loads(output.read_text())
    try:
        if result['native_congestion'][-1]['total_overflow']!=121 or result['segments_sha256']!=EXPECTED_SEGMENTS:
            raise ValueError('Read-only observer no longer reproduces121 route')
        stage,=(trace.OUT/'replay').glob('*-openroad-globalrouting')
        grid=audit(stage/'native-grid.tsv')
        for row in result['native_congestion'][:-1]:
            if grid['layers'][row['layer']]['overflow']!=row['total_overflow']:
                raise ValueError('Calibrated grid and native overflow disagree')
        result.update(native_grid=grid,grid_observer_completed=True,
                      checkpoint_segments_exact=True,checkpoint_overflow=121,
                      grid_patch_sha256=trace.cfg.sha(PATCH),observer_sha256=trace.cfg.sha(Path(__file__)),
                      source_revision=os.environ.get('GITHUB_SHA'),workflow_run=os.environ.get('GITHUB_RUN_ID'))
    except Exception as exc:
        result.update(grid_observer_completed=False,error=str(exc))
        raise
    finally:
        output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--inside':
        trace.TRACE=observed_trace(trace.TRACE,PATCH.read_text())
        trace.reports.instrument=trace.instrument
        trace.reports.inside(*(Path(p) for p in sys.argv[2:]))
    elif len(sys.argv)==1:
        main()
    else:
        raise SystemExit('Unsupported observer invocation')
