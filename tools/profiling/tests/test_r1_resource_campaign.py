import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('r1_campaign',ROOT/'test_internal/cloud_r1_resource.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_actual_worker_command_shape():
    args=m.arguments(['--worker','uart_spi_11','model','output'])
    assert args.worker and args.paths==['uart_spi_11','model','output']
    args=m.arguments(['model','output'])
    assert not args.worker and args.paths==['model','output']


@pytest.mark.parametrize('args',[[],['model'],['--worker','model','out'],['model','out','extra']])
def test_incomplete_campaign_or_worker_rejected(args):
    with pytest.raises(SystemExit):m.arguments(args)


def test_no_local_eda(monkeypatch):
    monkeypatch.delenv('GITHUB_ACTIONS',raising=False)
    with pytest.raises(RuntimeError):m.worker('uart_spi_11',None,None)
    with pytest.raises(RuntimeError):m.main(None,None)


def test_campaign_records_failure_and_still_runs_all_workloads(tmp_path,monkeypatch):
    import json
    monkeypatch.setenv('GITHUB_ACTIONS','true')
    model=tmp_path/'model';model.mkdir()
    (model/'resource-control.json').write_text(json.dumps(dict(
        passed=True,physical_candidate=False,generated_sha256={})))
    versions={'yosys':'Yosys 0.66+179 e74db6dea',
              'nextpnr-generic':'nextpnr-0.11.1-34-gc4fbb55a'}
    monkeypatch.setattr(m.compiler,'tool_versions',lambda:versions)
    called=[]
    def execute(command,log):
        case=command[3];called.append(case)
        folder=Path(command[-1]);folder.mkdir()
        if len(called)==1:
            (folder/'pnr.log').write_text('ERROR: failed to route net example\n')
            raise RuntimeError('Worker failed')
        (folder/'case.json').write_text(json.dumps(dict(case=case,tools=versions)))
    monkeypatch.setattr(m,'run_bounded',execute)
    out=tmp_path/'out'
    with pytest.raises(RuntimeError,match='all outcomes retained'):m.main(model,out)
    result=json.loads((out/'result.json').read_text())
    assert called==list(m.CASES) and set(result['cases'])==set(m.CASES)
    assert result['passed'] is False
    assert result['cases'][m.CASES[0]]['native_diagnosis']['category']=='routing'


def test_absent_pnr_log_is_not_reported_as_architecture_nonfit(tmp_path):
    row=m.failure_record('uart',tmp_path,RuntimeError('missing compiler executable'))
    assert row['native_diagnosis']['category']=='unobserved'
