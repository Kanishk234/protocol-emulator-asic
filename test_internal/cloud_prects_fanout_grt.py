"""Pair fanout-clean rebuilt placement with the best133 control, unchanged GRT policy."""
import json
from pathlib import Path
import shutil
import cloud_delay_rebalance_grt as adapter
import cloud_prects_fanout as producer
import cloud_hotspot_grt as paired
import cloud_hold_allocation as payload
import cloud_cfg_fanout as cfg

ROOT=cfg.ROOT
INPUT=ROOT/'build/prects_fanout_grt_input'
OUT=ROOT/'build/prects_fanout_grt'
RESULT_SHA='df6f07c502518e2d9a1ec95facd43de5f5d060df11206dab6f59d484da33271b'
CANDIDATE={'odb':'90940c876925b362f0589d6e3052d37527d3fdae75b71388848b717d0d82bb17',
 'nl':'d53fd05fb028b4589f7b855daaed84415cc4425fe2b88c840938e002a3d5d35f','sdc':adapter.SDC_SHA}


def validate(directory,baseline):
    adapter.validate_control(baseline)
    if cfg.sha(directory/'result.json')!=RESULT_SHA:raise ValueError('Measured reflow producer differs')
    result=json.loads((directory/'result.json').read_text())
    if result.get('producer_passed') is not True or result.get('source_run')!=38319615838:
        raise ValueError('Wrong or failed fanout-clean producer')
    audit=producer.immutability((directory/'producer_before.tsv').read_text(),(directory/'after.tsv').read_text())
    if audit!=result['audit']:raise ValueError('Measured immutability/connectivity audit differs')
    for name,key in (('padded.odb','odb'),('padded.nl.v','nl')):
        if cfg.sha(directory/name)!=CANDIDATE[key]:raise ValueError('Candidate routing view differs')
    for corner in ('nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C'):
        case=result['corners'][corner]
        if (case['odb_sha256']!=CANDIDATE['odb'] or case['nl_sha256']!=CANDIDATE['nl']
                or case['sdc_sha256']!=CANDIDATE['sdc']):raise ValueError('Measured timing views differ')
        m=case['metrics']
        if m[f'timing__hold__ws__corner:{corner}']<0.1 or m[f'timing__setup__ws__corner:{corner}']<=0:
            raise ValueError('Producer timing margin lost')
        keys=[f'design__{s}_violation__count__corner:{corner}' for s in ('max_fanout','max_slew','max_cap')]
        keys += [f'timing__{s}_vio__count__corner:{corner}' for s in ('setup','hold')]
        if any(m[k]!=0 for k in keys):raise ValueError('Producer electrical/timing violations')
    # Native snapshot already proves macro and physical boundary/row identity.
    return {'original_instances':3645,'added_identity_buffers':10,'producer_audit':audit}


def main():
    baseline,candidate=INPUT/'baseline',INPUT/'padded'
    for name,digest in payload.EXPECTED.items():
        if cfg.sha(baseline/name)!=digest:raise ValueError('Best control differs before adaptation')
    archive=ROOT/'build/fanout-preflight-source.tar.gz'
    if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError('Original payload archive differs')
    payload.prepare_payload(archive,baseline/'original_source')
    for directory,old,new in ((baseline,'padded.odb','buffered.odb'),(baseline,'padded.nl.v','buffered.nl.v'),
            (candidate,'buffered.odb','padded.odb'),(candidate,'buffered.nl.v','padded.nl.v')):
        shutil.copyfile(directory/old,directory/new)
    target=baseline/'buffered_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc'
    target.parent.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(baseline/'padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc',target)
    shutil.copyfile(candidate/'before.tsv',candidate/'producer_before.tsv')
    shutil.copyfile(baseline/'after.tsv',candidate/'before.tsv')
    (candidate/'original_source').symlink_to(baseline/'original_source',target_is_directory=True)
    paired.INPUT,paired.OUT=INPUT,OUT
    paired.SOURCE_RUN,paired.RESULT_SHA=38320631258,RESULT_SHA
    paired.BUFFERED,paired.PADDED=adapter.BASELINE,CANDIDATE
    paired.validate_candidate,paired.validate_padding=adapter.validate_control,validate
    try:paired.main()
    finally:
        path=OUT/'result.json'
        if path.exists():
            result=json.loads(path.read_text());result['source_runs']['baseline']=38167697696
            result['scope']='unchanged-policy GRT: best133 control versus fanout-clean before-CTS reflow'
            result['candidate_global_route_passed']=result.get('cases',{}).get('padded',{}).get('route_passed',False)
            path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
