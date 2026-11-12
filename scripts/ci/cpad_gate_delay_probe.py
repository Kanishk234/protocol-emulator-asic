"""Bounded gate/delay sensitivity across five failing endpoints; no physical repair."""
import cpad_sizing_probe as probe
from cpad_frontier_sizing import TARGETS as GATES

HOLDS = ('hold10203', 'hold10204', 'hold10318', 'hold10319', 'hold10394', 'hold10395', 'hold10554', 'hold10767', 'hold10768', 'hold9183', 'hold9184', 'hold9185')


def main():
    targets = {**GATES, **{n: ('sg13cmos5l_dlygate4sd3_1', 'sg13cmos5l_dlygate4sd2_1') for n in HOLDS}}
    gate_changes = {n: pair[1] for n, pair in GATES.items()}
    probe.TARGETS = targets
    original_change = probe.change_netlist
    def guarded_change(text, changes):
        selected = dict(targets)
        for name, master in changes.items():
            if name in HOLDS:
                assert master in ('sg13cmos5l_dlygate4sd2_1', 'sg13cmos5l_dlygate4sd1_1')
                selected[name] = (targets[name][0], master)
            else:
                assert name in GATES and master == GATES[name][1]
        probe.TARGETS = selected
        try:
            return original_change(text, changes)
        finally:
            probe.TARGETS = targets
    probe.change_netlist = guarded_change
    probe.CASES = {'baseline': {}, 'gates12': gate_changes,
        **{f'gates12_delay{d}': {**gate_changes,
            **{n: f'sg13cmos5l_dlygate4sd{d}_1' for n in HOLDS}} for d in (2,1)}}
    probe.main()


if __name__ == '__main__':
    main()
