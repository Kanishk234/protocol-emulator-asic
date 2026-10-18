"""Bound native buffer-chain cost and add hold reserve after paired routed evidence."""
from pathlib import Path
from native_post_antenna_screen import configure as antenna_configure
from native_margin_screen import main


def configure(config):
    result = antenna_configure(config)
    if (result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] != 100
            or result['GRT_RESIZER_HOLD_SLACK_MARGIN'] != .10):
        raise ValueError('Unexpected native antenna source policy')
    result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 150
    result['GRT_RESIZER_HOLD_SLACK_MARGIN'] = .125
    return result


if __name__ == '__main__':
    main(config_transform=configure, final_antenna_repair=True,
         audit_tcl=Path('workflow-src/scripts/ci/native_timing_headroom_audit.tcl'))
