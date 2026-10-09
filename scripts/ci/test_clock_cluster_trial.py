import json
import pytest
from clock_cluster_trial import configure, main
from postgrt_timing import CORNERS


def recipe():
    return dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56, SYNTH_STRATEGY='AREA 1',
                GRT_ADJUSTMENT=.16, GRT_RESIZER_HOLD_SLACK_MARGIN=.10,
                RUN_POST_GRT_RESIZER_TIMING=True, RSZ_CORNERS=list(CORNERS),
                PNR_SDC_FILE='/runner/src/signoff.sdc', SIGNOFF_SDC_FILE='/runner/src/signoff.sdc')


def test_one_change_and_no_mutation():
    source = recipe()
    result = configure(source)
    assert set(result)-set(source) == {'CTS_SINK_CLUSTERING_SIZE'}
    assert all(result[k] == v for k,v in source.items())
    assert 'CTS_SINK_CLUSTERING_SIZE' not in source
    assert result['CTS_SINK_CLUSTERING_SIZE'] == 8


@pytest.mark.parametrize('key,value', [('CLOCK_PERIOD', 21), ('PL_TARGET_DENSITY_PCT', 57),
    ('GRT_RESIZER_HOLD_SLACK_MARGIN', .05), ('RSZ_CORNERS', list(CORNERS[:1])),
    ('PNR_SDC_FILE', '/runner/src/pnr.sdc'), ('SIGNOFF_SDC_FILE', '/runner/src/pnr.sdc'),
    ('CTS_SINK_CLUSTERING_ENABLE', False), ('CTS_SINK_CLUSTERING_SIZE', 8)])
def test_reject_wrong_source(key,value):
    source=recipe();source[key]=value
    with pytest.raises(ValueError):configure(source)


def test_existing_output_is_not_overwritten(tmp_path):
    source=tmp_path/'source.json';source.write_text(json.dumps(recipe()))
    output=tmp_path/'trial.json'
    receipt=main(source,output)
    assert receipt['measured_result'] is False
    with pytest.raises(ValueError):main(source,output)
    with pytest.raises(ValueError):main(source,source)


def test_clock_screen_uses_clean_stock_flow_and_fixed_full_candidate():
    from pathlib import Path
    import yaml
    root=Path(__file__).resolve().parents[2]
    workflow=yaml.safe_load((root/'.github/workflows/gds-native-clock8-screen.yaml').read_text())
    job=workflow['jobs']['harden']
    assert job['env']['NATIVE_CLOCK_CLUSTER_SIZE']=='8'
    assert job['env']['NATIVE_HOLD_TARGET']=='0.10'
    assert job['env']['CANDIDATE_SHA']=='3393eea9a58c5cad9077cc360a8515d0e5ec8284'
    assert not any('download-artifact@' in s.get('uses','') for s in job['steps'])
    step=next(s for s in job['steps'] if s['name'].startswith('Run stock synthesis'))
    assert step['run'].endswith('native_stock_screen.py')
