"""D-092: intervene before CTS; retain actual failures, never infer chip acceptance."""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import cloud_cfg_fanout as cfg
import cloud_hold_allocation as payload
import cloud_delay_rebalance as shared
from cloud_congestion_reflow import check_rows

ROOT=cfg.ROOT
OUT=ROOT/'build/prects_reflow'
BASE_FLOW=['OpenROAD.CTS','OpenROAD.ResizerTimingPostCTS','OpenROAD.STAMidPNR']
REFLOW=['OpenROAD.GlobalPlacement','OpenROAD.DetailedPlacement']+BASE_FLOW
PROTECTED=('CLOCK_PORT','CLOCK_PERIOD','CLOCK_UNCERTAINTY_CONSTRAINT','CLOCK_TRANSITION_CONSTRAINT',
    'MAX_FANOUT_CONSTRAINT','FALLBACK_SDC','PNR_SDC_FILE','TIME_DERATING_CONSTRAINT')


def configure(source, reflow):
    result=dict(source,CTS_SINK_CLUSTERING_SIZE=8)
    result['meta']={'version':2,'flow':list(REFLOW if reflow else BASE_FLOW)}
    if reflow:
        result.update(PL_TARGET_DENSITY_PCT=55,PL_ROUTABILITY_DRIVEN=True,
            PL_TIMING_DRIVEN=False,PL_SKIP_INITIAL_PLACEMENT=True)
    allowed={'CTS_SINK_CLUSTERING_SIZE','meta','PL_TARGET_DENSITY_PCT','PL_ROUTABILITY_DRIVEN',
             'PL_TIMING_DRIVEN','PL_SKIP_INITIAL_PLACEMENT'}
    if any(result.get(k)!=v for k,v in source.items() if k not in allowed):
        raise ValueError('Unexpected source configuration change')
    return result


def resolved_policy(stage, config):
    resolved=json.loads((stage/'config.json').read_text())
    if resolved.get('CELL_LIBS')!=config['LIB'] or cfg.macro_contract(resolved.get('MACROS',{}))!=cfg.macro_contract(config['MACROS']):
        raise ValueError('Native library/macro contract changed')
    for key in PROTECTED:
        if resolved.get(key)!=config.get(key):raise ValueError('Protected native policy changed: '+key)


