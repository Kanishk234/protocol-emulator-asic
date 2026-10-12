"""Add one bounded non-reset buffer move to the measured133-overflow placement.

Replays exact26-move combined plan from authenticated original source, then
changes only fanout234 relative to that combined candidate. Native geometry,
connectivity and all six electrical guards precede any routing claim.
"""
import json
import cloud_reset_combined as combo

trial = combo.trial
trial.INPUT = trial.ROOT / 'build/fanout234_input'
trial.OUT = trial.ROOT / 'build/fanout234_placement'
trial.PLAN = dict(trial.PLAN, fanout234={
    'before': [57600,559440,59520,563220],
    'after': [56160,559440,58080,563220]})


def main():
    try:
        trial.main()
    finally:
        path = trial.OUT / 'result.json'
        if path.exists():
            result = json.loads(path.read_text())
            result['scope'] = 'Combined reset placement plus one existing fanout234 relocation'
            result['measured_control'] = {'producer_run':38167697696,
                'routing_run':38168159774, 'native_overflow':133,
                'additional_changed_instance':'fanout234'}
            result['proxy_tradeoff_um'] = {'aggregate_center_distance_improvement':2.88,
                'not_routed_wirelength':True,'routing_benefit_unproven':True}
            path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
