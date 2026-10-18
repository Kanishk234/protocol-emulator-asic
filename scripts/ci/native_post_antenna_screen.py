"""Clean native build followed by post-timing antenna repair and fresh gates."""
from native_antenna_margin_screen import configure as antenna_configure
from native_margin_screen import main

SUBSTITUTIONS = {'+OpenROAD.ResizerTimingPostGRT': 'OpenROAD.RepairAntennas'}

def configure(config):
    result = antenna_configure(config)
    result['meta'] = dict(result['meta'], substituting_steps=dict(SUBSTITUTIONS))
    return result


if __name__ == '__main__':
    main(config_transform=configure, final_antenna_repair=True)