def run_stage(config,state,label):
    path=OUT/(label+'_config.json');path.write_text(json.dumps(config))
    initial=OUT/(label+'_state.json');initial.write_text(json.dumps(state))
    run=OUT/label;run.mkdir(exist_ok=False)
    cmd=[sys.executable,'-m','librelane','--docker-no-tty','--dockerized','--pdk','ihp-sg13cmos5l',
        '--pdk-root',os.environ['PDK_ROOT'],'--manual-pdk','--hide-progress-bar','--force-run-dir',str(run),
        '--with-initial-state',str(initial),str(path)]
    with (OUT/(label+'.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    return run


def snapshot(odb,label):
    # Native export is exercised on the unchanged source before any experiment.
    script=OUT/'snapshot.tcl'
    script.write_text(cfg.CENSUS+'\nread_db $::env(WARP_INPUT_ODB)\nset block [ord::get_db_block]\n'+
        'check_placement'+shared.EDIT.split('check_placement',1)[1]+'\nwrite_def $::env(WARP_DEF)\n')
    env={'WARP_INPUT_ODB':odb,'WARP_AFTER':OUT/(label+'.tsv'),'WARP_GEOMETRY':OUT/(label+'_geometry.tsv'),
        'WARP_OUTPUT_ODB':OUT/(label+'_snapshot.odb'),'WARP_OUTPUT_NL':OUT/(label+'_snapshot.nl.v'),
        'WARP_DEF':OUT/(label+'.def')}
    cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT)]
    for key,value in env.items():cmd.extend(['-e',f'{key}={value}'])
    cmd.extend(['--entrypoint','openroad',cfg.IMAGE,'-exit',str(script)])
    with (OUT/(label+'_snapshot.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    instances,_=cfg.parse_census((OUT/(label+'.tsv')).read_text())
    geometry=(OUT/(label+'_geometry.tsv')).read_text();text=(OUT/(label+'.def')).read_text()
    from cloud_hotspot_padding import boxes
    _,_,shapes=boxes(geometry)
    pins=re.search(r'^PINS\s+\d+\s*;.*?^END PINS\s*$',text,re.M|re.S)
    if pins is None:raise ValueError('Native boundary pins missing')
    return {'macro':instances['u_fabric'],'macro_box':shapes['u_fabric'],
        'pins':pins.group(),'rows':[x for x in text.splitlines() if x.startswith(('ROW ','DIEAREA '))],
        'core_power_phase_cells':check_rows(text,geometry,instances),'instances':len(instances)}


def main():
    OUT.mkdir(exist_ok=False)
    result={'diagnostic_complete':False,'physical_acceptance':False,'routing_executed':False,
        'configured_timing_acceptance':False,'cases':{}}
    def save():(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        archive=ROOT/'build/fanout-preflight-source.tar.gz'
        if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError('Original archive differs')
        bundle=payload.prepare_payload(archive,OUT/'original_source')
        replace=lambda s:s.replace('@BUNDLE@',str(bundle)).replace('@PDK@',os.environ['PDK_ROOT'])
        state=cfg.transform(json.loads((bundle/'state.json').read_text()),replace)
        source=cfg.transform(json.loads((bundle/'config.json').read_text()),replace)
        if source.get('PAD_LIBS') is None:source['PAD_LIBS']={}
        for key,digest in cfg.EXPECTED.items():
            if cfg.sha(Path(state[key]))!=digest:raise ValueError('Pre-CTS source view differs')
        original=snapshot(Path(state['odb']),'source')
        for label,reflow in (('control',False),('reflow',True)):
            config=configure(source,reflow)
            run=run_stage(config,state,label)
            stages=list(run.glob('*-openroad-cts'))
            if len(stages)!=1:raise ValueError('Missing unique rebuilt CTS stage')
            resolved_policy(stages[0],config)
            stages=list(run.glob('*-openroad-stamidpnr'))
            if len(stages)!=1:raise ValueError('Missing unique completed STA stage')
            resolved_policy(stages[0],config)
            final=json.loads((stages[0]/'state_out.json').read_text())
            actual=snapshot(Path(final['odb']),label)
            for key in ('macro','macro_box','pins','rows'):
                if actual[key]!=original[key]:raise ValueError('Fixed physical interface changed: '+key)
            case={'rebuilt_cts':True,'native_interface_exact':True,'placement':actual,
                  'corner_guards':{},'electrical_timing_guards_pass':False}
            result['cases'][label]=case;save()
            for corner in source['STA_CORNERS']:
                selected=cfg.single_corner_config(config,corner)
                selected['meta']={'version':2,'flow':['OpenROAD.STAMidPNR']}
                corner_run=run_stage(selected,final,label+'_'+corner)
                stage,=corner_run.glob('*-openroad-stamidpnr');resolved_policy(stage,selected)
                metrics=json.loads((stage/'state_out.json').read_text())['metrics']
                required=[f'design__{kind}_violation__count__corner:{corner}' for kind in ('max_fanout','max_slew','max_cap')]
                required += [f'timing__{kind}_vio__count__corner:{corner}' for kind in ('setup','hold')]
                if any(k not in metrics for k in required):raise ValueError('Missing actual corner violations')
                setup=metrics[f'timing__setup__ws__corner:{corner}'];hold=metrics[f'timing__hold__ws__corner:{corner}']
                if any(type(v) not in (int,float) or not math.isfinite(v) for v in (setup,hold)):
                    raise ValueError('Missing/nonfinite actual slack')
                passed=all(metrics[k]==0 for k in required) and setup>0 and hold>=0.1
                case['corner_guards'][corner]={'pass':passed,'setup_slack_ns':setup,'hold_slack_ns':hold,
                    'violations':{k:metrics[k] for k in required},'metrics':metrics};save()
            case['electrical_timing_guards_pass']=all(v['pass'] for v in case['corner_guards'].values());save()
        for key,digest in cfg.EXPECTED.items():
            if cfg.sha(Path(state[key]))!=digest:raise ValueError('Original source modified')
        result['diagnostic_complete']=True
    except Exception as exc:result['error']=str(exc);raise
    finally:save()


if __name__=='__main__':main()
