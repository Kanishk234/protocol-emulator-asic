"""Integrity and timestamp controls for real-capture replay."""
import io
from fractions import Fraction
import zipfile

import pytest
import capture_replay as R


def sr(*,rate='16 MHz',unitsize=1,duplicate=False):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('metadata',f'[device 1]\nunitsize={unitsize}\nsamplerate={rate}\nprobe1=RX\n'+('probe2=RX\n' if duplicate else ''))
        for n,value in [(10,10),(2,2),(1,1)]:z.writestr(f'logic-1-{n}',bytes([value]))
    return buf.getvalue()


def test_chunks_are_numeric_and_metadata_rate_is_exact():
    samples,hz,channels=R.read_sr(sr())
    assert samples==bytes([1,2,10])
    assert hz==16_000_000 and channels=={'RX':0}


@pytest.mark.parametrize('kwargs',[{'unitsize':2},{'rate':'51 MHz'},{'rate':'0 Hz'},
                                  {'rate':'not a rate'},{'duplicate':True}])
def test_unsupported_capture_is_not_silently_reinterpreted(kwargs):
    with pytest.raises(ValueError):R.read_sr(sr(**kwargs))


def test_fractional_resampling_has_no_accumulated_drift_or_level_rewrite():
    c=R.Capture.__new__(R.Capture)
    c.samples=bytes(i&1 for i in range(1000));c.hz=Fraction(16_000_000);c.channels={'rx':0}
    for sample in range(1000):
        first=(sample*R.HZ+15_999_999)//16_000_000
        last=((sample+1)*R.HZ+15_999_999)//16_000_000-1
        assert c.levels(first)==c.levels(last)=={'rx':sample&1}
        assert 0<=Fraction(first,R.HZ)-Fraction(sample,16_000_000)<Fraction(1,R.HZ)
    with pytest.raises(ValueError):c.levels(-1)


def test_modified_cached_source_is_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(R,'CACHE',tmp_path)
    monkeypatch.setattr(R,'manifest',lambda:{'files':{'capture.sr':{'sha256':R.digest(b'original')}}})
    (tmp_path/'capture.sr').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Changed capture/source'):R.verified('capture.sr')
