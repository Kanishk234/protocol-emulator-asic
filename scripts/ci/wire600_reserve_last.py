"""Add one BUF4 for the sole reserve miss measured in run39700222717."""
from functools import partial
import json
from pathlib import Path

import wire600_reserve_finish as base
from wire600_selective_screen import main as screen

REVIEW = json.loads((Path(__file__).parent/'fixtures/wire600_selective/reserve_last.json').read_text())
plan = partial(base.plan, review=REVIEW)
target_call = partial(base.target_call, review=REVIEW)
validate_change = partial(base.validate_change, review=REVIEW)


def main():
    screen(plan_builder=plan, target_emitter=target_call, connectivity_audit=validate_change,
           output=Path('runs/wire600-reserve-last-screen'))


if __name__ == '__main__':
    main()
