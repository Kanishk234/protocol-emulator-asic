"""Read-only diagnosis of the failed lane-mask candidate, never route authority."""
from native_stage_probe import HASHES, main as probe

PROFILE = dict(
    source_run=39498376778,
    source_sha='f365a50a3208c8a36a051c73efc13ab0acd39a16',
    source_workflow='.github/workflows/gds-native-lane-mask-setup-reserve-screen.yaml',
    hashes={**HASHES,
            'trw_chan_port.v': '1ffd8c8004d86ec93c7da8e2967650861e6f5d67b8e44e83bc977649298508ba',
            'trw_lane.v': '5a2905a6c59ac4eb6efb621e95d5bd18d1b9f2dc1ad599f5c7690573760ffd06'},
    nets=('_10742_', '_20400_'),
    audit_tcl='workflow-src/scripts/ci/native_lane_mask_stage_probe.tcl',
    output='runs/native-lane-mask-stage-probe',
)


if __name__ == '__main__':
    probe(PROFILE)
