import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
import official_gds_signoff_audit as auditmod


def package(root,monkeypatch):
    run=root/'runs/wokwi';run.mkdir(parents=True)
    paths=['47-openroad-detailedrouting/tt_um_tripwire.odb','47-openroad-detailedrouting/tt_um_tripwire.nl.v','55-openroad-fillinsertion/tt_um_tripwire.nl.v','61-klayout-streamout/tt_um_tripwire.gds']
    constants=['ROUTED_ODB_SHA','ROUTED_NL_SHA','FINAL_NL_SHA','GDS_SHA']
    for path,key in zip(paths,constants):
        p=run/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(path)
        monkeypatch.setattr(auditmod,key,auditmod.digest(p))
    state={'gds':'/home/runner/work/protocol-emulator-asic/protocol-emulator-asic/runs/wokwi/'+paths[-1],
           'metrics':{'route__drc_errors':0,'magic__drc_error__count':57923,'magic__illegal_overlap__count':10,'timing__setup_vio__count':0,'timing__hold_vio__count':0}}
    p=root/auditmod.SOURCE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(state))
    p=run/'65-magic-drc/reports/drc.magic.rpt';p.parent.mkdir(parents=True)
    p.write_text('tt_um_tripwire\n----------------------------------------\nfixture rule\n----------------------------------------\n'+' 12.1um 40.1um 12.2um 40.2um\n'*57923)
    doc=ET.Element('report-database');items=ET.SubElement(doc,'items')
    for _ in range(10):
        item=ET.SubElement(items,'item');ET.SubElement(item,'category').text="'obsm4-metal4.ILLEGAL_OVERLAP'"
        values=ET.SubElement(item,'values');ET.SubElement(values,'value').text='polygon: (28.19,186.1;30.29,192.3)'
    p=run/'67-magic-spiceextraction/feedback.xml';p.parent.mkdir(parents=True);ET.ElementTree(doc).write(p)
    return dict(id=auditmod.RUN,head_sha=auditmod.SHA,head_branch='main',conclusion='failure',path='.github/workflows/gds.yaml')


def test_scoped_inventory_is_not_signoff(tmp_path,monkeypatch):
    row=auditmod.audit(tmp_path,package(tmp_path,monkeypatch))
    assert row['magic_error_count']==57923 and row['magic_errors_outside_macro']==0
    assert row['real_geometry_klayout_drc_pending'] and not row['official_signoff']


@pytest.mark.parametrize('fault',['outside','incomplete','gds','metadata'])
def test_reject_unreviewed_or_incomplete_evidence(tmp_path,monkeypatch,fault):
    metadata=package(tmp_path,monkeypatch)
    p=tmp_path/'runs/wokwi/65-magic-drc/reports/drc.magic.rpt'
    if fault=='outside':p.write_text(p.read_text().replace('12.1um','0.1um',1))
    elif fault=='incomplete':p.write_text(p.read_text().replace(' 12.1um 40.1um 12.2um 40.2um\n','',1))
    elif fault=='gds':(tmp_path/'runs/wokwi/61-klayout-streamout/tt_um_tripwire.gds').write_text('changed')
    else:metadata['head_sha']='wrong'
    with pytest.raises(ValueError):auditmod.audit(tmp_path,metadata)


def test_klayout_destination_exists_before_cli(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'src').mkdir()
    (tmp_path/'src/config_merged.json').write_text('{}')
    (tmp_path/'official-failure-run.json').write_text('{}')
    monkeypatch.setattr(auditmod,'audit',lambda *args:{'official_signoff':False})
    monkeypatch.setattr(auditmod,'bootstrap',lambda *args:None)
    monkeypatch.setattr(auditmod.sys,'argv',['audit','klayout'])
    def check_cli(command,check):
        destination=Path(command[command.index('--force-run-dir')+1])
        assert destination.is_dir(), 'Pinned CLI requires pre-existing output directory'
        assert check is True
        config=json.loads(Path(command[-1]).read_text())
        assert config['meta']['flow']==['KLayout.DRC','Checker.KLayoutDRC']
        assert config['ERROR_ON_KLAYOUT_DRC'] is True
        raise RuntimeError('CLI handoff checked')
    monkeypatch.setattr(auditmod.subprocess,'run',check_cli)
    with pytest.raises(RuntimeError,match='CLI handoff checked'):auditmod.main()
