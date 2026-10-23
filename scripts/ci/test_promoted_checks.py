import importlib.util
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('l2_injections', ROOT/'test_internal/l2/run_injections.py')
injections = importlib.util.module_from_spec(spec)
spec.loader.exec_module(injections)


@pytest.mark.parametrize('line', [
    "wire [15:0] q_inc  = (r_wrap && (qn != 16'h7fff)) ? qn + 16'd1 : qn;",
    "wire [15:0] base_inc = (base_wrap && (q_b != 16'h7fff)) ? q_b + 16'd1 : q_b;",
])
def test_cursor_injection_changes_only_normal_increment(line):
    before, after = injections.cursor_mutation(line)
    assert before == line
    assert after == line.replace("+ 16'd1", "+ 16'd2")
    with pytest.raises(RuntimeError):
        injections.cursor_mutation(line+'\n'+line)


def test_unknown_cursor_implementation_is_not_credited():
    with pytest.raises(RuntimeError):
        injections.cursor_mutation('wire [15:0] arbitrary = 0;')


def test_fault_variants_cannot_share_compiled_model_or_results(tmp_path):
    baseline = injections.isolated_make(tmp_path/'baseline')
    mutation = injections.isolated_make(tmp_path/'mutation')
    assert baseline != mutation
    assert f'SIM_BUILD={tmp_path / "baseline/sim_build"}' in baseline
    assert f'COCOTB_RESULTS_FILE={tmp_path / "mutation/results.xml"}' in mutation


def test_narrow_lint_annotations_leave_unrelated_warning_fatal(tmp_path):
    path = tmp_path/'trw_pin_cfg.v'
    path.write_text("module trw_pin_cfg(input wire a, output wire b); wire rogue_internal = 1'b0; assign b=a; endmodule\n")
    result = subprocess.run(['verilator', '--lint-only', '-Wall', str(ROOT/'scripts/ci/promoted_rtl.vlt'),
                             '--top-module', 'trw_pin_cfg', str(path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'rogue_internal' in result.stderr


def test_local_check_scripts_parse():
    for name in ('scripts/check_all.sh', 'scripts/gl_local.sh', 'scripts/ci/official_openroad_wrapper.sh'):
        subprocess.run(['bash', '-n', str(ROOT/name)], check=True)


@pytest.mark.parametrize('outside_latch', [False, True])
def test_synthesis_check_permits_only_latch_store_modules(tmp_path, outside_latch):
    code = """module trw_slots(input wire g,d,output reg q); always @* if(g) q=d; endmodule
module other(input wire g,d,output reg q); OTHER endmodule
module top(input wire g,d,output wire a,b); trw_slots s(g,d,a); other o(g,d,b); endmodule
""".replace('OTHER', 'always @* if(g) q=d;' if outside_latch else 'always @* q=d;')
    path = tmp_path/'latches.v'
    path.write_text(code)
    script = ('read_verilog '+str(path)+'; hierarchy -top top; proc; '
              'select -assert-none t:$dlatch t:$_DLATCH_* %u N:*trw_slots* N:*trw_pin_cfg* %u %d')
    result = subprocess.run(['yosys', '-Q', '-T', '-p', script], capture_output=True, text=True)
    assert (result.returncode != 0) == outside_latch
