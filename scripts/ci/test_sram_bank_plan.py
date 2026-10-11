import hashlib
import copy
from pathlib import Path
import pytest
import sram_bank_plan as runner


def test_allocator_reserves_previous_moves_and_preserves_site_grid():
    rows = [(0, 100, 'N', 20, 10)]
    boxes = [('existing', 40, 100, 70, 120)]
    first = runner.allocate(rows, boxes, 'a', 20, 20, [50, 100])
    assert first[1] % 10 == 0 and (first[1]+20 <= 40 or first[1] >= 70)
    boxes.append(('a', first[1], first[2], first[1]+20, first[2]+20))
    second = runner.allocate(rows, boxes, 'b', 20, 20, [50, 100])
    assert second[1]+20 <= first[1] or second[1] >= first[1]+20
    assert second[1]+20 <= 40 or second[1] >= 70


def test_allocator_rejects_no_space_for_complete_footprint():
    with pytest.raises(ValueError):
        runner.allocate([(0, 0, 'N', 2, 10)], [], 'a', 30, 20, [0, 0])


def fixture(tmp_path, monkeypatch):
    nl = ''
    layout = 'UNITS DISTANCE MICRONS 1000 ;\n- u_chip.u_sram.sram RM_IHPSG13_1P_512x16_c2_bm_bist + FIXED ( 12000 40000 ) FS ;\nROW row CoreSite 0 245700 N DO 600 BY 1 STEP 480 0 ;\n'
    boxes = []
    lef = ''
    for bit in range(16):
        name = f'buf{bit}'
        x = 400000+bit*5000
        nl += f'sg13cmos5l_buf_4 {name} (.A(\\u_chip.g_lane[0].u_lane.mem_rdata[{bit}] ), .X(n{bit}));\n'
        layout += f'- {name} sg13cmos5l_buf_4 + PLACED ( {x} 230580 ) N ;\n'
        boxes.append((name, x, 230580, x+3840, 234360))
        lef += f'PIN A_DOUT[{bit}]\nRECT {10+bit*10} 0 {11+bit*10} 1 ;\nEND A_DOUT[{bit}]\n'
    macro = tmp_path/'macro.lef'; macro.write_text(lef)
    monkeypatch.setattr(runner, 'NL_SHA', hashlib.sha256(nl.encode()).hexdigest())
    monkeypatch.setattr(runner, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    monkeypatch.setattr(runner, 'MACRO_LEF_SHA', hashlib.sha256(macro.read_bytes()).hexdigest())
    monkeypatch.setattr(runner, 'occupancy', lambda *args: ((3840, 3780), boxes.copy()))
    return nl, layout, macro


def test_complete_bank_preserves_identity_and_has_no_combined_overlap(tmp_path, monkeypatch):
    nl, layout, macro = fixture(tmp_path, monkeypatch)
    p = runner.plan(nl, layout, Path('/unused'), macro)
    assert len(p['proposals']) == 16 and p['added_cells'] == 0
    assert p['footprint_overlap_count'] == 0 and not p['physical_timing_measured']
    for g in p['proposals']:
        assert g['pins']['X'] == 'n'+str(g['bit'])
        assert g['new_origin_distance_dbu'] < g['old_origin_distance_dbu']
    fragment = runner.placement_fragment(p)['MANUAL_GLOBAL_PLACEMENTS']
    assert len(fragment) == 16
    first = p['proposals'][0]
    assert fragment[first['instance']]['location'] == [v/1000 for v in first['new_location'][:2]]


def test_placement_export_rejects_wrong_source_or_duplicate_instance(tmp_path, monkeypatch):
    import copy
    nl, layout, macro = fixture(tmp_path, monkeypatch)
    p = runner.plan(nl, layout, Path('/unused'), macro)
    wrong = copy.deepcopy(p); wrong['source_run'] = 1
    with pytest.raises(ValueError): runner.placement_fragment(wrong)


def test_clean_stage_has_separate_provenance_and_export(tmp_path, monkeypatch):
    nl, layout, macro = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, 'CLEAN_NL_SHA', runner.NL_SHA)
    monkeypatch.setattr(runner, 'CLEAN_DEF_SHA', runner.DEF_SHA)
    p = runner.plan(nl, layout, Path('/unused'), macro, clean_postgpl=True)
    assert p['source_run'] == 37990280838 and p['source_stage'] == 'postgpl-clean'
    assert len(runner.placement_fragment(p)['MANUAL_GLOBAL_PLACEMENTS']) == 16
    wrong = copy.deepcopy(p); wrong['proposals'].append(wrong['proposals'][0])
    with pytest.raises(ValueError): runner.placement_fragment(wrong)


@pytest.mark.parametrize('fault', ['netlist', 'layout', 'macro', 'missing_buffer'])
def test_wrong_source_or_missing_interface_rejected(tmp_path, monkeypatch, fault):
    nl, layout, macro = fixture(tmp_path, monkeypatch)
    if fault == 'netlist': nl += 'changed'
    if fault == 'layout': layout += 'changed'
    if fault == 'macro': macro.write_text('changed')
    if fault == 'missing_buffer':
        nl = nl.replace('sg13cmos5l_buf_4 buf0', 'sg13cmos5l_buf_1 buf0')
        monkeypatch.setattr(runner, 'NL_SHA', hashlib.sha256(nl.encode()).hexdigest())
    with pytest.raises(ValueError): runner.plan(nl, layout, Path('/unused'), macro)
