import shutil
import subprocess

import pytest
import verify_lane_read_mask as target


def fixture(output):
    source = output/'src'
    source.mkdir()
    for name in ('trw_lane.v', 'trw_alu.v', 'trw_defs.vh', 'trw_assert.vh'):
        shutil.copyfile(target.ROOT/'src'/name, source/name)
    return output


def test_patch_is_single_file_and_reversible(tmp_path):
    fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in (tmp_path/'src').iterdir()}
    result = target.apply_delta(tmp_path)
    assert target.digest(result) == target.TRIAL_HASH
    assert (tmp_path/'lane_read_gold.v').read_bytes() == before['trw_lane.v']
    subprocess.run(['git', 'apply', '--reverse',
                    str(target.ROOT/'spikes/r4_floorplan/lane_read_mask.patch')],
                   cwd=tmp_path, check=True)
    assert {p.name: p.read_bytes() for p in (tmp_path/'src').iterdir()} == before


def test_wrong_base_rejected_before_change(tmp_path):
    fixture(tmp_path)
    source = tmp_path/'src/trw_lane.v'
    source.write_text(source.read_text()+'\n// mismatched source\n')
    before = source.read_bytes()
    with pytest.raises(ValueError, match='Wrong lane'):
        target.apply_delta(tmp_path)
    assert source.read_bytes() == before
    assert not (tmp_path/'lane_read_gold.v').exists()


@pytest.mark.parametrize('mutate', [False, True])
def test_real_lane_equivalence_and_wrong_read_negative_control(tmp_path, mutate):
    fixture(tmp_path)
    source = target.apply_delta(tmp_path)
    if mutate:
        text = source.read_text()
        needle = "({16{ia == 2'd0}} & regs[15:0])"
        assert text.count(needle) == 1
        source.write_text(text.replace(needle, "({16{ia == 2'd0}} & regs[31:16])"))
        with pytest.raises(subprocess.CalledProcessError):
            target.prove(tmp_path)
    else:
        assert target.prove(tmp_path) == 2181


def test_full_patch_binds_all_five_workflow_sources(tmp_path):
    import yaml
    from timing_trial import CANDIDATE, PATCHES
    from verify_timing_trial import verify
    variant = 'bs-resync-cfg-tx-cached-lane-mask'
    patch, files = PATCHES[variant]
    for name in files:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(['git', 'show', f'{CANDIDATE}:{name}']))
    subprocess.run(['git', 'apply', str(target.ROOT/'spikes/r4_floorplan'/patch)],
                   cwd=tmp_path, check=True)
    workflow = target.ROOT/'.github/workflows/gds-native-lane-mask-setup-reserve-screen.yaml'
    job = yaml.safe_load(workflow.read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == variant
    commands = '\n'.join(s.get('run', '') for s in job['steps'])
    for name in files:
        assert target.digest(tmp_path/name) in commands
    assert target.digest(tmp_path/'src/trw_lane.v') == target.TRIAL_HASH
    assert 'native_lane_mask_screen.py' in commands
    assert 'float(cfg["CLOCK_PERIOD"]) == 20.0' in commands
    assert 'OpenROAD.RepairAntennas-1' in commands
    with pytest.raises(ValueError, match='clocked-host'):
        verify(variant, tmp_path/'wrong-verifier')


def test_wrapper_requires_exact_variant_and_original_physical_policy(monkeypatch):
    import native_lane_mask_screen as screen
    calls = []
    monkeypatch.setattr(screen, 'reserve_screen', lambda **kw: calls.append(kw))
    monkeypatch.setenv('VARIANT', 'bs-resync-cfg-tx-cached-select')
    with pytest.raises(ValueError): screen.main()
    monkeypatch.setenv('VARIANT', 'bs-resync-cfg-tx-cached-lane-mask')
    screen.main()
    assert calls == [{'config_transform': screen.configure}]
