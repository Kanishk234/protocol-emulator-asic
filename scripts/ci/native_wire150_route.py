"""Route the reviewed wire150/hold125 clean screen, repeating no repairs."""
import argparse
from native_post_antenna_route import main, prepare
from native_wire150_screen import configure

PROFILE = dict(source_run=39177724036,
    source_sha='e7117101dd77e87cc7c1099c156b77c89e9cc54e',
    source_workflow='.github/workflows/gds-native-wire150-hold125-screen.yaml',
    hold_target_ns=.125, output='runs/native-wire150-hold125-route')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    prepare(config_transform=configure) if args.prepare else main(profile=PROFILE)
