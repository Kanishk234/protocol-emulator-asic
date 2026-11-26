"""Connected RC diagnostic for actually loaded placement images; no acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from assembly_catalog import sha
from compile.bitfile import BitFile
from configuration_audit import audit
from routed_timing import annotation,assert_cases,observed_cases,prepare as prepare_parent,run as run_parent
from run_timing import compare,parse_log



GATE_CHECK=re.compile(
    r'(if \{\[sta::pin_sim_logic_value \[lindex \[get_pins \{([^{}]+)/GATE\}\] 0\]\]!="0" \|\| '
    r'\[sta::pin_sim_logic_value \[lindex \[get_pins \{([^{}]+/Q)\}\] 0\]\]!=")'
    r'([01])("\} \{error "configuration case/gate mismatch"\}\nincr closed)')


def assert_gate_checks(text,values):
    matches=list(GATE_CHECK.finditer(text))
    if (len(matches)!=len(values) or
            any(m[2]+'/Q'!=m[3] for m in matches) or
            len({m[3] for m in matches})!=len(matches) or
            {m[3]:m[4] for m in matches}!=values or
            text.count('configuration case/gate mismatch')!=len(matches)):
        raise ValueError('Configuration gate checks differ from actual loaded state')


def replace_cases(text,old,new):
    assert_cases(text,old)
    assert_gate_checks(text,old)
    if set(new)!=set(old) or any(v not in ('0','1') for v in new.values()):
        raise ValueError('Candidate configuration identity or binary state differs')
    pattern=(r'(set p \[get_pins -quiet \{([^{}]+/Q)\}\]\n'
             r'if \{\[llength \$p\]!=1\} \{error "missing configuration pin"\}\n'
             r'set_case_analysis )([01])( \$p\nincr observed)')
    result=re.sub(pattern,lambda m:m[1]+new[m[2]]+m[4],text)
    result=GATE_CHECK.sub(lambda m:m[1]+new[m[3]]+m[5],result)
    assert_cases(result,new)
    assert_gate_checks(result,new)
    return result


def prepare(rc,proof,native,capsule,pdk,functional,out):
    functional,out=Path(functional).resolve(),Path(out).resolve()
    data=json.loads((functional/'result.json').read_text())
    if (not data['passed'] or not {'control','candidate','shell'}<=set(data['cases']) or
            any(not row['passed'] for row in data['cases'].values())):
        raise ValueError('Require all actual native loading cases')
    if data['cases']['candidate']!=data['cases']['shell']:
        raise ValueError('Actual direct and management/reload observations differ')
    observed=json.loads((functional/'candidate/configuration-state.json').read_text())
    image=functional/'candidate/quiesced.wbit'
    quiescence=json.loads((functional/'candidate/quiescence.json').read_text())
    admitted={'0834b13c09e5e23a35122f71258ceabfbe8a61d3dffbc31b6b0a1851921d241f',
              'cf186c6d78f4b003ffc868b3f6d5e34f16aad4e1df14f2989195dbd03a7d049b',
              'cbea6b084f843d95222cbb93cfd4a55ac0698a3d51b54689eb358d9678ff0462',
              '6a29427ad987091613795b89ef9dc463be0b7c2e1d85c6679e04312c23d72066',
              '696cd708a5fad674134724bcbdf43c1ceed287b61a73d1bfa393ac301b70d187',
              'a7306047e903996e8488819ab428543389cc1ffd71fe2d95a7fb2475f720884e',
              '79db28f92959f998faf2b6b00b65be3539abc5e03625f77bd80584601fa2fd6a',
              '218ac7799311951ed9f319ef151aa793128febbaaa6b67a3daa67fe07952920d',
              '4326eab8868442494239e0a413aa199158293b14cff856453ae8c37bd6d7403a',
              '97caee72e610700fddd885f21b7d07a3116f19b45540bc3c02423740df999d5e',
              'c13edb09ddfc73c9aa58ba4f4c99f08ec52faa2e172b2218cc20bbf1aa936a88',
              'b242b24acb04989e040c622fd96ad0dd9f8d44a80f99b267c5933b2c8c404564',
              '983a08f26cc001227265ce1a3ff16616d0acaee9b15cdd954aceb70a43e91be4',
              '6cfaea26ad9d8239ed20d449211f86748a2bd607303425dfa9b21dd6dd8153a9',
              '4a35f4d6f66bb0706f6c147934dd6ea520d6c7fd5c33e6c457b3c56b84b78300',
              '5d15c67f4659a632be27fe45f5bd40499bb15f8793749f7174f7d7ab8759fe87',
              '75b7c2cd84b846f2ed8cfee040e1b34c05498bc67bf6b12d69d119f3f0ea1cee',
              '1406326c1784f20a287795271639586e6e4fb47aac8a284eca254b3a55287f8d'}
    if quiescence['source_image_sha256'] not in admitted:
        raise ValueError('Require an admitted fixed-source placement image')
    if sha(image)!=data['cases']['candidate']['image_sha256'] or sha(functional/'candidate/configuration-state.json')!=data['cases']['candidate']['observed_configuration_sha256']:
        raise ValueError('Actual native evidence changed')
    modules=Path(native)/'registered_native/all-native.json'
    frame=audit(json.loads(modules.read_text())['modules'],observed,BitFile.load(image).words)
    if not frame['passed'] or frame['compared_configuration_bits']!=8736:
        raise ValueError('Actual SA frame agreement incomplete')
    out.mkdir(parents=True,exist_ok=False)
    prepare_parent(rc,proof,native,capsule,pdk,out/'baseline')
    old=observed_cases(json.loads((Path(native)/'registered_functional/candidate/configuration-state.json').read_text()))
    new=observed_cases(observed);scripts={}
    for kind in ('setup','hold'):
        for policy in ('static','dynamic'):
            label='routed_'+kind+'_'+policy
            target=out/(label+'.tcl')
            target.write_text(replace_cases((out/'baseline'/(label+'.tcl')).read_text(),old,new))
            scripts[label]=sha(target)
    bound=[Path(__file__).resolve(),functional/'result.json',functional/'candidate/configuration-state.json',image,
           functional/'candidate/quiescence.json',modules]
    (out/'plan.json').write_text(json.dumps(dict(inputs={str(p):sha(p) for p in bound},scripts=scripts,
         actual_native_run=data['run'],frame_audit=frame,actually_loaded_image_sha256=sha(image)),indent=2)+'\n')



def validate_parent(parent):
    if (not parent.get('diagnostic_complete') or
            parent.get('error')!='Configured macro setup/hold or loop-policy check fails'):
        raise ValueError('Original connected timing control did not reproduce')
    for kind,expected in (('setup',-11.108903),('hold',-1.870506)):
        model=parent['models']['routed_'+kind]
        if (abs(model['worst_slack_ns']-expected)>0.000001 or
                model['structural_loops']!=0 or model['loop_policy_sensitive']):
            raise ValueError('Original connected timing control changed')
    coverage=[parent['annotation']['routed_'+kind+'_'+policy]
              for kind in ('setup','hold') for policy in ('static','dynamic')]
    if any(not row['passed'] for row in coverage):
        raise ValueError('Original active annotation is incomplete')


def run(out):
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Actual candidate evidence changed')
    try:run_parent(out/'baseline')
    except SystemExit:pass
    parent=json.loads((out/'baseline/result.json').read_text())
    validate_parent(parent)
    models={};coverage={}
    for kind in ('setup','hold'):
        logs=[]
        for policy in ('static','dynamic'):
            label='routed_'+kind+'_'+policy;script=out/(label+'.tcl')
            if sha(script)!=plan['scripts'][label]:raise ValueError('SA case script changed')
            with (out/(label+'.log')).open('w') as stream:
                proc=subprocess.run(['sta','-exit',str(script)],stdout=stream,stderr=subprocess.STDOUT,timeout=240)
            text=(out/(label+'.log')).read_text()
            (out/(label+'.execution.json')).write_text(json.dumps(dict(returncode=proc.returncode,
                completion_marker=text.endswith('RUNSTA_END\n'),log_sha256=sha(out/(label+'.log'))),indent=2)+'\n')
            if proc.returncode:raise ValueError('Native timing execution failed ('+str(proc.returncode)+')')
            logs.append(parse_log(text));coverage[label]=annotation(text)
        models[kind]=compare(*logs)
        models[kind]['structural_loops_by_policy']={policy:row['structural_loops']
            for policy,row in zip(('static','dynamic'),logs)}
        models[kind]['structural_loops']=max(row['structural_loops'] for row in logs)
    qualified=all(a['passed'] for a in coverage.values()) and all(not m['loop_policy_sensitive'] and m['structural_loops']==0 for m in models.values())
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),diagnostic_complete=True,
        models=models,coverage=coverage,model_qualified=qualified,
        necessary_macro_constraints_met=qualified and all(m['worst_slack_ns']>=0 for m in models.values()),
        actual_native_run=plan['actual_native_run'],actually_loaded_image_sha256=plan['actually_loaded_image_sha256'],
        timing_acceptance=False,physical_acceptance=False,adopted=False,
        scope='Actually loaded placement image on unchanged source-proven connected nominal RC, original 20ns/0.25ns/conditional zero-I/O boundary. Original failing parent retained. No full-chip/PVT/loading-mode acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not qualified:raise SystemExit('SA timing model coverage/loop qualification failed; retain failure')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('rc','proof','native','capsule','pdk','functional','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)
