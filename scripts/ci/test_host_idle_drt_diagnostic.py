import pytest
from host_idle_drt_diagnostic import configure


def test_only_bounded_diagnostic_controls_change_and_source_is_preserved():
    original=dict(CLOCK_PERIOD=20,MACROS={'m':{'location':[12,40]}},
                  GRT_RESIZER_HOLD_SLACK_MARGIN=.175,DRT_OPT_ITERS=64,
                  DRT_SAVE_DRC_REPORT_ITERS=None,DRT_ANTENNA_REPAIR_ITERS=3)
    result=configure(original)
    assert result['DRT_OPT_ITERS']==42 and result['DRT_SAVE_DRC_REPORT_ITERS']==1
    assert result['DRT_ANTENNA_REPAIR_ITERS']==0 and result['DRT_SAVE_SNAPSHOTS'] is False
    assert result['CLOCK_PERIOD']==20 and result['GRT_RESIZER_HOLD_SLACK_MARGIN']==.175
    assert result['MACROS']==original['MACROS'] and result['MACROS'] is not original['MACROS']
    assert original['DRT_OPT_ITERS']==64 and original['DRT_ANTENNA_REPAIR_ITERS']==3
    allowed={'DRT_OPT_ITERS','DRT_SAVE_DRC_REPORT_ITERS','DRT_ANTENNA_REPAIR_ITERS',
             'DRT_SAVE_SNAPSHOTS','OPENROAD_THREADS'}
    assert {k:v for k,v in result.items() if k not in allowed}=={k:v for k,v in original.items() if k not in allowed}


@pytest.mark.parametrize('period',[None,18,25])
def test_changed_or_missing_source_clock_rejects(period):
    with pytest.raises(ValueError):configure(dict(CLOCK_PERIOD=period))
