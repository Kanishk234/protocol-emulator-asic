import pytest
from route_reopen_libraries import select


def fixture():
    return dict(DEFAULT_CORNER='nom_typ', CELL_LIBS={'nom_typ': ['/pdk/cells.lib']},
                MACROS={'sram': {'lib': {'nom_*': ['/macro/sram.lib']}}})


def test_resolved_corner_selection():
    assert select(fixture()) == ['/pdk/cells.lib', '/macro/sram.lib']


@pytest.mark.parametrize('mapping', [{}, {'nom_*': ['/a.lib'], '*': ['/b.lib']}])
def test_missing_or_ambiguous_macro_rejects(mapping):
    settings = fixture()
    settings['MACROS']['sram']['lib'] = mapping
    with pytest.raises(ValueError):
        select(settings)


def test_unresolved_path_rejects():
    settings = fixture()
    settings['CELL_LIBS']['nom_typ'] = ['dir::cells.lib']
    with pytest.raises(ValueError):
        select(settings)
