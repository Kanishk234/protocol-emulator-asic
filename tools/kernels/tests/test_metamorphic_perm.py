"""Finite L4-PERM fast-path checks; never erase resource-phase counterexamples."""
import hashlib
import json

import pytest
from kernels.metamorphic_perm import image,run_model

PROFILES=[('uart',115200),('uart',460800),('spi',50),('spi',10),('spi',6),
          ('i2c',500),('i2c',125),('i2c',50)]


@pytest.mark.parametrize('protocol,rate',PROFILES)
def test_legal_fast_path_permutations_are_cycle_exact(protocol,rate):
    baseline=run_model(protocol,rate)
    for mapping in ['units','lane','both']:
        candidate=run_model(protocol,rate,mapping)
        assert baseline==candidate,(protocol,rate,mapping)
        digest=hashlib.sha256(bytes(v for row in baseline[0] for v in row)).hexdigest()
        print('L4_PERM '+json.dumps({'protocol':protocol,'rate':rate,'mapping':mapping,
              'clocks':len(baseline[0]),'host_items':len(baseline[1]),'trace_sha256':digest},sort_keys=True))


@pytest.mark.parametrize('protocol,rate',[('uart',460800),('spi',10),('i2c',125)])
def test_wrong_output_owner_is_detected(protocol,rate):
    with pytest.raises(AssertionError):run_model(protocol,rate,'both',wrong_owner=True)


def test_native_routine_controller_exposes_rotation_phase_premise():
    # Explicitly the native qualified one-EVAL-per-clock design, not a claim
    # about every alternative scheduler in the model.
    baseline=run_model('i2c_controller',124,fire_period=1)
    units=run_model('i2c_controller',124,'units',fire_period=1)
    unaligned=run_model('i2c_controller',124,'both',fire_period=1)
    aligned=run_model('i2c_controller',124,'both',warmup=1,fire_period=1)
    assert baseline==units==aligned
    assert baseline[0]!=unaligned[0] and baseline[1]==unaligned[1]
    differences=[i for i,(a,b) in enumerate(zip(baseline[0],unaligned[0])) if a!=b]
    print('L4_PERM_PHASE '+json.dumps({'first_difference':differences[0],
          'different_clocks':len(differences),'host_delivery_equal':True,
          'unaligned_not_cycle_exact':True,'one_real_idle_clock_before_load_restores_trace':True},sort_keys=True))
