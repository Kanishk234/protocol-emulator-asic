"""Restore known five-net fanout repair on the measured pre-CTS reflow result."""
import json
import os
from pathlib import Path
import subprocess
import cloud_cfg_fanout as cfg
import cloud_cfg_fanout_local as fixed
import cloud_hotspot_padding as guards
import cloud_prects_reflow as stage

ROOT=cfg.ROOT
SOURCE=ROOT/'build/prects_reflow'
OUT=ROOT/'build/prects_fanout'
RESULT_SHA='f8db35215e1070f84fdda2450748e3d9b0e5b215bcba73e30c9b2eb461c942bd'
EXPECTED={'odb':'7dccd603c72ed7dc3039b61dc2e13cd061107ce5084a821edeba14c00e21b48e',
 'nl':'469fe33d8b1d67f5e0b619e988fde65c2b411e93cd6ca43498c34059e6ed036f',
 'sdc':'2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e'}


def editor(count):
    if count!=3645:raise ValueError('Unexpected measured original instance count')
    snapshot=fixed.SNAPSHOT.replace('3596','3645').replace('3595','3644')
    start='census $::env(WARP_BEFORE)\n';legal='detailed_placement\ncheck_placement -verbose\n'
    if cfg.EDIT.count(start)!=1 or cfg.EDIT.count(legal)!=1:raise ValueError('Buffer edit anchors changed')
    return cfg.EDIT.replace(start,start+snapshot,1).replace(legal,fixed.LEGALIZE.replace('3596','3645'),1)


def immutability(before,after):
    audit=cfg.verify_connections(before,after)
    old,_=cfg.parse_census(before);new,_=cfg.parse_census(after)
    if len(old)!=3645 or any(new[n]!=v for n,v in old.items()):raise ValueError('Original instance moved or changed')
    return audit


def main():
    OUT.mkdir(exist_ok=False)
    result={'producer_passed':False,'physical_acceptance':False,'routing_executed':False,
        'source_run':38319615838,'corners':{}}
    def save():(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        if cfg.sha(SOURCE/'result.json')!=RESULT_SHA:raise ValueError('Measured stage comparison differs')
        source=json.loads((SOURCE/'result.json').read_text())['cases']['reflow']
        if not source['native_interface_exact'] or len(source['corner_guards'])!=3:raise ValueError('Source evidence incomplete')
        for guard in source['corner_guards'].values():
            if guard['setup_slack_ns']<=0 or guard['hold_slack_ns']<0.1:raise ValueError('Source timing guard differs')
            counts=guard['violations']
            if any(value!=(5 if 'max_fanout' in key else 0) for key,value in counts.items()):raise ValueError('Source electrical diagnosis differs')
        final=SOURCE/'reflow/final'
        paths={k:final/kind/('tt_um_warp.'+ext) for k,kind,ext in (('odb','odb','odb'),('nl','nl','nl.v'),('sdc','sdc','sdc'))}
        for key,path in paths.items():
            if cfg.sha(path)!=EXPECTED[key]:raise ValueError('Measured source view differs')
        script=OUT/'buffer.tcl';script.write_text(cfg.CENSUS+editor(3645))
        env={'WARP_INPUT_ODB':paths['odb'],'WARP_BEFORE':OUT/'before.tsv','WARP_AFTER':OUT/'after.tsv',
             'WARP_OUTPUT_ODB':OUT/'buffered.odb','WARP_OUTPUT_NL':OUT/'buffered.nl.v'}
        cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT)]
        for key,value in env.items():cmd.extend(['-e',f'{key}={value}'])
        cmd.extend(['--entrypoint','openroad',cfg.IMAGE,'-exit',str(script)])
        with (OUT/'buffer.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        if cfg.parse_census((OUT/'before.tsv').read_text())!=cfg.parse_census((SOURCE/'reflow.tsv').read_text()):raise ValueError('Native source census differs')
        result['audit']=immutability((OUT/'before.tsv').read_text(),(OUT/'after.tsv').read_text());save()
        # Export/check actual final geometry and ROW power phase using preflighted reader.
        stage.OUT=OUT
        result['placement']=stage.snapshot(OUT/'buffered.odb','buffered')
        original=source['placement']
        for key in ('macro','macro_box','pins','rows'):
            if json.loads(json.dumps(result['placement'][key]))!=original[key]:raise ValueError('Physical interface changed')
        config=json.loads((SOURCE/'reflow_config.json').read_text());config['meta']={'version':2,'flow':['OpenROAD.STAMidPNR']}
        guards.OUT=OUT
        for corner in config['STA_CORNERS']:
            guard=guards.sta(config,'buffered_'+corner,OUT/'buffered.odb',OUT/'buffered.nl.v',paths['sdc'],corner)
            if guard['metrics'][f'timing__hold__ws__corner:{corner}']<0.1:raise ValueError('Additional original hold guard lost')
            result['corners'][corner]=guard;save()
        for key,path in paths.items():
            if cfg.sha(path)!=EXPECTED[key]:raise ValueError('Original physical source modified')
        result['candidate_sha256']={n:cfg.sha(OUT/n) for n in ('buffered.odb','buffered.nl.v')}
        result['producer_passed']=True
    except Exception as exc:result['error']=str(exc);raise
    finally:save()


if __name__=='__main__':main()
