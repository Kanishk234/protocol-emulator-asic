from copy import deepcopy

import pytest

from selector_density_trial import select


def comparison():
    from test_host_idle_portable_trials import reference
    from host_idle_portable_trials import select as portable
    config, selected = reference()
    return portable(config, selected, 'clock75_hold125')[0]


def test_only_density_changes_and_original_is_preserved():
    config = comparison()
    before = deepcopy(config)
    result = select(config)
    assert config == before
    assert {k: v for k, v in result.items() if config.get(k) != v} == {'PL_TARGET_DENSITY_PCT': 60}
    assert result['CLOCK_PERIOD'] == 20


@pytest.mark.parametrize('key,value', [('CLOCK_PERIOD', 22), ('PL_TARGET_DENSITY_PCT', 64),
                                     ('GRT_ANTENNA_REPAIR_DIODE_ONLY', False)])
def test_comparison_drift_is_rejected(key, value):
    config = comparison()
    config[key] = value
    with pytest.raises(ValueError):
        select(config)


def test_foreign_recipe_is_rejected():
    with pytest.raises(ValueError):
        select(dict(PL_TARGET_DENSITY_PCT=56, CLOCK_PERIOD=20))
