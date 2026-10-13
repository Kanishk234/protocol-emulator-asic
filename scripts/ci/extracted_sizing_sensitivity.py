"""Fixed-SPEF cell-sizing sensitivity only; never physical qualification."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
from event_nor2_screen import logical_cells
from native_stock_route import CORNERS, fingerprints, run_step
from sram_bank_clean_route import unique

SOURCE_RUN=38305592967
SOURCE_SHA='2d73b6fe4b3ee22337fe7db2240cda7761dcda5e'
SOURCE_WORKFLOW='.github/workflows/gds-electrical-incremental-route.yaml'
SOURCE_DRT_ROOT=Path('runs/electrical-incremental-route/drt')
NETLIST_SHA='54538d3f6c830927b5d7947cb22ddf02db01652899d34433605c0aa5c3397b6a'
TARGETS={
    'place7221':('sg13cmos5l_buf_1','sg13cmos5l_buf_2'),
    '_24876_':('sg13cmos5l_inv_1','sg13cmos5l_inv_2'),
    '_30202_':('sg13cmos5l_nor3_1','sg13cmos5l_nor3_2'),
    '_37732_':('sg13cmos5l_nand2_1','sg13cmos5l_nand2_2'),
}
EXTRA_VARIANTS={}
CASES={'baseline':{},**{name:{name:new} for name,(old,new) in TARGETS.items()},
       'combined':{name:new for name,(old,new) in TARGETS.items()},
       'strong_inputs':dict(place7221='sg13cmos5l_buf_4',_24876_='sg13cmos5l_inv_4',
                            _30202_='sg13cmos5l_nor3_2',_37732_='sg13cmos5l_nand2_2')}


def validate_run(run,expected=None):
    if expected is None:expected=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='failure',
                  path=SOURCE_WORKFLOW)
    if any(run.get(k)!=v for k,v in expected.items()):raise ValueError('Wrong extracted diagnostic source')


def change_netlist(text,changes):
    old=logical_cells(text);result=text
    for name,new in changes.items():
        if name not in TARGETS or new not in ({TARGETS[name][1]}|({'sg13cmos5l_buf_4'} if name=='place7221' else {'sg13cmos5l_inv_4'} if name=='_24876_' else set())|EXTRA_VARIANTS.get(name,set())):
            raise ValueError('Unreviewed sizing target')
        master=TARGETS[name][0]
        if old.get(name,(None,))[0]!=master:raise ValueError('Wrong original sizing master')
        pattern=r'\b'+re.escape(master)+r'(\s+)'+re.escape(name)+r'(?=\s*\()'
        result,count=re.subn(pattern,lambda m:new+m[1]+name,result)
        if count!=1:raise ValueError('Ambiguous sizing replacement')
    expected=dict(old)
    for name,new in changes.items():expected[name]=(new,old[name][1])
    if logical_cells(result)!=expected:raise ValueError('Sizing changed connectivity or unrelated cells')
    return result


def corner_metrics(stage):
    # Pinned MultiCornerSTA aggregates generated metrics into state_out.json;
    # it does not emit the OpenROAD-only or_metrics_out.json. Input metrics
    # are empty, so these keys cannot be inherited from the source.
    metrics=json.loads((stage/'state_out.json').read_text())['metrics'];result={}
    for c in CORNERS:
        for report in ('ws.max.rpt','ws.min.rpt','checks.rpt'):
            if c not in (stage/c/report).read_text():raise ValueError('Missing fresh extracted corner report')
        result[c]={k:metrics[k] for k in (
            f'timing__setup__ws__corner:{c}',f'timing__hold__ws__corner:{c}',
            *[f'design__max_{kind}_violation__count__corner:{c}' for kind in ('slew','fanout','cap')])}
    return result


def baseline_matches(metrics,reference):
    for c,row in metrics.items():
        for kind in ('setup','hold'):
            key=f'timing__{kind}__ws__corner:{c}'
            if not math.isfinite(row[key]) or not math.isfinite(reference[key]) or abs(row[key]-reference[key])>1e-6:raise ValueError('Fixed-SPEF baseline does not reproduce source')



def sta_input_state(state,modified):
    # Pinned STAPostPNR dereferences the optional ODB after STA to filter
    # unannotated net reports. Keep the original ODB for that check only;
    # OpenSTA timing still consumes modified NL plus unchanged SPEF.
    if not state.get('odb') or not Path(state['odb']).is_file():
        raise ValueError('Missing reference ODB for pinned annotation check')
    proposal=dict(state,nl=str(modified.resolve()),pnl=None,sdf=None,lib=None,metrics={})
    proposal['def']=None
    return proposal

def main(output=Path('runs/extracted-sizing-sensitivity')):
    validate_run(json.loads(Path('/tmp/native-strength-source-run.json').read_text()))
    trusted=json.loads(Path('/tmp/native-trusted-files.json').read_text());actual=fingerprints(Path.cwd())
    hardware=lambda values:{k:v for k,v in values.items() if not(k.startswith('src/config') and k.endswith('.json'))}
    if hardware(trusted)!=hardware(actual):raise ValueError('Hardware or constraints changed')
    root=Path('runs/extracted-timing');source=unique(root,'*-openroad-stapostpnr/state_out.json')
    state=json.loads(source.read_text());nl=Path(state['nl']);text=nl.read_text()
    if hashlib.sha256(nl.read_bytes()).hexdigest()!=NETLIST_SHA:raise ValueError('Wrong exact extracted netlist')
    if not state.get('spef') or any(not Path(p).is_file() for p in state['spef'].values()):
        raise ValueError('Missing existing extracted SPEF')
    drt=unique(SOURCE_DRT_ROOT,'*-openroad-detailedrouting/state_out.json')
    if json.loads(drt.read_text())['metrics'].get('route__drc_errors')!=0:raise ValueError('Source DRT incomplete')
    config=json.loads(Path('src/config_electrical_incremental_route.json').read_text())
    if config.get('CLOCK_PERIOD')!=20 or config.get('SYNTH_STRATEGY')!='AREA 1' or config.get('GRT_ALLOW_CONGESTION') is not False:
        raise ValueError('Source physical recipe mismatch')
    config.update(STA_CORNERS=list(CORNERS),STA_THREADS=3,SIGNOFF_SDC_FILE=str(Path('src/signoff.sdc').resolve()))
    config.pop('STA_EXTRA_CORNER_TCL_FILE',None)
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE',None)
    reference=json.loads((root/'corner_summary.json').read_text());results={}
    for name,changes in CASES.items():
        modified=output/(name+'.v');modified.write_text(change_netlist(text,changes))
        proposal=sta_input_state(state,modified)
        checkpoint=output/(name+'.json');checkpoint.write_text(json.dumps(proposal,indent=2)+'\n')
        run_step(config,checkpoint,output/name,['OpenROAD.STAPostPNR'])
        stage=unique(output/name,'*-openroad-stapostpnr/state_out.json').parent
        metrics=corner_metrics(stage)
        if name=='baseline':baseline_matches(metrics,reference)
        results[name]=dict(changes=changes,corners=metrics)
        (output/'results.json').write_text(json.dumps(dict(source_run=SOURCE_RUN,
            fixed_spef=True,reference_odb_for_annotation_only=True,physical_change_applied=False,physical_qualified=False,official_signoff=False,
            cases=results),indent=2)+'\n')
        print(name,json.dumps(metrics),flush=True)


if __name__=='__main__':main()
