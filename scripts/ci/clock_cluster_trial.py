"""Prepare one native CTS-size trial; do not alter signoff constraints."""
import argparse
import hashlib
import json
from pathlib import Path
from postgrt_timing import CORNERS


def configure(base):
    expected = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                    SYNTH_STRATEGY='AREA 1', GRT_ADJUSTMENT=.16,
                    GRT_RESIZER_HOLD_SLACK_MARGIN=.10,
                    RUN_POST_GRT_RESIZER_TIMING=True, RSZ_CORNERS=list(CORNERS))
    if any(base.get(key) != value for key, value in expected.items()):
        raise ValueError('Wrong native hold100 clean-build recipe')
    for key in ('PNR_SDC_FILE', 'SIGNOFF_SDC_FILE'):
        if not str(base.get(key, '')).endswith('/src/signoff.sdc'):
            raise ValueError('Fully timed signoff constraints required')
    if base.get('CTS_SINK_CLUSTERING_ENABLE', True) is not True:
        raise ValueError('Clock clustering is disabled')
    if base.get('CTS_SINK_CLUSTERING_SIZE') is not None:
        raise ValueError('Source already overrides clock clustering size')
    return dict(base, CTS_SINK_CLUSTERING_SIZE=8)


def main(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Refusing to replace source or existing trial')
    raw = source.read_bytes()
    config = configure(json.loads(raw))
    output.write_text(json.dumps(config, indent=2)+'\n')
    return dict(source_sha256=hashlib.sha256(raw).hexdigest(),
                changed_config_keys=['CTS_SINK_CLUSTERING_SIZE'],
                clean_build_required=True, measured_result=False, official_signoff=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(main(args.source, args.output), indent=2))
