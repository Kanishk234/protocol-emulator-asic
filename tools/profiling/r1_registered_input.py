"""Opt-in one-bit R1 image experiment, bound to the measured D134 parent."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from compile.bitfile import BitFile

ROOT=Path(__file__).resolve().parents[2]
PARENT_SHA='9af858413aa8c39739f3f7bda8e290433d58cb1702f69a04c9c6e74657b90410'


def admit_timing_result(result,change):
    candidate=result['observations']['candidate'];control=result['observations']['control']
    slack=candidate['worst_slack_ns']
    if (result.get('diagnostic_complete') is not True or result.get('hypothesis_supported') is not True
            or result['change']!=change or candidate['loop_policy_sensitive']
            or candidate['loop_policy_differences'] or len(control['loop_policy_differences'])!=6
            or type(slack) not in (int,float) or not math.isfinite(slack) or slack<0):
        raise ValueError('Registered-input timing hypothesis is not supported')


def park_words(words,change):
    if (len(words)!=962 or change['tile_bit']!=183 or change['frame']!=5 or change['data_bit']!=23
            or change['tile']!='Tile_X2Y3_LUT4x8_ha' or change['before']!='0' or change['after']!='1'):
        raise ValueError('Wrong registered-input experiment change')
    index=273;mask=1<<23
    if words[index]&mask:raise ValueError('Parent selector is already set')
    candidate=list(words);candidate[index]|=mask
    if sum((a^b).bit_count() for a,b in zip(words,candidate))!=1:
        raise ValueError('Experiment changed more than one frame bit')
    return candidate


def audit_snapshots(parent,candidate,shell):
    before=parent['tiles'];after=candidate['tiles'];reloaded=shell['tiles']
    if len(before)!=40 or set(before)!=set(after) or after!=reloaded:
        raise ValueError('Incomplete or inconsistent native candidate snapshots')
    changes=[]
    for tile,row in before.items():
        other=after[tile]
        if row['tile_type']!=other['tile_type'] or set(row['q'])!=set(other['q']):
            raise ValueError('Native configuration topology differs')
        for cell,value in row['q'].items():
            if other['q'][cell]!=value:changes.append((tile,cell,value,other['q'][cell]))
    if changes!=[('Tile_X2Y3_LUT4x8_ha','_1560_','0','1')]:
        raise ValueError('Loaded native configuration differs beyond the one analyzed bit')
    return dict(native_tiles=40,configuration_changes=changes,analysis_case_matches_loaded_candidate=True)


def apply(model,case,parent_image,out):
    model,case,parent_image,out=(Path(p).resolve() for p in (model,case,parent_image,out))
    capsule=model.parents[1]
    if model!=capsule/'model/resource' or case!=capsule/'model/compile/uart_spi_11':
        raise ValueError('Registered-input experiment requires the authenticated primary capsule')
    if hashlib.sha256(parent_image.read_bytes()).hexdigest()!=PARENT_SHA:
        raise ValueError('Registered-input experiment parent differs')
    parent=BitFile.load(parent_image)
    if parent.arch_version!=0xFE:raise ValueError('Production images are excluded')
    sys.path.insert(0,str(ROOT/'spikes/r1'))
    from unused_lut_probe import prepare
    admission=out/'registered-input-admission'
    prepare(capsule,admission,target='unused-d-upstream-select')
    plan=json.loads((admission/'plan.json').read_text());change=plan['change']
    evidence=os.environ.get('R1_REGISTERED_INPUT_TIMING_RESULT')
    if not evidence:raise ValueError('Require the measured registered-input timing result')
    evidence=Path(evidence).resolve()
    admit_timing_result(json.loads(evidence.read_text()),change)
    candidate=park_words(parent.words,change)
    image=out/'registered-input.wbit';BitFile(parent.arch_version,candidate).save(image)
    record=dict(policy='registered-H-source-on-unused-D-input',parent_image_sha256=PARENT_SHA,
                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),changed_bits=1,
                change=change,scope='Diagnostic image only; actual native load/function/reload and timing qualification required.')
    inputs=[Path(__file__),parent_image,evidence,admission/'plan.json',ROOT/'tools/compile/bitfile.py',
            *map(Path,plan['input_sha256'])]
    return image,record,inputs
