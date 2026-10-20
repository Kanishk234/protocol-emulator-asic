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
