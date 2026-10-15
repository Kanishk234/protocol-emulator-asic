import json
from pathlib import Path
import pytest
from inline_electrical_margin_audit import sources, audit
from post_antenna_fanout_audit import validate_batch
from postgrt_timing import CORNERS


def reports(root, iteration, actual):
    for corner in CORNERS:
        (root/f'postant_margin_{iteration}_{corner}.rpt').write_text(
            f'TRIPWIRE_MARGIN_BEGIN {corner}\nTRIPWIRE_NET_HEX 736f75726365\n'
            f'max slew\nsink/A 2.5 {actual} 0 (MET)\n'
            f'TRIPWIRE_MARGIN_END {corner} 1\n')


def small_case():
    before='sg13cmos5l_buf_1 driver (.A(in),.X(source));\nsg13cmos5l_buf_1 sink (.A(source),.X(out));'
    after=before.replace('sink (.A(source)','sink (.A(tripwire_postant_0_0_net)')+'\nsg13cmos5l_buf_4 tripwire_postant_0_0 (.A(source),.X(tripwire_postant_0_0_net));'
    group=dict(buffer='tripwire_postant_0_0',net='tripwire_postant_0_0_net',source_net='source',master='sg13cmos5l_buf_4',sinks=[['sink','A']])
    return before,after,{'groups':[group]}


def test_small_fanout_requires_independent_margin_evidence():
    before,after,proposal=small_case()
    with pytest.raises(ValueError):validate_batch(before,after,proposal,0)
    assert validate_batch(before,after,proposal,0,{'source'})==1


def test_margin_history_and_final_convergence_are_audited(tmp_path):
    before,after,p=small_case()
    for suffix,text in (('before.nl.v',before),('after.nl.v',after)):
        (tmp_path/('postant_0.'+suffix)).write_text(text)
    (tmp_path/'postant_0.json').write_text(json.dumps(p))
    reports(tmp_path,0,1.2); reports(tmp_path,1,1.0)
    log='TRIPWIRE post-antenna fanout: batch 0 added 1 BUF4 cells\nTRIPWIRE post-antenna fanout: converged after 1 batches'
    assert audit(before,after,tmp_path,log)['inline_electrical_margin_audited'] is True
    reports(tmp_path,1,1.2)
    with pytest.raises(ValueError,match='did not converge'):audit(before,after,tmp_path,log)
    reports(tmp_path,0,1.0)
    with pytest.raises(ValueError):audit(before,after,tmp_path,log)


def test_missing_corner_never_supplies_margin_authorization(tmp_path):
    reports(tmp_path,0,1.2)
    (tmp_path/f'postant_margin_0_{CORNERS[0]}.rpt').unlink()
    with pytest.raises(ValueError):sources(tmp_path,0)


def test_workflow_and_wrapper_keep_live_router_ordering():
    import yaml
    from inline_margin_screen import PROFILE
    root=Path(__file__).resolve().parents[2]
    assert PROFILE['source_run']==38689478738
    assert PROFILE['post_antenna_audit'] is audit
    shell=(root/'scripts/ci/openroad_inline_margin_wrapper.sh').read_text()
    assert shell.index('source /usr/local/share/tripwire/post_antenna_fanout.tcl') < shell.index('source /usr/local/share/tripwire/inline_electrical_margin.tcl') < shell.index('tripwire_post_antenna_finish $antenna_args')
    w=yaml.safe_load((root/'.github/workflows/gds-inline-margin-screen.yaml').read_text())
    assert 'detailedrouting' not in str(w).lower()
    assert any(s.get('run')=='python workflow-src/scripts/ci/inline_margin_screen.py' for s in w['jobs']['harden']['steps'])


@pytest.mark.parametrize('reviewed,protected,expected',[(False,False,0),(True,False,1),(True,True,0)])
def test_tcl_margin_selection_can_buffer_small_data_net_but_never_clock(tmp_path,reviewed,protected,expected):
    import os,subprocess
    from test_post_antenna_fanout import MOCK
    folder=Path(__file__).parent.resolve()
    text=f'source {{{folder/"electrical_repair.tcl"}}}\nsource {{{folder/"post_antenna_fanout.tcl"}}}\n'+MOCK
    text+='set sinks [lrange $sinks 0 0]\n'
    if protected:text+='interp alias {} sink0_A {} term sink0 CLK\n'
    text+='set reviewed '+('{source 1}' if reviewed else '{}')+'\n'
    text+='puts "GROUPS [llength [tripwire_post_antenna_groups 0 $reviewed]]"\n'
    script=tmp_path/'case.tcl';script.write_text(text)
    r=subprocess.run([os.environ.get('TRIPWIRE_TCLSH','tclsh'),str(script)],text=True,capture_output=True)
    assert r.returncode==0,r.stdout+r.stderr
    assert f'GROUPS {expected}' in r.stdout


