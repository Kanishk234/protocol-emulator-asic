"""Diagnose the exact official GDS signoff failure without altering physical data."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

from cache_final_route import local_view, bootstrap
from cache_final_protocols import ROUTED_ODB_SHA, ROUTED_NL_SHA, FINAL_NL_SHA
from physical_runtime import container_flags

RUN=44138149950
SHA='1dfee9eaf49ccd5cc5805299f96da9aa8a6850e5'
GDS_SHA='ddf9668fc20eba68fc936f408bdeee3446ba0dd026c8cf8b99ee8b0e12d5f9fb'
SOURCE='runs/wokwi/75-misc-reportmanufacturability/state_out.json'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(root,metadata):
    root=Path(root)
    expected=dict(id=RUN,head_sha=SHA,head_branch='main',conclusion='failure',path='.github/workflows/gds.yaml')
    if any(metadata.get(k)!=v for k,v in expected.items()):raise ValueError('Wrong official failure identity')
    run=root/'runs/wokwi'
    state=json.loads((root/SOURCE).read_text())
    for path,sha in [('47-openroad-detailedrouting/tt_um_tripwire.odb',ROUTED_ODB_SHA),
                     ('47-openroad-detailedrouting/tt_um_tripwire.nl.v',ROUTED_NL_SHA),
                     ('55-openroad-fillinsertion/tt_um_tripwire.nl.v',FINAL_NL_SHA)]:
        if digest(run/path)!=sha:raise ValueError('Official physical/replay identity changed: '+path)
    if digest(local_view(root,state['gds']))!=GDS_SHA:raise ValueError('Wrong merged GDS')
    metrics=state['metrics']
    for key,value in [('route__drc_errors',0),('magic__drc_error__count',57923),('magic__illegal_overlap__count',10),
                      ('timing__setup_vio__count',0),('timing__hold_vio__count',0)]:
        if metrics.get(key)!=value:raise ValueError('Unexpected final metric: '+key)
    # The text report preserves all errors. Its XML drops one duplicate Cnt.c category.
    text=(run/'65-magic-drc/reports/drc.magic.rpt').read_text()
    parts=text.split('----------------------------------------');groups=[];total=0
    for i in range(1,len(parts)-1,2):
        rule=parts[i].strip()
        boxes=[tuple(map(float,b)) for b in re.findall(r'([-\d.]+)um\s+([-\d.]+)um\s+([-\d.]+)um\s+([-\d.]+)um',parts[i+1])]
        if not boxes:raise ValueError('Empty/unparsed Magic rule group')
        if any(not (12<=a<=c<=248.8 and 40<=b<=d<=231.34) for a,b,c,d in boxes):
            raise ValueError('Magic DRC outside SRAM footprint')
        groups.append(dict(rule=rule,count=len(boxes)));total+=len(boxes)
    if total!=57923:raise ValueError('Incomplete Magic text error inventory')
    feedback=ET.parse(run/'67-magic-spiceextraction/feedback.xml').getroot()
    items=feedback.findall('./items/item')
    if len(items)!=10 or any(i.findtext('category')!="'obsm4-metal4.ILLEGAL_OVERLAP'" for i in items):
        raise ValueError('Unknown overlap markers')
    for item in items:
        polygons=[v.text for v in item.findall('./values/value') if (v.text or '').startswith('polygon:')]
        if len(polygons)!=1:raise ValueError('Missing overlap geometry')
        coords=re.findall(r'([-\d.]+),([-\d.]+)',polygons[0])
        if not coords or any(not (12<=float(x)<=248.8 and 40<=float(y)<=231.34) for x,y in coords):
            raise ValueError('Overlap outside SRAM footprint')
    return dict(official_run=RUN,gds_sha256=GDS_SHA,routed_odb_matches_qualified=True,
                final_netlist_matches_22_case_replay=True,magic_error_count=total,
                magic_groups=groups,magic_errors_outside_macro=0,abstract_m4_overlap_markers=10,
                real_geometry_klayout_drc_pending=True,official_signoff=False,phase2_complete=False)


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['audit','klayout'])
    args=p.parse_args();root=Path.cwd()
    row=audit(root,json.loads(Path('official-failure-run.json').read_text()))
    Path('official-macro-failure-audit.json').write_text(json.dumps(row,indent=2)+'\n')
    if args.stage=='audit':print(json.dumps(row,indent=2));return
    config=json.loads(Path('src/config_merged.json').read_text())
    bootstrap(config,Path(SOURCE),'official-signoff-pdk')
    cfg={**config,'meta':{'version':1,'flow':['KLayout.DRC','Checker.KLayoutDRC']},
         'RUN_KLAYOUT_DRC':True,'ERROR_ON_KLAYOUT_DRC':True,'KLAYOUT_DRC_THREADS':2}
    target=Path('src/config_official_klayout_audit.json');target.write_text(json.dumps(cfg,indent=2)+'\n')
    subprocess.run([sys.executable,'-m','librelane','--pdk-root','/home/runner/pdk',*container_flags(),
                    '--pdk','ihp-sg13cmos5l','--run-tag','official-klayout-audit',
                    '--force-run-dir','runs/official-klayout-audit','--hide-progress-bar',
                    '--with-initial-state',SOURCE,str(target)],check=True)
    results=list(Path('runs/official-klayout-audit').glob('*-klayout-drc/state_out.json'))
    if len(results)!=1:raise ValueError('Missing unique fresh KLayout result')
    count=json.loads(results[0].read_text())['metrics'].get('klayout__drc_error__count')
    if type(count) is not int or count!=0:raise ValueError('KLayout DRC nonzero/missing: '+str(count))
    if digest(local_view(root,json.loads(Path(SOURCE).read_text())['gds']))!=GDS_SHA:
        raise ValueError('Merged GDS changed during read-only audit')
    row.update(real_geometry_klayout_drc_pending=False,klayout_drc_errors=0)
    Path('official-macro-failure-audit.json').write_text(json.dumps(row,indent=2)+'\n')
    print(json.dumps(row,indent=2))


if __name__=='__main__':main()
