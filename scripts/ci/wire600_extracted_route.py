"""Route the clean 81-buffer/13-size profile without repeating its repairs."""
import json
from pathlib import Path

import wire600_clean_route as base
from wire600_extracted_reserve import REVIEW, validate_change

SCREEN_ROOT = Path('runs/wire600-extracted-clean')
BINDING_PATH = Path(__file__).parent/'fixtures/wire600_selective/extracted_route.json'


def profile():
    return dict(binding=json.loads(BINDING_PATH.read_text()),screen_root=SCREEN_ROOT,
                output=Path('runs/wire600-extracted-route'),proposal_review=REVIEW,
                connectivity_audit=validate_change)


def main():
    base.main(profile())


if __name__ == '__main__':
    main()
