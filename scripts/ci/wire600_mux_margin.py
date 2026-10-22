"""One strength change on both remaining extracted setup-violating paths."""
from functools import partial
import json
from pathlib import Path

import wire600_reserve_finish as base
from wire600_clean_reproduction import main as screen

REVIEW = json.loads((Path(__file__).parent/'fixtures/wire600_selective/mux_margin.json').read_text())
plan = partial(base.plan,review=REVIEW)
target_call = partial(base.target_call,review=REVIEW)
validate_change = partial(base.validate_change,review=REVIEW)


def main():
    screen(plan_builder=plan,target_emitter=target_call,connectivity_audit=validate_change,
           output=Path('runs/wire600-mux-margin-clean'))


if __name__ == '__main__':
    main()