@pytest.mark.parametrize('bit',[0,8,15])
def test_sram_data_bit_is_audited_individually_and_wrong_bit_is_rejected(bit):
    values=[f'd{i}' for i in reversed(range(16))];values[15-bit]='source'
    before='sg13cmos5l_buf_1 driver (.A(in),.X(source));\n'
    before+='RM_IHPSG13_1P_512x16_c2_bm_bist ram (.A_DIN({'+','.join(values)+'}),.A_REN(ren));'
    new_values=list(values);new_values[15-bit]='tripwire_postant_0_0_net'
    after=before.replace(','.join(values),','.join(new_values))
    after+='\nsg13cmos5l_buf_4 tripwire_postant_0_0 (.A(source),.X(tripwire_postant_0_0_net));'
    group=dict(buffer='tripwire_postant_0_0',net='tripwire_postant_0_0_net',source_net='source',master='sg13cmos5l_buf_4',sinks=[['ram',f'A_DIN[{bit}]']])
    assert validate_batch(before,after,{'groups':[group]},0,{'source'})==1
    wrong=after.replace('d'+str((bit+1)%16), 'unplanned_net')
    with pytest.raises(ValueError):validate_batch(before,wrong,{'groups':[group]},0,{'source'})
    broken=dict(group,sinks=[['ram',f'A_DIN[{(bit+1)%16}]']])
    with pytest.raises(ValueError):validate_batch(before,after,{'groups':[broken]},0,{'source'})


def test_sram_data_width_cannot_be_silently_truncated():
    from electrical_repair_plan import expanded_pins
    with pytest.raises(ValueError,match='width'):
        expanded_pins('RM_IHPSG13_1P_512x16_c2_bm_bist',[('A_DIN','{a,b}')])


def test_failed_audit_evidence_upload_precedes_bulk_even_without_gates():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-inline-margin-screen.yaml').read_text())
    uploads=[s for s in w['jobs']['harden']['steps'] if 'upload-artifact@' in s.get('uses','')]
    assert len(uploads)==3
    audit=uploads[1];bulk=uploads[2]
    assert 'openroad-globalrouting.log' in audit['if']
    assert 'gates.json' not in audit['if']
    assert 'postant_*.nl.v' in audit['with']['path']
    assert 'postant_margin_*.rpt' in audit['with']['path']
    assert 'runs/**' in bulk['with']['path']


def test_saved_grt_replay_refuses_stale_qualification_or_missing_views(tmp_path):
    from combined_physical_screen import resume_grt
    stage=tmp_path/'grt/1-openroad-globalrouting';stage.mkdir(parents=True)
    odb=stage/'chip.odb';layout=stage/'chip.def'
    for p in (odb,layout,stage/'chip.baseline.nl.v',stage/'chip.eco.nl.v',stage/'chip.eco.pnl.v',stage/'after_edits.nl.v'):
        p.write_text('saved view')
    raw=stage/'state_out.json';raw.write_text(json.dumps({'odb':str(odb),'def':str(layout)}))
    proposal={'groups':[],'resizes':[]}
    (tmp_path/'proposal.json').write_text(json.dumps(proposal))
    assert resume_grt(tmp_path,proposal)==raw
    (tmp_path/'gates.json').write_text('{}')
    with pytest.raises(ValueError,match='existing qualification'):resume_grt(tmp_path,proposal)
    (tmp_path/'gates.json').unlink();odb.unlink()
    with pytest.raises(ValueError,match='Missing saved replay view'):resume_grt(tmp_path,proposal)


def test_qualification_replay_binds_failed_run_and_download():
    import yaml
    from inline_margin_qualify import PROFILE
    root=Path(__file__).resolve().parents[2]
    assert PROFILE['resume_grt_run']['id']==38773856018
    assert PROFILE['resume_grt_run']['head_sha']=='0e37feb50922926a4eaaedf7826614c94d4a67d5'
    w=yaml.safe_load((root/'.github/workflows/gds-inline-margin-qualify.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    first=next(s['with'] for s in steps if 'download-artifact@' in s.get('uses',''))
    assert first['run-id']==38773856018
    assert first['name']=='gds-inline-margin-screen-38773856018'
    assert any(s.get('run')=='python workflow-src/scripts/ci/inline_margin_qualify.py' for s in steps)
