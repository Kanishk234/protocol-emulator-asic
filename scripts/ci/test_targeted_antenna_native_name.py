"""Regression for the exact OpenDB spelling captured in run41968668727."""
from pathlib import Path
import subprocess


def test_target_list_matches_raw_native_name(tmp_path):
    source = Path(__file__).with_name('targeted_antenna_size.tcl').read_text()
    start = source.index('set trw_targets')
    targets = source[start:source.index('\n}\n', start) + 3]
    script = tmp_path / 'names.tcl'
    script.write_text(targets + '\nputs "NATIVE_NET_HEX [binary encode hex [dict get [lindex [lindex $trw_targets 2] 3] B]]"\n')
    result = subprocess.run(['yosys', '-Q', '-T', '-c', str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    actual_native_name = r'u_chip.g_lane\[1\].slots\[626\]'
    assert 'NATIVE_NET_HEX ' + actual_native_name.encode().hex() in result.stdout
