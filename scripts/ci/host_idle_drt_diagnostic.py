"""Bounded DRC evidence capture; never a routing/signoff qualification."""
from copy import deepcopy


def configure(config):
    if config.get('CLOCK_PERIOD')!=20:
        raise ValueError('Expected unchanged 20 ns source')
    result=deepcopy(config)
    result.update(OPENROAD_THREADS=4,DRT_OPT_ITERS=42,
                  DRT_SAVE_DRC_REPORT_ITERS=1,DRT_SAVE_SNAPSHOTS=False,
                  DRT_ANTENNA_REPAIR_ITERS=0)
    return result
