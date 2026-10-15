"""Rebuild exact best133 views from the approved durable pre-CTS source archive.

No expired artifacts or public uploads. Native execution remains cloud-only.
Every historical intermediate/final physical view is byte authenticated; this
produces fresh estimated STA evidence, never a replacement historical run result.
"""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

import cloud_cfg_fanout as cfg
import cloud_cfg_fanout_local as fixed
import cloud_hold_allocation as reference
import cloud_prects_reflow as prects
import cloud_reset_combined  # installs only the documented combined26move PLAN
import cloud_reset643_whitespace as reset
import cloud_hotspot_padding as guards

ROOT = cfg.ROOT
OUT = ROOT / 'build/reset_combined'
WORK = ROOT / 'build/control_regeneration'
DESTINATION = ROOT / 'build/route_trace_input/baseline'
FIXED_ODB_SHA = '0d2e6ea8666c9336e4447018be9325275f9366f58cb785cf6b70b616734b84e9'
SDC_SHA = cfg.DERIVED['sdc']


def native(script_text, label, env):
    script = WORK / (label+'.tcl');script.write_text(script_text)
    cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT)]
    for key,value in env.items():cmd.extend(['-e',f'{key}={value}'])
    cmd.extend(['--entrypoint','openroad',cfg.IMAGE,'-exit',str(script)])
    with (WORK/(label+'.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)


def final_config(source):
    config=dict(source)
    if config.get('MAX_FANOUT_CONSTRAINT')!=10 or config.get('CLOCK_PERIOD')!=20:
        raise ValueError('Original timing policy differs')
    config['CTS_SINK_CLUSTERING_SIZE']=8
    config['meta']={'version':2,'flow':['OpenROAD.STAMidPNR']}
    return config


def authenticate_final(directory):
    for name,digest in reference.EXPECTED.items():
        if cfg.sha(directory/name)!=digest:
            raise ValueError('Reproduced historical view differs: '+name)


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Cloud-only native regeneration')
    OUT.mkdir(exist_ok=False);WORK.mkdir(exist_ok=False)
    result={'regenerated':False,'source_run':38167697696,
        'source_archive_sha256':cfg.SOURCE_SHA,'physical_acceptance':False,
        'configured_timing_acceptance':False,'routing_executed':False,'corners':{}}
    def save(): (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        archive=ROOT/'build/fanout-preflight-source.tar.gz'
        if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError('Approved archive differs')
        bundle=reference.prepare_payload(archive,OUT/'original_source')
        replace=lambda s:s.replace('@BUNDLE@',str(bundle)).replace('@PDK@',os.environ['PDK_ROOT'])
        source=cfg.transform(json.loads((bundle/'config.json').read_text()),replace)
        state=cfg.transform(json.loads((bundle/'state.json').read_text()),replace)
        if source.get('PAD_LIBS') is None:source['PAD_LIBS']={}
        for kind,digest in cfg.EXPECTED.items():
            if cfg.sha(Path(state[kind]))!=digest:raise ValueError('Original preCTS view differs')
        prects.OUT=WORK
        stage_config=prects.configure(source,False)
        run=prects.run_stage(stage_config,state,'cluster8')
        cts,=run.glob('*-openroad-cts');prects.resolved_policy(cts,stage_config)
        sta,=run.glob('*-openroad-stamidpnr');prects.resolved_policy(sta,stage_config)
        final=json.loads((sta/'state_out.json').read_text())
        for kind,digest in cfg.DERIVED.items():
            if cfg.sha(Path(final[kind]))!=digest:raise ValueError('Regenerated cluster8 differs: '+kind)
        result['cluster8_sha256']=dict(cfg.DERIVED);save()
        fixed_dir=WORK/'fixed';fixed_dir.mkdir()
        if cfg.sha(Path(cfg.__file__))!=fixed.INHERITED_SHA:
            raise ValueError('Reviewed inherited ten-buffer implementation changed')
        env={'WARP_INPUT_ODB':final['odb'],'WARP_BEFORE':fixed_dir/'before.tsv',
            'WARP_AFTER':fixed_dir/'after.tsv','WARP_OUTPUT_ODB':fixed_dir/'buffered.odb',
            'WARP_OUTPUT_NL':fixed_dir/'buffered.nl.v'}
        native(cfg.CENSUS+fixed.local_edit(),'fixed',env)
        result['fixed_original_audit']=fixed.verify_immobility(
            (fixed_dir/'before.tsv').read_text(),(fixed_dir/'after.tsv').read_text())
        if cfg.sha(fixed_dir/'buffered.odb')!=FIXED_ODB_SHA or cfg.sha(fixed_dir/'buffered.nl.v')!=reference.EXPECTED['padded.nl.v']:
            raise ValueError('Exact fixed-original intermediate differs')
        result['fixed_odb_sha256']=FIXED_ODB_SHA;save()
        env={'WARP_INPUT_ODB':fixed_dir/'buffered.odb','WARP_BEFORE':OUT/'before.tsv',
            'WARP_AFTER':OUT/'after.tsv','WARP_GEOMETRY_BEFORE':OUT/'geometry_before.tsv',
            'WARP_GEOMETRY_AFTER':OUT/'geometry_after.tsv','WARP_SELECTION':OUT/'selected.txt',
            'WARP_OUTPUT_ODB':OUT/'padded.odb','WARP_OUTPUT_NL':OUT/'padded.nl.v'}
        native(cfg.CENSUS+reset.edit(),'combined_reset',env)
        result['placement']=reset.audit_move((OUT/'before.tsv').read_text(),(OUT/'after.tsv').read_text(),
            (OUT/'geometry_before.tsv').read_text(),(OUT/'geometry_after.tsv').read_text(),
            (OUT/'selected.txt').read_text().splitlines())
        config=final_config(source)
        # Original producer wrote indent2 JSON without a trailing newline.
        (OUT/'config.json').write_text(json.dumps(config,indent=2))
        authenticate_final(OUT)
        result['expected_view_sha256']=dict(reference.EXPECTED);save()
        guards.OUT=OUT
        for corner in config['STA_CORNERS']:
            case=guards.sta(config,'padded_sta_'+corner,OUT/'padded.odb',OUT/'padded.nl.v',Path(final['sdc']),corner)
            hold=case['metrics'][f'timing__hold__ws__corner:{corner}']
            if not isinstance(hold,(int,float)) or not math.isfinite(hold) or hold<0.1:
                raise ValueError('Regenerated control loses additional hold guard')
            result['corners'][corner]=case;save()
        sdc=OUT/'padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc'
        if cfg.sha(sdc)!=SDC_SHA:raise ValueError('Reproduced final SDC differs')
        authenticate_final(OUT)
        for kind,digest in cfg.EXPECTED.items():
            if cfg.sha(Path(state[kind]))!=digest:raise ValueError('Approved original source was modified')
        result['sdc_sha256']=SDC_SHA
        result['regenerated']=True;save()
        DESTINATION.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(OUT,DESTINATION)
        authenticate_final(DESTINATION)
    except Exception as exc:
        result['error']=str(exc);save();raise


if __name__=='__main__':main()
